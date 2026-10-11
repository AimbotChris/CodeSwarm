#!/usr/bin/python3 -I
"""Explicit owner-run R6 UI patch. No service restarts, enrollment or permissions changes."""
import fcntl,hashlib,json,os,pathlib,stat,subprocess,sys,tempfile

TARGETS={'code-swarm-connect':'usr/local/bin/code-swarm-connect','code-swarm-tailscale-helper':'usr/local/libexec/code-swarm-tailscale-helper'}
BASELINE={'code-swarm-connect':'e9f20f895543258b7e004f8fb5d0862904df11a3e713c58e160249d1211754ed','code-swarm-tailscale-helper':'2c27205e7e0094b63e6467bb90e1332b637ea060c25fe58cfdd08440185eb5a0'}
BUNDLE=pathlib.Path(__file__).resolve().parent
BACKUP='var/lib/code-swarm/patches/connect-r7'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def secure_path(p):
 for q in [p,*p.parents]:
  if q.exists():
   s=q.lstat()
   if stat.S_ISLNK(s.st_mode) or s.st_uid!=0 or s.st_mode&0o022:raise RuntimeError('Target/control path is not root-protected')
def replace(p,data):
 fd,name=tempfile.mkstemp(prefix='.connect-r7-',dir=p.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
  os.chmod(name,0o755);os.replace(name,p)
 finally:
  if os.path.exists(name):os.unlink(name)
def change(root=pathlib.Path('/'),restore=False):
 # root injection is an internal test seam, not an installed CLI/environment option.
 expected=json.loads((BUNDLE/'payload-sha256.json').read_text());backup=root/BACKUP
 payload={n:BUNDLE/'payload'/n for n in TARGETS}
 for n,p in payload.items():
  if digest(p)!=expected[n]:raise RuntimeError('Patch payload checksum mismatch')
 for n,relative in TARGETS.items():
  p=root/relative;secure_path(p)
  if digest(p)!=(expected[n] if restore else BASELINE[n]):raise RuntimeError('Installed files do not match the expected version; no changes made')
 secure_path(backup.parent)
 if restore:
  secure_path(backup)
  for n in TARGETS:
   p=backup/n;secure_path(p)
   if digest(p)!=BASELINE[n]:raise RuntimeError('Saved original checksum mismatch')
 else:
  if backup.exists():raise RuntimeError('A prior patch backup exists; inspect it before proceeding')
  backup.mkdir(parents=True,mode=0o700)
  for n,relative in TARGETS.items():
   p=backup/n;p.write_bytes((root/relative).read_bytes());p.chmod(0o600)
 originals={n:(root/relative).read_bytes() for n,relative in TARGETS.items()}
 try:
  for n,relative in TARGETS.items():replace(root/relative,(backup/n if restore else payload[n]).read_bytes())
 except Exception:
  for n,relative in TARGETS.items():replace(root/relative,originals[n])
  raise
 print('Restored original R6 setup files.' if restore else 'Installed R7 setup files. Open Home → Connect Tailscale. No restart required.')
 print('Tailscale/account state, services, firewall, sudo and polkit policies were not changed. QR dependency remains installed on restore.')
def main():
 if os.geteuid()!=0:raise RuntimeError('Run this owner-approved patch with sudo')
 if sys.argv[1:] not in ([],['--restore']):raise RuntimeError('Usage: sudo python3 -I install.py [--restore]')
 for p in pathlib.Path('/proc').glob('[0-9]*/cmdline'):
  try:args=p.read_bytes().split(b'\0')
  except OSError:continue
  if b'/usr/local/bin/code-swarm-connect' in args or b'/usr/local/libexec/code-swarm-tailscale-helper' in args:raise RuntimeError('Close Connect Tailscale and finish/cancel setup before applying this patch')
 lock=pathlib.Path('/run/code-swarm-connect.lock');secure_path(lock)
 with lock.open('a') as f:
  os.chmod(lock,0o600)
  try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:raise RuntimeError('A setup attempt is active; close it first')
  if not sys.argv[1:]:
   # Dependency installation is a separate explicit owner step; never run apt automatically.
   try:import qrcode
   except ImportError:raise RuntimeError('Install the small signed Debian dependency first: sudo apt install python3-qrcode')
  change(restore=bool(sys.argv[1:]))
if __name__=='__main__':
 try:main()
 except Exception as e:print('Patch stopped:',str(e),file=sys.stderr);raise SystemExit(1)
