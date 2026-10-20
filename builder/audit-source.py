#!/usr/bin/env python3
"""Targeted source/artifact audit. Never print credential candidate values."""
import argparse
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = {'qa', 'vendor', 'build', 'output', 'private', 'cache', 'evidence', '__pycache__', '.aws', '.ssh'}
EXTENSIONS = {'.iso', '.qcow2', '.raw', '.img', '.deb', '.pyc', '.log', '.pem', '.key', '.tar', '.gz', '.tgz', '.zip'}
LIMIT = 2 * 1024 * 1024
PATTERNS = [rb'gh[pousr]_[A-Za-z0-9]{30,}', rb'github_pat_[A-Za-z0-9_]{30,}',
            rb'tskey-(?:auth|api|client)-[A-Za-z0-9_-]{16,}',
            rb'sk-(?:proj-|ant-)[A-Za-z0-9_-]{20,}',
            rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
            rb'https://login\.tailscale\.com/a/[A-Za-z0-9_-]{10,}']
FIXTURES = [b'tskey-auth-SYNTHETIC-NOT-A-REAL-KEY',
            b'https://login.tailscale.com/a/SYNTHETIC-NOT-A-REAL-LINK',
            b'https://login.tailscale.com/a/SYNTHETIC-ROTATED-LINK']


def git(*args, root=ROOT):
    return subprocess.check_output(['git', *args], cwd=root)


def inspect(name, data, mode='100644'):
    path = Path(name)
    if set(path.parts) & FORBIDDEN or path.suffix in EXTENSIONS or path.name.startswith('.env'):
        return 'forbidden runtime/artifact path'
    if mode not in {'100644', '100755'} or len(data) > LIMIT:
        return 'non-source file, symlink or oversized source'
    for fixture in FIXTURES:
        data = data.replace(fixture, b'SYNTHETIC_FIXTURE')
    if any(re.search(pattern, data) for pattern in PATTERNS):
        return 'credential-like data (value redacted)'
    if b'\0' in data and not (name.startswith('brand/') and path.suffix == '.png'):
        return 'unexpected binary data'
    return None


def entries(mode, root):
    if mode == 'working':
        names = set(git('ls-files', '--cached', '--others', '--exclude-standard', '-z', root=root).decode().split('\0'))
        for name in sorted(names - {''}):
            path = root / name
            if not path.exists() and not path.is_symlink():
                continue  # A deleted tracked file is absent from the working tree.
            if path.is_symlink() or not path.is_file():
                yield name, b'', '120000'
            elif path.stat().st_size > LIMIT:
                yield name, b'', 'oversized'
            else:
                yield name, path.read_bytes(), '100644'
        return
    refs = [None] if mode == 'index' else git('rev-list', '--all', root=root).decode().splitlines()
    seen = set()
    for ref in refs:
        listing = git('ls-files', '--stage', '-z', root=root) if ref is None else git('ls-tree', '-r', '-z', ref, root=root)
        for row in listing.split(b'\0'):
            if not row:
                continue
            metadata, name = row.decode().split('\t', 1)
            bits = metadata.split()
            filemode, oid = (bits[0], bits[1]) if ref is None else (bits[0], bits[2])
            if ref is None and bits[2] != '0':
                yield name, b'', 'unmerged'
                continue
            key = (name, filemode, oid)
            if key in seen:
                continue
            seen.add(key)
            if filemode not in {'100644', '100755'}:
                yield name, b'', filemode
            elif int(git('cat-file', '-s', oid, root=root)) > LIMIT:
                yield name, b'', 'oversized'
            else:
                yield name, git('cat-file', 'blob', oid, root=root), filemode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['working', 'index', 'history'], default='working')
    args = parser.parse_args()
    errors = []
    count = 0
    for name, data, mode in entries(args.mode, ROOT):
        count += 1
        problem = inspect(name, data, mode)
        if problem:
            errors.append(name + ': ' + problem)
    if not count:
        raise RuntimeError('No source files to audit')
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print(f'PASS: {args.mode}: {count} source entries; no targeted credential/artifact findings. Synthetic fixtures allowlisted.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
