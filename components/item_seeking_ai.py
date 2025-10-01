"""Item-seeking AI component for monsters.

This module provides AI behavior for monsters that can seek out and pick up
items from the game world. It integrates with the existing AI system to add
item-seeking behavior while maintaining combat priorities.
"""

import logging
import math
from typing import List, Optional, Tuple, Any
from config.game_constants import get_monster_equipment_config

logger = logging.getLogger(__name__)


class ItemSeekingAI:
    """AI component that adds item-seeking behavior to monsters.
    
    This component works alongside existing AI to make monsters seek out
    and pick up items when appropriate, while maintaining combat priorities.
    """
    
    def __init__(self, monster, seek_distance: int = 5):
        """Initialize item-seeking AI.
        
        Args:
            monster: The monster entity this AI controls
            seek_distance: Maximum distance to seek items
        """
        self.monster = monster
        self.seek_distance = seek_distance
        self.config = get_monster_equipment_config()
        self.target_item = None  # Current item being sought
        self.last_player_distance = None  # Track player distance for comparison
        
    def get_item_seeking_action(self, game_map, entities, player) -> Optional[dict]:
        """Get an action for item seeking, if appropriate.
        
        Args:
            game_map: The current game map
            entities: List of all entities in the game
            player: The player entity
            
        Returns:
            dict: Action dictionary if item seeking should occur, None otherwise
        """
        # Only seek items if monster has inventory capability
        if not (hasattr(self.monster, 'inventory') and self.monster.inventory):
            return None
            
        # Only seek items if inventory has space
        if len(self.monster.inventory.items) >= self.monster.inventory.capacity:
            logger.debug(f"{self.monster.name} inventory full, not seeking items")
            return None
            
        # Only seek items if they're in FOV (monster can "see" them)
        if not self._is_in_fov(game_map):
            return None
            
        # Find nearby items
        nearby_items = self._find_nearby_items(entities)
        if not nearby_items:
            return None
            
        # Check if any item is closer than the player
        player_distance = self._calculate_distance(self.monster.x, self.monster.y, player.x, player.y)
        
        best_item = None
        best_distance = float('inf')
        
        for item, distance in nearby_items:
            # Item must be closer than player to be worth pursuing
            if distance < player_distance:
                if distance < best_distance:
                    best_item = item
                    best_distance = distance
                    
        if not best_item:
            logger.debug(f"{self.monster.name} found items but none closer than player (player: {player_distance:.1f})")
            return None
            
        # Move towards the best item
        self.target_item = best_item
        logger.debug(f"{self.monster.name} seeking {best_item.name} at distance {best_distance:.1f}")
        
        return self._get_move_towards_item(best_item, game_map, entities)
    
    def _is_in_fov(self, game_map) -> bool:
        """Check if monster is in field of view (can see items).
        
        Args:
            game_map: The current game map
            
        Returns:
            bool: True if monster can see (is in computed FOV)
        """
        # For now, assume monsters can always "see" items in their vicinity
        # In a more sophisticated implementation, this would check actual FOV
        return True
    
    def _find_nearby_items(self, entities) -> List[Tuple[Any, float]]:
        """Find items within seeking distance.
        
        Args:
            entities: List of all entities in the game
            
        Returns:
            List[Tuple[Entity, float]]: List of (item, distance) tuples
        """
        nearby_items = []
        
        for entity in entities:
            # Only consider items (entities with item component)
            if not (hasattr(entity, 'item') and entity.item):
                continue
                
            # Skip items that are being carried
            if hasattr(entity, 'owner') and entity.owner:
                continue
                
            distance = self._calculate_distance(
                self.monster.x, self.monster.y,
                entity.x, entity.y
            )
            
            if distance <= self.seek_distance:
                nearby_items.append((entity, distance))
                
        # Sort by distance (closest first)
        nearby_items.sort(key=lambda x: x[1])
        
        if nearby_items:
            logger.debug(f"{self.monster.name} found {len(nearby_items)} nearby items")
            
        return nearby_items
    
    def _calculate_distance(self, x1: int, y1: int, x2: int, y2: int) -> float:
        """Calculate distance between two points.
        
        Args:
            x1, y1: First point coordinates
            x2, y2: Second point coordinates
            
        Returns:
            float: Distance between points
        """
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    
    def _get_move_towards_item(self, item, game_map, entities) -> Optional[dict]:
        """Get movement action towards an item.
        
        Args:
            item: Target item entity
            game_map: The current game map
            entities: List of all entities
            
        Returns:
            dict: Movement action or None if can't move
        """
        # Calculate direction to item
        dx = item.x - self.monster.x
        dy = item.y - self.monster.y
        
        # Normalize to single step
        if dx != 0:
            dx = 1 if dx > 0 else -1
        if dy != 0:
            dy = 1 if dy > 0 else -1
            
        # Check if we're on the same tile as the item (can pick it up)
        # Must be EXACTLY on the item, not just adjacent
        if item.x == self.monster.x and item.y == self.monster.y:
            return self._get_pickup_action(item)
            
        # Check if movement is valid
        new_x = self.monster.x + dx
        new_y = self.monster.y + dy
        
        if not self._is_valid_move(new_x, new_y, game_map, entities):
            # Try alternative moves if direct path is blocked
            alternatives = [(dx, 0), (0, dy), (-dx, 0), (0, -dy)]
            for alt_dx, alt_dy in alternatives:
                alt_x = self.monster.x + alt_dx
                alt_y = self.monster.y + alt_dy
                if self._is_valid_move(alt_x, alt_y, game_map, entities):
                    return {"move": (alt_dx, alt_dy)}
            
            # No valid move found
            logger.debug(f"{self.monster.name} blocked from reaching {item.name}")
            return None
            
        return {"move": (dx, dy)}
    
    def _get_pickup_action(self, item) -> dict:
        """Get action to pick up an item.
        
        Args:
            item: Item to pick up
            
        Returns:
            dict: Pickup action
        """
        logger.info(f"{self.monster.name} attempting to pick up {item.name}")
        return {"pickup_item": item}
    
    def _is_valid_move(self, x: int, y: int, game_map, entities) -> bool:
        """Check if a move to the given coordinates is valid.
        
        Args:
            x, y: Target coordinates
            game_map: The current game map
            entities: List of all entities
            
        Returns:
            bool: True if move is valid
        """
        # Check map boundaries
        if x < 0 or x >= game_map.width or y < 0 or y >= game_map.height:
            return False
            
        # Check if tile is blocked
        if game_map.tiles[x][y].blocked:
            return False
            
        # Check for blocking entities
        for entity in entities:
            if entity.x == x and entity.y == y and getattr(entity, 'blocks', False):
                return False
                
        return True


def create_item_seeking_ai(monster, monster_def) -> Optional[ItemSeekingAI]:
    """Create an ItemSeekingAI component for a monster if appropriate.
    
    Args:
        monster: The monster entity
        monster_def: Monster definition from configuration
        
    Returns:
        ItemSeekingAI: AI component if monster can seek items, None otherwise
    """
    if not monster_def.can_seek_items:
        return None
        
    if not (hasattr(monster, 'inventory') and monster.inventory):
        logger.warning(f"Monster {monster.name} configured to seek items but has no inventory")
        return None
        
    return ItemSeekingAI(monster, monster_def.seek_distance)
