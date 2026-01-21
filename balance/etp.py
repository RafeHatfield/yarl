"""Effective Threat Points (ETP) system for encounter budgeting.

This module provides the core ETP calculation and budgeting functionality:
- Load band configuration from YAML
- Calculate monster ETP at a given depth
- Get budget ranges for rooms and floors
- Apply band-based stat multipliers

ETP Formula:
    ETP = (DPS × 6) × Durability × Behavior × Synergy

Where:
    DPS: Average damage per enemy turn
    Durability: Expected player hits to kill / 3 (1.0 ≈ 3 hits to kill)
    Behavior: 0.8-1.2 modifier based on AI role
    Synergy: +0.1 per meaningful combo (starts at 1.0)
"""

import logging
import os
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Any

import yaml

from utils.resource_paths import get_resource_path

logger = logging.getLogger(__name__)


@dataclass
class BandConfig:
    """Configuration for a single difficulty band."""
    
    name: str
    description: str
    floor_min: int
    floor_max: int
    hp_multiplier: float
    damage_multiplier: float
    room_etp_min: int
    room_etp_max: int
    floor_etp_min: int
    floor_etp_max: int
    target_ttk_hits: int
    target_ttd_hits: int
    perk_unlock: bool = False


@dataclass
class ETPConfig:
    """Complete ETP configuration loaded from YAML."""
    
    bands: Dict[str, BandConfig]
    behavior_modifiers: Dict[str, float]
    spike_multiplier: float
    room_tolerance: float
    floor_tolerance: float
    warning_threshold: float
    error_threshold: float
    debug_log_room: bool
    debug_log_floor: bool
    debug_log_violations: bool
    debug_log_monster: bool
    
    @classmethod
    def from_yaml(cls, yaml_data: dict) -> "ETPConfig":
        """Create ETPConfig from parsed YAML data."""
        bands = {}
        for band_id, band_data in yaml_data.get("bands", {}).items():
            bands[band_id] = BandConfig(
                name=band_data.get("name", band_id),
                description=band_data.get("description", ""),
                floor_min=band_data.get("floor_min", 1),
                floor_max=band_data.get("floor_max", 5),
                hp_multiplier=band_data.get("hp_multiplier", 1.0),
                damage_multiplier=band_data.get("damage_multiplier", 1.0),
                room_etp_min=band_data.get("room_etp", {}).get("min", 3),
                room_etp_max=band_data.get("room_etp", {}).get("max", 5),
                floor_etp_min=band_data.get("floor_etp", {}).get("min", 15),
                floor_etp_max=band_data.get("floor_etp", {}).get("max", 30),
                target_ttk_hits=band_data.get("target_ttk_hits", 3),
                target_ttd_hits=band_data.get("target_ttd_hits", 5),
                perk_unlock=band_data.get("perk_unlock", False),
            )
        
        behavior_mods = yaml_data.get("behavior_modifiers", {})
        spike_settings = yaml_data.get("spike_settings", {})
        tolerance = yaml_data.get("tolerance", {})
        debug = yaml_data.get("debug", {})
        
        return cls(
            bands=bands,
            behavior_modifiers=behavior_mods,
            spike_multiplier=spike_settings.get("spike_multiplier", 1.5),
            room_tolerance=tolerance.get("room_tolerance", 0.10),
            floor_tolerance=tolerance.get("floor_tolerance", 0.10),
            warning_threshold=tolerance.get("warning_threshold", 0.15),
            error_threshold=tolerance.get("error_threshold", 0.25),
            debug_log_room=debug.get("log_room_etp", True),
            debug_log_floor=debug.get("log_floor_etp", True),
            debug_log_violations=debug.get("log_budget_violations", True),
            debug_log_monster=debug.get("log_monster_etp", False),
        )


# Global config instance (lazy loaded)
_etp_config: Optional[ETPConfig] = None


