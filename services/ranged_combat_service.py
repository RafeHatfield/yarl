"""Ranged combat service - Phase 22.2 Ranged Combat Doctrine.

SINGLE SOURCE OF TRUTH for ranged attack mechanics:
- Range band calculation (distance → band → multiplier/deny)
- Damage modifier application
- Retaliation triggering (adjacent only)
- Ranged knockback (10% chance, 1-tile)

Fighter.attack_d20() is the orchestrator and calls into this service.

═══════════════════════════════════════════════════════════════════════════════
DOCTRINE RULES (do not change without discussion)
═══════════════════════════════════════════════════════════════════════════════

1. RETALIATION ORDERING: Adjacent ranged attacks are reckless; retaliation
   resolves BEFORE the ranged shot. This is intentional punishment for
   shooting at melee range. The sequence is:
   - Player declares ranged attack at d==1
   - Target retaliates with free melee strike (player armor halved)
   - If player survives, ranged shot proceeds at 25% damage
   
2. RANGE DENIAL: Attacks beyond max range (OPTIMAL_MAX + 2 = 8) are hard
   denied - no hit roll, no damage roll, no effects. This is not "miss";
   it's "cannot fire."

3. KNOCKBACK: 10% proc chance on successful ranged hit, exactly 1 tile,
   routes through canonical knockback service (respects Entity.move).

═══════════════════════════════════════════════════════════════════════════════

Range Bands (OPTIMAL_MAX = 6, max range = 8):
- d==1: 25% damage AND threatened retaliation (free melee strike w/ halved armor)
- d==2: 50% damage
- 3<=d<=OPTIMAL_MAX (6): 100% damage
- OPTIMAL_MAX<d<=OPTIMAL_MAX+1 (7): 50% damage
- d==OPTIMAL_MAX+2 (8): 25% damage
- d>OPTIMAL_MAX+2 (>8): DENIED (no damage roll, attack fails)

Metrics (tracked on SUCCESSFUL HITS only unless noted):
- ranged_attacks_made_by_player: incremented on every ranged attack attempt
- ranged_attacks_denied_out_of_range: incremented when attack is denied
- ranged_damage_dealt_by_player: actual damage dealt after modifiers
- ranged_damage_penalty_total: (pre_modifier_damage - post_modifier_damage) on hits
- ranged_adjacent_retaliations_triggered: count of retaliation strikes
- ranged_knockback_procs: count of successful knockbacks
"""

from contextlib import contextmanager
from typing import Dict, Any, List, Optional, TYPE_CHECKING, Tuple
import random

from logger_config import get_logger

if TYPE_CHECKING:
    from entity import Entity
    from map_objects.game_map import GameMap

logger = get_logger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS - Range Band Table (single source of truth)
# ═══════════════════════════════════════════════════════════════════════════════

OPTIMAL_MAX = 6  # Maximum distance for full damage
RANGED_WEAPON_THRESHOLD = 3  # Weapons with reach >= this are "ranged" (bows, not spears)
RANGED_KNOCKBACK_CHANCE = 0.10  # 10% chance for 1-tile knockback on hit


def _get_metrics_collector():
    """Get active scenario metrics collector if available."""
    try:
        from services.scenario_metrics import get_active_metrics_collector
        return get_active_metrics_collector()
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# WEAPON DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

def get_weapon_reach(entity: 'Entity') -> int:
    """Get the reach of the entity's equipped weapon.
    
    Args:
        entity: The entity to check
        
    Returns:
        int: The reach of the weapon in tiles (default 1)
    """
    from components.component_registry import ComponentType
    equipment = entity.get_component_optional(ComponentType.EQUIPMENT)
    if (equipment and equipment.main_hand and 
        equipment.main_hand.components.has(ComponentType.EQUIPPABLE)):
        weapon = equipment.main_hand.equippable
        reach = getattr(weapon, 'reach', 1)
        # Handle Mock objects in tests - ensure reach is an int
        if not isinstance(reach, int):
            return 1
        return reach
    return 1


