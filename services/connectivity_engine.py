"""Dungeon connectivity engine for MST and loop-based corridor generation.

This module provides:
- MST (Minimum Spanning Tree) pathfinding for baseline connectivity
- Loop generation for additional connections
- Multiple corridor digging styles (orthogonal, jagged, organic)
- Door placement at regular intervals
"""

from typing import List, Dict, Tuple, Set, Optional
from dataclasses import dataclass
from random import randint, random, choice, sample
from logger_config import get_logger
import math

logger = get_logger(__name__)


@dataclass
class MSTPair:
    """Connection between two rooms for MST."""
    room_a_idx: int
    room_b_idx: int
    distance: float


class UnionFind:
    """Union-Find (Disjoint Set) data structure for MST detection."""
    
    def __init__(self, n: int):
        """Initialize with n elements."""
        self.parent = list(range(n))
        self.rank = [0] * n
    
    def find(self, x: int) -> int:
        """Find the root of element x with path compression."""
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]
    
    def union(self, x: int, y: int) -> bool:
        """Union two sets. Returns True if they were in different sets."""
        root_x = self.find(x)
        root_y = self.find(y)
        
        if root_x == root_y:
            return False
        
        # Union by rank
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1
        
        return True


class ConnectivityEngine:
    """Engine for generating dungeon connectivity patterns."""
    
    def __init__(self):
        """Initialize connectivity engine."""
        self.connections: List[Tuple[int, int]] = []
        self.loops: List[Tuple[int, int]] = []
    
    def compute_mst_paths(self, rooms: List) -> List[Tuple[int, int]]:
        """Compute minimum spanning tree connections between rooms.
        
        Uses Kruskal's algorithm with Union-Find to create minimal connections
        that ensure all rooms are reachable.
        
        Args:
            rooms: List of room objects with x, y, x1, y1, x2, y2 attributes
            
        Returns:
            List of (room_a_idx, room_b_idx) tuples representing connections
        """
        if len(rooms) <= 1:
            return []
        
        # Calculate all pairwise distances
        edges = []
        for i in range(len(rooms)):
            for j in range(i + 1, len(rooms)):
                room_a = rooms[i]
                room_b = rooms[j]
                
                # Distance between room centers
                center_a = (room_a.center()[0], room_a.center()[1])
                center_b = (room_b.center()[0], room_b.center()[1])
                
                distance = math.sqrt(
                    (center_a[0] - center_b[0]) ** 2 +
                    (center_a[1] - center_b[1]) ** 2
                )
                
                edges.append((distance, i, j))
        
        # Sort edges by distance (Kruskal's algorithm)
        edges.sort()
        
        # Apply Union-Find to build MST
        uf = UnionFind(len(rooms))
        mst_edges = []
        
        for distance, i, j in edges:
            if uf.union(i, j):
                mst_edges.append((i, j))
                logger.debug(f"MST edge: Room {i} <-> Room {j} (distance: {distance:.1f})")
                
                if len(mst_edges) == len(rooms) - 1:
                    break  # MST complete
        
        logger.info(f"MST complete: {len(mst_edges)} connections for {len(rooms)} rooms")
        self.connections = mst_edges
        return mst_edges
    
    def add_loop_connections(self, rooms: List, loop_count: int, 
                           existing_connections: Set[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Add additional random connections to create loops.
        
        Args:
            rooms: List of room objects
            loop_count: Number of loop connections to add
            existing_connections: Set of existing MST edges
            
        Returns:
            List of new (room_a_idx, room_b_idx) tuples for loop connections
        """
        if len(rooms) <= 2 or loop_count <= 0:
            return []
        
        # Build possible connections (not already connected)
        possible_connections = []
        for i in range(len(rooms)):
            for j in range(i + 1, len(rooms)):
                conn = tuple(sorted([i, j]))
                if conn not in existing_connections:
                    possible_connections.append(conn)
        
        if not possible_connections:
            logger.warning("No new connections possible for loops")
            return []
        
        # Select random connections for loops
        loop_count = min(loop_count, len(possible_connections))
        loop_edges = sample(possible_connections, loop_count)
        
        logger.info(f"Added {len(loop_edges)} loop connections")
        self.loops = loop_edges
        return loop_edges
    
    def dig_corridor(self, start: Tuple[int, int], end: Tuple[int, int], 
                    style: str = "orthogonal") -> List[Tuple[int, int]]:
        """Generate corridor tiles from start to end using specified style.
        
        Args:
            start: (x, y) starting position
            end: (x, y) ending position
            style: "orthogonal", "jagged", or "organic"
            
        Returns:
            List of (x, y) corridor tiles
        """
        if style == "orthogonal":
            return self._dig_orthogonal(start, end)
        elif style == "jagged":
            return self._dig_jagged(start, end)
        elif style == "organic":
            return self._dig_organic(start, end)
        else:
            return self._dig_orthogonal(start, end)  # Default
    
    def _dig_orthogonal(self, start: Tuple[int, int], end: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Dig straight corridors (orthogonal: H+V or V+H).
        
        Creates L-shaped corridors with 50% horizontal-first, 50% vertical-first.
        """
        tiles = []
        x1, y1 = start
        x2, y2 = end
        
        if random() > 0.5:
            # Horizontal first
            for x in range(min(x1, x2), max(x1, x2) + 1):
                tiles.append((x, y1))
            for y in range(min(y1, y2), max(y1, y2) + 1):
                tiles.append((x2, y))
        else:
            # Vertical first
            for y in range(min(y1, y2), max(y1, y2) + 1):
                tiles.append((x1, y))
            for x in range(min(x1, x2), max(x1, x2) + 1):
                tiles.append((x, y2))
        
        return tiles
    
    def _dig_jagged(self, start: Tuple[int, int], end: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Dig jagged corridors (random zigzag pattern).
        
        Creates corridors that randomly step between x and y, creating a jagged appearance.
        """
        tiles = []
        x, y = start
        x_end, y_end = end
        
        dx = 1 if x_end > x else -1
        dy = 1 if y_end > y else -1
        
        while x != x_end or y != y_end:
            tiles.append((x, y))
            
            # Decide whether to move x or y (weighted by remaining distance)
            x_dist = abs(x_end - x)
            y_dist = abs(y_end - y)
            
            if x_dist == 0:
                y += dy
            elif y_dist == 0:
                x += dx
            elif random() < (x_dist / (x_dist + y_dist)):
                x += dx
            else:
                y += dy
        
        tiles.append((x_end, y_end))
        return tiles
    
    def _dig_organic(self, start: Tuple[int, int], end: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Dig organic/winding corridors (smooth curves).
        
        Creates corridors that wind naturally, similar to hand-drawn paths.
        """
        tiles = []
        x, y = start
        x_end, y_end = end
        
        # Use Bresenham-like algorithm with some randomness
        dx = abs(x_end - x)
        dy = abs(y_end - y)
        sx = 1 if x_end > x else -1
        sy = 1 if y_end > y else -1
        
        err = (dx - dy) / 2.0
        turn_chance = 0.15  # Chance to take a "scenic route"
        
        while x != x_end or y != y_end:
            tiles.append((x, y))
            
            # Small chance to deviate for organic feel
            if random() < turn_chance and ((x != x_end and y != y_end)):
                if random() > 0.5:
                    x += sx
                else:
                    y += sy
            else:
                # Standard Bresenham step
                e2 = err
                if e2 > -dx:
                    err -= dy
                    x += sx
                if e2 < dy:
                    err += dx
                    y += sy
        
        tiles.append((x_end, y_end))
        return tiles
    
    def place_doors_on_corridor(self, corridor_tiles: List[Tuple[int, int]], 
                               every_n_tiles: int) -> List[Tuple[int, int]]:
        """Place doors at regular intervals along a corridor.
        
        Args:
            corridor_tiles: List of (x, y) corridor tiles
            every_n_tiles: Place doors every N tiles (0 = no placement)
            
        Returns:
            List of (x, y) positions where doors should be placed
        """
        if every_n_tiles <= 0 or len(corridor_tiles) < every_n_tiles:
            return []
        
        door_positions = []
        for i in range(every_n_tiles - 1, len(corridor_tiles), every_n_tiles):
            door_positions.append(corridor_tiles[i])
        
        logger.debug(f"Placed {len(door_positions)} doors on corridor (every {every_n_tiles} tiles)")
        return door_positions


# Global singleton
_connectivity_engine: Optional[ConnectivityEngine] = None


def get_connectivity_engine() -> ConnectivityEngine:
    """Get the global connectivity engine.
    
    Returns:
        ConnectivityEngine singleton instance
    """
    global _connectivity_engine
    if _connectivity_engine is None:
        _connectivity_engine = ConnectivityEngine()
    return _connectivity_engine


def reset_connectivity_engine() -> None:
    """Reset the global connectivity engine (for testing)."""
    global _connectivity_engine
    _connectivity_engine = None