def _load_etp_config() -> ETPConfig:
    """Load ETP configuration from YAML file."""
    config_path = get_resource_path("config/etp_config.yaml")
    
    if not os.path.exists(config_path):
        logger.warning(f"ETP config not found at {config_path}, using defaults")
        return _get_default_config()
    
    with open(config_path, "r") as f:
        yaml_data = yaml.safe_load(f)
    
    return ETPConfig.from_yaml(yaml_data)


def _get_default_config() -> ETPConfig:
    """Return default ETP configuration if YAML not found."""
    return ETPConfig(
        bands={
            "B1": BandConfig("Early Game", "", 1, 5, 1.0, 1.0, 3, 5, 15, 30, 3, 5),
            "B2": BandConfig("Early-Mid Game", "", 6, 10, 1.1, 1.05, 6, 8, 30, 48, 4, 4),
            "B3": BandConfig("Mid Game", "", 11, 15, 1.2, 1.1, 9, 12, 45, 72, 5, 4, True),
            "B4": BandConfig("Mid-Late Game", "", 16, 20, 1.35, 1.15, 12, 15, 60, 90, 5, 3),
            "B5": BandConfig("Late Game", "", 21, 25, 1.5, 1.2, 16, 20, 80, 120, 6, 3, True),
        },
        behavior_modifiers={
            "passive": 0.8,
            "basic_melee": 0.9,
            "basic_ranged": 1.0,
            "gap_closer": 1.05,
            "control": 1.1,
            "kiter": 1.1,
            "area_denial": 1.15,
            "summoner": 1.2,
            "boss": 1.3,
        },
        spike_multiplier=1.5,
        room_tolerance=0.10,
        floor_tolerance=0.10,
        warning_threshold=0.15,
        error_threshold=0.25,
        debug_log_room=True,
        debug_log_floor=True,
        debug_log_violations=True,
        debug_log_monster=False,
    )


def get_etp_config() -> ETPConfig:
    """Get the ETP configuration (lazy load)."""
    global _etp_config
    if _etp_config is None:
        _etp_config = _load_etp_config()
    return _etp_config


def reload_etp_config() -> None:
    """Force reload of ETP configuration from disk."""
    global _etp_config
    _etp_config = _load_etp_config()
    logger.info("ETP configuration reloaded")


# Public API alias
ETP_CONFIG = get_etp_config


def get_band_for_depth(depth: int) -> str:
    """Get the band ID (B1-B5) for a given dungeon depth.
    
    Args:
        depth: Dungeon level (1-25)
        
    Returns:
        Band ID string ("B1", "B2", "B3", "B4", or "B5")
    """
    config = get_etp_config()
    
    for band_id, band_config in config.bands.items():
        if band_config.floor_min <= depth <= band_config.floor_max:
            return band_id
    
    # Default to highest band for depths beyond 25
    if depth > 25:
        return "B5"
    # Default to lowest band for invalid depths
    return "B1"


def get_band_config(depth: int) -> BandConfig:
    """Get the band configuration for a given dungeon depth.
    
    Args:
        depth: Dungeon level (1-25)
        
    Returns:
        BandConfig for the appropriate band
    """
    config = get_etp_config()
    band_id = get_band_for_depth(depth)
    return config.bands[band_id]


def get_behavior_modifier(ai_type: str) -> float:
    """Get the behavior modifier for an AI type.
    
    Args:
        ai_type: AI behavior type string
        
    Returns:
        Behavior modifier (0.8-1.3)
    """
    config = get_etp_config()
    
    # Map common AI types to behavior categories
    ai_mapping = {
        "basic": "basic_melee",
        "basic_monster": "basic_melee",
        "slime": "control",
        "boss": "boss",
        "stationary": "passive",
    }
    
    mapped_type = ai_mapping.get(ai_type, ai_type)
    return config.behavior_modifiers.get(mapped_type, 1.0)


def calculate_monster_dps(damage_min: int, damage_max: int, power: int = 0) -> float:
    """Calculate average DPS for a monster.
    
    Args:
        damage_min: Minimum natural damage
        damage_max: Maximum natural damage
        power: Power bonus added to damage
        
    Returns:
        Average damage per attack
    """
    avg_damage = (damage_min + damage_max) / 2.0
    return avg_damage + power


