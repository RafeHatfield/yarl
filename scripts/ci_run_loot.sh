#!/usr/bin/env bash
# CI helper script for loot/pity sanity checks
# Runs loot_sanity.py --bands --runs 5 --normal and logs output
# Always exits 0 (warnings don't fail CI)

set -euo pipefail

echo "════════════════════════════════════════════════════════════════════════"
echo "LOOT & PITY SANITY CHECK (normal mode)"
echo "════════════════════════════════════════════════════════════════════════"
echo ""

# Ensure SDL dummy driver for headless environments
export SDL_VIDEODRIVER="${SDL_VIDEODRIVER:-dummy}"

# Run from repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

echo "Working directory: $REPO_ROOT"
echo "Running: python3 loot_sanity.py --bands --runs 5 --normal"
echo ""

# Run loot sanity and tee to log file
python3 loot_sanity.py --bands --runs 5 --normal 2>&1 | tee loot_sanity.log

echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo "Loot sanity check complete. Log saved to loot_sanity.log"
echo "════════════════════════════════════════════════════════════════════════"

