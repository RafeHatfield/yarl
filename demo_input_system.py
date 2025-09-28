#!/usr/bin/env python3
"""Demo script for the Input System.

This script demonstrates the capabilities of the input abstraction system
including event handling, input mapping, state management, and backend
abstraction.
"""

import time
from pathlib import Path

from input import (
    InputManager, initialize_input_manager,
    InputAction, InputEventType, InputModifiers, MouseButton,
    KeyBinding, MouseBinding, ActionMapping, InputProfile,
    InputSequence, InputSequenceStep, InputCombo,
    create_key_event, create_mouse_event
)


def demo_basic_input_manager():
    """Demonstrate basic input manager functionality."""
    print("🎮 === Basic Input Manager Demo ===")
    
    # Initialize input manager
    manager = initialize_input_manager(
        preferred_backend="null",  # Use null backend for demo
        auto_detect_backend=False
    )
    
    print(f"✅ Input Manager initialized")
    print(f"   Backend: {manager.backend.name}")
    print(f"   Capabilities: {[cap.name for cap in manager.backend.capabilities if manager.has_capability(cap)]}")
    
    # Get status
    status = manager.get_status()
    print(f"   Status: Enabled={status['enabled']}, Backend Initialized={status['backend_initialized']}")
    print(f"   Active Profile: {status['active_profile']}")
    print(f"   Available Backends: {status['available_backends']}")
    
    return manager


def demo_input_events():
    """Demonstrate input event creation and handling."""
    print("\n⌨️  === Input Events Demo ===")
    
    # Create different types of events
    key_event = create_key_event(
        InputEventType.KEY_DOWN,
        "a",
        InputModifiers.CTRL | InputModifiers.SHIFT,
        key_code=65,
        unicode="A"
    )
    
    mouse_event = create_mouse_event(
        InputEventType.MOUSE_DOWN,
        x=100, y=200,
        button=MouseButton.LEFT,
        delta_x=5, delta_y=-3
    )
    
    print(f"✅ Key Event: {key_event}")
    print(f"   Type: {key_event.event_type.name}")
    print(f"   Key: {key_event.key}")
    print(f"   Modifiers: {key_event.modifiers}")
    print(f"   String representation: {str(key_event)}")
    
    print(f"✅ Mouse Event: {mouse_event}")
    print(f"   Type: {mouse_event.event_type.name}")
    print(f"   Position: ({mouse_event.x}, {mouse_event.y})")
    print(f"   Button: {mouse_event.button.name if mouse_event.button else 'None'}")
    print(f"   Delta: ({mouse_event.delta_x}, {mouse_event.delta_y})")
    
    # Test event consumption
    print(f"   Event consumed: {key_event.is_consumed()}")
    key_event.consume()
    print(f"   Event consumed after consume(): {key_event.is_consumed()}")
    
    # Test serialization
    key_data = key_event.to_dict()
    print(f"✅ Event serialization works: {len(key_data)} fields")


def demo_input_mapping():
    """Demonstrate input mapping and profiles."""
    print("\n🗺️  === Input Mapping Demo ===")
    
    # Create custom input profile
    custom_profile = InputProfile("fps_controls", "FPS-style controls")
    
    # Add movement mappings
    custom_profile.add_mapping(ActionMapping(
        action=InputAction.MOVE_UP,
        bindings=[KeyBinding(key="w"), KeyBinding(key="up")],
        description="Move forward"
    ))
    
    custom_profile.add_mapping(ActionMapping(
        action=InputAction.MOVE_DOWN,
        bindings=[KeyBinding(key="s"), KeyBinding(key="down")],
        description="Move backward"
    ))
    
    custom_profile.add_mapping(ActionMapping(
        action=InputAction.MOVE_LEFT,
        bindings=[KeyBinding(key="a"), KeyBinding(key="left")],
        description="Move left"
    ))
    
    custom_profile.add_mapping(ActionMapping(
        action=InputAction.MOVE_RIGHT,
        bindings=[KeyBinding(key="d"), KeyBinding(key="right")],
        description="Move right"
    ))
    
    # Add action mappings
    custom_profile.add_mapping(ActionMapping(
        action=InputAction.ATTACK,
        bindings=[
            MouseBinding(button=MouseButton.LEFT),
            KeyBinding(key="space")
        ],
        description="Primary attack"
    ))
    
    custom_profile.add_mapping(ActionMapping(
        action=InputAction.USE_ITEM,
        bindings=[
            MouseBinding(button=MouseButton.RIGHT),
            KeyBinding(key="e")
        ],
        description="Use item/interact"
    ))
    
    # Add combo mapping (Ctrl+C for quit)
    custom_profile.add_mapping(ActionMapping(
        action=InputAction.QUIT,
        bindings=[KeyBinding(key="c", modifiers=InputModifiers.CTRL)],
        description="Quit game"
    ))
    
    print(f"✅ Created custom profile: {custom_profile.name}")
    print(f"   Description: {custom_profile.description}")
    print(f"   Mappings: {len(custom_profile.mappings)}")
    
    # Test event matching
    test_events = [
        ("W key", create_key_event(InputEventType.KEY_DOWN, "w")),
        ("Left mouse", create_mouse_event(InputEventType.MOUSE_DOWN, button=MouseButton.LEFT)),
        ("Ctrl+C", create_key_event(InputEventType.KEY_DOWN, "c", InputModifiers.CTRL)),
        ("Unknown key", create_key_event(InputEventType.KEY_DOWN, "z")),
    ]
    
    print("\n🎯 Testing event matching:")
    for event_name, event in test_events:
        actions = custom_profile.get_actions_for_event(event)
        if actions:
            print(f"   {event_name} -> {actions}")
        else:
            print(f"   {event_name} -> No actions")
    
    return custom_profile