def calculate_durability(hp: int, target_ttk_hits: int = 3) -> float:
    """Calculate durability factor for ETP.
    
    Durability is (expected hits to kill) / 3, where 1.0 ≈ 3 hits to kill.
    This uses a baseline of ~20 damage per player hit to estimate hits-to-kill.
    
    Args:
        hp: Monster HP
        target_ttk_hits: Baseline hits to kill (default 3 for B1)
        
    Returns:
        Durability factor (1.0 ≈ 3 hits to kill)
    """
    # Baseline player damage per hit: ~6-7 damage in B1 
    # (1d8 weapon + 2 STR = 4.5+2 = 6.5 avg)
    baseline_player_damage = 6.5
    
    hits_to_kill = hp / baseline_player_damage
    
    # Normalize so 3 hits = durability 1.0
    return hits_to_kill / 3.0


# Elite multiplier applied to monsters with "(Elite)" suffix in vault rooms
ELITE_ETP_MULTIPLIER = 1.5

# Speed-based ETP multiplier tiers (Phase 6)
# Fast monsters are more dangerous due to bonus attack potential
SPEED_ETP_TIERS = [
    (2.0, 2.0),    # Speed >= 2.0: 2.0x multiplier
    (1.5, 1.5),    # Speed 1.5-1.9: 1.5x multiplier
    (1.1, 1.25),   # Speed 1.1-1.4: 1.25x multiplier
    (0.0, 1.0),    # Speed <= 1.0: 1.0x multiplier (no bonus)
]


def get_speed_etp_multiplier(speed_ratio: float) -> float:
    """Get ETP multiplier based on monster speed ratio.
    
    Phase 6: Fast monsters are more dangerous due to bonus attack mechanics.
    This applies a tiered multiplier to their ETP based on speed_bonus.
    
    Speed Ratio | ETP Multiplier
    ------------|---------------
    >= 2.0      | 2.0x
    1.5-1.9     | 1.5x
    1.1-1.4     | 1.25x
    <= 1.0      | 1.0x (no change)
    
    Args:
        speed_ratio: Monster's speed_bonus ratio (0.0 = slow, 2.0 = very fast)
        
    Returns:
        ETP multiplier (1.0-2.0)
    """
    for threshold, multiplier in SPEED_ETP_TIERS:
        if speed_ratio >= threshold:
            return multiplier
    return 1.0  # Default fallback

# Lists of boss and miniboss monster types (used for spawn control and ETP exemption)
BOSS_MONSTER_TYPES = frozenset([
    "zhyraxion_human",
    "zhyraxion_full_dragon", 
    "zhyraxion_grief_dragon",
])

MINIBOSS_MONSTER_TYPES = frozenset([
    "dragon_lord",
    "demon_king",
    "corrupted_ritualist",
])


def is_boss_monster(monster_type: str) -> bool:
    """Check if a monster type is a boss (final encounter tier).
    
    Args:
        monster_type: Monster type identifier
        
    Returns:
        True if this is a boss monster
    """
    base_type = _get_base_monster_type(monster_type)
    return base_type in BOSS_MONSTER_TYPES


def is_miniboss_monster(monster_type: str) -> bool:
    """Check if a monster type is a miniboss.
    
    Args:
        monster_type: Monster type identifier
        
    Returns:
        True if this is a miniboss monster
    """
    base_type = _get_base_monster_type(monster_type)
    return base_type in MINIBOSS_MONSTER_TYPES


def can_spawn_monster_in_room(monster_type: str, room_role: str) -> bool:
    """Check if a monster type can spawn in a room based on its role.
    
    Spawn rules:
    - Zhyraxion variants: Only in end_boss rooms
    - Minibosses (dragon_lord, demon_king): Only in miniboss, boss, or end_boss rooms
    - Normal monsters: Any room
    
    Args:
        monster_type: Monster type identifier
        room_role: Room role (normal, miniboss, boss, end_boss, treasure, optional)
        
    Returns:
        True if the monster can spawn in this room
    """
    base_type = _get_base_monster_type(monster_type)
    
    # Zhyraxion variants: end_boss only
    if base_type in BOSS_MONSTER_TYPES:
        return room_role == "end_boss"
    
    # Minibosses: miniboss, boss, or end_boss rooms
    if base_type in MINIBOSS_MONSTER_TYPES:
        return room_role in ("miniboss", "boss", "end_boss")
    
    # Normal monsters can spawn anywhere
    return True


