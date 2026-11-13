#!/usr/bin/env bash
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"
python3 -m unittest discover -s tests -v
bash tools/build-mod.sh --check "$@"
