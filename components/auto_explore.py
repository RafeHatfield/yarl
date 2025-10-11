"""Auto-exploration component for systematic dungeon discovery.

This module provides automated dungeon exploration functionality, allowing
the player to efficiently map unexplored areas with a single command. It
serves as a foundation for future auto-play features.

Architecture:
- AutoExplore: Component for managing automated exploration state
- Uses Dijkstra pathfinding to find optimal exploration paths
- Room-by-room exploration (finishes current room before moving to next)
- Avoids ground hazards (treats them as impassable)
- Stops on threats (monsters, items, traps, damage, etc.)

Design Decisions:
- One tile per turn (animated, not instant) for player control
- Extensible for future auto-play (auto-combat, auto-loot)
- Treats hazards as walls to ensure safe exploration
- Clear stop messages so player knows why exploration halted
"""

import logging
import random
from typing import List, Tuple, Optional, Set, TYPE_CHECKING
from collections import deque
import heapq

from map_objects.rectangle import Rect

if TYPE_CHECKING:
    from entity import Entity
    from map_objects.game_map import GameMap

logger = logging.getLogger(__name__)


# Pithy adventure quotes for starting auto-explore
ADVENTURE_QUOTES = [
    "Into the unknown!",
    "Adventure awaits!",
    "Fortune favors the bold!",
    "Let's see what's out there...",
    "Time to map this place out.",
    "Onward to glory!",
    "No stone left unturned!",
    "The dungeon calls...",
    "Let's find some treasure!",
    "Exploring the unexplored!",
    "Into the depths we go!",
    "What secrets await?",
    "Boldly pressing forward!",
    "The map won't draw itself!",
    "Adventure is out there!",
    "Mapping the mysteries!",
    "Seeking the unseen!",
    "Charting new territory!",
]