def get_spawn_restriction_reason(monster_type: str, room_role: str) -> Optional[str]:
    """Get the reason why a monster can't spawn in a room, if any.
    
    Args:
        monster_type: Monster type identifier
        room_role: Room role
        
    Returns:
        Reason string if spawn is blocked, None if allowed
    """
    base_type = _get_base_monster_type(monster_type)
    
    if base_type in BOSS_MONSTER_TYPES:
        if room_role != "end_boss":
            return f"Boss '{base_type}' requires end_boss room (got: {room_role})"
        return None
    
    if base_type in MINIBOSS_MONSTER_TYPES:
        if room_role not in ("miniboss", "boss", "end_boss"):
            return f"Miniboss '{base_type}' requires miniboss/boss/end_boss room (got: {room_role})"
        return None
    
    return None


def _get_base_monster_type(monster_type: str) -> str:
    """Extract base monster type from display name.
    
    Handles cases like "Orc (Elite)" -> "orc", "Troll (Elite)" -> "troll"
    
    Args:
        monster_type: Monster type or display name
        
    Returns:
        Base monster type identifier
    """
    # Handle "(Elite)" suffix from vault monsters
    if " (Elite)" in monster_type or " (elite)" in monster_type:
        base_name = monster_type.replace(" (Elite)", "").replace(" (elite)", "")
        # Convert display name to type identifier (e.g., "Orc" -> "orc")
        return base_name.lower().replace(" ", "_")
    
    # Already a type identifier
    return monster_type.lower().replace(" ", "_")


def _is_elite_variant(monster_type: str) -> bool:
    """Check if a monster is an elite variant.
    
    Args:
        monster_type: Monster type or display name
        
    Returns:
        True if this is an elite variant
    """
    return "(elite)" in monster_type.lower()


