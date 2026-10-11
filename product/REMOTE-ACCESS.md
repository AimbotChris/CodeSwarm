# Code Swarm OS remote access

Run these steps only on the newly installed worker, after its owner approves remote access. Nothing is enrolled or enabled by the ISO. No API key is needed. Verify the physical display works first: the software shares an existing Xorg display; it does not create one. Headless boot/EDID behavior remains a per-model test.

## Choose the first-boot access model

- **Session only:** remote access begins after local OS login. Lower privilege; somebody must log in locally after a power outage. Prepare with `sudo code-swarm-remote-setup --user "$USER" --access-model session`.
- **Authenticated login screen:** permits remote OS login after cold boot, followed by encrypted-keyring unlock. Prepare with `sudo code-swarm-remote-setup --user "$USER" --access-model greeter`. This explicitly chooses a root-owned screen-sharing service that can control the physical login screen and subsequent desktop. Protect it with tailnet ACLs plus separate web and VNC passwords. Enable it only if you accept that access model. It stays off until the activation step below.

Both modes keep normal Debian password authentication and the encrypted keyring. Neither mode automatically resumes signed-in Codex work after a power outage. Greeter mode lets an authorized operator log in remotely; fully unattended keyring unlock remains an unresolved credential-policy choice, not an enabled feature. No blank keyring or autologin is configured.

## Enroll and protect the worker

1. Run `sudo systemctl enable --now tailscaled`, then `sudo tailscale up`. Complete approval in the browser. Check `tailscale status` and review tailnet ACLs. Worker telemetry is readable by devices allowed to reach its HTTPS service. It contains resource/desktop readiness, not usernames, task contents, credentials or account tokens.
2. Set a unique VNC password. For **session mode**, as the desktop owner run `mkdir -p ~/.vnc && chmod 700 ~/.vnc`, then `tigervncpasswd ~/.vnc/passwd`. For **greeter mode**, run `sudo tigervncpasswd /etc/codex-remote/greeter.passwd` and `sudo chmod 600 /etc/codex-remote/greeter.passwd`. Choose no view-only password. Legacy VNC uses only eight effective password characters; it is never exposed outside loopback directly.
3. Set a separate strong web password with `sudo htpasswd -c /etc/codex-remote/web.htpasswd "$USER"`. For later changes omit `-c` to preserve entries. Run `sudo chown root:www-data /etc/codex-remote/web.htpasswd && sudo chmod 640 /etc/codex-remote/web.htpasswd`.
4. Create the nginx site link if absent: `sudo ln -s /etc/nginx/sites-available/codex-remote /etc/nginx/sites-enabled/codex-remote`. Check `sudo nginx -t`. Explicitly approve activation with `sudo touch /etc/codex-remote/enabled`, `sudo chmod 644 /etc/codex-remote/enabled`, then `sudo systemctl enable --now nginx codex-websockify code-swarm-status-broker`.
5. For **session mode**, run `systemctl --user start code-swarm-vnc code-swarm-status`. For **greeter mode**, run `sudo systemctl enable --now code-swarm-greeter-vnc` and `systemctl --user start code-swarm-status`. Future graphical logins start only the chosen owner's session telemetry. The broker starts before login and reports login required or display unavailable rather than claiming the app is ready.
6. Read `tailscale serve status` first. On a new worker with no existing routes, run `sudo tailscale serve --bg http://127.0.0.1:6080`. If there are existing routes, stop and integrate paths deliberately; do not replace another service. Never use Funnel. Tailscale may request explicit HTTPS enablement in its console.
7. On another authorized tailnet device open the returned HTTPS URL plus `/vnc.html`. Authenticate with the web password, then the VNC password. Greeter mode then asks for normal OS login and keyring unlock; session mode shows the already logged-in desktop. The URL plus `/code-swarm-status` should return a small read-only status report. Test a cold reboot locally before placing the worker somewhere unattended.

## Management app

On an already enrolled management computer run `python3 fleet/server.py` (installed copy: `/usr/share/code-swarm/fleet/server.py`). Open `http://127.0.0.1:8765`. Or use Home's **Open Workers management** button. It discovers peers through local `tailscale status --json`; no API key or new tailnet role is required. Put exact worker addresses in `~/.config/code-swarm/workers.json`:

```json
{
  "worker.your-tailnet.ts.net": {
    "desktop_url": "https://worker.your-tailnet.ts.net/vnc.html",
    "status_url": "https://worker.your-tailnet.ts.net/code-swarm-status"
  }
}
```

Use exactly the worker's reported hostname. The console verifies TLS, refuses redirects and unrecognized addresses, and checks report freshness. A desktop button appears only when a fresh report confirms a graphical seat plus VNC and its HTTPS route responds. HTTP401 verifies the password gate, not a successful login. Transport, desktop, app and unknown work/sign-in are separate; stale/error reports clear readiness. Telemetry is advisory and may be influenced by local workloads; it never authorizes an update, access grant or drain.

The console is loopback-only and read-only. Ctrl+C stops its manual launch; Home starts an ordinary user service that can be stopped with `systemctl --user stop code-swarm-fleet`. No controller service is enabled at boot. A Mac controller needs Python3 and Tailscale installed by its owner plus the fleet folder. The offline saved-link inventory remains at `fleet/offline-inventory.html`.

## Revocation and limits

On the dedicated worker, deliberately remove its Serve route, remove `/etc/codex-remote/enabled`, stop owner services `code-swarm-vnc code-swarm-status`, and disable/stop `code-swarm-greeter-vnc code-swarm-status-broker codex-websockify nginx`. Revoke Tailscale enrollment if desired. Preserve unrelated routes/services. This app provides no remote shell, reboot, update-install or permission-grant button.

Virtual tests proved password gates, existing-display VNC, pre-login readiness, noVNC delivery and WebSocket upgrade. Real tailnet HTTPS end-to-end enrollment and physical headless/cold-boot reliability require owner setup and actual hardware testing. Multiple graphical seats/users are not supported; the greeter mode targets LightDM display :0.
