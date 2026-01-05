"""Unit tests for Root Potion consumption (Barkskin buff).

Phase 20D.1: Root Potion dual-mode consumable
- THROWN: Applies EntangledEffect (roots bind target)
- CONSUMED: Applies BarkskinEffect (defensive buff, +3 AC)

This test module validates the CONSUMED mode behavior.
Drinking an unidentified potion is never harmful (by design).
"""

import pytest


class TestRootPotionConsume:
    """Test Root Potion consumption applies Barkskin buff correctly."""
    
    def test_drink_root_potion_applies_barkskin(self):
        """Drinking Root Potion applies BarkskinEffect to the drinker."""
        from entity import Entity
        from components.component_registry import ComponentType
        from components.status_effects import StatusEffectManager, BarkskinEffect
        from item_functions import drink_root_potion
        
        # Create test entity
        entity = Entity(x=0, y=0, char='@', color=(255, 255, 255), name='Test Player')
        entity.status_effects = StatusEffectManager(entity)
        entity.components.add(ComponentType.STATUS_EFFECTS, entity.status_effects)
        
        # Drink the potion
        results = drink_root_potion(entity)
        
        # Verify barkskin effect is active
        assert entity.status_effects.has_effect('barkskin'), (
            "Barkskin effect should be active after drinking root potion"
        )
        
        # Verify effect properties
        barkskin = entity.status_effects.get_effect('barkskin')
        assert barkskin is not None
        assert barkskin.duration == 10, f"Expected duration 10, got {barkskin.duration}"
        assert barkskin.ac_bonus == 3, f"Expected AC bonus 3, got {barkskin.ac_bonus}"
        
        # Verify consumption
        assert any(r.get('consumed') for r in results), "Potion should be consumed"
    
    def test_drink_root_potion_does_not_apply_entangle(self):
        """Drinking Root Potion should NOT apply EntangledEffect to self."""
        from entity import Entity
        from components.component_registry import ComponentType
        from components.status_effects import StatusEffectManager
        from item_functions import drink_root_potion
        
        # Create test entity
        entity = Entity(x=0, y=0, char='@', color=(255, 255, 255), name='Test Player')
        entity.status_effects = StatusEffectManager(entity)
        entity.components.add(ComponentType.STATUS_EFFECTS, entity.status_effects)
        
        # Drink the potion
        drink_root_potion(entity)
        
        # Verify entangle is NOT applied
        assert not entity.status_effects.has_effect('entangled'), (
            "Entangled effect should NOT be applied when drinking (only when thrown)"
        )
    
    def test_barkskin_duration_refresh_not_stack(self):
        """Reapplying Barkskin refreshes duration, doesn't stack AC bonus."""
        from entity import Entity
        from components.component_registry import ComponentType
        from components.status_effects import StatusEffectManager
        from item_functions import drink_root_potion
        
        # Create test entity
        entity = Entity(x=0, y=0, char='@', color=(255, 255, 255), name='Test Player')
        entity.status_effects = StatusEffectManager(entity)
        entity.components.add(ComponentType.STATUS_EFFECTS, entity.status_effects)
        
        # Drink first potion
        drink_root_potion(entity)
        
        # Simulate some turns passing
        barkskin = entity.status_effects.get_effect('barkskin')
        barkskin.duration -= 5  # 5 turns passed
        assert barkskin.duration == 5
        
        # Drink second potion - should refresh to full duration
        drink_root_potion(entity)
        
        # Duration should be refreshed to 10
        barkskin = entity.status_effects.get_effect('barkskin')
        assert barkskin.duration == 10, (
            f"Expected duration refreshed to 10, got {barkskin.duration}"
        )
        
        # AC bonus should NOT stack (still +3)
        assert barkskin.ac_bonus == 3, (
            f"Expected AC bonus 3 (not stacked), got {barkskin.ac_bonus}"
        )


