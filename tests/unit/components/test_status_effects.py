"""Unit tests for status effects, focusing on Phase 7 debuff mechanics.

Tests cover:
- SluggishEffect duration, stacking, and decay
- Potion of Tar usage and effect application
- Integration with SpeedBonusTracker debuff system
- VFX queuing when debuff applies
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from components.status_effects import (
    StatusEffect,
    StatusEffectManager,
    SluggishEffect,
    SlowedEffect,
    LightningReflexesEffect,
)
from components.speed_bonus_tracker import SpeedBonusTracker
from components.component_registry import ComponentType


class MockEntity:
    """Mock entity for testing status effects."""
    
    def __init__(self, name: str = "TestEntity"):
        self.name = name
        self.x = 5
        self.y = 5
        self.components = MockComponentRegistry()
        self.status_effects = None
        self.speed_bonus_tracker = None
    
    def get_component_optional(self, component_type):
        """Mock component retrieval."""
        if component_type == ComponentType.SPEED_BONUS_TRACKER:
            return self.speed_bonus_tracker
        return None


class MockComponentRegistry:
    """Mock component registry."""
    
    def __init__(self):
        self._components = {}
    
    def has(self, component_type):
        return component_type in self._components
    
    def add(self, component_type, component):
        self._components[component_type] = component
    
    def get(self, component_type):
        return self._components.get(component_type)


class TestSluggishEffectBasics:
    """Tests for SluggishEffect basic behavior."""
    
    def test_initialization(self):
        """Test SluggishEffect initializes with correct values."""
        entity = MockEntity()
        effect = SluggishEffect(duration=10, owner=entity, speed_penalty=0.25)
        
        assert effect.name == "sluggish"
        assert effect.duration == 10
        assert effect.speed_penalty == 0.25
        assert effect.owner == entity
    
    def test_default_speed_penalty(self):
        """Test default speed penalty is 0.25 (-25%)."""
        entity = MockEntity()
        effect = SluggishEffect(duration=5, owner=entity)
        
        assert effect.speed_penalty == 0.25
    
    def test_apply_message(self):
        """Test apply() returns appropriate message."""
        entity = MockEntity()
        effect = SluggishEffect(duration=10, owner=entity, speed_penalty=0.25)
        
        results = effect.apply()
        
        # Should have a message about feeling sluggish
        assert len(results) > 0
        messages = [r.get('message') for r in results if 'message' in r]
        assert len(messages) > 0
        # Message content check - should mention sluggish and the penalty
        message_text = str(messages[0])
        assert "sluggish" in message_text.lower()
    
    def test_remove_message(self):
        """Test remove() returns appropriate message."""
        entity = MockEntity()
        effect = SluggishEffect(duration=10, owner=entity)
        effect.apply()  # Must apply first
        
        results = effect.remove()
        
        assert len(results) > 0
        messages = [r.get('message') for r in results if 'message' in r]
        assert len(messages) > 0


class TestSluggishEffectWithSpeedTracker:
    """Tests for SluggishEffect integration with SpeedBonusTracker."""
    
    def test_apply_creates_tracker_if_missing(self):
        """Test that apply() creates SpeedBonusTracker if entity doesn't have one."""
        entity = MockEntity()
        effect = SluggishEffect(duration=10, owner=entity, speed_penalty=0.25)
        
        assert entity.speed_bonus_tracker is None
        
        effect.apply()
        
        # Should have created a tracker
        assert entity.speed_bonus_tracker is not None
    
    def test_apply_adds_debuff_to_existing_tracker(self):
        """Test that apply() adds debuff to existing tracker."""
        entity = MockEntity()
        tracker = SpeedBonusTracker(speed_bonus_ratio=0.0)
        entity.speed_bonus_tracker = tracker
        entity.components.add(ComponentType.SPEED_BONUS_TRACKER, tracker)
        
        effect = SluggishEffect(duration=10, owner=entity, speed_penalty=0.25)
        effect.apply()
        
        assert tracker._debuff_ratio == 0.25
    
    def test_remove_clears_debuff(self):
        """Test that remove() clears the debuff from tracker."""
        entity = MockEntity()
        tracker = SpeedBonusTracker(speed_bonus_ratio=0.0)
        entity.speed_bonus_tracker = tracker
        entity.components.add(ComponentType.SPEED_BONUS_TRACKER, tracker)
        
        effect = SluggishEffect(duration=10, owner=entity, speed_penalty=0.25)
        effect.apply()
        
        assert tracker._debuff_ratio == 0.25
        
        effect.remove()
        
        assert tracker._debuff_ratio == 0.0
    
    def test_debuff_stacks_additively_with_equipment(self):
        """Test that debuff stacks additively with equipment bonuses."""
        entity = MockEntity()
        tracker = SpeedBonusTracker(speed_bonus_ratio=0.0)
        entity.speed_bonus_tracker = tracker
        entity.components.add(ComponentType.SPEED_BONUS_TRACKER, tracker)
        
        # Add equipment bonus
        tracker.add_equipment_bonus(0.50, "Fast Boots")
        assert tracker.speed_bonus_ratio == 0.50
        
        # Apply sluggish effect
        effect = SluggishEffect(duration=10, owner=entity, speed_penalty=0.25)
        effect.apply()
        
        # Net should be 0.50 - 0.25 = 0.25
        assert tracker.speed_bonus_ratio == 0.25
    
    def test_debuff_can_reduce_to_zero(self):
        """Test that debuff can reduce speed bonus to zero."""
        entity = MockEntity()
        tracker = SpeedBonusTracker(speed_bonus_ratio=0.0)
        entity.speed_bonus_tracker = tracker
        entity.components.add(ComponentType.SPEED_BONUS_TRACKER, tracker)
        
        tracker.add_equipment_bonus(0.25, "Dagger")
        
        effect = SluggishEffect(duration=10, owner=entity, speed_penalty=0.25)
        effect.apply()
        
        # Should be exactly 0
        assert tracker.speed_bonus_ratio == 0.0
    
    def test_debuff_clamps_to_zero(self):
        """Test that net speed bonus cannot go negative."""
        entity = MockEntity()
        tracker = SpeedBonusTracker(speed_bonus_ratio=0.0)
        entity.speed_bonus_tracker = tracker
        entity.components.add(ComponentType.SPEED_BONUS_TRACKER, tracker)
        
        # No equipment bonus, apply large debuff
        effect = SluggishEffect(duration=10, owner=entity, speed_penalty=0.50)
        effect.apply()
        
        # Should clamp to 0, not go negative
        assert tracker.speed_bonus_ratio == 0.0