class AutoExplore:
    """Component for automated dungeon exploration.
    
    Manages systematic exploration of the dungeon using intelligent pathfinding.
    Explores room-by-room, avoiding hazards, and stops when threats are detected.
    Designed to be extensible for future auto-play features (combat, looting).
    
    Attributes:
        owner (Entity): The player entity that owns this component
        active (bool): Whether auto-explore is currently running
        current_path (List[Tuple[int, int]]): Current path being followed
        current_room (Optional[Rect]): Room currently being explored
        stop_reason (Optional[str]): Human-readable reason for stopping
        last_hp (int): Player HP at last turn check (for damage detection)
        target_tile (Optional[Tuple[int, int]]): Current exploration target
    
    Example:
        >>> auto_explore = AutoExplore()
        >>> auto_explore.owner = player
        >>> quote = auto_explore.start(game_map, entities)
        >>> print(quote)  # "Into the unknown!"
        >>> 
        >>> # Each turn:
        >>> action = auto_explore.get_next_action(game_map, entities, fov_map)
        >>> if action is None:
        >>>     print(f"Stopped: {auto_explore.stop_reason}")
    """
    
    def __init__(self):
        """Initialize the auto-explore component."""
        self.owner: Optional['Entity'] = None
        self.active: bool = False
        self.current_path: List[Tuple[int, int]] = []
        self.current_room: Optional[Rect] = None
        self.stop_reason: Optional[str] = None
        self.last_hp: int = 0
        self.target_tile: Optional[Tuple[int, int]] = None
    
    def start(self, game_map: 'GameMap', entities: List['Entity']) -> str:
        """Begin auto-exploring the dungeon.
        
        Initializes exploration state and returns a random adventure quote
        for the player.
        
        Args:
            game_map: Current dungeon level
            entities: All entities on the map
            
        Returns:
            str: Random pithy adventure quote
        """
        if not self.owner:
            logger.error("AutoExplore component has no owner")
            return "Error: No owner"
        
        self.active = True
        self.current_path = []
        self.current_room = None
        self.stop_reason = None
        self.target_tile = None
        
        # Store initial HP for damage detection
        if hasattr(self.owner, 'fighter') and self.owner.fighter:
            self.last_hp = self.owner.fighter.hp
        else:
            self.last_hp = 0
        
        logger.info(f"Auto-explore started for {self.owner.name}")
        return random.choice(ADVENTURE_QUOTES)
    
    def stop(self, reason: str) -> None:
        """Stop auto-exploring.
        
        Args:
            reason: Human-readable explanation for why exploration stopped
        """
        self.active = False
        self.stop_reason = reason
        self.current_path = []
        self.target_tile = None
        logger.info(f"Auto-explore stopped: {reason}")
    
    def is_active(self) -> bool:
        """Check if auto-explore is currently running.
        
        Returns:
            bool: True if actively exploring
        """
        return self.active
    
    def get_next_action(
        self,
        game_map: 'GameMap',
        entities: List['Entity'],
        fov_map
    ) -> Optional[dict]:
        """Calculate the next move for auto-exploration.
        
        This is called once per turn when auto-explore is active. It:
        1. Checks stop conditions (threats, completion, etc.)
        2. Follows current path if available
        3. Finds next unexplored tile if path exhausted
        4. Returns movement action or None if stopped
        
        Args:
            game_map: Current game map
            entities: All entities on the map
            fov_map: Field-of-view map for visibility checks
            
        Returns:
            dict: Action dict with 'dx' and 'dy' keys for movement,
                  or None if auto-explore should stop
        """
        if not self.active or not self.owner:
            return None
        
        # Check stop conditions (implemented in Slice 2)
        # For now, just basic completion check
        
        # If we have a current path, follow it
        if self.current_path:
            next_pos = self.current_path.pop(0)
            dx = next_pos[0] - self.owner.x
            dy = next_pos[1] - self.owner.y
            return {'dx': dx, 'dy': dy}
        
        # Need to find a new target
        next_target = self._find_next_unexplored_tile(game_map)
        
        if next_target is None:
            # No more unexplored tiles reachable
            self.stop("All areas explored")
            return None
        
        # Calculate path to target
        self.target_tile = next_target
        self.current_path = self._calculate_path_to(next_target, game_map, entities)
        
        if not self.current_path:
            # No path found
            self.stop("Cannot reach unexplored areas")
            return None
        
        # Follow the path
        next_pos = self.current_path.pop(0)
        dx = next_pos[0] - self.owner.x
        dy = next_pos[1] - self.owner.y
        return {'dx': dx, 'dy': dy}
    
    def _find_next_unexplored_tile(self, game_map: 'GameMap') -> Optional[Tuple[int, int]]:
        """Find the nearest unexplored tile using room-by-room priority.
        
        Strategy:
        1. Identify current room (if any)
        2. Find unexplored tiles in current room
        3. If room complete, find nearest unexplored tile in any room
        4. Use Dijkstra to find closest reachable unexplored tile
        
        Args:
            game_map: Game map with tile data
            
        Returns:
            (x, y): Coordinates of next tile to explore, or None if all explored
        """
        if not self.owner:
            return None
        
        # Identify current room
        self.current_room = self._identify_current_room(game_map)
        
        # If in a room, prioritize finishing it
        if self.current_room:
            room_unexplored = self._get_unexplored_tiles_in_room(
                self.current_room, game_map
            )
            if room_unexplored:
                # Find closest unexplored tile in current room
                return self._find_closest_tile(room_unexplored, game_map)
        
        # Either not in a room, or current room is done
        # Find any unexplored tile
        all_unexplored = self._get_all_unexplored_tiles(game_map)
        
        if not all_unexplored:
            return None  # Map fully explored!
        
        # Find closest reachable unexplored tile
        return self._find_closest_tile(all_unexplored, game_map)
    
    def _identify_current_room(self, game_map: 'GameMap') -> Optional[Rect]:
        """Identify which room the player is currently in.
        
        Scans nearby tiles to find room boundaries. Rooms are defined as
        contiguous open areas surrounded by walls.
        
        Args:
            game_map: Game map with tile data
            
        Returns:
            Rect: Room boundaries if in a room, None if in hallway
        """
        if not self.owner:
            return None
        
        px, py = self.owner.x, self.owner.y
        
        # Flood fill from player position to find room bounds
        visited = set()
        queue = deque([(px, py)])
        room_tiles = []
        
        while queue and len(visited) < 100:  # Limit search to reasonable room size
            x, y = queue.popleft()
            
            if (x, y) in visited:
                continue
            
            if not (0 <= x < game_map.width and 0 <= y < game_map.height):
                continue
            
            # Check if tile is walkable
            if game_map.tiles[x][y].blocked:
                continue
            
            visited.add((x, y))
            room_tiles.append((x, y))
            
            # Add neighbors
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                queue.append((x + dx, y + dy))
        
        if len(room_tiles) < 9:  # Too small to be a room (min 3x3)
            return None
        
        # Calculate bounding box
        if not room_tiles:
            return None
        
        xs = [x for x, y in room_tiles]
        ys = [y for x, y in room_tiles]
        
        x1, x2 = min(xs), max(xs)
        y1, y2 = min(ys), max(ys)
        
        # Create Rect (note: Rect uses width/height, not x2/y2)
        return Rect(x1, y1, x2 - x1, y2 - y1)
    
    def _get_unexplored_tiles_in_room(
        self, room: Rect, game_map: 'GameMap'
    ) -> List[Tuple[int, int]]:
        """Get all unexplored walkable tiles in a room.
        
        Args:
            room: Room boundaries
            game_map: Game map with tile data
            
        Returns:
            List of (x, y) tuples for unexplored tiles
        """
        unexplored = []
        
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                if not (0 <= x < game_map.width and 0 <= y < game_map.height):
                    continue
                
                tile = game_map.tiles[x][y]
                
                # Must be walkable and not yet explored
                if not tile.blocked and not tile.explored:
                    # Also check for hazards (treat as blocked)
                    if not game_map.hazard_manager.has_hazard_at(x, y):
                        unexplored.append((x, y))
        
        return unexplored
    
    def _get_all_unexplored_tiles(self, game_map: 'GameMap') -> List[Tuple[int, int]]:
        """Get all unexplored walkable tiles on the map.
        
        Args:
            game_map: Game map with tile data
            
        Returns:
            List of (x, y) tuples for unexplored tiles
        """
        unexplored = []
        
        for x in range(game_map.width):
            for y in range(game_map.height):
                tile = game_map.tiles[x][y]
                
                # Must be walkable and not yet explored
                if not tile.blocked and not tile.explored:
                    # Also check for hazards (treat as blocked)
                    if not game_map.hazard_manager.has_hazard_at(x, y):
                        unexplored.append((x, y))
        
        return unexplored
    
    def _find_closest_tile(
        self, tiles: List[Tuple[int, int]], game_map: 'GameMap'
    ) -> Optional[Tuple[int, int]]:
        """Find the closest reachable tile from the list using Dijkstra.
        
        Args:
            tiles: List of candidate tiles
            game_map: Game map for pathfinding
            
        Returns:
            (x, y): Closest reachable tile, or None if none reachable
        """
        if not self.owner or not tiles:
            return None
        
        # Use Dijkstra to find closest tile
        # Priority queue: (distance, (x, y))
        start = (self.owner.x, self.owner.y)
        pq = [(0, start)]
        visited = set()
        distances = {start: 0}
        target_tiles = set(tiles)
        
        while pq:
            dist, pos = heapq.heappop(pq)
            
            if pos in visited:
                continue
            
            visited.add(pos)
            
            # Check if we reached a target
            if pos in target_tiles:
                return pos
            
            x, y = pos
            
            # Check neighbors
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                neighbor = (nx, ny)
                
                # Check bounds
                if not (0 <= nx < game_map.width and 0 <= ny < game_map.height):
                    continue
                
                # Check if walkable
                if game_map.tiles[nx][ny].blocked:
                    continue
                
                # Check for hazards (treat as blocked)
                if game_map.hazard_manager.has_hazard_at(nx, ny):
                    continue
                
                # Calculate new distance
                new_dist = dist + 1
                
                if neighbor not in distances or new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    heapq.heappush(pq, (new_dist, neighbor))
        
        # No reachable target found
        return None
    
    def _calculate_path_to(
        self,
        target: Tuple[int, int],
        game_map: 'GameMap',
        entities: List['Entity']
    ) -> List[Tuple[int, int]]:
        """Calculate A* path to target, avoiding hazards.
        
        Args:
            target: (x, y) destination
            game_map: Game map for pathfinding
            entities: All entities (for collision detection)
            
        Returns:
            List of (x, y) positions to visit (excluding start position)
        """
        if not self.owner:
            return []
        
        # Use A* pathfinding with hazard avoidance
        import tcod
        
        # Create cost map
        cost = [[0 for _ in range(game_map.height)] for _ in range(game_map.width)]
        
        for x in range(game_map.width):
            for y in range(game_map.height):
                # Blocked tiles are impassable
                if game_map.tiles[x][y].blocked:
                    cost[x][y] = 0
                # Hazards are treated as impassable
                elif game_map.hazard_manager.has_hazard_at(x, y):
                    cost[x][y] = 0
                else:
                    cost[x][y] = 1
        
        # Entities block movement (except target tile)
        for entity in entities:
            if entity.blocks and entity != self.owner:
                ex, ey = entity.x, entity.y
                if 0 <= ex < game_map.width and 0 <= ey < game_map.height:
                    if (ex, ey) != target:  # Allow moving to target even if entity there
                        cost[ex][ey] = 0
        
        # Convert to numpy array for tcod
        import numpy as np
        cost_array = np.array(cost, dtype=np.int8).T  # Transpose for tcod
        
        # Create pathfinder
        pathfinder = tcod.path.Pathfinder(cost_array)
        pathfinder.add_root((self.owner.x, self.owner.y))
        
        # Find path
        path = pathfinder.path_to((target[0], target[1]))
        
        # Convert to list of tuples (excluding start position)
        return [(x, y) for x, y in path[1:]]

