# Coding workflows

Code Swarm is a general coding workstation. ChatGPT is the default startup app,
and each user can choose another workflow without changing the OS or other users.
From Home, open **Workflows** to launch a tool, sign in, or save what opens at login:
ChatGPT, T3 Code, Codex CLI, Claude Code, OpenCode, Terminal, or Home only.
Changing this choice takes effect on the next login; it does not stop running work.

## Included tools

Personal images include only the selected coding tools. The README's agent prompt
collects choices and produces a validated recipe; see [agent build instructions](AGENT-BUILD.md).
The default recipe remains the full tool bundle when no custom recipe is supplied.

Git, SSH client, ripgrep and unzip are included in the base. Build-essential and
Debian Node.js/npm are added when Development tools is selected, from signed
Debian repositories. Git was already part of the original image.
T3 Code's native Debian desktop package and the native Codex, Claude Code and
OpenCode CLIs are included from pinned, checksum-verified public vendor artifacts.
They do not require npm installation at first login. Codex includes its companion
runtimes. OpenCode uses the baseline x64 build for broader CPU compatibility.
Exact versions, URLs, SHA256s and upstream license/notice inputs live in
`config/toolchain.json`; an image keeps
this file at `/usr/share/code-swarm/toolchain.json` and records CLI smoke-check
versions in `/usr/share/code-swarm/toolchain-versions.txt`.
CodeSwarm's license and third-party guide are installed under
`/usr/share/doc/code-swarm`, with additional upstream notices in its `vendor` directory.

## First use

1. Open **Home → Workflows → T3 Code → Open**.
2. Use **Sign in** beside your preferred CLI, or run `codex login`,
   `claude auth login`, or `opencode auth login` in a terminal.
3. In T3 Code, open **Settings → Providers** and enable/configure that provider.
   The bundled CLIs are on the system PATH. If discovery fails, use
   `/usr/local/bin/codex`, `/usr/local/bin/claude`, or `/usr/local/bin/opencode`
   as its binary path. Add a project and start a thread.
4. Choose **T3 Code** under **Open at login** and save if that is your daily workflow.

ChatGPT desktop sign-in and Codex CLI sign-in are distinct setup steps. No account,
API key, subscription, repository credential, or signed-in profile is baked into
the image. Network access and an eligible provider account are still needed.
Git works with any host: set your own `git config --global user.name` and
`user.email`, then configure SSH or HTTPS credentials for your repositories.

T3 also supports other providers. Cursor, Grok Build, Antigravity, Pi and Muse are
not bundled here; install/configure them using their official instructions and
T3's provider settings. User-installed binaries must be visible to the graphical
session's PATH, or configured with an absolute binary path in T3. Debian's Node.js
version may be too old for some optional providers; follow that provider's runtime
requirements. No root-level latest-installer script runs at first boot.

CLI alternatives: `code-swarm-workflow start t3`, `code-swarm-workflow login claude`,
`code-swarm-workflow set-default terminal`, and `code-swarm-workflow get-default`.
Preferences live in the user's XDG config directory under `code-swarm/workflow.json`.
T3's desktop runs as a user service, `code-swarm-t3.service`, with bounded crash
recovery. Inspect it with `journalctl --user -u code-swarm-t3`; log out to stop it.
No public server, mobile pairing or remote exposure is configured automatically.

## Building and updates

The core image recipe (`scripts/configure.py`) stages these tools for every builder,
independent of the Mac front end. `scripts/toolchain.py fetch` downloads reviewed
inputs; `stage` verifies their hashes again before copying them into the image.
The build fails if an input is missing, changed, unsafe to extract, or if a CLI
cannot report its version inside the Debian chroot. The same source allowlist
includes the new recipe, manifest, launcher and guide.

APT approval coverage remains limited to its approved signed repositories. Native
provider binaries and T3's downloaded Debian package require separate owner review
or an image rebuild with reviewed pins. Their own update features are outside
the OS approval executor. Do not assume APT will update them or roll them back.
Inventory displays this boundary explicitly. Never bulk-upgrade providers during
an active session; stop work and review T3 compatibility before changing versions.

The fleet console's existing app telemetry still describes ChatGPT only; it does
not claim T3/Claude/OpenCode readiness, sign-in, activity or idleness.

Source and synthetic tests verify integration, extraction and preference behavior.
An updated ISO must still pass a clean Debian build, boot/install test, graphical
T3 launch, provider discovery and real owner sign-in on target hardware. The old
verified R7 ISO does not contain this toolchain.

Official references, checked 2026-10-20:

- [T3 installation and provider setup](https://github.com/pingdotgg/t3code/blob/main/docs/user/install.md)
- [Codex CLI](https://developers.openai.com/codex/cli)
- [Claude Code setup](https://code.claude.com/docs/en/setup)
- [OpenCode](https://opencode.ai/docs/)