class TestSluggishEffectDuration:
    """Tests for SluggishEffect duration and decay."""
    
    def test_duration_decrements_on_turn_end(self):
        """Test that duration decreases each turn."""
        entity = MockEntity()
        effect = SluggishEffect(duration=5, owner=entity)
        effect.apply()
        
        assert effect.duration == 5
        
        effect.process_turn_end()
        assert effect.duration == 4
        
        effect.process_turn_end()
        assert effect.duration == 3
    
    def test_effect_expires_at_zero_duration(self):
        """Test that effect is ready for removal when duration hits 0."""
        entity = MockEntity()
        effect = SluggishEffect(duration=2, owner=entity)
        effect.apply()
        
        effect.process_turn_end()
        assert effect.duration == 1
        
        effect.process_turn_end()
        assert effect.duration == 0


class TestSluggishEffectStacking:
    """Tests for multiple SluggishEffect stacking behavior."""
    
    def test_multiple_debuffs_stack(self):
        """Test that multiple debuff sources stack additively."""
        entity = MockEntity()
        tracker = SpeedBonusTracker(speed_bonus_ratio=0.0)
        entity.speed_bonus_tracker = tracker
        entity.components.add(ComponentType.SPEED_BONUS_TRACKER, tracker)
        
        tracker.add_equipment_bonus(1.0, "Super Speed Boots")  # +100%
        
        # Apply first debuff
        tracker.add_debuff(0.25, "tar")
        assert tracker.speed_bonus_ratio == 0.75  # 1.0 - 0.25
        
        # Apply second debuff
        tracker.add_debuff(0.25, "slow spell")
        assert tracker.speed_bonus_ratio == 0.50  # 1.0 - 0.50
    
    def test_removing_one_debuff_leaves_others(self):
        """Test that removing one debuff doesn't affect others."""
        entity = MockEntity()
        tracker = SpeedBonusTracker(speed_bonus_ratio=0.0)
        entity.speed_bonus_tracker = tracker
        entity.components.add(ComponentType.SPEED_BONUS_TRACKER, tracker)
        
        tracker.add_equipment_bonus(1.0, "Boots")
        tracker.add_debuff(0.25, "tar")
        tracker.add_debuff(0.25, "slow")
        
        assert tracker.speed_bonus_ratio == 0.50
        
        # Remove one debuff
        tracker.remove_debuff(0.25, "tar")
        
        assert tracker.speed_bonus_ratio == 0.75  # Still have slow debuff