def is_ranged_weapon(entity: 'Entity') -> bool:
    """Check if entity is wielding a ranged weapon (bow/crossbow).
    
    Phase 22.2.2: Uses explicit is_ranged_weapon tag instead of reach heuristic.
    
    Args:
        entity: The entity to check
        
    Returns:
        bool: True if wielding ranged weapon (explicitly tagged in weapon definition)
    """
    from components.component_registry import ComponentType
    equipment = entity.get_component_optional(ComponentType.EQUIPMENT)
    if (equipment and equipment.main_hand and 
        equipment.main_hand.components.has(ComponentType.EQUIPPABLE)):
        weapon = equipment.main_hand.equippable
        # Phase 22.2.2: Check explicit flag, not reach heuristic
        is_ranged = getattr(weapon, 'is_ranged_weapon', False)
        # Handle Mock objects in tests
        if not isinstance(is_ranged, bool):
            return False
        return is_ranged
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# RANGE BAND CALCULATION (single source of truth for band table)
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_range_band(distance: int) -> Dict[str, Any]:
    """Calculate range band effects for a given distance.
    
    THIS IS THE SINGLE SOURCE OF TRUTH for the range band table.
    All range-based decisions should query this function.
    
    Args:
        distance: Chebyshev distance to target (tiles)
        
    Returns:
        dict with keys:
            - damage_multiplier: float (0.0 = denied, 0.25, 0.5, 1.0)
            - retaliation_triggered: bool (True only at d==1)
            - denied: bool (True if attack cannot proceed)
            - band_name: str for logging/debugging
    """
    if distance > OPTIMAL_MAX + 2:
        # Beyond max range - attack denied
        return {
            "damage_multiplier": 0.0,
            "retaliation_triggered": False,
            "denied": True,
            "band_name": "denied_out_of_range"
        }
    elif distance == OPTIMAL_MAX + 2:
        # Long range - severe penalty
        return {
            "damage_multiplier": 0.25,
            "retaliation_triggered": False,
            "denied": False,
            "band_name": "extreme_range"
        }
    elif distance == OPTIMAL_MAX + 1:
        # Far range - moderate penalty
        return {
            "damage_multiplier": 0.50,
            "retaliation_triggered": False,
            "denied": False,
            "band_name": "far_range"
        }
    elif distance >= 3:
        # Optimal range - full damage
        return {
            "damage_multiplier": 1.0,
            "retaliation_triggered": False,
            "denied": False,
            "band_name": "optimal_range"
        }
    elif distance == 2:
        # Close range - moderate penalty
        return {
            "damage_multiplier": 0.50,
            "retaliation_triggered": False,
            "denied": False,
            "band_name": "close_range"
        }
    else:  # distance == 1 or <= 0
        # Adjacent - severe penalty + retaliation
        return {
            "damage_multiplier": 0.25,
            "retaliation_triggered": True,
            "denied": False,
            "band_name": "adjacent_threatened"
        }


def check_ranged_attack_validity(attacker: 'Entity', target: 'Entity') -> Dict[str, Any]:
    """Pre-check if a ranged attack can proceed.
    
    Called by Fighter.attack_d20() before hit roll to determine if attack
    should be denied due to range.
    
    Args:
        attacker: Entity attempting ranged attack
        target: Target entity
        
    Returns:
        dict with keys:
            - valid: bool (True if attack can proceed)
            - reason: str (explanation if invalid)
            - distance: int (calculated distance)
            - band: dict (range band info from calculate_range_band)
    """
    if not is_ranged_weapon(attacker):
        return {
            "valid": False,
            "reason": "Not wielding a ranged weapon",
            "distance": 0,
            "band": None
        }
    
    distance = max(abs(attacker.x - target.x), abs(attacker.y - target.y))
    band = calculate_range_band(distance)
    
    if band["denied"]:
        # Track denial metric
        collector = _get_metrics_collector()
        if collector:
            collector.increment('ranged_attacks_denied_out_of_range')
        
        return {
            "valid": False,
            "reason": f"Target out of range (distance: {distance}, max: {OPTIMAL_MAX + 2})",
            "distance": distance,
            "band": band
        }
    
    return {
        "valid": True,
        "reason": None,
        "distance": distance,
        "band": band
    }


# ═══════════════════════════════════════════════════════════════════════════════
# DAMAGE MODIFIER APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════

