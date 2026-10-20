# Agent-guided local ISO build

This is the runbook behind the README's copyable prompt. The user answers a few
questions in their existing coding agent. There is no separate app, hosted builder,
uploaded recipe, hosted ISO, or account service.

## Ask only what you need

Inspect the host OS, CPU, available memory/disk and existing virtualization tools
yourself. Do not ask the user to diagnose their computer or choose a hypervisor.
Then ask in plain language:

1. **Which tools would you like?** Offer ChatGPT, T3 Code, Codex CLI, Claude Code,
   OpenCode, and Development tools. Explain that Git, a browser, a terminal and
   recovery tools come with every image. Development tools adds Node.js/npm and a
   C/C++ compiler. If unsure, suggest ChatGPT + T3 Code + Codex CLI.
2. **What should open when you log in?** Offer one selected tool, Terminal, or Home
   only. Explain that it can be changed after installation.

Use answers already supplied instead of repeating questions. If T3 is selected
without a bundled provider, ask which of Codex CLI, Claude Code or OpenCode to add.
Do not silently add an unchecked provider. Use a new folder in Downloads for output
unless the user supplies another location. Only ask about the folder if necessary.
Summarize their choices once before starting substantial downloads.

Do not ask for provider credentials, API keys, Tailscale keys or signed-in profiles.
These are configured after OS installation. Do not automatically accept a default
checklist as the user's answer. `BUILD-MY-ISO.md` is a recipe template for the agent
to fill, not another form the user must complete.

## Save a recipe and check it

Save confirmed answers in a local JSON file outside the source tree. This schema
is deliberately closed: no arbitrary package names, download URLs or shell commands.

```json
{
  "schema": 1,
  "tools": ["chatgpt", "t3", "codex"],
  "startup": "chatgpt"
}
```

Tool IDs: `chatgpt`, `t3`, `codex`, `claude`, `opencode`, `development`.
Startup values: selected tool IDs except `development`, plus `terminal` and `none`.
An empty tool list with `terminal` or `none` is a valid base-only image.
An edited copy of `BUILD-MY-ISO.md` is accepted too. Never edit tracked vendor pins
or the source allowlist to implement ordinary user choices.

```sh
python3 builder/recipe.py check --recipe /path/to/my-workflow.json
```

Use the host's Python command (`py -3`, `python`, or `python3`). The portable recipe
helper uses only Python's standard library and does not require Tk, Node or Lima.
It validates selections before creating a source bundle. It never executes content
from the recipe.

## Choose the local build environment

The result is always a Debian 13 amd64 installer for a separate x86_64 PC. "Host
independent" describes this prompt and source recipe, not an ability to create
arbitrary Windows/macOS installation media.

**macOS:** use the existing isolated Lima/QEMU front end and its prerequisites in
[MAC-BUILDER.md](MAC-BUILDER.md). Pass the confirmed recipe:

```sh
python3 builder/mac.py doctor --output /path/to/new-output
python3 builder/mac.py build --recipe /path/to/my-workflow.json --output /path/to/new-output
```

**Windows or Linux:** use a dedicated disposable Debian 13 amd64 VM through an
available local hypervisor. This is agent-operated VM provisioning; there is no
tested automatic host launcher for these platforms yet. Do not call the macOS
launcher on another OS or run the guest script on the developer's host. Use only
an actual isolated VM with no physical disk passthrough, shared home, SSH-agent
forwarding or copied profiles. A generic container or the host's WSL distribution
does not satisfy that isolation boundary.

If a suitable backend is missing, explain the specific prerequisite and whether
installation requires administrator action. Follow the agent's permission policy.
Do not disable host security, install unreviewed helpers, or fake a completed build.
If local VM execution is unavailable, stop with the recipe preserved and state
exactly what is needed. A chat-only agent cannot build an ISO on the user's machine.

Use at least 8 GiB host RAM and 45 GiB free disk as initial checks; the VM reserves
2 CPUs, 4 GiB RAM and a 64 GiB sparse disk. Leave room for outputs outside that disk.
ARM hosts need x86_64 emulation; expect long builds. The pinned base image URL and
SHA512 in `builder/lima.yaml` can be used for equivalent VM provisioning. Verify
the digest before boot; don't replace missing pinned inputs with `latest`.

For an equivalent agent-provisioned VM:

1. Create a new, isolated builder. Confirm guest `uname -m` is `x86_64`, APT's
   architecture is `amd64`, and `/etc/os-release` is Debian 13. Provision Python 3
   and OpenSSH if the chosen base image needs them. Establish guest access without
   importing the user's account keys or agent; use VM-specific access instead.
2. Prepare a source archive on the host:
   `python3 builder/recipe.py bundle --recipe /path/to/my-workflow.json --output /path/to/new-source.tar`.
   This exports only the source allowlist, a validated `config/workflow.json`, and
   source hashes. It contains no vendor binaries or user configuration.
3. Copy it into the guest with the hypervisor's file-copy mechanism or dedicated
   SSH connection. In that disposable guest only, create `/work`, extract the
   archive there, and write `codeswarm-builder-v1` to `/etc/code-swarm-builder`.
   Never overwrite an existing VM/workspace or create this marker on the host.
4. In that VM only, run `sudo bash /work/builder/guest-build.sh`. Keep showing the
   user meaningful build progress; do not report success until it exits successfully.
5. Transfer `/work/output/` to the user's new local output directory. Verify the
   ISO's SHA256 on the host against `SHA256SUMS`. Preserve workflow, package,
   toolchain and source manifests with the image.
6. Stop the task-owned VM. Remove only task-owned disposable state after preserving
   output; do not delete pre-existing machines or unrelated caches.

## Finish simply and honestly

Return the ISO's local path, checksum, selected tools and startup choice. Clearly
separate "build completed" from VM boot/install tests, real provider sign-in, and
physical-hardware acceptance. Follow [STATUS.md](STATUS.md) for release testing.
Never upload an ISO, create a release, change repository visibility, write a USB,
or install onto a physical disk as part of this build request.

The base includes dormant owner-controlled Tailscale/remote setup tools, with no
enrollment or remote access enabled. A custom recipe cannot add arbitrary tools
yet. If someone asks for another tool, explain that it needs a reviewed project
addition rather than silently downloading and executing an installer.
