#!/usr/bin/env python3
"""Small stdlib Mac front end; all Debian operations happen in one dedicated VM."""
import argparse
from contextlib import contextmanager
import fcntl
import getpass
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import runpy
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
VM = 'codeswarm-builder-v1'
STATE = Path.home()/'Library/Application Support/CodeSwarm'
GIB = 1024**3

def state_directory():
    STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
    if STATE.is_symlink() or STATE.stat().st_uid != os.getuid() or STATE.stat().st_mode & 0o077:
        raise RuntimeError('Builder state directory must be owner-only (0700), not a symlink.')

@contextmanager
def builder_lock():
    state_directory()
    fd = os.open(STATE/'builder.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as lock:
        if os.fstat(lock.fileno()).st_uid != os.getuid() or os.fstat(lock.fileno()).st_mode & 0o077:
            raise RuntimeError('Builder lock must be owned privately by this user.')
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('Another CodeSwarm build or personalization is running.') from None
        yield

def command(args, **kw):
    return subprocess.run(args, check=True, **kw)

def shell(*args, **kw):
    return command(['limactl', 'shell', '--workdir=/', VM, *args], **kw)

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(4*1024*1024), b''):
            h.update(block)
    return h.hexdigest()

def architecture(system=None, machine=None):
    system, machine = system or platform.system(), machine or platform.machine()
    if system != 'Darwin' or machine not in ('arm64', 'x86_64'):
        raise RuntimeError('This front end requires an Intel or Apple Silicon Mac.')
    return 'Apple Silicon: x86_64 QEMU emulation (slow)' if machine == 'arm64' else 'Intel: x86_64 VM'

def doctor(output):
    print(architecture()+'. Target: Debian 13 amd64, never arm64.', flush=True)
    for binary in ('limactl', 'qemu-system-x86_64'):
        if not shutil.which(binary):
            raise RuntimeError('Missing '+binary+'. See docs/MAC-BUILDER.md for owner-run prerequisites.')
    memory = int(command(['sysctl', '-n', 'hw.memsize'], capture_output=True, text=True).stdout)
    if memory < 8*GIB:
        raise RuntimeError('At least 8 GiB host RAM is required; the VM reserves 4 GiB.')
    for location in (Path.home(), output.parent):
        if not location.exists():
            raise RuntimeError('Output parent must already exist.')
        if shutil.disk_usage(location).free < 45*GIB:
            raise RuntimeError('At least 45 GiB free is required on home and output volumes.')
    print('Resources: VM 2 CPUs / 4 GiB RAM / 64 GiB sparse disk. Host prerequisites passed.', flush=True)

def source_paths(root=ROOT):
    result = []
    for name in (root/'builder/source-files.txt').read_text().splitlines():
        if not name or name.startswith('#'):
            continue
        rel = Path(name)
        if rel.is_absolute() or '..' in rel.parts:
            raise RuntimeError('Unsafe source manifest path')
        path = root/rel
        if not path.is_file() or any(p.is_symlink() for p in [path, *path.parents] if p != root.parent):
            raise RuntimeError('Source must contain regular files with no symlink ancestors')
        result.append((path, name))
    return result

def archive(destination, root=ROOT, recipe=None):
    if recipe is not None:
        helper = runpy.run_path(str(ROOT/'builder/recipe.py'))
        helper['bundle'](destination, helper['read'](recipe), root)
        return
    with tarfile.open(destination, 'w') as tar:
        for path, name in source_paths(root):
            info = tar.gettarinfo(str(path), arcname=name)
            info.uid = info.gid = 0
            info.uname = info.gname = ''
            with path.open('rb') as f:
                tar.addfile(info, f)

def vm_ready():
    config = ROOT/'builder/lima.yaml'
    expected = sha(config)
    state_directory()
    record = STATE/'builder.json'
    names = command(['limactl', 'list', '--format', '{{.Name}}'], capture_output=True, text=True).stdout.splitlines()
    if VM in names:
        if not record.is_file() or json.loads(record.read_text()) != {'vm': VM, 'config_sha256': expected}:
            raise RuntimeError('Existing VM is not owned by this configuration. Do not overwrite it; see troubleshooting.')
        command(['limactl', 'start', '--tty=false', VM])
    else:
        print('Creating dedicated Debian VM; no home mount, disk passthrough or agent forwarding.', flush=True)
        command(['limactl', 'start', '--tty=false', '--name='+VM, str(config)])
        shell('sudo', 'sh', '-c', 'printf "%s\\n" codeswarm-builder-v1 > /etc/code-swarm-builder')
        record.write_text(json.dumps({'vm': VM, 'config_sha256': expected}))
        record.chmod(0o600)
    shell('sh', '-c', 'test "$(uname -m)" = x86_64 && test "$(dpkg --print-architecture)" = amd64 && test "$(cat /etc/code-swarm-builder)" = codeswarm-builder-v1')

def fresh_output(path):
    path = path.expanduser().absolute()
    if path.exists() or path.is_symlink():
        raise RuntimeError('Output must be a new directory; existing results are never overwritten.')
    if path == ROOT or ROOT in path.parents:
        raise RuntimeError('Place outputs outside the Git source tree.')
    path.mkdir(mode=0o700)
    return path

def download(guest, path):
    with path.open('xb') as output:
        path.chmod(0o600)
        shell('sudo', 'cat', guest, stdout=output)

