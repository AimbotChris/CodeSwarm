# Agent recipe template

Users start with the prompt in [README.md](README.md). Their agent asks the
questions and fills in a copy of this template, or saves an equivalent JSON recipe.
Users do not need to edit this file. Initial checks below are suggestions, not
confirmed user choices. See [the agent runbook](docs/AGENT-BUILD.md).

## My tools

Put an `x` in the boxes you want. Leave the others empty.

<!-- codeswarm-tools:start -->
- [x] ChatGPT
- [x] T3 Code
- [x] Codex CLI
- [ ] Claude Code
- [ ] OpenCode
- [x] Development tools
<!-- codeswarm-tools:end -->

Git, a browser, a terminal, the desktop and recovery tools are always included.
Development tools adds Node.js/npm and a C/C++ build toolchain. T3 Code needs at
least one checked provider: Codex CLI, Claude Code or OpenCode.

## When I log in

Change the line below to ChatGPT, T3 Code, Codex CLI, Claude Code, OpenCode,
Terminal, or Home only. If you choose a tool, check its box above too.

Open at login: ChatGPT

The result is a Debian-based installer for an x86_64 PC. Windows, macOS and Linux
can be the starting computer for the agent-guided process; local VM setup depends
on that computer. The current automated launcher is for macOS; other hosts need
an agent-provisioned compatible VM. Builds can take hours and need substantial
free disk space. You sign in to your tools after installing the OS.
