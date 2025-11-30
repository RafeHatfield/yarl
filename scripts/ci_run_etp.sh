#!/usr/bin/env bash
# CI helper script for ETP sanity checks
# Runs etp_sanity.py --strict and logs output
# Exit codes propagate: non-zero on OVER violations in normal rooms

set -euo pipefail

echo "════════════════════════════════════════════════════════════════════════"
echo "ETP SANITY CHECK (strict mode)"
echo "════════════════════════════════════════════════════════════════════════"
echo ""

# Ensure SDL dummy driver for headless environments
export SDL_VIDEODRIVER="${SDL_VIDEODRIVER:-dummy}"

# Run from repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

echo "Working directory: $REPO_ROOT"
echo "Running: python3 etp_sanity.py --strict"
echo ""

# Run ETP sanity and tee to log file
# Exit code from etp_sanity.py will propagate due to set -e
python3 etp_sanity.py --strict 2>&1 | tee etp_sanity.log

echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo "ETP sanity check complete. Log saved to etp_sanity.log"
echo "════════════════════════════════════════════════════════════════════════"

