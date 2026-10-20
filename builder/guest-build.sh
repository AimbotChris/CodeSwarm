#!/bin/bash
# Only inside the dedicated disposable Debian builder. Never run on your host.
set -euo pipefail
umask 022
[[ $EUID = 0 && $(uname -m) = x86_64 && $(dpkg --print-architecture) = amd64 ]]
[[ -f /etc/code-swarm-builder && -d /work && ! -e /work/build ]]
cd /work
echo '1/5 Installing signed Debian build prerequisites in the VM'
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends live-build loadlin dctrl-tools appstream librsvg2-bin fonts-dejavu-core zsync wget bzip2 fdisk parted apt-utils debootstrap debian-archive-keyring ca-certificates curl xorriso squashfs-tools qemu-utils syslinux-common isolinux grub-pc-bin grub-efi-amd64-bin grub-efi-ia32-bin grub-efi-amd64-signed shim-signed isomd5sum mtools dosfstools file cpio python3 gnupg
echo '2/5 Fetching pinned official vendor inputs'
bash scripts/fetch-vendor.sh
python3 scripts/toolchain.py fetch
echo '3/5 Generating fresh image configuration'
python3 scripts/configure.py
python3 builder/configure-firstboot.py
echo '4/5 Building amd64 installer (this may take hours on Apple Silicon)'
cd build
lb config
nice -n 10 lb build
echo '5/5 Checking and exporting artifact'
test -s live-image-amd64.hybrid.iso
test -s chroot/usr/share/codex-prototype/packages.tsv
# Public builds must contain no enrollment state, private key or installed owner.
test ! -e chroot/etc/code-swarm-enrollment/authkey
test ! -e chroot/var/lib/tailscale/tailscaled.state
test ! -s chroot/etc/machine-id
test ! -e chroot/var/lib/code-swarm/admin-provisioned
mkdir /work/output
cp live-image-amd64.hybrid.iso /work/output/code-swarm-amd64.iso
cp chroot/usr/share/codex-prototype/packages.tsv /work/output/packages.tsv
cp chroot/usr/share/code-swarm/toolchain.json /work/output/toolchain.json
cp chroot/usr/share/code-swarm/toolchain-versions.txt /work/output/toolchain-versions.txt
cp chroot/etc/code-swarm/workflow.json /work/output/workflow.json
if [ -f /work/source-sha256.json ]; then cp /work/source-sha256.json /work/output/source-sha256.json; fi
dpkg-query -W -f='${Package}\t${Version}\t${Architecture}\n' > /work/output/builder-packages.tsv
cd /work/output
sha256sum code-swarm-amd64.iso > SHA256SUMS
echo 'Build complete. No disk was flashed.'
