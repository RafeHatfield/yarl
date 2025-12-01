#!/usr/bin/env bash
# CI Quick: Fast local dev testing script
# Runs fast pytest (excludes slow tests), strict ETP check, and quick loot sanity
# Exit codes propagate from pytest and ETP (fails on test failure or ETP OVER violations)

set -euo pipefail

echo "════════════════════════════════════════════════════════════════════════"
echo "YARL CI QUICK - Fast Dev Test Suite"
echo "════════════════════════════════════════════════════════════════════════"
echo ""

# Ensure SDL dummy driver for headless environments
export SDL_VIDEODRIVER="${SDL_VIDEODRIVER:-dummy}"
export PYTHONUNBUFFERED="${PYTHONUNBUFFERED:-1}"

# Run from repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

echo "Working directory: $REPO_ROOT"
echo ""

# ─────────────────────────────────────────────────────────────────────
# Step 1: Fast pytest (excludes slow tests)
# ─────────────────────────────────────────────────────────────────────
echo "────────────────────────────────────────────────────────────────────────"
echo "Step 1: Fast pytest (excludes slow tests with '-m \"not slow\"')"
echo "────────────────────────────────────────────────────────────────────────"
echo ""

if [ -d tests ]; then
    echo "Running: pytest -q -m \"not slow\""
    pytest -q -m "not slow"
    echo ""
    echo "✓ Fast pytest passed"
else
    echo "No tests/ directory found, skipping pytest"
fi
echo ""

# ─────────────────────────────────────────────────────────────────────
# Step 2: Strict ETP sanity check
# ─────────────────────────────────────────────────────────────────────
echo "────────────────────────────────────────────────────────────────────────"
echo "Step 2: ETP sanity check (strict mode)"
echo "────────────────────────────────────────────────────────────────────────"
echo ""

if [ -x ./scripts/ci_run_etp.sh ]; then
    echo "Running: ./scripts/ci_run_etp.sh"
    ./scripts/ci_run_etp.sh
else
    echo "Running: python3 etp_sanity.py --strict"
    python3 etp_sanity.py --strict 2>&1 | tee etp_sanity.log
fi
echo ""
echo "✓ ETP sanity check passed"
echo ""

# ─────────────────────────────────────────────────────────────────────
# Step 3: Quick loot sanity check (1 run per band)
# ─────────────────────────────────────────────────────────────────────
echo "────────────────────────────────────────────────────────────────────────"
echo "Step 3: Quick loot sanity check (1 run per band)"
echo "────────────────────────────────────────────────────────────────────────"
echo ""

echo "Running: python3 loot_sanity.py --bands --runs 1 --normal"
python3 loot_sanity.py --bands --runs 1 --normal 2>&1 | tee loot_sanity.log

# Surface any CI-specific WARNING lines
if [ -f loot_sanity.log ]; then
    echo ""
    echo "Loot sanity warnings (if any):"
    grep "^WARNING: " loot_sanity.log || echo "  (no balance warnings)"
fi
echo ""

# ─────────────────────────────────────────────────────────────────────
# Done
# ─────────────────────────────────────────────────────────────────────
echo "════════════════════════════════════════════════════════════════════════"
echo "✓ CI Quick completed successfully"
echo "════════════════════════════════════════════════════════════════════════"

