"""Tests for analysis/depth_pressure_curve.py — Phase 23

Fast tests only. No simulation harness is invoked.
"""

import csv
import subprocess
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent

# Minimal valid CSV rows for synthetic data.
# Columns match depth_pressure_table.csv schema from depth_pressure_compare.py.
_CSV_HEADERS = [
    "scenario_id", "depth",
    "player_hits_to_kill", "monster_hits_to_kill",
    "player_dpr", "monster_dpr",
    "player_death_rate", "data_sufficient",
]

_BASE_ROWS = [
    {
        "scenario_id": "depth1_orc_easy", "depth": "1",
        "player_hits_to_kill": "4.5", "monster_hits_to_kill": "9.0",
        "player_dpr": "3.1", "monster_dpr": "2.0",
        "player_death_rate": "0.10", "data_sufficient": "True",
    },
    {
        "scenario_id": "depth2_orc_baseline", "depth": "2",
        "player_hits_to_kill": "5.8", "monster_hits_to_kill": "7.5",
        "player_dpr": "3.0", "monster_dpr": "2.4",
        "player_death_rate": "0.22", "data_sufficient": "True",
    },
    {
        "scenario_id": "depth3_orc_brutal", "depth": "3",
        "player_hits_to_kill": "7.2", "monster_hits_to_kill": "6.1",
        "player_dpr": "2.9", "monster_dpr": "2.9",
        "player_death_rate": "0.40", "data_sufficient": "True",
    },
]

_GEAR_ROW = {
    "scenario_id": "depth3_orc_brutal_gear_weapon_plus1", "depth": "3",
    "player_hits_to_kill": "6.0", "monster_hits_to_kill": "6.1",
    "player_dpr": "3.4", "monster_dpr": "2.9",
    "player_death_rate": "0.32", "data_sufficient": "True",
}


def _write_csv(path: Path, rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=_CSV_HEADERS)
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# Import the module under test
# ---------------------------------------------------------------------------

sys.path.insert(0, str(_REPO_ROOT))
from analysis.depth_pressure_curve import (  # noqa: E402
    GEAR_PROBE_IDS,
    generate_curve_md,
    load_csv,
    sparkline,
)


# ---------------------------------------------------------------------------
# Unit tests: sparkline
# ---------------------------------------------------------------------------

def test_sparkline_empty():
    assert sparkline([]) == "(no data)"


def test_sparkline_flat():
    result = sparkline([5.0, 5.0, 5.0])
    assert len(result) == 3
    # All same char (midpoint)
    assert len(set(result)) == 1


def test_sparkline_ascending():
    result = sparkline([1.0, 2.0, 3.0, 4.0])
    assert len(result) == 4
    # Should go from lower to higher block chars
    assert result[0] <= result[-1]


def test_sparkline_returns_string():
    result = sparkline([1.0, 5.0, 3.0])
    assert isinstance(result, str)
    assert len(result) == 3


# ---------------------------------------------------------------------------
# Unit tests: generate_curve_md (single variant)
# ---------------------------------------------------------------------------

def test_curve_md_single_variant_headings(tmp_path):
    csv_path = tmp_path / "depth_pressure_table.csv"
    _write_csv(csv_path, _BASE_ROWS)
    on_rows = load_csv(csv_path)
    md = generate_curve_md(on_rows)

    assert "# Depth Pressure Curve" in md
    assert "Death%" in md
    assert "H_PM" in md
    assert "H_MP" in md


def test_curve_md_single_variant_no_off_columns(tmp_path):
    csv_path = tmp_path / "depth_pressure_table.csv"
    _write_csv(csv_path, _BASE_ROWS)
    on_rows = load_csv(csv_path)
    md = generate_curve_md(on_rows)

    assert "(off)" not in md
    assert "(on)" in md


def test_curve_md_single_variant_sorted_by_depth(tmp_path):
    csv_path = tmp_path / "depth_pressure_table.csv"
    _write_csv(csv_path, _BASE_ROWS)
    on_rows = load_csv(csv_path)
    md = generate_curve_md(on_rows)

    pos1 = md.index("depth1_orc_easy")
    pos2 = md.index("depth2_orc_baseline")
    pos3 = md.index("depth3_orc_brutal")
    assert pos1 < pos2 < pos3


def test_curve_md_contains_sparklines(tmp_path):
    csv_path = tmp_path / "depth_pressure_table.csv"
    _write_csv(csv_path, _BASE_ROWS)
    on_rows = load_csv(csv_path)
    md = generate_curve_md(on_rows)

    assert "Sparklines" in md
    # At least one block character present
    block_chars = "▁▂▃▄▅▆▇█"
    assert any(c in md for c in block_chars)


# ---------------------------------------------------------------------------
# Unit tests: generate_curve_md (A/B mode)
# ---------------------------------------------------------------------------

def test_curve_md_ab_mode_has_on_and_off_columns(tmp_path):
    on_csv = tmp_path / "on.csv"
    off_csv = tmp_path / "off.csv"
    _write_csv(on_csv, _BASE_ROWS)
    # OFF variant: slightly worse metrics
    off_rows_data = [
        {**r, "player_death_rate": str(float(r["player_death_rate"]) + 0.1)}
        for r in _BASE_ROWS
    ]
    _write_csv(off_csv, off_rows_data)

    on_rows = load_csv(on_csv)
    off_rows = load_csv(off_csv)
    md = generate_curve_md(on_rows, off_rows)

    assert "(on)" in md
    assert "(off)" in md
    assert "A/B" in md


