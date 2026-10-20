# Builder verification

Use [validation status](STATUS.md) for the current source and outstanding image
acceptance work. Use [development setup](DEVELOPMENT.md) to reproduce ordinary
checks. [R7 verification](R7-VERIFICATION.md) covers a different historical image.

The original builder work added synthetic tests for architecture checks, private
state/locking, source export, firstboot eligibility, existing-identity preservation,
claim persistence, timeout cleanup and synthetic Tailscale outcomes. The tests
run without a real Mac, VM, account, key or provider API.

A maintainer also recorded a separate synthetic private-remaster smoke run. The
fixture source is `tests/private_remaster_smoke.py`; it needs image tools and a
disposable root environment. It checks clean-image preservation, private file
permissions, checksum updates and cleanup. It does not boot or enroll an image.
Private raw QA evidence from that run is not included in this repository.

The source audit checks selected credential patterns and forbidden artifact paths
in working files, the Git index, or reachable history. It does not establish that
all credentials or vulnerabilities are absent. New image inputs are explicitly
listed in `builder/source-files.txt` and version/hash-pinned where applicable.

A clean image build, real Mac run, private-image boot/enrollment and physical
thin-client qualification remain separate acceptance steps. CI runs source tests;
it neither builds nor publishes an ISO and receives no provider credentials.