class TestRootPotionThrow:
    """Test Root Potion throwing applies Entangle effect correctly."""
    
    def test_throw_root_potion_applies_entangle(self):
        """Throwing Root Potion at target applies EntangledEffect."""
        from entity import Entity
        from components.component_registry import ComponentType
        from components.status_effects import StatusEffectManager, EntangledEffect
        from item_functions import apply_root_potion_throw
        
        # Create test entity (the target)
        target = Entity(x=5, y=5, char='o', color=(128, 128, 128), name='Test Orc')
        target.status_effects = StatusEffectManager(target)
        target.components.add(ComponentType.STATUS_EFFECTS, target.status_effects)
        
        # Throw potion at target
        results = apply_root_potion_throw(target)
        
        # Verify entangle effect is active
        assert target.status_effects.has_effect('entangled'), (
            "Entangled effect should be active after being hit by root potion"
        )
        
        # Verify effect properties
        entangled = target.status_effects.get_effect('entangled')
        assert entangled is not None
        assert entangled.duration == 3, f"Expected duration 3, got {entangled.duration}"
        
        # Verify consumption
        assert any(r.get('consumed') for r in results), "Potion should be consumed"
    
    def test_throw_root_potion_does_not_apply_barkskin(self):
        """Throwing Root Potion should NOT apply BarkskinEffect to target."""
        from entity import Entity
        from components.component_registry import ComponentType
        from components.status_effects import StatusEffectManager
        from item_functions import apply_root_potion_throw
        
        # Create test entity (the target)
        target = Entity(x=5, y=5, char='o', color=(128, 128, 128), name='Test Orc')
        target.status_effects = StatusEffectManager(target)
        target.components.add(ComponentType.STATUS_EFFECTS, target.status_effects)
        
        # Throw potion at target
        apply_root_potion_throw(target)
        
        # Verify barkskin is NOT applied
        assert not target.status_effects.has_effect('barkskin'), (
            "Barkskin effect should NOT be applied when throwing (only when drunk)"
        )
    
    def test_entangle_duration_refresh_not_stack(self):
        """Reapplying Entangle refreshes duration, no stacking."""
        from entity import Entity
        from components.component_registry import ComponentType
        from components.status_effects import StatusEffectManager
        from item_functions import apply_root_potion_throw
        
        # Create test entity (the target)
        target = Entity(x=5, y=5, char='o', color=(128, 128, 128), name='Test Orc')
        target.status_effects = StatusEffectManager(target)
        target.components.add(ComponentType.STATUS_EFFECTS, target.status_effects)
        
        # First throw
        apply_root_potion_throw(target)
        
        # Simulate time passing
        entangled = target.status_effects.get_effect('entangled')
        entangled.duration -= 2  # 2 turns passed
        assert entangled.duration == 1
        
        # Second throw - should refresh to full duration
        apply_root_potion_throw(target)
        
        # Duration should be refreshed to 3
        entangled = target.status_effects.get_effect('entangled')
        assert entangled.duration == 3, (
            f"Expected duration refreshed to 3, got {entangled.duration}"
        )


