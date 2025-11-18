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

# Stuck detection threshold: number of consecutive combat decisions without progress
STUCK_THRESHOLD = 8


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
    
    def __init__(self, debug: bool = False) -> None:
        """Initialize BotBrain with default EXPLORE state.
        
        Args:
            debug: Enable debug logging for troubleshooting
        """
        self.state = BotState.EXPLORE
        self.current_target = None
        self._stuck_counter = 0
        self._last_player_pos = None
        self._last_target_pos = None
        self._recent_positions = deque(maxlen=6)  # Track last 6 positions for oscillation detection
        self._just_dropped_due_to_stuck = False  # Flag to prevent immediate re-entry
        self._stuck_dropped_target = None  # Target we dropped due to being stuck
        self.debug = debug
        # COMBAT no-op fail-safe: track consecutive no-op actions in COMBAT
        self._combat_noop_counter = 0
        self._combat_noop_threshold = 10  # Drop to EXPLORE after 10 consecutive no-op actions
        self._just_dropped_due_to_noop = False  # Flag to prevent immediate re-entry after no-op fail-safe
        self._noop_dropped_target = None  # Target we dropped due to no-op fail-safe
        # Track autoexplore lifecycle for logging
        self._last_autoexplore_active = False
    
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
            # Get player entity
            player = self._get_player(game_state)
            if not player:
                return {}
            
            # Get visible enemies
            visible_enemies = self._get_visible_enemies(game_state, player)
            
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
            entities = getattr(game_state, 'entities', [])
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
                        else:
                            # Different target or flags not set - can enter COMBAT
                            if self.state != BotState.COMBAT or self.current_target != nearest_enemy:
                                self._debug(f"Entering COMBAT with enemy at ({nearest_enemy.x}, {nearest_enemy.y}), distance {manhattan_dist}")
                                # Reset stuck state when switching targets
                                if self.current_target != nearest_enemy:
                                    self._reset_stuck_state()
                            self.state = BotState.COMBAT
                            self.current_target = nearest_enemy
                            # Clear flags when successfully entering COMBAT with a different target
                            self._just_dropped_due_to_stuck = False
                            self._just_dropped_due_to_noop = False
                            self._stuck_dropped_target = None
                            self._noop_dropped_target = None
                    else:
                        if self.state == BotState.COMBAT:
                            self._debug(f"Enemy too far (distance {manhattan_dist}), leaving COMBAT")
                        self.current_target = None
                        self.state = BotState.EXPLORE
                        self._reset_stuck_state()
                else:
                    if self.state == BotState.COMBAT:
                        self._debug("No nearest enemy found, leaving COMBAT")
                    self.current_target = None
                    self.state = BotState.EXPLORE
                    self._reset_stuck_state()
            elif standing_on_loot:
                if self.state != BotState.LOOT:
                    self._debug("Entering LOOT state")
                self.state = BotState.LOOT
                # Clear combat target when looting
                if self.current_target:
                    self.current_target = None
                    self._reset_stuck_state()
            else:
                if self.state == BotState.COMBAT:
                    self._debug("No enemies visible, leaving COMBAT")
                    # Only reset stuck state when transitioning FROM COMBAT to EXPLORE
                    self._reset_stuck_state()
                self.current_target = None
                self.state = BotState.EXPLORE
            
            # Actions based on state
            action = {}
            if self.state == BotState.EXPLORE:
                # Normal EXPLORE path - start autoexplore once, then let it run
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
        - If autoexplore is active: return empty dict to let it handle movement
        - No interference with autoexplore while it's running
        
        Args:
            player: Player entity
            game_state: Game state object (for checking autoexplore status)
            
        Returns:
            ActionDict with start_auto_explore or empty dict
        """
        player_pos = (player.x, player.y)
        is_active = self._is_autoexplore_active(game_state)
        
        # Track lifecycle transitions for logging
        was_active = self._last_autoexplore_active
        self._last_autoexplore_active = is_active
        
        if not is_active:
            # Autoexplore is not active - start it once
            if not was_active:
                # Transition: inactive -> starting (first time)
                logger.debug("BotBrain: EXPLORE starting autoexplore at %s", player_pos)
            return {"start_auto_explore": True}
        else:
            # Autoexplore is active - let it handle movement, don't interfere
            if not was_active:
                # Transition: inactive -> active (just started)
                logger.debug("BotBrain: EXPLORE autoexplore started at %s", player_pos)
            logger.debug("BotBrain: EXPLORE letting autoexplore run at %s", player_pos)
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
    
    def _debug(self, msg: str) -> None:
        """Log debug message if debug mode is enabled.
        
        Args:
            msg: Message to log
        """
        if self.debug:
            # Print directly to console for immediate visibility during debugging
            # Also log to file for later analysis
            print(f"BotBrain: {msg}")
            logger.info(f"BotBrain: {msg}")

