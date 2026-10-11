#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p vendor
# Cache only public pinned downloads; never use a personalized chroot as a cache.
cache=${CODESWARM_VENDOR_CACHE:-/var/cache/code-swarm-inputs}
mkdir -p "$cache"
fetch() {
 name=$1; hash=$2; url=$3
 if ! printf '%s  %s\n' "$hash" "$cache/$name" | sha256sum -c - >/dev/null 2>&1; then
  curl --proto '=https' --tlsv1.2 -fL --retry 3 --limit-rate 12M "$url" -o "$cache/$name.part"
  printf '%s  %s\n' "$hash" "$cache/$name.part" | sha256sum -c -
  mv "$cache/$name.part" "$cache/$name"
 fi
 cp "$cache/$name" "vendor/$name"
 printf '%s  %s\n' "$hash" "vendor/$name" | sha256sum -c -
}
fetch chatgpt_amd64.deb 276b5341c3d74b261d3ad52106f7fa7edde06841e4767fe2a40cb54099b1f3ed https://persistent.oaistatic.com/codex-app-prod/linux/deb/pool/main/c/chatgpt/chatgpt_26.1007.21434_amd64.deb
fetch tailscale-archive-keyring.gpg 3e03dacf222698c60b8e2f990b809ca1b3e104de127767864284e6c228f1fb39 https://pkgs.tailscale.com/stable/debian/trixie.noarmor.gpg
fetch tailscale.list 5a1b21b30892bf22fb5d7c4f52fefe9b65efda2100e82abba2e0849da2a2264b https://pkgs.tailscale.com/stable/debian/trixie.tailscale-keyring.list
