#!/usr/bin/env python3
"""Demonstration of the event-driven architecture system.

This script showcases the capabilities of the event system including
basic events, game events, patterns, and complex event flows.
"""

import time
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from events import (
    # Core components
    EventBus, initialize_event_bus, get_event_bus, SimpleEvent, create_event,
    EventPriority, EventResult, EventContext,
    
    # Listeners
    EventListener, SimpleEventListener, event_handler, CallableEventListener,
    
    # Game events
    GameEventType, CombatEvent, MovementEvent, InventoryEvent,
    create_combat_event, create_movement_event, create_inventory_event,
    
    # Patterns
    EventChain, DelayedEvent, RecurringEvent, ConditionalEvent,
    create_event_chain, create_delayed_event, create_recurring_event,
    
    # Dispatchers
    SynchronousDispatcher, QueuedDispatcher, ThreadedDispatcher
)


class GameEventLogger(EventListener):
    """Example event listener that logs game events."""
    
    def __init__(self):
        super().__init__("game_logger")
        self.logged_events = []
    
    def get_handled_events(self):
        return [
            "combat.attack", "combat.damage", "combat.death",
            "movement.move", "inventory.pickup", "player.level_up"
        ]
    
    @event_handler("combat.attack", "combat.damage")
    def handle_combat_events(self, event):
        if isinstance(event, CombatEvent):
            if event.game_event_type == GameEventType.COMBAT_ATTACK:
                print(f"🗡️  {event.attacker_id} attacks {event.target_id}")
            elif event.game_event_type == GameEventType.COMBAT_DAMAGE:
                crit = " (CRITICAL!)" if event.critical_hit else ""
                print(f"💥 {event.target_id} takes {event.damage} damage{crit}")
        
        self.logged_events.append(event.event_type)
        return EventResult.HANDLED
    
    @event_handler("movement.move")
    def handle_movement(self, event):
        if isinstance(event, MovementEvent):
            print(f"🚶 {event.entity_id} moves from ({event.from_x},{event.from_y}) "
                  f"to ({event.to_x},{event.to_y})")
        
        self.logged_events.append(event.event_type)
        return EventResult.HANDLED
    
    @event_handler("inventory.pickup")
    def handle_inventory(self, event):
        if isinstance(event, InventoryEvent):
            print(f"📦 {event.entity_id} picks up {event.quantity}x {event.item_name}")
        
        self.logged_events.append(event.event_type)
        return EventResult.HANDLED
    
    @event_handler("player.level_up")
    def handle_level_up(self, event):
        print(f"⭐ Player leveled up! New level: {event.data.get('level', '?')}")
        self.logged_events.append(event.event_type)
        return EventResult.HANDLED