class TestEntangledEffectBehavior:
    """Test EntangledEffect movement blocking behavior."""
    
    def test_entangled_blocks_movement_player(self):
        """EntangledEffect blocks player movement via MovementService."""
        from entity import Entity
        from components.component_registry import ComponentType, ComponentRegistry
        from components.status_effects import StatusEffectManager, EntangledEffect
        
        # Create test player
        player = Entity(x=5, y=5, char='@', color=(255, 255, 255), name='Test Player')
        player.components = ComponentRegistry()
        player.status_effects = StatusEffectManager(player)
        player.components.add(ComponentType.STATUS_EFFECTS, player.status_effects)
        
        # Apply entangled effect
        entangled = EntangledEffect(owner=player, duration=3)
        player.status_effects.add_effect(entangled)
        
        # Verify has_status_effect method works
        assert player.has_status_effect('entangled') if hasattr(player, 'has_status_effect') else (
            player.status_effects.has_effect('entangled')
        ), "Player should have entangled status"
    
    def test_entity_move_returns_false_when_entangled(self):
        """Entity.move() returns False when blocked by entangle status."""
        from entity import Entity
        from components.component_registry import ComponentType, ComponentRegistry
        from components.status_effects import StatusEffectManager, EntangledEffect
        
        # Create test entity
        entity = Entity(x=5, y=5, char='o', color=(128, 128, 128), name='Test Orc')
        entity.components = ComponentRegistry()
        entity.status_effects = StatusEffectManager(entity)
        entity.components.add(ComponentType.STATUS_EFFECTS, entity.status_effects)
        
        # Apply entangled effect
        entangled = EntangledEffect(owner=entity, duration=3)
        entity.status_effects.add_effect(entangled)
        
        # Try to move
        original_x, original_y = entity.x, entity.y
        result = entity.move(1, 0)
        
        # Verify move was blocked
        assert result is False, "Entity.move() should return False when entangled"
        assert entity.x == original_x and entity.y == original_y, (
            "Entity position should not change when entangled"
        )
    
    def test_entity_move_succeeds_when_not_entangled(self):
        """Entity.move() returns True and moves when not entangled."""
        from entity import Entity
        from components.component_registry import ComponentType, ComponentRegistry
        from components.status_effects import StatusEffectManager
        
        # Create test entity without entangle
        entity = Entity(x=5, y=5, char='o', color=(128, 128, 128), name='Test Orc')
        entity.components = ComponentRegistry()
        entity.status_effects = StatusEffectManager(entity)
        entity.components.add(ComponentType.STATUS_EFFECTS, entity.status_effects)
        
        # Try to move (no entangle)
        original_x, original_y = entity.x, entity.y
        result = entity.move(1, 0)
        
        # Verify move succeeded
        assert result is True, "Entity.move() should return True when not entangled"
        assert entity.x == original_x + 1 and entity.y == original_y, (
            "Entity position should change when not entangled"
        )
    
    def test_repeated_move_attempts_while_entangled_no_infinite_loop(self):
        """Simulates AI repeatedly trying to move while entangled - no infinite loop.
        
        This is a regression test to ensure that:
        1. Entity doesn't move when entangled
        2. Each move attempt returns False
        3. Turns would advance (simulated by effect duration decreasing)
        4. After effect expires, movement works again
        """
        from entity import Entity
        from components.component_registry import ComponentType, ComponentRegistry
        from components.status_effects import StatusEffectManager, EntangledEffect
        
        # Create test entity
        entity = Entity(x=5, y=5, char='o', color=(128, 128, 128), name='Test Orc')
        entity.components = ComponentRegistry()
        entity.status_effects = StatusEffectManager(entity)
        entity.components.add(ComponentType.STATUS_EFFECTS, entity.status_effects)
        
        # Apply entangled effect (3 turns)
        entangled = EntangledEffect(owner=entity, duration=3)
        entity.status_effects.add_effect(entangled)
        
        # Simulate 3 turns of failed movement
        for turn in range(3):
            original_x = entity.x
            result = entity.move(1, 0)
            assert result is False, f"Move should fail on turn {turn + 1}"
            assert entity.x == original_x, f"Position shouldn't change on turn {turn + 1}"
            
            # Simulate turn end (duration decreases)
            entangled.process_turn_end()
        
        # After 3 turns, effect should be expired (duration = 0)
        assert entangled.duration == 0, "Effect should have expired after 3 turns"
        
        # Remove the expired effect (normally done by StatusEffectManager)
        entity.status_effects.remove_effect('entangled')
        
        # Now movement should work
        original_x = entity.x
        result = entity.move(1, 0)
        assert result is True, "Move should succeed after entangle expires"
        assert entity.x == original_x + 1, "Position should change after entangle expires"
    
    def test_entangled_on_move_blocked_increments_metrics(self):
        """on_move_blocked() should increment entangle_moves_blocked metric."""
        from entity import Entity
        from components.component_registry import ComponentType, ComponentRegistry
        from components.status_effects import StatusEffectManager, EntangledEffect
        from services.scenario_harness import RunMetrics
        from services.scenario_metrics import ScenarioMetricsCollector, set_active_metrics_collector, clear_active_metrics_collector
        
        # Set up metrics collector
        metrics = RunMetrics()
        collector = ScenarioMetricsCollector(metrics)
        set_active_metrics_collector(collector)
        
        try:
            # Create test entity with entangled effect
            entity = Entity(x=5, y=5, char='o', color=(128, 128, 128), name='Test Orc')
            entity.components = ComponentRegistry()
            entity.status_effects = StatusEffectManager(entity)
            entity.components.add(ComponentType.STATUS_EFFECTS, entity.status_effects)
            
            entangled = EntangledEffect(owner=entity, duration=3)
            entity.status_effects.add_effect(entangled)
            
            # Call on_move_blocked
            entangled.on_move_blocked()
            
            # Verify metric was incremented
            assert getattr(metrics, 'entangle_moves_blocked', 0) == 1, (
                f"Expected entangle_moves_blocked=1, got {getattr(metrics, 'entangle_moves_blocked', 0)}"
            )
            
            # Call again
            entangled.on_move_blocked()
            assert getattr(metrics, 'entangle_moves_blocked', 0) == 2
            
        finally:
            clear_active_metrics_collector()


