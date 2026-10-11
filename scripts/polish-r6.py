"""R6 image-only configuration: ordinary admin access and owner-approved setup."""
from pathlib import Path
root=Path('/work/build')
def put(name,text,mode=0o644):
 p=root/'config/includes.chroot'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text);p.chmod(mode)
for name in ['code-swarm-home','code-swarm-session','code-swarm-connect']:
 put('usr/local/bin/'+name,Path('/work/product',name).read_text(),0o755)
put('usr/local/libexec/code-swarm-tailscale-helper',Path('/work/product/code-swarm-tailscale-helper').read_text(),0o755)
put('usr/share/polkit-1/actions/com.codeswarm.connect.policy','''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE policyconfig PUBLIC "-//freedesktop//DTD PolicyKit Policy Configuration 1.0//EN" "http://www.freedesktop.org/standards/PolicyKit/1/policyconfig.dtd">
<policyconfig><vendor>Code Swarm OS</vendor><action id="com.codeswarm.connect">
<description>Connect this computer to Tailscale</description>
<message>Enter your local administrator password to enable Tailscale and begin browser sign-in.</message>
<defaults><allow_any>no</allow_any><allow_inactive>no</allow_inactive><allow_active>auth_admin</allow_active></defaults>
<annotate key="org.freedesktop.policykit.exec.path">/usr/local/libexec/code-swarm-tailscale-helper</annotate>
</action></policyconfig>
''')
p=root/'config/package-lists/desktop.list.chroot';lines=p.read_text().splitlines()
for package in ('sudo','lxpolkit'):
 if package not in lines:lines.append(package)
p.write_text('\n'.join(lines)+'\n')
put('etc/sudoers.d/10-code-swarm-admin','''# Normal password authentication for installer-created administrators.
Defaults authenticate
%sudo ALL=(ALL:ALL) ALL
''',0o440)
p=root/'config/hooks/live/0945-admin-required.hook.chroot';p.write_text('''#!/bin/sh
set -eu
apt-mark manual sudo lxpolkit
test -x /usr/bin/sudo
visudo -c
''');p.chmod(0o755)
