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
from typing import Tuple, Dict, Any, Optional, List
from dataclasses import dataclass

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
        print(f">>> MovementService: ({player.x}, {player.y}) -> ({dest_x}, {dest_y}) via {source}, state={current_state}")

        # Check for immobilized status effect
        from components.component_registry import ComponentType
        if player.components.has(ComponentType.STATUS_EFFECTS):
            status_effects = player.status_effects
            if status_effects and status_effects.has_effect("immobilized"):
                result.blocked_by_status = True
                result.messages.append(MB.warning("You are stuck in place and cannot move!"))
                logger.debug("Movement blocked by immobilized status effect")
                return result

        # Check for wall/blocked tile
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
        result.new_position = (player.x, player.y)
        result.fov_recompute = True
        
        logger.info(f"Player moved: {old_pos} -> {result.new_position} via {source}")
        print(f">>> MovementService: Player moved to {result.new_position}")
        
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

        portal_entity = self._check_portal_entry(player, entities)
        if portal_entity:
            print(f">>> MovementService: PORTAL ENTRY DETECTED at {result.new_position}!")
            logger.info(f"=== MOVEMENT_SERVICE: PORTAL ENTRY DETECTED!")

            # Only trigger confrontation if player has obtained Ruby Heart
            player_has_ruby_heart = (hasattr(player, 'victory') and
                                   player.victory and
                                   player.victory.has_ruby_heart)

            if player_has_ruby_heart:
                # Check if confrontation has already started (prevent multiple boss spawns)
                confrontation_already_started = (hasattr(player, 'victory') and
                                               player.victory and
                                               player.victory.confrontation_started)

                if confrontation_already_started:
                    # Player has already entered the portal - just move them
                    logger.debug("Portal entry: confrontation already started, allowing movement")
                    result.messages.append({"message": MB.info("You step through the portal once more...")})
                else:
                    # First time entering portal - trigger confrontation
                    result.portal_entry = True
                    result.messages.append({"message": MB.item_effect("You step through the portal...")})
                    result.messages.append({"message": MB.warning("Reality twists around you!")})

                    # Mark confrontation started on player
                    player.victory.start_confrontation()
                    logger.debug("Victory component: confrontation started")
            else:
                # Portal exists but doesn't trigger confrontation yet
                logger.debug("Portal found but player hasn't obtained Ruby Heart")
                result.messages.append({"message": MB.info("The portal hums with otherworldly energy, but nothing happens...")})
        else:
            logger.debug("Portal entry check: no portal at player position")
        
        # Check for passive secret door reveals
        self._check_secret_reveals(player, game_map)
        
        return result
    
    def _check_portal_entry(self, player, entities) -> Optional['Entity']:
        """Check if player is standing on a portal.
        
        Args:
            player: Player entity
            entities: List of all entities
            
        Returns:
            Portal entity if player is on it, None otherwise
        """
        portal_count = 0
        portal_entity = None
        
        for entity in entities:
            if hasattr(entity, 'is_portal') and entity.is_portal:
                portal_count += 1
                logger.debug(f"Found portal at ({entity.x}, {entity.y})")
                print(f">>> MovementService: Found portal at ({entity.x}, {entity.y})")
                
                if entity.x == player.x and entity.y == player.y:
                    logger.info(f"Player on portal at ({entity.x}, {entity.y})")
                    print(f">>> MovementService: Player IS on portal!")
                    portal_entity = entity
        
        if portal_count == 0:
            logger.warning("No portals found in entities list!")
            print(f">>> MovementService: WARNING - No portals in entities list!")
        elif portal_entity is None:
            logger.debug(f"Portals exist ({portal_count}) but player not on any")
            print(f">>> MovementService: {portal_count} portal(s) exist, but player not on one")
        
        return portal_entity
    
    def _check_secret_reveals(self, player, game_map):
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


# Singleton instance
_movement_service = None


def get_movement_service(state_manager=None):
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


def reset_movement_service():
    """Reset the global movement service instance (for testing)."""
    global _movement_service
    _movement_service = None

