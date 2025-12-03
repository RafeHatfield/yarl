"""Bot decision-making brain for automated gameplay.

This module provides a minimal decision-making "BotBrain" used by bot input.
Phase 2.0 scope: EXPLORE + simple COMBAT + simple LOOT behavior.

Supports bot personas for different playstyles (balanced, cautious, aggressive, greedy, speedrunner).
"""

import logging
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from game_states import GameStates
from components.component_registry import ComponentType
from fov_functions import map_is_in_fov
from components.faction import are_factions_hostile

logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """Logging tier levels for BotBrain."""
    SUMMARY = "summary"  # Default: state transitions, lifecycle events
    DEBUG = "debug"       # Verbose: turn-by-turn details
    ERROR = "error"       # Only contract violations or impossible states


# Stuck detection threshold: number of consecutive combat decisions without progress
STUCK_THRESHOLD = 8

# Terminal exploration reasons - these stop reasons indicate the floor is as explored
# as it's going to get. When AutoExplore stops with one of these, the bot should not
# attempt to restart exploration. Used in _handle_explore(), _is_floor_complete(), 
# and for soak run termination.
TERMINAL_EXPLORE_REASONS = frozenset({
    "All areas explored",
    "Cannot reach unexplored areas",
})


# =============================================================================
# BOT PERSONAS — Configurable behavior profiles
# =============================================================================

@dataclass(frozen=True)
class BotPersonaConfig:
    """Configuration parameters for a bot persona.
    
    Each persona defines thresholds and weights that influence BotBrain decisions:
    - Combat behavior: engagement distance, retreat threshold
    - Loot behavior: pickup priority, deviation willingness
    - Exploration: stairs priority vs full exploration
    - Survival: potion use threshold
    
    Attributes:
        name: Human-readable persona name
        retreat_hp_threshold: HP fraction below which bot considers retreating (0.0-1.0)
        potion_hp_threshold: HP fraction below which bot drinks potions (0.0-1.0)
        combat_engagement_distance: Max Manhattan distance to engage enemies
        loot_priority: Weight for loot vs exploration (0=ignore loot, 1=normal, 2=greedy)
        prefer_stairs: If True, prioritize stairs over full exploration when safe
        avoid_combat: If True, avoid non-adjacent enemies when possible
    """
    name: str
    retreat_hp_threshold: float = 0.25  # Retreat when HP below this
    potion_hp_threshold: float = 0.40   # Drink potion when HP below this
    combat_engagement_distance: int = 8  # Max distance to chase enemies
    loot_priority: int = 1               # 0=skip, 1=normal, 2=greedy
    prefer_stairs: bool = False          # True = prioritize stairs over exploration
    avoid_combat: bool = False           # True = avoid non-adjacent enemies


# Pre-defined personas
PERSONAS: Dict[str, BotPersonaConfig] = {
    "balanced": BotPersonaConfig(
        name="balanced",
        retreat_hp_threshold=0.25,
        potion_hp_threshold=0.40,
        combat_engagement_distance=8,
        loot_priority=1,
        prefer_stairs=False,
        avoid_combat=False,
    ),
    "cautious": BotPersonaConfig(
        name="cautious",
        retreat_hp_threshold=0.40,   # Retreat earlier
        potion_hp_threshold=0.50,    # Drink potions earlier
        combat_engagement_distance=5, # Don't chase far
        loot_priority=1,
        prefer_stairs=False,
        avoid_combat=True,           # Avoid non-adjacent enemies
    ),
    "aggressive": BotPersonaConfig(
        name="aggressive",
        retreat_hp_threshold=0.10,   # Fight to the death
        potion_hp_threshold=0.25,    # Only drink when critical
        combat_engagement_distance=12, # Chase enemies further
        loot_priority=0,             # Ignore loot during combat
        prefer_stairs=False,
        avoid_combat=False,
    ),
    "greedy": BotPersonaConfig(
        name="greedy",
        retreat_hp_threshold=0.25,
        potion_hp_threshold=0.40,
        combat_engagement_distance=6,
        loot_priority=2,             # Prioritize loot heavily
        prefer_stairs=False,
        avoid_combat=False,
    ),
    "speedrunner": BotPersonaConfig(
        name="speedrunner",
        retreat_hp_threshold=0.30,
        potion_hp_threshold=0.40,
        combat_engagement_distance=4, # Minimal engagement
        loot_priority=0,              # Skip loot
        prefer_stairs=True,           # Rush to stairs
        avoid_combat=True,            # Avoid fights
    ),
}


def get_persona(name: str) -> BotPersonaConfig:
    """Get a persona config by name.
    
    Args:
        name: Persona name (balanced, cautious, aggressive, greedy, speedrunner)
        
    Returns:
        BotPersonaConfig for the requested persona
        
    Raises:
        ValueError: If persona name is not recognized
    """
    if name not in PERSONAS:
        valid = ", ".join(PERSONAS.keys())
        raise ValueError(f"Unknown persona '{name}'. Valid options: {valid}")
    return PERSONAS[name]


def list_personas() -> List[str]:
    """List available persona names.
    
    Returns:
        List of valid persona name strings
    """
    return list(PERSONAS.keys())



class BotState(Enum):
    """Bot decision-making states."""
    EXPLORE = "explore"
    COMBAT = "combat"
    LOOT = "loot"


