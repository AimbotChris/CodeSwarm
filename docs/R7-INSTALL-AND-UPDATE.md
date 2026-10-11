# Code Swarm OS R7 — approve Tailscale on your Mac or phone

## Existing R6: no reinstall needed

Use `code-swarm-connect-r7-update.tar.gz` and `SHA256SUMS-r7-update`. Verify the archive checksum, extract it, and follow its README. Close Connect Tailscale first. Install the small QR dependency from signed Debian repositories and apply the two-file patch with normal owner sudo authentication:

```sh
sudo apt install --no-install-recommends python3-qrcode
sudo python3 -I install.py
```

No reboot, ChatGPT restart, Tailscale restart, enrollment, network change, or permission change is performed by the patch. Unknown installed file hashes or an active setup helper cause it to stop. It is intended for the verified R6 setup files, not R5 or modified installations. Original files are backed up; `sudo python3 -I install.py --restore` restores only those two files after validation. The QR dependency remains installed. This is not OS rollback or the automatic update system.

## New installation

Verify `SHA256SUMS-r7` before writing the ISO to a deliberately selected USB device. Writing erases that USB. Boot the installer and explicitly choose/approve the target disk only when ready. No target disk or password is preseeded. Recovery and Abort remain available. Hardware compatibility still requires testing on the actual thin client.

Create your local owner account/password. R7 retains R6's tested password-protected sudo and locked root defaults. After login, create/unlock the encrypted keyring and the official desktop app starts. Home remains available with Alt+Tab.

## Connect Tailscale

1. In Home, choose **Connect Tailscale**, then **Approve and connect**. Use your local password in the system prompt.
2. Scan the local QR with your trusted phone, or use **Copy Link** and open it on your Mac. Approve the worker in Tailscale's official browser flow. **Open Firefox here** is optional and never automatic.
3. Keep the setup window open. **Waiting for sign-in**, **waiting for tailnet administrator approval**, and **Connected** are separate states. Connected requires the local daemon to report Running; it is not a claim that every remote service is reachable. If admin approval is pending after setup stops waiting, **Check approval** refreshes status without a new password prompt.

The visible link comes from the current local Tailscale AuthURL. It is strictly limited to the official HTTPS login host and authorization path. QR encoding runs locally; no QR service receives it. Link/QR are cleared on withdrawal, rotation, lost status freshness, approval transition, completion, cancellation or timeout. Only the user chooses to copy or open it. This app clears matching clipboard text when retiring a link, but cannot revoke copies/history on another device or browser history created by explicitly opening Firefox.

Waiting is bounded. Cancel/timeout stops this setup attempt; it does not disable the owner-approved service or revoke a sign-in already completed elsewhere. Retry or refresh status after resolving network/admin approval. Existing configured stopped profiles are not reset.

No remote desktop, public route, Tailscale SSH, exit node or assistant access is enabled by this flow. Enrollment remains your action.

## ChatGPT / Codex sign-in

For the bundled official desktop build, a supported desktop QR/device-code entry has not been established. Choose its **Continue to sign in** and complete the supported local browser flow. The separate documented Codex CLI device-code flow is not assumed to authenticate the desktop. No vendor code, auth handoff or token storage has been modified. See `R7-AUTH-FEASIBILITY.md` for the inspected package and official sources.

## Recovery and scope

Home offers logs, stop/start and a recovery terminal. Ctrl+Alt+F2 opens a normal login console. Process-crash supervision and maintenance suppression are unchanged. No hang detector, global desktop safe drain, automatic update executor or proven OS rollback is claimed. Real account sign-in/enrollment and passkey success were not used in QA; QR visual/decoder tests use clearly synthetic links.
