#!/usr/bin/python3 -I
"""Private remaster of a clean locally-built ISO; secret arrives only on stdin."""
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

BASE = Path('/work/output/code-swarm-amd64.iso')
WORK = Path('/var/lib/code-swarm-private')
MARKER = Path('/etc/code-swarm-builder')
FIRSTBOOT = Path('/work/builder/firstboot.py')

def digest(path, algorithm='sha256'):
    h = hashlib.new(algorithm)
    with path.open('rb') as f:
        for block in iter(lambda: f.read(4*1024*1024), b''):
            h.update(block)
    return h.hexdigest()

def run(args):
    subprocess.run(args, check=True, stdin=subprocess.DEVNULL,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def patch_checksums(text, changes, algorithm):
    lines = []
    seen = set()
    for line in text.splitlines():
        parts = line.split(None, 1)
        if len(parts) != 2:
            raise RuntimeError('Invalid checksum manifest')
        name = parts[1].lstrip('*')
        name = name[2:] if name.startswith('./') else name
        if name in changes:
            line = digest(changes[name], algorithm)+'  ./'+name
            seen.add(name)
        lines.append(line)
    for name in sorted(set(changes)-seen):
        lines.append(digest(changes[name], algorithm)+'  ./'+name)
    return '\n'.join(lines)+'\n'

def main():
    assert os.geteuid() == 0
    assert MARKER.read_text().strip() == 'codeswarm-builder-v1'
    assert not WORK.exists() and not WORK.is_symlink(), 'Private work already exists; owner review required'
    assert digest(BASE) == (BASE.parent/'SHA256SUMS').read_text().split()[0]
    key = sys.stdin.buffer.read(512).strip()
    assert re.fullmatch(rb'tskey-auth-[A-Za-z0-9_-]{16,256}', key)
    os.umask(0o077)
    WORK.mkdir(mode=0o700)
    try:
        original = WORK/'original.squashfs'
        run(['xorriso','-osirrox','on','-indev',str(BASE),'-extract','/live/filesystem.squashfs',str(original),
             '-extract','/md5sum.txt',str(WORK/'md5sum.txt')])
        fs = WORK/'rootfs'
        run(['unsquashfs','-processors','2','-d',str(fs),str(original)])
        assert not (fs/'var/lib/tailscale/tailscaled.state').exists()
        assert not (fs/'var/lib/code-swarm/admin-provisioned').exists()
        assert not (fs/'etc/code-swarm-enrollment').exists()
        assert not (fs/'etc/machine-id').read_bytes().strip()
        assert digest(fs/'usr/local/libexec/code-swarm-firstboot') == digest(FIRSTBOOT)
        folder = fs/'etc/code-swarm-enrollment'
        folder.mkdir(mode=0o700)
        (folder/'authkey').write_bytes(key+b'\n')
        (folder/'authkey').chmod(0o600)
        key = None
        squash = WORK/'filesystem.squashfs'
        run(['mksquashfs',str(fs),str(squash),'-noappend','-comp','zstd','-Xcompression-level','3','-processors','2','-mem','1G'])
        size = WORK/'filesystem.size'
        size.write_text(subprocess.check_output(['du','-sx','--block-size=1',str(fs)],text=True).split()[0]+'\n')
        changes = {'live/filesystem.squashfs':squash, 'live/filesystem.size':size}
        manifest = WORK/'md5sum.txt'
        manifest.write_text(patch_checksums(manifest.read_text(), changes, 'md5'))
        manifests = {'md5sum.txt':manifest}
        sha_manifest = WORK/'sha256sum.txt'
        # Some live-build revisions also carry a SHA256 file inventory.
        extracted = subprocess.run(['xorriso','-osirrox','on','-indev',str(BASE),'-extract',
                                    '/sha256sum.txt',str(sha_manifest)], stdin=subprocess.DEVNULL,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if sha_manifest.exists():
            assert extracted.returncode == 0
            sha_manifest.write_text(patch_checksums(sha_manifest.read_text(), changes, 'sha256'))
            manifests['sha256sum.txt'] = sha_manifest
        output = WORK/'output'; output.mkdir(mode=0o700)
        iso = output/'code-swarm-private-amd64.iso'
        args = ['xorriso','-indev',str(BASE),'-outdev',str(iso),'-boot_image','any','replay']
        for name,path in {**changes,**manifests}.items():
            args += ['-map',str(path),'/'+name]
        run(args+['-commit','-end'])
        iso.chmod(0o600)
        (output/'SHA256SUMS').write_text(digest(iso)+'  '+iso.name+'\n')
        # Remove extracted secret-bearing trees. SSD/VM snapshots still require revocation.
        for p in WORK.iterdir():
            if p != output:
                shutil.rmtree(p) if p.is_dir() else p.unlink()
    except BaseException:
        # Fail closed, remove partial artifacts; do not print exception/secret payloads.
        shutil.rmtree(WORK)
        raise

if __name__ == '__main__':
    try:
        main()
    except BaseException:
        print('Private remaster failed; no enrollment was attempted. Review builder state and revoke the key if needed.', file=sys.stderr)
        raise SystemExit(1)
