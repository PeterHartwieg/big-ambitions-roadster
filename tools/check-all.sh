#!/usr/bin/env bash
# Full offline regression suite plus official Windows/Mac SDK build, run on the Mac.
# Optional --generate also regenerates the committed prefab/material assets first.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"
python3 -m unittest discover -s tests -v
bash tools/build-mod.sh --check "$@"
