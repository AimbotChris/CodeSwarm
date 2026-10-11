from pathlib import Path
import os
root=Path('/work/build')
def put(name,content,mode=0o644):
 p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content);p.chmod(mode)
put('config/hooks/live/0960-installer-only.hook.binary','''#!/bin/sh
set -eu
if [ -d binary/isolinux ]; then cd binary; fi
cp /work/config/installer-only/isolinux.cfg isolinux/isolinux.cfg
cp /work/config/installer-only/grub.cfg boot/grub/grub.cfg
cp /work/config/installer-only/grub.cfg boot/grub/loopback.cfg
''',0o755)
put('auto/config','''#!/bin/sh
set -eu
lb config noauto --mode debian --distribution trixie --architectures amd64 \\
 --build-with-chroot false --binary-images iso-hybrid --debian-installer live --debian-installer-gui false \\
 --archive-areas "main contrib non-free-firmware" --apt-recommends false \\
 --mirror-bootstrap https://deb.debian.org/debian/ --mirror-chroot https://deb.debian.org/debian/ \\
 --mirror-binary https://deb.debian.org/debian/ --security true --updates true \\
 --bootappend-live "boot=live components username=chris hostname=codex-thin-client noswap noeject live-config.noroot" \\
 --iso-application "Chris Codex Thin Client Prototype" \\
 --memtest none --chroot-squashfs-compression-type zstd \\
 --chroot-squashfs-compression-level 3 "$@"
''',0o755)
put('config/package-lists/desktop.list.chroot','''linux-image-amd64
chatgpt
live-boot
live-config
live-config-systemd
user-setup
sudo
lxpolkit
locales
python3-xdg
systemd-sysv
xserver-xorg
xinit
openbox
lightdm
lightdm-gtk-greeter
dbus-user-session
gnome-keyring
libpam-gnome-keyring
libsecret-tools
firefox-esr
xdg-utils
desktop-file-utils
xterm
network-manager
network-manager-gnome
polkitd
pkexec
fonts-dejavu
ca-certificates
curl
openssl
python3
python3-apt
git
pciutils
usbutils
firmware-linux-free
firmware-realtek
firmware-iwlwifi
alsa-utils
pulseaudio
''')
mime_defaults='''[Default Applications]
x-scheme-handler/http=firefox-esr.desktop
x-scheme-handler/https=firefox-esr.desktop
text/html=firefox-esr.desktop
application/xhtml+xml=firefox-esr.desktop
x-scheme-handler/codex=chatgpt.desktop
'''
put('config/includes.chroot/etc/xdg/mimeapps.list',mime_defaults)
put('config/includes.chroot/etc/skel/.config/mimeapps.list',mime_defaults)
put('config/hooks/live/0880-browser-handlers.hook.chroot','''#!/bin/sh
set -eu
update-desktop-database /usr/share/applications
''',0o755)
put('config/includes.chroot/etc/lightdm/lightdm.conf.d/50-codex.conf','''[Seat:*]
autologin-user=chris
autologin-user-timeout=0
user-session=openbox
autologin-session=openbox
''')
put('config/includes.chroot/etc/xdg/openbox/autostart','''systemctl --user import-environment DISPLAY XAUTHORITY DBUS_SESSION_BUS_ADDRESS
dbus-update-activation-environment --systemd DISPLAY XAUTHORITY
gnome-keyring-daemon --start --components=secrets
systemctl --user start codex-desktop.service
nm-applet &
''',0o755)
# Authenticate encrypted Secret Service before the app can cover its prompt.
put('config/includes.chroot/usr/local/libexec/codex-session-start','''#!/bin/sh
set -eu
if ! printf '%s' 'non-secret readiness marker' | secret-tool store --label='Codex desktop keyring readiness' application codex-prototype purpose startup-readiness; then
 echo 'Keyring setup/unlock was cancelled or failed. Use Start ChatGPT to retry.' >&2
 exit 0
fi
exec /usr/bin/chatgpt --ozone-platform=x11
''',0o755)
(root/'config/hooks/live/0920-keyring-dialog.hook.chroot').unlink(missing_ok=True)
put('config/includes.chroot/etc/systemd/user/codex-desktop.service','''[Unit]
Description=Official ChatGPT desktop with bounded crash recovery
StartLimitIntervalSec=300
StartLimitBurst=4
ConditionPathExists=!/run/codex-maintenance
[Service]
ExecStart=/usr/local/libexec/codex-session-start
Restart=on-failure
RestartSec=10
RestartSteps=4
RestartMaxDelaySec=60
TimeoutStopSec=60
KillMode=control-group
''')
put('config/includes.chroot/etc/xdg/openbox/menu.xml','''<?xml version="1.0" encoding="UTF-8"?>
<openbox_menu xmlns="http://openbox.org/3.4/menu"><menu id="root-menu" label="Recovery">
<item label="Start ChatGPT"><action name="Execute"><command>systemctl --user start codex-desktop</command></action></item>
<item label="Stop ChatGPT"><action name="Execute"><command>systemctl --user stop codex-desktop</command></action></item>
<item label="Reset crash limit and start"><action name="Execute"><command>sh -c 'systemctl --user reset-failed codex-desktop; systemctl --user start codex-desktop'</command></action></item>
<item label="Recovery terminal"><action name="Execute"><command>xterm</command></action></item>
<item label="Browser / sign in"><action name="Execute"><command>firefox</command></action></item>
<item label="Log out"><action name="Exit"/></item>
</menu></openbox_menu>
''')
put('config/includes.chroot/etc/apt/apt.conf.d/99approval-only','''APT::Periodic::Enable "0";
APT::Periodic::Unattended-Upgrade "0";
APT::Get::AllowUnauthenticated "false";
Acquire::AllowInsecureRepositories "false";
''')
put('config/hooks/live/0900-safety.hook.chroot','''#!/bin/sh
set -eu
# No live sudo or fixed password survives. Installer asks for real credentials.
rm -f /etc/sudoers.d/live
mkdir -p /var/lib/codex-control
chmod 0700 /var/lib/codex-control
systemctl mask apt-daily-upgrade.service apt-daily-upgrade.timer
systemctl enable codex-stage.timer
# Retain authenticated repository metadata and exact installed package inventory.
mkdir -p /usr/share/codex-prototype
dpkg-query -W -f='${Package}\\t${Version}\\t${Architecture}\\n' > /usr/share/codex-prototype/packages.tsv
apt-get update
apt-cache policy chatgpt > /usr/share/codex-prototype/chatgpt-policy.txt
''',0o755)
put('config/includes.chroot/etc/systemd/system/codex-stage.service','''[Unit]
Description=Stage signed update proposal only; never install
ConditionPathExists=/etc/codex-control/enrolled
[Service]
Type=oneshot
ExecStart=/usr/local/sbin/codex-stage
Nice=15
CPUQuota=25%
MemoryMax=512M
IOSchedulingClass=idle
UMask=0077
''')
put('config/includes.chroot/etc/systemd/system/codex-stage.timer','''[Unit]
Description=Daily approval-gated update proposal
[Timer]
OnBootSec=15min
OnUnitActiveSec=1d
RandomizedDelaySec=1h
Persistent=true
[Install]
WantedBy=timers.target
''')
# Package bytes are pinned; no silent latest download during the build.
p=root/'config/packages.chroot';p.mkdir(parents=True,exist_ok=True)
import shutil
shutil.copy2('/work/vendor/chatgpt_amd64.deb',p/'chatgpt_amd64.deb')
shutil.copy2('/work/scripts/codex-stage',root/'config/includes.chroot/usr/local/sbin/codex-stage') if (root/'config/includes.chroot/usr/local/sbin').exists() else None
put('config/includes.chroot/usr/local/sbin/codex-stage',Path('/work/scripts/codex-stage').read_text(),0o750)
put('config/includes.chroot/usr/local/sbin/codex-control',Path('/work/scripts/codex-control').read_text(),0o750)

