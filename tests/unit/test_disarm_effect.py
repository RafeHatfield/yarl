"""Unit tests for DisarmedEffect (Phase 20E.2).

Tests basic disarm effect functionality:
- Default and custom durations
- Effect apply/remove messages
- Refresh-not-stack via StatusEffectManager
"""

import pytest
from unittest.mock import Mock
from components.status_effects import DisarmedEffect, StatusEffectManager


def test_disarmed_effect_default_duration():
    """Test that DisarmedEffect has correct default duration."""
    entity = Mock()
    entity.name = "Test"
    
    effect = DisarmedEffect(owner=entity)
    
    assert effect.duration == 3, "Default duration should be 3 turns"
    assert effect.name == "disarmed"


def test_disarmed_effect_custom_duration():
    """Test that DisarmedEffect accepts custom duration."""
    entity = Mock()
    entity.name = "Test"
    
    effect = DisarmedEffect(owner=entity, duration=5)
    
    assert effect.duration == 5, "Custom duration should be respected"


def test_disarmed_effect_apply_message():
    """Test that applying disarm shows appropriate message."""
    entity = Mock()
    entity.name = "Orc"
    
    effect = DisarmedEffect(owner=entity, duration=3)
    results = effect.apply()
    
    # Verify apply sets is_active
    assert effect.is_active
    
    # Verify message exists
    assert len(results) > 0
    assert any('disarmed' in str(r.get('message', '')).lower() for r in results)


def test_disarmed_effect_remove_message():
    """Test that removing disarmed effect shows appropriate message."""
    entity = Mock()
    entity.name = "Test"
    
    effect = DisarmedEffect(owner=entity, duration=3)
    results = effect.remove()
    
    # Verify removal message
    assert len(results) > 0
    assert any('weapon grip' in str(r.get('message', '')).lower() for r in results)


def test_disarmed_effect_refresh_via_manager():
    """Test that StatusEffectManager refreshes disarm duration instead of stacking."""
    entity = Mock()
    entity.name = "Orc"
    entity.equipment = None  # No equipment (simplest case)
    manager = StatusEffectManager(entity)
    
    # Apply first disarm
    effect1 = DisarmedEffect(owner=entity, duration=3)
    manager.add_effect(effect1)
    
    # Verify first effect is active
    assert manager.has_effect('disarmed')
    active_effect = manager.get_effect('disarmed')
    assert active_effect.duration == 3
    assert active_effect.is_active
    
    # Reduce duration to simulate passage of time
    active_effect.duration = 1
    
    # Apply second disarm (should refresh, not stack)
    effect2 = DisarmedEffect(owner=entity, duration=3)
    results = manager.add_effect(effect2)
    
    # Verify duration was refreshed to 3
    refreshed_effect = manager.get_effect('disarmed')
    assert refreshed_effect.duration == 3, "Duration should be refreshed to 3"
    
    # Verify only one disarmed effect exists
    disarmed_effects = [e for e in manager.active_effects.values() if e.name == 'disarmed']
    assert len(disarmed_effects) == 1, "Should only have one disarmed effect (no stacking)"
    
    # Verify refresh message was sent
    assert any('refreshed' in str(r.get('message', '')).lower() for r in results)
