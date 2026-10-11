"""R7 adds local QR generation; no auth/profile or host changes."""
from pathlib import Path
root=Path('/work/build')
for source,target in [('code-swarm-connect','usr/local/bin/code-swarm-connect'),('code-swarm-tailscale-helper','usr/local/libexec/code-swarm-tailscale-helper')]:
 p=root/'config/includes.chroot'/target;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(Path('/work/product',source).read_bytes());p.chmod(0o755)
p=root/'config/package-lists/desktop.list.chroot';s=p.read_text()
if 'python3-qrcode\n' not in s:p.write_text(s+'python3-qrcode\n')
