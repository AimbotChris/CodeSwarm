# Licenses and third-party software

CodeSwarm's original project source and artwork are licensed under GPL-3.0-only;
see [LICENSE](LICENSE). Bundled or downloaded third-party software keeps its own
license and terms. CodeSwarm's license does not relicense those components or
provide rights to redistribute proprietary applications.

The Git repository contains recipes, source, fixtures and small project assets.
Vendor binaries, runtime profiles, account credentials and installer images are
excluded. A built ISO contains additional third-party software; publishing the
source repository does not establish that such an image may be redistributed.
Review all component licenses, notices and vendor terms before publishing one.

| Component | Upstream and license/terms reference | How it is obtained |
| --- | --- | --- |
| Debian and packages | [Debian licensing](https://www.debian.org/legal/licenses/) | Signed Debian repositories; individual package licenses apply |
| ChatGPT desktop | [OpenAI terms](https://openai.com/policies/terms-of-use/) | Proprietary, pinned official Debian download in `scripts/fetch-vendor.sh` |
| T3 Code | [Upstream license](https://github.com/pingdotgg/t3code/blob/main/LICENSE) | Pinned upstream Debian release |
| Codex CLI | [Upstream license](https://github.com/openai/codex/blob/main/LICENSE) | Pinned upstream native package, including companion runtimes/notices |
| Claude Code | [Upstream notices and terms](https://github.com/anthropics/claude-code) | Proprietary native platform artifact from the official npm namespace |
| OpenCode | [Upstream license](https://github.com/anomalyco/opencode/blob/dev/LICENSE) | Pinned upstream native baseline x64 release |
| Tailscale | [Upstream license](https://github.com/tailscale/tailscale/blob/main/LICENSE), [service terms](https://tailscale.com/terms) | Signed upstream Debian repository |
| Lima | [Upstream license](https://github.com/lima-vm/lima/blob/master/LICENSE) | Owner-installed build tool; not installed into the target image |

Exact T3/provider artifact versions, URLs and SHA256s are recorded in
`config/toolchain.json`. Claude's native artifact was additionally checked against
npm registry SHA512 integrity when its pin was selected. ChatGPT and Tailscale
repository inputs have separate pins in `scripts/fetch-vendor.sh`; the Debian
cloud image is pinned in `builder/lima.yaml`. Signed APT repositories still evolve,
so future images are not promised to be byte-identical.

Original vendor packages and extracted tool directories retain their notices.
Check the pinned release itself when reviewing licensing, rather than assuming
an upstream default branch has the same terms. Provider accounts, paid services
and subscriptions are supplied separately by the user.

CodeSwarm is independent and is not endorsed by these vendors or projects.
