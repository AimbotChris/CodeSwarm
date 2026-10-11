#!/bin/sh
set -eu
. /usr/share/debconf/confmodule
info=''
for disk in $(list-devices disk); do
 name=${disk##*/}
 model=$(cat "/sys/class/block/$name/device/model" 2>/dev/null || echo unknown)
 serial=$(cat "/sys/class/block/$name/device/serial" 2>/dev/null || echo unavailable)
 sectors=$(cat "/sys/class/block/$name/size")
 gib=$((sectors / 2097152))
 info="$info $disk | $model | ${gib} GiB | serial: $serial;"
done
cat > /tmp/code-swarm-disks.templates <<'TEMPLATE'
Template: code-swarm/disks
Type: note
Description: Code Swarm OS — choose your installation disk carefully
 Available target disks: ${DISKS}
 .
 The detected installation medium is excluded from automatic disk discovery.
 Choose your target in the next partitioning screens. No disk has been selected
 for you. Writing partitions requires your final explicit confirmation.
 .
 If a disk serial is unavailable, verify its model and capacity independently.
TEMPLATE
debconf-loadtemplate code-swarm /tmp/code-swarm-disks.templates
db_subst code-swarm/disks DISKS "$info"
db_input critical code-swarm/disks || true
db_go
