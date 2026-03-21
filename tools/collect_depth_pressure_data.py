#!/usr/bin/env python3
"""Depth Pressure Data Pack Runner — Phase 22.4 / Phase 23 A/B

Runs a defined set of depth probe scenarios (depths 1–6) via the ecosystem
harness and exports JSON metrics to a timestamped folder.  After all scenarios
complete, calls analysis/depth_pressure_report.py to produce a Markdown +
CSV pressure report.

Usage:
    python3 tools/collect_depth_pressure_data.py [options]

Options:
    --runs N                 Runs per scenario (default: 50)
    --seed-base N            Seed base for deterministic runs (default: 1337)
    --output-dir DIR         Root directory for reports (default: reports/depth_pressure)
    --dry-run                Print commands without executing them
    --no-report              Skip the analysis report step after data collection
    --disable-depth-boons    Run control variant only (boons disabled, flat layout)
    --ab                     Run both variants (ON + OFF) and produce a compare report
    --include-gear-probes    Also run gear pressure probe scenarios (depth3 weapon/armor +1)
    --help                   Show this message

Output (default / --disable-depth-boons):
    reports/depth_pressure/<timestamp>/
        depth1_orc_easy.json
        ...
        depth_pressure_report.md
        depth_pressure_table.csv
        depth_pressure_curve.md
        depth_pressure_curve.png
        manifest.json           (boons_mode: "on" or "off")

Output (--ab):
    reports/depth_pressure/<timestamp>/
        on/
            *.json  manifest.json  depth_pressure_report.md  depth_pressure_table.csv
        off/
            *.json  manifest.json  depth_pressure_report.md  depth_pressure_table.csv
        manifest.json               (top-level; boons_mode: "ab"; written FIRST)
        depth_pressure_compare.md
        depth_pressure_curve.md
        depth_pressure_curve.png

    Open depth_pressure_compare.md first for a side-by-side delta table.
    Each subdir manifest.json records boons_mode: "on" or "off" for that variant.

Reproducibility:
    All runs use --seed-base=1337 by default.  Re-running with the same seed
    and the same game version will produce identical results.  Record the git
    commit SHA alongside the report for future comparison.

Stop conditions:
    The runner fails immediately (non-zero exit) if:
      - ecosystem_sanity.py returns a non-zero exit code for any scenario
      - The JSON export file is not created after a run
    This prevents silently continuing with corrupt or missing data.
"""

import argparse
import datetime
import json
import os
import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Scenario suite definition
# ---------------------------------------------------------------------------

# Each entry is:
#   scenario_id: str       — ID passed to --scenario
#   depth: int             — nominal dungeon depth (documentation only here)
#   faction: str           — human-readable faction note for the report
#   note: str | None       — optional substitution/coverage note
DEPTH_PRESSURE_SUITE = [
    {
        "scenario_id": "depth1_orc_easy",
        "depth": 1,
        "faction": "orc (grunt x2)",
        "note": None,
    },
    {
        "scenario_id": "depth2_orc_baseline",
        "depth": 2,
        "faction": "orc (grunt x3)",
        "note": None,
    },
    {
        "scenario_id": "depth3_orc_brutal",
        "depth": 3,
        "faction": "orc (grunt x4)",
        "note": None,
    },
    {
        "scenario_id": "midgame_pressure_probe_orcs",
        "depth": 4,
        "faction": "orc (grunt + brute + shaman + skirmisher)",
        "note": "Mixed orc composition; depth 4 canary probe.",
    },
    {
        "scenario_id": "depth4_plague",
        "depth": 4,
        "faction": "zombie (plague_zombie x2 + zombie x2)",
        "note": (
            "Second depth-4 data point; DIFFERENT faction from midgame_pressure_probe_orcs. "
            "Zombie curve has no depth scaling (1.0x), so these enemies are less HP-scaled "
            "than orcs at the same depth. Not directly comparable to the orc series."
        ),
    },
    {
        "scenario_id": "depth5_zombie",
        "depth": 5,
        "faction": "zombie (zombie x8)",
        "note": "Zombie curve: no HP/dmg scaling at depth 5 (see ZOMBIE_CURVE in depth_scaling.py).",
    },
    {
        "scenario_id": "depth6_orc_siege",
        "depth": 6,
        "faction": "orc (grunt x2 + brute + skirmisher)",
        "note": (
            "New diagnostic probe created for this data pack (no pre-existing depth-6 "
            "scenario existed). Open arena, loose expectations. Depth 6 = 1.25x HP / "
            "1.12x to-hit / 1.05x damage (DEFAULT_CURVE)."
        ),
    },
]