def verify_output(output, name):
    expected = (output/'SHA256SUMS').read_text().split()
    if len(expected) != 2 or expected[1] != name or sha(output/name) != expected[0]:
        raise RuntimeError('Output SHA256 verification failed; do not use the image.')

def build(output, recipe=None):
    if recipe is not None:
        runpy.run_path(str(ROOT/'builder/recipe.py'))['read'](recipe)
    doctor(output)
    output = fresh_output(output)
    vm_ready()
    try:
        # This is a private disposable VM with a marker; no host directory is mounted.
        shell('sudo', 'sh', '-c', 'test "$(cat /etc/code-swarm-builder)" = codeswarm-builder-v1 && rm -rf /work && mkdir -m 755 /work')
        with tempfile.TemporaryDirectory(prefix='codeswarm-source-') as temp:
            bundle = Path(temp)/'source.tar'
            archive(bundle, recipe=recipe)
            with bundle.open('rb') as f:
                shell('sudo', 'tar', '-xf', '-', '-C', '/work', stdin=f)
        shell('sudo', 'bash', '/work/builder/guest-build.sh')
        for name in ('code-swarm-amd64.iso', 'SHA256SUMS', 'packages.tsv', 'builder-packages.tsv', 'toolchain.json', 'toolchain-versions.txt', 'workflow.json'):
            download('/work/output/'+name, output/name)
        verify_output(output, 'code-swarm-amd64.iso')
        shutil.copyfile(ROOT/'builder/lima.yaml', output/'builder-config.yaml')
        if recipe is not None:
            download('/work/output/source-sha256.json', output/'source-sha256.json')
        else:
            (output/'source-sha256.json').write_text(json.dumps({n: sha(p) for p,n in source_paths()}, indent=2)+'\n')
        print('Verified ISO and package manifests: '+str(output), flush=True)
    finally:
        command(['limactl', 'stop', VM])

def valid_key(key):
    return re.fullmatch(r'tskey-auth-[A-Za-z0-9_-]{16,256}', key) is not None

def verify_private_helpers():
    for name in ('personalize.py', 'firstboot.py', 'configure-firstboot.py'):
        result = shell('sudo', 'sha256sum', '/work/builder/'+name, capture_output=True, text=True)
        if result.stdout.split()[0] != sha(ROOT/'builder'/name):
            raise RuntimeError('Guest helper differs from current source. Rebuild the clean ISO before personalization.')

def personalize(output):
    doctor(output)
    print('PRIVATE ISO: the enrollment key is recoverable from the ISO and builder disk.\n'
          'Use a short-lived least-privilege auth key. One-off keys enroll one device; reusable keys enroll many.\n'
          'Revoke the key after use. Do not upload this ISO, VM, backups or private directory.\n'
          'This only enrolls Tailscale after installation; Codex still needs owner sign-in.', flush=True)
    if input('Type PRIVATE to accept and continue: ') != 'PRIVATE':
        raise RuntimeError('Cancelled without reading a key.')
    output = fresh_output(output)
    vm_ready()
    try:
        # No input is accepted until a completed clean build and compatible helper exist.
        shell('sudo', 'test', '-f', '/work/output/code-swarm-amd64.iso')
        shell('sudo', 'test', '-f', '/work/builder/personalize.py')
        verify_private_helpers()
        if not sys.stdin.isatty():
            raise RuntimeError('Private enrollment requires an interactive terminal; never pipe a key.')
        key = getpass.getpass('Tailscale auth key (hidden, never saved on the Mac): ')
        if not valid_key(key):
            raise RuntimeError('Expected an auth key, not an API/OAuth credential. Input was discarded.')
        # Only stdin carries the secret; no shell substitution, argv, env or log.
        shell('sudo', 'python3', '-I', '/work/builder/personalize.py', input=(key+'\n').encode())
        key = None
        for name in ('code-swarm-private-amd64.iso', 'SHA256SUMS'):
            download('/var/lib/code-swarm-private/output/'+name, output/name)
        verify_output(output, 'code-swarm-private-amd64.iso')
        shell('sudo', 'rm', '-rf', '/var/lib/code-swarm-private')
        print('Private ISO verified: '+str(output)+'\nRevoke the key after enrollment; deletion does not erase SSD/VM snapshots.', flush=True)
    finally:
        command(['limactl', 'stop', VM])

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['doctor', 'build', 'personalize', 'source-archive'])
    parser.add_argument('--output', type=Path, default=Path.home()/('CodeSwarm-'+time.strftime('%Y%m%d-%H%M%S')))
    parser.add_argument('--recipe', type=Path, help='Agent-created Markdown or JSON workflow recipe')
    args = parser.parse_args()
    if args.action == 'source-archive':
        if args.output.exists():
            raise RuntimeError('Archive output already exists.')
        archive(args.output, recipe=args.recipe)
    elif args.action == 'doctor':
        doctor(args.output)
    elif args.action == 'build':
        with builder_lock():
            build(args.output, recipe=args.recipe)
    else:
        with builder_lock():
            personalize(args.output)

if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, ValueError, OSError, subprocess.CalledProcessError, KeyboardInterrupt) as e:
        # Never include a CalledProcessError payload or captured output that might contain a secret.
        print('Stopped: '+(str(e) if isinstance(e, (RuntimeError, ValueError)) else type(e).__name__+'. See docs/MAC-BUILDER.md.'), file=sys.stderr)
        raise SystemExit(1)
