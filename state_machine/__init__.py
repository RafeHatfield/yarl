"""Enhanced state management system for game components.

This package provides a sophisticated state machine system that integrates
with the event system to provide hierarchical states, smooth transitions,
state persistence, and better organization of game logic.

Key Components:
- StateMachine: Core state machine engine with transition management
- State: Abstract state interface with enter/exit/update lifecycle
- StateTransition: Event-driven transitions with guards and actions
- HierarchicalState: Nested states with parent-child relationships
- StateManager: Enhanced integration with existing GameStateManager
- StatePersistence: Save/load state information
"""

from .core import (
    State, StateMachine, StateTransition, TransitionGuard, TransitionAction,
    StateContext, StateResult, StateMachineError
)
from .hierarchical import HierarchicalState, StateHierarchy, CompositeState
from .manager import EnhancedStateManager, StateManagerConfig, StateManagerMode
from .persistence import (
    StatePersistence, StateSnapshot, PersistenceError, 
    JsonPersistenceBackend, create_json_persistence
)
from .game_states import (
    GameStateMachine, GameStateContext, BaseGameState,
    PlayerTurnState, EnemyTurnState, InventoryState, TargetingState,
    CharacterScreenState, PlayerDeadState, LevelUpState
)
from .transitions import (
    StateTransitionBuilder, ConditionalTransition, TimedTransition,
    EventTriggeredTransition, create_transition
)
from .events import (
    StateEvent, StateEventType, StateChangeEvent, StateTransitionEvent,
    create_state_change_event, create_state_transition_event, create_state_request_event,
    create_state_lifecycle_event, create_state_error_event, create_hierarchical_state_event
)

__all__ = [
    # Core
    'State',
    'StateMachine',
    'StateTransition',
    'TransitionGuard',
    'TransitionAction',
    'StateContext',
    'StateResult',
    'StateMachineError',
    
    # Hierarchical
    'HierarchicalState',
    'StateHierarchy',
    'CompositeState',
    
    # Manager
    'EnhancedStateManager',
    'StateManagerConfig',
    'StateManagerMode',
    
    # Persistence
    'StatePersistence',
    'StateSnapshot',
    'PersistenceError',
    'JsonPersistenceBackend',
    'create_json_persistence',
    
    # Game States
    'GameStateMachine',
    'GameStateContext',
    'BaseGameState',
    'PlayerTurnState',
    'EnemyTurnState',
    'InventoryState',
    'TargetingState',
    'CharacterScreenState',
    'PlayerDeadState',
    'LevelUpState',
    
    # Transitions
    'StateTransitionBuilder',
    'ConditionalTransition',
    'TimedTransition',
    'EventTriggeredTransition',
    'create_transition',
    
    # Events
    'StateEvent',
    'StateEventType',
    'StateChangeEvent',
    'StateTransitionEvent',
    'create_state_change_event',
    'create_state_transition_event',
    'create_state_request_event',
    'create_state_lifecycle_event',
    'create_state_error_event',
    'create_hierarchical_state_event',
]