# Gear pressure probe scenarios — included only when --include-gear-probes is set.
# Identical monster composition to depth3_orc_brutal; only player equipment differs.
GEAR_PROBE_SUITE = [
    {
        "scenario_id": "depth3_orc_brutal_gear_weapon_plus1",
        "depth": 3,
        "faction": "orc (grunt x4)",
        "note": "Gear probe: fine_longsword (+1 to-hit). Not in main suite.",
    },
    {
        "scenario_id": "depth3_orc_brutal_gear_armor_plus1",
        "depth": 3,
        "faction": "orc (grunt x4)",
        "note": "Gear probe: chain_mail (+1 defense). Not in main suite.",
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _timestamp() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def _repo_root() -> Path:
    """Return the repo root (two levels up from tools/)."""
    return Path(__file__).resolve().parent.parent


def _git_sha(repo_root: Path) -> str:
    """Return the short git SHA, or 'unknown' if git is unavailable."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "unknown"


def compute_expected_boons_for_depth(depth: int) -> list[str]:
    """Return the boon IDs a player accumulates before arriving at depth D.

    A fresh character arriving at depth D would have received the boon at each
    depth they traversed (1 through D-1) via next_floor(). Depth 1 is the
    starting depth so no prior traversal exists → returns [].

    This is the deterministic boon budget injected into the ON variant during
    A/B depth pressure analysis so that ON and OFF variants actually differ.

    Examples:
        depth 1 → []
        depth 2 → ["fortitude_10"]
        depth 3 → ["fortitude_10", "accuracy_1"]
        depth 4 → ["fortitude_10", "accuracy_1", "defense_1"]
    """
    # Local import: keeps module-load free of game code, but sources the
    # canonical map so this function never drifts from balance/depth_boons.py.
    # sys.path patch is required when the script runs as a subprocess from
    # tools/ (Python inserts the script's directory, not the repo root).
    _repo = Path(__file__).resolve().parent.parent
    if str(_repo) not in sys.path:
        sys.path.insert(0, str(_repo))
    from balance.depth_boons import DEPTH_BOON_MAP
    return [DEPTH_BOON_MAP[d] for d in range(1, depth) if d in DEPTH_BOON_MAP]


def _build_ecosystem_cmd(
    scenario_id: str,
    runs: int,
    seed_base: int,
    export_path: Path,
    repo_root: Path,
    *,
    disable_depth_boons: bool = False,
    inject_boons: list[str] | None = None,
) -> list[str]:
    """Build the subprocess command for one ecosystem_sanity.py run.

    When disable_depth_boons is True, appends --disable-depth-boons so the
    harness suppresses automatic depth boons for all runs of this scenario.

    When inject_boons is a non-empty list, appends --inject-boons with the
    comma-joined boon IDs (and implies disable_depth_boons in the harness).
    """
    cmd = [
        sys.executable,
        str(repo_root / "ecosystem_sanity.py"),
        "--scenario", scenario_id,
        "--runs", str(runs),
        "--seed-base", str(seed_base),
        "--export-json", str(export_path),
    ]
    if disable_depth_boons:
        cmd.append("--disable-depth-boons")
    if inject_boons:
        cmd.extend(["--inject-boons", ",".join(inject_boons)])
    return cmd


def _run_scenario(
    entry: dict,
    runs: int,
    seed_base: int,
    out_dir: Path,
    dry_run: bool,
    repo_root: Path,
    *,
    disable_depth_boons: bool = False,
    inject_boons: list[str] | None = None,
) -> Path:
    """Run one scenario and return the path to the exported JSON.

    Raises SystemExit on failure.
    """
    scenario_id = entry["scenario_id"]
    export_path = out_dir / f"{scenario_id}.json"
    cmd = _build_ecosystem_cmd(
        scenario_id, runs, seed_base, export_path, repo_root,
        disable_depth_boons=disable_depth_boons,
        inject_boons=inject_boons,
    )

    cmd_str = " ".join(cmd)
    print(f"\n{'=' * 70}")
    print(f"  SCENARIO: {scenario_id}  (depth {entry['depth']}, {entry['faction']})")
    if entry.get("note"):
        print(f"  NOTE:     {entry['note']}")
    print(f"  COMMAND:  {cmd_str}")
    print(f"{'=' * 70}")

    if dry_run:
        print("  [DRY RUN] skipping execution")
        return export_path

    result = subprocess.run(cmd, cwd=str(repo_root))
    if result.returncode != 0:
        print(
            f"\nFATAL: ecosystem_sanity.py exited with code {result.returncode} "
            f"for scenario '{scenario_id}'.\n"
            f"Command was: {cmd_str}\n"
            "Aborting — no further scenarios will be run.",
            file=sys.stderr,
        )
        sys.exit(result.returncode)

    if not export_path.exists():
        print(
            f"\nFATAL: JSON export was not created at '{export_path}' "
            f"after running scenario '{scenario_id}'.\n"
            "This may indicate that --export-json was ignored or the scenario "
            "exited before writing output.\n"
            "Aborting.",
            file=sys.stderr,
        )
        sys.exit(1)

    size = export_path.stat().st_size
    print(f"  OK: exported {size} bytes → {export_path}")
    return export_path


def _write_manifest(
    out_dir: Path,
    suite: list,
    runs: int,
    seed_base: int,
    *,
    boons_mode: str = "on",
    git_sha: str = "unknown",
    extra: dict | None = None,
) -> None:
    """Write a machine-readable manifest.json describing this collection run.

    boons_mode is one of "on", "off", or "ab".
      "on"  — boons enabled (default campaign behaviour)
      "off" — boons disabled (control; --disable-depth-boons was used)
      "ab"  — top-level manifest for a two-variant run
    """
    manifest: dict = {
        "collected_at": datetime.datetime.now().isoformat(),
        "git_sha": git_sha,
        "runs_per_scenario": runs,
        "seed_base": seed_base,
        "boons_mode": boons_mode,
        "scenarios": [
            {
                "scenario_id": e["scenario_id"],
                "depth": e["depth"],
                "faction": e["faction"],
                "note": e.get("note"),
            }
            for e in suite
        ],
    }
    if extra:
        manifest.update(extra)

    manifest_path = out_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nManifest written → {manifest_path}")


def _run_report(out_dir: Path, repo_root: Path, dry_run: bool) -> None:
    """Call analysis/depth_pressure_report.py to produce Markdown + CSV."""
    report_script = repo_root / "analysis" / "depth_pressure_report.py"
    if not report_script.exists():
        print(
            f"\nWARNING: Report generator not found at '{report_script}'. "
            "Skipping report step.",
            file=sys.stderr,
        )
        return

    cmd = [sys.executable, str(report_script), str(out_dir)]
    print(f"\n{'=' * 70}")
    print("  REPORT GENERATION")
    print(f"  COMMAND: {' '.join(cmd)}")
    print(f"{'=' * 70}")

    if dry_run:
        print("  [DRY RUN] skipping execution")
        return

    result = subprocess.run(cmd, cwd=str(repo_root))
    if result.returncode != 0:
        print(
            f"\nWARNING: Report generator exited with code {result.returncode}. "
            "JSON exports are still valid; report may be incomplete.",
            file=sys.stderr,
        )


def _run_compare(
    on_csv: Path,
    off_csv: Path,
    out_md: Path,
    repo_root: Path,
    dry_run: bool,
) -> None:
    """Call analysis/depth_pressure_compare.py to produce the delta report."""
    compare_script = repo_root / "analysis" / "depth_pressure_compare.py"
    if not compare_script.exists():
        print(
            f"\nWARNING: Compare script not found at '{compare_script}'. "
            "Skipping compare step.",
            file=sys.stderr,
        )
        return

    cmd = [sys.executable, str(compare_script), str(on_csv), str(off_csv), str(out_md)]
    print(f"\n{'=' * 70}")
    print("  COMPARE REPORT")
    print(f"  COMMAND: {' '.join(cmd)}")
    print(f"{'=' * 70}")

    if dry_run:
        print("  [DRY RUN] skipping execution")
        return

    result = subprocess.run(cmd, cwd=str(repo_root))
    if result.returncode != 0:
        print(
            f"\nWARNING: Compare script exited with code {result.returncode}. "
            "Variant reports are still valid; compare may be incomplete.",
            file=sys.stderr,
        )
    else:
        print(f"  OK: compare report → {out_md}")


def _run_curve(out_dir: Path, repo_root: Path, dry_run: bool) -> None:
    """Call analysis/depth_pressure_curve.py for a single-variant directory."""
    curve_script = repo_root / "analysis" / "depth_pressure_curve.py"
    if not curve_script.exists():
        print(
            f"\nWARNING: Curve script not found at '{curve_script}'. "
            "Skipping curve generation.",
            file=sys.stderr,
        )
        return

    cmd = [sys.executable, str(curve_script), str(out_dir)]
    print(f"\n{'=' * 70}")
    print("  CURVE GENERATION (single variant)")
    print(f"  COMMAND: {' '.join(cmd)}")
    print(f"{'=' * 70}")

    if dry_run:
        print("  [DRY RUN] skipping execution")
        return

    result = subprocess.run(cmd, cwd=str(repo_root))
    if result.returncode != 0:
        print(
            f"\nWARNING: Curve generator exited with code {result.returncode}. "
            "Reports are still valid; curve may be incomplete.",
            file=sys.stderr,
        )


def _run_curve_ab(
    on_csv: Path,
    off_csv: Path,
    out_dir: Path,
    repo_root: Path,
    dry_run: bool,
) -> None:
    """Call analysis/depth_pressure_curve.py --ab for an A/B run."""
    curve_script = repo_root / "analysis" / "depth_pressure_curve.py"
    if not curve_script.exists():
        print(
            f"\nWARNING: Curve script not found at '{curve_script}'. "
            "Skipping curve generation.",
            file=sys.stderr,
        )
        return

    cmd = [
        sys.executable, str(curve_script),
        "--ab", str(on_csv), str(off_csv), str(out_dir),
    ]
    print(f"\n{'=' * 70}")
    print("  CURVE GENERATION (A/B)")
    print(f"  COMMAND: {' '.join(cmd)}")
    print(f"{'=' * 70}")

    if dry_run:
        print("  [DRY RUN] skipping execution")
        return

    result = subprocess.run(cmd, cwd=str(repo_root))
    if result.returncode != 0:
        print(
            f"\nWARNING: Curve generator exited with code {result.returncode}. "
            "Variant reports are still valid; curve may be incomplete.",
            file=sys.stderr,
        )
    else:
        print(f"  OK: curve report → {out_dir / 'depth_pressure_curve.md'}")


def _run_dashboard(out_dir: Path, repo_root: Path, dry_run: bool) -> None:
    """Call analysis/generate_dashboard.py to produce dashboard.html."""
    dash_script = repo_root / "analysis" / "generate_dashboard.py"
    if not dash_script.exists():
        print(
            f"\nWARNING: Dashboard script not found at '{dash_script}'. "
            "Skipping dashboard generation."
        )
        return

    cmd = [sys.executable, str(dash_script), str(out_dir)]
    print(f"\n{'=' * 70}")
    print("  DASHBOARD GENERATION")
    print(f"  COMMAND: {' '.join(cmd)}")
    print(f"{'=' * 70}")

    if dry_run:
        print("  (dry run — skipped)")
        return

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR: Dashboard generation failed:\n{result.stderr}", file=sys.stderr)
    else:
        print(f"  OK: dashboard → {out_dir / 'dashboard.html'}")


def _run_variant(
    out_dir: Path,
    runs: int,
    seed_base: int,
    dry_run: bool,
    repo_root: Path,
    git_sha: str,
    *,
    disable_depth_boons: bool,
    boons_mode: str,
    inject_boons_by_depth: bool = False,
    suite: list | None = None,
) -> list[Path]:
    """Run a scenario suite for one boon variant.

    Creates out_dir, runs every scenario in the suite, and writes a
    manifest.json into the variant directory.

    Args:
        out_dir: Destination directory for this variant's JSON exports.
        runs: Runs per scenario.
        seed_base: Seed base passed to ecosystem_sanity.py.
        dry_run: When True, print commands without executing.
        repo_root: Repo root for subprocess invocations.
        git_sha: Git SHA to record in the manifest.
        disable_depth_boons: When True, passes --disable-depth-boons to
            ecosystem_sanity.py for every scenario.
        boons_mode: Label recorded in manifest.json ("on" or "off").
        inject_boons_by_depth: When True, injects the expected boon budget for
            each scenario's depth via --inject-boons. Depth-1 scenarios receive
            an empty budget and the flag is omitted. Used for the A/B ON variant.
        suite: Scenario list to run. Defaults to DEPTH_PRESSURE_SUITE.

    Returns:
        List of exported JSON paths (may not exist if dry_run is True).
    """
    if suite is None:
        suite = DEPTH_PRESSURE_SUITE
    out_dir.mkdir(parents=True, exist_ok=True)
    exported_paths = []
    for entry in suite:
        inj: list[str] | None = None
        if inject_boons_by_depth:
            budget = compute_expected_boons_for_depth(entry["depth"])
            inj = budget if budget else None  # omit flag entirely for depth 1
        path = _run_scenario(
            entry=entry,
            runs=runs,
            seed_base=seed_base,
            out_dir=out_dir,
            dry_run=dry_run,
            repo_root=repo_root,
            disable_depth_boons=disable_depth_boons,
            inject_boons=inj,
        )
        exported_paths.append(path)

    manifest_extra: dict | None = None
    if inject_boons_by_depth:
        manifest_extra = {
            "boon_budget_by_depth": {
                str(e["depth"]): compute_expected_boons_for_depth(e["depth"])
                for e in suite
            },
        }
    _write_manifest(
        out_dir, suite, runs, seed_base,
        boons_mode=boons_mode,
        git_sha=git_sha,
        extra=manifest_extra,
    )
    return exported_paths


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--runs", type=int, default=50,
        help="Runs per scenario (default: 50)",
    )
    parser.add_argument(
        "--seed-base", type=int, default=1337,
        help="Seed base for deterministic runs (default: 1337)",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=None,
        help="Root output directory (default: reports/depth_pressure)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print commands without executing them",
    )
    parser.add_argument(
        "--no-report", action="store_true",
        help="Skip the analysis report step after data collection",
    )
    parser.add_argument(
        "--disable-depth-boons", action="store_true",
        help=(
            "Run control variant only: depth boons are disabled for all runs. "
            "Produces a flat output directory (same layout as default). "
            "Cannot be combined with --ab."
        ),
    )
    parser.add_argument(
        "--ab", action="store_true",
        help=(
            "Run both variants (boons ON and boons OFF) and produce a compare report. "
            "Output is split into on/ and off/ subdirectories with a top-level "
            "depth_pressure_compare.md. Cannot be combined with --disable-depth-boons."
        ),
    )
    parser.add_argument(
        "--include-gear-probes", action="store_true",
        help=(
            "Also run gear pressure probe scenarios (depth3_orc_brutal_gear_weapon_plus1 "
            "and depth3_orc_brutal_gear_armor_plus1). Gear probes are appended to the "
            "main suite and appear in all reports. Compatible with --ab."
        ),
    )
    args = parser.parse_args()

    if args.ab and args.disable_depth_boons:
        parser.error("--ab and --disable-depth-boons are mutually exclusive.")

    repo_root = _repo_root()
    # Force cwd to repo root so ecosystem_sanity.py can find config/levels/
    os.chdir(repo_root)

    timestamp = _timestamp()
    base_dir = args.output_dir or (repo_root / "reports" / "depth_pressure")
    out_dir = base_dir / timestamp
    out_dir.mkdir(parents=True, exist_ok=True)

    git_sha = _git_sha(repo_root)

    boons_mode_label = "ab" if args.ab else ("off" if args.disable_depth_boons else "on")

    # Build the effective suite for this run
    effective_suite = (
        DEPTH_PRESSURE_SUITE + GEAR_PROBE_SUITE
        if args.include_gear_probes
        else DEPTH_PRESSURE_SUITE
    )

    print(f"\nDepth Pressure Data Pack Runner")
    print(f"  Timestamp:     {timestamp}")
    print(f"  Output dir:    {out_dir}")
    print(f"  Runs/scenario: {args.runs}")
    print(f"  Seed base:     {args.seed_base}")
    print(f"  Scenarios:     {len(effective_suite)}"
          + (" (incl. gear probes)" if args.include_gear_probes else ""))
    print(f"  Boons mode:    {boons_mode_label}")
    print(f"  Git SHA:       {git_sha}")
    print(f"  Dry run:       {args.dry_run}")

    # Validate all scenario config files exist before running anything
    scenarios_dir = repo_root / "config" / "levels"
    missing = []
    for entry in effective_suite:
        sid = entry["scenario_id"]
        candidate = scenarios_dir / f"scenario_{sid}.yaml"
        if not candidate.exists():
            missing.append((sid, str(candidate)))
    if missing:
        print("\nFATAL: The following scenario files are missing:", file=sys.stderr)
        for sid, path in missing:
            print(f"  scenario_id='{sid}'  expected at: {path}", file=sys.stderr)
        print(
            "\nAdd the missing scenario YAML files or adjust DEPTH_PRESSURE_SUITE "
            "in this script to use existing scenario IDs.",
            file=sys.stderr,
        )
        sys.exit(1)

    print("\nAll scenario files found. Starting runs...\n")

    # -------------------------------------------------------------------------
    # A/B mode: run both variants, produce compare report
    # -------------------------------------------------------------------------
    if args.ab:
        on_dir = out_dir / "on"
        off_dir = out_dir / "off"

        # Write the top-level manifest BEFORE running variants so that any
        # interruption mid-run still leaves a record of what was intended.
        _write_manifest(
            out_dir, effective_suite, args.runs, args.seed_base,
            boons_mode="ab",
            git_sha=git_sha,
            extra={
                "variants": {
                    "on":  str(on_dir),
                    "off": str(off_dir),
                },
                "gear_probes_included": args.include_gear_probes,
            },
        )

        print(f"\n{'#' * 70}")
        print(f"  VARIANT: ON  (boons injected by depth — deterministic ON variant)")
        print(f"  Output:  {on_dir}")
        print(f"{'#' * 70}\n")
        _run_variant(
            on_dir, args.runs, args.seed_base, args.dry_run, repo_root, git_sha,
            disable_depth_boons=False,
            boons_mode="on",
            inject_boons_by_depth=True,
            suite=effective_suite,
        )
        if not args.no_report:
            _run_report(on_dir, repo_root, args.dry_run)

        print(f"\n{'#' * 70}")
        print(f"  VARIANT: OFF  (boons disabled — control)")
        print(f"  Output:  {off_dir}")
        print(f"{'#' * 70}\n")
        _run_variant(
            off_dir, args.runs, args.seed_base, args.dry_run, repo_root, git_sha,
            disable_depth_boons=True,
            boons_mode="off",
            suite=effective_suite,
        )
        if not args.no_report:
            _run_report(off_dir, repo_root, args.dry_run)

        on_csv  = on_dir  / "depth_pressure_table.csv"
        off_csv = off_dir / "depth_pressure_table.csv"
        compare_md = out_dir / "depth_pressure_compare.md"
        _run_compare(on_csv, off_csv, compare_md, repo_root, args.dry_run)
        _run_curve_ab(on_csv, off_csv, out_dir, repo_root, args.dry_run)
        _run_dashboard(out_dir, repo_root, args.dry_run)

        print(f"\n{'=' * 70}")
        print(f"DONE (A/B). Output directory: {out_dir}")
        if not args.dry_run:
            for p in sorted(out_dir.rglob("*")):
                if p.is_file():
                    rel = p.relative_to(out_dir)
                    print(f"  {rel}")
        print(f"{'=' * 70}\n")
        return

    # -------------------------------------------------------------------------
    # Single-variant mode (default or --disable-depth-boons)
    # -------------------------------------------------------------------------
    disable = args.disable_depth_boons
    exported_paths = []
    for entry in effective_suite:
        path = _run_scenario(
            entry=entry,
            runs=args.runs,
            seed_base=args.seed_base,
            out_dir=out_dir,
            dry_run=args.dry_run,
            repo_root=repo_root,
            disable_depth_boons=disable,
        )
        exported_paths.append(path)

    _write_manifest(
        out_dir, effective_suite, args.runs, args.seed_base,
        boons_mode="off" if disable else "on",
        git_sha=git_sha,
        extra={"gear_probes_included": args.include_gear_probes} if args.include_gear_probes else None,
    )

    if not args.no_report:
        _run_report(out_dir, repo_root, args.dry_run)
    _run_curve(out_dir, repo_root, args.dry_run)
    _run_dashboard(out_dir, repo_root, args.dry_run)

    print(f"\n{'=' * 70}")
    print(f"DONE. Output directory: {out_dir}")
    print(f"Files created:")
    for p in sorted(out_dir.iterdir()):
        print(f"  {p.name}")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    main()
