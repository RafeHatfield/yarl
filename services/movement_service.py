"""Movement service - single source of truth for all player movement.

This service handles movement from ANY input source (keyboard, mouse pathfinding)
and ensures all movement-related checks happen consistently:
- Portal entry (Phase 5)
- Secret door reveals
- Camera updates
- FOV updates

By centralizing movement logic, we prevent bugs where a feature works
for keyboard input but not mouse input (or vice versa).
"""

import logging
from typing import Tuple, Dict, Any, Optional, List, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from entity import Entity
    from map_objects.game_map import GameMap

logger = logging.getLogger(__name__)


@dataclass
class MovementResult:
    """Result of a movement attempt.

    Attributes:
        success: Whether movement succeeded
        blocked_by_wall: Movement blocked by wall/tile
        blocked_by_entity: Movement blocked by entity (combat target)
        blocked_by_status: Movement blocked by status effect (immobilized, etc.)
        portal_entry: Player stepped on portal (triggers confrontation)
        messages: List of message dictionaries to display
        fov_recompute: Whether FOV needs recomputation
        camera_updated: Whether camera was updated
        new_position: Player's new (x, y) position if moved
    """
    success: bool = False
    blocked_by_wall: bool = False
    blocked_by_entity: Optional['Entity'] = None  # For combat
    blocked_by_status: bool = False  # For immobilized, etc.
    portal_entry: bool = False
    messages: List[Dict[str, Any]] = None
    fov_recompute: bool = False
    camera_updated: bool = False
    new_position: Optional[Tuple[int, int]] = None
    
    def __post_init__(self):
        if self.messages is None:
            self.messages = []