# Remove Debian Live default password; retain local graphical autologin.
p=root/"config/hooks/live/0900-safety.hook.chroot"
p.write_text(p.read_text().replace("rm -f /etc/sudoers.d/live\n", "rm -f /etc/sudoers.d/live\n" + 'sed -i \'s/^\\t_PASSWORD=.*/\\t_PASSWORD="!"/\' /usr/lib/live/config/0030-user-setup\n'))
exec(Path('/work/scripts/add-remote.py').read_text())


put("config/rootfs/excludes", "var/lib/apt/lists/*\n")
put("config/hooks/live/0950-boot-timeout.hook.binary", "#!/bin/sh\nset -eu\nif [ -d binary/isolinux ]; then cd binary; fi\nsed -i -E 's/^timeout .*/timeout 50/' isolinux/isolinux.cfg\nsed -i '/^set timeout=/d' boot/grub/config.cfg\nprintf '\\nset timeout=5\\n' >> boot/grub/config.cfg\n# Keep hook-installed remote packages on the installed system.\n: > live/filesystem.packages-remove\n",0o755)
# Code Swarm OS installed session: no account name is assumed.
put('config/includes.chroot/etc/lightdm/lightdm.conf.d/50-codex.conf','''[Seat:*]
user-session=code-swarm
greeter-hide-users=false
''')
put('config/includes.chroot/usr/share/xsessions/code-swarm.desktop','''[Desktop Entry]
Name=Code Swarm OS
Comment=Codex worker with visible recovery controls
Exec=/usr/local/bin/code-swarm-session
Type=Application
DesktopNames=OPENBOX
''')
for name in ['code-swarm-session','code-swarm-home','code-swarm-inventory']:
 put('config/includes.chroot/usr/local/bin/'+name,Path('/work/product/'+name).read_text(),0o755)
