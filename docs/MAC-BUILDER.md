# Build an amd64 thin-client installer on a Mac

Status: implemented prototype; synthetic tests pass on Agent PC. An actual Mac build and private-image boot/enrollment remain unverified. No Mac dependency or setting was changed during implementation.

## Prerequisites

Use an Intel or Apple Silicon Mac with Python 3.10+, Git, Lima, QEMU, at least 8 GiB RAM and 45 GiB free on the home/output volumes. More disk space is useful for successive images. The dedicated VM reserves two CPUs, 4 GiB RAM and a 64 GiB sparse virtual disk. Keep the Mac awake and connected during the build. Apple Silicon runs a complete x86_64 VM under emulation and may be very slow; this intentionally avoids silently building an arm64 target.

Install tools yourself following [Lima's official installation instructions](https://lima-vm.io/docs/installation/). If you already use Homebrew, the owner-run command is:

```sh
brew install lima qemu python
```

The tool never runs Homebrew, installs Rosetta, edits host sudoers, opens a host service, forwards your SSH agent or passes through physical disks. Lima manages its own guest SSH access; root build operations are confined to the disposable builder VM. The thin-client installer retains ordinary password-protected administration.

## Guided build

```sh
git clone https://github.com/AimbotChris/CodeSwarm.git
cd CodeSwarm
python3 builder/mac.py doctor
python3 builder/mac.py build --output "$HOME/CodeSwarm-clean-01"
```

You can also open `Build CodeSwarm.command` and choose a menu item. Outputs must be new directories outside the repository. The tool refuses overwrite and simultaneous builder operations. `doctor` is read-only and does not create a VM. `build` creates/starts only `codeswarm-builder-v1`, uses a pinned official Debian cloud image, checks actual guest amd64 architecture, copies an explicit source-file allowlist, and builds on the guest Linux filesystem at `/work`.

Every build discards that dedicated VM's previous `/work` tree after checking its ownership marker. Public vendor downloads are cached by SHA256 at `/var/cache/code-swarm-inputs`; the Lima base image is also cached. Chroots and personalized filesystem trees are never reused as public input. Build progress comes from five explicit stages and the Debian tools. A failed build is not reported as an ISO; the VM is stopped and its partial `/work` remains for diagnosis. Do not interrupt a build by starting a second Lima command yourself.

Successful output:

- `code-swarm-amd64.iso`, `SHA256SUMS`
- `packages.tsv`, `builder-packages.tsv`
- `builder-config.yaml`, `source-sha256.json`

The tool verifies the downloaded ISO checksum. You can independently run `shasum -a 256 -c SHA256SUMS` from the output directory. This repository provides no disk-writing command: separately choose a USB-writing tool and explicitly confirm the USB device. Booting the installer still requires disk selection and installation confirmation.

## Optional private firstboot Tailscale enrollment

First complete a clean build with the current source. Then, in an interactive terminal:

```sh
python3 builder/mac.py personalize --output "$HOME/CodeSwarm-private-01"
```

The tool checks guest helper versions before accepting a key. It asks you to type `PRIVATE`, then reads your existing owner-created Tailscale **auth key** with terminal echo disabled. Do not paste a key into a command argument, environment variable, chat, source file, issue or CI secret for this workflow. API/OAuth credentials, Codex credentials and existing `tailscaled.state` are not accepted as enrollment inputs.

**The personalized ISO contains the key. Anyone who obtains it can extract the key.** The output directory is 0700 and files are 0600. The key travels through SSH stdin, is written only in a root-only private guest overlay, and is not included in command arguments, environment, terminal output, build logs or the public image. Do not put the private ISO in Git, Library, cloud sync or public artifact hosting. Builder virtual disks, snapshots, backups and the written USB are also sensitive. Filesystem deletion is not secure erasure.

Use the shortest practical expiry and least-privilege tags/grants. A one-off key is for one machine; a reusable key permits multiple machines until expiry/revocation and raises the exposure risk. Configure those properties in your own tailnet admin console; the builder does not create keys or change policy. Revoke the key after enrollment or immediately if an image leaks. Revoking the enrollment key does not automatically remove already enrolled devices: review devices separately. [Official key lifecycle documentation](https://tailscale.com/docs/features/access-control/auth-keys).

After the ordinary installer finishes and the new machine boots, a root service checks the installed-owner marker and refuses live boots or existing node state. It claims one attempt durably, enables Tailscale, and allows the official client up to four minutes to connect. It deletes the installed key after that attempt. It never resets an existing identity. Each installed machine gets its own machine ID, hostname and Tailscale node state. The immutable ISO/USB still contains the key and must be protected/revoked.

Check `sudo cat /var/lib/code-swarm/enrollment-status` for `connected`, `pending-device-approval`, `attempting`, or `failed-owner-review-required`. A failed/ambiguous attempt is not automatically retried across boots; use Home → Connect Tailscale for a fresh owner-approved interactive connection. Tailnet device approval, network availability and grants can still delay access. `connected` means the daemon reports Running, not that every service is reachable. This does not enable Tailscale SSH, Serve, Funnel, remote desktop, exit nodes or an assistant watcher.

The private remaster keeps the clean ISO unchanged. Its extracted trees are removed on normal completion, and the private guest output is removed after verified transfer. On transfer failure, the guest output may remain under `/var/lib/code-swarm-private`; revoke the key before recovery or disposal. The tool stops the VM. To remove this dedicated VM after preserving your desired outputs, explicitly run:

```sh
limactl delete codeswarm-builder-v1
```

Deletion removes the VM's cache/workspace; it does not revoke keys or erase other copies. The next build creates a new dedicated VM.

## Troubleshooting and reproduction limits

If missing prerequisites or low disk/RAM stop `doctor`, resolve those yourself and rerun. If the same-name VM has no matching private ownership record, inspect it before taking any action; the tool refuses to overwrite an unrelated VM. If the pinned cloud image or vendor version disappears, or a checksum changes, fail closed and review a source lock update rather than using `latest` or bypassing verification.

To inspect a failed non-private build, start the dedicated VM with `limactl start codeswarm-builder-v1` and use `limactl shell --workdir=/ codeswarm-builder-v1`; files are under `/work/build`. Stop it afterward with `limactl stop codeswarm-builder-v1`. Never post a private VM or its filesystem as a debugging attachment.

Source hashes, pinned vendor bytes and package manifests make builds auditable. Debian/Tailscale package indexes and Lima/QEMU versions evolve; a future build can differ. The existing R7 image used retained build state plus an original installer payload; the new full `live-build` path must pass fresh Mac/VM acceptance before it can replace that qualified artifact. No claim of successful Mac execution, personalized-image boot, real enrollment or physical thin-client compatibility is made yet.

Architecture reference: [Lima Intel-on-ARM](https://lima-vm.io/docs/config/multi-arch/) and [plain mode isolation](https://lima-vm.io/docs/config/plain/). Debian image checksum was checked against the [official dated SHA512 manifest](https://cloud.debian.org/images/cloud/trixie/20261001-2618/SHA512SUMS). All apt repositories retain signature verification.