def demo_input_sequences_and_combos():
    """Demonstrate input sequences and combos."""
    print("\n🔄 === Input Sequences and Combos Demo ===")
    
    # Create Konami Code sequence
    konami_steps = [
        InputSequenceStep(key="up"),
        InputSequenceStep(key="up"),
        InputSequenceStep(key="down"),
        InputSequenceStep(key="down"),
        InputSequenceStep(key="left"),
        InputSequenceStep(key="right"),
        InputSequenceStep(key="left"),
        InputSequenceStep(key="right"),
        InputSequenceStep(key="b"),
        InputSequenceStep(key="a"),
    ]
    
    konami_sequence = InputSequence("konami_code", konami_steps, timeout=5.0)
    
    print(f"✅ Created Konami Code sequence")
    print(f"   Steps: {len(konami_sequence.steps)}")
    print(f"   Timeout: {konami_sequence.timeout}s")
    
    # Test sequence processing
    print("\n🎮 Testing sequence (first 3 steps):")
    test_sequence_events = [
        create_key_event(InputEventType.KEY_DOWN, "up"),
        create_key_event(InputEventType.KEY_DOWN, "up"),
        create_key_event(InputEventType.KEY_DOWN, "down"),
    ]
    
    for i, event in enumerate(test_sequence_events):
        completed = konami_sequence.process_event(event)
        print(f"   Step {i+1}: {event.key} -> Progress: {konami_sequence.get_progress():.1%}")
        if completed:
            print(f"   🎉 Sequence completed!")
            break
    
    # Create input combo (Ctrl+Shift+D for debug)
    debug_combo = InputCombo(
        "debug_mode",
        keys=["d"],
        modifiers=InputModifiers.CTRL | InputModifiers.SHIFT
    )
    
    print(f"\n✅ Created debug combo: {debug_combo.name}")
    print(f"   Keys: {debug_combo.keys}")
    print(f"   Modifiers: {debug_combo.modifiers}")
    
    return konami_sequence, debug_combo


def demo_state_management(manager):
    """Demonstrate input state management."""
    print("\n📊 === Input State Management Demo ===")
    
    state_manager = manager.state_manager
    
    # Simulate some input events
    print("🎯 Simulating input events:")
    
    # Key press sequence
    events = [
        create_key_event(InputEventType.KEY_DOWN, "w"),
        create_mouse_event(InputEventType.MOUSE_MOVE, x=150, y=250, delta_x=10, delta_y=15),
        create_mouse_event(InputEventType.MOUSE_DOWN, button=MouseButton.LEFT),
        create_key_event(InputEventType.KEY_UP, "w"),
        create_mouse_event(InputEventType.MOUSE_UP, button=MouseButton.LEFT),
    ]
    
    for event in events:
        state_manager.process_event(event)
        
        if hasattr(event, 'key'):
            print(f"   Key {event.key} {event.event_type.name}")
            print(f"     W pressed: {state_manager.is_key_pressed('w')}")
            print(f"     W just pressed: {state_manager.is_key_just_pressed('w')}")
            print(f"     W just released: {state_manager.is_key_just_released('w')}")
        elif hasattr(event, 'button') and event.button:
            print(f"   Mouse {event.button.name} {event.event_type.name}")
            print(f"     Left button pressed: {state_manager.mouse_state.is_button_pressed(MouseButton.LEFT)}")
        elif hasattr(event, 'x'):
            print(f"   Mouse moved to ({event.x}, {event.y})")
            print(f"     Position: {state_manager.get_mouse_position()}")
            print(f"     Delta: {state_manager.get_mouse_delta()}")
        
        # Update frame to transition states
        state_manager.update_frame()
    
    print("✅ State management demonstration complete")


