# Validation status

CodeSwarm is a prototype. Passing source checks does not establish that an installer
is ready for physical machines or that a provider's authentication works.

## Current source — 2026-10-20

| Area | Evidence | Limit |
| --- | --- | --- |
| Python behavior | 109 local unit tests pass, including personal recipes, workflow, archive safety and audit tests | Synthetic fixtures; no real provider accounts |
| Fleet frontend | Both Node.js suites | Browser logic; not a real tailnet acceptance run |
| Native tool inputs | SHA256 verification and staging of the four tools and upstream notices | Download integrity is not runtime compatibility |
| Image configuration | Full recipe generated with synthetic legacy-vendor fixtures; final shell/Python/XML syntax checked | No packages installed into a built image |
| Tool exclusion | Full Claude-only and base-only configurations generated; omitted packages, services and native artifacts checked | Not a custom ISO build or boot |
| CLI runtimes | Codex 0.163.0, Claude Code 2.1.305 and OpenCode 1.19.3 report versions on Linux x86_64 | Not a Debian image boot or authenticated coding session |
| Desktop layout | Home and workflow chooser mapped in Xvfb with no controls clipped at their default sizes | No installed T3 or real-provider interaction |
| Public source hygiene | Working-tree and reachable-history targeted audits | No comprehensive secret-detection or security guarantee |
| Current installer | Recipe updated for T3 Code and provider CLIs | No fresh full image build or boot qualification yet |
| Agent-guided custom images | Markdown/JSON selection validation, source packaging and selected-tool staging | Automated host launcher remains macOS-only; other-host VM provisioning is unvalidated |

Run the commands in [development setup](DEVELOPMENT.md) to reproduce source checks.
CI repeats them on GitHub; a local pass is not a claim of a successful remote run.
The workflow manifest in `config/toolchain.json` is the source of truth for pins.

## Before releasing an installer

- Complete a clean Debian amd64 build and retain package/source/toolchain manifests.
- Boot the ISO in a disposable VM; verify disk selection and cancellation leave
  unrelated disks untouched, then install to a disposable disk.
- Verify owner password, locked root, working sudo, unique hostname/machine identity,
  no copied profiles, and inactive remote access by default.
- Verify Home, ChatGPT, T3 Code, every bundled CLI, startup choices and logout cleanup.
- Verify T3 discovers the CLIs, starts a thread, and handles owner sign-in for each
  supported bundled provider. Confirm behavior when offline or unauthenticated.
- Verify desktop fit, keyboard navigation, crash recovery, and diagnostics on the
  target screen resolution.
- Test real networking, graphics, CPU support, storage, cold boot and remote access
  on each intended thin-client model. Follow [physical qualification](PHYSICAL-QUALIFICATION.md).
- Review component licenses/terms before distributing vendor binaries or an ISO.
  Publish only clean artifacts with hashes and a clear record of what was tested.

## Historical R7

The repository inherited a maintainer's record of a previous R7 image with VM
boot/install and ChatGPT launch checks. That image predates the current builder
and multi-provider changes. The ISO, screenshots and private QA logs are not in
this repository, so readers cannot reproduce those historical results from Git
alone. [R7 verification](R7-VERIFICATION.md) preserves the checksum and scope;
`docs/packages-r7.tsv` is its historical package inventory.

No physical thin-client qualification, real provider sign-in, private-image
enrollment, global job-idleness detection, or OS rollback is established here.
