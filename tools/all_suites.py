#!/usr/bin/env python3
"""All Suites Runner - Orchestrates running all test suites in sequence.

Phase 22.4: Runs all test suites in a deterministic order:
  1. Identity Suite - mechanic identity and invariants
  2. Hazards Suite - trap and environmental correctness
  3. Balance Suite - ecosystem outcome drift

Usage:
    python3 tools/all_suites.py
    python3 tools/all_suites.py --seed-base 42
    python3 tools/all_suites.py --skip-balance
"""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Tuple


def run_suite(name: str, cmd: List[str]) -> Tuple[bool, str]:
    """Run a single suite and return result.

    Args:
        name: Suite name for display
        cmd: Command to run

    Returns:
        Tuple of (success: bool, output: str)
    """
    print(f"\n{'='*60}")
    print(f"Running: {name}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}\n")

    try:
        result = subprocess.run(cmd, capture_output=False, text=True, check=False)
        return result.returncode == 0, ""
    except Exception as e:
        return False, str(e)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run all test suites in sequence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--seed-base",
        type=int,
        default=1337,
        help="Base seed for deterministic runs (default: 1337)",
    )
    parser.add_argument(
        "--skip-identity",
        action="store_true",
        help="Skip the identity suite",
    )
    parser.add_argument(
        "--skip-hazards",
        action="store_true",
        help="Skip the hazards suite",
    )
    parser.add_argument(
        "--skip-balance",
        action="store_true",
        help="Skip the balance suite",
    )

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("All Suites Runner - Orchestrated Test Suite Execution")
    print("=" * 60)
    print(f"Seed Base: {args.seed_base}")
    print(f"Skip Identity: {args.skip_identity}")
    print(f"Skip Hazards: {args.skip_hazards}")
    print(f"Skip Balance: {args.skip_balance}")
    print("=" * 60)

    results = []
    start_time = datetime.now()

    # Suite 1: Identity Suite
    if not args.skip_identity:
        cmd = ["python3", "tools/identity_suite.py", "--seed-base", str(args.seed_base)]
        success, _ = run_suite("Identity Suite", cmd)
        results.append(("Identity Suite", success))
    else:
        print("\n⏭️  Skipping Identity Suite")
        results.append(("Identity Suite", None))

    # Suite 2: Hazards Suite
    if not args.skip_hazards:
        cmd = ["python3", "tools/hazards_suite.py", "--seed-base", str(args.seed_base)]
        success, _ = run_suite("Hazards Suite", cmd)
        results.append(("Hazards Suite", success))
    else:
        print("\n⏭️  Skipping Hazards Suite")
        results.append(("Hazards Suite", None))

    # Suite 3: Balance Suite
    if not args.skip_balance:
        cmd = ["python3", "tools/balance_suite.py", "--seed-base", str(args.seed_base)]
        success, _ = run_suite("Balance Suite", cmd)
        results.append(("Balance Suite", success))
    else:
        print("\n⏭️  Skipping Balance Suite")
        results.append(("Balance Suite", None))

    # Summary
    end_time = datetime.now()
    duration = end_time - start_time

    print("\n" + "=" * 60)
    print("All Suites - Summary")
    print("=" * 60)
    print(f"Duration: {duration}")
    print()

    all_pass = True
    for name, success in results:
        if success is None:
            status = "SKIPPED"
        elif success:
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
            all_pass = False
        print(f"  {name}: {status}")

    print()

    if all_pass:
        print("✅ All Suites PASSED")
        print("=" * 60 + "\n")
        return 0
    else:
        print("❌ Some Suites FAILED")
        print("=" * 60 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
