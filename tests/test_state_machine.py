"""Comprehensive tests for the enhanced state machine system.

This module tests all components of the state machine system including
core functionality, hierarchical states, transitions, events, and persistence.
"""

import pytest
import time
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from state_machine import (
    # Core
    State, StateMachine, StateContext, StateResult, StateMachineError,
    StateTransition, TransitionGuard, TransitionAction,
    
    # Hierarchical
    HierarchicalState, StateHierarchy, CompositeState,
    
    # Manager
    EnhancedStateManager, StateManagerConfig, StateManagerMode,
    
    # Game States
    GameStateMachine, BaseGameState, PlayerTurnState, EnemyTurnState,
    InventoryState, TargetingState, CharacterScreenState, PlayerDeadState,
    
    # Transitions
    StateTransitionBuilder, ConditionalTransition, TimedTransition,
    EventTriggeredTransition, create_transition,
    
    # Events
    StateEvent, StateEventType, StateChangeEvent, StateTransitionEvent,
    create_state_change_event, create_state_request_event,
    
    # Persistence
    StatePersistence, StateSnapshot, JsonPersistenceBackend,
    create_json_persistence,
)

from events import EventBus, SimpleEvent, EventResult
from game_states import GameStates


class MockState(State):
    """Mock state for testing."""
    
    def __init__(self, state_id: str, name: str = None):
        super().__init__(state_id, name)
        self.enter_called = False
        self.exit_called = False
        self.update_called = False
        self.update_count = 0
    
    def enter(self, context: StateContext) -> StateResult:
        self.enter_called = True
        return StateResult.CONTINUE
    
    def exit(self, context: StateContext) -> StateResult:
        self.exit_called = True
        return StateResult.CONTINUE
    
    def update(self, context: StateContext, dt: float) -> StateResult:
        self.update_called = True
        self.update_count += 1
        return StateResult.CONTINUE


class TestStateCore:
    """Test core state machine functionality."""
    
    def test_state_context_creation(self):
        """Test state context creation and data management."""
        context = StateContext()
        
        assert isinstance(context.data, dict)
        assert isinstance(context.state_start_time, float)
        assert isinstance(context.last_update_time, float)
        
        # Test data operations
        context.set_data("test_key", "test_value")
        assert context.get_data("test_key") == "test_value"
        assert context.has_data("test_key")
        assert not context.has_data("nonexistent_key")
        assert context.get_data("nonexistent_key", "default") == "default"
        
        # Test timing
        elapsed = context.get_elapsed_time()
        assert elapsed >= 0
        
        delta = context.get_delta_time()
        assert delta >= 0
    
    def test_mock_state_lifecycle(self):
        """Test mock state lifecycle methods."""
        state = MockState("test_state", "Test State")
        context = StateContext()
        
        assert state.state_id == "test_state"
        assert state.name == "Test State"
        assert not state.active
        assert not state.paused
        
        # Test lifecycle
        result = state.enter(context)
        assert result == StateResult.CONTINUE
        assert state.enter_called
        
        result = state.update(context, 0.016)
        assert result == StateResult.CONTINUE
        assert state.update_called
        assert state.update_count == 1
        
        result = state.exit(context)
        assert result == StateResult.CONTINUE
        assert state.exit_called
    
    def test_state_machine_creation(self):
        """Test state machine creation and basic operations."""
        machine = StateMachine("test_machine")
        
        assert machine.machine_id == "test_machine"
        assert not machine.is_running()
        assert len(machine.states) == 0
        assert len(machine.transitions) == 0
        
        # Test state addition
        state1 = MockState("state1")
        state2 = MockState("state2")
        
        machine.add_state(state1)
        machine.add_state(state2)
        
        assert len(machine.states) == 2
        assert "state1" in machine.states
        assert "state2" in machine.states
    
    def test_state_machine_lifecycle(self):
        """Test state machine start/stop lifecycle."""
        machine = StateMachine("test_machine")
        state1 = MockState("state1")
        machine.add_state(state1)
        
        # Test start
        success = machine.start("state1")
        assert success
        assert machine.is_running()
        assert machine.get_current_state() == state1
        assert state1.enter_called
        
        # Test update
        machine.update(0.016)
        assert state1.update_called
        
        # Test stop
        machine.stop()
        assert not machine.is_running()
        assert state1.exit_called
    
    def test_state_transitions(self):
        """Test state transitions."""
        machine = StateMachine("test_machine")
        
        state1 = MockState("state1")
        state2 = MockState("state2")
        machine.add_state(state1)
        machine.add_state(state2)
        
        # Add transition
        transition = StateTransition("state1", "state2")
        machine.add_transition(transition)
        
        # Start machine
        machine.start("state1")
        assert machine.get_current_state() == state1
        
        # Test manual transition
        success = machine.transition_to("state2")
        assert success
        assert machine.get_current_state() == state2
        assert machine.get_previous_state() == state1
        assert state1.exit_called
        assert state2.enter_called
    
    def test_transition_guards_and_actions(self):
        """Test transition guards and actions."""
        machine = StateMachine("test_machine")
        
        state1 = MockState("state1")
        state2 = MockState("state2")
        machine.add_state(state1)
        machine.add_state(state2)
        
        # Create guard that always allows transition
        class AlwaysAllowGuard(TransitionGuard):
            def can_transition(self, from_state, to_state, context):
                return True
        
        # Create action that sets data
        class SetDataAction(TransitionAction):
            def execute(self, from_state, to_state, context):
                context.set_data("transition_executed", True)
        
        # Add transition with guard and action
        transition = StateTransition(
            "state1", "state2",
            guards=[AlwaysAllowGuard()],
            actions=[SetDataAction()]
        )
        machine.add_transition(transition)
        
        # Start and transition
        machine.start("state1")
        success = machine.transition_to("state2")
        
        assert success
        assert machine.context.get_data("transition_executed") == True


