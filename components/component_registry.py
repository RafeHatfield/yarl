"""Type-safe component registry system for entity components.

This module provides a registry pattern for entity components, replacing
verbose hasattr() checks with type-safe component lookups. The registry
supports efficient O(1) component access, type safety, and future features
like component querying and lifecycle hooks.

Example:
    >>> entity = Entity(5, 5, 'o', (255, 0, 0), "Orc", fighter=Fighter(...))
    >>> entity.components.has(ComponentType.FIGHTER)
    True
    >>> fighter = entity.require_component(ComponentType.FIGHTER)  # or get_component_optional()
    >>> fighter.hp
    10

Classes:
    ComponentType: Enum of all valid component types
    ComponentRegistry: Type-safe storage and lookup for components
"""

from enum import Enum, auto
from typing import Dict, Optional, Any, Iterator, List


class ComponentType(Enum):
    """Type-safe identifiers for all entity components.
    
    This enum provides compile-time type safety for component lookups,
    preventing typos and enabling IDE autocomplete. Each component type
    represents a specific capability or data container that can be
    attached to an entity.
    
    Attributes:
        FIGHTER: Combat stats (HP, defense, power, attacks)
        AI: Autonomous behavior (movement, targeting, actions)
        ITEM: Item-specific data (usable, throwable, etc.)
        INVENTORY: Collection of items owned by entity
        EQUIPMENT: Worn/wielded items (weapons, armor)
        EQUIPPABLE: Metadata for equippable items (slots, bonuses)
        LEVEL: Experience and level progression
        STAIRS: Dungeon traversal connection
        PATHFINDING: Player click-to-move pathfinding state
        STATUS_EFFECTS: Temporary buffs/debuffs (poison, confusion, etc.)
        WAND: Multi-charge magical item
        RING: Passive effect ring
        GROUND_HAZARD: Persistent ground effect (fire, poison)
        STATISTICS: Combat/gameplay statistics tracking
        FACTION: Allegiance system (player, enemy, neutral)
        ITEM_USAGE: Monster item usage AI component
        ITEM_SEEKING_AI: Monster item-seeking behavior
        AUTO_EXPLORE: Automated dungeon exploration for player
        MAP_FEATURE: Base map feature (chests, signposts, etc.)
        CHEST: Interactive chest container
        SIGNPOST: Readable sign with messages
    """
    FIGHTER = auto()
    AI = auto()
    ITEM = auto()
    INVENTORY = auto()
    EQUIPMENT = auto()
    EQUIPPABLE = auto()
    LEVEL = auto()
    STAIRS = auto()
    PATHFINDING = auto()
    STATUS_EFFECTS = auto()
    WAND = auto()
    RING = auto()
    GROUND_HAZARD = auto()
    STATISTICS = auto()
    FACTION = auto()
    BOSS = auto()
    ITEM_USAGE = auto()
    ITEM_SEEKING_AI = auto()
    AUTO_EXPLORE = auto()
    MAP_FEATURE = auto()
    CHEST = auto()
    SIGNPOST = auto()
    MURAL = auto()
    LOCKED_DOOR = auto()


