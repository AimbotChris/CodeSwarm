"""Run explicitly as root only in a disposable test container with xorriso/squashfs.
Tiny nonbootable fixture; no Tailscale daemon or network operation is invoked.
"""
import hashlib
import importlib.util
import io
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
assert os.geteuid()==0, 'Use a disposable root test container, never sudo on your host'
spec=importlib.util.spec_from_file_location('personalize',ROOT/'builder/personalize.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
fake=b'tskey-auth-SYNTHETIC-NOT-A-REAL-KEY'
with tempfile.TemporaryDirectory(prefix='codeswarm-synthetic-') as temp:
    top=Path(temp);fs=top/'root';iso_tree=top/'iso';(iso_tree/'live').mkdir(parents=True)
    for directory in ['etc','usr/local/libexec','var/lib/code-swarm']:(fs/directory).mkdir(parents=True)
    (fs/'etc/machine-id').write_text('')
    shutil.copyfile(ROOT/'builder/firstboot.py',fs/'usr/local/libexec/code-swarm-firstboot')
    m.run(['mksquashfs',str(fs),str(iso_tree/'live/filesystem.squashfs'),'-noappend','-processors','1'])
    (iso_tree/'live/filesystem.size').write_text('0\n')
    for file,alg in [('md5sum.txt','md5'),('sha256sum.txt','sha256')]:
        (iso_tree/file).write_text(''.join(m.digest(iso_tree/name,alg)+'  ./'+name+'\n' for name in ['live/filesystem.squashfs','live/filesystem.size']))
    m.BASE=top/'code-swarm-amd64.iso';m.WORK=top/'private'
    m.MARKER=top/'marker';m.MARKER.write_text('codeswarm-builder-v1\n')
    m.FIRSTBOOT=ROOT/'builder/firstboot.py'
    m.run(['xorriso','-as','mkisofs','-r','-o',str(m.BASE),str(iso_tree)])
    original=m.digest(m.BASE)
    (top/'SHA256SUMS').write_text(original+'  '+m.BASE.name+'\n')
    m.sys.stdin=SimpleNamespace(buffer=io.BytesIO(fake+b'\n'))
    m.main()
    assert m.digest(m.BASE)==original
    output=m.WORK/'output';private_iso=output/'code-swarm-private-amd64.iso'
    assert private_iso.stat().st_mode&0o777==0o600
    assert m.WORK.stat().st_mode&0o777==0o700
    assert list(m.WORK.iterdir())==[output], 'No extracted private tree may remain'
    extracted=top/'extracted'
    m.run(['xorriso','-osirrox','on','-indev',str(private_iso),'-extract','/',str(extracted)])
    private_fs=top/'private-root'
    m.run(['unsquashfs','-processors','1','-d',str(private_fs),str(extracted/'live/filesystem.squashfs')])
    key=private_fs/'etc/code-swarm-enrollment/authkey'
    assert key.read_bytes()==fake+b'\n'
    assert key.stat().st_uid==0 and key.stat().st_mode&0o777==0o600
    assert key.parent.stat().st_mode&0o777==0o700
    assert not (fs/'etc/code-swarm-enrollment').exists()
    for filename,algorithm in [('md5sum.txt','md5'),('sha256sum.txt','sha256')]:
        for line in (extracted/filename).read_text().splitlines():
            expected,name=line.split();assert m.digest(extracted/name,algorithm)==expected
    print('PASS: tiny synthetic remaster, unchanged clean ISO, root-only key, private output permissions, both checksum manifests, temporary private-tree cleanup. No boot or enrollment tested.')
