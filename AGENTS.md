# Agent instructions

## Start here

Read `README.md`, `docs/DEVELOPMENT.md`, and `docs/STATUS.md`. This is a Debian image
recipe and a small Python/JavaScript desktop/fleet toolset, not an npm application.
There is no root package.json, dependency install, or development build step.

For a user's personal ISO request, follow `docs/AGENT-BUILD.md`: ask for tools and
startup choice, save their answers outside the source tree, then validate/package
with `builder/recipe.py`. There is no separate builder app or mandatory form. Do
not assume the suggested checkboxes in `BUILD-MY-ISO.md` are confirmed selections.

## Local setup and checks

Use Debian 13 or Ubuntu 24.04+ for the full suite, with system Python 3.12+,
python3-apt, python3-tk and Node.js 18+. Tests use the standard library; no pip/npm
packages or provider credentials are required. On Ubuntu, use `/usr/bin/python3`
so the distro's `apt` module is available.

```sh
/usr/bin/python3 -m unittest discover -s tests -v
node tests/test_fleet.js
node tests/test_fleet_ui.js
python3 builder/audit-source.py
python3 builder/audit-source.py --mode history
git diff --check
```

For a local fleet preview, run `python3 fleet/server.py` and open
`http://127.0.0.1:8765`. No enrollment is required to see its missing-setup states.
The installed desktop needs Xorg, Tk and systemd user services; importing its UI
scripts may start windows. Test pure policy/workflow functions with `runpy` using
a non-main run name, as the tests do. Do not execute root helpers for a smoke test.

## Where changes go

- `product/`: installed desktop tools and owner-controlled remote setup.
- `fleet/`: read-only local controller and browser UI.
- `scripts/configure.py`: main live-build recipe; calls revision overlays in order.
- `scripts/configure-workflows.py`: current toolchain and workflow image integration.
- `config/toolchain.json`, `scripts/toolchain.py`: pinned vendor inputs and staging.
- `config/installer-only/`: interactive installer hooks; disk/admin changes are critical.
- `builder/`: isolated build front end, private remaster and firstboot helpers.
- `builder/recipe.py`: portable recipe validator and source-bundle exporter.
- `update-r7/`: frozen legacy two-file patch, not the current image update system.
- `tests/`: synthetic regression fixtures, no real credentials or live APIs.

Later configure overlays can overwrite earlier files. Inspect the final generated
configuration when changing an overlay. Preserve the legacy patch's payload hashes
and fixtures unless deliberately changing that patch. Add every new image input
to `builder/source-files.txt`; repo-only contributor docs do not belong there.

## Boundaries

Run image builds only in a fresh, dedicated Debian amd64 VM with the required
builder marker. `builder/guest-build.sh` and image configuration use `/work` and
perform root package/system changes. Never run them on the developer's host.
The Mac front end has its own documented prerequisites; do not make it a requirement
for editing or testing core functionality. Do not install the OS onto a real disk
or change repository visibility as part of ordinary source work.

Keep remote access opt-in, loopback-only until explicitly configured, and tied to
the installed owner. Keep local password authentication and encrypted keyrings.
Do not add unattended sign-in, blanket sudo, `--no-sandbox`, permissive TLS, automatic
disk selection, or an update executor while implementing unrelated features.
Telemetry must not infer login, readiness or idleness for unobserved providers.

Never read or copy real account profiles into fixtures/images. Do not commit
credentials, auth links, vendor binaries, ISOs, caches, logs, private evidence or
machine identity. Use clearly synthetic fixtures. The audit scans working files
by default; use history mode before public release. It is a targeted check, not
a guarantee that every secret format or vulnerability is detected.

Update documentation with behavior changes. Separate source tests, native binary
smoke checks, VM boot tests, real authentication, and physical hardware results.
Do not call an image verified because unit tests pass. CodeSwarm's original source
is GPL-3.0-only; preserve upstream licenses and document third-party additions.
