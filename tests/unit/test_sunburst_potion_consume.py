"""Unit tests for Sunburst Potion consumption (Focused buff) and throwing (Blinded debuff).

Phase 20E.1: Sunburst Potion dual-mode consumable
- THROWN: Applies BlindedEffect (-4 to-hit penalty on target)
- CONSUMED: Applies FocusedEffect (accuracy buff, +2 to-hit)

This test module validates both mode behaviors.
"""

import pytest


class TestSunburstPotionConsume:
    """Test Sunburst Potion consumption applies Focused buff correctly."""
    
    def test_drink_sunburst_potion_applies_focused(self):
        """Drinking Sunburst Potion applies FocusedEffect to the drinker."""
        from entity import Entity
        from components.component_registry import ComponentType
        from components.status_effects import StatusEffectManager, FocusedEffect
        from item_functions import drink_sunburst_potion
        
        # Create test entity
        entity = Entity(x=0, y=0, char='@', color=(255, 255, 255), name='Test Player')
        entity.status_effects = StatusEffectManager(entity)
        entity.components.add(ComponentType.STATUS_EFFECTS, entity.status_effects)
        
        # Drink the potion
        results = drink_sunburst_potion(entity)
        
        # Verify focused effect is active
        assert entity.status_effects.has_effect('focused'), (
            "Focused effect should be active after drinking sunburst potion"
        )
        
        # Verify effect properties
        focused = entity.status_effects.get_effect('focused')
        assert focused is not None
        assert focused.duration == 8, f"Expected duration 8, got {focused.duration}"
        assert focused.to_hit_bonus == 2, f"Expected to-hit bonus 2, got {focused.to_hit_bonus}"
        
        # Verify consumption
        assert any(r.get('consumed') for r in results), "Potion should be consumed"
    
    def test_drink_sunburst_potion_does_not_apply_blinded(self):
        """Drinking Sunburst Potion should NOT apply BlindedEffect to self."""
        from entity import Entity
        from components.component_registry import ComponentType
        from components.status_effects import StatusEffectManager
        from item_functions import drink_sunburst_potion
        
        # Create test entity
        entity = Entity(x=0, y=0, char='@', color=(255, 255, 255), name='Test Player')
        entity.status_effects = StatusEffectManager(entity)
        entity.components.add(ComponentType.STATUS_EFFECTS, entity.status_effects)
        
        # Drink the potion
        drink_sunburst_potion(entity)
        
        # Verify blinded is NOT applied
        assert not entity.status_effects.has_effect('blinded'), (
            "Blinded effect should NOT be applied when drinking (only when thrown)"
        )
    
    def test_focused_duration_refresh_not_stack(self):
        """Reapplying Focused refreshes duration, doesn't stack to-hit bonus."""
        from entity import Entity
        from components.component_registry import ComponentType
        from components.status_effects import StatusEffectManager
        from item_functions import drink_sunburst_potion
        
        # Create test entity
        entity = Entity(x=0, y=0, char='@', color=(255, 255, 255), name='Test Player')
        entity.status_effects = StatusEffectManager(entity)
        entity.components.add(ComponentType.STATUS_EFFECTS, entity.status_effects)
        
        # Drink first potion
        drink_sunburst_potion(entity)
        
        # Simulate some turns passing
        focused = entity.status_effects.get_effect('focused')
        focused.duration -= 4  # 4 turns passed
        assert focused.duration == 4
        
        # Drink second potion - should refresh to full duration
        drink_sunburst_potion(entity)
        
        # Duration should be refreshed to 8
        focused = entity.status_effects.get_effect('focused')
        assert focused.duration == 8, (
            f"Expected duration refreshed to 8, got {focused.duration}"
        )
        
        # To-hit bonus should NOT stack (still +2)
        assert focused.to_hit_bonus == 2, (
            f"Expected to-hit bonus 2 (not stacked), got {focused.to_hit_bonus}"
        )


