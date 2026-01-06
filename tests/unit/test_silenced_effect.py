"""Unit tests for SilencedEffect (Phase 20F).

Tests basic silence effect functionality:
- Default and custom durations
- Effect apply/remove messages
- Refresh-not-stack via StatusEffectManager
- is_entity_silenced helper function
- record_silenced_cast_blocked helper function
"""

import pytest
from unittest.mock import Mock, patch
from components.status_effects import (
    SilencedEffect,
    StatusEffectManager,
    is_entity_silenced,
    record_silenced_cast_blocked,
)
from components.component_registry import ComponentType


def test_silenced_effect_default_duration():
    """Test that SilencedEffect has correct default duration."""
    entity = Mock()
    entity.name = "Test"
    
    effect = SilencedEffect(owner=entity)
    
    assert effect.duration == 3, "Default duration should be 3 turns"
    assert effect.name == "silenced"


def test_silenced_effect_custom_duration():
    """Test that SilencedEffect accepts custom duration."""
    entity = Mock()
    entity.name = "Test"
    
    effect = SilencedEffect(owner=entity, duration=5)
    
    assert effect.duration == 5, "Custom duration should be respected"


def test_silenced_effect_apply_message():
    """Test that applying silence shows appropriate message."""
    entity = Mock()
    entity.name = "Orc Shaman"
    
    effect = SilencedEffect(owner=entity, duration=3)
    results = effect.apply()
    
    # Verify apply sets is_active
    assert effect.is_active
    
    # Verify message exists
    assert len(results) > 0
    assert any('silenced' in str(r.get('message', '')).lower() for r in results)


def test_silenced_effect_remove_message():
    """Test that removing silenced effect shows appropriate message."""
    entity = Mock()
    entity.name = "Test"
    
    effect = SilencedEffect(owner=entity, duration=3)
    results = effect.remove()
    
    # Verify removal message
    assert len(results) > 0
    assert any('spell' in str(r.get('message', '')).lower() for r in results)


def test_silenced_effect_refresh_via_manager():
    """Test that StatusEffectManager refreshes silence duration instead of stacking."""
    entity = Mock()
    entity.name = "Orc Shaman"
    entity.equipment = None  # No equipment (simplest case)
    manager = StatusEffectManager(entity)
    
    # Apply first silence
    effect1 = SilencedEffect(owner=entity, duration=3)
    manager.add_effect(effect1)
    
    # Verify first effect is active
    assert manager.has_effect('silenced')
    active_effect = manager.get_effect('silenced')
    assert active_effect.duration == 3
    assert active_effect.is_active
    
    # Reduce duration to simulate passage of time
    active_effect.duration = 1
    
    # Apply second silence (should refresh, not stack)
    effect2 = SilencedEffect(owner=entity, duration=3)
    results = manager.add_effect(effect2)
    
    # Verify duration was refreshed to 3
    refreshed_effect = manager.get_effect('silenced')
    assert refreshed_effect.duration == 3, "Duration should be refreshed to 3"
    
    # Verify only one silenced effect exists
    silenced_effects = [e for e in manager.active_effects.values() if e.name == 'silenced']
    assert len(silenced_effects) == 1, "Should only have one silenced effect (no stacking)"
    
    # Verify refresh message was sent
    assert any('refreshed' in str(r.get('message', '')).lower() for r in results)


def test_is_entity_silenced_returns_false_when_no_status_effects():
    """Test is_entity_silenced returns False when entity has no status effects."""
    entity = Mock()
    entity.get_component_optional = Mock(return_value=None)
    
    result = is_entity_silenced(entity)
    
    assert result is False


def test_is_entity_silenced_returns_false_when_not_silenced():
    """Test is_entity_silenced returns False when entity not silenced."""
    entity = Mock()
    status_effects = Mock()
    status_effects.has_effect = Mock(return_value=False)
    entity.get_component_optional = Mock(return_value=status_effects)
    
    result = is_entity_silenced(entity)
    
    assert result is False
    status_effects.has_effect.assert_called_once_with('silenced')


def test_is_entity_silenced_returns_true_when_silenced():
    """Test is_entity_silenced returns True when entity has SilencedEffect."""
    entity = Mock()
    status_effects = Mock()
    status_effects.has_effect = Mock(return_value=True)
    entity.get_component_optional = Mock(return_value=status_effects)
    
    result = is_entity_silenced(entity)
    
    assert result is True
    status_effects.has_effect.assert_called_once_with('silenced')


def test_is_entity_silenced_handles_none_entity():
    """Test is_entity_silenced handles None entity gracefully."""
    result = is_entity_silenced(None)
    
    assert result is False


def test_record_silenced_cast_blocked_increments_metric():
    """Test record_silenced_cast_blocked increments the correct metric."""
    with patch('components.status_effects._get_metrics_collector') as mock_get_collector:
        mock_collector = Mock()
        mock_get_collector.return_value = mock_collector
        
        record_silenced_cast_blocked("Orc Shaman")
        
        mock_collector.increment.assert_called_once_with('silenced_casts_blocked')


def test_record_silenced_cast_blocked_handles_no_collector():
    """Test record_silenced_cast_blocked handles case when no collector available."""
    with patch('components.status_effects._get_metrics_collector') as mock_get_collector:
        mock_get_collector.return_value = None
        
        # Should not raise
        record_silenced_cast_blocked("Test")


