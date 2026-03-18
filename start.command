#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

python3 download_hubble_images.py \
  --input urls.txt \
  --increment-numbers \
  --number-steps 25 \
  --workers 12 \
  "$@"
echo
echo "Finished. Press Enter to close this window."
read -r _
