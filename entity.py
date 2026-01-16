"""Entity system for game objects.

This module defines the Entity class which represents all game objects
including players, monsters, items, and interactive elements. Uses a
component-based architecture for flexible object composition.
"""

import math
from typing import Optional, Tuple, List, Any, Dict, TYPE_CHECKING

import tcod

from components.item import Item
from components.faction import Faction, get_faction_from_string
from components.component_registry import ComponentRegistry, ComponentType
from config.game_constants import get_pathfinding_config
from render_functions import RenderOrder

# Legacy libtcod symbols retained for tests/monkeypatching.
libtcod = None
libtcodpy = None

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
        
        # Initialize tags (for entity classification and metadata)
        self.tags: set[str] = set()
        
        # Phase 11: Species ID for monster knowledge tracking
        # Set by entity factory when creating from YAML templates
        self._species_id: Optional[str] = None
        
        # Initialize component registry (NEW: Type-safe component system)
        self.components = ComponentRegistry()
        
        # Initialize all components to None first (for backward compatibility)
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
            # Also register with ComponentRegistry (if not already registered)
            if ComponentType.ITEM not in self.components._components:
                self.components.add(ComponentType.ITEM, self.item)
    
    def _register_components(self, components: dict[str, Any]) -> None:
        """Register components and establish ownership relationships.
        
        This method now uses the ComponentRegistry for type-safe component
        storage while maintaining backward compatibility with direct attribute
        access (entity.fighter, entity.ai, etc.).
        
        Args:
            components: Dictionary of component_name -> component_instance
        """
        # Mapping from component name (string) to ComponentType enum
        component_type_mapping = {
            'fighter': ComponentType.FIGHTER,
            'ai': ComponentType.AI,
            'item': ComponentType.ITEM,
            'inventory': ComponentType.INVENTORY,
            'stairs': ComponentType.STAIRS,
            'level': ComponentType.LEVEL,
            'equipment': ComponentType.EQUIPMENT,
            'equippable': ComponentType.EQUIPPABLE,
            'pathfinding': ComponentType.PATHFINDING,
            'status_effects': ComponentType.STATUS_EFFECTS,
        }
        
        for component_name, component in components.items():
            if component_name not in component_type_mapping:
                raise ValueError(f"Unknown component: {component_name}")
            
            # NEW: Register with type-safe ComponentRegistry
            component_type = component_type_mapping[component_name]
            self.components.add(component_type, component)
            
            # BACKWARD COMPATIBILITY: Also set as direct attribute using super().__setattr__
            # This bypasses __setattr__ hook to avoid duplicate registration
            super().__setattr__(component_name, component)
            
            # Establish ownership if the component supports it
            if component and hasattr(component, 'owner'):
                component.owner = self
    
    def __setattr__(self, name: str, value: Any) -> None:
        """Override setattr to automatically register components in the component registry.
        
        This allows tests and code to set components via direct assignment (entity.fighter = fighter)
        while automatically registering them in the component system (entity.components.add(...)).
        This maintains backward compatibility while ensuring the component registry stays in sync.
        """
        # Map component names to their ComponentType
        component_mapping = {
            'fighter': ComponentType.FIGHTER,
            'ai': ComponentType.AI,
            'item': ComponentType.ITEM,
            'inventory': ComponentType.INVENTORY,
            'stairs': ComponentType.STAIRS,
            'level': ComponentType.LEVEL,
            'equipment': ComponentType.EQUIPMENT,
            'equippable': ComponentType.EQUIPPABLE,
            'wand': ComponentType.WAND,
            'portal': ComponentType.PORTAL,
            'chest': ComponentType.CHEST,
            'signpost': ComponentType.SIGNPOST,
            'mural': ComponentType.MURAL,
            'item_seeking_ai': ComponentType.ITEM_SEEKING_AI,
            'item_usage': ComponentType.ITEM_USAGE,
        }
        
        # Set the attribute normally
        super().__setattr__(name, value)
        
        # If this is a component assignment AND we have a components registry initialized,
        # automatically register it (if not already registered)
        if name in component_mapping and value is not None and hasattr(self, 'components'):
            component_type = component_mapping[name]
            # Only add if not already in registry (to avoid duplicate registration)
            if component_type not in self.components._components:
                self.components.add(component_type, value)
            
            # Establish ownership if the component supports it
            if hasattr(value, 'owner'):
                value.owner = self
    
    @classmethod
    def create_player(
        cls,
        x: int,
        y: int,
        fighter: 'Fighter',
        inventory: 'Inventory',
        level: 'Level',
        equipment: 'Equipment',
        status_effects: Optional[Any] = None
    ) -> 'Entity':
        """Create a player entity with standard components.
        
        Args:
            x (int): Starting x coordinate
            y (int): Starting y coordinate
            fighter (Fighter): Combat component
            inventory (Inventory): Inventory component
            level (Level): Level/XP component
            equipment (Equipment): Equipment component
            status_effects (StatusEffectManager): Status effect manager (auto-created if None)
            
        Returns:
            Entity: Configured player entity
        """
        # Auto-create StatusEffectManager if not provided
        # Create a placeholder that will be initialized after player entity exists
        if status_effects is None:
            from components.status_effects import StatusEffectManager
            # Pass None as owner temporarily - will be set by _register_components
            status_effects = StatusEffectManager(owner=None)
        
        # Create player entity with status_effects component
        player = cls(
            x=x, y=y, char='@', color=(255, 255, 255), name='Player',
            blocks=True, render_order=RenderOrder.ACTOR, faction=Faction.PLAYER,
            fighter=fighter, inventory=inventory, level=level, equipment=equipment,
            status_effects=status_effects
        )
        
        return player
    
    @classmethod
    def create_monster(
        cls,
        x: int,
        y: int,
        char: str,
        color: Tuple[int, int, int],
        name: str,
        fighter: 'Fighter',
        ai: Any
    ) -> 'Entity':
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
    def create_item(
        cls,
        x: int,
        y: int,
        char: str,
        color: Tuple[int, int, int],
        name: str,
        item_component: Item,
        equippable: Optional['Equippable'] = None
    ) -> 'Entity':
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

    def move(self, dx: int, dy: int) -> bool:
        """Move the entity by a given amount.
        
        Phase 20D.1: Movement blocked if entity has 'entangled' status effect.
        Enforcement happens here at the execution point, not in AI logic.

        Args:
            dx: Change in x coordinate
            dy: Change in y coordinate
            
        Returns:
            True if movement succeeded, False if blocked by status effect
        """
        # Phase 20D.1: Check for entangled status - movement blocked at execution point
        from components.component_registry import ComponentType
        if self.components.has(ComponentType.STATUS_EFFECTS):
            status_effects = self.get_component_optional(ComponentType.STATUS_EFFECTS)
            if status_effects and status_effects.has_effect('entangled'):
                # Movement blocked - increment metrics
                entangled = status_effects.get_effect('entangled')
                if entangled and hasattr(entangled, 'on_move_blocked'):
                    entangled.on_move_blocked()
                return False  # Movement blocked
        
        self.x += dx
        self.y += dy
        return True  # Movement succeeded

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

    # ==================== Component Access Helpers ====================
    
    def require_component(self, component_type: ComponentType):
        """Get a component or raise a clear error if missing.
        
        This is the preferred way to access components that MUST exist.
        Use this when the absence of a component indicates a bug.
        
        Args:
            component_type: The type of component to retrieve
            
        Returns:
            The requested component
            
        Raises:
            ValueError: If the component is not present on this entity
            
        Example:
            fighter = entity.require_component(ComponentType.FIGHTER)
            # Will raise ValueError if entity has no Fighter component
        """
        component = self.components.get(component_type)
        if component is None:
            raise ValueError(
                f"{self.name} is missing required component: {component_type.name}"
            )
        return component
    
    def get_component_optional(self, component_type: ComponentType):
        """Get a component or None if not present.
        
        This is the preferred way to access components that are optional.
        Use this when the absence of a component is expected and normal.
        
        Args:
            component_type: The type of component to retrieve
            
        Returns:
            The requested component, or None if not present
            
        Example:
            equipment = entity.get_component_optional(ComponentType.EQUIPMENT)
            if equipment:
                # Entity has equipment, do something
                pass
        """
        return self.components.get(component_type)
    
    def has_component(self, component_type: ComponentType) -> bool:
        """Check if entity has a specific component.
        
        Args:
            component_type: The type of component to check for
            
        Returns:
            True if the component is present, False otherwise
            
        Example:
            if entity.has_component(ComponentType.AI):
                # Entity is an AI-controlled monster
                pass
        """
        return self.components.has(component_type)
    
    # ==================================================================

    def move_astar(self, target: 'Entity', entities: List['Entity'], game_map: 'GameMap') -> None:
        """Move towards target using A* pathfinding algorithm.

        Uses A* pathfinding to find the optimal route to the target,
        taking into account obstacles, other entities, and ground hazards.
        
        Monsters will prefer safer paths that avoid ground hazards when possible,
        but will cross hazards if it's the only available route. Hazard damage
        is added as extra pathfinding cost, making high-damage hazards (like fresh
        fire at 10 dmg) much less attractive than low-damage hazards (like decaying
        gas at 1 dmg).

        Args:
            target: The target entity to move towards
            entities: List of entities that block movement
            game_map: The game map for pathfinding (may include hazard_manager)
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
        
        # Add hazard costs to make monsters avoid dangerous tiles
        # Hazards add their current damage as extra cost, making monsters prefer safer routes
        try:
            if (hasattr(game_map, 'hazard_manager') and 
                game_map.hazard_manager is not None):
                for hazard in game_map.hazard_manager.get_all_hazards():
                    hx, hy = hazard.x, hazard.y
                    if walkable[hy, hx]:  # Only modify walkable tiles
                        # Add hazard damage as pathfinding cost
                        # Fire (10 dmg) adds +10 cost, gas (5 dmg) adds +5 cost
                        # As hazards decay, they become progressively safer to cross
                        hazard_cost = hazard.get_current_damage()
                        cost[hy, hx] = int(cost[hy, hx]) + hazard_cost
        except (AttributeError, TypeError):
            # No valid hazard manager or method, skip hazard costs
            pass
        
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
                # Use move() to respect status effects like entangle
                dx = x - self.x
                dy = y - self.y
                self.move(dx, dy)  # May return False if blocked by status effect
            # If blocked, don't move this turn (path will be recalculated next turn)
        else:
            # Keep the old move function as a backup so that if there are no
            # paths (for example another monster blocks a corridor) it will
            # still try to move towards the player (closer to the corridor opening)
            self.move_towards(target.x, target.y, game_map, entities)

    def distance_to(self, other: 'Entity') -> float:
        """Calculate the Euclidean distance to another entity.

        Args:
            other: The other entity

        Returns:
            The Euclidean distance to the other entity
        """
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx**2 + dy**2)
    
    def chebyshev_distance_to(self, other: 'Entity') -> int:
        """Calculate the Chebyshev distance (chessboard distance) to another entity.
        
        Chebyshev distance is the maximum of the absolute differences in coordinates.
        This treats all 8 surrounding tiles as distance 1, making it ideal for
        melee range checks in roguelikes where diagonal movement is allowed.
        
        Examples:
            - Orthogonal neighbor (1, 0): max(1, 0) = 1
            - Diagonal neighbor (1, 1): max(1, 1) = 1
            - Knight's move (2, 1): max(2, 1) = 2
        
        Args:
            other: The other entity
        
        Returns:
            int: The Chebyshev distance (number of king moves in chess)
        """
        dx = abs(other.x - self.x)
        dy = abs(other.y - self.y)
        return max(dx, dy)
    
    @property
    def species_id(self) -> str:
        """Get the species ID for this entity.
        
        Phase 11: Used by monster knowledge system to track per-species info.
        
        Returns the explicit species_id if set (from entity factory),
        otherwise derives it from the entity name.
        
        Returns:
            str: Species identifier (e.g., "orc", "plague_zombie")
        """
        if self._species_id:
            return self._species_id
        # Fallback: derive from name
        return self.name.lower().replace(" ", "_")
    
    @species_id.setter
    def species_id(self, value: str) -> None:
        """Set the species ID for this entity.
        
        Args:
            value: The species identifier
        """
        self._species_id = value

    def get_display_name(self, compact: bool = False) -> str:
        """Get the display name with damage/defense ranges if applicable.
        
        For items with identification system, shows appearance if unidentified.
        For wands, includes charge count.
        
        Args:
            compact: If True, return abbreviated name for sidebar display
        
        Returns:
            str: Display name with damage/defense info in brackets, or charge count for wands
        """
        # Check if this has an item component with identification
        item_comp = getattr(self, 'item', None)
        if item_comp and not item_comp.identified and item_comp.appearance:
            # Return unidentified appearance directly (no need for extra formatting)
            return item_comp.appearance
        
        # Check if this is a wand - if so, use the wand's display name
        wand = getattr(self, 'wand', None)
        if wand:
            return wand.get_display_name(compact=compact)
        
        # Replace underscores with spaces for better readability
        # Handle case where name might not be a string
        name_str = str(self.name) if not isinstance(self.name, str) else self.name
        display_name = name_str.replace('_', ' ').title()
        
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
    
    def get_status_effect_manager(self) -> Any:
        """Get or create the status effect manager for this entity.
        
        Returns:
            StatusEffectManager: The status effect manager
        """
        if self.status_effects is None:
            from components.status_effects import StatusEffectManager
            self.status_effects = StatusEffectManager(self)
        return self.status_effects
    
    def add_status_effect(self, effect: Any) -> List[Dict[str, Any]]:
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
    
    def process_status_effects_turn_start(self) -> List[Dict[str, Any]]:
        """Process status effects at the start of this entity's turn.
        
        Returns:
            List of result dictionaries from effect processing
        """
        if self.status_effects is None:
            return []
        return self.status_effects.process_turn_start()
    
    def process_status_effects_turn_end(self) -> List[Dict[str, Any]]:
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
