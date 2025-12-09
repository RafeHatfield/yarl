"""Scenario Harness for Phase 12B.

This module provides infrastructure for running scenario-based simulations,
enabling automated testing of specific game mechanics.

Phase 12B: Scenario Harness & Basic Metrics
- RunMetrics: Per-run metrics tracking
- AggregatedMetrics: Multi-run aggregation
- BotPolicy: Abstraction for player control in scenarios
- run_scenario_once: Single scenario execution
- run_scenario_many: Multi-run aggregation

Usage:
    from services.scenario_harness import (
        run_scenario_once,
        run_scenario_many,
        make_bot_policy,
    )
    
    scenario = get_scenario_definition("backstab_training")
    policy = make_bot_policy("observe_only")
    metrics = run_scenario_once(scenario, policy, turn_limit=200)
"""

import logging
import os
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol

from components.component_registry import ComponentType
from game_states import GameStates
from loader_functions.initialize_new_game import get_constants
from game_messages import MessageLog
from services.scenario_invariants import ScenarioInvariantError, validate_scenario_instance
from services.scenario_level_loader import (
    ScenarioBuildError,
    ScenarioMapResult,
    build_scenario_map,
)

logger = logging.getLogger(__name__)


# =============================================================================
# RunMetrics: Per-run metrics tracking
# =============================================================================

@dataclass
class RunMetrics:
    """Metrics collected from a single scenario run."""
    turns_taken: int = 0
    player_died: bool = False
    kills_by_faction: Dict[str, int] = field(default_factory=dict)
    kills_by_source: Dict[str, int] = field(default_factory=dict)
    plague_infections: int = 0
    reanimations: int = 0
    surprise_attacks: int = 0
    bonus_attacks_triggered: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'turns_taken': self.turns_taken,
            'player_died': self.player_died,
            'kills_by_faction': dict(self.kills_by_faction),
            'kills_by_source': dict(self.kills_by_source),
            'plague_infections': self.plague_infections,
            'reanimations': self.reanimations,
            'surprise_attacks': self.surprise_attacks,
            'bonus_attacks_triggered': self.bonus_attacks_triggered,
        }


# =============================================================================
# AggregatedMetrics: Multi-run aggregation
# =============================================================================

@dataclass
class AggregatedMetrics:
    """Aggregated metrics from multiple scenario runs."""
    runs: int = 0
    average_turns: float = 0.0
    player_deaths: int = 0
    total_kills_by_faction: Dict[str, int] = field(default_factory=dict)
    total_kills_by_source: Dict[str, int] = field(default_factory=dict)
    total_plague_infections: int = 0
    total_reanimations: int = 0
    total_surprise_attacks: int = 0
    total_bonus_attacks_triggered: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'runs': self.runs,
            'average_turns': round(self.average_turns, 2),
            'player_deaths': self.player_deaths,
            'total_kills_by_faction': dict(self.total_kills_by_faction),
            'total_kills_by_source': dict(self.total_kills_by_source),
            'total_plague_infections': self.total_plague_infections,
            'total_reanimations': self.total_reanimations,
            'total_surprise_attacks': self.total_surprise_attacks,
            'total_bonus_attacks_triggered': self.total_bonus_attacks_triggered,
        }


from services.scenario_metrics import (
    get_active_metrics_collector,
    scoped_metrics_collector,
)


# =============================================================================
# BotPolicy: Protocol for player control
# =============================================================================

class BotPolicy(Protocol):
    """Protocol for bot policies that control the player in scenarios.
    
    Bot policies decide what action the player takes each turn during
    automated scenario runs. Different policies can implement different
    behaviors (passive observation, aggressive combat, etc.).
    """
    
    def choose_action(self, game_state: Any) -> Optional[Dict[str, Any]]:
        """Choose an action for the player to take.
        
        Args:
            game_state: Current game state object containing player, entities,
                        game_map, message_log, and current_state.
        
        Returns:
            Action dict compatible with ActionProcessor, or None for no-op/wait.
            Common actions:
            - {'wait': True} - Wait/pass turn
            - {'move': (dx, dy)} - Move in direction
            - None - Interpreted as wait
        """
        ...


