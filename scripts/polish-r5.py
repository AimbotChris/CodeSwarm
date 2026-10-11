"""Shared by configure.py and the bounded R5 revision build."""
from pathlib import Path
import shutil
root=Path('/work/build')
def put(path,text,mode=0o644):
 p=root/'config/includes.chroot'/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text);p.chmod(mode)
for name in ['code-swarm-session','code-swarm-home','code-swarm-status','code-swarm-status-broker']:
 put('usr/local/bin/'+name,Path('/work/product',name).read_text(),0o755)
put('usr/local/sbin/code-swarm-remote-setup',Path('/work/product/code-swarm-remote-setup').read_text(),0o755)
put('usr/share/code-swarm/REMOTE-ACCESS.md',Path('/work/product/REMOTE-ACCESS.md').read_text())
for name in ['server.py','static/index.html','static/app.js','static/state.js','static/style.css','static/brand.svg','offline-inventory.html','README.md']:
 put('usr/share/code-swarm/fleet/'+name,Path('/work/fleet',name).read_text())
brand=root/'config/includes.chroot/usr/share/code-swarm/brand';brand.mkdir(parents=True,exist_ok=True)
for name in ['code-swarm-mark.svg','code-swarm-mark.png']:shutil.copy2(Path('/work/brand',name),brand/name)
put('etc/systemd/journald.conf.d/50-code-swarm.conf','''[Journal]
SystemMaxUse=128M
SystemKeepFree=512M
RuntimeMaxUse=32M
MaxRetentionSec=7day
RateLimitIntervalSec=30s
RateLimitBurst=1000
''')
put('etc/systemd/user/code-swarm-vnc.service','''[Unit]
Description=Approved same-session Code Swarm desktop
ConditionPathExists=/etc/codex-remote/enabled
ConditionPathExists=%h/.vnc/passwd
StartLimitIntervalSec=300
StartLimitBurst=4
[Service]
ExecCondition=/bin/sh -c 'test "$(cat /etc/codex-remote/owner)" = "$(id -un)"'
ExecCondition=/bin/sh -c 'test "$(cat /etc/codex-remote/access-model)" = session'
ExecStart=/usr/bin/x0tigervncserver -fg -localhost=1 -rfbport=5900 -PasswordFile=%h/.vnc/passwd -SecurityTypes=VncAuth -AlwaysShared=1
Restart=on-failure
RestartSec=15
NoNewPrivileges=true
''')
put('etc/systemd/user/code-swarm-status.service','''[Unit]
Description=Approved read-only worker telemetry on loopback
ConditionPathExists=/etc/codex-remote/enabled
StartLimitIntervalSec=300
StartLimitBurst=4
[Service]
ExecCondition=/bin/sh -c 'test "$(cat /etc/codex-remote/owner)" = "$(id -un)"'
ExecStart=/usr/local/bin/code-swarm-status
Restart=on-failure
RestartSec=15
NoNewPrivileges=true
''')
put('etc/systemd/user/code-swarm-fleet.service','''[Unit]
Description=Read-only local Code Swarm workers console
[Service]
ExecStart=/usr/bin/python3 /usr/share/code-swarm/fleet/server.py
NoNewPrivileges=true
MemoryMax=128M
CPUQuota=25%
''')
put('etc/systemd/system/code-swarm-status-broker.service','''[Unit]
Description=Approved worker status, including pre-login readiness
ConditionPathExists=/etc/codex-remote/enabled
After=systemd-logind.service
[Service]
User=code-swarm-status
Group=code-swarm-status
ExecStart=/usr/local/bin/code-swarm-status-broker
Restart=on-failure
RestartSec=15
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
MemoryMax=64M
CPUQuota=10%
[Install]
WantedBy=multi-user.target
''')
hook=root/'config/hooks/live/0940-status-account.hook.chroot'
hook.write_text('#!/bin/sh\nset -eu\ngetent passwd code-swarm-status >/dev/null || useradd --system --no-create-home --home-dir /nonexistent --shell /usr/sbin/nologin code-swarm-status\n')
hook.chmod(0o755)
put('etc/systemd/system/code-swarm-greeter-vnc.service','''[Unit]
Description=Explicitly approved authenticated physical greeter and desktop sharing
ConditionPathExists=/etc/codex-remote/enabled
ConditionPathExists=/etc/codex-remote/greeter.passwd
After=display-manager.service
StartLimitIntervalSec=300
StartLimitBurst=10
[Service]
ExecCondition=/bin/sh -c 'test "$(cat /etc/codex-remote/access-model)" = greeter'
Environment=XAUTHORITY=/run/lightdm/root/:0
Environment=HOME=/run/code-swarm-greeter
RuntimeDirectory=code-swarm-greeter
ExecStart=/usr/bin/x0tigervncserver -fg -display :0 -localhost=1 -rfbport=5900 -PasswordFile=/etc/codex-remote/greeter.passwd -SecurityTypes=VncAuth -AlwaysShared=1
Restart=always
RestartSec=15
NoNewPrivileges=true
CapabilityBoundingSet=
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
[Install]
WantedBy=graphical.target
''')
# Replace the obsolete fixed-account system service with a disabled tombstone.
put('etc/systemd/system/codex-vnc.service','''[Unit]
Description=Obsolete fixed-account service; use owner-session code-swarm-vnc
ConditionPathExists=/this-service-is-not-used
[Service]
Type=oneshot
ExecStart=/bin/false
''')
put('etc/nginx/sites-available/codex-remote','''server {
 listen 127.0.0.1:6080;
 server_name _;
 access_log off;
 error_log stderr warn;
 auth_basic "Code Swarm OS desktop";
 auth_basic_user_file /etc/codex-remote/web.htpasswd;
 root /usr/share/novnc;
 index vnc.html;
 add_header X-Frame-Options DENY always;
 add_header X-Content-Type-Options nosniff always;
 location = /code-swarm-status {
  auth_basic off;
  proxy_pass http://127.0.0.1:9071/status;
  proxy_connect_timeout 2s;
  proxy_read_timeout 5s;
 }
 location /websockify {
  proxy_pass http://127.0.0.1:6081;
  proxy_http_version 1.1;
  proxy_set_header Upgrade $http_upgrade;
  proxy_set_header Connection "upgrade";
  proxy_read_timeout 3600;
 }
}
''')