def demo_profile_serialization(profile):
    """Demonstrate profile serialization."""
    print("\n💾 === Profile Serialization Demo ===")
    
    # Save profile to temporary file
    import tempfile
    import json
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        profile_data = profile.to_dict()
        json.dump(profile_data, f, indent=2)
        temp_path = f.name
    
    print(f"✅ Saved profile to: {temp_path}")
    print(f"   Profile data keys: {list(profile_data.keys())}")
    print(f"   Mappings count: {len(profile_data['mappings'])}")
    
    # Load profile back
    try:
        loaded_profile = InputProfile.load_from_file(temp_path)
        print(f"✅ Loaded profile: {loaded_profile.name}")
        print(f"   Description: {loaded_profile.description}")
        print(f"   Mappings: {len(loaded_profile.mappings)}")
        
        # Test that loaded profile works the same
        test_event = create_key_event(InputEventType.KEY_DOWN, "w")
        original_actions = profile.get_actions_for_event(test_event)
        loaded_actions = loaded_profile.get_actions_for_event(test_event)
        
        print(f"   Original actions for 'w': {original_actions}")
        print(f"   Loaded actions for 'w': {loaded_actions}")
        print(f"   Serialization preserved functionality: {original_actions == loaded_actions}")
        
    except Exception as e:
        print(f"❌ Error loading profile: {e}")
    finally:
        # Clean up
        Path(temp_path).unlink(missing_ok=True)


def demo_advanced_features(manager):
    """Demonstrate advanced input features."""
    print("\n🚀 === Advanced Features Demo ===")
    
    # Event callbacks
    event_count = {"count": 0}
    
    def event_callback(event):
        event_count["count"] += 1
        print(f"   📨 Event callback #{event_count['count']}: {type(event).__name__}")
    
    manager.add_event_callback(event_callback)
    print("✅ Added event callback")
    
    # Action callbacks
    action_triggered = {"actions": []}
    
    def action_callback(action):
        action_triggered["actions"].append(action)
        print(f"   🎯 Action triggered: {action}")
    
    manager.add_action_callback(InputAction.MOVE_UP, action_callback)
    manager.add_action_callback(InputAction.ATTACK, action_callback)
    print("✅ Added action callbacks")
    
    # Simulate some events to trigger callbacks
    print("\n🎮 Simulating events to trigger callbacks:")
    
    # Mock the backend to return our test events
    test_events = [
        create_key_event(InputEventType.KEY_DOWN, "w"),
        create_key_event(InputEventType.KEY_DOWN, "space"),
        create_mouse_event(InputEventType.MOUSE_DOWN, button=MouseButton.LEFT),
    ]
    
    manager.backend.poll_events = lambda: test_events
    
    # Process events
    triggered_actions = manager.process_events()
    
    print(f"✅ Processed {len(test_events)} events")
    print(f"   Event callbacks triggered: {event_count['count']}")
    print(f"   Actions triggered: {triggered_actions}")
    print(f"   Action callbacks triggered: {len(action_triggered['actions'])}")
    
    # Clean up callbacks
    manager.remove_event_callback(event_callback)
    manager.remove_action_callback(InputAction.MOVE_UP, action_callback)
    manager.remove_action_callback(InputAction.ATTACK, action_callback)
    print("✅ Cleaned up callbacks")


def demo_backend_info(manager):
    """Demonstrate backend information and capabilities."""
    print("\n🔧 === Backend Information Demo ===")
    
    backend_info = manager.get_backend_info()
    print(f"✅ Backend Information:")
    for key, value in backend_info.items():
        if isinstance(value, list) and len(value) > 3:
            print(f"   {key}: [{len(value)} items]")
        else:
            print(f"   {key}: {value}")
    
    # Test capability checking
    capabilities_to_test = [
        "KEYBOARD", "MOUSE", "GAMEPAD", "TOUCH",
        "KEY_REPEAT", "MOUSE_CAPTURE", "WINDOW_EVENTS"
    ]
    
    print(f"\n🎯 Capability Testing:")
    for cap_name in capabilities_to_test:
        try:
            from input.backend import InputCapabilities
            capability = getattr(InputCapabilities, cap_name)
            has_cap = manager.has_capability(capability)
            print(f"   {cap_name}: {'✅' if has_cap else '❌'}")
        except AttributeError:
            print(f"   {cap_name}: ❓ (unknown capability)")


def main():
    """Main demo function."""
    print("🎮 Input System Demo")
    print("=" * 50)
    
    # Run all demos
    manager = demo_basic_input_manager()
    demo_input_events()
    custom_profile = demo_input_mapping()
    konami_sequence, debug_combo = demo_input_sequences_and_combos()
    demo_state_management(manager)
    demo_profile_serialization(custom_profile)
    demo_advanced_features(manager)
    demo_backend_info(manager)
    
    print("\n🎉 Demo completed successfully!")
    print("\nThe Input System provides:")
    print("  ✅ Unified input abstraction across multiple backends")
    print("  ✅ Flexible input mapping with profiles and custom bindings")
    print("  ✅ Advanced input patterns (sequences, combos, modifiers)")
    print("  ✅ Real-time input state tracking and management")
    print("  ✅ Event-driven architecture with callbacks")
    print("  ✅ Serializable profiles for user customization")
    print("  ✅ Extensible backend system for different platforms")
    print("  ✅ Comprehensive error handling and validation")
    
    # Cleanup
    manager.shutdown()
    print("\n🧹 Input manager shut down cleanly")


if __name__ == "__main__":
    main()