put('config/includes.chroot/usr/local/libexec/codex-session-start',Path('/work/product/codex-session-start').read_text(),0o755)
p=root/'config/package-lists/desktop.list.chroot';p.write_text(p.read_text()+'python3-tk\nx11-utils\n')
put('config/includes.chroot/etc/issue','Code Swarm OS — powered by Debian GNU/Linux 13\\n \\l\n')
put('config/includes.chroot/etc/lightdm/lightdm-gtk-greeter.conf.d/60-code-swarm.conf','''[greeter]
background=#14252b
font-name=DejaVu Sans 12
indicators=~host;~session;~power
''')
p=root/'config/includes.chroot/etc/xdg/openbox/autostart';p.write_text(p.read_text().replace('gnome-keyring-daemon --start --components=secrets\n',''))
p=root/'auto/config';p.write_text(p.read_text().replace('Chris Codex Thin Client Prototype','Code Swarm OS — Debian 13'))

for name in ['code-swarm.cfg','code-swarm-prepare.sh','code-swarm-disks.sh','code-swarm-hostname.sh','code-swarm-apt.py','code-swarm-admin.sh']:
 put('config/includes.binary/'+name,Path('/work/config/installer-only/'+name).read_text(),0o644)

# Avoid racing LightDM's PAM keyring initialization with user Secret Service startup.
# Password authentication/account/session controls remain Debian's defaults.
put('config/hooks/live/0930-keyring-session.hook.chroot',"""#!/bin/sh
set -eu
sed -i '/pam_gnome_keyring.so/d' /etc/pam.d/lightdm
grep -q '@include common-auth' /etc/pam.d/lightdm
""",0o755)
exec(Path('/work/scripts/polish-r5.py').read_text())

exec(Path('/work/scripts/polish-r6.py').read_text())

exec(Path('/work/scripts/polish-r7.py').read_text())