def get_monster_etp(
    monster_type: str,
    depth: int,
    monster_data: Optional[Dict[str, Any]] = None,
    synergy_bonus: float = 0.0,
) -> float:
    """Calculate the Effective Threat Points for a monster at a given depth.
    
    ETP = (DPS × 6) × Durability × Behavior × Synergy
    
    This applies band multipliers to the monster's base stats before calculation.
    Elite variants (with "(Elite)" suffix) get an additional multiplier.
    
    Args:
        monster_type: Type identifier for the monster (e.g., "orc", "troll", "Orc (Elite)")
        depth: Current dungeon depth (1-25)
        monster_data: Optional monster stats dict. If None, loads from entities.yaml
        synergy_bonus: Additional synergy from group composition (0.0-0.3 typical)
        
    Returns:
        Effective Threat Points value
    """
    # Check if this is an elite variant and extract base type
    is_elite = _is_elite_variant(monster_type)
    base_type = _get_base_monster_type(monster_type)
    
    # Get band configuration for this depth
    band_config = get_band_config(depth)
    
    # Load monster data if not provided - use base type for lookup
    if monster_data is None:
        monster_data = _load_monster_data(base_type)
    
    if monster_data is None:
        # Try original monster_type as fallback
        monster_data = _load_monster_data(monster_type)
    
    if monster_data is None:
        logger.debug(f"No data found for monster type '{monster_type}' (base: {base_type}), using default ETP")
        # Return a reasonable default based on whether it's elite
        return 20.0 * ELITE_ETP_MULTIPLIER if is_elite else 20.0
    
    # Check for explicit etp_base value
    etp_base = monster_data.get("etp_base")
    if etp_base is not None:
        # Apply band multipliers to base ETP
        # Band multipliers affect the underlying stats, which affects ETP
        # For simplicity, scale by geometric mean of HP and damage multipliers
        band_multiplier = (
            (band_config.hp_multiplier + band_config.damage_multiplier) / 2.0
        )
        synergy = 1.0 + synergy_bonus
        
        # Apply elite multiplier if this is an elite variant
        elite_mult = ELITE_ETP_MULTIPLIER if is_elite else 1.0
        
        # Phase 6: Apply speed-based ETP multiplier
        speed_ratio = monster_data.get("speed_bonus", 0.0)
        speed_mult = get_speed_etp_multiplier(speed_ratio)
        
        final_etp = etp_base * band_multiplier * synergy * elite_mult * speed_mult
        
        config = get_etp_config()
        if config.debug_log_monster:
            logger.debug(
                f"ETP for {monster_type} at depth {depth}: "
                f"base={etp_base:.1f}, band_mult={band_multiplier:.2f}, "
                f"elite_mult={elite_mult:.2f}, speed_mult={speed_mult:.2f}, "
                f"synergy={synergy:.2f}, final={final_etp:.1f}"
            )
        
        return final_etp
    
    # Calculate ETP from stats
    stats = monster_data.get("stats", {})
    hp = stats.get("hp", 10)
    damage_min = stats.get("damage_min", 1)
    damage_max = stats.get("damage_max", 3)
    power = stats.get("power", 0)
    ai_type = monster_data.get("ai_type", "basic")
    
    # Apply band multipliers to stats
    scaled_hp = hp * band_config.hp_multiplier
    scaled_damage_min = damage_min * band_config.damage_multiplier
    scaled_damage_max = damage_max * band_config.damage_multiplier
    scaled_power = power * band_config.damage_multiplier
    
    # Calculate components
    dps = calculate_monster_dps(scaled_damage_min, scaled_damage_max, scaled_power)
    durability = calculate_durability(scaled_hp)
    behavior = get_behavior_modifier(ai_type)
    synergy = 1.0 + synergy_bonus
    
    # ETP = (DPS × 6) × Durability × Behavior × Synergy
    etp = (dps * 6) * durability * behavior * synergy
    
    # Apply elite multiplier if this is an elite variant
    if is_elite:
        etp *= ELITE_ETP_MULTIPLIER
    
    # Phase 6: Apply speed-based ETP multiplier
    speed_ratio = monster_data.get("speed_bonus", 0.0)
    speed_mult = get_speed_etp_multiplier(speed_ratio)
    etp *= speed_mult
    
    config = get_etp_config()
    if config.debug_log_monster:
        logger.debug(
            f"ETP for {monster_type} at depth {depth}: "
            f"DPS={dps:.1f}, durability={durability:.2f}, "
            f"behavior={behavior:.2f}, synergy={synergy:.2f}, "
            f"elite={'yes' if is_elite else 'no'}, speed_mult={speed_mult:.2f}, ETP={etp:.1f}"
        )
    
    return etp


def _load_monster_data(monster_type: str) -> Optional[Dict[str, Any]]:
    """Load monster data from entities.yaml.
    
    Args:
        monster_type: Monster type identifier
        
    Returns:
        Monster data dict or None if not found
    """
    config_path = get_resource_path("config/entities.yaml")
    
    if not os.path.exists(config_path):
        logger.warning(f"Entities config not found at {config_path}")
        return None
    
    try:
        with open(config_path, "r") as f:
            entities = yaml.safe_load(f)
        
        monsters = entities.get("monsters", {})
        return monsters.get(monster_type)
    except Exception as e:
        logger.error(f"Error loading monster data: {e}")
        return None


def get_room_etp_budget(depth: int, allow_spike: bool = False) -> Tuple[float, float]:
    """Get the ETP budget range for a room at a given depth.
    
    Args:
        depth: Dungeon depth (1-25)
        allow_spike: If True, allow spike rooms with higher budget
        
    Returns:
        Tuple of (min_etp, max_etp)
    """
    band_config = get_band_config(depth)
    config = get_etp_config()
    
    min_etp = band_config.room_etp_min
    max_etp = band_config.room_etp_max
    
    if allow_spike:
        max_etp = max_etp * config.spike_multiplier
    
    return (min_etp, max_etp)


