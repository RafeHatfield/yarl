"""Per-depth target bands for balance metrics.

Single source of truth for what "good" looks like at each depth.
These targets are used by the analysis pipeline to evaluate observed
data, flag out-of-range metrics, and generate diagnostic recommendations.

Target bands are intentionally ranges, not point values. A metric
within the band is acceptable; outside the band triggers investigation.

Design intent per depth:
  Depth 1: Safe learning — player can't realistically die
  Depth 2: Warm-up — mild pressure, still forgiving
  Depth 3: Pressure begins — mistakes start to cost resources
  Depth 4: Serious — tactical play required, deaths expected
  Depth 5: Dangerous — healing matters, retreat is valid
  Depth 6: Brutal but survivable — high stakes, gear-dependent

These values are a starting point. Refine based on harness data.
See ROADMAP.md (Phase 24) for the iterative tuning methodology.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class TargetBand:
    """Target range for a single depth."""

    depth: int
    feel: str  # Human-readable design intent

    # Death rate (fraction, not percentage): 0.05 = 5%
    death_rate_min: float
    death_rate_max: float

    # H_PM: player hits to kill monster (higher = tankier monsters)
    h_pm_min: float
    h_pm_max: float

    # H_MP: monster hits to kill player (lower = more lethal)
    h_mp_min: float
    h_mp_max: float

    @property
    def death_pct_range(self) -> Tuple[float, float]:
        """Death rate as percentage tuple for display."""
        return (self.death_rate_min * 100, self.death_rate_max * 100)

    @property
    def death_rate_midpoint(self) -> float:
        return (self.death_rate_min + self.death_rate_max) / 2.0

    @property
    def h_pm_midpoint(self) -> float:
        return (self.h_pm_min + self.h_pm_max) / 2.0

    @property
    def h_mp_midpoint(self) -> float:
        return (self.h_mp_min + self.h_mp_max) / 2.0


# =============================================================================
# Target Bands by Depth
# =============================================================================
#
# These define the acceptable ranges for key balance metrics at each depth.
#
# Calibration assumptions:
#   - Boons ON (player has accumulated depth boons up to this point)
#   - Default starting gear (dagger + leather armor) unless gear probes
#   - Deterministic scenarios with tactical_fighter bot policy
#
# The bands assume the player has NOT found any gear upgrades beyond starting
# equipment. Gear probes measure the delta; if gear trivializes a depth,
# that's useful data but doesn't invalidate the target band.

TARGET_BANDS: Dict[int, TargetBand] = {
    1: TargetBand(
        depth=1,
        feel="safe learning",
        death_rate_min=0.00, death_rate_max=0.05,
        h_pm_min=6.0,  h_pm_max=8.0,
        h_mp_min=20.0, h_mp_max=24.0,
    ),
    2: TargetBand(
        depth=2,
        feel="warm-up",
        death_rate_min=0.00, death_rate_max=0.08,
        h_pm_min=7.0,  h_pm_max=9.0,
        h_mp_min=20.0, h_mp_max=24.0,
    ),
    3: TargetBand(
        depth=3,
        feel="pressure begins",
        death_rate_min=0.05, death_rate_max=0.15,
        h_pm_min=8.0,  h_pm_max=10.0,
        h_mp_min=20.0, h_mp_max=23.0,
    ),
    4: TargetBand(
        depth=4,
        feel="serious",
        death_rate_min=0.15, death_rate_max=0.30,
        h_pm_min=9.0,  h_pm_max=11.0,
        h_mp_min=18.0, h_mp_max=22.0,
    ),
    5: TargetBand(
        depth=5,
        feel="dangerous",
        death_rate_min=0.25, death_rate_max=0.40,
        h_pm_min=9.0,  h_pm_max=12.0,
        h_mp_min=17.0, h_mp_max=21.0,
    ),
    6: TargetBand(
        depth=6,
        feel="brutal but survivable",
        death_rate_min=0.35, death_rate_max=0.55,
        h_pm_min=10.0, h_pm_max=13.0,
        h_mp_min=16.0, h_mp_max=20.0,
    ),
}


def get_target_band(depth: int) -> Optional[TargetBand]:
    """Get target band for a depth. Returns None if no target defined."""
    return TARGET_BANDS.get(depth)


def evaluate_metric(
    observed: float, lo: float, hi: float
) -> str:
    """Evaluate a single metric against its target range.

    Returns: 'OK', 'LOW', or 'HIGH'
    """
    if observed < lo:
        return "LOW"
    elif observed > hi:
        return "HIGH"
    return "OK"


def evaluate_depth(
    depth: int,
    observed_death_rate: float,
    observed_h_pm: float,
    observed_h_mp: float,
) -> Optional[Dict]:
    """Evaluate observed metrics against target band for a depth.

    Returns None if no target band exists for this depth.
    Returns dict with observed values, targets, status, and gap for each metric.
    """
    band = get_target_band(depth)
    if band is None:
        return None

    def _eval(observed, lo, hi):
        status = evaluate_metric(observed, lo, hi)
        if status == "LOW":
            gap = observed - lo  # Negative = below target
        elif status == "HIGH":
            gap = observed - hi  # Positive = above target
        else:
            gap = 0.0
        return {
            "observed": round(observed, 3),
            "target": (lo, hi),
            "midpoint": round((lo + hi) / 2.0, 3),
            "status": status,
            "gap": round(gap, 3),
        }

    return {
        "depth": depth,
        "feel": band.feel,
        "death_rate": _eval(
            observed_death_rate,
            band.death_rate_min,
            band.death_rate_max,
        ),
        "h_pm": _eval(observed_h_pm, band.h_pm_min, band.h_pm_max),
        "h_mp": _eval(observed_h_mp, band.h_mp_min, band.h_mp_max),
    }


def diagnose(evaluation: Dict) -> list[str]:
    """Generate diagnostic recommendations from an evaluation.

    Returns a list of human-readable diagnosis strings.
    """
    if evaluation is None:
        return []

    findings = []
    depth = evaluation["depth"]
    dr = evaluation["death_rate"]
    hpm = evaluation["h_pm"]
    hmp = evaluation["h_mp"]

    # Death rate diagnosis
    if dr["status"] == "HIGH":
        pct = dr["observed"] * 100
        target_hi = dr["target"][1] * 100
        findings.append(
            f"Depth {depth}: Death rate {pct:.0f}% exceeds target "
            f"ceiling {target_hi:.0f}%."
        )
        # Determine likely cause
        if hmp["status"] == "LOW":
            findings.append(
                f"  -> Monsters too lethal (H_MP {hmp['observed']:.1f}, "
                f"target {hmp['target'][0]:.0f}-{hmp['target'][1]:.0f}). "
                f"Consider reducing monster damage or accuracy at depth {depth}."
            )
        elif hpm["status"] == "HIGH":
            findings.append(
                f"  -> Monsters too tanky (H_PM {hpm['observed']:.1f}, "
                f"target {hpm['target'][0]:.0f}-{hpm['target'][1]:.0f}). "
                f"Consider reducing HP multiplier at depth {depth}."
            )
        elif hpm["status"] == "OK" and hmp["status"] == "OK":
            findings.append(
                "  -> H_PM and H_MP are within target but Death% is high. "
                "Likely a composition or action economy issue — "
                "consider adjusting encounter design (fewer monsters, "
                "different mix, or repositioning)."
            )

    elif dr["status"] == "LOW":
        pct = dr["observed"] * 100
        target_lo = dr["target"][0] * 100
        findings.append(
            f"Depth {depth}: Death rate {pct:.0f}% below target "
            f"floor {target_lo:.0f}%. Encounters may be too easy."
        )

    # Standalone H_PM/H_MP issues (without high death rate)
    if dr["status"] != "HIGH":
        if hpm["status"] == "HIGH":
            findings.append(
                f"Depth {depth}: H_PM {hpm['observed']:.1f} above target "
                f"({hpm['target'][0]:.0f}-{hpm['target'][1]:.0f}). "
                f"Fights may feel grindy."
            )
        if hmp["status"] == "LOW":
            findings.append(
                f"Depth {depth}: H_MP {hmp['observed']:.1f} below target "
                f"({hmp['target'][0]:.0f}-{hmp['target'][1]:.0f}). "
                f"Monsters are more lethal than intended."
            )

    return findings