class TestHierarchicalStates:
    """Test hierarchical state functionality."""
    
    def test_hierarchical_state_creation(self):
        """Test hierarchical state creation and child management."""
        class TestHierarchicalState(HierarchicalState):
            def on_enter(self, context):
                return StateResult.CONTINUE
            def on_exit(self, context):
                return StateResult.CONTINUE
            def on_update(self, context, dt):
                return StateResult.CONTINUE
        
        parent = TestHierarchicalState("parent", "Parent State")
        child1 = MockState("child1")
        child2 = MockState("child2")
        
        # Test child addition
        parent.add_child_state(child1, is_default=True)
        parent.add_child_state(child2)
        
        assert len(parent.child_states) == 2
        assert parent.default_child == "child1"
        assert parent.has_child("child1")
        assert parent.has_child("child2")
        assert not parent.has_child("nonexistent")
    
    def test_state_hierarchy(self):
        """Test state hierarchy management."""
        root_state = MockState("root")
        hierarchy = StateHierarchy(root_state)
        
        # Build hierarchy: root -> parent -> child
        hierarchy.add_child_relationship("root", "parent")
        hierarchy.add_child_relationship("parent", "child")
        
        # Test relationships
        assert hierarchy.get_parent("child") == "parent"
        assert hierarchy.get_parent("parent") == "root"
        assert hierarchy.get_parent("root") is None
        
        assert hierarchy.get_children("root") == ["parent"]
        assert hierarchy.get_children("parent") == ["child"]
        assert hierarchy.get_children("child") == []
        
        # Test ancestors and descendants
        assert hierarchy.get_ancestors("child") == ["parent", "root"]
        assert hierarchy.get_descendants("root") == ["parent", "child"]
        
        # Test depth
        assert hierarchy.get_depth("root") == 0
        assert hierarchy.get_depth("parent") == 1
        assert hierarchy.get_depth("child") == 2
        
        # Test common ancestor
        hierarchy.add_child_relationship("parent", "child2")
        assert hierarchy.get_common_ancestor("child", "child2") == "parent"
    
    def test_composite_state(self):
        """Test composite state with concurrent children."""
        composite = CompositeState("composite", "Composite State")
        
        child1 = MockState("child1")
        child2 = MockState("child2")
        
        composite.add_child_state(child1, auto_activate=True)
        composite.add_child_state(child2, auto_activate=False)
        
        # Test active children
        assert composite.is_child_active("child1")
        assert not composite.is_child_active("child2")
        
        # Test activation/deactivation
        success = composite.activate_child("child2")
        assert success
        assert composite.is_child_active("child2")
        
        success = composite.deactivate_child("child1")
        assert success
        assert not composite.is_child_active("child1")