class TestStatusEffectManagerWithSluggish:
    """Tests for StatusEffectManager handling SluggishEffect."""
    
    def test_add_sluggish_effect(self):
        """Test adding SluggishEffect via manager."""
        entity = MockEntity()
        manager = StatusEffectManager(entity)
        entity.status_effects = manager
        
        effect = SluggishEffect(duration=10, owner=entity)
        results = manager.add_effect(effect)
        
        assert manager.has_effect("sluggish")
        assert len(results) > 0
    
    def test_refresh_extends_duration(self):
        """Test that re-applying refreshes the effect."""
        entity = MockEntity()
        manager = StatusEffectManager(entity)
        entity.status_effects = manager
        
        effect1 = SluggishEffect(duration=5, owner=entity)
        manager.add_effect(effect1)
        
        # Simulate some turns
        manager.process_turn_end()
        manager.process_turn_end()
        
        # Re-apply with fresh duration
        effect2 = SluggishEffect(duration=10, owner=entity)
        manager.add_effect(effect2)
        
        current = manager.get_effect("sluggish")
        assert current.duration == 10
    
    def test_turn_end_removes_expired_effect(self):
        """Test that turn end processing removes expired effects."""
        entity = MockEntity()
        tracker = SpeedBonusTracker(speed_bonus_ratio=0.25)
        entity.speed_bonus_tracker = tracker
        entity.components.add(ComponentType.SPEED_BONUS_TRACKER, tracker)
        
        manager = StatusEffectManager(entity)
        entity.status_effects = manager
        
        effect = SluggishEffect(duration=1, owner=entity, speed_penalty=0.25)
        manager.add_effect(effect)
        
        assert manager.has_effect("sluggish")
        assert tracker._debuff_ratio == 0.25
        
        # Process turn end - effect should expire
        manager.process_turn_end()
        
        assert not manager.has_effect("sluggish")
        assert tracker._debuff_ratio == 0.0  # Debuff should be cleaned up


class TestPotionOfTar:
    """Tests for Potion of Tar item function."""
    
    def test_drink_tar_potion_applies_effect(self):
        """Test that drinking tar potion applies SluggishEffect."""
        from item_functions import drink_tar_potion
        
        entity = MockEntity()
        
        results = drink_tar_potion(entity, duration=10, speed_penalty=0.25)
        
        # Should have consumed the potion
        consumed_results = [r for r in results if r.get('consumed')]
        assert len(consumed_results) > 0
        
        # Entity should have status effects
        assert entity.status_effects is not None
        assert entity.status_effects.has_effect("sluggish")
    
    def test_drink_tar_potion_uses_yaml_params(self):
        """Test that drink_tar_potion respects duration/penalty params."""
        from item_functions import drink_tar_potion
        
        entity = MockEntity()
        tracker = SpeedBonusTracker(speed_bonus_ratio=0.5)
        entity.speed_bonus_tracker = tracker
        entity.components.add(ComponentType.SPEED_BONUS_TRACKER, tracker)
        
        # Use custom params (as if from yaml)
        results = drink_tar_potion(entity, duration=15, speed_penalty=0.30)
        
        effect = entity.status_effects.get_effect("sluggish")
        assert effect.duration == 15
        assert effect.speed_penalty == 0.30
        assert tracker._debuff_ratio == 0.30
    
    def test_drink_tar_potion_default_values(self):
        """Test that drink_tar_potion uses defaults when params not provided."""
        from item_functions import drink_tar_potion
        
        entity = MockEntity()
        
        results = drink_tar_potion(entity)  # No params
        
        effect = entity.status_effects.get_effect("sluggish")
        assert effect.duration == 10  # Default
        assert effect.speed_penalty == 0.25  # Default
    
    def test_drink_tar_potion_no_entity(self):
        """Test that drink_tar_potion handles missing entity gracefully."""
        from item_functions import drink_tar_potion
        
        results = drink_tar_potion(None)
        
        # Should not consume
        consumed_results = [r for r in results if r.get('consumed')]
        assert len(consumed_results) == 0 or not consumed_results[0].get('consumed', True)


