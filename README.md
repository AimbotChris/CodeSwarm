# CodeSwarm OS

A lightweight Debian coding workstation for x86_64 thin clients.

CodeSwarm brings your coding tools into one simple desktop. ChatGPT is the default
workflow, with T3 Code, Codex CLI, Claude Code, OpenCode, Git, and a terminal also
available. Choose what opens at login from **Home → Workflows**. Sign in with your
own provider accounts and use the tools directly or through T3 Code.

**Status: prototype.** This repository contains source and image-building recipes,
not a supported OS release or a downloadable installer. The current multi-provider
image still needs a full build, boot/install test, and hardware qualification.
See [validation status](docs/STATUS.md) for what has actually been tested.

## Make your own ISO

Paste this into your coding agent of choice:

> Help me build my own CodeSwarm ISO locally. Get the source from
> https://github.com/AimbotChris/CodeSwarm and read AGENTS.md and docs/AGENT-BUILD.md.
> Ask which coding tools I want and what should open when I log in. Explain the
> options simply; inspect my computer yourself rather than asking me technical
> setup questions. Save my choices, check the prerequisites, and build in an
> isolated local Debian VM. Keep accounts and credentials out of the image.
> Do not upload the ISO or write it to a USB or physical disk. When finished,
> give me its local location, verified checksum, and a clear test-status summary.

Your agent asks the questions and handles the build; there is no extra app or form
to fill out. You need an agent with local computer access. The output is a Debian
installer for an x86_64 PC, regardless of the starting computer. macOS has an
automated launcher; Windows/Linux require agent-operated VM setup and are not yet
validated end to end. Builds need substantial free disk space and can take hours.
CodeSwarm does not host installer images.

## What is included

- Debian 13 amd64 with a small Openbox/Xorg desktop and local recovery controls.
- ChatGPT and T3 Code, plus native Codex, Claude Code, and OpenCode CLIs.
- Git, SSH client, ripgrep, build tools, and Debian Node.js/npm.
- A personal startup choice: any bundled workflow, a terminal, or Home only.
- Optional Tailscale connectivity and a local, read-only worker console.

Provider accounts, subscriptions, and repository access are set up by each user.
ChatGPT desktop and Codex CLI sign-in are separate. Other providers can be added
using their official installers and T3's provider settings.

## Try the source

```sh
git clone https://github.com/AimbotChris/CodeSwarm.git
cd CodeSwarm
python3 fleet/server.py
```

Open [127.0.0.1:8765](http://127.0.0.1:8765). The console uses Python's standard
library. Live discovery requires an installed, connected Tailscale client;
without it, the console shows setup guidance. This command does not install the OS.

For development dependencies and tests, see [development setup](docs/DEVELOPMENT.md).
Agents should start with [AGENTS.md](AGENTS.md).

## Build or use the OS

The existing build front end runs a dedicated Debian VM through Lima on macOS.
The OS and image recipe are Linux-based; the Mac front end is optional tooling,
not the product. A standalone Linux build launcher is not provided yet.

- [Build an installer](docs/MAC-BUILDER.md)
- [Choose tools and sign in](docs/WORKFLOWS.md)
- [Installation and recovery](docs/R7-INSTALL-AND-UPDATE.md)
- [Optional remote access](product/REMOTE-ACCESS.md)
- [Physical hardware checklist](docs/PHYSICAL-QUALIFICATION.md)

Installation requires explicit disk selection and confirmation. No script here
automatically flashes a physical disk. Optional private enrollment images contain
credentials and must never be published.

## Current limits

Crash recovery detects process exits, not hangs or idle work. Fleet app status
currently refers to ChatGPT only. Automatic update installation, global job
draining, unattended provider sign-in, and OS rollback are not implemented.
Pinned third-party tools need separate update review. Linux Computer Use is not
claimed. Hardware and headless operation still require testing on each model.

## Contributing and licensing

Read [CONTRIBUTING.md](CONTRIBUTING.md) for changes and validation, and
[SECURITY.md](SECURITY.md) for reporting security issues.

CodeSwarm's original source is licensed under [GPL-3.0-only](LICENSE).
Third-party software retains its own licenses and terms, including proprietary
applications downloaded by the build. See [THIRD-PARTY.md](THIRD-PARTY.md) before
distributing an image. CodeSwarm is an independent project, not an official OpenAI,
Anthropic, Debian, T3, or Tailscale distribution.
