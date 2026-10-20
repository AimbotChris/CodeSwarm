# Contributing

CodeSwarm is an early prototype. Small changes with a clear purpose and reproducible
checks are easiest to review. For larger changes, open an issue to explain the
problem and proposed behavior first.

1. Follow [development setup](docs/DEVELOPMENT.md).
2. Make a focused change and add regression coverage for meaningful behavior changes.
3. Run the relevant tests, source audit, and `git diff --check`.
4. Explain what changed, how you tested it, and what remains unverified in your PR.

Keep user-facing text short and readable. Write setup commands for someone using
a fresh clone, not a maintainer's existing machine. Keep provider choice open and
preserve the simple local desktop experience.

Never include real credentials, signed-in profiles, private images, runtime state,
or vendor binaries in a PR. Report security concerns through [SECURITY.md](SECURITY.md).
Changes to installer disks, authentication, privilege boundaries, networking, or
update control need explicit tests and a clear account of their effects.

Your contributions to original project code are provided under GPL-3.0-only.
Identify the source and license of any third-party material you add. Do not modify
or redistribute proprietary tool internals as part of a contribution.