class TestSpeedBonusTrackerDebuff:
    """Tests for SpeedBonusTracker debuff functionality."""
    
    def test_add_debuff(self):
        """Test adding a debuff."""
        tracker = SpeedBonusTracker(speed_bonus_ratio=0.0)
        
        tracker.add_debuff(0.25, "test")
        
        assert tracker._debuff_ratio == 0.25
        assert tracker.has_debuff()
    
    def test_remove_debuff(self):
        """Test removing a debuff."""
        tracker = SpeedBonusTracker(speed_bonus_ratio=0.0)
        tracker.add_debuff(0.25, "test")
        
        tracker.remove_debuff(0.25, "test")
        
        assert tracker._debuff_ratio == 0.0
        assert not tracker.has_debuff()
    
    def test_remove_debuff_clamps_to_zero(self):
        """Test that removing more than exists clamps to zero."""
        tracker = SpeedBonusTracker(speed_bonus_ratio=0.0)
        tracker.add_debuff(0.10, "small")
        
        tracker.remove_debuff(0.50, "large")  # Remove more than added
        
        assert tracker._debuff_ratio == 0.0
    
    def test_speed_ratio_with_debuff(self):
        """Test speed_bonus_ratio property with debuff applied."""
        tracker = SpeedBonusTracker(speed_bonus_ratio=0.25)
        tracker.add_equipment_bonus(0.25, "Boots")
        
        # Base 0.25 + Equipment 0.25 = 0.50
        assert tracker.speed_bonus_ratio == 0.50
        
        tracker.add_debuff(0.20, "slow")
        
        # 0.50 - 0.20 = 0.30
        assert tracker.speed_bonus_ratio == 0.30
    
    def test_get_debuff_ratio(self):
        """Test get_debuff_ratio returns current debuff."""
        tracker = SpeedBonusTracker(speed_bonus_ratio=0.0)
        
        assert tracker.get_debuff_ratio() == 0.0
        
        tracker.add_debuff(0.35, "tar")
        
        assert tracker.get_debuff_ratio() == 0.35
    
    def test_bonus_sources_shows_debuff(self):
        """Test that get_bonus_sources includes debuff info."""
        tracker = SpeedBonusTracker(speed_bonus_ratio=0.0)
        tracker.add_equipment_bonus(0.25, "Dagger")
        tracker.add_debuff(0.10, "slow")
        
        sources = tracker.get_bonus_sources()
        
        assert "Debuffed" in sources or "10%" in sources


