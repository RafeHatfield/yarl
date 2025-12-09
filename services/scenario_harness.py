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
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol

logger = logging.getLogger(__name__)


# =============================================================================
# RunMetrics: Per-run metrics tracking
# =============================================================================

@dataclass
class RunMetrics:
    """Metrics collected from a single scenario run.
    
    Attributes:
        turns_taken: Number of turns the scenario ran
        player_died: Whether the player died during the run
        kills_by_faction: Dict mapping faction name to kill count
            e.g., {"PLAYER": 3, "ORC_FACTION": 2}
    """
    turns_taken: int = 0
    player_died: bool = False
    kills_by_faction: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'turns_taken': self.turns_taken,
            'player_died': self.player_died,
            'kills_by_faction': dict(self.kills_by_faction),
        }


# =============================================================================
# AggregatedMetrics: Multi-run aggregation
# =============================================================================

@dataclass
class AggregatedMetrics:
    """Aggregated metrics from multiple scenario runs.
    
    Attributes:
        runs: Number of runs executed
        average_turns: Average number of turns across all runs
        player_deaths: Total number of player deaths
        total_kills_by_faction: Cumulative kills by faction across all runs
    """
    runs: int = 0
    average_turns: float = 0.0
    player_deaths: int = 0
    total_kills_by_faction: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'runs': self.runs,
            'average_turns': round(self.average_turns, 2),
            'player_deaths': self.player_deaths,
            'total_kills_by_faction': dict(self.total_kills_by_faction),
        }


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
    
    # TODO (Phase 12C): Add more policies
    # - "melee_brute": Aggressive melee combat
    # - "tactical_fighter": Smart combat with positioning
    # - "explorer": Prioritizes exploration over combat
    
    raise ValueError(f"Unknown bot policy: {name}")


# =============================================================================
# Scenario Runner
# =============================================================================

def _initialize_headless_mode() -> None:
    """Initialize headless mode for scenario runs.
    
    Sets environment variables to disable display output for automated
    scenario testing.
    """
    os.environ['SDL_VIDEODRIVER'] = 'dummy'


def _create_minimal_game_state(scenario) -> Dict[str, Any]:
    """Create a minimal game state for scenario execution.
    
    This initializes the game using existing infrastructure but bypasses
    menus and title screen to drop directly into gameplay.
    
    Args:
        scenario: ScenarioDefinition with scenario configuration
        
    Returns:
        Dict containing player, entities, game_map, message_log, game_state
    """
    from loader_functions.initialize_new_game import get_constants, get_game_variables
    from game_states import GameStates
    
    # Get game constants
    constants = get_constants()
    
    # Apply scenario depth override if specified
    if scenario.depth is not None:
        constants['start_level'] = scenario.depth
    
    # Initialize game variables
    player, entities, game_map, message_log, game_state = get_game_variables(constants)
    
    # Force PLAYERS_TURN state to start gameplay immediately
    game_state = GameStates.PLAYERS_TURN
    
    # Create a simple state object that mimics what play_game_with_engine expects
    class SimpleGameState:
        def __init__(self, player, entities, game_map, message_log, current_state, constants):
            self.player = player
            self.entities = entities
            self.game_map = game_map
            self.message_log = message_log
            self.current_state = current_state
            self.constants = constants
            self.fov_recompute = True
    
    return SimpleGameState(
        player=player,
        entities=entities,
        game_map=game_map,
        message_log=message_log,
        current_state=game_state,
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
    
    # If no action or wait action, just pass the turn
    if action is None:
        action = {'wait': True}
    
    # Handle wait action
    if action.get('wait'):
        # Waiting passes the turn to enemies
        game_state.current_state = GameStates.ENEMY_TURN
        return
    
    # TODO (Phase 12C): Handle other actions (move, attack, use item, etc.)
    # For now, treat any non-wait action as wait
    game_state.current_state = GameStates.ENEMY_TURN


def _process_enemy_turn(game_state: Any, metrics: RunMetrics) -> None:
    """Process the enemy turn phase.
    
    Args:
        game_state: Current game state
        metrics: RunMetrics to update (kills_by_faction)
    """
    from game_states import GameStates
    from components.component_registry import ComponentType
    
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
    )
    
    try:
        # Create game state
        game_state = _create_minimal_game_state(scenario)
        
        # Import game states
        from game_states import GameStates
        
        # Main loop
        for turn in range(turn_limit):
            # Check for termination conditions
            if _check_player_death(game_state):
                metrics.player_died = True
                logger.info(f"Scenario ended: player death at turn {turn + 1}")
                break
            
            # Handle current state
            if game_state.current_state == GameStates.PLAYERS_TURN:
                # Get player action from bot policy
                action = bot_policy.choose_action(game_state)
                _process_player_action(game_state, action, metrics)
                
            elif game_state.current_state == GameStates.ENEMY_TURN:
                # Process enemy turns
                _process_enemy_turn(game_state, metrics)
                
                # Increment turn counter after full turn cycle
                metrics.turns_taken += 1
                
            elif game_state.current_state == GameStates.PLAYER_DEAD:
                # Player died
                metrics.player_died = True
                logger.info(f"Scenario ended: player death at turn {metrics.turns_taken}")
                break
            
            else:
                # Other states (menus, etc.) - just advance to player turn
                game_state.current_state = GameStates.PLAYERS_TURN
        
        # Cap turns_taken to turn_limit
        if metrics.turns_taken == 0:
            metrics.turns_taken = min(turn_limit, 1)
        
        # Update kill counts
        _count_dead_entities(game_state, metrics)
        
    except Exception as e:
        logger.error(f"Scenario run error: {e}", exc_info=True)
        # Return partial metrics on error
        if metrics.turns_taken == 0:
            metrics.turns_taken = 1
    
    # Convert defaultdict to regular dict for serialization
    metrics.kills_by_faction = dict(metrics.kills_by_faction)
    
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
    
    # Merge kills by faction
    merged_kills: Dict[str, int] = defaultdict(int)
    for run in all_runs:
        for faction, count in run.kills_by_faction.items():
            merged_kills[faction] += count
    
    aggregated = AggregatedMetrics(
        runs=runs,
        average_turns=total_turns / runs if runs > 0 else 0.0,
        player_deaths=player_deaths,
        total_kills_by_faction=dict(merged_kills),
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
# Convenience exports
# =============================================================================

__all__ = [
    'RunMetrics',
    'AggregatedMetrics',
    'BotPolicy',
    'ObserveOnlyPolicy',
    'make_bot_policy',
    'run_scenario_once',
    'run_scenario_many',
]
