# Code Swarm OS

Debian 13 amd64 installer for a physical x86_64 thin client, with an Openbox/Xorg session that opens the official ChatGPT desktop application containing Codex. This is a prototype, not an OpenAI or Debian distribution.

## Build on your Mac

Read [the Mac builder guide](docs/MAC-BUILDER.md), install its prerequisites yourself, then:

```sh
git clone https://github.com/AimbotChris/CodeSwarm.git
cd CodeSwarm
python3 builder/mac.py doctor
python3 builder/mac.py build
```

Or open **Build CodeSwarm.command** for the small guided menu. The builder creates a dedicated Debian amd64 Lima VM: Intel Macs use an x86_64 VM; Apple Silicon uses QEMU x86_64 emulation, which can take hours. It does not install Debian tools on macOS, mount your home in the VM, flash a disk, change host networking, or enroll the Mac.

The new output directory contains an ISO, SHA256 checksum, target/builder package manifests and source hashes. Official ChatGPT 26.1007.21434 and the Debian cloud image are checksum-pinned. Signed Debian and Tailscale repositories supply other packages. This is a repeatable source recipe with recorded versions, **not a byte-identical build promise**.

Optional `python3 builder/mac.py personalize` privately adds an owner-supplied Tailscale auth key to the last clean build. **That ISO is a credential-bearing private artifact.** Enrollment happens only after interactive installation; it preserves unique machine identity and requires network connectivity and applicable tailnet approval. See the guide before using it. No Codex credentials or existing node identity are copied.

## Verified artifact versus new builder

R7 was built and tested on Agent PC: interactive UEFI USB-style boot, unchanged sentinel disk, installation to a disposable virtual disk, installed owner/password checks, official app launch, and connection-dialog cancellation. Its 3,208,970,240-byte ISO has SHA256:

```text
ba47f5687e30d75705feeb2b9622ad4537230c36fdc7e2bf20a6e54bfa7eaeea
```

The authoritative R7 checksum is in [R7 verification](docs/R7-VERIFICATION.md). R7 is retained on Agent PC and is not a Git artifact. The source includes newer Mac-builder and optional firstboot code; **those paths have synthetic tests but have not completed a full build on a real Mac or a real enrollment**. They do not retroactively change the tested R7 ISO. Physical thin-client model, RAM, disk, graphics, networking and firmware compatibility remain unqualified.

## Operation and limits

- Installer boot asks for language, owner password, disk selection and destructive disk confirmation. Nothing is automatically flashed or erased by this repository.
- Installed login starts the minimal desktop and official app. First-run vendor sign-in and keyring setup remain owner actions. Desktop QR/unattended reusable authentication is not established; documented CLI device auth is a separate flow.
- Bounded process-crash restart/backoff and recovery controls are included. This does not detect application hangs or prove global job idleness.
- Signed update proposals and an exact-manifest/device, expiring, single-use permit model are included. Live assistant enrollment is not configured; disruptive updates fail closed. Unknown desktop work blocks safe-drain claims. APT is not rollback; no OS A/B rollback is claimed.
- Linux Computer Use is unsupported in the official documentation. Remote desktop and Tailscale configuration remain explicit owner-controlled features.

See [installation/recovery](docs/R7-INSTALL-AND-UPDATE.md), [physical qualification](docs/PHYSICAL-QUALIFICATION.md), [test scope](docs/BUILDER-VERIFICATION.md), and [vendor authentication findings](docs/R7-AUTH-FEASIBILITY.md).

Only original source/configuration and small project assets are stored here. Vendor binaries, boot images, signed-in profiles, runtime state, actual credentials, build caches and private ISOs are excluded. See [third-party notes](THIRD-PARTY.md).