class TestVFXIntegration:
    """Tests for VFX integration with debuff effects."""
    
    def test_effect_type_slow_exists(self):
        """Test that SLOW effect type is defined."""
        from visual_effect_queue import EffectType
        
        assert hasattr(EffectType, 'SLOW')
    
    def test_effect_vfx_config_has_slow(self):
        """Test that SLOW is in the central VFX config."""
        from visual_effect_queue import EFFECT_VFX_CONFIG, EffectType
        
        assert EffectType.SLOW in EFFECT_VFX_CONFIG
        
        config = EFFECT_VFX_CONFIG[EffectType.SLOW]
        assert 'color' in config
        assert 'char' in config
    
    def test_slow_effect_color_is_orange(self):
        """Test that SLOW effect uses orange color."""
        from visual_effect_queue import get_effect_color, EffectType
        
        color = get_effect_color(EffectType.SLOW)
        
        # Orange-ish color (R > G > B)
        r, g, b = color
        assert r > 200  # Strong red component
        assert 100 <= g <= 200  # Medium green
        assert b < 100  # Low blue
    
    def test_queue_slow_effect(self):
        """Test queueing a slow effect."""
        from visual_effect_queue import get_effect_queue, EffectType
        
        queue = get_effect_queue()
        queue.clear()
        
        queue.queue_slow_effect(10, 20, entity=None)
        
        assert queue.has_effects()
        assert len(queue.effects) == 1
        assert queue.effects[0].effect_type == EffectType.SLOW
    
    def test_show_slow_effect_function(self):
        """Test the show_slow_effect convenience function."""
        from visual_effects import show_slow_effect
        from visual_effect_queue import get_effect_queue, EffectType
        
        queue = get_effect_queue()
        queue.clear()
        
        show_slow_effect(5, 10)
        
        assert queue.has_effects()
        assert queue.effects[0].effect_type == EffectType.SLOW
    
    def test_show_effect_vfx_unified_api(self):
        """Test the unified show_effect_vfx function."""
        from visual_effects import show_effect_vfx
        from visual_effect_queue import get_effect_queue, EffectType
        
        queue = get_effect_queue()
        queue.clear()
        
        show_effect_vfx(10, 20, EffectType.SLOW)
        
        assert queue.has_effects()
        effect = queue.effects[0]
        assert effect.effect_type == EffectType.SLOW
        assert effect.x == 10
        assert effect.y == 20


class TestSluggishVsSlowedEffect:
    """Tests to ensure SluggishEffect and SlowedEffect are distinct."""
    
    def test_different_effect_names(self):
        """Test that SluggishEffect and SlowedEffect have different names."""
        entity = MockEntity()
        
        sluggish = SluggishEffect(duration=5, owner=entity)
        slowed = SlowedEffect(duration=5, owner=entity)
        
        assert sluggish.name == "sluggish"
        assert slowed.name == "slowed"
        assert sluggish.name != slowed.name
    
    def test_sluggish_uses_tracker_slowed_skips_turns(self):
        """Test that SluggishEffect uses tracker, SlowedEffect skips turns."""
        entity = MockEntity()
        tracker = SpeedBonusTracker(speed_bonus_ratio=0.5)
        entity.speed_bonus_tracker = tracker
        entity.components.add(ComponentType.SPEED_BONUS_TRACKER, tracker)
        
        # Sluggish should modify tracker
        sluggish = SluggishEffect(duration=5, owner=entity, speed_penalty=0.25)
        sluggish.apply()
        
        assert tracker._debuff_ratio == 0.25
        
        # Slowed should have turn_counter attribute (for skip logic)
        slowed = SlowedEffect(duration=5, owner=entity)
        assert hasattr(slowed, 'turn_counter')
    
    def test_both_effects_can_coexist(self):
        """Test that both effects can be active simultaneously."""
        entity = MockEntity()
        manager = StatusEffectManager(entity)
        entity.status_effects = manager
        
        sluggish = SluggishEffect(duration=5, owner=entity)
        slowed = SlowedEffect(duration=5, owner=entity)
        
        manager.add_effect(sluggish)
        manager.add_effect(slowed)
        
        assert manager.has_effect("sluggish")
        assert manager.has_effect("slowed")


class TestLootTagsIntegration:
    """Tests for tar_potion loot tag configuration."""
    
    def test_tar_potion_loot_tag_exists(self):
        """Test that tar_potion has loot tags defined."""
        from balance.loot_tags import get_loot_tags
        
        tags = get_loot_tags("tar_potion")
        
        assert tags is not None
    
    def test_tar_potion_is_panic_category(self):
        """Test that tar_potion is categorized as panic."""
        from balance.loot_tags import get_loot_tags
        
        tags = get_loot_tags("tar_potion")
        
        assert tags.has_category("panic")
    
    def test_tar_potion_starts_band_2(self):
        """Test that tar_potion appears starting in Band 2."""
        from balance.loot_tags import get_loot_tags
        
        tags = get_loot_tags("tar_potion")
        
        assert tags.band_min == 2
        assert not tags.is_available_in_band(1)
        assert tags.is_available_in_band(2)
        assert tags.is_available_in_band(5)
