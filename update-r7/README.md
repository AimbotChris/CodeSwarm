# R6 → R7 connection-window patch

Owner-installed patch for the verified R6 image. No reinstall or reboot is required. Close Connect Tailscale and finish/cancel any setup attempt before installing. This replaces only its window and fixed-action helper. It does not enroll Tailscale, sign in to ChatGPT, restart services, change network settings, or alter sudo/polkit permissions.

Verify the downloaded archive against SHA256SUMS-r7-update, extract it, and open its directory. Then run:

```sh
sudo apt install --no-install-recommends python3-qrcode
sudo python3 -I install.py
```

The first command installs the small local QR encoder from R6's configured signed Debian repository. No QR service receives a link. The second asks for normal administrator authorization and refuses unknown/modified installed files or active setup processes. Original R6 files are backed up under `/var/lib/code-swarm/patches/connect-r7`. No API keys, auth URLs or credentials are included.

Open Home → Connect Tailscale. Approve local setup, then scan the QR or use Copy Link to approve on your trusted Mac/phone. Local Firefox is optional. Keep the window open; it displays Connected only after the local backend reports Running. Admin approval is shown separately. Cancel/timeout clears the window and this app's copied clipboard text, but does not revoke an already completed sign-in. Clipboard history and copies on other devices cannot be cleared by this window.

To restore the two original setup files, close the window and run `sudo python3 -I install.py --restore` from this same extracted directory. Restore checks the patched file hashes first. The QR dependency remains installed. This is a two-file repair option, not operating-system rollback.

This patch is for the shipped R6 file hashes only, not R5 or a modified installation. No live installation is performed by delivering this archive. Official ChatGPT authentication is unchanged; desktop QR/device-code login is not established for the included vendor version. Use its supported local browser flow.
