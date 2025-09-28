"""Specialized object pools for common game objects.

This module provides pre-configured object pools for frequently created
game objects like messages, entities, components, and events.
"""

from typing import Any, Dict, List, Optional, Tuple, Type
import logging
from dataclasses import dataclass

from .core import ObjectPool, PoolableObject, PoolManager, MemoryConfig
from events import Event, SimpleEvent
from game_messages import Message

logger = logging.getLogger(__name__)


class PooledMessage(PoolableObject):
    """Poolable version of game message."""
    
    def __init__(self, text: str = "", color: Tuple[int, int, int] = (255, 255, 255)):
        """Initialize pooled message.
        
        Args:
            text (str): Message text
            color (Tuple[int, int, int]): Message color
        """
        self.text = text
        self.color = color
    
    def reset(self) -> None:
        """Reset message to initial state."""
        self.text = ""
        self.color = (255, 255, 255)
    
    def set_message(self, text: str, color: Tuple[int, int, int] = (255, 255, 255)) -> None:
        """Set message content.
        
        Args:
            text (str): Message text
            color (Tuple[int, int, int]): Message color
        """
        self.text = text
        self.color = color
    
    def to_message(self) -> Message:
        """Convert to regular Message object.
        
        Returns:
            Message: Regular message object
        """
        return Message(self.text, self.color)


class PooledEvent(PoolableObject):
    """Poolable version of game event."""
    
    def __init__(self, event_type: str = "", data: Dict[str, Any] = None):
        """Initialize pooled event.
        
        Args:
            event_type (str): Event type
            data (Dict[str, Any], optional): Event data
        """
        self.event_type = event_type
        self.data = data or {}
        self.cancelled = False
        self.processed = False
    
    def reset(self) -> None:
        """Reset event to initial state."""
        self.event_type = ""
        self.data.clear()
        self.cancelled = False
        self.processed = False
    
    def set_event(self, event_type: str, data: Dict[str, Any] = None) -> None:
        """Set event content.
        
        Args:
            event_type (str): Event type
            data (Dict[str, Any], optional): Event data
        """
        self.event_type = event_type
        self.data = data or {}
        self.cancelled = False
        self.processed = False
    
    def to_event(self) -> SimpleEvent:
        """Convert to regular Event object.
        
        Returns:
            SimpleEvent: Regular event object
        """
        return SimpleEvent(self.event_type, self.data.copy())