def test_silenced_effect_repr():
    """Test SilencedEffect string representation."""
    entity = Mock()
    entity.name = "Test"
    
    effect = SilencedEffect(owner=entity, duration=3)
    
    repr_str = repr(effect)
    assert "SilencedEffect" in repr_str
    assert "3" in repr_str


# ============================================================
# Phase 20F: Canonical gate tests - prove executors block silence
# ============================================================

def test_spell_executor_blocks_silenced_caster():
    """Test SpellExecutor.cast() blocks silenced caster at execution point.
    
    This proves the canonical gate works - even if AI forgets to check,
    the spell executor will block the cast.
    """
    from spells.spell_executor import SpellExecutor
    from spells.spell_definition import SpellDefinition
    from spells.spell_types import SpellCategory, TargetingType
    
    # Create silenced caster
    caster = Mock()
    caster.name = "Silenced Wizard"
    status_effects = Mock()
    status_effects.has_effect = Mock(return_value=True)  # silenced
    caster.get_component_optional = Mock(return_value=status_effects)
    
    # Create a simple spell definition
    spell = SpellDefinition(
        spell_id="test_fireball",
        name="Fireball",
        category=SpellCategory.OFFENSIVE,
        targeting=TargetingType.AOE,
    )
    
    # Execute via SpellExecutor
    executor = SpellExecutor()
    results = executor.cast(spell, caster)
    
    # Verify: cast was blocked
    assert len(results) > 0, "Should return results"
    assert any('silenced' in str(r.get('message', '')).lower() for r in results), \
        "Should contain 'silenced' in blocked message"
    # Verify: action was consumed (turn taken, spell not cast)
    assert any(r.get('consumed') is True for r in results), \
        "Action should be marked as consumed"


def test_inventory_use_blocks_silenced_player_scroll():
    """Test Inventory.use() blocks silenced player using scroll.
    
    This proves the canonical gate at Inventory.use() level blocks
    scroll usage for silenced players.
    """
    from components.inventory import Inventory
    from components.item import Item
    from components.component_registry import ComponentRegistry, ComponentType
    
    # Create silenced player
    player = Mock()
    player.name = "Silenced Player"
    status_effects = Mock()
    status_effects.has_effect = Mock(return_value=True)  # silenced
    player.get_component_optional = Mock(return_value=status_effects)
    
    # Create inventory
    inventory = Inventory(capacity=10)
    inventory.owner = player
    
    # Create a scroll item entity
    scroll_entity = Mock()
    scroll_entity.name = "Scroll of Fireball"
    
    # Setup item component
    item_component = Mock()
    item_component.use_function = Mock(return_value=[{"consumed": True}])
    item_component.function_kwargs = {}
    item_component.targeting = False
    
    # Mock get_component_optional to return item_component
    def get_comp(comp_type):
        if comp_type == ComponentType.ITEM:
            return item_component
        return None
    scroll_entity.get_component_optional = get_comp
    scroll_entity.equippable = None
    
    # Add scroll to inventory
    inventory.items = [scroll_entity]
    
    # Try to use the scroll
    results = inventory.use(scroll_entity)
    
    # Verify: scroll use was blocked
    assert len(results) > 0, "Should return results"
    assert any('silenced' in str(r.get('message', '')).lower() for r in results), \
        "Should contain 'silenced' in blocked message"
    # Verify: use_function was NOT called
    item_component.use_function.assert_not_called()


def test_inventory_use_allows_silenced_player_potion():
    """Test Inventory.use() allows silenced player to use potions.
    
    Potions are NOT spell-like, so they should not be blocked by silence.
    """
    from components.inventory import Inventory
    from components.item import Item
    from components.component_registry import ComponentRegistry, ComponentType
    
    # Create silenced player
    player = Mock()
    player.name = "Silenced Player"
    status_effects = Mock()
    status_effects.has_effect = Mock(return_value=True)  # silenced
    player.get_component_optional = Mock(return_value=status_effects)
    
    # Create inventory
    inventory = Inventory(capacity=10)
    inventory.owner = player
    
    # Create a potion item entity (NOT a scroll)
    potion_entity = Mock()
    potion_entity.name = "Healing Potion"  # Not a scroll!
    
    # Setup item component with all required attributes
    item_component = Mock()
    item_component.use_function = Mock(return_value=[{"consumed": True, "message": "Healed!"}])
    item_component.function_kwargs = {}
    item_component.targeting = False
    item_component.stackable = False  # Not stackable
    item_component.quantity = 1
    
    # Mock get_component_optional
    def get_comp(comp_type):
        if comp_type == ComponentType.ITEM:
            return item_component
        return None
    potion_entity.get_component_optional = get_comp
    potion_entity.equippable = None
    
    # Mock wand attribute
    potion_entity.wand = None
    
    # Add potion to inventory
    inventory.items = [potion_entity]
    
    # Try to use the potion
    results = inventory.use(potion_entity)
    
    # Verify: potion use was NOT blocked
    item_component.use_function.assert_called_once()
    # Verify: results contain the use function output
    assert any('Healed!' in str(r.get('message', '')) for r in results), \
        "Potion should have been used successfully"

