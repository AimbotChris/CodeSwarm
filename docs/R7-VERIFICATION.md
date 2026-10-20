# Historical R7 verification

This is an inherited maintainer record for a previous image, not acceptance of
the current source. The ISO, screenshots, build logs and private QA evidence are
not published in this repository. Readers can inspect the source and historical
package inventory, but cannot independently repeat the recorded image checks
from those files alone. See [current status](STATUS.md).

## Recorded artifact

- Filename: `code-swarm-os-debian13-amd64-r7.iso`
- Size: 3,208,970,240 bytes
- SHA256: `ba47f5687e30d75705feeb2b9622ad4537230c36fdc7e2bf20a6e54bfa7eaeea`
- Package inventory: [packages-r7.tsv](packages-r7.tsv)

## Recorded scope

The maintainer reported interactive UEFI USB-style boot with an unchanged sentinel
disk, installation to a disposable 24 GiB virtual disk, password-protected owner
administration, locked root, unique hostname, encrypted test keyring setup, and
ChatGPT launch to its sign-in screen. Canceling the Tailscale permission prompt
left its daemon disabled/inactive. No real provider account or tailnet grant was used.

R7 introduced a locally encoded Tailscale authorization QR/link, with explicit copy
and browser actions, bounded waiting, status freshness and cancellation handling.
Its original source suite had 78 Python tests and both fleet frontend suites.
Synthetic Xvfb/QR-decoder checks were recorded separately from real authentication.
The repository includes synthetic regression fixtures, not the private screenshots
or raw logs cited in the original development notes.

The [legacy R6-to-R7 patch](../update-r7/README.md) replaces only the known connection
window/helper. Its apply/restore tests do not demonstrate OS rollback or an update
executor. Unknown installations and modified patched files are refused.

## Limits

The recorded image used retained build state and a preserved original installer
payload. Clean-room or byte-identical reproduction was not established. The newer
Mac builder, optional firstboot enrollment, T3 Code and provider CLI integration
were not part of this historical image. No real sign-in, physical hardware,
headless reliability, global job-idleness detection or OS rollback was qualified.

The recorded ChatGPT version was 26.1007.21434. Desktop authentication findings
are version-specific; see [R7 auth findings](R7-AUTH-FEASIBILITY.md). They are not a
promise about other releases or provider CLIs.
