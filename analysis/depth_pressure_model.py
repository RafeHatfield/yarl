"""Depth Pressure Model — Phase 22.4

Formal derivation layer for dungeon depth progression balance.

This module:
  - Accepts aggregated scenario metrics (from scenario harness runs)
  - Computes derived combat invariants per the formal definitions
  - Extracts observed depth curves
  - Defines target curve proposals (documentation only, not enforced)
  - Derives required damage multipliers to meet targets (report only)

Definitions (canonical):
  E[DMG_P] = average player damage per landed hit
  P(hit_P) = player hit rate
  E[DMG_M] = average monster damage per landed hit
  P(hit_M) = monster hit rate
  HP_P     = average player HP at start
  HP_M     = average HP of spawned monster type

  DPR_P = E[DMG_P] * P(hit_P)   (player damage per round)
  DPR_M = E[DMG_M] * P(hit_M)   (monster damage per round)

  H_PM  = HP_M / DPR_P          (player hits-to-kill monster)
  H_MP  = HP_P / DPR_M          (monster hits-to-kill player)

  Damage per encounter = total monster damage / enemies killed

All math is derived from observed scenario data. No guessing.

Usage:
    from analysis.depth_pressure_model import (
        compute_pressure_metrics,
        build_depth_curve,
        derive_required_damage_multiplier,
        print_pressure_report,
    )
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# =============================================================================
# Derived Pressure Metrics
# =============================================================================

@dataclass
class PressureMetrics:
    """Derived combat invariants for a single scenario/depth."""
    depth: int
    scenario_id: str
    runs: int

    # Raw inputs (from aggregated metrics)
    total_player_attacks: int = 0
    total_player_hits: int = 0
    total_monster_attacks: int = 0
    total_monster_hits: int = 0
    total_player_damage_dealt: int = 0
    total_monster_damage_dealt: int = 0
    total_kills: int = 0
    total_turns: float = 0.0
    player_deaths: int = 0
    player_hp: int = 54  # Default player HP from entities.yaml

    # Monster HP context (sum of all spawned monster max HP per run)
    monster_hp_budget_per_run: float = 0.0

    # Derived metrics
    player_hit_rate: float = 0.0      # P(hit_P)
    monster_hit_rate: float = 0.0     # P(hit_M)
    avg_player_dmg_per_hit: float = 0.0  # E[DMG_P]
    avg_monster_dmg_per_hit: float = 0.0  # E[DMG_M]
    player_dpr: float = 0.0           # DPR_P = E[DMG_P] * P(hit_P)
    monster_dpr: float = 0.0          # DPR_M = E[DMG_M] * P(hit_M)
    player_hits_to_kill: float = 0.0  # H_PM = HP_M / DPR_P
    monster_hits_to_kill: float = 0.0  # H_MP = HP_P / DPR_M
    avg_damage_per_encounter: float = 0.0  # total monster dmg / kills
    avg_turns_per_enemy: float = 0.0  # turns / kills
    player_death_rate: float = 0.0    # deaths / runs

    # Data quality flags
    data_sufficient: bool = True
    warnings: List[str] = field(default_factory=list)


def compute_pressure_metrics(
    aggregated_metrics: Dict[str, Any],
    scenario_id: str,
    depth: int,
    monster_hp_budget_per_run: float,
    player_hp: int = 54,
) -> PressureMetrics:
    """Compute derived pressure metrics from aggregated scenario data.

    Args:
        aggregated_metrics: Dictionary from AggregatedMetrics.to_dict()
        scenario_id: Scenario identifier
        depth: Dungeon depth for this scenario
        monster_hp_budget_per_run: Total monster max HP spawned per run
            (e.g., 3 orc grunts at 28 HP each at depth 2 = 84)
        player_hp: Player starting HP (default 54 from entities.yaml)

    Returns:
        PressureMetrics with all derived invariants computed
    """
    pm = PressureMetrics(
        depth=depth,
        scenario_id=scenario_id,
        runs=aggregated_metrics.get('runs', 1),
        player_hp=player_hp,
        monster_hp_budget_per_run=monster_hp_budget_per_run,
    )

    # Extract raw values
    pm.total_player_attacks = aggregated_metrics.get('total_player_attacks', 0)
    pm.total_player_hits = aggregated_metrics.get('total_player_hits', 0)
    pm.total_monster_attacks = aggregated_metrics.get('total_monster_attacks', 0)
    pm.total_monster_hits = aggregated_metrics.get('total_monster_hits', 0)
    pm.total_player_damage_dealt = aggregated_metrics.get('total_player_damage_dealt', 0)
    pm.total_monster_damage_dealt = aggregated_metrics.get('total_monster_damage_dealt', 0)
    pm.total_kills = aggregated_metrics.get('total_kills_by_source', {}).get('PLAYER', 0)
    pm.total_turns = aggregated_metrics.get('average_turns', 0) * pm.runs
    pm.player_deaths = aggregated_metrics.get('player_deaths', 0)

    # ─── STOP CONDITION CHECKS ───────────────────────────────────────────
    if pm.total_player_attacks == 0:
        pm.data_sufficient = False
        pm.warnings.append("STOP: No player attacks recorded — cannot derive hit rate")
        return pm

    if pm.total_monster_attacks == 0:
        pm.data_sufficient = False
        pm.warnings.append("STOP: No monster attacks recorded — cannot derive hit rate")
        return pm

    if pm.total_player_hits == 0:
        pm.data_sufficient = False
        pm.warnings.append("STOP: No player hits recorded — DPR_P would be zero")
        return pm

    if pm.total_player_damage_dealt == 0:
        pm.data_sufficient = False
        pm.warnings.append("STOP: No player damage recorded — instrumentation may be missing")
        return pm

    if pm.total_kills == 0:
        pm.data_sufficient = False
        pm.warnings.append("STOP: No kills recorded — cannot compute turns-per-enemy")
        return pm

    # ─── DERIVED COMPUTATIONS ────────────────────────────────────────────

    # Hit rates
    pm.player_hit_rate = pm.total_player_hits / pm.total_player_attacks
    pm.monster_hit_rate = (
        pm.total_monster_hits / pm.total_monster_attacks
        if pm.total_monster_attacks > 0 else 0.0
    )

    # Average damage per landed hit
    pm.avg_player_dmg_per_hit = (
        pm.total_player_damage_dealt / pm.total_player_hits
        if pm.total_player_hits > 0 else 0.0
    )
    pm.avg_monster_dmg_per_hit = (
        pm.total_monster_damage_dealt / pm.total_monster_hits
        if pm.total_monster_hits > 0 else 0.0
    )

    # Damage Per Round (DPR)
    pm.player_dpr = pm.avg_player_dmg_per_hit * pm.player_hit_rate
    pm.monster_dpr = pm.avg_monster_dmg_per_hit * pm.monster_hit_rate

    # Hits-to-kill invariants
    # H_PM = average monster HP / player DPR
    avg_monster_hp = monster_hp_budget_per_run / max(1, pm.total_kills / pm.runs)
    if pm.player_dpr > 0:
        pm.player_hits_to_kill = avg_monster_hp / pm.player_dpr
    else:
        pm.player_hits_to_kill = float('inf')
        pm.warnings.append("WARNING: Player DPR is zero — hits-to-kill is infinite")

    # H_MP = player HP / monster DPR
    if pm.monster_dpr > 0:
        pm.monster_hits_to_kill = pm.player_hp / pm.monster_dpr
    else:
        pm.monster_hits_to_kill = float('inf')
        pm.warnings.append("WARNING: Monster DPR is zero — monster hits-to-kill is infinite")

    # Damage taken per encounter
    if pm.total_kills > 0:
        pm.avg_damage_per_encounter = pm.total_monster_damage_dealt / pm.total_kills
    else:
        pm.avg_damage_per_encounter = 0.0

    # Average turns per enemy killed
    if pm.total_kills > 0:
        pm.avg_turns_per_enemy = pm.total_turns / pm.total_kills

    # Death rate
    pm.player_death_rate = pm.player_deaths / pm.runs if pm.runs > 0 else 0.0

    # ─── DATA QUALITY WARNINGS ───────────────────────────────────────────
    if pm.player_hit_rate < 0.20:
        pm.warnings.append(
            f"WARNING: Player hit rate unusually low ({pm.player_hit_rate:.1%})"
        )
    if pm.monster_hit_rate < 0.10:
        pm.warnings.append(
            f"WARNING: Monster hit rate unusually low ({pm.monster_hit_rate:.1%})"
        )
    if pm.player_hit_rate > 0.95:
        pm.warnings.append(
            f"WARNING: Player hit rate unusually high ({pm.player_hit_rate:.1%}) — "
            "may indicate evasion/AC imbalance"
        )

    return pm


# =============================================================================
# Depth Curve Extraction
# =============================================================================

@dataclass
class DepthCurvePoint:
    """Single point on the observed depth curve."""
    depth: int
    avg_player_hits_to_kill: float
    avg_monster_hits_to_kill: float
    avg_damage_per_encounter: float
    avg_turns_per_enemy: float
    player_dpr: float
    monster_dpr: float
    player_hit_rate: float
    monster_hit_rate: float
    player_death_rate: float
    scenario_id: str


def build_depth_curve(
    pressure_data: List[PressureMetrics],
) -> Dict[int, DepthCurvePoint]:
    """Aggregate PressureMetrics into a depth-indexed curve.

    Args:
        pressure_data: List of PressureMetrics from different depth scenarios

    Returns:
        Dict mapping depth -> DepthCurvePoint
    """
    curve: Dict[int, DepthCurvePoint] = {}

    for pm in pressure_data:
        if not pm.data_sufficient:
            logger.warning(
                f"Skipping depth {pm.depth} ({pm.scenario_id}): "
                f"insufficient data — {pm.warnings}"
            )
            continue

        curve[pm.depth] = DepthCurvePoint(
            depth=pm.depth,
            avg_player_hits_to_kill=pm.player_hits_to_kill,
            avg_monster_hits_to_kill=pm.monster_hits_to_kill,
            avg_damage_per_encounter=pm.avg_damage_per_encounter,
            avg_turns_per_enemy=pm.avg_turns_per_enemy,
            player_dpr=pm.player_dpr,
            monster_dpr=pm.monster_dpr,
            player_hit_rate=pm.player_hit_rate,
            monster_hit_rate=pm.monster_hit_rate,
            player_death_rate=pm.player_death_rate,
            scenario_id=pm.scenario_id,
        )

    return curve


def depth_curve_to_dict(curve: Dict[int, DepthCurvePoint]) -> Dict[int, Dict[str, Any]]:
    """Convert depth curve to serializable dictionary.

    Returns:
        {depth: {metric: value, ...}, ...}
    """
    result = {}
    for depth, point in sorted(curve.items()):
        result[depth] = {
            'avg_player_hits_to_kill': round(point.avg_player_hits_to_kill, 2),
            'avg_monster_hits_to_kill': round(point.avg_monster_hits_to_kill, 2),
            'avg_damage_per_encounter': round(point.avg_damage_per_encounter, 2),
            'avg_turns_per_enemy': round(point.avg_turns_per_enemy, 2),
            'player_dpr': round(point.player_dpr, 2),
            'monster_dpr': round(point.monster_dpr, 2),
            'player_hit_rate': round(point.player_hit_rate, 3),
            'monster_hit_rate': round(point.monster_hit_rate, 3),
            'player_death_rate': round(point.player_death_rate, 3),
            'scenario_id': point.scenario_id,
        }
    return result


# =============================================================================
# Target Curve Proposals (Documentation Only — Not Enforced)
# =============================================================================
#
# Design rationale:
#
# Player hits-to-kill (H_PM) — How many effective rounds to kill one monster.
#   - Too low (< 3): Monsters feel trivial, no tactical decisions needed.
#   - Too high (> 7): Attrition death spiral; player runs out of resources.
#   - Sweet spot: 3.5–6 depending on depth, scaling upward gradually.
#
# Monster hits-to-kill (H_MP) — How many effective monster rounds to kill player.
#   - This is the SURVIVAL BUDGET. Lower = more lethal.
#   - Too high (> 15): Player never feels threatened, game is boring.
#   - Too low (< 6): Player dies before tactical options matter.
#   - Must decrease with depth to create pressure, but not collapse.
#
# Action economy relationship:
#   - If player faces N monsters, effective pressure = N * monster_dpr.
#   - H_MP / N = turns before death against N monsters (without healing).
#   - At depth 2 (3 orcs), H_MP=12 gives ~4 turns to act (12/3).
#   - At depth 5 (8 zombies), H_MP=9 gives ~1.1 turns (9/8) — very lethal.
#   - This is why H_MP must account for typical encounter size.
#
# Anti-attrition design:
#   - HP-only scaling increases H_PM without increasing H_MP pressure.
#   - This makes fights LONGER but not MORE DANGEROUS.
#   - Result: player loses by attrition (resource drain) not tactical failure.
#   - Damage scaling maintains the ratio: harder monsters are both tougher AND deadlier.
#

# Legacy target dicts retained for backward compatibility with existing callers.
# Single source of truth is now balance.target_bands.TARGET_BANDS.
# These are derived from the new per-depth targets for callers that
# still reference the old 2-depth-band format.
try:
    from balance.target_bands import TARGET_BANDS as _TB, evaluate_metric
except ImportError:
    _TB = None
    evaluate_metric = None

TARGET_PLAYER_HITS_TO_KILL: Dict[str, Tuple[float, float]] = {
    "1-2": (3.5, 4.5),
    "3-4": (4.0, 5.0),
    "5-6": (4.5, 5.5),
    "7-8": (5.0, 6.0),
    "9+":  (6.0, 7.0),
}

TARGET_MONSTER_HITS_TO_KILL: Dict[str, Tuple[float, float]] = {
    "1-2": (10.0, 14.0),
    "3-4": (9.0, 12.0),
    "5-6": (8.0, 10.0),
    "7-8": (7.0, 9.0),
    "9+":  (6.0, 8.0),
}


def get_target_band(depth: int) -> str:
    """Map depth to legacy target curve band key."""
    if depth <= 2:
        return "1-2"
    elif depth <= 4:
        return "3-4"
    elif depth <= 6:
        return "5-6"
    elif depth <= 8:
        return "7-8"
    else:
        return "9+"


def evaluate_against_targets(
    curve: Dict[int, DepthCurvePoint],
) -> Dict[int, Dict[str, Any]]:
    """Compare observed curve against target ranges.

    Uses per-depth target bands from balance.target_bands when available,
    falling back to legacy 2-depth bands otherwise.

    Returns:
        {depth: {
            'h_pm_observed', 'h_pm_target', 'h_pm_status',
            'h_mp_observed', 'h_mp_target', 'h_mp_status',
            'death_rate_observed', 'death_rate_target', 'death_rate_status',
            'feel', 'diagnosis',
        }}
    """
    results = {}
    for depth, point in sorted(curve.items()):
        # Try per-depth targets first (new system)
        tb = _TB.get(depth) if _TB else None

        if tb is not None:
            from balance.target_bands import diagnose, evaluate_depth
            death_rate = point.player_death_rate if hasattr(point, 'player_death_rate') else (
                point.total_deaths / point.total_runs if hasattr(point, 'total_deaths') else 0.0
            )
            ev = evaluate_depth(
                depth,
                observed_death_rate=death_rate,
                observed_h_pm=point.avg_player_hits_to_kill,
                observed_h_mp=point.avg_monster_hits_to_kill,
            )
            diag = diagnose(ev)
            results[depth] = {
                'h_pm_observed': ev['h_pm']['observed'],
                'h_pm_target': ev['h_pm']['target'],
                'h_pm_status': ev['h_pm']['status'],
                'h_mp_observed': ev['h_mp']['observed'],
                'h_mp_target': ev['h_mp']['target'],
                'h_mp_status': ev['h_mp']['status'],
                'death_rate_observed': ev['death_rate']['observed'],
                'death_rate_target': ev['death_rate']['target'],
                'death_rate_status': ev['death_rate']['status'],
                'feel': ev['feel'],
                'diagnosis': diag,
            }
        else:
            # Fallback to legacy 2-depth bands (for depths 7+)
            band = get_target_band(depth)
            h_pm_lo, h_pm_hi = TARGET_PLAYER_HITS_TO_KILL[band]
            h_mp_lo, h_mp_hi = TARGET_MONSTER_HITS_TO_KILL[band]

            def _status(observed: float, lo: float, hi: float) -> str:
                if observed < lo:
                    return "LOW"
                elif observed > hi:
                    return "HIGH"
                return "OK"

            results[depth] = {
                'h_pm_observed': round(point.avg_player_hits_to_kill, 2),
                'h_pm_target': (h_pm_lo, h_pm_hi),
                'h_pm_status': _status(point.avg_player_hits_to_kill, h_pm_lo, h_pm_hi),
                'h_mp_observed': round(point.avg_monster_hits_to_kill, 2),
                'h_mp_target': (h_mp_lo, h_mp_hi),
                'h_mp_status': _status(point.avg_monster_hits_to_kill, h_mp_lo, h_mp_hi),
                'death_rate_observed': None,
                'death_rate_target': None,
                'death_rate_status': None,
                'feel': None,
                'diagnosis': [],
            }
    return results


# =============================================================================
# Required Damage Multiplier Derivation (Report Only — Does NOT Apply)
# =============================================================================

def derive_required_damage_multiplier(
    curve: Dict[int, DepthCurvePoint],
    target_h_mp: Optional[Dict[str, Tuple[float, float]]] = None,
) -> Dict[int, Dict[str, Any]]:
    """Derive the damage multiplier needed to bring H_MP into target range.

    This function computes what the monster damage multiplier WOULD need to be
    to achieve the target H_MP (monster hits-to-kill-player) at each depth.

    It does NOT modify any scaling values. Output is for reporting only.

    Mathematical derivation:
        H_MP = HP_P / DPR_M
        DPR_M = E[DMG_M] * P(hit_M)

        To achieve target_H_MP:
            target_DPR_M = HP_P / target_H_MP
            required_E_DMG_M = target_DPR_M / P(hit_M)
            multiplier = required_E_DMG_M / observed_E_DMG_M

    Args:
        curve: Observed depth curve from build_depth_curve()
        target_h_mp: Target ranges (defaults to TARGET_MONSTER_HITS_TO_KILL)

    Returns:
        {depth: {
            'observed_h_mp': float,
            'target_h_mp_midpoint': float,
            'observed_monster_dpr': float,
            'required_monster_dpr': float,
            'observed_avg_monster_dmg': float,
            'required_avg_monster_dmg': float,
            'recommended_damage_multiplier': float,
            'adjustment_needed': bool,
        }}
    """
    if target_h_mp is None:
        target_h_mp = TARGET_MONSTER_HITS_TO_KILL

    results = {}
    for depth, point in sorted(curve.items()):
        band = get_target_band(depth)
        h_mp_lo, h_mp_hi = target_h_mp[band]
        target_midpoint = (h_mp_lo + h_mp_hi) / 2.0

        observed_h_mp = point.avg_monster_hits_to_kill

        # If already in range, multiplier = 1.0 (no change needed)
        if h_mp_lo <= observed_h_mp <= h_mp_hi:
            results[depth] = {
                'observed_h_mp': round(observed_h_mp, 2),
                'target_h_mp_midpoint': round(target_midpoint, 2),
                'observed_monster_dpr': round(point.monster_dpr, 2),
                'required_monster_dpr': round(point.monster_dpr, 2),
                'observed_avg_monster_dmg': round(
                    point.monster_dpr / point.monster_hit_rate
                    if point.monster_hit_rate > 0 else 0.0, 2
                ),
                'required_avg_monster_dmg': round(
                    point.monster_dpr / point.monster_hit_rate
                    if point.monster_hit_rate > 0 else 0.0, 2
                ),
                'recommended_damage_multiplier': 1.0,
                'adjustment_needed': False,
            }
            continue

        # Derive required DPR_M to hit target midpoint
        # H_MP_target = HP_P / DPR_M_required
        # DPR_M_required = HP_P / H_MP_target
        player_hp = point.avg_monster_hits_to_kill * point.monster_dpr  # reconstruct HP_P
        if player_hp <= 0:
            # Fallback: use default
            player_hp = 54

        required_dpr_m = player_hp / target_midpoint if target_midpoint > 0 else point.monster_dpr

        # Derive required average monster damage per hit
        # DPR_M = E[DMG_M] * P(hit_M)
        # required_E_DMG_M = required_DPR_M / P(hit_M)
        observed_avg_dmg = (
            point.monster_dpr / point.monster_hit_rate
            if point.monster_hit_rate > 0 else 0.0
        )
        required_avg_dmg = (
            required_dpr_m / point.monster_hit_rate
            if point.monster_hit_rate > 0 else 0.0
        )

        # Multiplier = required / observed
        if observed_avg_dmg > 0:
            multiplier = required_avg_dmg / observed_avg_dmg
        else:
            multiplier = 1.0

        results[depth] = {
            'observed_h_mp': round(observed_h_mp, 2),
            'target_h_mp_midpoint': round(target_midpoint, 2),
            'observed_monster_dpr': round(point.monster_dpr, 2),
            'required_monster_dpr': round(required_dpr_m, 2),
            'observed_avg_monster_dmg': round(observed_avg_dmg, 2),
            'required_avg_monster_dmg': round(required_avg_dmg, 2),
            'recommended_damage_multiplier': round(multiplier, 3),
            'adjustment_needed': True,
        }

    return results


# =============================================================================
# Reporting
# =============================================================================

def format_pressure_table(curve: Dict[int, DepthCurvePoint]) -> str:
    """Format the observed depth curve as a readable ASCII table.

    Returns:
        Multi-line string table
    """
    lines = []
    lines.append("=" * 110)
    lines.append("OBSERVED DEPTH PRESSURE CURVE")
    lines.append("=" * 110)
    lines.append(
        f"{'Depth':>5}  {'Scenario':<35}  {'H_PM':>6}  {'H_MP':>6}  "
        f"{'DPR_P':>6}  {'DPR_M':>6}  {'P(hit_P)':>8}  {'P(hit_M)':>8}  "
        f"{'DMG/Enc':>8}  {'T/Kill':>6}  {'Death%':>6}"
    )
    lines.append("-" * 110)

    for depth in sorted(curve.keys()):
        pt = curve[depth]
        lines.append(
            f"{pt.depth:>5}  {pt.scenario_id:<35}  "
            f"{pt.avg_player_hits_to_kill:>6.2f}  {pt.avg_monster_hits_to_kill:>6.2f}  "
            f"{pt.player_dpr:>6.2f}  {pt.monster_dpr:>6.2f}  "
            f"{pt.player_hit_rate:>7.1%}  {pt.monster_hit_rate:>7.1%}  "
            f"{pt.avg_damage_per_encounter:>8.1f}  {pt.avg_turns_per_enemy:>6.1f}  "
            f"{pt.player_death_rate:>5.1%}"
        )

    lines.append("=" * 110)
    return "\n".join(lines)


def format_target_comparison(evaluation: Dict[int, Dict[str, Any]]) -> str:
    """Format observed vs target comparison table.

    Includes Death%, H_PM, H_MP with target ranges, status indicators,
    design feel labels, and diagnostic recommendations.

    Returns:
        Multi-line string table
    """
    lines = []
    lines.append("=" * 120)
    lines.append("TARGET CURVE COMPARISON")
    lines.append("=" * 120)

    has_death_rate = any(
        ev.get('death_rate_observed') is not None
        for ev in evaluation.values()
    )

    if has_death_rate:
        lines.append(
            f"{'Depth':>5}  {'Feel':<22}  "
            f"{'Death%':>6}  {'Target':>11}  {'':>4}  "
            f"{'H_PM':>6}  {'Target':>9}  {'':>4}  "
            f"{'H_MP':>6}  {'Target':>9}  {'':>4}"
        )
    else:
        lines.append(
            f"{'Depth':>5}  "
            f"{'H_PM Obs':>8}  {'H_PM Target':>14}  {'Status':>6}  "
            f"{'H_MP Obs':>8}  {'H_MP Target':>14}  {'Status':>6}"
        )
    lines.append("-" * 120)

    for depth in sorted(evaluation.keys()):
        ev = evaluation[depth]
        h_pm_t = ev['h_pm_target']
        h_mp_t = ev['h_mp_target']

        if has_death_rate and ev.get('death_rate_observed') is not None:
            dr = ev['death_rate_observed']
            dr_t = ev['death_rate_target']
            feel = ev.get('feel', '')
            lines.append(
                f"{depth:>5}  {feel:<22}  "
                f"{dr:>5.0%}  {dr_t[0]:>4.0%}–{dr_t[1]:<4.0%}  "
                f"{ev['death_rate_status']:>4}  "
                f"{ev['h_pm_observed']:>6.2f}  {h_pm_t[0]:>3.0f}–{h_pm_t[1]:<3.0f}  "
                f"{ev['h_pm_status']:>4}  "
                f"{ev['h_mp_observed']:>6.2f}  {h_mp_t[0]:>3.0f}–{h_mp_t[1]:<3.0f}  "
                f"{ev['h_mp_status']:>4}"
            )
        else:
            lines.append(
                f"{depth:>5}  "
                f"{ev['h_pm_observed']:>8.2f}  {h_pm_t[0]:>5.1f}–{h_pm_t[1]:<5.1f}   "
                f"{ev['h_pm_status']:>6}  "
                f"{ev['h_mp_observed']:>8.2f}  {h_mp_t[0]:>5.1f}–{h_mp_t[1]:<5.1f}   "
                f"{ev['h_mp_status']:>6}"
            )

    lines.append("=" * 120)

    # Diagnosis section
    all_diags = []
    for depth in sorted(evaluation.keys()):
        diags = evaluation[depth].get('diagnosis', [])
        all_diags.extend(diags)

    if all_diags:
        lines.append("")
        lines.append("DIAGNOSIS")
        lines.append("-" * 60)
        for d in all_diags:
            lines.append(d)
        lines.append("")

    return "\n".join(lines)


def format_multiplier_recommendations(
    multipliers: Dict[int, Dict[str, Any]],
) -> str:
    """Format derived damage multiplier recommendations.

    Returns:
        Multi-line string table
    """
    lines = []
    lines.append("=" * 95)
    lines.append("DERIVED DAMAGE MULTIPLIER RECOMMENDATIONS (NOT APPLIED)")
    lines.append("=" * 95)
    lines.append(
        f"{'Depth':>5}  {'Obs H_MP':>8}  {'Tgt H_MP':>8}  "
        f"{'Obs DPR_M':>9}  {'Req DPR_M':>9}  "
        f"{'Obs DMG':>7}  {'Req DMG':>7}  {'Mult':>6}  {'Adj?':>4}"
    )
    lines.append("-" * 95)

    for depth in sorted(multipliers.keys()):
        m = multipliers[depth]
        adj = "YES" if m['adjustment_needed'] else "no"
        lines.append(
            f"{depth:>5}  "
            f"{m['observed_h_mp']:>8.2f}  {m['target_h_mp_midpoint']:>8.2f}  "
            f"{m['observed_monster_dpr']:>9.2f}  {m['required_monster_dpr']:>9.2f}  "
            f"{m['observed_avg_monster_dmg']:>7.2f}  {m['required_avg_monster_dmg']:>7.2f}  "
            f"{m['recommended_damage_multiplier']:>6.3f}  {adj:>4}"
        )

    lines.append("=" * 95)
    return "\n".join(lines)


def format_scaling_diagnosis(curve: Dict[int, DepthCurvePoint]) -> str:
    """Produce a textual diagnosis of the current scaling system.

    Analyzes whether scaling is HP-heavy, DMG-light, or balanced
    based on how H_PM and H_MP trend across depth.

    Returns:
        Multi-line diagnosis string
    """
    lines = []
    lines.append("=" * 70)
    lines.append("SCALING SYSTEM DIAGNOSIS")
    lines.append("=" * 70)

    depths = sorted(curve.keys())
    if len(depths) < 2:
        lines.append("Insufficient depth data for trend analysis (need >= 2 depths)")
        return "\n".join(lines)

    # Compute trends
    first = curve[depths[0]]
    last = curve[depths[-1]]

    h_pm_delta = last.avg_player_hits_to_kill - first.avg_player_hits_to_kill
    h_mp_delta = last.avg_monster_hits_to_kill - first.avg_monster_hits_to_kill
    dpr_p_delta = last.player_dpr - first.player_dpr
    dpr_m_delta = last.monster_dpr - first.monster_dpr

    lines.append(f"Depth range analyzed: {depths[0]} → {depths[-1]}")
    lines.append("")
    lines.append("Trend Analysis (depth {0} → {1}):".format(depths[0], depths[-1]))
    lines.append(f"  H_PM (player hits-to-kill):   {first.avg_player_hits_to_kill:.2f} → "
                 f"{last.avg_player_hits_to_kill:.2f}  (Δ = {h_pm_delta:+.2f})")
    lines.append(f"  H_MP (monster hits-to-kill):  {first.avg_monster_hits_to_kill:.2f} → "
                 f"{last.avg_monster_hits_to_kill:.2f}  (Δ = {h_mp_delta:+.2f})")
    lines.append(f"  DPR_P (player DPR):           {first.player_dpr:.2f} → "
                 f"{last.player_dpr:.2f}  (Δ = {dpr_p_delta:+.2f})")
    lines.append(f"  DPR_M (monster DPR):          {first.monster_dpr:.2f} → "
                 f"{last.monster_dpr:.2f}  (Δ = {dpr_m_delta:+.2f})")
    lines.append("")

    # Diagnosis
    if h_pm_delta > 0.5 and abs(h_mp_delta) < 1.0:
        diagnosis = "HP-HEAVY SCALING"
        explanation = (
            "Monsters take more hits to kill at deeper depths (H_PM rising),\n"
            "  but monster lethality is flat (H_MP stable). This creates ATTRITION:\n"
            "  fights are longer, not deadlier. Player dies from resource exhaustion\n"
            "  rather than tactical failure. Damage scaling needs to increase."
        )
    elif h_pm_delta > 0.5 and h_mp_delta < -1.0:
        diagnosis = "BALANCED SCALING"
        explanation = (
            "Both H_PM (fight duration) and H_MP (survival budget) are moving\n"
            "  in the expected directions. Monsters are getting tougher AND deadlier."
        )
    elif h_pm_delta < 0.3 and h_mp_delta < -1.5:
        diagnosis = "SPIKE LETHALITY"
        explanation = (
            "Monster damage is scaling faster than HP. Fights are about the same\n"
            "  length but significantly deadlier. Risk of unavoidable spike deaths."
        )
    elif abs(h_pm_delta) < 0.3 and abs(h_mp_delta) < 1.0:
        diagnosis = "FLAT SCALING"
        explanation = (
            "Neither fight duration nor lethality is changing meaningfully.\n"
            "  Deeper depths feel similar to shallower ones. Scaling is too timid."
        )
    else:
        diagnosis = "MIXED SIGNALS"
        explanation = (
            "Trends do not clearly fit a single pattern. This may be due to\n"
            "  mixed monster types across depths or insufficient data points."
        )

    lines.append(f"Diagnosis: {diagnosis}")
    lines.append(f"  {explanation}")
    lines.append("")

    # Per-depth lethality context
    lines.append("Attrition vs Lethality Indicator:")
    for d in depths:
        pt = curve[d]
        ratio = pt.avg_player_hits_to_kill / pt.avg_monster_hits_to_kill if pt.avg_monster_hits_to_kill > 0 else 0
        indicator = "ATTRITION" if ratio > 0.6 else ("LETHAL" if ratio < 0.3 else "BALANCED")
        lines.append(
            f"  Depth {d}: H_PM/H_MP = {ratio:.3f}  → {indicator}"
        )

    lines.append("=" * 70)
    return "\n".join(lines)


def print_pressure_report(
    curve: Dict[int, DepthCurvePoint],
) -> str:
    """Generate the full pressure model report.

    Prints to console and returns the full report as a string.
    """
    sections = []

    # Section 1: Observed curve
    sections.append(format_pressure_table(curve))

    # Section 2: Target comparison
    evaluation = evaluate_against_targets(curve)
    sections.append(format_target_comparison(evaluation))

    # Section 3: Damage multiplier recommendations
    multipliers = derive_required_damage_multiplier(curve)
    sections.append(format_multiplier_recommendations(multipliers))

    # Section 4: Scaling diagnosis
    sections.append(format_scaling_diagnosis(curve))

    report = "\n\n".join(sections)
    print(report)
    return report


# =============================================================================
# Convenience: Run from JSON exports
# =============================================================================

def load_metrics_from_json(filepath: str) -> Dict[str, Any]:
    """Load aggregated metrics from a JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


