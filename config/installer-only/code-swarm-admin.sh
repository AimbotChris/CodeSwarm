#!/bin/sh
# Installer-only: fail closed if the chosen owner cannot administer the target.
set -eu
. /usr/share/debconf/confmodule
db_get passwd/username
owner=$RET
case "$owner" in ''|*[!a-zA-Z0-9_.-]*|-*) echo 'Invalid installer owner' >&2; exit 1;; esac
[ -d /target/etc ]
chroot /target /usr/bin/python3 - "$owner" <<'PY'
import pwd,subprocess,sys,pathlib
owner=sys.argv[1];entry=pwd.getpwnam(owner)
assert 1000 <= entry.pw_uid < 60000, 'Installer owner must be an ordinary account'
assert pathlib.Path('/usr/bin/sudo').is_file(), 'Required sudo package is missing'
assert subprocess.check_output(['dpkg-query','-W','-f=${Status}','sudo'],text=True)=='install ok installed'
assert subprocess.check_output(['passwd','-S',owner],text=True).split()[1]=='P', 'Owner must have a password'
subprocess.run(['usermod','-aG','sudo',owner],check=True)
# Disable password-based root login; keep recovery an explicit owner operation.
subprocess.run(['passwd','-l','root'],check=True,stdout=subprocess.DEVNULL)
assert subprocess.check_output(['passwd','-S','root'],text=True).split()[1]=='L'
subprocess.run(['visudo','-c'],check=True)
assert 'sudo' in subprocess.check_output(['id','-nG',owner],text=True).split()
# Debian's standard sudo policy: no passwordless rule is created.
policy=pathlib.Path('/etc/sudoers').read_text()
assert '%sudo' in policy and 'NOPASSWD' not in '\n'.join(l for l in policy.splitlines() if not l.lstrip().startswith('#'))
pathlib.Path('/var/lib/code-swarm').mkdir(exist_ok=True)
pathlib.Path('/var/lib/code-swarm/admin-provisioned').write_text('ordinary-owner-password-required\n')
print('Code Swarm: installer owner administrator access verified')
PY
