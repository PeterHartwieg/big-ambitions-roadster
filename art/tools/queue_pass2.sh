#!/usr/bin/env bash
# Waits for the first Sol modelling run to end, then starts the second pass with the reveal photos.
# Usage: art/tools/queue_pass2.sh <pid of the first codex run>
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
while kill -0 "$1" 2>/dev/null; do sleep 30; done
"$REPO/art/tools/run_sol_prop.sh" "$REPO/art/roadster-v2" 9877 "$REPO"/art/reference/*.jpg