class TestSunburstPotionThrow:
    """Test Sunburst Potion throwing applies Blinded effect correctly."""
    
    def test_throw_sunburst_potion_applies_blinded(self):
        """Throwing Sunburst Potion at target applies BlindedEffect."""
        from entity import Entity
        from components.component_registry import ComponentType
        from components.status_effects import StatusEffectManager, BlindedEffect
        from item_functions import apply_sunburst_potion_throw
        
        # Create test entity (the target)
        target = Entity(x=5, y=5, char='o', color=(128, 128, 128), name='Test Orc')
        target.status_effects = StatusEffectManager(target)
        target.components.add(ComponentType.STATUS_EFFECTS, target.status_effects)
        
        # Throw potion at target
        results = apply_sunburst_potion_throw(target)
        
        # Verify blinded effect is active
        assert target.status_effects.has_effect('blinded'), (
            "Blinded effect should be active after being hit by sunburst potion"
        )
        
        # Verify effect properties
        blinded = target.status_effects.get_effect('blinded')
        assert blinded is not None
        assert blinded.duration == 3, f"Expected duration 3, got {blinded.duration}"
        assert blinded.to_hit_penalty == 4, f"Expected to-hit penalty 4, got {blinded.to_hit_penalty}"
        
        # Verify consumption
        assert any(r.get('consumed') for r in results), "Potion should be consumed"
    
    def test_throw_sunburst_potion_does_not_apply_focused(self):
        """Throwing Sunburst Potion should NOT apply FocusedEffect to target."""
        from entity import Entity
        from components.component_registry import ComponentType
        from components.status_effects import StatusEffectManager
        from item_functions import apply_sunburst_potion_throw
        
        # Create test entity (the target)
        target = Entity(x=5, y=5, char='o', color=(128, 128, 128), name='Test Orc')
        target.status_effects = StatusEffectManager(target)
        target.components.add(ComponentType.STATUS_EFFECTS, target.status_effects)
        
        # Throw potion at target
        apply_sunburst_potion_throw(target)
        
        # Verify focused is NOT applied
        assert not target.status_effects.has_effect('focused'), (
            "Focused effect should NOT be applied when throwing (only when drunk)"
        )
    
    def test_blinded_duration_refresh_not_stack(self):
        """Reapplying Blinded refreshes duration, no stacking."""
        from entity import Entity
        from components.component_registry import ComponentType
        from components.status_effects import StatusEffectManager
        from item_functions import apply_sunburst_potion_throw
        
        # Create test entity (the target)
        target = Entity(x=5, y=5, char='o', color=(128, 128, 128), name='Test Orc')
        target.status_effects = StatusEffectManager(target)
        target.components.add(ComponentType.STATUS_EFFECTS, target.status_effects)
        
        # First throw
        apply_sunburst_potion_throw(target)
        
        # Simulate time passing
        blinded = target.status_effects.get_effect('blinded')
        blinded.duration -= 2  # 2 turns passed
        assert blinded.duration == 1
        
        # Second throw - should refresh to full duration
        apply_sunburst_potion_throw(target)
        
        # Duration should be refreshed to 3
        blinded = target.status_effects.get_effect('blinded')
        assert blinded.duration == 3, (
            f"Expected duration refreshed to 3, got {blinded.duration}"
        )
        
        # To-hit penalty should NOT stack (still -4)
        assert blinded.to_hit_penalty == 4, (
            f"Expected to-hit penalty 4 (not stacked), got {blinded.to_hit_penalty}"
        )


