"""Bot decision-making brain for automated gameplay.

This module provides a minimal decision-making "BotBrain" used by bot input.
Phase 2.0 scope: EXPLORE + simple COMBAT + simple LOOT behavior.

No retreat or healing logic yet.
"""

import logging
from collections import deque
from enum import Enum
from typing import Any, Dict, List, Optional

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

# Bot stairs-seeking configuration: maximum distance to walk to stairs after floor complete
BOT_STAIRS_RADIUS = 10  # Bot will walk up to 10 tiles to reach stairs when floor is explored


class BotState(Enum):
    """Bot decision-making states."""
    EXPLORE = "explore"
    COMBAT = "combat"
    LOOT = "loot"


class BotBrain:
    """Simple decision-making brain for bot input.
    
    Implements a state machine with EXPLORE, COMBAT, and LOOT states.
    Makes decisions based on game state without knowing about soak mode.
    
    Attributes:
        state: Current bot decision state
        current_target: Currently targeted enemy entity (if in COMBAT)
        _stuck_counter: Counter for detecting stuck behavior
        _last_player_pos: Last known player position (x, y)
        _last_target_pos: Last known target position (x, y)
        _recent_positions: Deque of recent player positions for oscillation detection
        debug: Enable debug logging
    """
    
    def __init__(self, debug: bool = False, log_level: LogLevel = LogLevel.SUMMARY) -> None:
        """Initialize BotBrain with default EXPLORE state.
        
        Args:
            debug: Enable debug logging for troubleshooting (deprecated, use log_level)
            log_level: Logging tier level (SUMMARY, DEBUG, or ERROR)
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
        # COMBAT no-op fail-safe: track consecutive no-op actions in COMBAT
        self._combat_noop_counter = 0
        self._combat_noop_threshold = 10  # Drop to EXPLORE after 10 consecutive no-op actions
        self._just_dropped_due_to_noop = False  # Flag to prevent immediate re-entry after no-op fail-safe
        self._noop_dropped_target = None  # Target we dropped due to no-op fail-safe
        # Track autoexplore lifecycle for logging
        self._last_autoexplore_active = False
        self._last_state = BotState.EXPLORE  # Track state transitions for summary logging
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
            
            # STAIRS DESCENT: If floor is fully explored, seek and use stairs (multi-floor soak testing)
            # Only triggers when:
            # - Floor is complete (AutoExplore stopped with "All areas explored" or "Cannot reach")
            # - No enemies visible (safe to descend)
            # Priority: Check if standing on stairs first, then seek nearby stairs, then end run
            if not visible_enemies and self._is_floor_complete(player):
                # Check if standing on stairs
                if self._is_standing_on_stairs(player, entities):
                    self._log_summary(f"STAIRS: Floor complete, descending from ({player.x}, {player.y})")
                    return {"take_stairs": True}
                
                # Look for stairs within radius
                stairs_pos = self._find_nearest_stairs(player, entities)
                if stairs_pos:
                    stairs_dist = abs(stairs_pos[0] - player.x) + abs(stairs_pos[1] - player.y)
                    self._debug(f"STAIRS: Walking to stairs at {stairs_pos} (distance {stairs_dist})")
                    # Calculate move toward stairs
                    dx = 0
                    dy = 0
                    if stairs_pos[0] > player.x:
                        dx = 1
                    elif stairs_pos[0] < player.x:
                        dx = -1
                    if stairs_pos[1] > player.y:
                        dy = 1
                    elif stairs_pos[1] < player.y:
                        dy = -1
                    return self._build_move_action(dx, dy)
                else:
                    # Floor complete but no reachable stairs - end run
                    self._log_summary(f"STAIRS: Floor complete, no stairs within {BOT_STAIRS_RADIUS} tiles - ending run")
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
                # Check if any enemy is within Manhattan distance <= 8
                nearest_enemy = self._find_nearest_enemy(player, visible_enemies)
                if nearest_enemy:
                    manhattan_dist = abs(player.x - nearest_enemy.x) + abs(player.y - nearest_enemy.y)
                    if manhattan_dist <= 8:
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
                # Check if we should skip LOOT state (oscillation prevention)
                if self._turn_counter < self._skip_loot_until_turn:
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
                    f"autoexplore_active={self._is_autoexplore_active(game_state)}, "
                    f"cached_autoexplore_active={self._last_autoexplore_active}"
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
            
            return action
        except (AttributeError, TypeError) as e:
            # Gracefully handle missing or mock attributes
            logger.debug(f"BotBrain decide_action caught exception: {e}")
            
            # If game state is in PLAYERS_TURN, return safe fallback to explore
            if game_state.current_state == GameStates.PLAYERS_TURN:
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
        
        This method respects the manual autoexplore contract:
        - If autoexplore is not active: start it once
        - If autoexplore is active: return empty dict (ActionProcessor handles movement automatically)
        - No interference with autoexplore while it's running
        
        CRITICAL: ActionProcessor automatically calls _process_auto_explore_turn() every turn
        when AutoExplore is active. BotBrain should trust its cached state and only check
        is_active() when cached state indicates it might be inactive.
        
        Args:
            player: Player entity
            game_state: Game state object (for checking autoexplore status)
            
        Returns:
            ActionDict with start_auto_explore or empty dict
        """
        # Optimization: Trust cached state when AutoExplore is active
        # Only check is_active() when we think it might be inactive (to detect stops)
        if self._last_autoexplore_active:
            # We believe AutoExplore is active - trust it and return empty dict
            # ActionProcessor will automatically call _process_auto_explore_turn()
            # DIAGNOSTIC: Verify AutoExplore is actually still active
            actual_active = self._is_autoexplore_active(game_state)
            if not actual_active:
                logger.warning(
                    f"🔍 DIAGNOSTIC: BotBrain cache mismatch! "
                    f"cached_active=True but actual_active=False at ({player.x},{player.y})"
                )
                self._last_autoexplore_active = False
                # Fall through to restart logic
            else:
                return {}
        
        # Cached state says inactive - verify and start if needed
        is_active = self._is_autoexplore_active(game_state)
        
        if not is_active:
            # Autoexplore is not active - start it once
            was_active = self._last_autoexplore_active
            
            if not was_active:
                # Transition: inactive -> starting (first time)
                player_pos = (player.x, player.y)
                self._log_summary(f"EXPLORE: Starting AutoExplore at {player_pos}")
                self._debug(f"BotBrain: EXPLORE starting autoexplore at {player_pos}")
                logger.info(f"🔍 DIAGNOSTIC: BotBrain._handle_explore: Starting AutoExplore at {player_pos}")
                # Optimistically update cache - AutoExplore.start() will activate it
                self._last_autoexplore_active = True
            else:
                # Transition: active -> inactive (AutoExplore stopped)
                # Get AutoExplore component to check stop_reason for logging
                auto_explore = None
                stop_reason = None
                if hasattr(player, 'get_component_optional'):
                    auto_explore = player.get_component_optional(ComponentType.AUTO_EXPLORE)
                    if auto_explore:
                        stop_reason = auto_explore.stop_reason
                player_pos = (player.x, player.y)
                logger.warning(
                    f"🔍 DIAGNOSTIC: BotBrain._handle_explore: AutoExplore stopped! "
                    f"pos={player_pos}, stop_reason='{stop_reason}', "
                    f"was_active={was_active}, is_active={is_active}"
                )
                if auto_explore and stop_reason:
                    self._log_summary(f"EXPLORE: AutoExplore stopped - {stop_reason}")
                # Cache says inactive (will be verified next turn if restart fails)
                self._last_autoexplore_active = False
            
            return {"start_auto_explore": True}
        else:
            # Check revealed AutoExplore is actually active (cached state was wrong)
            # This should be rare - update cache and return empty dict
            was_active = self._last_autoexplore_active
            if not was_active:
                # Transition: inactive -> active (just started)
                player_pos = (player.x, player.y)
                self._log_summary(f"EXPLORE: AutoExplore started at {player_pos}")
                self._debug(f"BotBrain: EXPLORE autoexplore started at {player_pos}")
                logger.info(f"🔍 DIAGNOSTIC: BotBrain._handle_explore: AutoExplore is active at {player_pos}")
            
            self._last_autoexplore_active = True
            # Return empty dict - ActionProcessor will automatically call _process_auto_explore_turn()
            return {}
    
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
        
        A floor is considered complete when AutoExplore has stopped with reasons:
        - "All areas explored"
        - "Cannot reach unexplored areas"
        
        Args:
            player: Player entity
            
        Returns:
            bool: True if floor is fully explored
        """
        auto_explore = player.get_component_optional(ComponentType.AUTO_EXPLORE)
        if not auto_explore:
            return False
        
        # Floor is complete if AutoExplore stopped due to completion
        if not auto_explore.is_active() and auto_explore.stop_reason:
            completion_reasons = ["All areas explored", "Cannot reach unexplored areas"]
            return any(reason in auto_explore.stop_reason for reason in completion_reasons)
        
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
    
    def _find_nearest_stairs(self, player: Any, entities: List[Any]) -> Optional[tuple]:
        """Find nearest stairs within BOT_STAIRS_RADIUS.
        
        Args:
            player: Player entity
            entities: List of all entities
            
        Returns:
            (x, y) position of nearest stairs, or None if none within radius
        """
        stairs_positions = []
        
        for entity in entities:
            if hasattr(entity, 'components') and entity.components.has(ComponentType.STAIRS):
                # Calculate Manhattan distance
                dist = abs(entity.x - player.x) + abs(entity.y - player.y)
                if dist <= BOT_STAIRS_RADIUS:
                    stairs_positions.append((dist, (entity.x, entity.y)))
        
        if not stairs_positions:
            return None
        
        # Return closest stairs
        stairs_positions.sort(key=lambda x: x[0])
        _, pos = stairs_positions[0]
        return pos
    
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
        - HP <= 40% (low health threshold)
        - No visible enemies (safe to drink)
        
        Args:
            player: Player entity
            visible_enemies: List of visible hostile enemies
            
        Returns:
            bool: True if bot should try to drink a potion
        """
        # Must be low on HP
        hp_fraction = self._get_player_hp_fraction(player)
        if hp_fraction > 0.4:  # 40% threshold
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