class ObserveOnlyPolicy:
    """Bot policy that always waits/does nothing.
    
    This policy is useful for testing game mechanics where we want to
    observe AI/environment behavior without player intervention.
    """
    
    def choose_action(self, game_state: Any) -> Optional[Dict[str, Any]]:
        """Always return a wait action.
        
        Args:
            game_state: Current game state (unused)
            
        Returns:
            Wait action dict
        """
        return {'wait': True}


def make_bot_policy(name: str) -> BotPolicy:
    """Factory function to create bot policies by name.
    
    Args:
        name: Policy name. Supported:
            - "observe_only": Passive policy that always waits
            
    Returns:
        BotPolicy instance
        
    Raises:
        ValueError: If policy name is not recognized
    """
    name_lower = name.lower().replace("-", "_").replace(" ", "_")
    
    if name_lower == "observe_only":
        return ObserveOnlyPolicy()
    if name_lower == "tactical_fighter":
        return TacticalFighterPolicy()
    
    raise ValueError(f"Unknown bot policy: {name}")


class TacticalFighterPolicy:
    """Simple deterministic fighter bot for combat scenarios."""
    
    def choose_action(self, game_state: Any) -> Optional[Dict[str, Any]]:
        player = game_state.player
        entities = game_state.entities or []
        game_map = game_state.game_map
        
        # Identify enemies (any living fighter with AI, not the player)
        enemies = [
            e for e in entities
            if e != player
            and getattr(e, 'fighter', None)
            and getattr(e.fighter, 'hp', 0) > 0
            and getattr(e, 'ai', None) is not None
        ]
        if not enemies:
            return {'wait': True}
        
        # Find nearest enemy by manhattan distance
        def manhattan(e):
            return abs(e.x - player.x) + abs(e.y - player.y)
        enemies.sort(key=manhattan)
        target = enemies[0]
        
        dx = target.x - player.x
        dy = target.y - player.y
        if abs(dx) <= 1 and abs(dy) <= 1:
            return {'attack': target}
        
        # Move one step toward target if not blocked
        step_x = 0 if dx == 0 else (1 if dx > 0 else -1)
        step_y = 0 if dy == 0 else (1 if dy > 0 else -1)
        
        dest_x, dest_y = player.x + step_x, player.y + step_y
        if (0 <= dest_x < game_map.width and 0 <= dest_y < game_map.height
            and not game_map.is_blocked(dest_x, dest_y)):
            blocking = next((e for e in entities if e.blocks and e.x == dest_x and e.y == dest_y), None)
            if blocking is None:
                return {'move': (step_x, step_y)}
        
        return {'wait': True}


# =============================================================================
# Scenario Runner
# =============================================================================

def _initialize_headless_mode() -> None:
    """Initialize headless mode for scenario runs.
    
    Sets environment variables to disable display output for automated
    scenario testing.
    """
    os.environ['SDL_VIDEODRIVER'] = 'dummy'


def _create_game_state_from_map(result: ScenarioMapResult, constants: Dict[str, Any]):
    """Create a simple game state object from a scenario map result."""
    message_log = MessageLog(
        constants["message_x"],
        constants["message_width"],
        constants["message_height"],
    )

    class SimpleGameState:
        def __init__(self, player, entities, game_map, message_log, constants):
            self.player = player
            self.entities = entities
            self.game_map = game_map
            self.message_log = message_log
            self.current_state = GameStates.PLAYERS_TURN
            self.constants = constants
            self.fov_recompute = True
            self.fov_map = None

    return SimpleGameState(
        player=result.player,
        entities=result.entities,
        game_map=result.game_map,
        message_log=message_log,
        constants=constants,
    )