class CombatSystem(EventListener):
    """Example combat system that responds to combat events."""
    
    def __init__(self):
        super().__init__("combat_system")
        self.entities = {
            "player": {"hp": 100, "max_hp": 100, "level": 1, "xp": 0},
            "orc": {"hp": 30, "max_hp": 30, "level": 1, "xp": 0},
            "troll": {"hp": 80, "max_hp": 80, "level": 3, "xp": 0}
        }
    
    def get_handled_events(self):
        return ["combat.attack"]
    
    @event_handler("combat.attack")
    def handle_attack(self, event):
        if not isinstance(event, CombatEvent):
            return EventResult.CONTINUE
        
        attacker_id = event.attacker_id
        target_id = event.target_id
        base_damage = event.damage
        
        if target_id not in self.entities:
            print(f"❌ Target {target_id} not found!")
            return EventResult.ERROR
        
        # Calculate actual damage (with some randomness)
        import random
        actual_damage = max(1, base_damage + random.randint(-2, 2))
        critical_hit = random.random() < 0.1  # 10% crit chance
        
        if critical_hit:
            actual_damage *= 2
        
        # Apply damage
        target = self.entities[target_id]
        target["hp"] = max(0, target["hp"] - actual_damage)
        
        # Create damage event
        damage_event = CombatEvent(
            GameEventType.COMBAT_DAMAGE,
            attacker_id=attacker_id,
            target_id=target_id,
            damage=actual_damage,
            critical_hit=critical_hit
        )
        
        # Dispatch damage event
        bus = get_event_bus()
        bus.dispatch(damage_event)
        
        # Check for death
        if target["hp"] <= 0:
            death_event = CombatEvent(
                GameEventType.COMBAT_DEATH,
                target_id=target_id
            )
            bus.dispatch(death_event)
            
            # Award XP to player
            if attacker_id == "player" and target_id != "player":
                xp_gained = target["level"] * 10
                self.entities["player"]["xp"] += xp_gained
                print(f"✨ Player gains {xp_gained} XP!")
                
                # Check for level up
                player = self.entities["player"]
                xp_needed = player["level"] * 100
                if player["xp"] >= xp_needed:
                    player["level"] += 1
                    player["xp"] -= xp_needed
                    player["max_hp"] += 10
                    player["hp"] = player["max_hp"]  # Full heal on level up
                    
                    level_up_event = SimpleEvent("player.level_up", {
                        "level": player["level"],
                        "new_max_hp": player["max_hp"]
                    })
                    bus.dispatch(level_up_event)
        
        return EventResult.HANDLED


def demonstrate_basic_events():
    """Demonstrate basic event functionality."""
    print("=" * 60)
    print("🎯 BASIC EVENT SYSTEM DEMONSTRATION")
    print("=" * 60)
    
    # Initialize event bus
    bus = initialize_event_bus(max_queue_size=1000)
    
    # Create and register listeners
    logger = GameEventLogger()
    combat_system = CombatSystem()
    
    bus.register_listener(logger)
    bus.register_listener(combat_system)
    
    print("✅ Event bus initialized with listeners")
    print(f"📊 Registered listeners: {len(bus.listener_registry.listeners)}")
    print()
    
    # Demonstrate simple events
    print("📢 Dispatching simple events...")
    
    simple_event = create_event(
        "system.startup",
        {"version": "1.0", "timestamp": time.time()},
        source="demo",
        priority=EventPriority.HIGH
    )
    
    result = bus.dispatch(simple_event)
    print(f"   System startup event: {result.name}")
    print()
    
    # Demonstrate game events
    print("🎮 Dispatching game events...")
    
    # Movement event
    move_event = create_movement_event(
        GameEventType.MOVEMENT_MOVE,
        entity_id="player",
        from_pos=(5, 5),
        to_pos=(6, 5)
    )
    bus.dispatch(move_event)
    
    # Inventory event
    pickup_event = create_inventory_event(
        GameEventType.INVENTORY_PICKUP,
        entity_id="player",
        item_name="Health Potion",
        quantity=2
    )
    bus.dispatch(pickup_event)
    
    # Combat sequence
    attack_event = create_combat_event(
        GameEventType.COMBAT_ATTACK,
        attacker_id="player",
        target_id="orc",
        damage=15,
        weapon="sword"
    )
    bus.dispatch(attack_event)
    
    print()
    
    # Show statistics
    stats = bus.get_stats()
    print("📈 Event Bus Statistics:")
    print(f"   Events dispatched: {stats['events_dispatched']}")
    print(f"   Listeners notified: {stats['listeners_notified']}")
    print(f"   Average processing time: {stats['avg_processing_time']:.4f}s")
    print(f"   Events by type: {dict(stats['events_by_type'])}")
    print()