class BotBrain:
    """Simple decision-making brain for bot input.
    
    Implements a state machine with EXPLORE, COMBAT, and LOOT states.
    Makes decisions based on game state without knowing about soak mode.
    
    Supports configurable personas that modify decision thresholds.
    
    Attributes:
        state: Current bot decision state
        current_target: Currently targeted enemy entity (if in COMBAT)
        persona: BotPersonaConfig defining behavior parameters
        _stuck_counter: Counter for detecting stuck behavior
        _last_player_pos: Last known player position (x, y)
        _last_target_pos: Last known target position (x, y)
        _recent_positions: Deque of recent player positions for oscillation detection
        debug: Enable debug logging
    """
    
    def __init__(
        self, 
        debug: bool = False, 
        log_level: LogLevel = LogLevel.SUMMARY,
        persona: Optional[str] = None
    ) -> None:
        """Initialize BotBrain with default EXPLORE state.
        
        Args:
            debug: Enable debug logging for troubleshooting (deprecated, use log_level)
            log_level: Logging tier level (SUMMARY, DEBUG, or ERROR)
            persona: Persona name string (balanced, cautious, aggressive, greedy, speedrunner).
                     Defaults to "balanced" if not specified.
        """
        self.state = BotState.EXPLORE
        self.current_target = None
        self._stuck_counter = 0
        self._last_player_pos = None
        self._last_target_pos = None
        self._recent_positions = deque(maxlen=6)  # Track last 6 positions for oscillation detection
        self._just_dropped_due_to_stuck = False  # Flag to prevent immediate re-entry
        self._stuck_dropped_target = None  # Target we dropped due to being stuck
        self.debug = debug  # Deprecated, kept for backward compatibility
        self.log_level = LogLevel.DEBUG if debug else log_level  # Use debug flag to set DEBUG level if True
        
        # Load persona config (default: balanced)
        persona_name = persona or "balanced"
        self.persona = get_persona(persona_name)
        self._log_summary(f"Initialized with persona: {self.persona.name}")
        
        # COMBAT no-op fail-safe: track consecutive no-op actions in COMBAT
        self._combat_noop_counter = 0
        self._combat_noop_threshold = 10  # Drop to EXPLORE after 10 consecutive no-op actions
        self._just_dropped_due_to_noop = False  # Flag to prevent immediate re-entry after no-op fail-safe
        self._noop_dropped_target = None  # Target we dropped due to no-op fail-safe
        # Track state transitions for summary logging
        self._last_state = BotState.EXPLORE
        # Equipment re-evaluation: periodically check for better gear
        self._turns_since_last_reequip_check = 0
        self._reequip_check_interval = 10  # Re-evaluate equipment every 10 turns
        # Stuck flag auto-clear: prevent infinite loops when stuck flag blocks combat
        self._stuck_skip_counter = 0
        # Loot oscillation prevention: skip LOOT state temporarily after oscillation
        self._skip_loot_until_turn = 0  # Turn number when we can re-enter LOOT
        self._turn_counter = 0  # Track turn count for loot skip timing
        # Disable opportunistic loot after LOOT oscillation to prevent ping-pong between items
        self._disable_opportunistic_loot = False
        # Movement blocked failure counter: abort run if AutoExplore repeatedly fails with "Movement blocked"
        self._movement_blocked_count = 0
        # Stairs descent state: tracks path to stairs when floor is complete
        self._stairs_path: Optional[List[Tuple[int, int]]] = None
    
    def decide_action(self, game_state: Any) -> Dict[str, Any]:
        """Decide the next action based on current game state.
        
        Args:
            game_state: Game state object with player, entities, map, etc.
            
        Returns:
            ActionDict: Dictionary with action keys (move, pickup, start_auto_explore, etc.)
                       or empty dict if no action should be taken.
        """
        # Only act during PLAYERS_TURN
        if not game_state or not hasattr(game_state, 'current_state'):
            return {}
        
        if game_state.current_state != GameStates.PLAYERS_TURN:
            return {}
        
        try:
            # Track turn count for loot skip timing
            self._turn_counter += 1
            
            # Get player entity
            player = self._get_player(game_state)
            if not player:
                return {}
            
            # Get entities list (needed for multiple checks)
            entities = getattr(game_state, 'entities', [])
            
            # Get visible enemies
            visible_enemies = self._get_visible_enemies(game_state, player)
            
            # POTION-DRINKING LOGIC: Check if bot should drink a potion (soak testing survivability)
            # This takes priority over other actions when conditions are met:
            # - Low HP (≤40%)
            # - No visible enemies (safe to drink)
            # - Has potions in inventory
            if self._should_drink_potion(player, visible_enemies):
                potion_index = self._choose_potion_to_drink(player)
                if potion_index is not None:
                    self._debug(f"Drinking potion at inventory index {potion_index}")
                    return {"inventory_index": potion_index}
            
            # MOVEMENT BLOCKED DETECTION: If AutoExplore keeps failing with "Movement blocked", abort run
            # This prevents infinite loops where AutoExplore recalculates the same blocked path
            auto_explore = player.get_component_optional(ComponentType.AUTO_EXPLORE)
            if auto_explore and not auto_explore.is_active() and auto_explore.stop_reason:
                if "Movement blocked" in auto_explore.stop_reason:
                    self._movement_blocked_count += 1
                    if self._movement_blocked_count >= 3:
                        self._log_summary(f"STUCK: Movement blocked {self._movement_blocked_count} times, aborting run")
                        return {"bot_abort_run": True}
                else:
                    # AutoExplore stopped for different reason - reset counter
                    self._movement_blocked_count = 0
            
            # FLOOR COMPLETION / STAIRS DESCENT: Check for terminal exploration states
            # 
            # When exploration is terminal-complete (floor fully explored or unreachable areas):
            # - If safe (no enemies): walk to stairs and descend
            # - If enemies visible: clear stairs path, fall back to combat handling
            #
            # This implements safe stair descent behavior where BotBrain temporarily
            # owns movement (like a mini-state) while walking to stairs. AutoExplore
            # is NOT restarted during this phase.
            is_floor_complete = self._is_floor_complete(player)
            if is_floor_complete or self._stairs_path:
                # Floor is terminal-complete OR we're already walking to stairs
                game_map = getattr(game_state, 'game_map', None)
                
                logger.warning(
                    f"BotBrain: Entering floor complete handling - "
                    f"is_floor_complete={is_floor_complete}, "
                    f"stairs_path={'exists' if self._stairs_path else 'None'}, "
                    f"visible_enemies={len(visible_enemies)}, "
                    f"game_map={'exists' if game_map else 'None'}"
                )
                
                try:
                    floor_action = self._handle_floor_complete(player, entities, game_map, visible_enemies)
                    logger.warning(f"BotBrain: floor_action result = {floor_action}")
                except Exception as e:
                    # Catch any unexpected errors in floor complete handling
                    self._log_error(f"Exception in _handle_floor_complete: {e}")
                    floor_action = {"bot_abort_run": True}
                
                # If _handle_floor_complete returned an action, use it
                if floor_action:
                    return floor_action
                
                # If returned empty dict, it means enemies appeared during stair walking
                # Fall through to combat handling ONLY if there are visible enemies
                # Otherwise, something went wrong - abort to avoid infinite loop
                if not visible_enemies:
                    self._log_error(
                        f"Floor complete but _handle_floor_complete returned empty with no enemies! "
                        f"Aborting to prevent loop. stairs_path={self._stairs_path}"
                    )
                    return {"bot_abort_run": True}
            
            # EQUIPMENT RE-EVALUATION: Periodically check for better gear (bot survivability)
            # This runs every N turns when in EXPLORE state and safe (no enemies)
            # Ensures the bot equips the best available gear even if it picked up items earlier
            self._turns_since_last_reequip_check += 1
            if (self._turns_since_last_reequip_check >= self._reequip_check_interval and
                not visible_enemies):
                # Safe to re-evaluate equipment
                self._turns_since_last_reequip_check = 0
                self._debug(f"Periodic equipment re-evaluation")
                from io_layer.bot_equipment import auto_equip_better_items
                auto_equip_better_items(player, is_bot_mode=True)
            
            # CRITICAL INVARIANT: Adjacent enemies always override "don't re-target" protections
            # If any hostile enemy is adjacent (Manhattan distance 1), we MUST attack it,
            # regardless of any recent stuck/abort flags. This prevents the bot from ignoring
            # adjacent enemies that are actively attacking.
            adjacent_enemy = None
            for enemy in visible_enemies:
                if self._is_adjacent(player, enemy):
                    adjacent_enemy = enemy
                    break
            
            if adjacent_enemy:
                # Adjacency overrides all drop flags - we must fight when toe-to-toe
                self._debug(f"Adjacent enemy detected at ({adjacent_enemy.x}, {adjacent_enemy.y}), forcing COMBAT (overriding drop flags)")
                self.state = BotState.COMBAT
                self.current_target = adjacent_enemy
                # Clear all drop flags - adjacency means we must engage
                self._just_dropped_due_to_stuck = False
                self._just_dropped_due_to_noop = False
                self._stuck_dropped_target = None
                self._noop_dropped_target = None
                # Reset stuck state when engaging adjacent enemy
                self._reset_stuck_state()
                # Return attack action immediately - don't proceed to state transition logic
                return self._handle_combat(player, visible_enemies, game_state)
            
            # Check if standing on loot
            standing_on_loot = self._standing_on_loot(player, entities)
            
            # If in COMBAT, validate current target first
            if self.state == BotState.COMBAT:
                if not self._is_valid_target(self.current_target, game_state, player):
                    self._debug(f"Dropping invalid target, returning to EXPLORE")
                    self.current_target = None
                    self.state = BotState.EXPLORE
                    self._reset_stuck_state()
            
            # State transitions (for non-adjacent enemies)
            if visible_enemies:
                # Check if any enemy is within combat engagement distance (persona-configurable)
                nearest_enemy = self._find_nearest_enemy(player, visible_enemies)
                if nearest_enemy:
                    manhattan_dist = abs(player.x - nearest_enemy.x) + abs(player.y - nearest_enemy.y)
                    
                    # Persona: avoid_combat skips non-adjacent enemies entirely
                    if self.persona.avoid_combat and manhattan_dist > 1:
                        self._debug(f"Persona '{self.persona.name}' avoiding combat with enemy at distance {manhattan_dist}")
                        # Fall through to EXPLORE handling below
                        nearest_enemy = None
                    elif manhattan_dist <= self.persona.combat_engagement_distance:
                        # Don't re-enter COMBAT with same target if we just dropped due to stuck or no-op fail-safe
                        if (self._just_dropped_due_to_stuck and self._stuck_dropped_target == nearest_enemy) or \
                           (self._just_dropped_due_to_noop and self._noop_dropped_target == nearest_enemy):
                            if self._just_dropped_due_to_stuck:
                                self._debug(f"Skipping re-entry to COMBAT with same target after stuck")
                                # Keep flag set to prevent immediate re-entry
                            if self._just_dropped_due_to_noop:
                                self._debug(f"Skipping re-entry to COMBAT with same target after no-op fail-safe")
                                # Keep flag set to prevent immediate re-entry
                            # Stay in EXPLORE, don't re-enter COMBAT
                            # Increment skip counter - after several skips, clear flags to allow re-engagement
                            self._stuck_skip_counter += 1
                            if self._stuck_skip_counter >= 5:
                                self._debug("Clearing stuck flags after 5 skip cycles")
                                self._just_dropped_due_to_stuck = False
                                self._just_dropped_due_to_noop = False
                                self._stuck_dropped_target = None
                                self._noop_dropped_target = None
                                self._stuck_skip_counter = 0
                        else:
                            # Different target or flags not set - can enter COMBAT
                            if self.state != BotState.COMBAT or self.current_target != nearest_enemy:
                                self._debug(f"Entering COMBAT with enemy at ({nearest_enemy.x}, {nearest_enemy.y}), distance {manhattan_dist}")
                                # Reset stuck state when switching targets
                                if self.current_target != nearest_enemy:
                                    self._reset_stuck_state()
                            self._log_state_transition(BotState.COMBAT)
                            self.state = BotState.COMBAT
                            self.current_target = nearest_enemy
                            # Clear flags when successfully entering COMBAT with a different target
                            self._just_dropped_due_to_stuck = False
                            self._just_dropped_due_to_noop = False
                            self._stuck_dropped_target = None
                            self._noop_dropped_target = None
                            self._stuck_skip_counter = 0  # Reset counter when entering combat
                    else:
                        if self.state == BotState.COMBAT:
                            self._debug(f"Enemy too far (distance {manhattan_dist}), leaving COMBAT")
                        self._log_state_transition(BotState.EXPLORE)
                        self.current_target = None
                        self.state = BotState.EXPLORE
                        self._reset_stuck_state()
                else:
                    if self.state == BotState.COMBAT:
                        self._debug("No nearest enemy found, leaving COMBAT")
                    self._log_state_transition(BotState.EXPLORE)
                    self.current_target = None
                    self.state = BotState.EXPLORE
                    self._reset_stuck_state()
            elif standing_on_loot:
                # Persona: loot_priority=0 skips loot entirely
                if self.persona.loot_priority == 0:
                    self._debug(f"Persona '{self.persona.name}' skipping loot (loot_priority=0)")
                    # Stay in EXPLORE, don't pick up loot
                    self._log_state_transition(BotState.EXPLORE)
                    self.current_target = None
                    self.state = BotState.EXPLORE
                # Check if we should skip LOOT state (oscillation prevention)
                elif self._turn_counter < self._skip_loot_until_turn:
                    # Skip LOOT for now - stay in EXPLORE to break oscillation
                    self._debug(f"Skipping LOOT state until turn {self._skip_loot_until_turn} (oscillation prevention)")
                    # Re-enable opportunistic loot after cooldown expires
                    auto_explore = player.get_component_optional(ComponentType.AUTO_EXPLORE)
                    if auto_explore and auto_explore.disable_opportunistic_loot and self._turn_counter >= self._skip_loot_until_turn - 1:
                        auto_explore.disable_opportunistic_loot = False
                        self._debug("Re-enabled opportunistic loot (cooldown ending)")
                else:
                    if self.state != BotState.LOOT:
                        self._debug("Entering LOOT state")
                        self._log_state_transition(BotState.LOOT)
                    self.state = BotState.LOOT
                    # Clear combat target when looting
                    if self.current_target:
                        self.current_target = None
                        self._reset_stuck_state()
                    # Re-enable opportunistic loot when successfully entering LOOT
                    # (oscillation has been avoided)
                    auto_explore = player.get_component_optional(ComponentType.AUTO_EXPLORE)
                    if auto_explore and auto_explore.disable_opportunistic_loot:
                        auto_explore.disable_opportunistic_loot = False
                        self._debug("Re-enabled opportunistic loot")
            else:
                if self.state == BotState.COMBAT:
                    self._debug("No enemies visible, leaving COMBAT")
                    # Only reset stuck state when transitioning FROM COMBAT to EXPLORE
                    self._reset_stuck_state()
                self._log_state_transition(BotState.EXPLORE)
                self.current_target = None
                self.state = BotState.EXPLORE
            
            # Actions based on state
            action = {}
            if self.state == BotState.EXPLORE:
                # FAIL-SAFE: If in EXPLORE with visible enemies but stuck flags prevent combat,
                # and we keep getting stuck in AutoExplore restart loops, just wait
                # This prevents infinite loops when bot can't engage enemy and can't explore
                if visible_enemies and (self._just_dropped_due_to_stuck or self._just_dropped_due_to_noop):
                    # Check if we're in a restart loop (AutoExplore keeps failing immediately)
                    auto_explore = player.get_component_optional(ComponentType.AUTO_EXPLORE)
                    if auto_explore and not auto_explore.is_active() and auto_explore.stop_reason:
                        # AutoExplore is stopped - if it's "Cannot reach", we're likely stuck
                        if "Cannot reach" in auto_explore.stop_reason:
                            self._debug("FAIL-SAFE: Stuck in EXPLORE with enemy visible and AutoExplore failing, waiting")
                            action = {"wait": True}
                            # This will be handled below, don't return yet
                
                # Normal EXPLORE path - start autoexplore once, then let it run
                if not action:  # Only if we didn't set wait action above
                    action = self._handle_explore(player, game_state)
            elif self.state == BotState.COMBAT:
                action = self._handle_combat(player, visible_enemies, game_state)
            elif self.state == BotState.LOOT:
                action = self._handle_loot()
            else:
                action = {}
            
            # Track player position for oscillation detection (COMBAT only)
            current_player_pos = (player.x, player.y)
            # Only append if position changed (avoid duplicates from multiple calls per turn)
            if not self._recent_positions or self._recent_positions[-1] != current_player_pos:
                self._recent_positions.append(current_player_pos)
            
            # Check for oscillation pattern (A ↔ B ↔ A ↔ B) - COMBAT only
            if self._is_oscillating():
                oscillating_positions = list(self._recent_positions)[-4:] if len(self._recent_positions) >= 4 else list(self._recent_positions)
                logger.warning(
                    f"🔍 DIAGNOSTIC: Oscillation detected! state={self.state.name}, "
                    f"positions={oscillating_positions}, "
                    f"autoexplore_active={self._is_autoexplore_active(game_state)}"
                )
                if self.state == BotState.COMBAT:
                    # COMBAT oscillation: drop to EXPLORE
                    self._debug(f"Oscillation detected, resetting to EXPLORE")
                    self._reset_stuck_state()
                    self._recent_positions.clear()
                    old_target = self.current_target
                    self.current_target = None
                    self.state = BotState.EXPLORE
                    # Set flag to prevent immediate re-entry
                    self._just_dropped_due_to_stuck = True
                    self._stuck_dropped_target = old_target
                    # Return explore action instead of combat action
                    return self._handle_explore(player, game_state)
                elif self.state == BotState.EXPLORE or self.state == BotState.LOOT:
                    # EXPLORE/LOOT oscillation: Break out of the loop
                    self._debug(f"Oscillation detected in {self.state.name}, forcing EXPLORE and skipping LOOT for 5 turns")
                    self._recent_positions.clear()
                    # Reset stuck skip counter to give combat another chance if enemy appears
                    self._stuck_skip_counter = 0
                    # Force EXPLORE state to break out of problematic LOOT loops
                    if self.state == BotState.LOOT:
                        self.state = BotState.EXPLORE
                        self._log_state_transition(BotState.EXPLORE)
                    # Skip LOOT state for 5 turns to break oscillation
                    self._skip_loot_until_turn = self._turn_counter + 5
                    # CRITICAL: Disable opportunistic loot to prevent AutoExplore from targeting nearby items
                    # Set flag on AutoExplore component if it exists
                    auto_explore = player.get_component_optional(ComponentType.AUTO_EXPLORE)
                    if auto_explore:
                        auto_explore.disable_opportunistic_loot = True
                        self._debug("Disabled opportunistic loot on AutoExplore to prevent item ping-pong")
                    # Return explore action immediately to break the cycle
                    return self._handle_explore(player, game_state)
            
            # If in COMBAT, update stuck detection with action
            if self.state == BotState.COMBAT and self.current_target:
                self._update_stuck_detection(player, self.current_target, action)
                
                # COMBAT no-op fail-safe: detect repeated no-op actions
                if self._is_noop_action(action):
                    self._combat_noop_counter += 1
                    if self._combat_noop_counter >= self._combat_noop_threshold:
                        self._debug(
                            f"COMBAT fail-safe triggered: {self._combat_noop_counter} consecutive no-op actions. "
                            "Dropping to EXPLORE."
                        )
                        self._reset_stuck_state()
                        old_target = self.current_target
                        self.current_target = None
                        self.state = BotState.EXPLORE
                        self._combat_noop_counter = 0
                        # Set flag to prevent immediate re-entry with same target
                        self._just_dropped_due_to_noop = True
                        self._noop_dropped_target = old_target
                        # Force an EXPLORE decision NOW instead of returning the no-op
                        explore_action = self._handle_explore(player, game_state)
                        self._debug(f"COMBAT fail-safe choose explore_action={explore_action}")
                        return explore_action
                else:
                    # Reset counter when non-no-op action is produced
                    self._combat_noop_counter = 0
                
                # Check if stuck after updating detection
                if self._is_stuck_on_target():
                    self._debug(f"Stuck on target (no progress), dropping to EXPLORE")
                    old_target = self.current_target
                    self.current_target = None
                    self.state = BotState.EXPLORE
                    self._reset_stuck_state()
                    # Set flag AFTER reset to prevent immediate re-entry with same target
                    self._just_dropped_due_to_stuck = True
                    # Store the target we dropped so we can check if we're trying to re-enter with it
                    self._stuck_dropped_target = old_target
                    # Return explore action instead of combat action
                    return self._handle_explore(player, game_state)
            else:
                # Reset no-op counter when not in COMBAT
                self._combat_noop_counter = 0
            
            # Log structured debug info after decision is made
            self._log_decision_debug(player, visible_enemies, action)
            
            # SAFETY: Ensure we never return conflicting actions in the same tick
            # This enforces the "one action per tick" rule
            if isinstance(action, dict):
                # Check for conflicting action types
                has_autoexplore = 'start_auto_explore' in action
                has_movement = 'move' in action
                has_attack = any(k in action for k in ['attack', 'melee_attack'])
                
                if has_autoexplore and (has_movement or has_attack):
                    # Conflict detected - prioritize movement/attack over autoexplore start
                    logger.error(
                        f"⚠️ BotBrain CONFLICT: Tried to return both start_auto_explore and movement/attack! "
                        f"action={action}, removing start_auto_explore"
                    )
                    action = {k: v for k, v in action.items() if k != 'start_auto_explore'}
            
            return action
        except (AttributeError, TypeError) as e:
            # Log at WARNING level so we can see what's happening
            import traceback
            logger.warning(
                f"⚠️ BotBrain decide_action caught exception: {e}\n"
                f"Traceback: {traceback.format_exc()}"
            )
            
            # If game state is in PLAYERS_TURN, check if floor is complete
            # If floor is complete, abort instead of restarting explore (prevents infinite loop)
            if game_state.current_state == GameStates.PLAYERS_TURN:
                # Try to check floor complete status
                try:
                    player = getattr(game_state, 'player', None)
                    if player and self._is_floor_complete(player):
                        logger.warning("BotBrain: Exception during floor complete - aborting run")
                        return {"bot_abort_run": True}
                except Exception:
                    pass  # If we can't check, fall through to default
                
                # Default: restart explore (but this should rarely happen now)
                self.state = BotState.EXPLORE
                return {"start_auto_explore": True}
            
            return {}
    
    def _get_player(self, game_state: Any) -> Optional[Any]:
        """Get the player entity from game state.
        
        Args:
            game_state: Game state object
            
        Returns:
            Player entity or None if not found
        """
        return getattr(game_state, 'player', None)
    
    def _get_visible_enemies(self, game_state: Any, player: Any) -> List[Any]:
        """Get all visible hostile enemies in FOV.
        
        Args:
            game_state: Game state object
            player: Player entity
            
        Returns:
            List of hostile entities visible in FOV
        """
        enemies = []
        
        if not hasattr(game_state, 'entities') or not hasattr(game_state, 'fov_map'):
            return enemies
        
        entities = getattr(game_state, 'entities', [])
        fov_map = game_state.fov_map
        
        if not fov_map:
            return enemies
        
        # Safely convert entities to iterable list
        try:
            entities_iter = list(entities)
        except TypeError:
            # entities is not iterable (e.g. bare Mock) - treat as empty
            return enemies
        
        player_faction = getattr(player, 'faction', None)
        
        for entity in entities_iter:
            # Skip self
            if entity == player:
                continue
            
            # Must have AI component (is a monster)
            # Safely check for components.has() - some mocks may not have this
            if hasattr(entity, 'components') and hasattr(entity.components, 'has'):
                if not entity.components.has(ComponentType.AI):
                    continue
            else:
                # No components attribute or no has method - skip
                continue
            
            # Must have fighter component and be alive
            get_component_optional = getattr(entity, 'get_component_optional', None)
            if not callable(get_component_optional):
                # No get_component_optional method - skip
                continue
            
            fighter = get_component_optional(ComponentType.FIGHTER)
            if not fighter or fighter.hp <= 0:
                continue
            
            # Must be in FOV
            if not map_is_in_fov(fov_map, entity.x, entity.y):
                continue
            
            # Check if hostile based on factions
            entity_faction = getattr(entity, 'faction', None)
            if player_faction and entity_faction:
                is_hostile = are_factions_hostile(player_faction, entity_faction)
            else:
                # No faction info - assume hostile if they have fighter and AI
                is_hostile = True
            
            if is_hostile:
                enemies.append(entity)
        
        return enemies
    
    def _find_nearest_enemy(self, player: Any, enemies: List[Any]) -> Optional[Any]:
        """Find the nearest enemy to the player.
        
        Args:
            player: Player entity
            enemies: List of enemy entities
            
        Returns:
            Nearest enemy entity or None if list is empty
        """
        if not enemies:
            return None
        
        nearest = None
        min_distance = float('inf')
        
        for enemy in enemies:
            # Use Manhattan distance
            distance = abs(player.x - enemy.x) + abs(player.y - enemy.y)
            if distance < min_distance:
                min_distance = distance
                nearest = enemy
        
        return nearest
    
    def _is_adjacent(self, a: Any, b: Any) -> bool:
        """Check if two entities are adjacent (Manhattan distance == 1).
        
        Args:
            a: First entity
            b: Second entity
            
        Returns:
            True if entities are adjacent
        """
        dx = abs(a.x - b.x)
        dy = abs(a.y - b.y)
        return dx + dy == 1
    
    def _standing_on_loot(self, player: Any, entities: List[Any]) -> bool:
        """Check if player is standing on a lootable item.
        
        Args:
            player: Player entity
            entities: List of all entities
            
        Returns:
            True if player is standing on an item
        """
        # Safely convert entities to iterable list
        try:
            entities_iter = list(entities)
        except TypeError:
            # entities is not iterable (e.g. bare Mock) - treat as empty
            return False
        
        for entity in entities_iter:
            # Safely check for components.has() - some mocks may not have this
            if hasattr(entity, 'components') and hasattr(entity.components, 'has'):
                if (entity.x == player.x and entity.y == player.y and
                    entity.components.has(ComponentType.ITEM)):
                    return True
        return False
    
    def _build_move_action(self, dx: int, dy: int) -> Dict[str, Any]:
        """Build a movement action dictionary matching keyboard input format.
        
        Args:
            dx: X delta (-1, 0, or 1)
            dy: Y delta (-1, 0, or 1)
            
        Returns:
            ActionDict with 'move' key
        """
        return {"move": (dx, dy)}
    
    def _is_autoexplore_active(self, game_state: Any) -> bool:
        """Check if autoexplore is currently active.
        
        Uses the same contract as manual autoexplore - checks the AutoExplore
        component's is_active() method.
        
        Args:
            game_state: Game state object with player entity
            
        Returns:
            True if autoexplore is active, False otherwise
        """
        player = self._get_player(game_state)
        if not player:
            return False
        
        get_component_optional = getattr(player, 'get_component_optional', None)
        if not callable(get_component_optional):
            return False
        
        auto_explore = get_component_optional(ComponentType.AUTO_EXPLORE)
        if not auto_explore:
            return False
        
        if not callable(getattr(auto_explore, 'is_active', None)):
            return False
        
        return auto_explore.is_active()
    
    def _handle_explore(self, player: Any, game_state: Any) -> Dict[str, Any]:
        """Handle EXPLORE state - start auto-explore once if not active, then let it run.
        
        This method respects the autoexplore contract:
        - If autoexplore is active: return empty dict (ActionProcessor handles movement)
        - If autoexplore is not active: check stop_reason and decide whether to restart
        - No cache - always query AutoExplore component directly
        
        CRITICAL: This should ONLY be called when BotBrain.state == EXPLORE.
        If there are visible enemies, state machine should be in COMBAT, not EXPLORE.
        
        Args:
            player: Player entity
            game_state: Game state object
            
        Returns:
            ActionDict with start_auto_explore or empty dict
        """
        # SAFETY: This should only be called in EXPLORE state
        if self.state != BotState.EXPLORE:
            logger.error(
                f"⚠️ BotBrain._handle_explore called in wrong state! "
                f"state={self.state.name}, expected=EXPLORE"
            )
            return {}
        
        # Get AutoExplore component - single source of truth
        auto_explore = None
        if hasattr(player, 'get_component_optional'):
            auto_explore = player.get_component_optional(ComponentType.AUTO_EXPLORE)
        
        # Check if AutoExplore is currently active
        is_active = auto_explore and auto_explore.is_active() if auto_explore else False
        
        if is_active:
            # AutoExplore is active - return empty dict, let it drive movement
            return {}
        
        # AutoExplore is not active - check stop_reason before deciding to restart
        stop_reason = auto_explore.stop_reason if auto_explore else None
        
        # Do NOT restart if:
        # 1. "Cancelled" - someone explicitly stopped it, respect that
        # 2. "Monster spotted" - should have transitioned to COMBAT, not here
        # 3. Terminal floor completion reasons - floor is done, don't loop forever
        if stop_reason == "Cancelled":
            self._debug(f"BotBrain: AutoExplore cancelled, not restarting")
            return {}
        
        if stop_reason and "Monster spotted" in stop_reason:
            logger.warning(
                f"⚠️ BotBrain: AutoExplore stopped with 'Monster spotted' but still in EXPLORE state! "
                f"This suggests state transition to COMBAT didn't happen. Returning empty."
            )
            return {}
        
        # Terminal floor completion reasons - floor is as explored as it's going to get
        # Don't restart autoexplore; let the bot wait, descend stairs, or abort
        # Use str() to handle any numpy string types
        stop_reason_str = str(stop_reason) if stop_reason else None
        if stop_reason_str in TERMINAL_EXPLORE_REASONS:
            self._debug(f"BotBrain: Floor exploration complete ('{stop_reason}'), not restarting AutoExplore")
            return {}
        
        # Don't restart AutoExplore if we're walking to stairs
        if self._stairs_path:
            self._debug(f"BotBrain: Walking to stairs, not restarting AutoExplore")
            return {}
        
        # SAFETY: Double-check floor complete status before restarting
        # This catches cases where the earlier floor complete check was bypassed
        if self._is_floor_complete(player):
            self._log_error(
                f"BotBrain: Floor complete but reached start_auto_explore code! "
                f"stop_reason='{stop_reason}', type={type(stop_reason)}. Aborting instead."
            )
            return {"bot_abort_run": True}
        
        # For other stop reasons (or first time), start autoexplore
        player_pos = (player.x, player.y)
        self._debug(f"BotBrain: Starting AutoExplore at {player_pos}, stop_reason='{stop_reason}'")
        return {"start_auto_explore": True}
    
    def _handle_combat(self, player: Any, enemies: List[Any], game_state: Any) -> Dict[str, Any]:
        """Handle COMBAT state - attack adjacent enemies or move toward nearest.
        
        Includes stuck detection to prevent infinite loops.
        
        Args:
            player: Player entity
            enemies: List of visible enemy entities
            game_state: Game state object for validation
            
        Returns:
            ActionDict with move or attack action, or EXPLORE action if stuck
        """
        if not enemies:
            return {}
        
        # Use current_target if available and valid, otherwise find nearest
        target = self.current_target
        if not target or not self._is_valid_target(target, game_state, player):
            target = self._find_nearest_enemy(player, enemies)
            if target:
                self.current_target = target
        
        if not target:
            self._debug("No valid combat target, dropping to EXPLORE")
            self.current_target = None
            self.state = BotState.EXPLORE
            self._reset_stuck_state()
            return self._handle_explore(player, game_state)
        
        # Check for adjacent enemy
        adjacent_enemy = None
        if self._is_adjacent(player, target):
            adjacent_enemy = target
        
        if adjacent_enemy:
            # Attack adjacent enemy - movement into enemy triggers attack
            dx = 0
            dy = 0
            
            if adjacent_enemy.x > player.x:
                dx = 1
            elif adjacent_enemy.x < player.x:
                dx = -1
            
            if adjacent_enemy.y > player.y:
                dy = 1
            elif adjacent_enemy.y < player.y:
                dy = -1
            
            action = self._build_move_action(dx, dy)
            # Reset stuck counter when attacking (making progress)
            self._reset_stuck_state()
            return action
        else:
            # Move toward target
            # Calculate single-step move toward enemy
            dx = 0
            dy = 0
            
            if target.x > player.x:
                dx = 1
            elif target.x < player.x:
                dx = -1
            
            if target.y > player.y:
                dy = 1
            elif target.y < player.y:
                dy = -1
            
            action = self._build_move_action(dx, dy)
            
            # Stuck detection is handled in decide_action before state transitions
            # We don't need to check it again here since we've already validated
            # that we're not stuck before entering this function
            
            return action
    
    def _handle_loot(self) -> Dict[str, Any]:
        """Handle LOOT state - pick up item.
        
        Returns:
            ActionDict with pickup action
        """
        return {"pickup": True}
    
    def _is_valid_target(self, target: Any, game_state: Any, player: Any) -> bool:
        """Check if a target is still valid for combat.
        
        A target is invalid if:
        - target is None
        - target not in entities list
        - target has no fighter component
        - target's HP <= 0
        - target is not in FOV
        
        Args:
            target: Target entity to validate
            game_state: Game state object
            player: Player entity
            
        Returns:
            True if target is valid, False otherwise
        """
        if not target:
            return False
        
        # Check if target is in entities list
        entities = getattr(game_state, 'entities', [])
        try:
            entities_list = list(entities)
            if target not in entities_list:
                return False
        except TypeError:
            # entities not iterable - can't validate
            return False
        
        # Check if target has fighter component and is alive
        get_component_optional = getattr(target, 'get_component_optional', None)
        if not callable(get_component_optional):
            return False
        
        from components.component_registry import ComponentType
        fighter = get_component_optional(ComponentType.FIGHTER)
        if not fighter or fighter.hp <= 0:
            return False
        
        # Check if target is in FOV
        fov_map = getattr(game_state, 'fov_map', None)
        if fov_map:
            if not map_is_in_fov(fov_map, target.x, target.y):
                return False
        
        return True
    
    def _update_stuck_detection(self, player: Any, target: Any, action: Dict[str, Any]) -> None:
        """Update stuck detection tracking.
        
        Tracks player and target positions to detect when the bot is making
        no progress toward a target. In COMBAT, if positions are unchanged:
        - Attack actions are treated as legitimate progress (attacking in place)
        - Move/wait/no-op actions increment stuck counter (blocked movement)
        
        Args:
            player: Player entity
            target: Target entity
            action: Action being taken
        """
        current_player_pos = (player.x, player.y)
        current_target_pos = None
        if target is not None and hasattr(target, "x") and hasattr(target, "y"):
            current_target_pos = (target.x, target.y)
        
        # Check if positions changed
        player_moved = (self._last_player_pos is not None and 
                       current_player_pos != self._last_player_pos)
        target_moved = (self._last_target_pos is not None and 
                       current_target_pos is not None and 
                       current_target_pos != self._last_target_pos)
        
        if self.state == BotState.COMBAT:
            # In COMBAT: check if positions are unchanged
            if (self._last_player_pos is not None and 
                self._last_target_pos is not None and
                not player_moved and 
                not target_moved):
                # Positions unchanged in COMBAT
                if self._is_attack_action(action):
                    # Attacking in place is legitimate progress
                    self._stuck_counter = 0
                    self._debug(f"Attack action in place, resetting stuck counter (player at {current_player_pos}, target at {current_target_pos})")
                else:
                    # Move/wait/no-op without movement = stuck
                    self._stuck_counter += 1
                    self._debug(f"Stuck counter: {self._stuck_counter} (player at {current_player_pos}, target at {current_target_pos}, action={action})")
            else:
                # Positions changed → we made progress
                self._stuck_counter = 0
        else:
            # Not in COMBAT → reset stuck counter
            self._stuck_counter = 0
        
        # Update last known positions
        self._last_player_pos = current_player_pos
        self._last_target_pos = current_target_pos
    
    def _is_stuck_on_target(self) -> bool:
        """Check if bot is stuck on current target.
        
        Returns:
            True if stuck counter exceeds threshold
        """
        return self._stuck_counter >= STUCK_THRESHOLD
    
    def _is_attack_action(self, action: Dict[str, Any]) -> bool:
        """Check if action is an attack action.
        
        Args:
            action: Action dictionary
            
        Returns:
            True if action represents an attack
        """
        # Moving into an adjacent enemy triggers attack, so movement toward enemy counts
        # We check for move actions in combat context separately
        return "attack" in action
    
    def _is_move_action(self, action: Dict[str, Any]) -> bool:
        """Check if action is a movement action.
        
        Args:
            action: Action dictionary
            
        Returns:
            True if action represents movement
        """
        return "move" in action and action["move"] is not None
    
    def _is_noop_action(self, action: Dict[str, Any]) -> bool:
        """Check if action is a no-op (wait or empty).
        
        Args:
            action: Action dictionary
            
        Returns:
            True if action is empty dict or contains only 'wait': True
        """
        if not action:
            return True
        if action == {"wait": True}:
            return True
        return False
    
    def _format_target(self, target: Any) -> str:
        """Format target for debug logging.
        
        Args:
            target: Target entity or None
            
        Returns:
            Formatted string representation
        """
        if target is None:
            return "None"
        if not hasattr(target, "x") or not hasattr(target, "y"):
            return "Invalid"
        return f"({target.x},{target.y})"
    
    def _log_decision_debug(self, player: Any, visible_enemies: List[Any], action: Dict[str, Any]) -> None:
        """Log structured debug information about the decision.
        
        Args:
            player: Player entity
            visible_enemies: List of visible enemies
            action: Action dictionary
        """
        if not self.debug:
            return
        
        target_str = self._format_target(self.current_target)
        oscillating = self._is_oscillating()
        
        self._debug(
            f"state={self.state.name}, "
            f"player=({player.x},{player.y}), "
            f"target={target_str}, "
            f"visible_enemies={len(visible_enemies)}, "
            f"action={action}, "
            f"stuck_counter={self._stuck_counter}, "
            f"combat_noop_counter={self._combat_noop_counter}, "
            f"oscillating={oscillating}"
        )
    
    def _is_oscillating(self) -> bool:
        """Check if bot is oscillating between two positions (A ↔ B ↔ A ↔ B).
        
        Returns:
            True if oscillation pattern detected
        """
        if len(self._recent_positions) < 4:
            return False
        
        # Get unique positions
        unique_positions = set(self._recent_positions)
        if len(unique_positions) != 2:
            return False
        
        # Get the two unique positions by finding first occurrence of each
        pos_list = list(self._recent_positions)
        a = pos_list[0]
        # Find the first position that's different from a
        b = None
        for pos in pos_list:
            if pos != a:
                b = pos
                break
        
        if b is None:
            # All positions are the same - not oscillating
            return False
        
        # Check for alternating pattern: all positions should alternate between a and b
        # We check if the pattern matches A,B,A,B... or B,A,B,A...
        pattern1 = all(pos_list[i] == (a if i % 2 == 0 else b) for i in range(len(pos_list)))
        pattern2 = all(pos_list[i] == (b if i % 2 == 0 else a) for i in range(len(pos_list)))
        
        return pattern1 or pattern2
    
    def _reset_stuck_state(self) -> None:
        """Reset stuck detection state."""
        self._stuck_counter = 0
        self._last_player_pos = None
        self._last_target_pos = None
        self._recent_positions.clear()
        self._combat_noop_counter = 0
        # Note: _just_dropped_due_to_stuck and _stuck_dropped_target are NOT reset here
        # They are reset when we successfully enter COMBAT or when we skip re-entry
    
    def _log_state_transition(self, new_state: BotState) -> None:
        """Log state transition at summary level.
        
        Args:
            new_state: New bot state
        """
        if self._last_state != new_state:
            self._log_summary(f"State transition: {self._last_state.name if self._last_state else 'INIT'} → {new_state.name}")
            self._last_state = new_state
    
    def _log_summary(self, msg: str) -> None:
        """Log summary-level message (state transitions, lifecycle events).
        
        Args:
            msg: Message to log
        """
        if self.log_level in (LogLevel.SUMMARY, LogLevel.DEBUG):
            logger.info(f"BotBrain: {msg}")
    
    def _log_error(self, msg: str) -> None:
        """Log error-level message (contract violations, impossible states).
        
        Args:
            msg: Message to log
        """
        logger.error(f"BotBrain ERROR: {msg}")
    
    def _debug(self, msg: str) -> None:
        """Log debug message if debug mode is enabled.
        
        Args:
            msg: Message to log
        """
        if self.log_level == LogLevel.DEBUG:
            # Print directly to console for immediate visibility during debugging
            # Also log to file for later analysis
            print(f"BotBrain: {msg}")
            logger.debug(f"BotBrain: {msg}")
    
    # ========================================================================
    # STAIRS DESCENT LOGIC (for multi-floor soak testing)
    # ========================================================================
    
    def _is_floor_complete(self, player: Any) -> bool:
        """Check if current floor is fully explored (for stairs descent).
        
        A floor is considered complete ONLY when AutoExplore has stopped with:
        - EXACTLY "All areas explored"
        - EXACTLY "Cannot reach unexplored areas"
        
        NOT "Movement blocked", NOT "Cancelled", NOT anything else.
        This ensures we only descend when truly complete, not on pathfinding failures.
        
        Args:
            player: Player entity
            
        Returns:
            bool: True if floor is fully explored
        """
        auto_explore = player.get_component_optional(ComponentType.AUTO_EXPLORE)
        if not auto_explore:
            return False
        
        # Floor is complete ONLY if AutoExplore stopped with exact completion reasons
        # Use str() to handle any numpy string types
        if not auto_explore.is_active() and auto_explore.stop_reason:
            stop_reason_str = str(auto_explore.stop_reason)
            is_terminal = stop_reason_str in TERMINAL_EXPLORE_REASONS
            if is_terminal:
                logger.warning(f"BotBrain: Floor IS complete (stop_reason='{stop_reason_str}')")
            return is_terminal
        
        return False
    
    def _is_standing_on_stairs(self, player: Any, entities: List[Any]) -> bool:
        """Check if player is currently standing on stairs.
        
        Args:
            player: Player entity
            entities: List of all entities
            
        Returns:
            bool: True if standing on stairs
        """
        for entity in entities:
            if hasattr(entity, 'components') and entity.components.has(ComponentType.STAIRS):
                if entity.x == player.x and entity.y == player.y:
                    return True
        return False
    
    def _find_nearest_stairs(self, player: Any, entities: List[Any]) -> Optional[Tuple[int, int]]:
        """Find the nearest stairs entity position.
        
        Args:
            player: Player entity
            entities: List of all entities
            
        Returns:
            (x, y) position of nearest stairs, or None if no stairs found
        """
        nearest_pos = None
        min_distance = float('inf')
        
        for entity in entities:
            if hasattr(entity, 'components') and entity.components.has(ComponentType.STAIRS):
                # Manhattan distance
                distance = abs(player.x - entity.x) + abs(player.y - entity.y)
                if distance < min_distance:
                    min_distance = distance
                    nearest_pos = (entity.x, entity.y)
        
        return nearest_pos
    
    def _calculate_path_to_stairs(
        self, 
        player: Any, 
        target: Tuple[int, int], 
        game_map: Any,
        entities: List[Any]
    ) -> List[Tuple[int, int]]:
        """Calculate A* path to target stairs position.
        
        Uses tcod pathfinding like AutoExplore does.
        
        Args:
            player: Player entity
            target: (x, y) destination
            game_map: Game map for pathfinding
            entities: All entities (for collision detection)
            
        Returns:
            List of (x, y) positions to visit (excluding start position),
            or empty list if no path found
        """
        import tcod
        import numpy as np
        
        try:
            # Create cost map using numpy (indexed as [y, x])
            cost = np.zeros((game_map.height, game_map.width), dtype=np.int8)
            
            for y in range(game_map.height):
                for x in range(game_map.width):
                    # Blocked tiles are impassable
                    if game_map.tiles[x][y].blocked:
                        cost[y, x] = 0
                    # Hazards are treated as impassable (if hazard_manager exists)
                    elif hasattr(game_map, 'hazard_manager') and game_map.hazard_manager.has_hazard_at(x, y):
                        cost[y, x] = 0
                    else:
                        cost[y, x] = 1
            
            # Entities block movement (except target tile)
            for entity in entities:
                if hasattr(entity, 'blocks') and entity.blocks and entity != player:
                    ex, ey = entity.x, entity.y
                    if 0 <= ex < game_map.width and 0 <= ey < game_map.height:
                        if (ex, ey) != target:  # Allow moving to target even if entity there
                            cost[ey, ex] = 0
            
            # Transpose cost array from [y, x] to [x, y] for tcod
            cost_array = cost.T
            
            # Validate player position is within map bounds
            start_x, start_y = player.x, player.y
            if start_x < 0 or start_x >= game_map.width or start_y < 0 or start_y >= game_map.height:
                self._debug(f"Player position ({start_x}, {start_y}) out of map bounds")
                return []
            
            # Create graph and pathfinder (modern tcod API)
            graph = tcod.path.SimpleGraph(cost=cost_array, cardinal=2, diagonal=3)
            pathfinder = tcod.path.Pathfinder(graph)
            pathfinder.add_root((start_x, start_y))
            
            # Find path
            path = pathfinder.path_to((target[0], target[1]))
            
            # Convert to list of tuples (excluding start position)
            return [(x, y) for x, y in path[1:]]
            
        except (AttributeError, TypeError, IndexError) as e:
            # Handle mock objects or missing attributes gracefully
            self._debug(f"Pathfinding error: {e}")
            return []
    
    def _handle_floor_complete(
        self, 
        player: Any, 
        entities: List[Any], 
        game_map: Any,
        visible_enemies: List[Any]
    ) -> Dict[str, Any]:
        """Handle floor complete state - walk to stairs and descend.
        
        This is called when AutoExplore has finished with a terminal reason.
        BotBrain takes over movement to walk to stairs.
        
        Behavior:
        - If enemies visible: clear stairs path, return empty (fall back to COMBAT)
        - If on stairs: descend
        - If stairs path exists: follow it
        - If no stairs path: find stairs and compute path
        - If no reachable stairs: abort run
        
        Args:
            player: Player entity
            entities: List of all entities
            game_map: Game map for pathfinding
            visible_enemies: List of visible hostile enemies
            
        Returns:
            ActionDict with take_stairs, move, or bot_abort_run
        """
        # Safety: If enemies appear while walking to stairs, abort stair descent
        # and fall back to normal combat handling
        if visible_enemies:
            if self._stairs_path:
                self._debug("Enemies visible while walking to stairs, clearing path")
                self._stairs_path = None
            # Return empty to let combat handling take over
            return {}
        
        # If standing on stairs, descend
        if self._is_standing_on_stairs(player, entities):
            self._log_summary(f"STAIRS: Floor complete, descending from ({player.x}, {player.y})")
            self._stairs_path = None  # Clear path
            return {"take_stairs": True}
        
        # If we have a stairs path, follow it
        if self._stairs_path:
            # Get next step
            next_pos = self._stairs_path.pop(0)
            dx = next_pos[0] - player.x
            dy = next_pos[1] - player.y
            
            self._debug(f"Walking to stairs: moving from ({player.x}, {player.y}) to {next_pos}, "
                       f"{len(self._stairs_path)} steps remaining")
            
            return self._build_move_action(dx, dy)
        
        # No path yet - find stairs and compute path
        stairs_pos = self._find_nearest_stairs(player, entities)
        
        # Log at WARNING level for floor complete diagnostics
        logger.warning(
            f"BotBrain FLOOR_COMPLETE: player=({player.x}, {player.y}), "
            f"stairs_pos={stairs_pos}, game_map={'exists' if game_map else 'None'}, "
            f"entities_count={len(entities) if entities else 0}"
        )
        
        if stairs_pos is None:
            # No stairs found
            # TODO: Mark as "no_stairs" in failure_type for soak harness integration
            logger.warning("BotBrain FLOOR_COMPLETE: No stairs found, aborting run")
            return {"bot_abort_run": True}
        
        # Already on stairs? (shouldn't happen due to check above, but safety)
        # Use int() conversion to handle numpy types
        player_pos = (int(player.x), int(player.y))
        stairs_pos_int = (int(stairs_pos[0]), int(stairs_pos[1]))
        if player_pos == stairs_pos_int:
            self._log_summary(f"STAIRS: Floor complete, descending from {player_pos}")
            return {"take_stairs": True}
        
        # Compute path to stairs
        self._stairs_path = self._calculate_path_to_stairs(player, stairs_pos, game_map, entities)
        
        logger.warning(
            f"BotBrain FLOOR_COMPLETE: Pathfinding result - path_len={len(self._stairs_path) if self._stairs_path else 0}"
        )
        
        if not self._stairs_path:
            # No path to stairs
            # TODO: Mark as "no_stairs" in failure_type for soak harness integration
            logger.warning(f"BotBrain FLOOR_COMPLETE: No path to stairs at {stairs_pos}, aborting run")
            return {"bot_abort_run": True}
        
        self._log_summary(f"STAIRS: Floor complete, walking to stairs at {stairs_pos} "
                         f"({len(self._stairs_path)} steps)")
        
        # Take first step
        next_pos = self._stairs_path.pop(0)
        dx = next_pos[0] - player.x
        dy = next_pos[1] - player.y
        
        return self._build_move_action(dx, dy)
    
    # ========================================================================
    # POTION-DRINKING LOGIC (for soak testing survivability)
    # ========================================================================
    
    def _get_player_hp_fraction(self, player: Any) -> float:
        """Calculate player's current HP as a fraction of max HP.
        
        Args:
            player: Player entity
            
        Returns:
            float: HP fraction (0.0 to 1.0), or 1.0 if no fighter component
        """
        fighter = player.get_component_optional(ComponentType.FIGHTER)
        if not fighter or fighter.max_hp <= 0:
            return 1.0
        
        return fighter.hp / fighter.max_hp
    
    def _get_healing_potions_in_inventory(self, player: Any) -> List[tuple]:
        """Get all known healing potions from player's inventory.
        
        CRITICAL: Returns indices into SORTED inventory (alphabetically by display name)
        to match the inventory action handler's expectations.
        
        Args:
            player: Player entity
            
        Returns:
            List of (index, item_entity) tuples for healing potions
        """
        inventory = player.get_component_optional(ComponentType.INVENTORY)
        if not inventory or not hasattr(inventory, 'items'):
            return []
        
        # CRITICAL: Sort inventory alphabetically to match action handler
        sorted_items = sorted(inventory.items, key=lambda item: item.get_display_name().lower())
        
        healing_potions = []
        for idx, item in enumerate(sorted_items):
            item_comp = item.get_component_optional(ComponentType.ITEM)
            if not item_comp:
                continue
            
            # Check if this is a healing potion
            # Healing potions have name "healing_potion" and use_function "heal"
            item_name = item.name.lower().replace(' ', '_')
            
            # Must be identified as a healing potion
            if item_comp.identified and item_name == "healing_potion":
                healing_potions.append((idx, item))
        
        return healing_potions
    
    def _get_any_potions_in_inventory(self, player: Any) -> List[tuple]:
        """Get all potions (identified or unidentified) from player's inventory.
        
        CRITICAL: Returns indices into SORTED inventory (alphabetically by display name)
        to match the inventory action handler's expectations.
        
        Args:
            player: Player entity
            
        Returns:
            List of (index, item_entity) tuples for all potions
        """
        inventory = player.get_component_optional(ComponentType.INVENTORY)
        if not inventory or not hasattr(inventory, 'items'):
            return []
        
        # CRITICAL: Sort inventory alphabetically to match action handler
        sorted_items = sorted(inventory.items, key=lambda item: item.get_display_name().lower())
        
        potions = []
        for idx, item in enumerate(sorted_items):
            item_comp = item.get_component_optional(ComponentType.ITEM)
            if not item_comp:
                continue
            
            # Check if this is a potion (has use_function and char '!' BUT not a wand)
            # Potions have char '!' but we must exclude wands which also have use_function
            # CRITICAL: Check for wand component to exclude wands
            if item.components.has(ComponentType.WAND):
                continue  # Skip wands
            
            if item_comp.use_function and item.char == '!':
                potions.append((idx, item))
        
        return potions
    
    def _should_drink_potion(self, player: Any, visible_enemies: List[Any]) -> bool:
        """Check if bot should drink a potion.
        
        Conditions:
        - HP <= persona.potion_hp_threshold (configurable per persona)
        - No visible enemies (safe to drink)
        
        Args:
            player: Player entity
            visible_enemies: List of visible hostile enemies
            
        Returns:
            bool: True if bot should try to drink a potion
        """
        # Must be low on HP (threshold from persona)
        hp_fraction = self._get_player_hp_fraction(player)
        if hp_fraction > self.persona.potion_hp_threshold:
            return False
        
        # Must have no visible enemies (safe)
        if visible_enemies:
            return False
        
        return True
    
    def _choose_potion_to_drink(self, player: Any) -> Optional[int]:
        """Choose which potion to drink and return its inventory index.
        
        Strategy:
        1. Prefer known healing potions (safe, effective)
        2. Fall back to any potion if no healing potions available
        
        Args:
            player: Player entity
            
        Returns:
            int: Inventory index of potion to drink, or None if no potions
        """
        # First, try to find a known healing potion
        healing_potions = self._get_healing_potions_in_inventory(player)
        if healing_potions:
            # Use the first healing potion
            idx, item = healing_potions[0]
            self._log_summary(
                f"POTION: Drinking known healing potion at HP {self._get_player_hp_fraction(player):.1%}"
            )
            return idx
        
        # No known healing potions - try any potion
        any_potions = self._get_any_potions_in_inventory(player)
        if any_potions:
            # Use the first available potion
            idx, item = any_potions[0]
            display_name = item.get_display_name() if hasattr(item, 'get_display_name') else item.name
            self._log_summary(
                f"POTION: Drinking unidentified potion ({display_name}) at HP {self._get_player_hp_fraction(player):.1%}"
            )
            return idx
        
        # No potions available
        return None