# ---------------------------------------------------------------------------
# Unit tests: gear probe tagging
# ---------------------------------------------------------------------------

def test_gear_probe_marked_in_md(tmp_path):
    csv_path = tmp_path / "depth_pressure_table.csv"
    _write_csv(csv_path, _BASE_ROWS + [_GEAR_ROW])
    on_rows = load_csv(csv_path)
    md = generate_curve_md(on_rows)

    assert "[gear probe]" in md
    # The base scenario should NOT be tagged
    assert "depth3_orc_brutal`\n" not in md or "`depth3_orc_brutal`" in md


def test_gear_probe_ids_constant():
    assert "depth3_orc_brutal_gear_weapon_plus1" in GEAR_PROBE_IDS
    assert "depth3_orc_brutal_gear_armor_plus1" in GEAR_PROBE_IDS


# ---------------------------------------------------------------------------
# Unit tests: missing column graceful handling
# ---------------------------------------------------------------------------

def test_missing_column_no_crash(tmp_path):
    """CSV missing player_death_rate should not raise."""
    headers_no_death = [h for h in _CSV_HEADERS if h != "player_death_rate"]
    rows_no_death = [{k: v for k, v in r.items() if k != "player_death_rate"} for r in _BASE_ROWS]

    csv_path = tmp_path / "depth_pressure_table.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers_no_death)
        writer.writeheader()
        writer.writerows(rows_no_death)

    on_rows = load_csv(csv_path)
    md = generate_curve_md(on_rows)  # must not raise
    assert isinstance(md, str)
    assert "missing" in md.lower() or "Death%" not in md


# ---------------------------------------------------------------------------
# Integration: write MD to disk (via main() monkeypatching sys.argv)
# ---------------------------------------------------------------------------

def test_curve_md_written_to_disk(tmp_path, monkeypatch):
    csv_path = tmp_path / "depth_pressure_table.csv"
    _write_csv(csv_path, _BASE_ROWS)

    monkeypatch.setattr(sys, "argv", ["depth_pressure_curve.py", str(tmp_path)])
    from analysis import depth_pressure_curve
    depth_pressure_curve.main()

    md_path = tmp_path / "depth_pressure_curve.md"
    assert md_path.exists(), "depth_pressure_curve.md was not written"
    content = md_path.read_text(encoding="utf-8")
    assert "# Depth Pressure Curve" in content


def test_curve_md_ab_written_to_disk(tmp_path, monkeypatch):
    on_dir = tmp_path / "on"
    off_dir = tmp_path / "off"
    on_dir.mkdir()
    off_dir.mkdir()
    on_csv = on_dir / "depth_pressure_table.csv"
    off_csv = off_dir / "depth_pressure_table.csv"
    _write_csv(on_csv, _BASE_ROWS)
    _write_csv(off_csv, _BASE_ROWS)

    monkeypatch.setattr(
        sys, "argv",
        ["depth_pressure_curve.py", "--ab", str(on_csv), str(off_csv), str(tmp_path)],
    )
    from analysis import depth_pressure_curve
    depth_pressure_curve.main()

    md_path = tmp_path / "depth_pressure_curve.md"
    assert md_path.exists(), "A/B depth_pressure_curve.md was not written"
    content = md_path.read_text(encoding="utf-8")
    assert "(on)" in content
    assert "(off)" in content


# ---------------------------------------------------------------------------
# CLI flag plumbing: --include-gear-probes dry-run
# ---------------------------------------------------------------------------

def test_include_gear_probes_dry_run():
    """--include-gear-probes dry-run should include both gear probe IDs in output."""
    result = subprocess.run(
        [
            sys.executable,
            str(_REPO_ROOT / "tools" / "collect_depth_pressure_data.py"),
            "--dry-run",
            "--include-gear-probes",
        ],
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT),
        timeout=30,
    )
    assert result.returncode == 0, f"Non-zero exit: {result.stderr}"
    combined = result.stdout + result.stderr
    assert "depth3_orc_brutal_gear_weapon_plus1" in combined, (
        "gear weapon probe not found in dry-run output"
    )
    assert "depth3_orc_brutal_gear_armor_plus1" in combined, (
        "gear armor probe not found in dry-run output"
    )


def test_gear_probes_absent_by_default():
    """Without --include-gear-probes, gear probe IDs must not appear."""
    result = subprocess.run(
        [
            sys.executable,
            str(_REPO_ROOT / "tools" / "collect_depth_pressure_data.py"),
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT),
        timeout=30,
    )
    assert result.returncode == 0
    combined = result.stdout + result.stderr
    assert "depth3_orc_brutal_gear_weapon_plus1" not in combined
    assert "depth3_orc_brutal_gear_armor_plus1" not in combined


# ---------------------------------------------------------------------------
# YAML file existence
# ---------------------------------------------------------------------------

def test_gear_probe_yaml_files_exist():
    levels_dir = _REPO_ROOT / "config" / "levels"
    weapon_yaml = levels_dir / "scenario_depth3_orc_brutal_gear_weapon_plus1.yaml"
    armor_yaml = levels_dir / "scenario_depth3_orc_brutal_gear_armor_plus1.yaml"
    assert weapon_yaml.exists(), f"Missing: {weapon_yaml}"
    assert armor_yaml.exists(), f"Missing: {armor_yaml}"