def demonstrate_event_patterns():
    """Demonstrate event patterns."""
    print("=" * 60)
    print("🔗 EVENT PATTERNS DEMONSTRATION")
    print("=" * 60)
    
    bus = get_event_bus()
    
    # Event Chain - Spell casting sequence
    print("⛓️  Event Chain: Spell Casting Sequence")
    
    spell_events = [
        SimpleEvent("spell.prepare", {"spell": "fireball", "mana_cost": 20}),
        SimpleEvent("spell.cast", {"spell": "fireball", "target": "troll"}),
        SimpleEvent("spell.effect", {"spell": "fireball", "damage": 25}),
        SimpleEvent("spell.complete", {"spell": "fireball"})
    ]
    
    spell_chain = create_event_chain(spell_events, pattern_id="fireball_cast")
    
    def on_spell_complete(pattern):
        print(f"   ✨ Spell casting completed! Duration: {pattern.get_duration():.3f}s")
    
    spell_chain.on_complete = on_spell_complete
    spell_chain.start()
    
    # Wait for completion
    time.sleep(0.1)
    print(f"   Progress: {spell_chain.get_progress():.0%}")
    print()
    
    # Delayed Event - Potion effect
    print("⏰ Delayed Event: Potion Effect")
    
    potion_event = SimpleEvent("effect.heal", {"amount": 30, "target": "player"})
    delayed_heal = create_delayed_event(potion_event, 0.5, pattern_id="heal_potion")
    
    def on_heal_start(pattern):
        print("   🧪 Drinking potion... effect will activate in 0.5s")
    
    def on_heal_complete(pattern):
        print("   💚 Healing effect activated!")
    
    delayed_heal.on_start = on_heal_start
    delayed_heal.on_complete = on_heal_complete
    delayed_heal.start()
    
    # Recurring Event - Regeneration
    print("🔄 Recurring Event: Health Regeneration")
    
    regen_event = SimpleEvent("effect.regenerate", {"amount": 5, "target": "player"})
    regen_pattern = create_recurring_event(
        regen_event, 0.2, max_occurrences=3, pattern_id="health_regen"
    )
    
    def on_regen_complete(pattern):
        print(f"   💖 Regeneration complete! Total ticks: {pattern.get_occurrence_count()}")
    
    regen_pattern.on_complete = on_regen_complete
    regen_pattern.start()
    
    # Conditional Event - Level up when XP threshold reached
    print("❓ Conditional Event: Level Up Check")
    
    player_xp = 0
    
    def xp_threshold_met():
        return player_xp >= 50
    
    levelup_event = SimpleEvent("player.conditional_levelup", {"new_level": 2})
    conditional_levelup = ConditionalEvent(
        levelup_event,
        xp_threshold_met,
        check_interval=0.1,
        timeout=2.0,
        pattern_id="conditional_levelup"
    )
    
    def on_levelup_start(pattern):
        print("   👀 Watching for XP threshold (50 XP needed)...")
    
    def on_levelup_complete(pattern):
        print("   🎉 Conditional level up triggered!")
    
    conditional_levelup.on_start = on_levelup_start
    conditional_levelup.on_complete = on_levelup_complete
    conditional_levelup.start()
    
    # Simulate gaining XP
    time.sleep(0.3)
    player_xp = 60
    print(f"   📈 Player gains XP! Total: {player_xp}")
    
    # Wait for all patterns to complete
    time.sleep(1.0)
    print()