def _process_player_action(
    game_state: Any,
    action: Optional[Dict[str, Any]],
    metrics: RunMetrics,
) -> None:
    """Process a player action and update game state.
    
    Args:
        game_state: Current game state
        action: Action dict from bot policy (or None for wait)
        metrics: RunMetrics to update
    """
    from game_states import GameStates
    
    collector = get_active_metrics_collector()
    
    # Default to wait
    if action is None:
        action = {'wait': True}
    
    # Handle wait action
    if action.get('wait'):
        game_state.current_state = GameStates.ENEMY_TURN
        return
    
    player = game_state.player
    game_map = game_state.game_map
    entities = game_state.entities
    message_log = game_state.message_log
    
    # Simple move action
    if 'move' in action:
        dx, dy = action['move']
        dest_x, dest_y = player.x + dx, player.y + dy
        
        # Check map bounds and blocking entities
        if (0 <= dest_x < game_map.width and 0 <= dest_y < game_map.height
            and not game_map.is_blocked(dest_x, dest_y)):
            blocking = next((e for e in entities if e.blocks and e.x == dest_x and e.y == dest_y), None)
            if blocking is None:
                player.x = dest_x
                player.y = dest_y
        
        game_state.current_state = GameStates.ENEMY_TURN
        return
    
    # Simple melee attack action
    if 'attack' in action:
        target = action['attack']
        player_fighter = player.get_component_optional(ComponentType.FIGHTER)
        target_fighter = target.get_component_optional(ComponentType.FIGHTER) if target else None
        
        if player_fighter and target_fighter and target_fighter.hp > 0:
            attack_results = player_fighter.attack_d20(target)
            for result in attack_results:
                msg = result.get("message")
                if msg:
                    message_log.add_message(msg)
                dead_entity = result.get("dead")
                if dead_entity:
                    # Record kill attribution
                    if collector:
                        collector.record_kill(player, dead_entity)
                    _handle_entity_death_simple(game_state, dead_entity, message_log)
        game_state.current_state = GameStates.ENEMY_TURN
        return
    
    # Fallback: wait
    game_state.current_state = GameStates.ENEMY_TURN


def _process_enemy_turn(game_state: Any, metrics: RunMetrics) -> None:
    """Process the enemy turn phase.
    
    Args:
        game_state: Current game state
        metrics: RunMetrics to update (kills_by_faction)
    """
    # Get all AI entities
    ai_entities = [
        e for e in game_state.entities
        if e != game_state.player
        and hasattr(e, 'ai') and e.ai is not None
        and hasattr(e, 'fighter') and e.fighter is not None
        and e.fighter.hp > 0
    ]
    
    # Process each AI entity's turn
    for entity in ai_entities:
        try:
            if entity.ai and callable(getattr(entity.ai, 'take_turn', None)):
                # Get state required for AI turn
                target = game_state.player
                fov_map = getattr(game_state, 'fov_map', None)
                game_map = game_state.game_map
                entities = game_state.entities
                
                # Process AI turn
                entity.ai.take_turn(target, fov_map, game_map, entities, game_state.message_log)
        except Exception as e:
            logger.debug(f"AI turn error for {entity.name}: {e}")
    
    # Return to player turn
    game_state.current_state = GameStates.PLAYERS_TURN


def _handle_entity_death_simple(game_state: Any, dead_entity: Any, message_log: Any) -> None:
    """Minimal death handling for harness to keep state consistent."""
    from death_functions import kill_player, kill_monster
    
    player = game_state.player
    if dead_entity == player:
        death_message, new_state = kill_player(player)
        message_log.add_message(death_message)
        game_state.current_state = new_state
        return
    
    game_map = game_state.game_map
    entities = game_state.entities
    death_message = kill_monster(dead_entity, game_map, entities)
    if death_message:
        message_log.add_message(death_message)


def _check_player_death(game_state: Any) -> bool:
    """Check if the player has died.
    
    Args:
        game_state: Current game state
        
    Returns:
        True if player is dead, False otherwise
    """
    player = game_state.player
    if player is None:
        return True
    
    if hasattr(player, 'fighter') and player.fighter is not None:
        return player.fighter.hp <= 0
    
    return False


def _count_dead_entities(game_state: Any, metrics: RunMetrics) -> None:
    """Count dead entities and update kill metrics.
    
    This is a simplified kill tracking for Phase 12B.
    
    TODO (Phase 12C): Wire into death events for accurate kill attribution.
    
    Args:
        game_state: Current game state
        metrics: RunMetrics to update
    """
    # For now, we just count player kills as a simple metric
    # More sophisticated kill tracking will come in Phase 12C
    pass


