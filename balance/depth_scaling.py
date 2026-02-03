"""Depth-based monster scaling system.

This module implements Option B depth scaling:
- Default curve for most monsters (orcs, etc.)
- Zombie override curve for undead-zombie archetype to avoid amplifying depth 5 spike

Scaling is applied exactly once at monster spawn time. Stats affected:
- HP (max_hp and current_hp)
- To-hit (accuracy modifier)
- Damage (damage_min and damage_max)

Depth bands:
- Depth 1-2: Base stats (1.0x all)
- Depth 3-4: Minor increase
- Depth 5-6: Moderate increase
- Depth 7-8: Significant increase
- Depth 9+: Maximum scaling

Note: Multipliers applied at spawn time; no RPG-style leveling.
"""

import logging
import math
from dataclasses import dataclass
from typing import Dict, Optional, Set

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ScalingMultipliers:
    """Stat multipliers for a given depth band."""
    hp: float
    to_hit: float
    damage: float


# ============================================================================
# Scaling Curves (Option B)
# ============================================================================

# Default curve: applied to most monsters (orcs, etc.)
# Provides gradual stat scaling to maintain challenge at deeper depths.
DEFAULT_CURVE: Dict[int, ScalingMultipliers] = {
    # Depth 1-2: Base stats
    1: ScalingMultipliers(hp=1.00, to_hit=1.00, damage=1.00),
    2: ScalingMultipliers(hp=1.00, to_hit=1.00, damage=1.00),
    # Depth 3-4: Minor increase (HP tuned down to reduce attrition)
    3: ScalingMultipliers(hp=1.08, to_hit=1.06, damage=1.00),
    4: ScalingMultipliers(hp=1.08, to_hit=1.06, damage=1.00),
    # Depth 5-6: Moderate increase
    5: ScalingMultipliers(hp=1.25, to_hit=1.12, damage=1.05),
    6: ScalingMultipliers(hp=1.25, to_hit=1.12, damage=1.05),
    # Depth 7-8: Significant increase
    7: ScalingMultipliers(hp=1.35, to_hit=1.17, damage=1.10),
    8: ScalingMultipliers(hp=1.35, to_hit=1.17, damage=1.10),
}
# Depth 9+ uses max scaling
DEFAULT_MAX_DEPTH = 9
DEFAULT_MAX_MULTIPLIERS = ScalingMultipliers(hp=1.45, to_hit=1.22, damage=1.15)


# Zombie override curve: conservative scaling to avoid amplifying depth 5 zombie spike.
# Applied only to monsters with explicit 'zombie' tag (zombie, plague_zombie).
ZOMBIE_CURVE: Dict[int, ScalingMultipliers] = {
    # Depth 1-6: Base stats (no scaling to avoid amplifying depth 5 swarm)
    1: ScalingMultipliers(hp=1.00, to_hit=1.00, damage=1.00),
    2: ScalingMultipliers(hp=1.00, to_hit=1.00, damage=1.00),
    3: ScalingMultipliers(hp=1.00, to_hit=1.00, damage=1.00),
    4: ScalingMultipliers(hp=1.00, to_hit=1.00, damage=1.00),
    5: ScalingMultipliers(hp=1.00, to_hit=1.00, damage=1.00),
    6: ScalingMultipliers(hp=1.00, to_hit=1.00, damage=1.00),
    # Depth 7-8: Minor increase
    7: ScalingMultipliers(hp=1.10, to_hit=1.05, damage=1.00),
    8: ScalingMultipliers(hp=1.10, to_hit=1.05, damage=1.00),
}
# Depth 9+ uses max zombie scaling
ZOMBIE_MAX_DEPTH = 9
ZOMBIE_MAX_MULTIPLIERS = ScalingMultipliers(hp=1.20, to_hit=1.10, damage=1.05)


# Tags that identify zombie archetype for override curve
# Uses explicit "zombie" tag to differentiate from other low-tier undead (e.g., skeletons)
ZOMBIE_ARCHETYPE_TAGS: Set[str] = {"zombie"}


# ============================================================================
# Scaling Logic
# ============================================================================

