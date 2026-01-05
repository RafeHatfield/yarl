"""Scenario map and entity builder (Phase 12C).

Creates a lightweight map plus player/monster/item placements from a
ScenarioDefinition. This module is used only by the scenario harness and
does not affect normal campaign generation.
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from components.component_registry import ComponentType
from components.equipment import Equipment
from components.fighter import Fighter
from components.inventory import Inventory
from components.level import Level
from components.player_pathfinding import PlayerPathfinding
from components.speed_bonus_tracker import SpeedBonusTracker
from components.statistics import Statistics
from components.faction import Faction
from config.factories import get_entity_factory
from config.game_constants import get_combat_config, get_inventory_config
from entity import Entity
from map_objects.game_map import GameMap
from render_functions import RenderOrder

logger = logging.getLogger(__name__)


@dataclass
class ScenarioMapResult:
    """Container for scenario map construction output."""

    game_map: GameMap
    player: Entity
    entities: List[Entity]


class ScenarioBuildError(Exception):
    """Raised when a scenario map or entity fails to build."""


class _ModuleLevelRandom:
    """Wrapper that delegates to module-level random functions.
    
    This allows build_scenario_map to use the module-level random (which is
    seeded by set_global_seed) by default, while still accepting an explicit
    random.Random instance for tests.
    """
    
    def randint(self, a: int, b: int) -> int:
        return random.randint(a, b)
    
    def choice(self, seq):
        return random.choice(seq)
    
    def shuffle(self, seq):
        return random.shuffle(seq)


# Singleton instance for module-level random delegation
_module_rng = _ModuleLevelRandom()


def build_scenario_map(scenario, rng: Optional[random.Random] = None) -> ScenarioMapResult:
    """Construct a simple map plus entities for a scenario.

    Args:
        scenario: ScenarioDefinition
        rng: Optional random.Random for deterministic tests. If None, uses
             the module-level random (which respects set_global_seed).

    Returns:
        ScenarioMapResult with map, player, and all entities (player first)

    Raises:
        ScenarioBuildError: on construction failures (invalid types, etc.)
    """
    # Use module-level random by default (respects set_global_seed)
    rng = rng or _module_rng

    # Map dimensions: derive from rooms if present; otherwise use a small arena.
    default_width = 30
    default_height = 20
    width, height = _derive_map_size(scenario.rooms, default_width, default_height)
    dungeon_level = scenario.depth or 1

    game_map = GameMap(width, height, dungeon_level=dungeon_level)
    _carve_open_floor(game_map)
    
    # Apply obstacles (walls/pillars) after carving floor
    _apply_obstacles(scenario.rooms, game_map)

    player = _create_player_entity(scenario.player)
    _apply_player_position(player, scenario.player, game_map)

    entities: List[Entity] = [player]

    _spawn_monsters(scenario.monsters or [], entities, game_map, rng)
    _spawn_items(scenario.items or [], entities, game_map, rng, dungeon_level)
    _spawn_portals(scenario.portals or [], entities, game_map)

    return ScenarioMapResult(game_map=game_map, player=player, entities=entities)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _derive_map_size(
    rooms: Optional[List[Dict[str, Any]]],
    fallback_w: int,
    fallback_h: int,
) -> Tuple[int, int]:
    if not rooms:
        return fallback_w, fallback_h

    max_w = max(room.get("width", 0) for room in rooms if isinstance(room, dict)) or fallback_w
    max_h = max(room.get("height", 0) for room in rooms if isinstance(room, dict)) or fallback_h
    # Provide a little buffer around the largest room.
    return max(max_w + 4, fallback_w), max(max_h + 4, fallback_h)


def _carve_open_floor(game_map: GameMap) -> None:
    """Turn the entire map into walkable floor."""
    for x in range(game_map.width):
        for y in range(game_map.height):
            tile = game_map.get_tile(x, y)
            if tile:
                tile.blocked = False
                tile.block_sight = False


def _apply_obstacles(rooms: Optional[List[Dict[str, Any]]], game_map: GameMap) -> None:
    """Apply obstacles (walls/pillars) from room definitions.
    
    Obstacles are defined in room config as:
        obstacles:
          - position: [x, y]  # Single tile wall/pillar
          - position: [x, y]
    
    Each obstacle creates a tile that is both blocked and blocks sight,
    enabling LOS breaks in otherwise open arenas.
    """
    if not rooms:
        return
    
    for room in rooms:
        if not isinstance(room, dict):
            continue
        
        obstacles = room.get("obstacles", [])
        if not obstacles:
            continue
        
        for obstacle in obstacles:
            if not isinstance(obstacle, dict):
                continue
            
            pos = obstacle.get("position")
            if not isinstance(pos, (list, tuple)) or len(pos) != 2:
                continue
            
            x, y = int(pos[0]), int(pos[1])
            
            # Bounds check
            if not game_map.is_in_bounds(x, y):
                logger.warning(f"Obstacle position out of bounds: ({x}, {y})")
                continue
            
            tile = game_map.get_tile(x, y)
            if tile:
                tile.blocked = True
                tile.block_sight = True
                logger.debug(f"Placed obstacle at ({x}, {y})")


def _create_player_entity(player_cfg: Optional[Dict[str, Any]]) -> Entity:
    """Build a player entity using base stats and optional overrides."""
    entity_factory = get_entity_factory()
    player_stats = entity_factory.get_player_stats()

    combat_config = get_combat_config()
    inventory_config = get_inventory_config()

    fighter_component = Fighter(
        hp=player_stats.hp,
        defense=player_stats.defense,
        power=player_stats.power,
        damage_min=getattr(player_stats, "damage_min", 0),
        damage_max=getattr(player_stats, "damage_max", 0),
        strength=getattr(player_stats, "strength", 14),
        dexterity=getattr(player_stats, "dexterity", 12),
        constitution=getattr(player_stats, "constitution", 14),
        accuracy=getattr(player_stats, "accuracy", None),
        evasion=getattr(player_stats, "evasion", None),
    )
    inventory_component = Inventory(inventory_config.DEFAULT_INVENTORY_CAPACITY)
    level_component = Level(
        level_up_base=combat_config.DEFAULT_LEVEL_UP_BASE,
        level_up_factor=combat_config.DEFAULT_LEVEL_UP_FACTOR,
    )
    equipment_component = Equipment()
    statistics_component = Statistics()
    pathfinding_component = PlayerPathfinding()

    player = Entity.create_player(
        x=0,
        y=0,
        fighter=fighter_component,
        inventory=inventory_component,
        level=level_component,
        equipment=equipment_component,
    )

    # Register extra components
    player.pathfinding = pathfinding_component
    pathfinding_component.owner = player
    player.components.add(ComponentType.PATHFINDING, pathfinding_component)

    player.statistics = statistics_component
    statistics_component.owner = player
    player.components.add(ComponentType.STATISTICS, statistics_component)

    speed_bonus_component = SpeedBonusTracker(speed_bonus_ratio=0.25)
    player.speed_bonus_tracker = speed_bonus_component
    speed_bonus_component.owner = player
    player.components.add(ComponentType.SPEED_BONUS_TRACKER, speed_bonus_component)

    _apply_player_loadout(player, player_cfg or {})
    # Ensure HP starts at max after equipment adjustments
    if hasattr(player, "fighter"):
        player.fighter.hp = player.fighter.max_hp

    return player


def _apply_player_position(player: Entity, player_cfg: Optional[Dict[str, Any]], game_map: GameMap) -> None:
    """Place the player; default to top-left safe tile if unspecified."""
    if player_cfg and "position" in player_cfg and isinstance(player_cfg["position"], (list, tuple)):
        pos = player_cfg["position"]
        if len(pos) == 2:
            player.x, player.y = int(pos[0]), int(pos[1])
            return
    # Fallback spawn near top-left on a walkable tile.
    for x in range(game_map.width):
        for y in range(game_map.height):
            if not game_map.tiles[x][y].blocked:
                player.x, player.y = x, y
                return


def _apply_player_loadout(player: Entity, player_cfg: Dict[str, Any]) -> None:
    """Apply inventory and equipment overrides from scenario config."""
    entity_factory = get_entity_factory()
    inventory_cfg = player_cfg.get("inventory", []) if isinstance(player_cfg, dict) else []
    equipment_cfg = player_cfg.get("equipment", {}) if isinstance(player_cfg, dict) else {}

    # Inventory items
    for item_entry in inventory_cfg:
        # Phase 17B: Support both string format ("healing_potion") and dict format ({"type": "healing_potion"})
        if isinstance(item_entry, str):
            item_type = item_entry
            count = 1
        elif isinstance(item_entry, dict):
            item_type = item_entry.get("type")
            count = int(item_entry.get("count", 1))
        else:
            continue
        
        if not item_type:
            continue
        
        for _ in range(max(count, 1)):
            # Phase 17B: Try all item creation methods (spell_item includes potions)
            item_entity = (
                entity_factory.create_spell_item(item_type, player.x, player.y)  # Potions, scrolls
                or entity_factory.create_wand(item_type, player.x, player.y)     # Wands
            )
            if item_entity:
                player.require_component(ComponentType.INVENTORY).add_item(item_entity)

    # Equipment overrides
    if equipment_cfg:
        for slot_key, equip_type in equipment_cfg.items():
            if not equip_type:
                continue
            equip_entity = (
                entity_factory.create_weapon(equip_type, player.x, player.y)
                or entity_factory.create_armor(equip_type, player.x, player.y)
                or entity_factory.create_ring(equip_type, player.x, player.y)
            )
            if equip_entity:
                inv = player.require_component(ComponentType.INVENTORY)
                inv.add_item(equip_entity)
                equip = player.get_component_optional(ComponentType.EQUIPMENT)
                if equip:
                    equip.toggle_equip(equip_entity)


def _spawn_monsters(monster_entries, entities: List[Entity], game_map: GameMap, rng: random.Random) -> None:
    factory = get_entity_factory()
    for entry in monster_entries:
        monster_type = entry.get("type")
        if not monster_type:
            continue
        count = max(1, int(entry.get("count", 1)))
        
        # Special-case inert corpses: they are not true monsters and should not
        # go through the monster factory (avoids "Unknown monster type: corpse").
        if monster_type == "corpse":
            for _ in range(count):
                x, y = _resolve_position(entry, game_map, entities, rng)
                corpse = _create_corpse_entity(x, y, entry)
                entities.append(corpse)
            continue
        
        for _ in range(count):
            x, y = _resolve_position(entry, game_map, entities, rng)
            monster = factory.create_monster(monster_type, x, y)
            if monster is None:
                raise ScenarioBuildError(f"Unknown monster type '{monster_type}'")
            if getattr(monster, "faction", None) is None:
                monster.faction = Faction.NEUTRAL
            
            # Phase 20D.1: Apply special monster combat state from YAML
            # state: "in_combat" sets in_combat=True so monster chases player without FOV
            # Note: state: "aware" is NOT processed to preserve existing baseline behavior
            monster_state = entry.get("state", "unaware")
            if monster_state == "in_combat" and hasattr(monster, 'ai') and monster.ai:
                if hasattr(monster.ai, 'in_combat'):
                    monster.ai.in_combat = True
            
            entities.append(monster)


def _spawn_items(
    item_entries,
    entities: List[Entity],
    game_map: GameMap,
    rng: random.Random,
    dungeon_level: int,
) -> None:
    factory = get_entity_factory()
    for entry in item_entries:
        item_type = entry.get("type")
        if not item_type:
            continue
        count = max(1, int(entry.get("count", 1)))
        for _ in range(count):
            x, y = _resolve_position(entry, game_map, entities, rng)
            
            # Special case: Wand of Portals (legendary item)
            if item_type == "wand_of_portals":
                item_entity = factory.create_wand_of_portals(x, y)
            else:
                # Standard item creation fallback chain
                item_entity = (
                    factory.create_spell_item(item_type, x, y)
                    or factory.create_wand(item_type, x, y, dungeon_level=dungeon_level)
                    or factory.create_weapon(item_type, x, y)
                    or factory.create_armor(item_type, x, y)
                    or factory.create_ring(item_type, x, y)
                )
            
            if item_entity is None:
                raise ScenarioBuildError(f"Unknown item type '{item_type}'")
            entities.append(item_entity)


def _spawn_portals(
    portal_entries: List[Dict[str, Any]],
    entities: List[Entity],
    game_map: GameMap,
) -> None:
    """Spawn portals defined in a scenario.

    Supports explicit positions and bidirectional linking via ids.
    """
    if not portal_entries:
        return

    from services.portal_manager import get_portal_manager

    portal_manager = get_portal_manager()
    created: Dict[str, Entity] = {}
    pending_links: List[Tuple[Portal, str]] = []

    for entry in portal_entries:
        portal_type = entry.get("type")
        pos = entry.get("position")
        portal_id = entry.get("id")
        link_to = entry.get("link_to")

        if portal_type not in ("entrance", "exit", "entity_portal"):
            raise ScenarioBuildError(f"Unknown portal type '{portal_type}'")
        if not (isinstance(pos, (list, tuple)) and len(pos) == 2):
            raise ScenarioBuildError(f"Portal entry missing position: {entry}")

        x, y = int(pos[0]), int(pos[1])
        if not game_map.is_in_bounds(x, y):
            raise ScenarioBuildError(f"Portal position out of bounds: ({x}, {y})")
        if game_map.get_tile(x, y) is None or game_map.get_tile(x, y).blocked:
            raise ScenarioBuildError(f"Portal position blocked: ({x}, {y})")

        linked_component = None
        if link_to and link_to in created and hasattr(created[link_to], "portal"):
            linked_component = created[link_to].portal

        portal_entity = portal_manager.create_portal_entity(
            portal_type=portal_type,
            x=x,
            y=y,
            linked_portal=linked_component,
            from_yaml=True,
        )
        if portal_entity is None:
            raise ScenarioBuildError(f"Failed to create portal entity ({portal_type}) at ({x}, {y})")

        # If we already know the counterpart, link back
        if linked_component and portal_entity.portal.linked_portal is None:
            portal_entity.portal.linked_portal = linked_component
            linked_component.linked_portal = portal_entity.portal

        entities.append(portal_entity)

        if portal_id:
            created[portal_id] = portal_entity
        if link_to:
            pending_links.append((portal_entity.portal, link_to))

    # Resolve any links where the destination was defined later
    for portal_component, link_id in pending_links:
        if portal_component.linked_portal:
            continue
        target_entity = created.get(link_id)
        if not target_entity or not hasattr(target_entity, "portal"):
            raise ScenarioBuildError(f"Link target '{link_id}' not found for portal")
        portal_component.linked_portal = target_entity.portal
        target_entity.portal.linked_portal = portal_component


def _resolve_position(entry: Dict[str, Any], game_map: GameMap, entities: List[Entity], rng: random.Random) -> Tuple[int, int]:
    """Resolve an explicit position, region, or fallback to a random walkable tile."""
    if "position" in entry and isinstance(entry["position"], (list, tuple)):
        pos = entry["position"]
        if len(pos) == 2:
            return int(pos[0]), int(pos[1])

    region = entry.get("region") or entry.get("spawn_zone")
    if isinstance(region, str):
        rx, ry = _position_from_region(region, game_map, rng)
        if rx is not None and ry is not None:
            if not _is_occupied(rx, ry, entities):
                return rx, ry

    return _random_walkable_position(game_map, entities, rng)


def _create_corpse_entity(x: int, y: int, entry: Dict[str, Any]) -> Entity:
    """Create an inert corpse entity (non-monster)."""
    name = entry.get("name") or "corpse"
    corpse = Entity(
        x=x,
        y=y,
        char='%',
        color=(127, 0, 0),
        name=name,
        blocks=False,
        render_order=RenderOrder.CORPSE,
    )
    # Corpses should not have combat or AI components
    corpse.fighter = None
    corpse.ai = None
    return corpse


def _position_from_region(region: str, game_map: GameMap, rng: random.Random) -> Tuple[Optional[int], Optional[int]]:
    """Very simple region mapping for Phase 12C."""
    region = region.lower()
    rects = {
        "start": (1, 1, max(2, game_map.width // 4), max(2, game_map.height // 4)),
        "corridor": (1, game_map.height // 3, game_map.width - 2, max(2, game_map.height // 4)),
        "arena": (2, 2, game_map.width - 4, game_map.height - 4),
        "plague_arena_main": (2, 2, game_map.width - 4, game_map.height - 4),
        "safe_alcove": (1, 1, max(4, game_map.width // 5), max(4, game_map.height // 5)),
    }
    if region not in rects:
        return None, None
    x0, y0, rw, rh = rects[region]
    rx = rng.randint(x0, min(game_map.width - 1, x0 + max(1, rw) - 1))
    ry = rng.randint(y0, min(game_map.height - 1, y0 + max(1, rh) - 1))
    return rx, ry


def _random_walkable_position(game_map: GameMap, entities: List[Entity], rng: random.Random) -> Tuple[int, int]:
    attempts = game_map.width * game_map.height
    for _ in range(attempts):
        x = rng.randint(0, game_map.width - 1)
        y = rng.randint(0, game_map.height - 1)
        if game_map.is_in_bounds(x, y) and not game_map.tiles[x][y].blocked and not _is_occupied(x, y, entities):
            return x, y
    # As a last resort, just return origin (validator will catch issues)
    return 0, 0


def _is_occupied(x: int, y: int, entities: List[Entity]) -> bool:
    return any(e.x == x and e.y == y for e in entities)
