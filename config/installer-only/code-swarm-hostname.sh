#!/bin/sh
set -eu
[ -d /target/etc ]
name="swarm-$(cut -c1-8 /proc/sys/kernel/random/uuid)"
printf '%s\n' "$name" > /target/etc/hostname
sed -i '/^[[:space:]]*127\.0\.1\.1[[:space:]]/d' /target/etc/hosts
printf '127.0.1.1\t%s\n' "$name" >> /target/etc/hosts
# apt-setup may retain an optical-media source even when use_mirror=false.
# Run solely inside /target and preserve unrelated vendor source stanzas/keys.
chroot /target python3 - < /cdrom/code-swarm-apt.py
