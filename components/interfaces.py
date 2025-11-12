"""Component and System Interfaces using Python Protocols.

This module defines structural type interfaces (Protocols) that establish
contracts for how different components and systems should behave.

Using Protocols from typing_extensions allows us to:
1. Specify expected method signatures without forcing inheritance
2. Enable IDE autocompletion and type checking
3. Document what methods/properties must exist on components
4. Catch type errors before runtime

Example:
    ```python
    def move_entity(entity: 'Entity', component: AIProtocol) -> None:
        # IDE knows that component has take_turn() method
        results = component.take_turn(...)
    ```

Key Protocols:
    - AIProtocol: All AI components must implement
    - ComponentProtocol: All components should implement
    - ServiceProtocol: All services should implement
    - EntityProtocol: Minimum interface for game entities
"""

from typing import Protocol, List, Dict, Any, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from entity import Entity
    from fov_functions import FOVMap
    from map_objects.game_map import GameMap


class AIProtocol(Protocol):
    """Interface that all AI components must implement.
    
    AI components control the behavior of non-player entities (monsters, bosses).
    They must be able to take turns and return action results.
    
    Attributes:
        owner: The entity this AI component controls
    """
    
    owner: 'Entity'
    
    def take_turn(
        self,
        target: Optional['Entity'],
        fov_map: 'FOVMap',
        game_map: 'GameMap',
        entities: List['Entity']
    ) -> List[Dict[str, Any]]:
        """Execute one turn of AI behavior.
        
        Args:
            target: The target entity (usually the player), if visible
            fov_map: Field of view map for visibility checks
            game_map: The dungeon map
            entities: All entities in the game
            
        Returns:
            List of action results (dictionaries with action data)
        """
        ...


class ComponentProtocol(Protocol):
    """Base interface all components should implement.
    
    Components are data objects that hold functionality for entities.
    They should track their owner and provide a consistent interface.
    
    Attributes:
        owner: The entity this component belongs to
    """
    
    owner: 'Entity'
    
    def __init__(self) -> None:
        """Initialize the component."""
        ...


class EquippableProtocol(ComponentProtocol):
    """Interface for items that can be equipped.
    
    Equippable items grant bonuses to the wearer.
    """
    
    slot: str  # Equipment slot name (main_hand, chest, etc)
    power_bonus: int
    defense_bonus: int
    
    def __init__(self, slot: str, power_bonus: int = 0, defense_bonus: int = 0) -> None:
        """Initialize equippable item."""
        ...


class InventoryProtocol(ComponentProtocol):
    """Interface for inventory management.
    
    Inventories store items and manage capacity.
    """
    
    capacity: int
    items: List['Entity']
    
    def add_item(self, item: 'Entity') -> None:
        """Add an item to inventory."""
        ...
    
    def remove_item(self, item: 'Entity') -> None:
        """Remove an item from inventory."""
        ...


class FighterProtocol(ComponentProtocol):
    """Interface for combat-capable entities.
    
    Fighters have HP, damage, defense, and status effects.
    """
    
    hp: int
    max_hp: int
    power: int
    defense: int
    xp: int
    
    def take_damage(self, amount: int) -> List[Dict[str, Any]]:
        """Take damage and return action results."""
        ...
    
    def heal(self, amount: int) -> List[Dict[str, Any]]:
        """Heal and return action results."""
        ...


class ItemProtocol(ComponentProtocol):
    """Interface for usable items.
    
    Items can be picked up, carried, and used.
    """
    
    name: str
    identified: bool
    stackable: bool
    
    def __init__(self, name: str = "Item") -> None:
        """Initialize item."""
        ...


class ServiceProtocol(Protocol):
    """Base interface for game services.
    
    Services are singletons that provide game-wide functionality.
    They should be stateless or thread-safe where possible.
    """
    
    def reset(self) -> None:
        """Reset service to initial state (for testing)."""
        ...


class MovementServiceProtocol(ServiceProtocol):
    """Interface for movement and collision handling.
    
    Handles entity movement, collision detection, and terrain checks.
    """
    
    def execute_movement(
        self,
        dx: int,
        dy: int,
        source: str = "keyboard"
    ) -> Dict[str, Any]:
        """Execute movement and return results."""
        ...


class PortalServiceProtocol(ServiceProtocol):
    """Interface for portal management.
    
    Handles portal creation, collision detection, and teleportation.
    """
    
    @staticmethod
    def check_portal_collision(
        entity: 'Entity',
        entities_list: List['Entity']
    ) -> Optional[Dict[str, Any]]:
        """Check if entity stepped on a portal and handle teleportation."""
        ...


class EntityProtocol(Protocol):
    """Minimum interface required for game entities.
    
    An entity is a game object with position, appearance, and components.
    """
    
    x: int
    y: int
    char: str
    color: Tuple[int, int, int]
    name: str
    blocks: bool
    
    def get_component_optional(self, component_type: 'ComponentType') -> Optional[ComponentProtocol]:
        """Get a component if it exists, None otherwise."""
        ...
    
    def require_component(self, component_type: 'ComponentType') -> ComponentProtocol:
        """Get a component, raise ValueError if missing."""
        ...


class FactoryProtocol(Protocol):
    """Interface for entity factories.
    
    Factories create game entities from configuration.
    """
    
    def create_monster(self, monster_type: str, x: int, y: int) -> Optional['Entity']:
        """Create a monster entity."""
        ...
    
    def create_weapon(self, weapon_type: str, x: int, y: int) -> Optional['Entity']:
        """Create a weapon entity."""
        ...
    
    def create_item(self, item_type: str, x: int, y: int) -> Optional['Entity']:
        """Create an item entity."""
        ...


__all__ = [
    'AIProtocol',
    'ComponentProtocol',
    'EquippableProtocol',
    'InventoryProtocol',
    'FighterProtocol',
    'ItemProtocol',
    'ServiceProtocol',
    'MovementServiceProtocol',
    'PortalServiceProtocol',
    'EntityProtocol',
    'FactoryProtocol',
]

