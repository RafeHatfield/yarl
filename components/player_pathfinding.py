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
from game_messages import Message

if TYPE_CHECKING:
    from entity import Entity
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
    
    def set_destination(self, x: int, y: int, game_map: 'GameMap', entities: List['Entity']) -> bool:
        """Set a new destination and compute the path.
        
        Args:
            x (int): Target x coordinate
            y (int): Target y coordinate
            game_map (GameMap): The game map for pathfinding
            entities (List[Entity]): List of entities for collision detection
            
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
        
        # Compute path using A*
        path = self._compute_path(x, y, game_map, entities)
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
            logger.debug(f"Movement interrupted: {reason}")
    
    def cancel_movement(self) -> None:
        """Cancel the current movement entirely."""
        self.is_moving = False
        self.current_path.clear()
        self.destination = None
        self.path_index = 0
        self.movement_interrupted = False
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
        """Check if destination coordinates are valid.
        
        Args:
            x (int): Target x coordinate
            y (int): Target y coordinate
            game_map (GameMap): The game map
            
        Returns:
            bool: True if destination is valid
        """
        # Check bounds
        if x < 0 or y < 0 or x >= game_map.width or y >= game_map.height:
            return False
        
        # Check if tile is walkable
        if game_map.is_blocked(x, y):
            return False
        
        return True
    
    def _compute_path(self, target_x: int, target_y: int, game_map: 'GameMap', 
                     entities: List['Entity']) -> List[Tuple[int, int]]:
        """Compute A* path to target coordinates.
        
        Args:
            target_x (int): Target x coordinate
            target_y (int): Target y coordinate
            game_map (GameMap): The game map for pathfinding
            entities (List[Entity]): List of entities for collision detection
            
        Returns:
            List[Tuple[int, int]]: List of (x, y) coordinates forming the path
        """
        if not self.owner:
            return []
        
        # Create a FOV map that has the dimensions of the map
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
        
        # Allocate a A* path
        my_path = libtcodpy.path_new_using_map(fov, pathfinding_config.DIAGONAL_MOVE_COST)
        
        try:
            # Compute the path between player's coordinates and the target coordinates
            libtcodpy.path_compute(my_path, self.owner.x, self.owner.y, target_x, target_y)
            
            # Check if the path exists and is reasonable length
            if (libtcodpy.path_is_empty(my_path) or 
                libtcodpy.path_size(my_path) >= pathfinding_config.MAX_PATH_LENGTH):
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
            # Always clean up the path to free memory
            libtcodpy.path_delete(my_path)
    
    def _complete_movement(self) -> None:
        """Complete the current movement and clean up state."""
        self.is_moving = False
        self.current_path.clear()
        self.destination = None
        self.path_index = 0
        logger.debug("Movement completed successfully")
