# Official desktop authentication: examined, not modified

This document describes the historical R7 image. See [current status](STATUS.md)
and [coding workflows](WORKFLOWS.md) for the newer source. Referenced release
artifacts are not supplied by this repository.

The installed official ChatGPT package is 26.1007.21434. Its packaged login route contains Continue to sign in, a browser continuation/copy-link fallback, and API-key/Bedrock branches. In the actual installed VM, Sign in another way opened an empty API-key form, with no QR/device-code choice. No credentials were entered or grant started. No device-code/QR entry is exposed by that first-login route. Shared internal code contains a device-code session method; that alone does not establish a supported user-facing desktop login path, and no internal APIs or feature flags were invoked.

Official OpenAI authentication documentation specifies Continue to sign in followed by the browser flow for the desktop app. Its device-code instructions explicitly describe Codex CLI (`codex login --device-auth`, subject to account/workspace settings). CLI login is not assumed to authenticate this desktop app, and no credentials are copied between devices or profiles.

Consequently R7 leaves vendor authentication untouched. Use the desktop's supported local browser sign-in; any passkey options depend on the official identity-provider/browser flow and actual hardware. The vendor documents local session caching and token refresh, but no real account was used to validate that behavior here. A QR wrapped around a desktop callback URL is not implemented or claimed to work on another device.

Sources checked 2026-10-11:
- https://learn.chatgpt.com/docs/auth — desktop and separate headless CLI instructions.
- https://learn.chatgpt.com/docs/linux/linux-app — official Linux package/support.
- Local signed package resources/app.asar, login-route-cd5e75fe07da.js and shared device-code session implementation (read only; no vendor-file changes).

The new Tailscale QR is a different, supported device-approval flow. Its source is the local daemon's current AuthURL; its QR is generated locally. Tailscale 1.104.1 defines AuthURL as the current control-provided client authorization URL, and separates NeedsLogin, NeedsMachineAuth and Running:
https://github.com/tailscale/tailscale/blob/v1.104.1/ipn/ipnstate/ipnstate.go

## Personalized ISO architecture question

A user can build a personalized image containing non-secret configuration, software choices and an enrollment UI. That does not make desktop account provisioning unattended. For the examined official desktop build, no supported reusable device grant or unattended first-login provisioning interface was established. Internal device-code implementation is not authorization to invoke hidden flows, and CLI device auth remains a separate documented surface.

The verified R7 artifact generates an installation-specific hostname and contains no machine IDs, Tailscale state, OpenAI sessions, keys, tokens or authenticated profiles. The newer Mac builder supports an explicitly selected private Tailscale auth-key overlay; that image is credential-bearing, has independent per-install identity, and still does not provision Codex login. See [Mac builder](MAC-BUILDER.md). This newer path has synthetic tests only. No real credentials were inspected or copied, and no live grants were started.
