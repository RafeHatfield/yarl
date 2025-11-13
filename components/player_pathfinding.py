"""Player pathfinding component for mouse-driven movement.

This component manages multi-step pathfinding for the player, allowing
click-to-move functionality with automatic turn progression until the
destination is reached or movement is interrupted.
"""

import math
from typing import List, Tuple, Optional, TYPE_CHECKING
import logging

import tcod
import tcod.libtcodpy as libtcodpy

from config.game_constants import get_pathfinding_config
from fov_functions import map_is_in_fov
from game_messages import Message

if TYPE_CHECKING:
    from map_objects.game_map import GameMap

logger = logging.getLogger(__name__)


class PlayerPathfinding:
    """Component for managing player pathfinding and continuous movement.
    
    This component handles click-to-move functionality by:
    - Computing A* paths to clicked destinations
    - Managing multi-step movement across turns
    - Detecting movement interruptions (enemies in FOV)
    - Providing movement status and feedback
    
    Attributes:
        owner (Entity): The player entity that owns this component
        current_path (List[Tuple[int, int]]): Current path being followed
        destination (Tuple[int, int]): Final destination coordinates
        path_index (int): Current position in the path
        is_moving (bool): Whether player is currently following a path
        movement_interrupted (bool): Whether movement was stopped by enemy detection
    """
    
    def __init__(self):
        """Initialize the player pathfinding component."""
        self.owner: Optional['Entity'] = None
        self.current_path: List[Tuple[int, int]] = []
        self.destination: Optional[Tuple[int, int]] = None
        self.path_index: int = 0
        self.is_moving: bool = False
        self.movement_interrupted: bool = False
        
        # Movement statistics for debugging
        self.total_moves_planned: int = 0
        self.total_moves_completed: int = 0
        self.interruption_count: int = 0
        
        # Auto-pickup for double-click pathfinding
        self.auto_pickup_target: Optional['Entity'] = None
        
        # Auto-open for chest pathfinding
        self.auto_open_target: Optional['Entity'] = None
        
        # Auto-read for mural pathfinding
        self.auto_read_target: Optional['Entity'] = None
    
    def set_destination(self, x: int, y: int, game_map: 'GameMap', entities: List['Entity'], 
                        fov_map=None) -> bool:
        """Set a new destination and compute the path.
        
        Args:
            x (int): Target x coordinate
            y (int): Target y coordinate
            game_map (GameMap): The game map for pathfinding
            entities (List[Entity]): List of entities for collision detection
            fov_map: Optional FOV map to determine if destination is visible
            
        Returns:
            bool: True if a valid path was found, False otherwise
        """
        if not self.owner:
            logger.error("PlayerPathfinding component has no owner")
            return False
        
        # Validate destination
        if not self._is_valid_destination(x, y, game_map):
            logger.debug(f"Invalid destination: ({x}, {y})")
            return False
        
        # Don't pathfind if already at destination
        if self.owner.x == x and self.owner.y == y:
            logger.debug("Already at destination")
            return False
        
        # Compute path using A* (with FOV awareness for smart limits)
        path = self._compute_path(x, y, game_map, entities, fov_map)
        if not path:
            logger.debug(f"No path found to ({x}, {y})")
            return False
        
        # Set up movement state
        self.current_path = path
        self.destination = (x, y)
        self.path_index = 0
        self.is_moving = True
        self.movement_interrupted = False
        self.total_moves_planned = len(path)
        
        logger.debug(f"Path set to ({x}, {y}) with {len(path)} steps")
        return True
    
    def get_next_move(self) -> Optional[Tuple[int, int]]:
        """Get the next move in the current path.
        
        Returns:
            Tuple[int, int]: Next (x, y) coordinates, or None if no move available
        """
        if not self.is_moving or not self.current_path:
            return None
        
        if self.path_index >= len(self.current_path):
            # Path completed
            self._complete_movement()
            return None
        
        next_pos = self.current_path[self.path_index]
        self.path_index += 1
        self.total_moves_completed += 1
        
        # Check if this was the last step
        if self.path_index >= len(self.current_path):
            self._complete_movement()
        
        return next_pos
    
    def interrupt_movement(self, reason: str = "Enemy spotted") -> None:
        """Interrupt the current movement.
        
        Args:
            reason (str): Reason for interruption (for logging/messaging)
        """
        if self.is_moving:
            self.is_moving = False
            self.movement_interrupted = True
            self.interruption_count += 1
            self.auto_pickup_target = None  # Clear auto-pickup on interrupt
            self.auto_open_target = None  # Clear auto-open on interrupt
            logger.debug(f"Movement interrupted: {reason}")
    
    def cancel_movement(self) -> None:
        """Cancel the current movement entirely."""
        self.is_moving = False
        self.current_path.clear()
        self.destination = None
        self.path_index = 0
        self.movement_interrupted = False
        self.auto_pickup_target = None  # Clear auto-pickup on cancel
        self.auto_open_target = None  # Clear auto-open on cancel
        logger.debug("Movement cancelled")
    
    def is_path_active(self) -> bool:
        """Check if player is currently following a path.
        
        Returns:
            bool: True if actively moving along a path
        """
        return self.is_moving and bool(self.current_path)
    
    def get_remaining_steps(self) -> int:
        """Get number of steps remaining in current path.
        
        Returns:
            int: Number of steps left, 0 if no active path
        """
        if not self.is_moving or not self.current_path:
            return 0
        return len(self.current_path) - self.path_index
    
    def get_movement_stats(self) -> dict:
        """Get movement statistics for debugging.
        
        Returns:
            dict: Dictionary containing movement statistics
        """
        return {
            'is_moving': self.is_moving,
            'current_path_length': len(self.current_path),
            'path_index': self.path_index,
            'remaining_steps': self.get_remaining_steps(),
            'destination': self.destination,
            'movement_interrupted': self.movement_interrupted,
            'total_moves_planned': self.total_moves_planned,
            'total_moves_completed': self.total_moves_completed,
            'interruption_count': self.interruption_count,
        }
    
    def _is_valid_destination(self, x: int, y: int, game_map: 'GameMap') -> bool:
        """Check if destination coordinates are valid for pathfinding.
        
        A valid destination must be:
        1. Within map bounds
        2. Not blocked (walkable)
        3. Explored by the player (visible or previously seen)
        
        This allows players to click on any explored tile to automatically
        pathfind there, enabling quick travel across previously-explored areas.
        
        Args:
            x (int): Target x coordinate
            y (int): Target y coordinate
            game_map (GameMap): The game map
            
        Returns:
            bool: True if destination is valid (walkable and explored)
        """
        # Check bounds
        if x < 0 or y < 0 or x >= game_map.width or y >= game_map.height:
            return False
        
        # Check if tile is walkable
        if game_map.is_blocked(x, y):
            return False
        
        # Check if tile has been explored by the player
        # This allows pathfinding to anywhere the player has previously visited
        if not game_map.tiles[x][y].explored:
            return False
        
        return True
    
    def _compute_path(self, target_x: int, target_y: int, game_map: 'GameMap', 
                     entities: List['Entity'], fov_map=None) -> List[Tuple[int, int]]:
        """Compute A* path to target coordinates.
        
        Args:
            target_x (int): Target x coordinate
            target_y (int): Target y coordinate
            game_map (GameMap): The game map for pathfinding
            entities (List[Entity]): List of entities for collision detection
            fov_map: Optional FOV map to determine if destination is visible
            
        Returns:
            List[Tuple[int, int]]: List of (x, y) coordinates forming the path
        """
        if not self.owner:
            return []
        
        # Create a FOV map that has the dimensions of the map
        # Note: tcod.map.Map is deprecated but still functional. Migration to numpy
        # arrays would require significant refactoring of pathfinding logic.
        import warnings
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=DeprecationWarning)
            fov = tcod.map.Map(game_map.width, game_map.height)
        
        # Scan the current map each turn and set all the walls as unwalkable
        for y1 in range(game_map.height):
            for x1 in range(game_map.width):
                fov.transparent[y1, x1] = not game_map.tiles[x1][y1].block_sight
                fov.walkable[y1, x1] = not game_map.tiles[x1][y1].blocked
        
        # Scan all the objects to see if there are objects that must be
        # navigated around. Don't block the destination tile even if there's an entity there
        for entity in entities:
            if (entity.blocks and entity != self.owner and 
                not (entity.x == target_x and entity.y == target_y)):
                # Set the tile as a wall so it must be navigated around
                fov.transparent[entity.y, entity.x] = True
                fov.walkable[entity.y, entity.x] = False
        
        # Get pathfinding configuration
        pathfinding_config = get_pathfinding_config()
        
        # Determine max path length based on tile visibility and exploration status
        destination_in_fov = False
        destination_explored = game_map.tiles[target_x][target_y].explored
        
        if fov_map is not None:
            try:
                destination_in_fov = map_is_in_fov(fov_map, target_x, target_y)
            except (AttributeError, TypeError):
                # FOV map might be None or invalid, fall back to conservative limit
                pass
        
        # Choose appropriate path length limit:
        # - Visible tiles: 40 steps (short, player can see it)
        # - Explored tiles: 150 steps (long, player has been there before)
        # - Unexplored tiles: 25 steps (conservative, shouldn't reach here due to validation)
        if destination_in_fov:
            max_path_length = pathfinding_config.MAX_PATH_LENGTH_IN_FOV
        elif destination_explored:
            max_path_length = pathfinding_config.MAX_PATH_LENGTH_EXPLORED
        else:
            max_path_length = pathfinding_config.MAX_PATH_LENGTH_OUT_FOV
        
        logger.debug(f"Computing path to ({target_x}, {target_y}), in_fov={destination_in_fov}, "
                    f"max_length={max_path_length}")
        
        # Allocate a A* path
        my_path = libtcodpy.path_new_using_map(fov, pathfinding_config.DIAGONAL_MOVE_COST)
        
        try:
            # Compute the path between player's coordinates and the target coordinates
            libtcodpy.path_compute(my_path, self.owner.x, self.owner.y, target_x, target_y)
            
            # Check if the path exists and is reasonable length
            if (libtcodpy.path_is_empty(my_path) or 
                libtcodpy.path_size(my_path) >= max_path_length):
                return []
            
            # Extract the path coordinates
            path = []
            while not libtcodpy.path_is_empty(my_path):
                x, y = libtcodpy.path_walk(my_path, True)
                if x is not None and y is not None:
                    path.append((x, y))
                else:
                    break
            
            return path
            
        finally:
            # Path objects are automatically deleted by libtcod (no manual cleanup needed)
            pass
    
    def _complete_movement(self) -> None:
        """Complete the current movement and clean up state."""
        self.is_moving = False
        self.current_path.clear()
        self.destination = None
        self.path_index = 0
        logger.debug("Movement completed successfully")
