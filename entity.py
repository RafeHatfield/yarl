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
from components.faction import Faction, get_faction_from_string
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
        faction (Faction): Entity faction for combat relationships
        invisible (bool): Whether entity is invisible to most AI
        status_effects (Optional[Any]): Status effect manager
        special_abilities (Optional[List[str]]): List of special abilities
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
    faction: Faction
    invisible: bool
    status_effects: Optional[Any]  # StatusEffectManager - avoid circular import
    special_abilities: Optional[List[str]]
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
        faction: Optional[Faction] = None,
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
            faction (Faction, optional): Entity faction for combat relationships. Defaults to NEUTRAL.
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
        
        # Set faction (default to NEUTRAL for most entities)
        self.faction = faction if faction is not None else Faction.NEUTRAL
        
        # Initialize status effect properties
        self.invisible = False
        self.status_effects = None  # Will be initialized when first status effect is added
        
        # Initialize special abilities
        self.special_abilities = None
        
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
            'level', 'equipment', 'equippable', 'pathfinding', 'status_effects'
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
            blocks=True, render_order=RenderOrder.ACTOR, faction=Faction.PLAYER,
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
        # Create a FOV map using the modern numpy-based API
        import numpy as np
        
        # Initialize transparent and walkable arrays
        transparent = np.ones((game_map.height, game_map.width), dtype=bool, order="F")
        walkable = np.ones((game_map.height, game_map.width), dtype=bool, order="F")
        
        # Scan the current map each turn and set all the walls as unwalkable
        for y1 in range(game_map.height):
            for x1 in range(game_map.width):
                transparent[y1, x1] = not game_map.tiles[x1][y1].block_sight
                walkable[y1, x1] = not game_map.tiles[x1][y1].blocked

        # Scan all the objects to see if there are objects that must be
        # navigated around. Check also that the object isn't self or the target
        # (so that the start and the end points are free). The AI class handles
        # the situation if self is next to the target so it will not use this
        # A* function anyway
        for entity in entities:
            if entity.blocks and entity != self and entity != target:
                # Set the tile as a wall so it must be navigated around
                walkable[entity.y, entity.x] = False
        
        # Create the cost map for pathfinding (1 = normal cost, 0 = blocked)
        cost = np.where(walkable, 1, 0).astype(np.int8)
        
        # Create pathfinder using the modern tcod.path API
        # IMPORTANT: cost array is indexed [y, x] but tcod expects (x, y)
        # We need to transpose the cost array OR swap coordinates
        # Here we transpose the cost array to match tcod's (x, y) expectations
        cost_transposed = cost.T  # Transpose from [y, x] to [x, y]
        graph = tcod.path.SimpleGraph(cost=cost_transposed, cardinal=2, diagonal=3)
        pf = tcod.path.Pathfinder(graph)
        pf.add_root((self.x, self.y))

        # Get pathfinding configuration
        pathfinding_config = get_pathfinding_config()
        
        # Compute path to target
        path = pf.path_to((target.x, target.y))
        
        # Check if the path exists and is not too long
        # NOTE: path includes the starting position, so we need at least 2 elements
        if len(path) > 1 and len(path) < pathfinding_config.MAX_PATH_LENGTH:
            # Get next step (skip first element which is current position)
            x, y = path[1]
            
            # Validate that the destination is not occupied by a blocking entity
            # (entities might have moved since pathfinding was calculated)
            destination_blocked = False
            for entity in entities:
                if entity.blocks and entity != self and entity.x == x and entity.y == y:
                    destination_blocked = True
                    break
            
            # Only move if destination is clear
            if not destination_blocked:
                self.x = x
                self.y = y
            # If blocked, don't move this turn (path will be recalculated next turn)
        else:
            # Keep the old move function as a backup so that if there are no
            # paths (for example another monster blocks a corridor) it will
            # still try to move towards the player (closer to the corridor opening)
            self.move_towards(target.x, target.y, game_map, entities)

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
    
    def get_display_name(self) -> str:
        """Get the display name with damage/defense ranges if applicable.
        
        Returns:
            str: Display name with damage/defense info in brackets
        """
        display_name = self.name
        
        if self.equippable:
            # Add damage range for weapons
            damage_text = self.equippable.get_damage_range_text()
            if damage_text:
                display_name += f" {damage_text}"
            
            # Add defense range for armor
            defense_text = self.equippable.get_defense_range_text()
            if defense_text:
                display_name += f" {defense_text}"
        
        return display_name
    
    def get_status_effect_manager(self):
        """Get or create the status effect manager for this entity.
        
        Returns:
            StatusEffectManager: The status effect manager
        """
        if self.status_effects is None:
            from components.status_effects import StatusEffectManager
            self.status_effects = StatusEffectManager(self)
        return self.status_effects
    
    def add_status_effect(self, effect):
        """Add a status effect to this entity.
        
        Args:
            effect: StatusEffect instance to add
            
        Returns:
            List of result dictionaries from applying the effect
        """
        manager = self.get_status_effect_manager()
        return manager.add_effect(effect)
    
    def has_status_effect(self, name: str) -> bool:
        """Check if entity has a specific status effect.
        
        Args:
            name: Name of the status effect to check for
            
        Returns:
            True if entity has the effect
        """
        if self.status_effects is None:
            return False
        return self.status_effects.has_effect(name)
    
    def process_status_effects_turn_start(self):
        """Process status effects at the start of this entity's turn.
        
        Returns:
            List of result dictionaries from effect processing
        """
        if self.status_effects is None:
            return []
        return self.status_effects.process_turn_start()
    
    def process_status_effects_turn_end(self):
        """Process status effects at the end of this entity's turn.
        
        Returns:
            List of result dictionaries from effect processing
        """
        if self.status_effects is None:
            return []
        return self.status_effects.process_turn_end()


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