def apply_damage_modifier(damage: int, band_info: Dict[str, Any]) -> Tuple[int, int]:
    """Apply range band damage modifier.
    
    Called by Fighter.attack_d20() after base damage calculation.
    
    Args:
        damage: Base damage before range penalty
        band_info: Range band info from calculate_range_band()
        
    Returns:
        Tuple of (modified_damage, penalty_amount)
        - modified_damage: damage after applying multiplier (minimum 1)
        - penalty_amount: damage lost to range penalty (for metrics)
    """
    if not band_info:
        return damage, 0
    
    multiplier = band_info.get("damage_multiplier", 1.0)
    
    if multiplier >= 1.0:
        return damage, 0
    
    modified_damage = int(damage * multiplier)
    modified_damage = max(1, modified_damage)  # Minimum 1 damage
    penalty = damage - modified_damage
    
    return modified_damage, penalty


def record_ranged_damage_metrics(damage_dealt: int, damage_penalty: int) -> None:
    """Record ranged combat damage metrics.
    
    Called by Fighter.attack_d20() after damage is applied.
    
    Args:
        damage_dealt: Actual damage dealt after modifiers
        damage_penalty: Damage lost to range penalty (pre - post, on this hit)
    """
    collector = _get_metrics_collector()
    if collector:
        collector.increment('ranged_attacks_made_by_player')
        if damage_dealt > 0:
            collector.increment('ranged_damage_dealt_by_player', damage_dealt)
        if damage_penalty > 0:
            collector.increment('ranged_damage_penalty_total', damage_penalty)


# ═══════════════════════════════════════════════════════════════════════════════
# RETALIATION (Close-Range Punishment)
# ═══════════════════════════════════════════════════════════════════════════════

@contextmanager
def retaliation_armor_penalty(entity: 'Entity'):
    """Context manager to temporarily halve armor for retaliation strike.
    
    Sets a flag on the Fighter component that the armor_class property
    should check. Ensures cleanup even if an exception occurs.
    
    Usage:
        with retaliation_armor_penalty(player):
            monster.fighter.attack_d20(player)
    """
    from components.component_registry import ComponentType
    
    fighter = entity.get_component_optional(ComponentType.FIGHTER)
    if not fighter:
        yield
        return
    
    # Set the penalty flag
    fighter._retaliation_armor_halved = True
    try:
        yield
    finally:
        # Always clean up, even if exception
        if hasattr(fighter, '_retaliation_armor_halved'):
            del fighter._retaliation_armor_halved


def can_retaliate(defender: 'Entity') -> bool:
    """Check if defender is able to make a retaliation strike.
    
    Retaliation is blocked if defender is incapacitated:
    - Asleep
    - Stunned/staggered
    - Paralyzed
    - Dead/dying
    
    Args:
        defender: Entity that would retaliate
        
    Returns:
        bool: True if defender can retaliate
    """
    from components.component_registry import ComponentType
    
    # Must have a fighter component
    fighter = defender.get_component_optional(ComponentType.FIGHTER)
    if not fighter:
        return False
    
    # Must be alive
    if fighter.hp <= 0:
        return False
    
    # Check for incapacitating status effects
    # TODO (Phase 22.3+): Replace name-list with canonical flag check.
    # Add `prevents_actions` or `incapacitated` flag to StatusEffect base,
    # then check `status_effects.has_any_effect_with_flag('incapacitated')`.
    # This matches doctrine: "action denial modeled as effects."
    status_effects = defender.get_component_optional(ComponentType.STATUS_EFFECTS)
    if status_effects:
        # Check for effects that prevent action (name-list for now, flag later)
        incapacitating_effects = ['asleep', 'sleep', 'stunned', 'staggered', 'paralysis', 'paralyzed']
        for effect_name in incapacitating_effects:
            if status_effects.has_effect(effect_name):
                logger.info(f"[RETALIATION BLOCKED] {defender.name} cannot retaliate - {effect_name}")
                return False
    
    return True