def demonstrate_dispatchers():
    """Demonstrate different event dispatchers."""
    print("=" * 60)
    print("🚀 EVENT DISPATCHERS DEMONSTRATION")
    print("=" * 60)
    
    # Create test listener
    processed_events = []
    
    def test_handler(event):
        processed_events.append(event.event_type)
        time.sleep(0.01)  # Simulate processing time
        return EventResult.HANDLED
    
    test_listener = CallableEventListener(
        ["dispatch.test"], test_handler, "test_dispatcher_listener"
    )
    
    # Synchronous Dispatcher
    print("⚡ Synchronous Dispatcher")
    sync_dispatcher = SynchronousDispatcher()
    
    start_time = time.time()
    for i in range(10):
        event = SimpleEvent("dispatch.test", {"index": i})
        sync_dispatcher.dispatch(event, [test_listener])
    
    sync_time = time.time() - start_time
    sync_count = len(processed_events)
    processed_events.clear()
    
    print(f"   Processed {sync_count} events in {sync_time:.3f}s (synchronous)")
    
    # Queued Dispatcher
    print("📋 Queued Dispatcher")
    queued_dispatcher = QueuedDispatcher(batch_size=5)
    
    # Queue events
    for i in range(10):
        event = SimpleEvent("dispatch.test", {"index": i})
        queued_dispatcher.dispatch(event, [test_listener])
    
    print(f"   Queued {queued_dispatcher.get_queue_size()} events")
    
    # Process queue
    start_time = time.time()
    processed = queued_dispatcher.process_queue()
    queue_time = time.time() - start_time
    
    print(f"   Processed {processed} events in {queue_time:.3f}s (queued)")
    processed_events.clear()
    
    # Threaded Dispatcher
    print("🧵 Threaded Dispatcher")
    threaded_dispatcher = ThreadedDispatcher(max_threads=3)
    
    start_time = time.time()
    for i in range(10):
        event = SimpleEvent("dispatch.test", {"index": i})
        threaded_dispatcher.dispatch(event, [test_listener])
    
    # Wait for threads to complete
    time.sleep(0.2)
    threaded_time = time.time() - start_time
    threaded_count = len(processed_events)
    
    print(f"   Processed {threaded_count} events in {threaded_time:.3f}s (threaded)")
    print()


def demonstrate_performance():
    """Demonstrate event system performance."""
    print("=" * 60)
    print("⚡ PERFORMANCE DEMONSTRATION")
    print("=" * 60)
    
    bus = get_event_bus()
    
    # Create multiple listeners
    counters = {"listener1": 0, "listener2": 0, "listener3": 0}
    
    def create_counter_handler(name):
        def handler(event):
            counters[name] += 1
            return EventResult.HANDLED
        return handler
    
    for name in counters.keys():
        listener = CallableEventListener(
            ["perf.test"], create_counter_handler(name), name
        )
        bus.register_listener(listener)
    
    # Performance test
    num_events = 5000
    print(f"🏃 Dispatching {num_events} events to {len(counters)} listeners...")
    
    start_time = time.time()
    
    for i in range(num_events):
        event = SimpleEvent("perf.test", {"index": i, "batch": i // 100})
        bus.dispatch(event)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"✅ Completed in {duration:.3f}s")
    print(f"📊 Performance: {num_events/duration:.0f} events/second")
    print(f"🎯 Events per listener: {counters}")
    
    # Show final statistics
    stats = bus.get_stats()
    print(f"📈 Total events dispatched: {stats['events_dispatched']}")
    print(f"📈 Total listeners notified: {stats['listeners_notified']}")
    print(f"📈 Average processing time: {stats['avg_processing_time']:.6f}s")
    print()


def main():
    """Run the complete event system demonstration."""
    print("🎮 EVENT-DRIVEN ARCHITECTURE DEMONSTRATION")
    print("=" * 60)
    print("This demo showcases the comprehensive event system including:")
    print("• Basic event creation and dispatching")
    print("• Game-specific events (combat, movement, inventory)")
    print("• Event patterns (chains, delays, recurring, conditional)")
    print("• Different dispatching strategies")
    print("• Performance characteristics")
    print()
    
    try:
        # Run demonstrations
        demonstrate_basic_events()
        demonstrate_event_patterns()
        demonstrate_dispatchers()
        demonstrate_performance()
        
        print("=" * 60)
        print("🎉 EVENT SYSTEM DEMONSTRATION COMPLETE!")
        print("=" * 60)
        print("The event system provides:")
        print("✅ Loose coupling between game components")
        print("✅ Flexible event patterns for complex behaviors")
        print("✅ High performance event processing")
        print("✅ Comprehensive error handling and statistics")
        print("✅ Thread-safe concurrent event processing")
        print()
        print("Ready for integration into the game engine! 🚀")
        
    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