def get_floor_etp_budget(depth: int) -> Tuple[float, float]:
    """Get the ETP budget range for an entire floor at a given depth.
    
    Args:
        depth: Dungeon depth (1-25)
        
    Returns:
        Tuple of (min_etp, max_etp)
    """
    band_config = get_band_config(depth)
    return (band_config.floor_etp_min, band_config.floor_etp_max)


def check_room_budget(
    total_etp: float,
    depth: int,
    room_id: str = "unknown",
    allow_spike: bool = False,
) -> Tuple[bool, str]:
    """Check if a room's total ETP is within budget.
    
    Args:
        total_etp: Sum of ETP for all monsters in room
        depth: Dungeon depth
        room_id: Identifier for logging
        allow_spike: Whether this room allows spiking
        
    Returns:
        Tuple of (is_valid, status_message)
    """
    config = get_etp_config()
    min_etp, max_etp = get_room_etp_budget(depth, allow_spike)
    band_id = get_band_for_depth(depth)
    
    # Calculate tolerance bounds
    tolerance = config.room_tolerance
    lower_bound = min_etp * (1 - tolerance)
    upper_bound = max_etp * (1 + tolerance)
    
    if total_etp < lower_bound:
        status = "under"
        deviation = (min_etp - total_etp) / min_etp if min_etp > 0 else 0
        message = (
            f"Room {room_id} under budget: {total_etp:.1f} ETP "
            f"(target: {min_etp}-{max_etp}, band: {band_id}, dev: {deviation:.1%})"
        )
        is_valid = deviation <= config.warning_threshold
    elif total_etp > upper_bound:
        status = "over"
        deviation = (total_etp - max_etp) / max_etp if max_etp > 0 else 0
        message = (
            f"Room {room_id} over budget: {total_etp:.1f} ETP "
            f"(target: {min_etp}-{max_etp}, band: {band_id}, dev: {deviation:.1%})"
        )
        is_valid = deviation <= config.warning_threshold
    else:
        status = "ok"
        message = (
            f"Room {room_id} within budget: {total_etp:.1f} ETP "
            f"(target: {min_etp}-{max_etp}, band: {band_id})"
        )
        is_valid = True
    
    # Log based on status and config
    if status != "ok" and config.debug_log_violations:
        logger.warning(message)
    elif config.debug_log_room:
        logger.debug(message)
    
    return (is_valid, message)


def get_stat_multipliers(depth: int) -> Tuple[float, float]:
    """Get HP and damage multipliers for a given depth.
    
    Args:
        depth: Dungeon depth (1-25)
        
    Returns:
        Tuple of (hp_multiplier, damage_multiplier)
    """
    band_config = get_band_config(depth)
    return (band_config.hp_multiplier, band_config.damage_multiplier)


def initialize_encounter_budget_engine() -> None:
    """Initialize the EncounterBudgetEngine with ETP values from entities.yaml.
    
    This function loads all monster definitions and registers their etp_base
    values with the global EncounterBudgetEngine singleton.
    """
    from services.encounter_budget_engine import get_encounter_budget_engine
    
    engine = get_encounter_budget_engine()
    config_path = get_resource_path("config/entities.yaml")
    
    if not os.path.exists(config_path):
        logger.warning(f"Entities config not found at {config_path}, skipping ETP init")
        return
    
    try:
        with open(config_path, "r") as f:
            entities = yaml.safe_load(f)
        
        monsters = entities.get("monsters", {})
        registered_count = 0
        
        for monster_type, monster_data in monsters.items():
            # Get etp_base if defined, otherwise calculate from stats
            etp_base = monster_data.get("etp_base")
            
            if etp_base is not None:
                engine.register_etp(monster_type, int(etp_base))
                registered_count += 1
            else:
                # Calculate ETP from stats (B1 baseline)
                stats = monster_data.get("stats", {})
                hp = stats.get("hp", 10)
                damage_min = stats.get("damage_min", 1)
                damage_max = stats.get("damage_max", 3)
                power = stats.get("power", 0)
                ai_type = monster_data.get("ai_type", "basic")
                
                dps = calculate_monster_dps(damage_min, damage_max, power)
                durability = calculate_durability(hp)
                behavior = get_behavior_modifier(ai_type)
                
                calculated_etp = int((dps * 6) * durability * behavior)
                engine.register_etp(monster_type, calculated_etp)
                registered_count += 1
                
                logger.debug(
                    f"Calculated ETP for {monster_type}: {calculated_etp} "
                    f"(DPS={dps:.1f}, dur={durability:.2f}, beh={behavior:.2f})"
                )
        
        logger.info(f"Initialized EncounterBudgetEngine with {registered_count} monster ETPs")
        
    except Exception as e:
        logger.error(f"Error initializing ETP values: {e}")