class PooledComponent(PoolableObject):
    """Base class for poolable components."""
    
    def __init__(self):
        """Initialize pooled component."""
        self.owner = None
        self._initialized = False
    
    def reset(self) -> None:
        """Reset component to initial state."""
        self.owner = None
        self._initialized = False
        self._reset_component_data()
    
    def _reset_component_data(self) -> None:
        """Reset component-specific data - override in subclasses."""
        pass
    
    def initialize_component(self, **kwargs) -> None:
        """Initialize component with specific data."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self._initialized = True
    
    def is_initialized(self) -> bool:
        """Check if component is initialized."""
        return self._initialized


class PooledFighter(PooledComponent):
    """Poolable fighter component."""
    
    def __init__(self):
        """Initialize pooled fighter."""
        super().__init__()
        self.max_hp = 0
        self.hp = 0
        self.defense = 0
        self.power = 0
        self.xp = 0
    
    def _reset_component_data(self) -> None:
        """Reset fighter-specific data."""
        self.max_hp = 0
        self.hp = 0
        self.defense = 0
        self.power = 0
        self.xp = 0


class PooledAI(PooledComponent):
    """Poolable AI component."""
    
    def __init__(self):
        """Initialize pooled AI."""
        super().__init__()
        self.ai_type = "basic"
        self.target = None
        self.path = []
        self.confused_turns = 0
    
    def _reset_component_data(self) -> None:
        """Reset AI-specific data."""
        self.ai_type = "basic"
        self.target = None
        self.path.clear()
        self.confused_turns = 0


class PooledItem(PooledComponent):
    """Poolable item component."""
    
    def __init__(self):
        """Initialize pooled item."""
        super().__init__()
        self.use_function = None
        self.targeting = False
        self.targeting_message = None
        self.item_type = "generic"
    
    def _reset_component_data(self) -> None:
        """Reset item-specific data."""
        self.use_function = None
        self.targeting = False
        self.targeting_message = None
        self.item_type = "generic"


class PooledEntity(PoolableObject):
    """Poolable entity for temporary objects."""
    
    def __init__(self):
        """Initialize pooled entity."""
        self.x = 0
        self.y = 0
        self.char = '?'
        self.color = (255, 255, 255)
        self.name = ""
        self.blocks = False
        self.render_order = None
        
        # Components
        self.fighter = None
        self.ai = None
        self.item = None
        self.inventory = None
        self.stairs = None
        self.level = None
        self.equipment = None
        self.equippable = None
    
    def reset(self) -> None:
        """Reset entity to initial state."""
        self.x = 0
        self.y = 0
        self.char = '?'
        self.color = (255, 255, 255)
        self.name = ""
        self.blocks = False
        self.render_order = None
        
        # Clear components
        self.fighter = None
        self.ai = None
        self.item = None
        self.inventory = None
        self.stairs = None
        self.level = None
        self.equipment = None
        self.equippable = None
    
    def initialize_entity(self, x: int, y: int, char: str, color: Tuple[int, int, int],
                         name: str, blocks: bool = False, render_order=None, **components) -> None:
        """Initialize entity with specific data.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
            char (str): Display character
            color (Tuple[int, int, int]): Color tuple
            name (str): Entity name
            blocks (bool): Whether entity blocks movement
            render_order: Render order
            **components: Component instances
        """
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks = blocks
        self.render_order = render_order
        
        # Set components
        for component_name, component in components.items():
            if hasattr(self, component_name):
                setattr(self, component_name, component)


class TemporaryObject(PoolableObject):
    """Generic temporary object for calculations."""
    
    def __init__(self):
        """Initialize temporary object."""
        self.data = {}
    
    def reset(self) -> None:
        """Reset temporary object."""
        self.data.clear()
    
    def set_data(self, **kwargs) -> None:
        """Set temporary data."""
        self.data.update(kwargs)
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """Get temporary data."""
        return self.data.get(key, default)


class MessagePool(ObjectPool[PooledMessage]):
    """Specialized pool for message objects."""
    
    def __init__(self, initial_size: int = 50, max_size: int = 200):
        """Initialize message pool.
        
        Args:
            initial_size (int): Initial pool size
            max_size (int): Maximum pool size
        """
        super().__init__(
            object_class=PooledMessage,
            initial_size=initial_size,
            max_size=max_size
        )
    
    def create_message(self, text: str, color: Tuple[int, int, int] = (255, 255, 255),
                      auto_release: bool = True) -> PooledMessage:
        """Create a message from the pool.
        
        Args:
            text (str): Message text
            color (Tuple[int, int, int]): Message color
            auto_release (bool): Whether to auto-release
            
        Returns:
            PooledMessage: Message from pool
        """
        message = self.acquire(auto_release=auto_release)
        if isinstance(message, PooledMessage):
            message.set_message(text, color)
        else:
            # It's a PooledObject wrapper
            message.set_message(text, color)
        return message


class EntityPool(ObjectPool[PooledEntity]):
    """Specialized pool for temporary entity objects."""
    
    def __init__(self, initial_size: int = 20, max_size: int = 100):
        """Initialize entity pool.
        
        Args:
            initial_size (int): Initial pool size
            max_size (int): Maximum pool size
        """
        super().__init__(
            object_class=PooledEntity,
            initial_size=initial_size,
            max_size=max_size
        )
    
    def create_entity(self, x: int, y: int, char: str, color: Tuple[int, int, int],
                     name: str, blocks: bool = False, render_order=None,
                     auto_release: bool = True, **components) -> PooledEntity:
        """Create an entity from the pool.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
            char (str): Display character
            color (Tuple[int, int, int]): Color tuple
            name (str): Entity name
            blocks (bool): Whether entity blocks movement
            render_order: Render order
            auto_release (bool): Whether to auto-release
            **components: Component instances
            
        Returns:
            PooledEntity: Entity from pool
        """
        entity = self.acquire(auto_release=auto_release)
        if isinstance(entity, PooledEntity):
            entity.initialize_entity(x, y, char, color, name, blocks, render_order, **components)
        else:
            # It's a PooledObject wrapper
            entity.initialize_entity(x, y, char, color, name, blocks, render_order, **components)
        return entity


class ComponentPool(ObjectPool):
    """Specialized pool for component objects."""
    
    def __init__(self, component_class: Type[PooledComponent], 
                 initial_size: int = 30, max_size: int = 150):
        """Initialize component pool.
        
        Args:
            component_class (Type[PooledComponent]): Component class to pool
            initial_size (int): Initial pool size
            max_size (int): Maximum pool size
        """
        super().__init__(
            object_class=component_class,
            initial_size=initial_size,
            max_size=max_size
        )
        self.component_class = component_class
    
    def create_component(self, auto_release: bool = True, **kwargs) -> PooledComponent:
        """Create a component from the pool.
        
        Args:
            auto_release (bool): Whether to auto-release
            **kwargs: Component initialization parameters
            
        Returns:
            PooledComponent: Component from pool
        """
        component = self.acquire(auto_release=auto_release)
        if isinstance(component, PooledComponent):
            component.initialize_component(**kwargs)
        else:
            # It's a PooledObject wrapper
            component.initialize_component(**kwargs)
        return component


class EventPool(ObjectPool[PooledEvent]):
    """Specialized pool for event objects."""
    
    def __init__(self, initial_size: int = 100, max_size: int = 500):
        """Initialize event pool.
        
        Args:
            initial_size (int): Initial pool size
            max_size (int): Maximum pool size
        """
        super().__init__(
            object_class=PooledEvent,
            initial_size=initial_size,
            max_size=max_size
        )
    
    def create_event(self, event_type: str, data: Dict[str, Any] = None,
                    auto_release: bool = True) -> PooledEvent:
        """Create an event from the pool.
        
        Args:
            event_type (str): Event type
            data (Dict[str, Any], optional): Event data
            auto_release (bool): Whether to auto-release
            
        Returns:
            PooledEvent: Event from pool
        """
        event = self.acquire(auto_release=auto_release)
        if isinstance(event, PooledEvent):
            event.set_event(event_type, data)
        else:
            # It's a PooledObject wrapper
            event.set_event(event_type, data)
        return event


class TemporaryObjectPool(ObjectPool[TemporaryObject]):
    """Pool for temporary calculation objects."""
    
    def __init__(self, initial_size: int = 50, max_size: int = 200):
        """Initialize temporary object pool.
        
        Args:
            initial_size (int): Initial pool size
            max_size (int): Maximum pool size
        """
        super().__init__(
            object_class=TemporaryObject,
            initial_size=initial_size,
            max_size=max_size
        )
    
    def create_temp_object(self, auto_release: bool = True, **data) -> TemporaryObject:
        """Create a temporary object from the pool.
        
        Args:
            auto_release (bool): Whether to auto-release
            **data: Temporary data to set
            
        Returns:
            TemporaryObject: Temporary object from pool
        """
        temp_obj = self.acquire(auto_release=auto_release)
        if isinstance(temp_obj, TemporaryObject):
            temp_obj.set_data(**data)
        else:
            # It's a PooledObject wrapper
            temp_obj.set_data(**data)
        return temp_obj


def create_default_pools(pool_manager: PoolManager) -> Dict[str, ObjectPool]:
    """Create default pools for common game objects.
    
    Args:
        pool_manager (PoolManager): Pool manager to register pools with
        
    Returns:
        Dict[str, ObjectPool]: Dictionary of created pools
    """
    pools = {}
    
    try:
        # Message pool
        pools['messages'] = pool_manager.create_pool(
            'messages', PooledMessage, initial_size=50, max_size=200
        )
        
        # Event pool
        pools['events'] = pool_manager.create_pool(
            'events', PooledEvent, initial_size=100, max_size=500
        )
        
        # Entity pool (for temporary entities)
        pools['temp_entities'] = pool_manager.create_pool(
            'temp_entities', PooledEntity, initial_size=20, max_size=100
        )
        
        # Component pools
        pools['fighters'] = pool_manager.create_pool(
            'fighters', PooledFighter, initial_size=30, max_size=150
        )
        
        pools['ai_components'] = pool_manager.create_pool(
            'ai_components', PooledAI, initial_size=30, max_size=150
        )
        
        pools['items'] = pool_manager.create_pool(
            'items', PooledItem, initial_size=40, max_size=200
        )
        
        # Temporary object pool
        pools['temp_objects'] = pool_manager.create_pool(
            'temp_objects', TemporaryObject, initial_size=50, max_size=200
        )
        
        logger.info(f"Created {len(pools)} default pools")
        
    except Exception as e:
        logger.error(f"Error creating default pools: {e}")
        raise
    
    return pools


def get_pool_recommendations() -> Dict[str, Dict[str, Any]]:
    """Get recommendations for pool configurations based on game analysis.
    
    Returns:
        Dict[str, Dict[str, Any]]: Pool configuration recommendations
    """
    return {
        'messages': {
            'description': 'Combat messages, notifications, and UI text',
            'estimated_usage': 'High - created every combat action and game event',
            'recommended_initial': 50,
            'recommended_max': 200,
            'memory_savings': 'High - messages are created frequently in combat'
        },
        'events': {
            'description': 'Game events for the event system',
            'estimated_usage': 'Very High - core communication mechanism',
            'recommended_initial': 100,
            'recommended_max': 500,
            'memory_savings': 'Very High - events are created constantly'
        },
        'temp_entities': {
            'description': 'Temporary entities for calculations and effects',
            'estimated_usage': 'Medium - pathfinding, FOV, and effect calculations',
            'recommended_initial': 20,
            'recommended_max': 100,
            'memory_savings': 'Medium - reduces entity allocation overhead'
        },
        'fighters': {
            'description': 'Fighter components for combat entities',
            'estimated_usage': 'Medium - monsters and combat NPCs',
            'recommended_initial': 30,
            'recommended_max': 150,
            'memory_savings': 'Medium - reused when monsters die and respawn'
        },
        'ai_components': {
            'description': 'AI components for intelligent entities',
            'estimated_usage': 'Medium - monsters and NPCs',
            'recommended_initial': 30,
            'recommended_max': 150,
            'memory_savings': 'Medium - reused for monster AI state'
        },
        'items': {
            'description': 'Item components for consumables and equipment',
            'estimated_usage': 'High - potions, scrolls, and temporary items',
            'recommended_initial': 40,
            'recommended_max': 200,
            'memory_savings': 'High - many temporary items created and destroyed'
        },
        'temp_objects': {
            'description': 'Generic temporary objects for calculations',
            'estimated_usage': 'High - pathfinding, algorithms, and temporary data',
            'recommended_initial': 50,
            'recommended_max': 200,
            'memory_savings': 'High - eliminates many small object allocations'
        }
    }
