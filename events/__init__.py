"""Event-driven architecture system for game components.

This package provides a comprehensive event system that enables loose coupling
between game components, supports complex event patterns, and provides a
foundation for advanced game features like scripting, AI behaviors, and
dynamic content.

Key Components:
- EventBus: Central event routing and management system
- GameEvent: Base class for all game events with metadata
- EventListener: Component-based event handling interface
- EventDispatcher: Async and sync event dispatching
- EventPattern: Complex event patterns and chains
"""

from .core import Event, EventPriority, EventResult, EventContext, SimpleEvent, create_event
from .bus import EventBus, get_event_bus, initialize_event_bus, shutdown_event_bus
from .dispatcher import (
    EventDispatcher, AsyncEventDispatcher, SynchronousDispatcher, 
    QueuedDispatcher, ThreadedDispatcher, PriorityDispatcher,
    DispatchStrategy, create_dispatcher, create_async_dispatcher
)
from .listener import (
    EventListener, EventHandler, event_handler, SimpleEventListener,
    CallableEventListener, EventListenerRegistry
)
from .game_events import (
    GameEvent, GameEventType, CombatEvent, MovementEvent, InventoryEvent, LevelEvent,
    PlayerEvent, EntityEvent, SystemEvent, UIEvent,
    create_combat_event, create_movement_event, create_inventory_event,
    create_player_event, create_system_event
)
from .patterns import (
    EventChain, ConditionalEvent, DelayedEvent, RecurringEvent,
    EventSequence, EventGroup, EventPattern, PatternState,
    create_event_chain, create_delayed_event, create_recurring_event,
    create_conditional_event
)
from .exceptions import (
    EventError, EventDispatchError, EventListenerError, EventRegistrationError,
    EventValidationError, EventTimeoutError, EventCancellationError
)

__all__ = [
    # Core
    'Event',
    'EventPriority',
    'EventResult', 
    'EventContext',
    'SimpleEvent',
    'create_event',
    
    # Bus
    'EventBus',
    'get_event_bus',
    'initialize_event_bus',
    'shutdown_event_bus',
    
    # Dispatchers
    'EventDispatcher',
    'AsyncEventDispatcher',
    'SynchronousDispatcher',
    'QueuedDispatcher',
    'ThreadedDispatcher',
    'PriorityDispatcher',
    'DispatchStrategy',
    'create_dispatcher',
    'create_async_dispatcher',
    
    # Listeners
    'EventListener',
    'EventHandler',
    'event_handler',
    'SimpleEventListener',
    'CallableEventListener',
    'EventListenerRegistry',
    
    # Game Events
    'GameEvent',
    'GameEventType',
    'CombatEvent',
    'MovementEvent',
    'InventoryEvent',
    'LevelEvent',
    'PlayerEvent',
    'EntityEvent',
    'SystemEvent',
    'UIEvent',
    'create_combat_event',
    'create_movement_event',
    'create_inventory_event',
    'create_player_event',
    'create_system_event',
    
    # Patterns
    'EventChain',
    'ConditionalEvent',
    'DelayedEvent',
    'RecurringEvent',
    'EventSequence',
    'EventGroup',
    'EventPattern',
    'PatternState',
    'create_event_chain',
    'create_delayed_event',
    'create_recurring_event',
    'create_conditional_event',
    
    # Exceptions
    'EventError',
    'EventDispatchError',
    'EventListenerError',
    'EventRegistrationError',
    'EventValidationError',
    'EventTimeoutError',
    'EventCancellationError',
]