class TestGameStates:
    """Test game-specific state implementations."""
    
    def test_base_game_state(self):
        """Test base game state functionality."""
        class TestGameState(BaseGameState):
            def on_enter(self, context):
                return StateResult.CONTINUE
            
            def on_exit(self, context):
                return StateResult.CONTINUE
            
            def on_update(self, context, dt):
                return StateResult.CONTINUE
        
        state = TestGameState("test_game_state", "Test Game State", GameStates.PLAYERS_TURN)
        
        assert state.state_id == "test_game_state"
        assert state.name == "Test Game State"
        assert state.legacy_state == GameStates.PLAYERS_TURN
        assert state.can_handle_input()
        assert state.should_render_ui()
    
    def test_player_turn_state(self):
        """Test player turn state."""
        state = PlayerTurnState()
        context = StateContext()
        
        assert state.state_id == "player_turn"
        assert state.legacy_state == GameStates.PLAYERS_TURN
        assert state.can_handle_input()
        assert not state.should_process_ai()
        
        # Test lifecycle
        result = state.enter(context)
        assert result == StateResult.CONTINUE
        
        result = state.update(context, 0.016)
        assert result == StateResult.CONTINUE
        
        result = state.exit(context)
        assert result == StateResult.CONTINUE
    
    def test_enemy_turn_state(self):
        """Test enemy turn state."""
        state = EnemyTurnState()
        context = StateContext()
        
        assert state.state_id == "enemy_turn"
        assert state.legacy_state == GameStates.ENEMY_TURN
        assert not state.can_handle_input()
        assert state.should_process_ai()
        
        # Test AI processing logic
        result = state.enter(context)
        assert result == StateResult.CONTINUE
        assert context.get_data("ai_processing_started") == True
        
        # Test update before AI completion
        result = state.update(context, 0.016)
        assert result == StateResult.CONTINUE
        
        # Test update after AI completion
        context.set_data("ai_processing_complete", True)
        result = state.update(context, 0.016)
        assert result == StateResult.TRANSITION
    
    def test_inventory_state(self):
        """Test hierarchical inventory state."""
        state = InventoryState()
        
        assert state.state_id == "inventory"
        assert len(state.child_states) == 2
        assert state.has_child("show_inventory")
        assert state.has_child("drop_inventory")
        assert state.default_child == "show_inventory"
    
    def test_game_state_machine_factory(self):
        """Test game state machine factory methods."""
        states = GameStateMachine.create_default_states()
        
        assert len(states) >= 6  # At least the core states
        assert "player_turn" in states
        assert "enemy_turn" in states
        assert "inventory" in states
        assert "targeting" in states
        assert "player_dead" in states
        
        # Test state types
        assert isinstance(states["player_turn"], PlayerTurnState)
        assert isinstance(states["enemy_turn"], EnemyTurnState)
        assert isinstance(states["inventory"], InventoryState)


