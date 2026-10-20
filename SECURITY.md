# Security

CodeSwarm is a prototype without a security support SLA or a production-hardened
release. Keep it on machines and networks you control, with current host software
and deliberate access permissions.

For sensitive reports, use the repository's **Security → Report a vulnerability**
option if it is available. If it is unavailable, open an issue requesting a private
contact route without describing the vulnerability or including sensitive data.
Never post credentials, live authorization URLs, private ISOs, or authenticated logs.

Useful reports include the affected commit, expected and observed behavior, and
minimal reproduction steps using synthetic data. Identify whether the problem is
in CodeSwarm source or an upstream component; report upstream issues to that vendor
as well. No response time or fix date is promised.

The image does not enroll workers or publish remote desktops by default. Remote
access is a separate owner action; greeter sharing controls the physical login
screen and requires careful access policy. Fleet telemetry is advisory and cannot
authorize updates or prove that agents are idle.

Optional personalized images embed a Tailscale auth key. Treat the ISO, USB, VM,
snapshots and backups as credentials. Revoke an exposed key through Tailscale and
review enrolled devices. Deleting files alone does not revoke access.

Before distributing an installer, review all component licenses and terms and run
the validation checklist in [docs/STATUS.md](docs/STATUS.md). The source audit is a
targeted credential/artifact check, not a comprehensive security assessment.
