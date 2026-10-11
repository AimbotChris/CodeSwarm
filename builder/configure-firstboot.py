"""Add dormant, opt-in enrollment code. Public image contains no auth key."""
from pathlib import Path
import shutil
root = Path('/work/build/config/includes.chroot')
p = root/'usr/local/libexec/code-swarm-firstboot'
p.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile('/work/builder/firstboot.py', p)
p.chmod(0o755)
p = root/'etc/systemd/system/code-swarm-firstboot.service'
p.write_text('''[Unit]
Description=Owner-selected installed-machine Tailscale enrollment
After=network-online.target
Wants=network-online.target
ConditionPathExists=/etc/code-swarm-enrollment/authkey
ConditionPathExists=/var/lib/code-swarm/admin-provisioned
ConditionPathExists=!/run/live/medium
[Service]
Type=oneshot
ExecStart=/usr/local/libexec/code-swarm-firstboot
TimeoutStartSec=360
UMask=0077
StandardOutput=null
StandardError=null
[Install]
WantedBy=multi-user.target
''')
p = root/'etc/systemd/system/multi-user.target.wants/code-swarm-firstboot.service'
p.parent.mkdir(parents=True, exist_ok=True)
p.symlink_to('../code-swarm-firstboot.service')


p = Path('/work/build/config/hooks/live/0990-clean-identity.hook.chroot')
p.write_text("""#!/bin/sh
set -eu
test ! -e /var/lib/tailscale/tailscaled.state
test ! -e /etc/code-swarm-enrollment/authkey
test ! -e /var/lib/code-swarm/admin-provisioned
: > /etc/machine-id
rm -f /var/lib/dbus/machine-id
ln -s /etc/machine-id /var/lib/dbus/machine-id
""")
p.chmod(0o755)