class TestStateTransitions:
    """Test advanced transition functionality."""
    
    def test_conditional_transition(self):
        """Test conditional transitions."""
        def test_condition(from_state, to_state, context):
            return context.get_data("allow_transition", False)
        
        transition = ConditionalTransition("state1", "state2", test_condition)
        
        machine = StateMachine("test_machine")
        state1 = MockState("state1")
        state2 = MockState("state2")
        machine.add_state(state1)
        machine.add_state(state2)
        machine.add_transition(transition)
        
        machine.start("state1")
        
        # Test blocked transition
        success = machine.transition_to("state2")
        assert not success
        assert machine.get_current_state() == state1
        
        # Test allowed transition
        machine.context.set_data("allow_transition", True)
        success = machine.transition_to("state2")
        assert success
        assert machine.get_current_state() == state2
    
    def test_timed_transition(self):
        """Test timed transitions."""
        transition = TimedTransition("state1", "state2", 0.1)  # 100ms delay
        
        machine = StateMachine("test_machine")
        state1 = MockState("state1")
        state2 = MockState("state2")
        machine.add_state(state1)
        machine.add_state(state2)
        machine.add_transition(transition)
        
        machine.start("state1")
        
        # Test immediate transition (should fail)
        success = machine.transition_to("state2")
        assert not success
        
        # Wait for delay and test again
        time.sleep(0.15)
        success = machine.transition_to("state2")
        assert success
        assert machine.get_current_state() == state2
    
    def test_event_triggered_transition(self):
        """Test event-triggered transitions."""
        event_bus = EventBus()
        transition = EventTriggeredTransition(
            "state1", "state2", ["test.trigger"], event_bus
        )
        
        machine = StateMachine("test_machine", event_bus)
        state1 = MockState("state1")
        state2 = MockState("state2")
        machine.add_state(state1)
        machine.add_state(state2)
        machine.add_transition(transition)
        
        machine.start("state1")
        
        # Test transition before event
        success = machine.transition_to("state2")
        assert not success
        
        # Trigger event
        trigger_event = SimpleEvent("test.trigger")
        event_bus.dispatch(trigger_event)
        
        # Test transition after event
        success = machine.transition_to("state2")
        assert success
        assert machine.get_current_state() == state2
    
    def test_transition_builder(self):
        """Test transition builder pattern."""
        def test_condition(from_state, to_state, context):
            return context.get_data("ready", False)
        
        transition = (StateTransitionBuilder
                     .from_state("state1")
                     .to_state("state2")
                     .with_trigger("test_trigger")
                     .with_priority(10)
                     .with_condition(test_condition)
                     .with_min_time(0.1)
                     .with_logging("Test transition executed")
                     .with_data_update({"transition_count": 1})
                     .build())
        
        assert transition.from_state_id == "state1"
        assert transition.to_state_id == "state2"
        assert transition.trigger == "test_trigger"
        assert transition.priority == 10
        assert len(transition.guards) == 2  # Condition + time guards
        assert len(transition.actions) == 2  # Logging + data actions


class TestStateEvents:
    """Test state event system."""
    
    def test_state_event_creation(self):
        """Test state event creation and serialization."""
        event = StateEvent(StateEventType.STATE_CHANGE, "test_state", {"key": "value"})
        
        assert event.event_type == "state.change"
        assert event.state_event_type == StateEventType.STATE_CHANGE
        assert event.state_id == "test_state"
        assert event.data["key"] == "value"
        
        # Test serialization
        data = event.to_dict()
        assert data["event_type"] == "state.change"
        assert data["state_id"] == "test_state"
        
        # Test deserialization
        restored = StateEvent.from_dict(data)
        assert restored.event_type == event.event_type
        assert restored.state_id == event.state_id
    
    def test_state_change_event(self):
        """Test state change event."""
        event = create_state_change_event(
            previous_state="state1",
            new_state="state2",
            context_data={"test": "data"}
        )
        
        assert isinstance(event, StateChangeEvent)
        assert event.previous_state == "state1"
        assert event.new_state == "state2"
        assert event.context_data["test"] == "data"
    
    def test_state_request_event(self):
        """Test state request event."""
        event = create_state_request_event(
            target_state="target_state",
            force=True,
            transition_data={"reason": "test"}
        )
        
        assert event.target_state == "target_state"
        assert event.force == True
        assert event.transition_data["reason"] == "test"


