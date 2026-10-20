# Development setup

Use Debian 13 or Ubuntu 24.04+ for the full test suite. You need Git, system Python
3.12+, Python's Tk and APT bindings, and Node.js 18+. The fleet server itself needs
only Python 3.10+ and its standard library. There are no pip or npm dependencies
for the repository's tests or server.

On a development Debian/Ubuntu machine, install test prerequisites:

```sh
sudo apt update
sudo apt install git python3 python3-apt python3-tk nodejs
git clone https://github.com/AimbotChris/CodeSwarm.git
cd CodeSwarm
```

Run the same source tests as CI:

```sh
/usr/bin/python3 -m unittest discover -s tests -v
node tests/test_fleet.js
node tests/test_fleet_ui.js
python3 builder/audit-source.py
git diff --check
```

Use the distro Python for `python3-apt`; an unrelated Python or isolated virtual
environment may not see it. Tests use temporary directories and synthetic fixtures,
not live accounts, system services, disks, or paid API requests. The optional
`tests/private_remaster_smoke.py` is separate: it needs image tools and a disposable
root environment. It is not part of ordinary unit-test discovery.

## Run individual components

```sh
python3 fleet/server.py
# Open http://127.0.0.1:8765; Ctrl+C stops it.

python3 -m unittest discover -s tests -p test_workflows.py -v
python3 product/code-swarm-workflow get-default
```

Without Tailscale, the fleet console shows setup guidance. For actual peers and
desktop links, follow [remote access](../product/REMOTE-ACCESS.md). UI scripts need
a graphical display; the installed session also needs Debian's systemd user manager.
Do not execute system configuration or root helpers on your development host.

## Image recipe

`scripts/configure.py` generates live-build configuration under `/work/build` in
a dedicated Debian amd64 build VM. It reads `scripts/add-remote.py`, then the
R5/R6/R7 overlays, then `scripts/configure-workflows.py`. Later overlays win.
`builder/configure-firstboot.py` adds the dormant optional enrollment service.
`builder/guest-build.sh` installs build dependencies, fetches pinned inputs,
generates configuration, builds the ISO, and exports manifests.

The existing [Mac build front end](MAC-BUILDER.md) provisions that isolated VM.
There is no supported standalone Linux launcher yet. The [agent build runbook](AGENT-BUILD.md)
describes equivalent VM provisioning on other hosts. Do not run the guest script
on the host or treat source tests as an ISO build. The entire image path is still
awaiting fresh acceptance testing; see [status](STATUS.md).

## Updating tool inputs

Review the upstream release, license, supported architecture, runtime requirements,
and T3 provider compatibility. Update `config/toolchain.json` with an exact version,
immutable version URL, and SHA256 from upstream. Claude's native npm artifact was
checked against registry SHA512 integrity before recording its SHA256. Do not use
`latest` URLs or accept a new hash just because a download changed.

In an isolated workspace, `python3 scripts/toolchain.py fetch --cache /path/to/cache`
fetches and verifies the reviewed inputs. They are ignored under `vendor/`.
`python3 scripts/toolchain.py stage --build /path/to/fresh-stage` verifies them again
and creates a staging tree, without installing anything on the host. The build
chroot checks CLI versions and records the results. A full acceptance run must also
launch T3 and test provider discovery and owner authentication.

Add new image source files to `builder/source-files.txt`. Keep repo-only docs outside
that allowlist. Before publication, run `python3 builder/audit-source.py --mode history`
as well as the default working-tree check. To audit an exact Git index, use
`python3 builder/audit-source.py --mode index` after staging the intended files.

`builder/recipe.py check --recipe /path/to/recipe.json` validates a personal build.
Its `bundle` action exports allowlisted source with the validated selection and
hash manifest. No app, GUI or platform-specific Python dependency is required.
The image build filters vendor downloads, package staging, CLI smoke checks and
startup defaults from that selection. Recipes cannot contain shell commands or URLs.