class TestBlindedEffectBehavior:
    """Test BlindedEffect to-hit penalty behavior."""
    
    def test_blinded_applies_to_hit_penalty(self):
        """BlindedEffect applies -4 to-hit penalty in Fighter.attack_d20()."""
        from entity import Entity
        from components.component_registry import ComponentType, ComponentRegistry
        from components.status_effects import StatusEffectManager, BlindedEffect
        from components.fighter import Fighter
        
        # Create test attacker
        attacker = Entity(x=5, y=5, char='@', color=(255, 255, 255), name='Test Player')
        attacker.components = ComponentRegistry()
        attacker.status_effects = StatusEffectManager(attacker)
        attacker.components.add(ComponentType.STATUS_EFFECTS, attacker.status_effects)
        # Fighter component auto-registers via Entity.__setattr__, so just assign it
        attacker.fighter = Fighter(hp=30, defense=5, power=5, strength=14, dexterity=14, constitution=14)
        attacker.fighter.owner = attacker
        
        # Apply blinded effect
        blinded = BlindedEffect(owner=attacker, duration=3)
        attacker.status_effects.add_effect(blinded)
        
        # Verify has_status_effect method works
        assert attacker.has_status_effect('blinded') if hasattr(attacker, 'has_status_effect') else (
            attacker.status_effects.has_effect('blinded')
        ), "Attacker should have blinded status"
        
        # Note: Full to-hit calculation testing requires mocking attack_d20(),
        # which is integration-tested in the scenario metrics test.
        # This unit test validates effect application only.
    
    def test_blinded_metrics_increment_on_apply(self):
        """BlindedEffect.apply() should increment blind_applications metric."""
        from entity import Entity
        from components.component_registry import ComponentType, ComponentRegistry
        from components.status_effects import StatusEffectManager, BlindedEffect
        from services.scenario_harness import RunMetrics
        from services.scenario_metrics import ScenarioMetricsCollector, set_active_metrics_collector, clear_active_metrics_collector
        
        # Set up metrics collector
        metrics = RunMetrics()
        collector = ScenarioMetricsCollector(metrics)
        set_active_metrics_collector(collector)
        
        try:
            # Create test entity
            entity = Entity(x=5, y=5, char='o', color=(128, 128, 128), name='Test Orc')
            entity.components = ComponentRegistry()
            entity.status_effects = StatusEffectManager(entity)
            entity.components.add(ComponentType.STATUS_EFFECTS, entity.status_effects)
            
            # Apply blinded effect
            blinded = BlindedEffect(owner=entity, duration=3)
            entity.status_effects.add_effect(blinded)
            
            # Verify metric was incremented
            assert getattr(metrics, 'blind_applications', 0) == 1, (
                f"Expected blind_applications=1, got {getattr(metrics, 'blind_applications', 0)}"
            )
            
            # Apply again (refresh)
            blinded2 = BlindedEffect(owner=entity, duration=3)
            entity.status_effects.add_effect(blinded2)
            
            # Metric should increment again (refresh counts as new application)
            assert getattr(metrics, 'blind_applications', 0) == 2
            
        finally:
            clear_active_metrics_collector()


class TestUseSunburstPotionDispatcher:
    """Test use_sunburst_potion() dispatcher chooses correct mode."""
    
    def test_use_sunburst_potion_with_throw_mode_kwarg(self):
        """use_sunburst_potion(throw_mode=True) should apply BlindedEffect."""
        from entity import Entity
        from components.component_registry import ComponentType
        from components.status_effects import StatusEffectManager
        from item_functions import use_sunburst_potion
        
        # Create test entities
        user = Entity(x=0, y=0, char='@', color=(255, 255, 255), name='Test Player')
        target = Entity(x=5, y=5, char='o', color=(128, 128, 128), name='Test Orc')
        
        user.status_effects = StatusEffectManager(user)
        user.components.add(ComponentType.STATUS_EFFECTS, user.status_effects)
        target.status_effects = StatusEffectManager(target)
        target.components.add(ComponentType.STATUS_EFFECTS, target.status_effects)
        
        # Use potion with throw_mode=True
        # NOTE: In throw mode, first arg is the TARGET (receiving entity), not the user
        use_sunburst_potion(target, throw_mode=True, target_x=target.x, target_y=target.y)
        
        # Verify target has blinded
        assert target.status_effects.has_effect('blinded'), "Target should be blinded"
    
    def test_use_sunburst_potion_default_mode_applies_focused(self):
        """use_sunburst_potion() with no kwargs should default to CONSUMED (FocusedEffect)."""
        from entity import Entity
        from components.component_registry import ComponentType
        from components.status_effects import StatusEffectManager
        from item_functions import use_sunburst_potion
        
        # Create test entity
        entity = Entity(x=0, y=0, char='@', color=(255, 255, 255), name='Test Player')
        entity.status_effects = StatusEffectManager(entity)
        entity.components.add(ComponentType.STATUS_EFFECTS, entity.status_effects)
        
        # Use potion with no mode specified (default to consume)
        use_sunburst_potion(entity)
        
        # Verify user has focused, not blinded
        assert entity.status_effects.has_effect('focused'), "User should be focused"
        assert not entity.status_effects.has_effect('blinded'), "User should not be blinded"



