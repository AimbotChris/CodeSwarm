#!/bin/sh
set -eu
media=$(awk '$2=="/cdrom" {print $1; exit}' /proc/mounts)
media=$(readlink -f "$media")
[ -b "$media" ] || { echo 'Cannot identify installation medium; automatic setup stopped.' >&2; exit 1; }
name=${media##*/}
if [ -f "/sys/class/block/$name/partition" ]; then name=$(basename "$(dirname "$(readlink -f "/sys/class/block/$name")")"); fi
printf '/dev/%s\n' "$name" > /run/code-swarm-install-medium
if [ ! -e /usr/bin/list-devices.code-swarm-original ]; then
 mv /usr/bin/list-devices /usr/bin/list-devices.code-swarm-original
 cat > /usr/bin/list-devices <<'WRAPPER'
#!/bin/sh
if [ "$#" = 1 ] && [ "$1" = disk ]; then
 medium=$(cat /run/code-swarm-install-medium)
 /usr/bin/list-devices.code-swarm-original "$@" | while IFS= read -r dev; do
  [ "$(readlink -f "$dev")" = "$medium" ] || printf '%s\n' "$dev"
 done
else
 exec /usr/bin/list-devices.code-swarm-original "$@"
fi
WRAPPER
 chmod 755 /usr/bin/list-devices
fi
