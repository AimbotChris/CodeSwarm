# Builder verification — 2026-10-11

This describes source/tooling checks, separately from the previously built R7 installer.

- 97 Python tests pass: 78 existing app, approval, installer, patch and inventory tests plus 19 Mac-builder/firstboot tests.
- Both existing fleet frontend suites pass.
- An independent reviewer inspected VM isolation, secret handling, firstboot gates, source export and reproduction claims, and independently passed the 19 builder tests. Findings about concurrent builder execution and stale guest helpers were fixed and regression-tested.
- A tiny synthetic ISO was actually remastered in the existing resource-limited disposable test container. The test verified unchanged clean-image bytes, a root-owned 0600 synthetic key under a 0700 directory, private ISO permissions, both internal MD5/SHA256 inventories, and removal of extracted private trees. It did not boot the image or start Tailscale. Test fixture source: `tests/private_remaster_smoke.py`.
- The source export allowlist is tested against extra QA passwords, vendor binaries, runtime trees, unlisted keys, symlinks and path traversal. Only explicitly listed regular source files are exported.
- Firstboot tests cover live/missing-owner refusal, existing identity preservation, durable claim/refusal after interruption, bounded timeout cleanup, pending administrator approval, and successful synthetic status. No real key, account, authorization URL or enrollment was used.
- The staged-source audit checks exactly the bytes intended for Git. It rejects runtime/artifact paths, large/unexpected binaries and credential patterns, with exact synthetic test fixtures allowlisted. This is a targeted audit, not a proof against every possible secret format.

Not yet performed: a full clean `live-build` run through Lima on Intel or Apple Silicon macOS; boot/install of that new output; boot/enrollment of a personalized output; real account sign-in; physical thin-client testing. The Mac is not connected or authorized for setup in this execution environment. No Mac dependency or system setting was changed.

The verified R7 ISO remains separate and unchanged. Its prior checks do not validate the newer optional firstboot overlay or the new clean Mac build path. Existing repositories/services and R5/R6 private shares were preserved. Task-owned build/test containers were stopped after testing.

Commands used for ordinary source tests:

```sh
python3 -m unittest discover -s tests -v
node tests/test_fleet.js
node tests/test_fleet_ui.js
python3 builder/audit-source.py
```

A GitHub workflow repeats the ordinary source checks without building or publishing an ISO and without credentials. Its actual result must be checked after pushing; this document does not claim a CI run that has not occurred.