def get_room_monsters_etp(monsters: list, depth: int) -> Tuple[float, list]:
    """Calculate total ETP for a list of monsters in a room.
    
    Args:
        monsters: List of monster entities or (type, count) tuples
        depth: Dungeon depth for band multipliers
        
    Returns:
        Tuple of (total_etp, list of (monster_type, etp) entries)
    """
    total_etp = 0.0
    etp_breakdown = []
    
    for monster in monsters:
        if hasattr(monster, 'name'):
            # It's an Entity object
            monster_type = getattr(monster, 'monster_type', monster.name.lower())
            etp = get_monster_etp(monster_type, depth)
            etp_breakdown.append((monster_type, etp))
            total_etp += etp
        elif isinstance(monster, tuple) and len(monster) == 2:
            # It's a (type, count) tuple
            monster_type, count = monster
            etp = get_monster_etp(monster_type, depth) * count
            etp_breakdown.append((monster_type, etp))
            total_etp += etp
    
    return total_etp, etp_breakdown


def log_room_etp_summary(
    room_id: str,
    depth: int,
    monster_list: list,
    total_etp: float,
    budget_min: float,
    budget_max: float
) -> None:
    """Log ETP summary for a room.
    
    Args:
        room_id: Room identifier for logging
        depth: Dungeon depth
        monster_list: List of (monster_type, etp) tuples
        total_etp: Total ETP for room
        budget_min: Budget minimum
        budget_max: Budget maximum
    """
    config = get_etp_config()
    band_id = get_band_for_depth(depth)
    
    if not config.debug_log_room:
        return
    
    status = "OK"
    if total_etp < budget_min:
        status = "UNDER"
    elif total_etp > budget_max:
        status = "OVER"
    
    monster_summary = ", ".join(f"{t}:{e:.0f}" for t, e in monster_list) if monster_list else "empty"
    
    logger.debug(
        f"Room ETP [{status}]: {room_id} @ depth {depth} (band {band_id}) | "
        f"Total: {total_etp:.1f} (budget: {budget_min:.0f}-{budget_max:.0f}) | "
        f"Monsters: [{monster_summary}]"
    )


def log_floor_etp_summary(
    depth: int,
    room_etp_totals: list,
    floor_total_etp: float,
) -> None:
    """Log ETP summary for an entire floor.
    
    Args:
        depth: Dungeon depth
        room_etp_totals: List of room ETP totals
        floor_total_etp: Total ETP for floor
    """
    config = get_etp_config()
    
    if not config.debug_log_floor:
        return
    
    band_id = get_band_for_depth(depth)
    floor_min, floor_max = get_floor_etp_budget(depth)
    
    status = "OK"
    if floor_total_etp < floor_min:
        status = "UNDER"
    elif floor_total_etp > floor_max:
        status = "OVER"
    
    logger.info(
        f"Floor ETP [{status}]: Depth {depth} (band {band_id}) | "
        f"Total: {floor_total_etp:.1f} (budget: {floor_min:.0f}-{floor_max:.0f}) | "
        f"Rooms: {len(room_etp_totals)}"
    )