class MovementService:
    """Service for handling all player movement logic.
    
    This is the single source of truth for movement mechanics.
    All input methods (keyboard, mouse) should use this service.
    """
    
    def __init__(self, state_manager):
        """Initialize movement service.
        
        Args:
            state_manager: The game's state manager
        """
        self.state_manager = state_manager
    
    def execute_movement(self, dx: int, dy: int, source: str = "keyboard") -> MovementResult:
        """Execute a movement action.
        
        This is the ONLY place movement logic should exist.
        Call this from keyboard handlers, pathfinding, or any other input source.
        
        Args:
            dx: X movement delta
            dy: Y movement delta
            source: Input source ("keyboard", "pathfinding", "other") - for debugging
            
        Returns:
            MovementResult with success status and side effects
        """
        from game_states import GameStates
        from message_builder import MessageBuilder as MB
        
        result = MovementResult()
        
        player = self.state_manager.state.player
        if not player:
            logger.error("No player found for movement")
            return result
        
        game_map = self.state_manager.state.game_map
        entities = self.state_manager.state.entities
        current_state = self.state_manager.state.current_state
        
        # Calculate destination
        dest_x = player.x + dx
        dest_y = player.y + dy
        
        logger.debug(f"Movement attempt: ({player.x}, {player.y}) -> ({dest_x}, {dest_y}) via {source}")

        # Check for movement-blocking status effects
        from components.component_registry import ComponentType
        
        # Track whether we should flip chant toggle after successful movement
        chant_should_flip_toggle = False
        
        if player.components.has(ComponentType.STATUS_EFFECTS):
            status_effects = player.status_effects
            
            # Check for immobilized (Glue spell)
            if status_effects and status_effects.has_effect("immobilized"):
                result.blocked_by_status = True
                result.messages.append(MB.warning("You are stuck in place and cannot move!"))
                logger.debug("Movement blocked by immobilized status effect")
                return result
            
            # Phase 20D.1: Check for entangled (Root Potion)
            # Movement is blocked but TURN IS CONSUMED
            if status_effects and status_effects.has_effect("entangled"):
                result.blocked_by_status = True
                # Get the entangled effect and call on_move_blocked for metrics
                entangled_effect = status_effects.get_effect("entangled")
                if entangled_effect and hasattr(entangled_effect, 'on_move_blocked'):
                    block_results = entangled_effect.on_move_blocked()
                    for br in block_results:
                        if 'message' in br:
                            result.messages.append(br['message'])
                else:
                    result.messages.append(MB.warning("Roots bind you! You struggle but cannot move!"))
                logger.debug("Movement blocked by entangled status effect")
                return result
            
            # Phase 19: Check for Dissonant Chant movement tax (alternating block)
            # While chanted, movement alternates: allowed -> blocked -> allowed -> blocked
            # This creates "movement costs 2" without double-advancing the world
            # IMPORTANT: Toggle only flips on SUCCESSFUL movement (not wall bumps)
            if status_effects.has_effect("dissonant_chant"):
                # Initialize toggle flag if not present
                if not hasattr(player, '_chant_move_block_next'):
                    player._chant_move_block_next = False
                
                if player._chant_move_block_next:
                    # Block this move, reset toggle for next attempt
                    player._chant_move_block_next = False
                    result.blocked_by_status = True
                    result.messages.append(MB.warning("🎵 The chant disrupts your footing!"))
                    logger.debug("Movement blocked by Dissonant Chant (alternating tax)")
                    return result
                else:
                    # Mark that we should flip toggle IF movement succeeds
                    # Don't flip yet - wait until after wall/entity checks
                    chant_should_flip_toggle = True
                    # Movement proceeds to validation checks below

        # Check for door at destination FIRST (before wall check)
        # Doors may block tiles, but we want to handle them specially
        door_entity = self._find_door_at_location(entities, dest_x, dest_y)
        if door_entity and door_entity.components.has(ComponentType.DOOR):
            door_result = self._handle_door_bump(player, door_entity, result)
            if not door_result.success:
                # Door blocked movement (locked or secret and undiscovered)
                result.blocked_by_entity = door_entity
                result.messages.extend(door_result.messages)
                logger.debug(f"Movement blocked by door at ({dest_x}, {dest_y})")
                return result
            else:
                # Door was opened - update tile to be passable and continue movement
                result.messages.extend(door_result.messages)
                # Door is now open, so tile should not block
                # Continue to movement execution below
        
        # Check for wall/blocked tile (after door handling)
        if game_map.is_blocked(dest_x, dest_y):
            result.blocked_by_wall = True
            logger.debug(f"Movement blocked by wall at ({dest_x}, {dest_y})")
            return result
        
        # Check for blocking entity (potential combat target)
        from entity import get_blocking_entities_at_location
        blocking_entity = get_blocking_entities_at_location(entities, dest_x, dest_y)
        if blocking_entity:
            result.blocked_by_entity = blocking_entity
            logger.debug(f"Movement blocked by {blocking_entity.name} at ({dest_x}, {dest_y})")
            return result
        
        # Movement is valid - execute it
        old_pos = (player.x, player.y)
        player.move(dx, dy)
        result.success = True
        logger.debug(f"[PLAYER_MOVE] SUCCESS: moved from {old_pos} to ({player.x}, {player.y}) via {source}")
        result.new_position = (player.x, player.y)
        result.fov_recompute = True
        
        # Phase 19: Flip chant toggle AFTER successful movement
        # This ensures wall bumps and blocked entities don't waste the toggle
        if chant_should_flip_toggle:
            player._chant_move_block_next = True
            logger.debug("Chant toggle flipped: next move will be blocked")
        
        logger.info(f"Player moved: {old_pos} -> {result.new_position} via {source}")
        
        # Update camera to follow player
        camera = self.state_manager.state.camera
        if camera:
            old_camera_pos = (camera.x, camera.y)
            camera_moved = camera.update(player.x, player.y)
            result.camera_updated = camera_moved
            if camera_moved:
                logger.debug(f"Camera updated: {old_camera_pos} -> ({camera.x}, {camera.y})")
        else:
            logger.warning(f"Camera missing during movement! Player at {result.new_position}")
        
        # ===================================================================
        # POST-MOVEMENT CHECKS (Phase 5: Portal Entry, Secret Doors, etc.)
        # ===================================================================
        
        # Check for portal entry (Phase 5) - always check when moving, regardless of state
        logger.debug(f"MovementService: Checking portal entry at {result.new_position}")

        # Check for wand portal collision (teleportation) using PortalManager
        from services.portal_manager import get_portal_manager
        portal_manager = get_portal_manager()
        portal_collision = portal_manager.check_portal_collision(player, entities)
        if portal_collision and portal_collision.get('teleported'):
            logger.info(f"Portal teleportation: {portal_collision.get('from_pos')} -> {portal_collision.get('to_pos')}")
            # Use the visual effect message from PortalManager
            vfx_msg = portal_collision.get('message', MB.item_effect("You step through the portal..."))
            result.messages.append({"message": vfx_msg})
            result.messages.append({"message": MB.warning("✨ Reality bends around you!")})
            # FOV needs recompute after teleportation
            result.fov_recompute = True
            return result  # Exit early after teleportation
        
        # Check for victory portal entry (only triggers confrontation, doesn't teleport)
        # Victory portal only spawns after picking up Ruby Heart, so we can assume it always triggers confrontation
        portal_entity = portal_manager.check_victory_portal_collision(player, entities)
        if portal_entity:
            logger.info(f"=== MOVEMENT_SERVICE: VICTORY PORTAL ENTRY DETECTED at {result.new_position}!")

            # Check if an ending has already been achieved (prevent re-entering after choice made)
            ending_already_achieved = (hasattr(player, 'victory') and
                                      player.victory and
                                      player.victory.ending_achieved is not None)

            if ending_already_achieved:
                # Player has already chosen an ending - just move them (shouldn't happen normally)
                logger.debug("Portal entry: ending already achieved, allowing movement")
                result.messages.append({"message": MB.info("You step through the portal once more...")})
            else:
                # Trigger confrontation (can be triggered multiple times if player exits with ESC)
                result.portal_entry = True
                result.messages.append({"message": MB.item_effect("You step through the portal...")})
                result.messages.append({"message": MB.warning("Reality twists around you!")})
                logger.debug("Portal entry: triggering confrontation (re-enterable until ending chosen)")
        else:
            logger.debug("Portal entry check: no portal at player position")
        
        # Check for passive secret door reveals
        self._check_secret_reveals(player, game_map)
        
        # Check for traps on the new tile
        self._check_trap_trigger(player, entities, game_map, result)
        
        return result
    
    # NOTE: _check_portal_entry() moved to PortalManager.check_victory_portal_collision()
    # PortalManager is now the single source of truth for all portal operations
    
    def _check_secret_reveals(self, player: 'Entity', game_map: 'GameMap') -> None:
        """Check for passive secret door reveals near player.
        
        Args:
            player: Player entity
            game_map: Game map
        """
        if not hasattr(game_map, 'reveal_secret_doors_near'):
            return
        
        # Check 1-tile radius for secret doors
        revealed = game_map.reveal_secret_doors_near(player.x, player.y, radius=1)
        if revealed:
            logger.debug(f"Revealed {revealed} secret door(s) near player")
    
    def _check_trap_trigger(self, player: 'Entity', entities: list, game_map: 'GameMap', result) -> None:
        """Check for traps on player's current tile and apply effects.
        
        This handles trap detection, triggering, and effect application.
        
        Args:
            player: Player entity
            entities: List of all entities
            game_map: Game map
            result: MovementResult to append messages to
        """
        from components.component_registry import ComponentType
        from random import random
        from message_builder import MessageBuilder as MB
        
        # Find trap at player's position
        trap_entity = None
        for entity in entities:
            if (entity.x == player.x and entity.y == player.y and 
                entity.components.has(ComponentType.TRAP)):
                trap_entity = entity
                break
        
        if not trap_entity:
            return
        
        trap = trap_entity.components.get(ComponentType.TRAP)
        if not trap:
            return
        
        # If trap is already disarmed, nothing happens
        if trap.is_disarmed:
            return
        
        # If trap is detected, player avoids it
        if trap.is_detected:
            result.messages.append({"message": MB.warning(f"You carefully avoid the {trap_entity.name}.")})
            return
        
        # Check for passive detection
        if trap.can_be_detected() and random() < trap.passive_detect_chance:
            trap.detect("passive")
            result.messages.append({"message": MB.success(f"You notice the {trap_entity.name}!")})
            return
        
        # If trap was not detected, it triggers!
        if trap.is_triggered():
            result.messages.append({"message": MB.danger(f"You stepped on the {trap_entity.name}!")})
            self._apply_trap_effects(player, trap_entity, trap, result)
    
    def _apply_trap_effects(self, player: 'Entity', trap_entity: 'Entity', trap, result) -> None:
        """Apply trap effects to the player.
        
        Args:
            player: Player entity
            trap_entity: Entity containing the trap
            trap: Trap component
            result: MovementResult to append messages to
        """
        from components.component_registry import ComponentType
        from components.fighter import Fighter
        from message_builder import MessageBuilder as MB
        
        if trap.trap_type == "spike_trap":
            # Spike trap: damage + bleed
            fighter = player.components.get(ComponentType.FIGHTER)
            if fighter:
                from services.damage_service import apply_damage
                
                damage = trap.spike_damage
                result.messages.append({"message": MB.player_hit(f"Spikes pierce you for {damage} damage!")})
                
                # Apply damage using centralized service (handles death automatically)
                damage_results = apply_damage(
                    self.state_manager,
                    player,
                    damage,
                    cause="spike_trap"
                )
                
                # Check if player died (service already finalized death, just need to stop processing)
                for damage_result in damage_results:
                    if damage_result.get("dead") == player:
                        return  # Don't apply bleed to dead player
                
                # Apply bleed status effect (only if player survived)
                status_effects = player.components.get(ComponentType.STATUS_EFFECTS)
                if status_effects:
                    status_effects.add_effect("bleed", {
                        "severity": trap.spike_bleed_severity,
                        "duration": trap.spike_bleed_duration
                    })
                    result.messages.append({"message": MB.warning(f"You are bleeding!")})
        
        elif trap.trap_type == "web_trap":
            # Web trap: slow/snare
            status_effects = player.components.get(ComponentType.STATUS_EFFECTS)
            if status_effects:
                status_effects.add_effect("slowed", {
                    "severity": trap.web_slow_severity,
                    "duration": trap.web_duration
                })
                result.messages.append({"message": MB.warning(f"You are stuck in sticky webs for {trap.web_duration} turns!")})
            else:
                result.messages.append({"message": MB.warning(f"You are stuck in sticky webs!")})
        
        elif trap.trap_type == "alarm_plate":
            # Alarm trap: alert nearby mobs in faction
            result.messages.append({"message": MB.danger(f"ALARM! The pressure plate triggers a loud gong!")})
            self._alert_nearby_mobs(player, trap)
    
    def _alert_nearby_mobs(self, player: 'Entity', trap) -> None:
        """Alert nearby monsters of the same faction as configured in trap.
        
        Args:
            player: Player entity
            trap: Trap component with alarm settings
        """
        from components.component_registry import ComponentType
        from components.ai import BasicMonster
        
        state = self.state_manager.state
        if not hasattr(state, 'entities'):
            return
        
        # Find nearby monsters of matching faction
        faction_to_alert = trap.alarm_faction
        radius = trap.alarm_radius
        
        alerted_count = 0
        for entity in state.entities:
            if entity == player:
                continue
            
            # Check distance
            distance = player.distance(entity.x, entity.y)
            if distance > radius:
                continue
            
            # Check if entity has faction and AI
            faction = entity.components.get(ComponentType.FACTION)
            ai = entity.components.get(ComponentType.AI)
            
            if faction and faction.faction == faction_to_alert and ai:
                # Alert this mob
                if hasattr(ai, 'alert_location'):
                    ai.alert_location(player.x, player.y)
                    alerted_count += 1
                elif hasattr(ai, 'set_target'):
                    ai.set_target(player)
                    alerted_count += 1
        
        if alerted_count > 0:
            logger.info(f"Alarm trap: alerted {alerted_count} {faction_to_alert}(s)")
    
    def _find_door_at_location(self, entities: List['Entity'], x: int, y: int) -> Optional['Entity']:
        """Find a door entity at the given location.
        
        Args:
            entities: List of entities
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Door entity if found, None otherwise
        """
        from components.component_registry import ComponentType
        
        for entity in entities:
            if entity.x == x and entity.y == y and entity.components.has(ComponentType.DOOR):
                return entity
        return None
    
    @dataclass
    class DoorResult:
        """Result of attempting to open/unlock a door."""
        success: bool = False
        messages: List[Dict[str, Any]] = None
        
        def __post_init__(self):
            if self.messages is None:
                self.messages = []
    
    def _handle_door_bump(self, player: 'Entity', door_entity: 'Entity', movement_result: 'MovementResult') -> 'DoorResult':
        """Handle player bumping into a door.
        
        Attempts to open/unlock the door based on its state and player's inventory.
        
        Args:
            player: Player entity
            door_entity: Door entity being bumped into
            movement_result: Current movement result (for context)
            
        Returns:
            DoorResult indicating success/failure and messages
        """
        from components.component_registry import ComponentType
        from message_builder import MessageBuilder as MB
        
        door_result = self.DoorResult()
        door = door_entity.components.get(ComponentType.DOOR)
        
        if not door:
            logger.error(f"Door entity at ({door_entity.x}, {door_entity.y}) has no Door component")
            return door_result
        
        # If door is already open, allow passage
        if not door.is_closed:
            door_result.success = True
            return door_result
        
        # If door is secret and undiscovered, treat as wall
        if door.is_secret and not door.is_discovered:
            door_result.messages.append(MB.warning("You bump into a solid wall."))
            logger.debug(f"Bumped into undiscovered secret door at ({door_entity.x}, {door_entity.y})")
            return door_result
        
        # Door is closed - try to open/unlock
        if door.is_locked:
            # Check for key in player inventory
            # Keys can be matched by:
            # 1. Entity ID (e.g., "iron_key")
            # 2. key_type attribute (e.g., key_type="iron")
            # 3. Item name normalized (e.g., "Iron Key" → "iron_key")
            key_found = False
            matching_key = None
            
            if player.components.has(ComponentType.INVENTORY):
                inventory = player.inventory
                
                # Debug: Log all keys in inventory
                keys_in_inventory = []
                for item in inventory.items:
                    if hasattr(item, 'key_type') or 'key' in item.name.lower():
                        keys_in_inventory.append(f"{item.name} (id:{getattr(item, 'entity_id', '?')}, key_type:{getattr(item, 'key_type', '?')})")
                
                if keys_in_inventory:
                    logger.debug(f"Keys in inventory: {keys_in_inventory}")
                    print(f"[KEY DEBUG] Looking for '{door.key_tag}' in inventory with keys: {keys_in_inventory}")
                
                for item in inventory.items:
                    # Try multiple matching strategies
                    item_matches = False
                    
                    # Strategy 1: Match by entity_id
                    if hasattr(item, 'entity_id') and item.entity_id == door.key_tag:
                        item_matches = True
                        logger.debug(f"Matched by entity_id: {item.entity_id} == {door.key_tag}")
                    
                    # Strategy 2: Match by key_type attribute  
                    elif hasattr(item, 'key_type'):
                        # door.key_tag might be "iron_key", item.key_type might be "iron"
                        # Check if key_type matches any part of key_tag
                        if item.key_type in door.key_tag or door.key_tag.replace('_key', '') == item.key_type:
                            item_matches = True
                            logger.debug(f"Matched by key_type: {item.key_type} matches {door.key_tag}")
                    
                    # Strategy 3: Match by normalized item name
                    elif hasattr(item, 'name'):
                        item_name_normalized = item.name.lower().replace(' ', '_')
                        if item_name_normalized == door.key_tag:
                            item_matches = True
                            logger.debug(f"Matched by name: {item_name_normalized} == {door.key_tag}")
                    
                    if item_matches:
                        key_found = True
                        matching_key = item
                        logger.info(f"Found matching key: {item.name} for door requiring {door.key_tag}")
                        break
            
            if not key_found:
                door_result.messages.append(MB.warning(f"The door is locked. (Need: {door.key_tag})"))
                logger.debug(f"Player tried to open locked door but no {door.key_tag} in inventory")
                print(f"[KEY DEBUG] NO MATCH FOUND for '{door.key_tag}'")
                return door_result
            
            # Player has key - unlock and open
            door.unlock()
            door.open()
            door_entity.char = '/'  # Open door glyph
            door_entity.color = (200, 180, 100)  # Lighter brown for open
            door_entity.blocks = False  # Allow passage through open door
            door_result.messages.append(MB.success(f"You unlock and open the door!"))
            logger.info(f"Player unlocked door at ({door_entity.x}, {door_entity.y}) with {door.key_tag}")
            door_result.success = True
            return door_result
        else:
            # Door is unlocked - just open it
            door.open()
            door_entity.char = '/'  # Open door glyph
            door_entity.color = (200, 180, 100)  # Lighter brown for open
            door_entity.blocks = False  # Allow passage through open door
            door_result.messages.append(MB.success("You open the door."))
            logger.debug(f"Player opened door at ({door_entity.x}, {door_entity.y})")
            door_result.success = True
            return door_result


# Singleton instance
_movement_service = None


def get_movement_service(state_manager: Any = None) -> 'MovementService':
    """Get the global movement service instance.

    Args:
        state_manager: State manager (required on first call)

    Returns:
        MovementService instance
    """
    global _movement_service
    if _movement_service is None:
        if state_manager is None:
            raise ValueError("state_manager required to initialize MovementService")
        _movement_service = MovementService(state_manager)
    return _movement_service


def reset_movement_service() -> None:
    """Reset the global movement service instance (for testing)."""
    global _movement_service
    _movement_service = None

