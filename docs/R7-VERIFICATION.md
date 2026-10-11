# R7 verification

Final ISO: code-swarm-os-debian13-amd64-r7.iso, 3208970240 bytes.
SHA256: ba47f5687e30d75705feeb2b9622ad4537230c36fdc7e2bf20a6e54bfa7eaeea.

## Implemented and tested

The setup window displays only the daemon's current validated HTTPS login.tailscale.com authorization URL. It is selectable; Copy Link and a locally encoded QR support approval on a trusted Mac/phone. Firefox opens only by explicit button action. Python qrcode 8.2-1 comes from the signed Debian repository, with no third-party QR service or new network request for encoding.

NeedsLogin, NeedsMachineAuth and Running are separate states. The helper continues polling during administrator approval and never treats it as connected. A pending admin-status refresh after the attempt ends is read-only and needs no new password prompt. The QR/link and matching clipboard text clear on withdrawal, rotation, status freshness expiry (8 seconds without refresh), cancellation, failure, timeout or completion. Old-attempt events cannot revive a link. Setup remains bounded; service enablement, narrow fixed root helper, polkit authentication and profile-preservation constraints remain in place.

78 Python tests and both fleet frontend suites pass. Coverage includes strict URL rejection, no auto-browser action, copy/clipboard cleanup, stale-link actions, old-attempt events, rotation/withdrawal, approval polling and real-backend-only success. Existing permit expiry/changed-manifest/unmanaged-work tests and fail-closed installer-hook tests remain included. Evidence: evidence/r7-tests.log.

Actual Tk rendering, selection/copy state, QR encoding, clipboard cleanup and waiting-for-admin/connected display were tested in isolated Xvfb using explicitly synthetic fixture links only. An independent zbar decoder recovered the exact synthetic fixture from the generated QR. Screenshots have a visible synthetic warning; no real auth URL was requested, captured or saved. Evidence: evidence/r7-visual-tests.log, r7-synthetic-link.png, r7-synthetic-approval.png. The fixture renderer is not installed in the image.

The final ISO's setup window/helper match tested source bytes. The fail-closed installer command matches release source. Final QR package version is in evidence/packages-r7.tsv. Build logs and payload comparison are retained in evidence/r7-build-final.log, r7-embedded-payload.log and r7-iso-extract.log.

## Existing-R6 patch

code-swarm-connect-r7-update.tar.gz replaces only the two known R6 setup files and adds no service, policy or credential configuration. The owner separately installs the small signed Debian QR dependency, closes setup and explicitly invokes the installer with sudo and Python isolated mode. Unknown file hashes, unsafe target/control ownership, active installed setup processes or a locked helper prevent application. Payload integrity is checked before mutation. Original files are backed up; controlled second-file write failure restores original bytes. Restore refuses modified patched files and leaves the QR package installed.

Tests exercise real file apply/restore, unknown installation refusal, modified-restore refusal, injected partial-write failure, nonroot/active-process rejection, plus real root ownership/path validation in a disposable container fixture. Evidence: r7-tests.log and r7-patch-root-smoke.log. No patch was installed on Chris's device or Agent PC, and no live permission or service changes were made. Two-file restore is not OS rollback.

## Final-image installed acceptance

The exact final ISO completed fresh installation to a new disposable 24 GiB disk, shut down and booted its installed system. The ordinary owner password authenticated normally; missing/three wrong sudo passwords were rejected, the correct password obtained administration, root remained locked, and installer policy/marker checks passed. No root debug shell or account repair was used. See evidence/r7-installed-sudo.log.

The installed QR dependency imports successfully; package versions and both installed setup-file hashes match the final ISO/source. Protected target directories are root-owned mode 0755. Tailscale was disabled/inactive. The new installation generated hostname swarm-<random-id>. See evidence/r7-installed-components.log.

The actual desktop created an encrypted test keyring and launched official ChatGPT to sign-in. Its alternate sign-in choice showed an empty API-key form; no credentials or auth grant were created. Home opened the actual R7 setup UI, and its graphical polkit prompt identified ownerqa. Canceling approval left tailscaled disabled/inactive and no helper/up process. Screenshots include no real approval link or credential. See evidence/r7-installed-cancel.log and r7-app.png, r7-vendor-signin-options.png, r7-installed-connect.png, r7-installed-polkit.png, r7-installed-cancel.png.

No physical hardware or real account sign-in/enrollment is part of QA. UI transitions that require an authentication URL were tested only using synthetic fixtures, not a live control-plane grant.

## Unchanged limits

Official ChatGPT remains 26.1007.21434. No supported desktop QR/device-code entry or unattended/reusable first-login provisioning was established; CLI device auth is not treated as desktop login. Vendor code/auth is untouched. See R7-AUTH-FEASIBILITY.md and official sources there.

No Linux Computer Use, global desktop safe drain, actual unattended update installation, hardware watchdog, A/B fallback or proven OS rollback is claimed. Existing process-crash recovery evidence belongs to R6 and was not repeated for this connection-window revision. Actual network approval/passkey/browser handoff success remains owner-controlled and untested. Connected means the local daemon reports Running, not that every service or peer is reachable.

Build uses retained live-build state and the preserved SHA-pinned original installer boot payload; clean-room or byte-identical reproduction is not claimed. Builder and VM run sequentially under existing 1-CPU limits; guest RAM is 4 GiB within a 5 GiB container. R5/R6 ISOs and private shares are preserved; R7 publication remains a separate owner action.

Final UEFI USB smoke test reached the interactive language chooser and left the sentinel disk hash unchanged (evidence/r7-usb-before.sha256, r7-usb-after.sha256, r7-usb.png). Task-owned builder and QA containers are stopped. QA plaintext secret and password-bearing test preseed/initrd were removed.
