"""Strict scenario invariant validation (Phase 12C)."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from config.entity_registry import get_entity_registry

logger = logging.getLogger(__name__)


class ScenarioInvariantError(Exception):
    """Raised when a scenario instance violates required invariants."""


def validate_scenario_instance(
    scenario,
    game_map,
    player,
    entities: List[Any],
) -> None:
    """Validate structural invariants for a scenario instance.

    Raises:
        ScenarioInvariantError on the first violation encountered.
    """
    _require_player(player)
    _validate_player_position(scenario, game_map, player, entities)

    _validate_monster_types(scenario)
    _validate_item_types(scenario)

    _validate_monsters(game_map, player, entities)
    _validate_items(game_map, player, entities)


# ---------------------------------------------------------------------------
# Type validation
# ---------------------------------------------------------------------------


def _validate_monster_types(scenario) -> None:
    registry = get_entity_registry()
    if not hasattr(registry, "monsters"):
        return
    allowed_extras = {"corpse"}
    for idx, entry in enumerate(scenario.monsters or []):
        monster_type = entry.get("type")
        if not monster_type:
            raise ScenarioInvariantError(f"Monster entry {idx} missing type")
        if monster_type not in registry.monsters and monster_type not in allowed_extras:
            raise ScenarioInvariantError(f"Monster type '{monster_type}' is not defined in registry")


def _validate_item_types(scenario) -> None:
    registry = get_entity_registry()
    valid_sets = [
        getattr(registry, "spells", {}),
        getattr(registry, "wands", {}),
        getattr(registry, "weapons", {}),
        getattr(registry, "armor", {}),
        getattr(registry, "rings", {}),
        getattr(registry, "unique_items", {}),
    ]
    for idx, entry in enumerate(scenario.items or []):
        item_type = entry.get("type")
        if not item_type:
            raise ScenarioInvariantError(f"Item entry {idx} missing type")
        if not any(item_type in s for s in valid_sets):
            raise ScenarioInvariantError(f"Item type '{item_type}' is not defined in registry")


# ---------------------------------------------------------------------------
# Player validation
# ---------------------------------------------------------------------------


def _require_player(player: Any) -> None:
    if player is None:
        raise ScenarioInvariantError("Player entity is missing")


def _validate_player_position(scenario, game_map, player, entities: List[Any]) -> None:
    if not game_map.is_in_bounds(player.x, player.y):
        raise ScenarioInvariantError(
            f"Player spawn ({player.x}, {player.y}) is out of bounds for scenario '{scenario.scenario_id}'"
        )
    tile = game_map.get_tile(player.x, player.y)
    if tile is None or tile.blocked:
        raise ScenarioInvariantError(
            f"Player spawn ({player.x}, {player.y}) is on a blocked tile for scenario '{scenario.scenario_id}'"
        )
    if any(e is not player and e.x == player.x and e.y == player.y for e in entities):
        raise ScenarioInvariantError(
            f"Player spawn ({player.x}, {player.y}) is already occupied in scenario '{scenario.scenario_id}'"
        )


# ---------------------------------------------------------------------------
# Monster validation
# ---------------------------------------------------------------------------


def _validate_monsters(game_map, player, entities: List[Any]) -> None:
    seen_positions = set()
    for entity in entities:
        if entity is player:
            continue
        if not getattr(entity, "blocks", False):
            continue  # Non-blocking entities are likely items or features

        pos = (entity.x, entity.y)
        if not game_map.is_in_bounds(entity.x, entity.y):
            raise ScenarioInvariantError(f"Monster '{getattr(entity, 'name', '?')}' is out of bounds at {pos}")
        tile = game_map.get_tile(entity.x, entity.y)
        if tile is None or tile.blocked:
            raise ScenarioInvariantError(
                f"Monster '{getattr(entity, 'name', '?')}' placed on blocked tile at {pos}"
            )
        if pos in seen_positions:
            raise ScenarioInvariantError(f"Multiple monsters occupy tile {pos}")
        seen_positions.add(pos)

        # Faction presence (common requirement for AI/targeting)
        if not getattr(entity, "faction", None):
            raise ScenarioInvariantError(f"Monster '{getattr(entity, 'name', '?')}' missing faction at {pos}")


# ---------------------------------------------------------------------------
# Item validation
# ---------------------------------------------------------------------------


def _validate_items(game_map, player, entities: List[Any]) -> None:
    blocking_positions = {(e.x, e.y) for e in entities if getattr(e, "blocks", False)}
    player_pos = (player.x, player.y)

    for entity in entities:
        if getattr(entity, "item", None) is None:
            continue  # Not an item
        pos = (entity.x, entity.y)
        if not game_map.is_in_bounds(entity.x, entity.y):
            raise ScenarioInvariantError(f"Item '{getattr(entity, 'name', '?')}' is out of bounds at {pos}")
        tile = game_map.get_tile(entity.x, entity.y)
        if tile is None or tile.blocked:
            raise ScenarioInvariantError(
                f"Item '{getattr(entity, 'name', '?')}' placed on blocked tile at {pos}"
            )
        if pos in blocking_positions or pos == player_pos:
            raise ScenarioInvariantError(
                f"Item '{getattr(entity, 'name', '?')}' overlaps an occupied tile at {pos}"
            )
