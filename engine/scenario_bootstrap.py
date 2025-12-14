"""Scenario bootstrap for bot-soak and harness runs.

This module provides the canonical entry point for creating game sessions
from scenario definitions. It ensures:

1. Scenario maps are loaded from YAML, not from procedural worldgen
2. An `is_scenario_run` flag is set to guard against worldgen fallbacks
3. scenario_id is wired into run_metrics and telemetry
4. Defensive checks verify the scenario map is actually used

CODE PATH DOCUMENTATION:
========================

NORMAL WORLDGEN PATH (campaign mode):
-------------------------------------
engine.py main() → get_game_variables(constants)
  → load_entity_config(), register_all_spells(), reset_*()
  → Creates player with dagger, leather armor, healing potion, wand of portals
  → game_map.make_map() generates procedural dungeon
  → initialize_run_metrics_recorder()
  → Returns (player, entities, game_map, message_log, game_state)

SCENARIO PATH (bot-soak --scenario <id>):
-----------------------------------------
engine.py main() → run_bot_soak() 
  → constants["scenario_id"] = args.scenario
  → (per run) create_scenario_session(scenario_id, constants)
      → Loads ScenarioDefinition from registry
      → build_scenario_map(scenario) creates map from YAML, not procedural
      → Player equipment comes from YAML only (no default potions)
      → Sets game_state.is_scenario_run = True
      → Sets game_state.scenario_monsters for defensive checks
      → Returns (player, entities, game_map, message_log, game_state)
  → play_game_with_engine() runs with scenario map

KEY DIFFERENCE: Scenario path uses build_scenario_map() which loads from YAML.
Campaign path uses game_map.make_map() which generates procedurally.
If a scenario run somehow triggers make_map(), the scenario is broken.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from components.component_registry import ComponentType
from config.level_template_registry import get_scenario_registry, ScenarioDefinition
from game_messages import MessageLog
from game_states import GameStates
from services.scenario_level_loader import build_scenario_map, ScenarioMapResult

logger = logging.getLogger(__name__)


@dataclass
class ScenarioMonsterMarker:
    """Marker for a specific monster expected from a scenario definition.
    
    Used for defensive checks to verify the scenario map wasn't overwritten.
    """
    monster_type: str
    x: int
    y: int


@dataclass
class ScenarioRunContext:
    """Context object tracking scenario-specific state for a run.
    
    This object is attached to the game state to enable defensive checks
    and proper telemetry tracking throughout the run.
    """
    scenario_id: str
    scenario_name: str
    depth: int
    expected_monsters: List[ScenarioMonsterMarker]
    is_validated: bool = False
    
    def validate_monsters_present(self, entities: List[Any]) -> Tuple[bool, str]:
        """Validate that expected scenario monsters are present.
        
        Args:
            entities: List of all game entities
            
        Returns:
            Tuple of (is_valid, message)
        """
        if not self.expected_monsters:
            return True, "No monster markers to validate"
        
        found_count = 0
        missing = []
        
        for marker in self.expected_monsters:
            found = False
            for entity in entities:
                if (hasattr(entity, 'x') and hasattr(entity, 'y') and
                    entity.x == marker.x and entity.y == marker.y):
                    # Found an entity at this position
                    fighter = entity.get_component_optional(ComponentType.FIGHTER)
                    if fighter:
                        found = True
                        found_count += 1
                        break
            
            if not found:
                missing.append(f"{marker.monster_type} at ({marker.x}, {marker.y})")
        
        if missing:
            return False, f"Missing expected monsters: {', '.join(missing)}"
        
        self.is_validated = True
        return True, f"Validated {found_count}/{len(self.expected_monsters)} scenario monsters"


def create_scenario_session(
    scenario_id: str,
    constants: Dict[str, Any],
) -> Tuple[Any, List[Any], Any, MessageLog, GameStates]:
    """Create a game session from a scenario definition.
    
    This is the canonical entry point for scenario-based runs (bot-soak, harness).
    It replaces the combination of get_game_variables() + procedural worldgen
    with scenario map loading from YAML.
    
    CRITICAL: This function sets game_state.is_scenario_run = True to guard
    against any code paths that might try to run worldgen on the session.
    
    Args:
        scenario_id: Unique identifier for the scenario (e.g., "orc_swarm_tight")
        constants: Game constants dict (will be mutated to include scenario context)
        
    Returns:
        Tuple of (player, entities, game_map, message_log, game_state)
        
    Raises:
        ValueError: if scenario_id not found in registry
    """
    from config.entity_registry import load_entity_config
    from config.identification_manager import reset_identification_manager
    from config.item_appearances import reset_appearance_generator
    from spells.spell_catalog import register_all_spells
    from balance.pity import reset_pity_state
    from services.monster_knowledge import reset_monster_knowledge_system
    from services.mural_manager import get_mural_manager
    from instrumentation.run_metrics import initialize_run_metrics_recorder
    from services.telemetry_service import get_telemetry_service
    
    # Load scenario definition
    registry = get_scenario_registry()
    scenario = registry.get_scenario_definition(scenario_id)
    
    if scenario is None:
        available = registry.list_scenarios()
        raise ValueError(
            f"Scenario '{scenario_id}' not found. Available: {', '.join(available)}"
        )
    
    logger.info(f"Creating scenario session: {scenario_id} ({scenario.name})")
    
    # === CRITICAL INITIALIZATION (same as get_game_variables) ===
    load_entity_config()
    
    # Initialize mural manager  
    mural_mgr = get_mural_manager()
    mural_mgr.set_current_floor(scenario.depth or 1)
    
    # Register all spells
    register_all_spells()
    
    # Initialize item identification system
    reset_appearance_generator()
    reset_identification_manager()
    
    # Reset pity system
    reset_pity_state()
    
    # Reset monster knowledge
    reset_monster_knowledge_system()
    
    # === BUILD SCENARIO MAP ===
    # This is the KEY difference from campaign mode:
    # - Campaign mode: game_map.make_map() generates procedural dungeon
    # - Scenario mode: build_scenario_map() loads from YAML definition
    map_result = build_scenario_map(scenario)
    
    # === CREATE SCENARIO RUN CONTEXT ===
    # Build list of expected monsters for defensive validation
    expected_monsters = []
    for monster_entry in (scenario.monsters or []):
        monster_type = monster_entry.get("type")
        pos = monster_entry.get("position")
        if monster_type and pos and len(pos) == 2:
            expected_monsters.append(ScenarioMonsterMarker(
                monster_type=monster_type,
                x=int(pos[0]),
                y=int(pos[1])
            ))
    
    scenario_context = ScenarioRunContext(
        scenario_id=scenario_id,
        scenario_name=scenario.name,
        depth=scenario.depth or 1,
        expected_monsters=expected_monsters,
    )
    
    # Store scenario context on game_map for access during run
    map_result.game_map.scenario_context = scenario_context
    
    # CRITICAL FLAG: Mark this as a scenario run
    # This prevents any code from accidentally triggering worldgen
    map_result.game_map.is_scenario_run = True
    
    # === SCENARIO CANARY ===
    # This is a unique, deterministic marker that worldgen can NEVER create.
    # Used as a tripwire to detect if worldgen overwrote the scenario map.
    # The canary is a hash of scenario_id + "canary" to ensure uniqueness.
    import hashlib
    canary_hash = hashlib.sha256(f"{scenario_id}:canary".encode()).hexdigest()[:16]
    map_result.game_map._scenario_canary = f"SCENARIO_CANARY_{canary_hash}"
    logger.info(f"Scenario canary planted: {map_result.game_map._scenario_canary}")
    
    # === INITIALIZE RUN METRICS WITH SCENARIO_ID ===
    bot_enabled = constants.get("input_config", {}).get("bot_enabled", False)
    run_mode = "bot" if bot_enabled else "human"
    soak_config = constants.get("soak_config", {})
    
    initialize_run_metrics_recorder(
        mode=run_mode,
        seed=soak_config.get("seed"),
        start_floor=scenario.depth or 1,
        max_turns=soak_config.get("max_turns"),
        max_floors=None,  # Scenarios are single-floor, no floor limit
        scenario_id=scenario_id,  # CRITICAL: Pass scenario_id for proper attribution
    )
    logger.info(
        f"Run metrics initialized for scenario {scenario_id} "
        f"(depth={scenario.depth or 1}, max_turns={soak_config.get('max_turns')})"
    )
    
    # === INITIALIZE TELEMETRY ===
    telemetry_service = get_telemetry_service()
    if telemetry_service.enabled:
        telemetry_service.start_floor(map_result.game_map.dungeon_level)
        _populate_scenario_telemetry(telemetry_service, map_result.game_map, map_result.entities)
    
    # === CREATE MESSAGE LOG ===
    message_log = MessageLog(
        constants["message_x"],
        constants["message_width"],
        constants["message_height"],
    )
    
    # === SET GAME STATE ===
    game_state = GameStates.PLAYERS_TURN
    
    # Log summary
    monster_count = len([e for e in map_result.entities 
                        if e.get_component_optional(ComponentType.FIGHTER) 
                        and e != map_result.player])
    logger.info(
        f"Scenario session created: {scenario_id}, "
        f"{monster_count} monsters, "
        f"map {map_result.game_map.width}x{map_result.game_map.height}"
    )
    
    return (
        map_result.player,
        map_result.entities,
        map_result.game_map,
        message_log,
        game_state,
    )


def check_scenario_canary(game_map: Any) -> Tuple[bool, str]:
    """Check if the scenario canary marker is present.
    
    The canary is a unique marker that worldgen can NEVER create.
    If it's missing, worldgen has overwritten the scenario map.
    
    Args:
        game_map: The GameMap to check
        
    Returns:
        Tuple of (is_valid, message)
    """
    canary = getattr(game_map, '_scenario_canary', None)
    is_scenario_run = getattr(game_map, 'is_scenario_run', False)
    
    if not is_scenario_run:
        return True, "Not a scenario run, canary check skipped"
    
    if canary is None:
        return False, "SCENARIO CANARY MISSING - worldgen overwrote the scenario map!"
    
    if not canary.startswith("SCENARIO_CANARY_"):
        return False, f"SCENARIO CANARY CORRUPTED - got '{canary}'"
    
    return True, f"Scenario canary intact: {canary}"


def validate_scenario_map_not_overwritten(game_map: Any, entities: List[Any]) -> None:
    """Defensive check to ensure the scenario map wasn't overwritten by worldgen.
    
    This function should be called at the start of the first turn in scenario mode.
    It verifies:
    1. The scenario canary marker is present
    2. Expected monsters from the scenario definition are present
    
    Args:
        game_map: The GameMap to validate
        entities: List of all entities
        
    Raises:
        AssertionError: if the scenario map appears to have been overwritten
    """
    if not getattr(game_map, 'is_scenario_run', False):
        # Not a scenario run, skip validation
        return
    
    # === CHECK CANARY FIRST ===
    # This is the most reliable check - if the canary is missing, worldgen ran
    canary_valid, canary_msg = check_scenario_canary(game_map)
    if not canary_valid:
        error_msg = f"SCENARIO MAP VALIDATION FAILED: {canary_msg}"
        logger.error(error_msg)
        raise AssertionError(error_msg)
    
    logger.info(f"Canary check passed: {canary_msg}")
    
    # === CHECK EXPECTED MONSTERS ===
    scenario_context = getattr(game_map, 'scenario_context', None)
    if not scenario_context:
        logger.warning("Scenario run flag set but no scenario_context found")
        return
    
    is_valid, message = scenario_context.validate_monsters_present(entities)
    
    if not is_valid:
        # CRITICAL: This means worldgen probably overwrote the scenario map
        error_msg = (
            f"SCENARIO MAP VALIDATION FAILED for {scenario_context.scenario_id}: {message}. "
            f"This usually means worldgen/new_game code overwrote the scenario map."
        )
        logger.error(error_msg)
        raise AssertionError(error_msg)
    
    logger.info(f"Scenario map validation passed: {message}")


def _populate_scenario_telemetry(telemetry_service, game_map, entities):
    """Populate telemetry data for a scenario floor.
    
    Similar to _populate_floor_telemetry in initialize_new_game.py but
    adapted for scenario context.
    """
    monster_count = 0
    item_count = 0
    
    for entity in entities:
        if hasattr(entity, 'name') and entity.name == "Player":
            continue
        
        fighter = entity.get_component_optional(ComponentType.FIGHTER)
        ai = entity.get_component_optional(ComponentType.AI)
        if fighter and ai:
            monster_count += 1
        
        item_comp = entity.get_component_optional(ComponentType.ITEM)
        if item_comp:
            item_count += 1
    
    telemetry_service.set_room_counts(
        rooms=1,  # Scenarios typically have one arena/room
        monsters=monster_count,
        items=item_count
    )
    
    logger.info(f"Scenario floor telemetry: Monsters={monster_count}, Items={item_count}")