def run_scenario_once(
    scenario,
    bot_policy: BotPolicy,
    turn_limit: int,
) -> RunMetrics:
    """Run a scenario once and collect metrics.
    
    This function:
    1. Initializes a minimal game state for the scenario
    2. Runs the game loop until turn_limit or termination
    3. Collects and returns metrics
    
    Args:
        scenario: ScenarioDefinition from the registry
        bot_policy: BotPolicy for player control
        turn_limit: Maximum turns to run
        
    Returns:
        RunMetrics with collected data
    """
    logger.info(f"Starting scenario run: {scenario.scenario_id} (turn_limit={turn_limit})")
    
    # Initialize headless mode
    _initialize_headless_mode()
    
    # Initialize metrics
    metrics = RunMetrics(
        turns_taken=0,
        player_died=False,
        kills_by_faction=defaultdict(int),
        kills_by_source=defaultdict(int),
    )
    
    try:
        with scoped_metrics_collector(metrics):
            constants = get_constants()
            if scenario.depth is not None:
                constants["start_level"] = scenario.depth

            map_result = build_scenario_map(scenario)
            validate_scenario_instance(scenario, map_result.game_map, map_result.player, map_result.entities)

            game_state = _create_game_state_from_map(map_result, constants)

            # Main loop
            for turn in range(turn_limit):
                if _check_player_death(game_state):
                    metrics.player_died = True
                    logger.info(f"Scenario ended: player death at turn {turn + 1}")
                    break

                if game_state.current_state == GameStates.PLAYERS_TURN:
                    action = bot_policy.choose_action(game_state)
                    _process_player_action(game_state, action, metrics)

                elif game_state.current_state == GameStates.ENEMY_TURN:
                    _process_enemy_turn(game_state, metrics)
                    metrics.turns_taken += 1

                elif game_state.current_state == GameStates.PLAYER_DEAD:
                    metrics.player_died = True
                    logger.info(f"Scenario ended: player death at turn {metrics.turns_taken}")
                    break

                else:
                    game_state.current_state = GameStates.PLAYERS_TURN

            if metrics.turns_taken == 0:
                metrics.turns_taken = min(turn_limit, 1)

            _count_dead_entities(game_state, metrics)

    except (ScenarioBuildError, ScenarioInvariantError) as e:
        logger.error(f"Scenario setup failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Scenario run error: {e}", exc_info=True)
        if metrics.turns_taken == 0:
            metrics.turns_taken = 1
    
    # Convert defaultdict to regular dict for serialization
    metrics.kills_by_faction = dict(metrics.kills_by_faction)
    metrics.kills_by_source = dict(metrics.kills_by_source)
    
    logger.info(f"Scenario run complete: turns={metrics.turns_taken}, "
                f"player_died={metrics.player_died}")
    
    return metrics


def run_scenario_many(
    scenario,
    bot_policy: BotPolicy,
    runs: int,
    turn_limit: int,
) -> AggregatedMetrics:
    """Run a scenario multiple times and aggregate metrics.
    
    Args:
        scenario: ScenarioDefinition from the registry
        bot_policy: BotPolicy for player control
        runs: Number of times to run the scenario
        turn_limit: Maximum turns per run
        
    Returns:
        AggregatedMetrics with combined data from all runs
    """
    logger.info(f"Starting {runs} scenario runs: {scenario.scenario_id}")
    
    # Collect individual run results
    all_runs: List[RunMetrics] = []
    
    for run_num in range(1, runs + 1):
        logger.info(f"Run {run_num}/{runs}")
        
        # Reset any necessary state between runs
        _reset_global_services()
        
        # Run the scenario
        run_metrics = run_scenario_once(scenario, bot_policy, turn_limit)
        all_runs.append(run_metrics)
    
    # Aggregate results
    total_turns = sum(r.turns_taken for r in all_runs)
    player_deaths = sum(1 for r in all_runs if r.player_died)
    
    # Merge kills by faction/source
    merged_kills_by_faction: Dict[str, int] = defaultdict(int)
    merged_kills_by_source: Dict[str, int] = defaultdict(int)
    total_plague_infections = 0
    total_reanimations = 0
    total_surprise_attacks = 0
    total_bonus_attacks = 0
    
    for run in all_runs:
        for faction, count in run.kills_by_faction.items():
            merged_kills_by_faction[faction] += count
        for source, count in run.kills_by_source.items():
            merged_kills_by_source[source] += count
        total_plague_infections += run.plague_infections
        total_reanimations += run.reanimations
        total_surprise_attacks += run.surprise_attacks
        total_bonus_attacks += run.bonus_attacks_triggered
    
    aggregated = AggregatedMetrics(
        runs=runs,
        average_turns=total_turns / runs if runs > 0 else 0.0,
        player_deaths=player_deaths,
        total_kills_by_faction=dict(merged_kills_by_faction),
        total_kills_by_source=dict(merged_kills_by_source),
        total_plague_infections=total_plague_infections,
        total_reanimations=total_reanimations,
        total_surprise_attacks=total_surprise_attacks,
        total_bonus_attacks_triggered=total_bonus_attacks,
    )
    
    logger.info(f"Scenario runs complete: {runs} runs, "
                f"avg_turns={aggregated.average_turns:.1f}, "
                f"deaths={aggregated.player_deaths}")
    
    return aggregated


