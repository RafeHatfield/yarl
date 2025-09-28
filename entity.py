"""Entity system for game objects.

This module defines the Entity class which represents all game objects
including players, monsters, items, and interactive elements. Uses a
component-based architecture for flexible object composition.
"""

import math
from typing import Optional, Tuple, List, Any, TYPE_CHECKING

import tcod
import tcod.libtcodpy as libtcodpy

from components.item import Item
from config.game_constants import get_pathfinding_config
from render_functions import RenderOrder

# Avoid circular imports
if TYPE_CHECKING:
    from components.fighter import Fighter
    from components.ai import BasicMonster, ConfusedMonster
    from components.inventory import Inventory
    from components.level import Level
    from components.equipment import Equipment
    from components.equippable import Equippable
    from map_objects.game_map import GameMap


class Entity:
    """A generic object to represent players, enemies, items, etc.

    This is the base class for all game objects including the player,
    monsters, items, stairs, and other interactive elements. It provides
    basic functionality for positioning, rendering, movement, and pathfinding.

    Attributes:
        x (int): X coordinate on the game map
        y (int): Y coordinate on the game map
        char (str): Character to display for this entity
        color (Tuple[int, int, int]): RGB color tuple for rendering
        name (str): Display name of the entity
        blocks (bool): Whether this entity blocks movement
        render_order (RenderOrder): Rendering priority order
        fighter (Optional[Fighter]): Combat component
        ai (Optional[Any]): AI behavior component
        item (Optional[Item]): Item component
        inventory (Optional[Inventory]): Inventory component
        stairs (Optional[Any]): Stairs component
        level (Optional[Level]): Level/XP component
        equipment (Optional[Equipment]): Equipment component
        equippable (Optional[Equippable]): Equippable component
    """
    
    # Type annotations for attributes
    x: int
    y: int
    char: str
    color: Tuple[int, int, int]
    name: str
    blocks: bool
    render_order: RenderOrder
    fighter: Optional['Fighter']
    ai: Optional[Any]  # Could be BasicMonster, ConfusedMonster, or custom AI
    item: Optional[Item]
    inventory: Optional['Inventory']
    stairs: Optional[Any]  # Stairs component not yet typed
    level: Optional['Level']
    equipment: Optional['Equipment']
    equippable: Optional['Equippable']

    def __init__(
        self,
        x: int,
        y: int,
        char: str,
        color: Tuple[int, int, int],
        name: str,
        blocks: bool = False,
        render_order: RenderOrder = RenderOrder.CORPSE,
        **components: Any
    ) -> None:
        """Initialize an Entity with automatic component management.

        Args:
            x (int): X coordinate on the game map
            y (int): Y coordinate on the game map
            char (str): Character to display for this entity
            color (tuple): RGB color tuple for rendering
            name (str): Display name of the entity
            blocks (bool, optional): Whether this entity blocks movement. Defaults to False.
            render_order (RenderOrder, optional): Rendering priority. Defaults to RenderOrder.CORPSE.
            **components: Component instances (fighter, ai, item, inventory, stairs, level, equipment, equippable)
        """
        # Set basic properties
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks = blocks
        self.render_order = render_order
        
        # Initialize all components to None first
        self.fighter = None
        self.ai = None
        self.item = None
        self.inventory = None
        self.stairs = None
        self.level = None
        self.equipment = None
        self.equippable = None
        
        # Set components and establish ownership automatically
        self._register_components(components)
        
        # Special handling: equippable items automatically get an item component
        if self.equippable and not self.item:
            self.item = Item()
            self.item.owner = self
    
    def _register_components(self, components: dict[str, Any]) -> None:
        """Register components and establish ownership relationships.
        
        Args:
            components: Dictionary of component_name -> component_instance
        """
        # Valid component names that can be registered
        valid_components = {
            'fighter', 'ai', 'item', 'inventory', 'stairs', 
            'level', 'equipment', 'equippable'
        }
        
        for component_name, component in components.items():
            if component_name not in valid_components:
                raise ValueError(f"Unknown component: {component_name}")
            
            # Set the component on this entity
            setattr(self, component_name, component)
            
            # Establish ownership if the component supports it
            if component and hasattr(component, 'owner'):
                component.owner = self
    
    @classmethod
    def create_player(cls, x, y, fighter, inventory, level, equipment):
        """Create a player entity with standard components.
        
        Args:
            x (int): Starting x coordinate
            y (int): Starting y coordinate
            fighter (Fighter): Combat component
            inventory (Inventory): Inventory component
            level (Level): Level/XP component
            equipment (Equipment): Equipment component
            
        Returns:
            Entity: Configured player entity
        """
        return cls(
            x=x, y=y, char='@', color=(255, 255, 255), name='Player',
            blocks=True, render_order=RenderOrder.ACTOR,
            fighter=fighter, inventory=inventory, level=level, equipment=equipment
        )
    
    @classmethod
    def create_monster(cls, x, y, char, color, name, fighter, ai):
        """Create a monster entity with standard components.
        
        Args:
            x (int): Starting x coordinate
            y (int): Starting y coordinate
            char (str): Display character
            color (tuple): RGB color
            name (str): Monster name
            fighter (Fighter): Combat component
            ai (AI): AI behavior component
            
        Returns:
            Entity: Configured monster entity
        """
        return cls(
            x=x, y=y, char=char, color=color, name=name,
            blocks=True, render_order=RenderOrder.ACTOR,
            fighter=fighter, ai=ai
        )
    
    @classmethod
    def create_item(cls, x, y, char, color, name, item_component, equippable=None):
        """Create an item entity with standard components.
        
        Args:
            x (int): Starting x coordinate
            y (int): Starting y coordinate
            char (str): Display character
            color (tuple): RGB color
            name (str): Item name
            item_component (Item): Item component
            equippable (Equippable, optional): Equippable component for equipment
            
        Returns:
            Entity: Configured item entity
        """
        components = {'item': item_component}
        if equippable:
            components['equippable'] = equippable
            
        return cls(
            x=x, y=y, char=char, color=color, name=name,
            blocks=False, render_order=RenderOrder.ITEM,
            **components
        )

    def move(self, dx: int, dy: int) -> None:
        """Move the entity by a given amount.

        Args:
            dx: Change in x coordinate
            dy: Change in y coordinate
        """
        self.x += dx
        self.y += dy

    def move_towards(self, target_x: int, target_y: int, game_map: 'GameMap', entities: List['Entity']) -> None:
        """Move towards a target position, avoiding obstacles.

        Args:
            target_x: Target x coordinate
            target_y: Target y coordinate
            game_map: The game map for collision detection
            entities: List of entities to avoid
        """
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx**2 + dy**2)

        dx = int(round(dx / distance))
        dy = int(round(dy / distance))

        if not (
            game_map.is_blocked(self.x + dx, self.y + dy)
            or get_blocking_entities_at_location(entities, self.x + dx, self.y + dy)
        ):
            self.move(dx, dy)

    def distance(self, x: int, y: int) -> float:
        """Calculate the distance to a specific coordinate.

        Args:
            x: Target x coordinate
            y: Target y coordinate

        Returns:
            The Euclidean distance to the target coordinates
        """
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)

    def move_astar(self, target: 'Entity', entities: List['Entity'], game_map: 'GameMap') -> None:
        """Move towards target using A* pathfinding algorithm.

        Uses A* pathfinding to find the optimal route to the target,
        taking into account obstacles and other entities.

        Args:
            target: The target entity to move towards
            entities: List of entities that block movement
            game_map: The game map for pathfinding
        """
        # Create a FOV map that has the dimensions of the map
        fov = tcod.map.Map(game_map.width, game_map.height)

        # Scan the current map each turn and set all the walls as unwalkable
        for y1 in range(game_map.height):
            for x1 in range(game_map.width):
                fov.transparent[y1, x1] = not game_map.tiles[x1][y1].block_sight
                fov.walkable[y1, x1] = not game_map.tiles[x1][y1].blocked

        # Scan all the objects to see if there are objects that must be
        # navigated around. Check also that the object isn't self or the target
        # (so that the start and the end points are free). The AI class handles
        # the situation if self is next to the target so it will not use this
        # A* function anyway
        for entity in entities:
            if entity.blocks and entity != self and entity != target:
                # Set the tile as a wall so it must be navigated around
                fov.transparent[entity.y, entity.x] = True
                fov.walkable[entity.y, entity.x] = False

        # Get pathfinding configuration
        pathfinding_config = get_pathfinding_config()
        
        # Allocate a A* path
        # Use configured diagonal cost for movement
        my_path = libtcodpy.path_new_using_map(fov, pathfinding_config.DIAGONAL_MOVE_COST)

        # Compute the path between self's coordinates and the target's coordinates
        libtcodpy.path_compute(my_path, self.x, self.y, target.x, target.y)

        # Check if the path exists, and in this case, also the path is shorter
        # than the configured maximum. The path size matters if you want the monster to use
        # alternative longer paths (for example through other rooms) if for
        # example the player is in a corridor. It makes sense to keep path size
        # relatively low to keep the monsters from running around the map if
        # there's an alternative path really far away
        if not libtcodpy.path_is_empty(my_path) and libtcodpy.path_size(my_path) < pathfinding_config.MAX_PATH_LENGTH:
            # Find the next coordinates in the computed full path
            x, y = libtcodpy.path_walk(my_path, True)
            if x or y:
                # Set self's coordinates to the next path tile
                self.x = x
                self.y = y
        else:
            # Keep the old move function as a backup so that if there are no
            # paths (for example another monster blocks a corridor) it will
            # still try to move towards the player (closer to the corridor opening)
            self.move_towards(target.x, target.y, game_map, entities)

            # Delete the path to free memory
        libtcodpy.path_delete(my_path)

    def distance_to(self, other: 'Entity') -> float:
        """Calculate the distance to another entity.

        Args:
            other: The other entity

        Returns:
            The Euclidean distance to the other entity
        """
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx**2 + dy**2)


def get_blocking_entities_at_location(entities: List[Entity], destination_x: int, destination_y: int) -> Optional[Entity]:
    """Find a blocking entity at the specified location.
    
    Args:
        entities: List of entities to search
        destination_x: X coordinate to check
        destination_y: Y coordinate to check
        
    Returns:
        The blocking entity at the location, or None if no blocking entity found
    """
    for entity in entities:
        if entity.blocks and entity.x == destination_x and entity.y == destination_y:
            return entity

    return None
