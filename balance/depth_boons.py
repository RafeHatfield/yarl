"""Depth Boons system — Phase 23 scaffold.

One boon is awarded to the player on *first arrival* at each dungeon depth.
The system is deliberately minimal: no RNG, no UI selection, no branching
pools.  These are all explicitly deferred to a later phase.

Architecture overview
---------------------
* BOON_REGISTRY — maps boon_id → BoonDefinition (metadata only).
* DEPTH_BOON_MAP — fixed depth→boon_id mapping for depths 1-5.
* apply_boon(player, boon_id) — mutates Fighter base fields in-place.
* apply_depth_boon_if_eligible(player, depth) — the main entry-point for
  both campaign (called from game_map.next_floor) and test code.

Save/load safety
----------------
All mutations land on Fighter base fields (base_max_hp, base_defense,
accuracy, damage_min) which are already serialised by data_loaders.
The visited_depths and boons_applied log live on Statistics, which is
now also serialised (see data_loaders._serialize_entity).

Determinism
-----------
DEPTH_BOON_MAP is a plain dict; no RNG is involved, so results are
identical under any seed.

Deferred
--------
* 3-choose-1 selection UI
* Large boon pool beyond depth 5
* Boon synergies / compound effects
* Boon display in sidebar
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

from components.component_registry import ComponentType

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BoonDefinition:
    """Metadata for a single boon type."""
    boon_id: str
    display_name: str
    description: str


BOON_REGISTRY: Dict[str, BoonDefinition] = {
    "fortitude_10": BoonDefinition(
        boon_id="fortitude_10",
        display_name="Fortitude",
        description="+10 max HP (also heals 10 HP immediately)",
    ),
    "accuracy_1": BoonDefinition(
        boon_id="accuracy_1",
        display_name="Keen Eye",
        description="+2 accuracy (improves to-hit chance)",
    ),
    "defense_1": BoonDefinition(
        boon_id="defense_1",
        display_name="Iron Skin",
        description="+1 defense (reduces damage taken)",
    ),
    "damage_1": BoonDefinition(
        boon_id="damage_1",
        display_name="Cruel Blow",
        description="+1 minimum damage",
    ),
    "resilience_5": BoonDefinition(
        boon_id="resilience_5",
        display_name="Resilience",
        description="+10 max HP (also heals 10 HP immediately)",
    ),
}


# ---------------------------------------------------------------------------
# Depth → boon mapping
# ---------------------------------------------------------------------------

DEPTH_BOON_MAP: Dict[int, str] = {
    1: "fortitude_10",
    2: "accuracy_1",
    3: "defense_1",
    4: "damage_1",
    5: "resilience_5",
}


def get_boon_for_depth(depth: int) -> Optional[str]:
    """Return the boon_id mapped to *depth*, or None if no mapping exists."""
    return DEPTH_BOON_MAP.get(depth)


# ---------------------------------------------------------------------------
# Boon application
# ---------------------------------------------------------------------------

def apply_boon(player: Any, boon_id: str) -> bool:
    """Apply *boon_id* to *player* by mutating Fighter base fields.

    Behaviour:
    * If fighter component is missing → return False (safe no-op).
    * If boon_id is unknown → raise ValueError (fail loudly; callers that
      want to swallow the error must catch it explicitly).
    * On success → mutate fighter fields in-place, return True.

    This function does NOT record anything to Statistics.  The caller
    (apply_depth_boon_if_eligible or _apply_player_boons in the scenario
    loader) is responsible for appending to boons_applied.

    Args:
        player: Entity with optional Fighter component.
        boon_id: ID string from BOON_REGISTRY.

    Returns:
        True if the boon was applied, False if fighter was missing.

    Raises:
        ValueError: If boon_id is not in BOON_REGISTRY.
    """
    if boon_id not in BOON_REGISTRY:
        raise ValueError(f"Unknown boon_id: '{boon_id}'. Valid IDs: {sorted(BOON_REGISTRY)}")

    fighter = player.get_component_optional(ComponentType.FIGHTER)
    if fighter is None:
        logger.warning(f"apply_boon: player has no Fighter component; boon '{boon_id}' not applied")
        return False

    if boon_id == "fortitude_10":
        fighter.base_max_hp += 10
        fighter.hp = min(fighter.hp + 10, fighter.base_max_hp)

    elif boon_id == "accuracy_1":
        fighter.accuracy += 2

    elif boon_id == "defense_1":
        fighter.base_defense += 1

    elif boon_id == "damage_1":
        fighter.damage_min += 1

    elif boon_id == "resilience_5":
        fighter.base_max_hp += 10
        fighter.hp = min(fighter.hp + 10, fighter.base_max_hp)

    # All known IDs handled above; the ValueError guard at the top means
    # we will never reach here with an unhandled known boon.
    logger.debug(f"apply_boon: applied '{boon_id}' to {getattr(player, 'name', player)}")
    return True


# ---------------------------------------------------------------------------
# Depth-gated entry point
# ---------------------------------------------------------------------------

def apply_depth_boon_if_eligible(player: Any, depth: int) -> Optional[str]:
    """Award a depth boon on first arrival at *depth*.

    This is the main entry point called by game_map.next_floor (for campaign
    play) and directly by tests.

    Rules:
    1. player must have a Statistics component (otherwise no-op).
    2. statistics.disable_depth_boons must be False.
    3. depth must not already be in statistics.visited_depths.
    4. A boon mapping must exist for depth (depths > 5 silently return None).

    Side-effects when a boon fires:
    * statistics.visited_depths.add(depth)
    * apply_boon(player, boon_id) — mutates Fighter fields
    * statistics.boons_applied.append(boon_id)
    * Logs at INFO level

    Args:
        player: Entity with Statistics and Fighter components.
        depth: The dungeon depth being entered (1-based).

    Returns:
        The boon_id that was applied, or None if no boon was awarded.

    Raises:
        ValueError: Propagated from apply_boon if BOON_REGISTRY is
            somehow inconsistent with DEPTH_BOON_MAP (programmer error).
    """
    stats = getattr(player, 'statistics', None)
    if stats is None:
        logger.debug("apply_depth_boon_if_eligible: no Statistics component; skipping")
        return None

    if getattr(stats, 'disable_depth_boons', False):
        logger.debug(f"apply_depth_boon_if_eligible: depth boons disabled; skipping depth {depth}")
        return None

    if depth in stats.visited_depths:
        logger.debug(f"apply_depth_boon_if_eligible: depth {depth} already visited; no re-grant")
        return None

    # Mark as visited regardless of whether a boon exists for this depth.
    stats.visited_depths.add(depth)

    boon_id = get_boon_for_depth(depth)
    if boon_id is None:
        logger.debug(f"apply_depth_boon_if_eligible: no boon mapped to depth {depth}")
        return None

    # apply_boon raises ValueError for unknown IDs — let it propagate.
    apply_boon(player, boon_id)
    stats.boons_applied.append(boon_id)
    logger.info(f"Depth boon applied at depth {depth}: {boon_id}")
    return boon_id