class ComponentRegistry:
    """Type-safe storage and lookup for entity components.
    
    The registry provides O(1) component access using ComponentType enum
    as keys, replacing hasattr() checks with type-safe lookups. Components
    are stored in a dictionary and accessed through type-safe methods.
    
    The registry maintains a single instance of each component type per
    entity, preventing duplication and ensuring consistent state.
    
    Example:
        >>> registry = ComponentRegistry()
        >>> fighter = Fighter(hp=10, defense=5, power=3)
        >>> registry.add(ComponentType.FIGHTER, fighter)
        >>> 
        >>> if registry.has(ComponentType.FIGHTER):
        ...     fighter = registry.get(ComponentType.FIGHTER)
        ...     print(f"HP: {fighter.hp}")
        HP: 10
    
    Attributes:
        _components: Internal dictionary mapping ComponentType to component instances
    """
    
    def __init__(self):
        """Initialize an empty component registry."""
        self._components: Dict[ComponentType, Any] = {}
    
    def add(self, component_type: ComponentType, component: Any) -> None:
        """Add a component to the registry.
        
        Registers a component instance with the given type. If a component
        of the same type already exists, raises ValueError to prevent
        accidental overwrites.
        
        Args:
            component_type: The type of component being added
            component: The component instance to store
            
        Raises:
            ValueError: If a component of this type already exists
            TypeError: If component_type is not a ComponentType enum value
            
        Example:
            >>> registry = ComponentRegistry()
            >>> fighter = Fighter(hp=10, defense=5, power=3)
            >>> registry.add(ComponentType.FIGHTER, fighter)
        """
        if not isinstance(component_type, ComponentType):
            raise TypeError(f"component_type must be ComponentType, got {type(component_type)}")
        
        if component_type in self._components:
            raise ValueError(f"Component {component_type.name} already exists in registry")
        
        self._components[component_type] = component
    
    def get(self, component_type: ComponentType) -> Optional[Any]:
        """Get a component by type.
        
        Retrieves the component instance for the given type, or None if
        the component doesn't exist. This is the primary method for
        accessing components.
        
        Args:
            component_type: The type of component to retrieve
            
        Returns:
            The component instance, or None if not found
            
        Example:
            >>> registry = ComponentRegistry()
            >>> fighter = registry.get(ComponentType.FIGHTER)
            >>> if fighter:
            ...     print(f"HP: {fighter.hp}")
        """
        return self._components.get(component_type)
    
    def has(self, component_type: ComponentType) -> bool:
        """Check if a component type exists in the registry.
        
        More efficient than get() when you only need to check existence.
        Replaces hasattr(entity, 'fighter') with entity.components.has(ComponentType.FIGHTER).
        
        Args:
            component_type: The type of component to check
            
        Returns:
            True if the component exists, False otherwise
            
        Example:
            >>> registry = ComponentRegistry()
            >>> registry.has(ComponentType.FIGHTER)
            False
            >>> registry.add(ComponentType.FIGHTER, Fighter(...))
            >>> registry.has(ComponentType.FIGHTER)
            True
        """
        return component_type in self._components
    
    def remove(self, component_type: ComponentType) -> Optional[Any]:
        """Remove a component from the registry.
        
        Removes and returns the component instance, or None if the component
        doesn't exist. This is useful for dynamic component removal (e.g.,
        when an entity dies, removing the AI component).
        
        Args:
            component_type: The type of component to remove
            
        Returns:
            The removed component instance, or None if not found
            
        Example:
            >>> registry = ComponentRegistry()
            >>> fighter = Fighter(hp=10, defense=5, power=3)
            >>> registry.add(ComponentType.FIGHTER, fighter)
            >>> removed = registry.remove(ComponentType.FIGHTER)
            >>> removed == fighter
            True
        """
        return self._components.pop(component_type, None)
    
    def get_all_types(self) -> List[ComponentType]:
        """Get a list of all component types in this registry.
        
        Returns the ComponentType enum values for all components currently
        registered. Useful for debugging and introspection.
        
        Returns:
            List of ComponentType enum values
            
        Example:
            >>> registry = ComponentRegistry()
            >>> registry.add(ComponentType.FIGHTER, Fighter(...))
            >>> registry.add(ComponentType.AI, BasicMonster())
            >>> registry.get_all_types()
            [ComponentType.FIGHTER, ComponentType.AI]
        """
        return list(self._components.keys())
    
    def clear(self) -> None:
        """Remove all components from the registry.
        
        Clears all components, resetting the registry to an empty state.
        This is primarily used for testing and cleanup scenarios.
        
        Example:
            >>> registry = ComponentRegistry()
            >>> registry.add(ComponentType.FIGHTER, Fighter(...))
            >>> len(registry._components)
            1
            >>> registry.clear()
            >>> len(registry._components)
            0
        """
        self._components.clear()
    
    def __contains__(self, component_type: ComponentType) -> bool:
        """Support 'in' operator for checking component existence.
        
        Allows Pythonic syntax: `if ComponentType.FIGHTER in entity.components:`
        
        Args:
            component_type: The type of component to check
            
        Returns:
            True if the component exists, False otherwise
            
        Example:
            >>> registry = ComponentRegistry()
            >>> registry.add(ComponentType.FIGHTER, Fighter(...))
            >>> ComponentType.FIGHTER in registry
            True
            >>> ComponentType.AI in registry
            False
        """
        return component_type in self._components
    
    def __iter__(self) -> Iterator[Any]:
        """Support iteration over all component instances.
        
        Allows iterating over all components without knowing their types:
        `for component in entity.components:`
        
        Yields:
            Component instances in registration order
            
        Example:
            >>> registry = ComponentRegistry()
            >>> registry.add(ComponentType.FIGHTER, Fighter(...))
            >>> registry.add(ComponentType.AI, BasicMonster())
            >>> for component in registry:
            ...     print(component.__class__.__name__)
            Fighter
            BasicMonster
        """
        return iter(self._components.values())
    
    def __len__(self) -> int:
        """Return the number of components in the registry.
        
        Allows using len() on the registry: `len(entity.components)`
        
        Returns:
            Number of registered components
            
        Example:
            >>> registry = ComponentRegistry()
            >>> len(registry)
            0
            >>> registry.add(ComponentType.FIGHTER, Fighter(...))
            >>> len(registry)
            1
        """
        return len(self._components)
    
    def __repr__(self) -> str:
        """Return a string representation of the registry for debugging.
        
        Returns:
            String showing component types and count
            
        Example:
            >>> registry = ComponentRegistry()
            >>> registry.add(ComponentType.FIGHTER, Fighter(...))
            >>> repr(registry)
            'ComponentRegistry(components=[FIGHTER], count=1)'
        """
        types = [ct.name for ct in self._components.keys()]
        return f"ComponentRegistry(components={types}, count={len(self._components)})"
