#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null; then
 echo 'Python 3 is required. Read docs/MAC-BUILDER.md.'
 exit 1
fi
echo 'CodeSwarm: build a Debian amd64 installer in a dedicated Linux VM.'
echo '1) Check prerequisites  2) Build clean ISO  3) Create private enrollment ISO  4) Exit'
read -r -p 'Choose 1–4: ' choice
case "$choice" in
 1) python3 builder/mac.py doctor;;
 2) python3 builder/mac.py build;;
 3) python3 builder/mac.py personalize;;
 *) exit 0;;
esac
read -r -p 'Press Enter to close.' unused
