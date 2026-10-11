from pathlib import Path
import shutil
root=Path('/work/build')
def put(path,text,mode=0o644):
 p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text);p.chmod(mode)
p=root/'config/includes.chroot/usr/share/keyrings';p.mkdir(parents=True,exist_ok=True)
shutil.copy2('/work/vendor/tailscale-archive-keyring.gpg',p/'tailscale-archive-keyring.gpg')
put('config/includes.chroot/etc/apt/sources.list.d/tailscale.list',Path('/work/vendor/tailscale.list').read_text())
put('config/hooks/live/0850-remote.hook.chroot','''#!/bin/sh
set -eu
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends tailscale tigervnc-scraping-server tigervnc-tools novnc websockify nginx-light apache2-utils i3lock
systemctl disable tailscaled nginx
# Remote services are never enabled or enrolled by the image.
rm -f /etc/nginx/sites-enabled/default
mkdir -p /etc/codex-remote
chmod 0750 /etc/codex-remote
chown root:www-data /etc/codex-remote
''',0o755)
put('config/includes.chroot/etc/nginx/sites-available/codex-remote','''server {
 listen 127.0.0.1:6080;
 server_name _;
 auth_basic "Agent desktop";
 auth_basic_user_file /etc/codex-remote/web.htpasswd;
 root /usr/share/novnc;
 index vnc.html;
 add_header X-Frame-Options DENY always;
 add_header X-Content-Type-Options nosniff always;
 location /websockify {
  proxy_pass http://127.0.0.1:6081;
  proxy_http_version 1.1;
  proxy_set_header Upgrade $http_upgrade;
  proxy_set_header Connection "upgrade";
  proxy_read_timeout 3600;
 }
}
''')
put('config/includes.chroot/etc/systemd/system/codex-vnc.service','''[Unit]
Description=Opt-in shared physical Xorg desktop
ConditionPathExists=/etc/codex-remote/enabled
ConditionPathExists=/home/chris/.vnc/passwd
After=display-manager.service
[Service]
User=chris
Environment=XAUTHORITY=/home/chris/.Xauthority
ExecStart=/usr/bin/x0tigervncserver -fg -display :0 -localhost=1 -rfbport=5900 -PasswordFile=/home/chris/.vnc/passwd -SecurityTypes=VncAuth -AlwaysShared=1
Restart=on-failure
RestartSec=15
NoNewPrivileges=true
[Install]
WantedBy=graphical.target
''')
put('config/includes.chroot/etc/systemd/system/codex-websockify.service','''[Unit]
Description=Opt-in localhost browser-to-VNC bridge
ConditionPathExists=/etc/codex-remote/enabled
After=codex-vnc.service
[Service]
User=www-data
ExecStart=/usr/bin/websockify 127.0.0.1:6081 127.0.0.1:5900
Restart=on-failure
RestartSec=10
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
[Install]
WantedBy=multi-user.target
''')
