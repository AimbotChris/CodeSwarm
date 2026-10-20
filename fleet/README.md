# Code Swarm OS Workers

From the repository root, run `python3 fleet/server.py`, then open `http://127.0.0.1:8765`. Python standard library only; no npm packages, API keys, credentials or cloud service. The local computer must already be connected to Tailscale. Stop with Ctrl+C. On the installed OS, Home's **Open Workers management** button starts the same loopback-only service.

Real peers come from local `tailscale status --json`. Transport, worker telemetry freshness, graphical session, app process and unknown work/sign-in are separate. The console never infers job idleness. Configured workers are checked over certificate-verified HTTPS, with no redirects or proxy inheritance. Only exact peer hostnames and documented paths are accepted. Unavailable/stale reports clear app/desktop states. Refreshes are cached for 15 seconds; the browser refreshes once per minute while visible.

To configure actual desktop links, follow [remote setup](../product/REMOTE-ACCESS.md) on each installed worker and put its exact addresses in `~/.config/code-swarm/workers.json`. No real worker is enrolled by this project. All endpoints are read-only; there are no reboot, shell, update, enrollment or remote permission mutations. Host-header checks prevent DNS rebinding; the controller binds only 127.0.0.1 and sends no CORS grants. Never publish the controller publicly.

The old browser-local saved inventory is retained as `offline-inventory.html`; it cannot monitor status. It is separate from the live console and makes no discovery claim.

Probe processes enforce total per-peer and aggregate deadlines, including DNS/TLS/trickled responses. At most two probes run at once, and overdue peers return unknown. Concurrent refreshes do not queue behind a lock. The browser independently expires reports/links, refreshes on visibility return and blocks an expired link at click time.

App telemetry describes ChatGPT only. T3 Code, Claude Code, OpenCode and their
authentication or work activity are not monitored. See [current status](../docs/STATUS.md).