def _reset_global_services() -> None:
    """Reset global services between scenario runs.
    
    This ensures each run has a clean state, similar to what
    the soak harness does.
    """
    try:
        from instrumentation.run_metrics import reset_run_metrics_recorder
        reset_run_metrics_recorder()
    except ImportError:
        pass
    
    try:
        from services.telemetry_service import reset_telemetry_service
        reset_telemetry_service()
    except ImportError:
        pass
    
    try:
        from services.movement_service import reset_movement_service
        reset_movement_service()
    except ImportError:
        pass
    
    try:
        from services.pickup_service import reset_pickup_service
        reset_pickup_service()
    except ImportError:
        pass
    
    try:
        from services.floor_state_manager import reset_floor_state_manager
        reset_floor_state_manager()
    except ImportError:
        pass


# =============================================================================
# Expected invariants evaluation
# =============================================================================


@dataclass
class ExpectedCheckResult:
    passed: bool
    failures: List[str]


def evaluate_expected_invariants(
    scenario: Any,
    metrics: AggregatedMetrics,
) -> ExpectedCheckResult:
    """Evaluate scenario.expected constraints against aggregated metrics."""
    expected = getattr(scenario, "expected", {}) or {}
    failures: List[str] = []
    
    def _check_min(key: str, actual: int, minimum: int) -> None:
        if actual < minimum:
            failures.append(f"{key} >= {minimum} (value: {actual})")
    
    def _check_max(key: str, actual: int, maximum: int) -> None:
        if actual > maximum:
            failures.append(f"{key} <= {maximum} (value: {actual})")
    
    key = "min_player_kills"
    if key in expected:
        actual = metrics.total_kills_by_source.get("PLAYER", 0)
        _check_min(key, actual, expected[key])
    
    key = "max_player_deaths"
    if key in expected:
        _check_max(key, metrics.player_deaths, expected[key])
    
    key = "plague_infections_min"
    if key in expected:
        _check_min(key, metrics.total_plague_infections, expected[key])
    
    key = "reanimations_min"
    if key in expected:
        _check_min(key, metrics.total_reanimations, expected[key])
    
    key = "surprise_attacks_min"
    if key in expected:
        _check_min(key, metrics.total_surprise_attacks, expected[key])
    
    key = "bonus_attacks_min"
    if key in expected:
        _check_min(key, metrics.total_bonus_attacks_triggered, expected[key])
    
    return ExpectedCheckResult(passed=len(failures) == 0, failures=failures)


# =============================================================================
# Convenience exports
# =============================================================================

__all__ = [
    'RunMetrics',
    'AggregatedMetrics',
    'BotPolicy',
    'ObserveOnlyPolicy',
    'TacticalFighterPolicy',
    'make_bot_policy',
    'ExpectedCheckResult',
    'evaluate_expected_invariants',
    'run_scenario_once',
    'run_scenario_many',
]