def process_retaliation(
    ranged_attacker: 'Entity',
    melee_defender: 'Entity',
) -> Tuple[int, List[Dict[str, Any]]]:
    """Process retaliation strike from defender against adjacent ranged attacker.
    
    The defender gets a free melee strike. For this strike only, the attacker's
    armor is halved (scoped via context manager).
    
    Retaliation is blocked if defender is incapacitated (asleep, stunned, etc.)
    
    Args:
        ranged_attacker: Entity making the ranged attack (receives retaliation)
        melee_defender: Entity retaliating with melee
        
    Returns:
        Tuple of (retaliation_damage, results_list)
        - retaliation_damage: Damage dealt by retaliation (0 if miss/blocked)
        - results_list: Combat messages to display
    """
    from components.component_registry import ComponentType
    from message_builder import MessageBuilder as MB
    
    results = []
    
    # Check if defender can retaliate
    if not can_retaliate(melee_defender):
        return 0, results
    
    defender_fighter = melee_defender.get_component_optional(ComponentType.FIGHTER)
    if not defender_fighter:
        return 0, results
    
    # Warn about close-range danger
    results.append({
        "message": MB.combat_critical(f"⚔️ {melee_defender.name} retaliates against your close-range shot!")
    })
    
    # Track metric
    collector = _get_metrics_collector()
    if collector:
        collector.increment('ranged_adjacent_retaliations_triggered')
    
    # Execute retaliation with halved armor (context manager ensures cleanup)
    retaliation_damage = 0
    with retaliation_armor_penalty(ranged_attacker):
        retaliation_results = defender_fighter.attack_d20(ranged_attacker)
        
        # Extract damage dealt from results
        for r in retaliation_results:
            if "dead" in r:
                retaliation_damage = r.get("damage_dealt", 0)
            elif "message" in r:
                results.append(r)
                # Extract damage from message
                msg_text = str(r.get("message", ""))
                if "damage" in msg_text.lower():
                    import re
                    match = re.search(r'(\d+)\s*damage', msg_text)
                    if match:
                        retaliation_damage = max(retaliation_damage, int(match.group(1)))
    
    return retaliation_damage, results


# ═══════════════════════════════════════════════════════════════════════════════
# RANGED KNOCKBACK (Public API)
# ═══════════════════════════════════════════════════════════════════════════════

def apply_ranged_knockback(
    attacker: 'Entity',
    target: 'Entity',
    game_map: 'GameMap',
    entities: List['Entity']
) -> Dict[str, Any]:
    """Apply 1-tile knockback from ranged hit.
    
    PUBLIC API for ranged knockback. Routes through the canonical knockback
    service to respect collisions/hazards/Entity.move().
    
    10% chance to trigger (caller should roll first or pass roll result).
    
    Args:
        attacker: Entity making the ranged attack
        target: Target to knock back
        game_map: Game map for terrain checks
        entities: Entity list for blocking checks
        
    Returns:
        dict with keys:
            - applied: bool (True if knockback occurred)
            - tiles: int (tiles moved, 0-1)
            - results: List[Dict] (messages)
    """
    from message_builder import MessageBuilder as MB
    from services.knockback_service import apply_knockback_single_tile
    
    results = []
    
    # Use the public knockback service API
    kb_result = apply_knockback_single_tile(attacker, target, game_map, entities)
    
    if kb_result["tiles_moved"] > 0:
        results.append({
            "message": MB.combat(f"💨 {target.name} is knocked back by the force of the shot!")
        })
        
        # Track metric
        collector = _get_metrics_collector()
        if collector:
            collector.increment('ranged_knockback_procs')
        
        return {
            "applied": True,
            "tiles": kb_result["tiles_moved"],
            "results": results
        }
    
    return {
        "applied": False,
        "tiles": 0,
        "results": []
    }


def roll_ranged_knockback() -> bool:
    """Roll for ranged knockback chance.
    
    Returns:
        bool: True if knockback should be applied (10% chance)
    """
    return random.random() < RANGED_KNOCKBACK_CHANCE


# ═══════════════════════════════════════════════════════════════════════════════
# ARMOR CLASS INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

def get_armor_class_with_retaliation_penalty(fighter) -> int:
    """Get armor class, applying halved penalty if in retaliation context.
    
    This is called by Fighter.armor_class property to check for the temporary
    retaliation penalty flag set by retaliation_armor_penalty context manager.
    
    Args:
        fighter: Fighter component to check
        
    Returns:
        int: Adjusted armor class bonus from equipment (halved if in retaliation)
    """
    from components.component_registry import ComponentType
    
    if not hasattr(fighter, 'owner') or not fighter.owner:
        return 0
    
    equipment = fighter.owner.get_component_optional(ComponentType.EQUIPMENT)
    if not equipment:
        return 0
    
    base_ac_bonus = equipment.get_armor_class_bonus()
    
    # Check for temporary retaliation penalty (set by context manager)
    if hasattr(fighter, '_retaliation_armor_halved') and fighter._retaliation_armor_halved:
        return base_ac_bonus // 2
    
    return base_ac_bonus