# =============================================================================
# Scenario Configuration for Known Depth Probes
# =============================================================================
# These define the monster HP budgets for each known scenario, used to
# compute avg_monster_hp for the H_PM invariant.
#
# Format: scenario_id -> {depth, monster_hp_budget_per_run, description}
#
# monster_hp_budget_per_run = sum of all monster max HP at base stats
# (depth scaling is already applied in the scenario run, so this is the
# SCALED HP that the player actually fights against)

KNOWN_SCENARIO_CONFIGS: Dict[str, Dict[str, Any]] = {
    "depth1_orc_easy": {
        "depth": 1,
        # 2x orc_grunt at depth 1: HP=28 each, scaling 1.0x → 28*2 = 56
        "monster_hp_budget_per_run": 56.0,
        "description": "2 orc grunts at depth 1 (no scaling)",
    },
    "depth2_orc_baseline": {
        "depth": 2,
        # 3x orc_grunt at depth 2: HP=28 each, scaling 1.0x → 28*3 = 84
        "monster_hp_budget_per_run": 84.0,
        "description": "3 orc grunts at depth 2 (no scaling)",
    },
    "depth3_orc_brutal": {
        "depth": 3,
        # 4x orc_grunt at depth 3: HP=28 each, scaling 1.08x → ceil(28*1.08)=31, 31*4 = 124
        "monster_hp_budget_per_run": 124.0,
        "description": "4 orc grunts at depth 3 (1.08x HP scaling)",
    },
    # Gear probes share identical monster composition with depth3_orc_brutal.
    # Only the player's starting equipment differs (weapon or armor upgrade).
    "depth3_orc_brutal_gear_weapon_plus1": {
        "depth": 3,
        "monster_hp_budget_per_run": 124.0,
        "description": "Gear probe: depth3_orc_brutal + fine_longsword (+1 to-hit)",
    },
    "depth3_orc_brutal_gear_armor_plus1": {
        "depth": 3,
        "monster_hp_budget_per_run": 124.0,
        "description": "Gear probe: depth3_orc_brutal + chain_mail (+1 defense)",
    },
    "midgame_pressure_probe_orcs": {
        "depth": 4,
        # Phase 24 tuning v3: 2x grunt + 1x skirmisher (scaling 1.08x HP):
        # 2x orc_grunt:      ceil(28*1.08) = 31 each = 62
        # 1x orc_skirmisher: ceil(24*1.08) = 26
        # Total: 62 + 26 = 88
        "monster_hp_budget_per_run": 88.0,
        "description": "2 grunts + skirmisher at depth 4 (1.08x HP scaling)",
    },
    "depth4_plague": {
        "depth": 4,
        # 2x plague_zombie + 2x zombie at depth 4: zombie curve = 1.0x (no scaling)
        # plague_zombie HP=30, zombie HP=24 → 30*2 + 24*2 = 108
        # Note: different faction than midgame_pressure_probe_orcs; not directly comparable.
        "monster_hp_budget_per_run": 108.0,
        "description": "2 plague_zombies + 2 zombies at depth 4 (zombie curve: no scaling)",
    },
    "depth5_zombie": {
        "depth": 5,
        # 8x zombie at depth 5: zombie curve has NO scaling at depth 5 → 24*8 = 192
        # (Zombie curve: depth 1-6 = 1.0x all)
        "monster_hp_budget_per_run": 192.0,
        "description": "8 zombies at depth 5 (no zombie-curve scaling)",
    },
    "depth6_orc_siege": {
        "depth": 6,
        # 2x orc_grunt + 1x orc_brute + 1x orc_skirmisher at depth 6 (1.25x HP scaling):
        # orc_grunt:      ceil(28 * 1.25) = 35  x2 = 70
        # orc_brute:      ceil(40 * 1.25) = 50  x1 = 50
        # orc_skirmisher: ceil(24 * 1.25) = 30  x1 = 30
        # Total: 150
        "monster_hp_budget_per_run": 150.0,
        "description": "2 grunts + 1 brute + 1 skirmisher at depth 6 (1.25x HP scaling)",
    },
}


def get_scenario_config(scenario_id: str) -> Optional[Dict[str, Any]]:
    """Get known scenario configuration for pressure model computation."""
    return KNOWN_SCENARIO_CONFIGS.get(scenario_id)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    'PressureMetrics',
    'DepthCurvePoint',
    'compute_pressure_metrics',
    'build_depth_curve',
    'depth_curve_to_dict',
    'evaluate_against_targets',
    'derive_required_damage_multiplier',
    'format_pressure_table',
    'format_target_comparison',
    'format_multiplier_recommendations',
    'format_scaling_diagnosis',
    'print_pressure_report',
    'load_metrics_from_json',
    'get_scenario_config',
    'KNOWN_SCENARIO_CONFIGS',
    'TARGET_PLAYER_HITS_TO_KILL',
    'TARGET_MONSTER_HITS_TO_KILL',
]
