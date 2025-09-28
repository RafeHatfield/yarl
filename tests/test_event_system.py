"""Comprehensive tests for the event system.

This module tests all components of the event-driven architecture,
including events, listeners, bus, dispatchers, and patterns.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

from events import (
    Event, EventPriority, EventResult, EventContext, SimpleEvent, create_event,
    EventBus, get_event_bus, initialize_event_bus,
    EventListener, SimpleEventListener, CallableEventListener, event_handler,
    GameEvent, GameEventType, CombatEvent, MovementEvent, InventoryEvent,
    create_combat_event, create_movement_event, create_inventory_event,
    EventChain, DelayedEvent, RecurringEvent, ConditionalEvent,
    create_event_chain, create_delayed_event, create_recurring_event,
    SynchronousDispatcher, QueuedDispatcher, ThreadedDispatcher,
    EventError, EventDispatchError, EventListenerError
)


class TestEventCore:
    """Test core event functionality."""
    
    def test_event_context_creation(self):
        """Test event context creation and metadata."""
        context = EventContext(source="test", target="target")
        
        assert context.source == "test"
        assert context.target == "target"
        assert context.priority == EventPriority.NORMAL
        assert isinstance(context.timestamp, float)
        assert isinstance(context.trace_id, str)
        
        # Test metadata
        context.add_metadata("key", "value")
        assert context.get_metadata("key") == "value"
        assert context.has_metadata("key")
        assert not context.has_metadata("nonexistent")
    
    def test_simple_event_creation(self):
        """Test simple event creation and validation."""
        event = SimpleEvent("test.event", {"data": "value"})
        
        assert event.event_type == "test.event"
        assert event.data["data"] == "value"
        assert not event.is_cancelled()
        assert not event.is_consumed()
        assert not event.is_handled()
        
        # Test validation
        errors = event.validate()
        assert len(errors) == 0
        
        # Test invalid event
        invalid_event = SimpleEvent("", "not_dict")
        errors = invalid_event.validate()
        assert len(errors) == 2
    
    def test_event_state_management(self):
        """Test event state changes."""
        event = SimpleEvent("test.event")
        
        # Test cancellation
        event.cancel("test reason")
        assert event.is_cancelled()
        assert event.result == EventResult.CANCELLED
        assert event.context.get_metadata("cancellation_reason") == "test reason"
        
        # Test consumption
        event2 = SimpleEvent("test.event2")
        event2.consume()
        assert event2.is_consumed()
        
        # Test handling
        event3 = SimpleEvent("test.event3")
        event3.mark_handled()
        assert event3.is_handled()
        
        # Test error
        event4 = SimpleEvent("test.event4")
        error = ValueError("test error")
        event4.set_error(error)
        assert event4.has_error()
        assert event4.error == error
    
    def test_event_processing_chain(self):
        """Test event processing chain tracking."""
        event = SimpleEvent("test.event")
        
        event.add_processor("processor1")
        event.add_processor("processor2")
        event.add_processor("processor1")  # Should not duplicate
        
        assert event.was_processed_by("processor1")
        assert event.was_processed_by("processor2")
        assert not event.was_processed_by("processor3")
        
        chain = event.get_processing_chain()
        assert len(chain) == 2
        assert "processor1" in chain
        assert "processor2" in chain
    
    def test_event_serialization(self):
        """Test event serialization and deserialization."""
        original = SimpleEvent("test.event", {"key": "value"})
        original.context.source = "source"
        original.context.target = "target"
        
        # Serialize
        data = original.to_dict()
        assert data["event_type"] == "test.event"
        assert data["data"]["key"] == "value"
        assert data["context"]["source"] == "source"
        
        # Deserialize
        restored = SimpleEvent.from_dict(data)
        assert restored.event_type == original.event_type
        assert restored.data == original.data
        assert restored.context.source == original.context.source
    
    def test_event_cloning(self):
        """Test event cloning."""
        original = SimpleEvent("test.event", {"key": "value"})
        original.add_processor("processor1")
        original.mark_handled()
        
        cloned = original.clone()
        
        assert cloned.event_type == original.event_type
        assert cloned.data == original.data
        assert cloned.result == original.result
        assert cloned.processed_by == original.processed_by
        assert cloned.trace_id != original.trace_id  # Should have new trace ID
    
    def test_create_event_helper(self):
        """Test create_event helper function."""
        event = create_event(
            "test.event",
            {"key": "value"},
            source="source",
            target="target",
            priority=EventPriority.HIGH
        )
        
        assert event.event_type == "test.event"
        assert event.data["key"] == "value"
        assert event.source == "source"
        assert event.target == "target"
        assert event.priority == EventPriority.HIGH


class TestEventListener:
    """Test event listener functionality."""
    
    def test_simple_event_listener(self):
        """Test simple event listener."""
        listener = SimpleEventListener("test_listener", ["test.event"])
        
        assert listener.listener_id == "test_listener"
        assert listener.is_enabled()
        assert listener.get_handled_events() == ["test.event"]
        assert listener.get_priority() == EventPriority.NORMAL
        
        # Test enable/disable
        listener.disable()
        assert not listener.is_enabled()
        listener.enable()
        assert listener.is_enabled()
    
    def test_event_handler_decorator(self):
        """Test event handler decorator."""
        
        class TestListener(SimpleEventListener):
            def __init__(self):
                super().__init__("test", ["test.event", "other.event"])
                self.handled_events = []
            
            @event_handler("test.event")
            def handle_test_event(self, event):
                self.handled_events.append(event.event_type)
                return EventResult.HANDLED
            
            @event_handler("other.event", priority=EventPriority.HIGH)
            def handle_other_event(self, event):
                self.handled_events.append(event.event_type)
                return EventResult.CONSUMED
        
        listener = TestListener()
        
        # Check handler discovery
        handler_info = listener.get_handler_info()
        assert "test.event" in handler_info
        assert "other.event" in handler_info
        
        # Test event handling
        test_event = SimpleEvent("test.event")
        result = listener.handle_event(test_event)
        assert result == EventResult.HANDLED
        assert "test.event" in listener.handled_events
        
        other_event = SimpleEvent("other.event")
        result = listener.handle_event(other_event)
        assert result == EventResult.CONSUMED
        assert "other.event" in listener.handled_events
    
    def test_callable_event_listener(self):
        """Test callable event listener."""
        handled_events = []
        
        def handler(event):
            handled_events.append(event.event_type)
            return EventResult.HANDLED
        
        listener = CallableEventListener(
            ["test.event"],
            handler,
            "callable_listener",
            EventPriority.HIGH
        )
        
        assert listener.listener_id == "callable_listener"
        assert listener.get_priority() == EventPriority.HIGH
        assert listener.get_handled_events() == ["test.event"]
        
        # Test handling
        event = SimpleEvent("test.event")
        result = listener.handle_event(event)
        assert result == EventResult.HANDLED
        assert "test.event" in handled_events
    
    def test_listener_error_handling(self):
        """Test listener error handling."""
        
        class ErrorListener(SimpleEventListener):
            def __init__(self):
                super().__init__("error_listener", ["test.event"])
            
            @event_handler("test.event")
            def handle_event_with_error(self, event):
                raise ValueError("Test error")
        
        listener = ErrorListener()
        event = SimpleEvent("test.event")
        
        result = listener.handle_event(event)
        assert result == EventResult.ERROR
        assert event.has_error()
        assert isinstance(event.error, ValueError)


class TestEventBus:
    """Test event bus functionality."""
    
    def setup_method(self):
        """Set up test event bus."""
        self.event_bus = EventBus()
        self.handled_events = []
        
        # Create test listener
        def handler(event):
            self.handled_events.append(event.event_type)
            return EventResult.HANDLED
        
        self.listener = CallableEventListener(
            ["test.event", "other.event"],
            handler,
            "test_listener"
        )
        
        self.event_bus.register_listener(self.listener)
    
    def test_listener_registration(self):
        """Test listener registration and unregistration."""
        # Test registration
        listeners = self.event_bus.get_listeners("test.event")
        assert len(listeners) == 1
        assert listeners[0] == self.listener
        
        # Test unregistration
        success = self.event_bus.unregister_listener("test_listener")
        assert success
        
        listeners = self.event_bus.get_listeners("test.event")
        assert len(listeners) == 0
        
        # Test unregistering non-existent listener
        success = self.event_bus.unregister_listener("nonexistent")
        assert not success
    
    def test_event_dispatch(self):
        """Test event dispatching."""
        event = SimpleEvent("test.event", {"data": "value"})
        
        result = self.event_bus.dispatch(event)
        assert result == EventResult.HANDLED
        assert "test.event" in self.handled_events
        assert event.was_processed_by("test_listener")
    
    def test_async_dispatch(self):
        """Test asynchronous event dispatching."""
        event = SimpleEvent("test.event")
        
        # Dispatch async (should queue)
        self.event_bus.dispatch_async(event)
        assert self.event_bus.get_queue_size() == 1
        
        # Process queue
        processed = self.event_bus.process_queued_events()
        assert processed == 1
        assert "test.event" in self.handled_events
    
    def test_event_filtering(self):
        """Test event filtering."""
        # Add filter that blocks events with "block" in data
        def filter_func(event):
            return event.data.get("action") != "block"
        
        self.event_bus.add_filter(filter_func)
        
        # Test allowed event
        allowed_event = SimpleEvent("test.event", {"action": "allow"})
        result = self.event_bus.dispatch(allowed_event)
        assert result == EventResult.HANDLED
        
        # Test blocked event
        blocked_event = SimpleEvent("test.event", {"action": "block"})
        result = self.event_bus.dispatch(blocked_event)
        assert result == EventResult.CONTINUE
        
        # Remove filter
        success = self.event_bus.remove_filter(filter_func)
        assert success
    
    def test_event_hooks(self):
        """Test pre and post dispatch hooks."""
        pre_hook_called = []
        post_hook_called = []
        
        def pre_hook(event):
            pre_hook_called.append(event.event_type)
        
        def post_hook(event, result):
            post_hook_called.append((event.event_type, result))
        
        self.event_bus.add_pre_dispatch_hook(pre_hook)
        self.event_bus.add_post_dispatch_hook(post_hook)
        
        event = SimpleEvent("test.event")
        result = self.event_bus.dispatch(event)
        
        assert "test.event" in pre_hook_called
        assert ("test.event", EventResult.HANDLED) in post_hook_called
    
    def test_event_bus_stats(self):
        """Test event bus statistics."""
        # Dispatch some events
        for i in range(5):
            event = SimpleEvent("test.event", {"index": i})
            self.event_bus.dispatch(event)
        
        stats = self.event_bus.get_stats()
        assert stats['events_dispatched'] == 5
        assert stats['listeners_notified'] == 5
        assert stats['events_by_type']['test.event'] == 5
        assert stats['avg_processing_time'] > 0
        
        # Reset stats
        self.event_bus.reset_stats()
        stats = self.event_bus.get_stats()
        assert stats['events_dispatched'] == 0
    
    def test_event_bus_enable_disable(self):
        """Test event bus enable/disable."""
        event = SimpleEvent("test.event")
        
        # Disable bus
        self.event_bus.disable()
        result = self.event_bus.dispatch(event)
        assert result == EventResult.CONTINUE
        assert len(self.handled_events) == 0
        
        # Re-enable bus
        self.event_bus.enable()
        result = self.event_bus.dispatch(event)
        assert result == EventResult.HANDLED
        assert "test.event" in self.handled_events


class TestGameEvents:
    """Test game-specific events."""
    
    def test_game_event_creation(self):
        """Test game event creation."""
        event = GameEvent(GameEventType.COMBAT_ATTACK, {"damage": 10})
        
        assert event.event_type == "combat.attack"
        assert event.game_event_type == GameEventType.COMBAT_ATTACK
        assert event.data["damage"] == 10
    
    def test_combat_event(self):
        """Test combat event."""
        event = CombatEvent(
            GameEventType.COMBAT_ATTACK,
            attacker_id="player",
            target_id="monster",
            damage=15,
            critical_hit=True
        )
        
        assert event.attacker_id == "player"
        assert event.target_id == "monster"
        assert event.damage == 15
        assert event.critical_hit
        
        # Test validation
        errors = event.validate()
        assert len(errors) == 0
        
        # Test invalid combat event
        invalid_event = CombatEvent(GameEventType.COMBAT_DAMAGE, damage=-5)
        errors = invalid_event.validate()
        assert len(errors) > 0
    
    def test_movement_event(self):
        """Test movement event."""
        event = MovementEvent(
            GameEventType.MOVEMENT_MOVE,
            entity_id="player",
            from_x=5, from_y=5,
            to_x=6, to_y=5
        )
        
        assert event.entity_id == "player"
        assert event.from_x == 5
        assert event.to_x == 6
    
    def test_inventory_event(self):
        """Test inventory event."""
        event = InventoryEvent(
            GameEventType.INVENTORY_PICKUP,
            entity_id="player",
            item_name="Health Potion",
            quantity=2
        )
        
        assert event.entity_id == "player"
        assert event.item_name == "Health Potion"
        assert event.quantity == 2
        
        # Test validation
        errors = event.validate()
        assert len(errors) == 0
        
        # Test invalid inventory event
        invalid_event = InventoryEvent(GameEventType.INVENTORY_DROP, quantity=0)
        errors = invalid_event.validate()
        assert len(errors) > 0
    
    def test_event_creation_helpers(self):
        """Test event creation helper functions."""
        # Combat event
        combat_event = create_combat_event(
            GameEventType.COMBAT_ATTACK,
            attacker_id="player",
            target_id="monster",
            damage=10
        )
        assert isinstance(combat_event, CombatEvent)
        assert combat_event.damage == 10
        
        # Movement event
        movement_event = create_movement_event(
            GameEventType.MOVEMENT_MOVE,
            entity_id="player",
            from_pos=(1, 2),
            to_pos=(3, 4)
        )
        assert isinstance(movement_event, MovementEvent)
        assert movement_event.from_x == 1
        assert movement_event.to_x == 3
        
        # Inventory event
        inventory_event = create_inventory_event(
            GameEventType.INVENTORY_PICKUP,
            entity_id="player",
            item_name="Sword"
        )
        assert isinstance(inventory_event, InventoryEvent)
        assert inventory_event.item_name == "Sword"


class TestEventPatterns:
    """Test event patterns."""
    
    def setup_method(self):
        """Set up test environment."""
        self.event_bus = EventBus()
        self.handled_events = []
        
        def handler(event):
            self.handled_events.append(event.event_type)
            return EventResult.HANDLED
        
        listener = CallableEventListener(
            ["test.event1", "test.event2", "test.event3"],
            handler,
            "test_listener"
        )
        self.event_bus.register_listener(listener)
    
    def test_event_chain(self):
        """Test event chain pattern."""
        events = [
            SimpleEvent("test.event1"),
            SimpleEvent("test.event2"),
            SimpleEvent("test.event3")
        ]
        
        chain = EventChain(events, event_bus=self.event_bus)
        
        assert not chain.is_active()
        assert not chain.is_completed()
        
        # Start chain
        success = chain.start()
        assert success
        
        # Chain executes synchronously, so it should be completed immediately
        # Wait a tiny bit to ensure all events are processed
        time.sleep(0.01)
        assert chain.is_completed()
        assert len(self.handled_events) == 3
        assert chain.get_progress() == 1.0
    
    def test_delayed_event(self):
        """Test delayed event pattern."""
        event = SimpleEvent("test.event1")
        delayed = DelayedEvent(event, 0.05, event_bus=self.event_bus)  # 50ms delay
        
        # Start delayed event
        success = delayed.start()
        assert success
        assert delayed.is_active()
        assert len(self.handled_events) == 0
        
        # Wait for execution
        time.sleep(0.1)
        assert delayed.is_completed()
        assert "test.event1" in self.handled_events
    
    def test_recurring_event(self):
        """Test recurring event pattern."""
        event = SimpleEvent("test.event1")
        recurring = RecurringEvent(
            event, 0.02, max_occurrences=3, event_bus=self.event_bus
        )  # 20ms interval, 3 occurrences
        
        # Start recurring event
        success = recurring.start()
        assert success
        assert recurring.is_active()
        
        # Wait for completion
        time.sleep(0.1)
        assert recurring.is_completed()
        assert recurring.get_occurrence_count() == 3
        assert self.handled_events.count("test.event1") == 3
    
    def test_conditional_event(self):
        """Test conditional event pattern."""
        condition_met = False
        
        def condition():
            return condition_met
        
        event = SimpleEvent("test.event1")
        conditional = ConditionalEvent(
            event, condition, check_interval=0.01, event_bus=self.event_bus
        )
        
        # Start conditional event
        success = conditional.start()
        assert success
        assert conditional.is_active()
        
        # Condition not met yet
        time.sleep(0.05)
        assert conditional.is_active()
        assert len(self.handled_events) == 0
        
        # Meet condition
        condition_met = True
        time.sleep(0.05)
        assert conditional.is_completed()
        assert "test.event1" in self.handled_events
    
    def test_pattern_cancellation(self):
        """Test pattern cancellation."""
        event = SimpleEvent("test.event1")
        delayed = DelayedEvent(event, 0.1, event_bus=self.event_bus)  # 100ms delay
        
        # Start and immediately cancel
        delayed.start()
        assert delayed.is_active()
        
        success = delayed.cancel()
        assert success
        assert not delayed.is_active()
        assert delayed.state.name == "CANCELLED"
        
        # Wait to ensure event doesn't execute
        time.sleep(0.15)
        assert len(self.handled_events) == 0
    
    def test_pattern_callbacks(self):
        """Test pattern callbacks."""
        callback_calls = []
        
        def on_start(pattern):
            callback_calls.append("start")
        
        def on_complete(pattern):
            callback_calls.append("complete")
        
        event = SimpleEvent("test.event1")
        delayed = DelayedEvent(event, 0.02, event_bus=self.event_bus)
        delayed.on_start = on_start
        delayed.on_complete = on_complete
        
        delayed.start()
        time.sleep(0.05)
        
        assert "start" in callback_calls
        assert "complete" in callback_calls


class TestEventDispatchers:
    """Test event dispatchers."""
    
    def setup_method(self):
        """Set up test environment."""
        self.handled_events = []
        
        def handler(event):
            self.handled_events.append(event.event_type)
            return EventResult.HANDLED
        
        self.listener = CallableEventListener(
            ["test.event"],
            handler,
            "test_listener"
        )
    
    def test_synchronous_dispatcher(self):
        """Test synchronous dispatcher."""
        dispatcher = SynchronousDispatcher()
        event = SimpleEvent("test.event")
        
        result = dispatcher.dispatch(event, [self.listener])
        assert result == EventResult.HANDLED
        assert "test.event" in self.handled_events
        
        stats = dispatcher.get_stats()
        assert stats['events_dispatched'] == 1
    
    def test_queued_dispatcher(self):
        """Test queued dispatcher."""
        dispatcher = QueuedDispatcher(batch_size=2)
        
        # Dispatch events (should queue)
        event1 = SimpleEvent("test.event")
        event2 = SimpleEvent("test.event")
        
        result1 = dispatcher.dispatch(event1, [self.listener])
        result2 = dispatcher.dispatch(event2, [self.listener])
        
        assert result1 == EventResult.CONTINUE
        assert result2 == EventResult.CONTINUE
        assert dispatcher.get_queue_size() == 2
        assert len(self.handled_events) == 0
        
        # Process queue
        processed = dispatcher.process_queue()
        assert processed == 2
        assert len(self.handled_events) == 2
        assert dispatcher.get_queue_size() == 0
    
    def test_threaded_dispatcher(self):
        """Test threaded dispatcher."""
        dispatcher = ThreadedDispatcher(max_threads=2)
        event = SimpleEvent("test.event")
        
        result = dispatcher.dispatch(event, [self.listener])
        assert result == EventResult.CONTINUE  # Immediate return
        
        # Wait for thread processing
        time.sleep(0.1)
        assert "test.event" in self.handled_events
    
    def test_dispatcher_enable_disable(self):
        """Test dispatcher enable/disable."""
        dispatcher = SynchronousDispatcher()
        event = SimpleEvent("test.event")
        
        # Disable dispatcher
        dispatcher.disable()
        result = dispatcher.dispatch(event, [self.listener])
        assert result == EventResult.CONTINUE
        assert len(self.handled_events) == 0
        
        # Re-enable dispatcher
        dispatcher.enable()
        result = dispatcher.dispatch(event, [self.listener])
        assert result == EventResult.HANDLED
        assert "test.event" in self.handled_events


class TestEventSystemIntegration:
    """Test complete event system integration."""
    
    def test_global_event_bus(self):
        """Test global event bus functionality."""
        # Initialize global bus
        bus = initialize_event_bus(max_queue_size=100)
        assert bus is not None
        
        # Get global bus
        same_bus = get_event_bus()
        assert same_bus is bus
        
        # Test basic functionality
        handled_events = []
        
        def handler(event):
            handled_events.append(event.event_type)
            return EventResult.HANDLED
        
        listener = CallableEventListener(["global.test"], handler, "global_listener")
        bus.register_listener(listener)
        
        event = SimpleEvent("global.test")
        result = bus.dispatch(event)
        assert result == EventResult.HANDLED
        assert "global.test" in handled_events
    
    def test_complex_event_flow(self):
        """Test complex event flow with multiple components."""
        bus = EventBus()
        
        # Create multiple listeners with different priorities
        high_priority_events = []
        normal_priority_events = []
        
        def high_priority_handler(event):
            high_priority_events.append(event.event_type)
            return EventResult.HANDLED
        
        def normal_priority_handler(event):
            normal_priority_events.append(event.event_type)
            return EventResult.HANDLED
        
        high_listener = CallableEventListener(
            ["test.event"], high_priority_handler, "high", EventPriority.HIGH
        )
        normal_listener = CallableEventListener(
            ["test.event"], normal_priority_handler, "normal", EventPriority.NORMAL
        )
        
        bus.register_listener(high_listener)
        bus.register_listener(normal_listener)
        
        # Dispatch event
        event = SimpleEvent("test.event")
        result = bus.dispatch(event)
        
        assert result == EventResult.HANDLED
        assert "test.event" in high_priority_events
        assert "test.event" in normal_priority_events
        
        # Verify processing order (high priority first)
        processing_chain = event.get_processing_chain()
        assert processing_chain[0] == "high"
        assert processing_chain[1] == "normal"
    
    def test_event_system_error_handling(self):
        """Test event system error handling."""
        bus = EventBus()
        
        # Create listener that throws error
        def error_handler(event):
            raise ValueError("Test error")
        
        error_listener = CallableEventListener(
            ["test.event"], error_handler, "error_listener"
        )
        bus.register_listener(error_listener)
        
        # Dispatch event
        event = SimpleEvent("test.event")
        result = bus.dispatch(event)
        
        assert result == EventResult.ERROR
        assert event.has_error()
        assert isinstance(event.error, ValueError)
        
        # Check stats
        stats = bus.get_stats()
        assert stats['errors_occurred'] == 1
    
    def test_performance_characteristics(self):
        """Test event system performance characteristics."""
        bus = EventBus()
        
        # Create simple listener
        handled_count = 0
        
        def counter_handler(event):
            nonlocal handled_count
            handled_count += 1
            return EventResult.HANDLED
        
        listener = CallableEventListener(
            ["perf.test"], counter_handler, "counter"
        )
        bus.register_listener(listener)
        
        # Dispatch many events
        start_time = time.time()
        num_events = 1000
        
        for i in range(num_events):
            event = SimpleEvent("perf.test", {"index": i})
            bus.dispatch(event)
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert handled_count == num_events
        assert duration < 1.0  # Should process 1000 events in under 1 second
        
        # Check stats
        stats = bus.get_stats()
        assert stats['events_dispatched'] == num_events
        assert stats['avg_processing_time'] > 0
        
        print(f"Processed {num_events} events in {duration:.3f}s "
              f"({num_events/duration:.0f} events/sec)")


if __name__ == "__main__":
    pytest.main([__file__])