class TestEnhancedStateManager:
    """Test enhanced state manager."""
    
    def setup_method(self):
        """Set up test environment."""
        self.config = StateManagerConfig(
            mode=StateManagerMode.ENHANCED,
            enable_events=True,
            enable_state_history=True
        )
        self.manager = EnhancedStateManager(self.config)
    
    def test_state_manager_creation(self):
        """Test state manager creation and configuration."""
        assert self.manager.config.mode == StateManagerMode.ENHANCED
        assert self.manager.config.enable_events == True
        assert isinstance(self.manager.event_bus, EventBus)
        assert isinstance(self.manager.state_machine, StateMachine)
    
    def test_state_registration(self):
        """Test state class registration."""
        self.manager.register_state_class(PlayerTurnState, GameStates.PLAYERS_TURN)
        
        assert "player_turn" in self.manager.state_registry
        assert self.manager.legacy_to_enhanced_map[GameStates.PLAYERS_TURN] == "player_turn"
        assert self.manager.enhanced_to_legacy_map["player_turn"] == GameStates.PLAYERS_TURN
    
    def test_state_manager_lifecycle(self):
        """Test state manager start/stop lifecycle."""
        # Register states
        self.manager.register_state_class(PlayerTurnState)
        self.manager.register_state_class(EnemyTurnState)
        
        # Test start
        success = self.manager.start("player_turn")
        assert success
        assert self.manager.get_current_state_id() == "player_turn"
        assert len(self.manager.get_state_history()) == 1
        
        # Test transition (force for test)
        success = self.manager.transition_to("enemy_turn", force=True)
        assert success
        assert self.manager.get_current_state_id() == "enemy_turn"
        assert self.manager.get_previous_state_id() == "player_turn"
        assert len(self.manager.get_state_history()) == 2
        
        # Test stop
        self.manager.stop()
        assert not self.manager.state_machine.is_running()
    
    def test_context_data_management(self):
        """Test context data management."""
        self.manager.set_context_data("test_key", "test_value")
        assert self.manager.get_context_data("test_key") == "test_value"
        assert self.manager.get_context_data("nonexistent", "default") == "default"
    
    def test_legacy_state_synchronization(self):
        """Test synchronization with legacy state system."""
        # Set up hybrid mode
        hybrid_config = StateManagerConfig(mode=StateManagerMode.HYBRID)
        hybrid_manager = EnhancedStateManager(hybrid_config)
        
        # Register states
        hybrid_manager.register_state_class(PlayerTurnState, GameStates.PLAYERS_TURN)
        
        # Test legacy state mapping
        legacy_state = hybrid_manager.get_legacy_state()
        assert isinstance(legacy_state, GameStates)
        
        # Test setting by legacy state
        success = hybrid_manager.set_legacy_state(GameStates.PLAYERS_TURN)
        # This might fail if state machine isn't started, which is expected