def get_scaling_multipliers(depth: int, tags: Optional[Set[str]] = None) -> ScalingMultipliers:
    """Get scaling multipliers for a monster at the given depth.
    
    Args:
        depth: Dungeon depth/floor number (1-indexed)
        tags: Set of monster tags (used to detect zombie archetype)
        
    Returns:
        ScalingMultipliers for the depth and monster type
    """
    if depth < 1:
        depth = 1
    
    # Determine which curve to use
    is_zombie_archetype = tags and bool(tags & ZOMBIE_ARCHETYPE_TAGS)
    
    if is_zombie_archetype:
        curve = ZOMBIE_CURVE
        max_depth = ZOMBIE_MAX_DEPTH
        max_multipliers = ZOMBIE_MAX_MULTIPLIERS
    else:
        curve = DEFAULT_CURVE
        max_depth = DEFAULT_MAX_DEPTH
        max_multipliers = DEFAULT_MAX_MULTIPLIERS
    
    # Get multipliers from curve
    if depth >= max_depth:
        return max_multipliers
    
    return curve.get(depth, ScalingMultipliers(hp=1.0, to_hit=1.0, damage=1.0))


def get_depth_band_name(depth: int) -> str:
    """Get the depth band name for metrics tracking.
    
    Args:
        depth: Dungeon depth/floor number
        
    Returns:
        Band name string (e.g., 'depth_1_2', 'depth_9_plus')
    """
    if depth <= 2:
        return "depth_1_2"
    elif depth <= 4:
        return "depth_3_4"
    elif depth <= 6:
        return "depth_5_6"
    elif depth <= 8:
        return "depth_7_8"
    else:
        return "depth_9_plus"


# ============================================================================
# Rounding Rules
# ============================================================================
# HP: Round up (ceil) - player should never face weaker monsters due to rounding
# Damage: Round to nearest, 0.5 rounds up
# To-hit: Round to nearest, 0.5 rounds up


def scale_hp(base_hp: int, multiplier: float) -> int:
    """Scale HP using ceiling (round up).
    
    Args:
        base_hp: Base HP value from monster definition
        multiplier: HP scaling multiplier
        
    Returns:
        Scaled HP (always >= base_hp when multiplier >= 1.0)
    """
    return math.ceil(base_hp * multiplier)


def scale_stat(base_value: int, multiplier: float) -> int:
    """Scale a stat using round-half-up (0.5 rounds up).
    
    Used for damage and to-hit values.
    
    Args:
        base_value: Base stat value
        multiplier: Scaling multiplier
        
    Returns:
        Scaled stat value
    """
    # math.floor(x + 0.5) is round-half-up for positive numbers
    return math.floor(base_value * multiplier + 0.5)


@dataclass
class ScaledStats:
    """Container for scaled monster stats."""
    hp: int
    damage_min: int
    damage_max: int
    accuracy: int


def apply_scaling(
    base_hp: int,
    base_damage_min: int,
    base_damage_max: int,
    base_accuracy: int,
    depth: int,
    tags: Optional[Set[str]] = None
) -> ScaledStats:
    """Apply depth scaling to base monster stats.
    
    Args:
        base_hp: Base HP from monster definition
        base_damage_min: Base minimum damage
        base_damage_max: Base maximum damage
        base_accuracy: Base accuracy/to-hit modifier
        depth: Dungeon depth for scaling lookup
        tags: Monster tags (for zombie archetype detection)
        
    Returns:
        ScaledStats with adjusted values
    """
    multipliers = get_scaling_multipliers(depth, tags)
    
    scaled_hp = scale_hp(base_hp, multipliers.hp)
    scaled_damage_min = scale_stat(base_damage_min, multipliers.damage)
    scaled_damage_max = scale_stat(base_damage_max, multipliers.damage)
    scaled_accuracy = scale_stat(base_accuracy, multipliers.to_hit)
    
    return ScaledStats(
        hp=scaled_hp,
        damage_min=scaled_damage_min,
        damage_max=scaled_damage_max,
        accuracy=scaled_accuracy
    )


def record_scaling_metrics(depth: int, is_zombie_archetype: bool = False) -> None:
    """Record metrics for monster scaling application.
    
    Args:
        depth: Dungeon depth where monster was spawned
        is_zombie_archetype: Whether zombie override curve was used
    """
    try:
        from services.scenario_metrics import get_active_metrics_collector
        collector = get_active_metrics_collector()
        if collector:
            # Total scaling applications
            collector.increment('monster_scaling_applied_count')
            
            # Track by depth band
            band_name = get_depth_band_name(depth)
            collector.increment(f'monster_scaling_band_{band_name}')
            
            # Track zombie overrides specifically
            if is_zombie_archetype:
                collector.increment('monster_scaling_zombie_override_count')
    except Exception:
        # Metrics are optional; don't break monster creation
        pass
