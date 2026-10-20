#!/usr/bin/env python3
"""Fetch and stage only the reviewed amd64 inputs in config/toolchain.json."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import shutil
import subprocess
import tarfile


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verified(source, item):
    path = source / 'vendor' / item['file']
    if digest(path) != item['sha256']:
        raise RuntimeError('Toolchain checksum mismatch: ' + item['name'])
    return path


def selected_manifest(source):
    selection = runpy.run_path(str(source / 'builder/recipe.py'))['load'](source)
    manifest = json.loads((source / 'config/toolchain.json').read_text())
    selected = set(selection['tools'])
    def included(item):
        owner = {'t3-code': 't3', 'codex-license': 'codex', 'codex-notice': 'codex',
                 'opencode-license': 'opencode'}.get(item['name'], item['name'])
        # Unknown notices stay with the source's reviewed bundle; never execute them.
        return owner in selected or (item['kind'] == 'notice' and owner not in {'codex', 'opencode'})
    return {**manifest, 'inputs': [item for item in manifest['inputs'] if included(item)]}


def fetch(source, cache):
    cache.mkdir(parents=True, exist_ok=True)
    (source / 'vendor').mkdir(exist_ok=True)
    for item in selected_manifest(source)['inputs']:
        path = cache / item['file']
        if not path.exists() or digest(path) != item['sha256']:
            part = path.with_name(path.name + '.part')
            subprocess.run(['curl', '--proto', '=https', '--proto-redir', '=https',
                            '--tlsv1.2', '-fL', '--retry', '3', item['url'], '-o', str(part)], check=True)
            if digest(part) != item['sha256']:
                part.unlink()
                raise RuntimeError('Toolchain checksum mismatch: ' + item['name'])
            part.replace(path)
        shutil.copy2(path, source / 'vendor' / item['file'])


def extract(archive, destination):
    # Reject links/devices and traversal before extracting any archive member.
    with tarfile.open(archive) as tar:
        members = tar.getmembers()
        for member in members:
            path = Path(member.name)
            if path.is_absolute() or '..' in path.parts or not (member.isfile() or member.isdir()):
                raise RuntimeError('Unsafe toolchain archive member')
        destination.mkdir(parents=True, exist_ok=True)
        tar.extractall(destination, members=members, filter='data')


def stage(source, build):
    manifest = selected_manifest(source)
    if manifest['architecture'] != 'amd64':
        raise RuntimeError('Only amd64 toolchain inputs are qualified')
    # Validate every input before writing the image tree.
    paths = [(item, verified(source, item)) for item in manifest['inputs']]
    root = build / 'config/includes.chroot'
    for item, archive in paths:
        if item['kind'] == 'notice':
            notices = root / 'usr/share/doc/code-swarm/vendor'
            notices.mkdir(parents=True, exist_ok=True)
            shutil.copy2(archive, notices / item['file'])
            continue
        if item['kind'] == 'deb':
            packages = build / 'config/packages.chroot'
            packages.mkdir(parents=True, exist_ok=True)
            shutil.copy2(archive, packages / item['file'])
            continue
        dest = root / 'opt/code-swarm/tools' / item['name']
        if dest.exists():
            raise RuntimeError('Refusing to overwrite staged tool: ' + item['name'])
        extract(archive, dest)
        member = {'codex': 'bin/codex', 'claude': 'package/claude', 'opencode': 'opencode'}[item['name']]
        executable = dest / member
        if not executable.is_file():
            raise RuntimeError('Missing tool executable: ' + item['name'])
        executable.chmod(0o755)
        link = root / 'usr/local/bin' / item['name']
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to('/' + str(executable.relative_to(root)))
    target = root / 'usr/share/code-swarm/toolchain.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['fetch', 'stage'])
    parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--cache', type=Path, default=Path('/var/cache/code-swarm-inputs'))
    parser.add_argument('--build', type=Path, default=Path('/work/build'))
    args = parser.parse_args()
    if args.action == 'fetch':
        fetch(args.source, args.cache)
    else:
        stage(args.source, args.build)
