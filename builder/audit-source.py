#!/usr/bin/env python3
"""Audit exactly Git's staged/tracked source; never print secret candidates."""
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
FORBIDDEN={'qa','vendor','build','output','private','cache','evidence','__pycache__','.aws','.ssh'}
EXTENSIONS={'.iso','.qcow2','.raw','.img','.deb','.pyc','.log','.pem','.key','.tar','.gz'}
PATTERNS=[rb'gh[pousr]_[A-Za-z0-9]{30,}', rb'github_pat_[A-Za-z0-9_]{30,}',
          rb'tskey-(?:auth|api|client)-[A-Za-z0-9_-]{16,}',
          rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
          rb'https://login\.tailscale\.com/a/[A-Za-z0-9_-]{10,}']
FIXTURES=[b'tskey-auth-SYNTHETIC-NOT-A-REAL-KEY',
          b'https://login.tailscale.com/a/SYNTHETIC-NOT-A-REAL-LINK',
          b'https://login.tailscale.com/a/SYNTHETIC-ROTATED-LINK']

def main():
    files=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    files=[n for n in files if n]
    if not files:raise RuntimeError('No staged/tracked files to audit')
    errors=[]
    for name in files:
        path=ROOT/name
        if set(path.relative_to(ROOT).parts)&FORBIDDEN or path.suffix in EXTENSIONS or path.name.startswith('.env'):
            errors.append(name+': forbidden runtime/artifact path');continue
        if path.is_symlink() or not path.is_file() or path.stat().st_size>2*1024*1024:
            errors.append(name+': non-source file');continue
        # Audit the exact staged bytes that would be committed, not merely working files.
        data=subprocess.check_output(['git','show',':'+name],cwd=ROOT)
        for fixture in FIXTURES:data=data.replace(fixture,b'SYNTHETIC_FIXTURE')
        if any(re.search(pattern,data) for pattern in PATTERNS):
            errors.append(name+': credential-like data (value redacted)')
        if b'\0' in data and not (name.startswith('brand/') and path.suffix=='.png'):
            errors.append(name+': unexpected binary data')
    if errors:
        print('\n'.join(errors),file=sys.stderr);return 1
    print(f'PASS: {len(files)} source files; no vendor binaries, runtime state or credential candidates found. Synthetic fixtures explicitly allowlisted.')
    return 0

if __name__=='__main__':raise SystemExit(main())