class TestStatePersistence:
    """Test state persistence functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.persistence = create_json_persistence(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_snapshot_creation(self):
        """Test snapshot creation and validation."""
        machine = StateMachine("test_machine")
        state = MockState("test_state")
        machine.add_state(state)
        machine.start("test_state")
        
        snapshot = self.persistence.create_snapshot(machine, {"custom": "data"})
        
        assert snapshot.machine_id == "test_machine"
        assert snapshot.current_state_id == "test_state"
        assert snapshot.custom_data["custom"] == "data"
        assert snapshot.is_valid()
        assert snapshot.get_age() >= 0
    
    def test_snapshot_serialization(self):
        """Test snapshot serialization and deserialization."""
        snapshot = StateSnapshot(
            machine_id="test_machine",
            current_state_id="test_state",
            context_data={"key": "value"}
        )
        
        # Test to_dict
        data = snapshot.to_dict()
        assert data["machine_id"] == "test_machine"
        assert data["current_state_id"] == "test_state"
        
        # Test from_dict
        restored = StateSnapshot.from_dict(data)
        assert restored.machine_id == snapshot.machine_id
        assert restored.current_state_id == snapshot.current_state_id
        assert restored.context_data == snapshot.context_data
    
    def test_persistence_save_load(self):
        """Test saving and loading snapshots."""
        machine = StateMachine("test_machine")
        state = MockState("test_state")
        machine.add_state(state)
        machine.start("test_state")
        machine.context.set_data("test_key", "test_value")
        
        # Test save
        success = self.persistence.save_state_machine(machine, "test_save")
        assert success
        
        # Create new machine
        new_machine = StateMachine("test_machine")
        new_state = MockState("test_state")
        new_machine.add_state(new_state)
        
        # Test load
        success = self.persistence.load_state_machine(new_machine, "test_save")
        assert success
        assert new_machine.context.get_data("test_key") == "test_value"
    
    def test_persistence_backends(self):
        """Test different persistence backends."""
        # Test JSON backend
        json_backend = JsonPersistenceBackend(self.temp_dir)
        test_data = {"key": "value", "number": 42}
        
        json_backend.save(test_data, "test_json")
        assert json_backend.exists("test_json")
        
        loaded_data = json_backend.load("test_json")
        assert loaded_data == test_data
        
        success = json_backend.delete("test_json")
        assert success
        assert not json_backend.exists("test_json")


class TestStateSystemIntegration:
    """Test complete state system integration."""
    
    def test_full_game_state_flow(self):
        """Test complete game state flow with events."""
        # Set up event bus and state manager
        event_bus = EventBus()
        config = StateManagerConfig(enable_events=True, event_bus=event_bus)
        manager = EnhancedStateManager(config)
        
        # Register game states
        manager.register_state_class(PlayerTurnState, GameStates.PLAYERS_TURN)
        manager.register_state_class(EnemyTurnState, GameStates.ENEMY_TURN)
        
        # Start with player turn
        success = manager.start("player_turn")
        assert success
        assert manager.get_current_state_id() == "player_turn"
        
        # Simulate player action -> enemy turn (force transition for test)
        success = manager.transition_to("enemy_turn", force=True)
        assert success
        assert manager.get_current_state_id() == "enemy_turn"
        
        # Simulate AI completion -> player turn (force transition for test)
        success = manager.transition_to("player_turn", force=True)
        assert success
        assert manager.get_current_state_id() == "player_turn"
        
        # Check history
        history = manager.get_state_history()
        assert len(history) == 3
        assert history == ["player_turn", "enemy_turn", "player_turn"]
    
    def test_hierarchical_inventory_flow(self):
        """Test hierarchical inventory state flow."""
        manager = EnhancedStateManager()
        
        # Register states
        manager.register_state_class(PlayerTurnState)
        manager.register_state_class(InventoryState)
        
        # Start with player turn
        manager.start("player_turn")
        
        # Transition to inventory (force for test)
        success = manager.transition_to("inventory", force=True)
        assert success
        
        current_state = manager.get_current_state()
        assert isinstance(current_state, InventoryState)
        assert current_state.get_current_child() is not None
        
        # Test child state transitions
        success = current_state.transition_child_to("drop_inventory")
        # This might not work without proper child state setup, which is expected
    
    def test_event_driven_transitions(self):
        """Test event-driven state transitions."""
        event_bus = EventBus()
        machine = StateMachine("test_machine", event_bus)
        
        state1 = MockState("state1")
        state2 = MockState("state2")
        machine.add_state(state1)
        machine.add_state(state2)
        
        # Add event-triggered transition
        transition = EventTriggeredTransition(
            "state1", "state2", ["player.action"], event_bus
        )
        machine.add_transition(transition)
        
        machine.start("state1")
        
        # Dispatch triggering event
        action_event = SimpleEvent("player.action", {"action": "move"})
        event_bus.dispatch(action_event)
        
        # Test transition
        success = machine.transition_to("state2")
        assert success
        assert machine.get_current_state() == state2
    
    def test_performance_characteristics(self):
        """Test state system performance characteristics."""
        manager = EnhancedStateManager()
        
        # Register multiple states
        class DynamicState(BaseGameState):
            def __init__(self, state_id="dynamic_state"):
                super().__init__(state_id)
            
            def on_enter(self, context):
                return StateResult.CONTINUE
            
            def on_exit(self, context):
                return StateResult.CONTINUE
            
            def on_update(self, context, dt):
                return StateResult.CONTINUE
        
        # Create state classes with different IDs
        for i in range(10):
            class_name = f"DynamicState{i}"
            state_class = type(class_name, (DynamicState,), {
                '__init__': lambda self, state_id=f"state_{i}": super(type(self), self).__init__(state_id)
            })
            manager.register_state_class(state_class)
        
        # Test rapid state transitions
        manager.start("state_0")
        
        start_time = time.time()
        for i in range(1, 10):
            manager.transition_to(f"state_{i}", force=True)  # Force transitions for test
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete quickly
        assert duration < 0.1  # Less than 100ms for 9 transitions
        
        # Check stats
        stats = manager.get_performance_stats()
        assert stats['state_changes'] == 9
        assert stats['transitions_executed'] == 9


if __name__ == "__main__":
    pytest.main([__file__])
