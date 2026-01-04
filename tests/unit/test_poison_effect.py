"""Unit tests for Phase 20A: Poison DOT Effect.

Tests cover:
- PoisonEffect initialization and defaults
- Duration ticking (decrement and expiration)
- Stacking/refresh behavior (non-stacking, refresh only)
- Resistance math (damage reduction calculation)
- Death finalization via poison (with state_manager)
- Metrics recording

This is the canonical DOT model - all future DOT effects should follow this pattern.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from components.status_effects import PoisonEffect, StatusEffectManager
from components.component_registry import ComponentType


class TestPoisonEffectInitialization:
    """Tests for PoisonEffect initialization and defaults."""
    
    def test_default_duration_is_six_turns(self):
        """PoisonEffect should default to 6 turns duration."""
        owner = Mock()
        owner.name = "TestEntity"
        
        effect = PoisonEffect(owner=owner)
        
        assert effect.duration == 6
        assert effect.name == "poison"
    
    def test_default_damage_is_one_per_tick(self):
        """PoisonEffect should default to 1 damage per tick."""
        owner = Mock()
        owner.name = "TestEntity"
        
        effect = PoisonEffect(owner=owner)
        
        assert effect.damage_per_tick == 1
    
    def test_custom_duration_and_damage(self):
        """PoisonEffect should accept custom duration and damage."""
        owner = Mock()
        owner.name = "TestEntity"
        
        effect = PoisonEffect(owner=owner, duration=10, damage_per_tick=3)
        
        assert effect.duration == 10
        assert effect.damage_per_tick == 3
    
    def test_effect_starts_inactive(self):
        """Effect should not be active until apply() is called."""
        owner = Mock()
        owner.name = "TestEntity"
        
        effect = PoisonEffect(owner=owner)
        
        assert not effect.is_active
    
    def test_apply_sets_active_flag(self):
        """apply() should set is_active to True."""
        owner = Mock()
        owner.name = "TestEntity"
        
        effect = PoisonEffect(owner=owner)
        effect.apply()
        
        assert effect.is_active


class TestPoisonDurationTicking:
    """Tests for poison duration mechanics."""
    
    def test_duration_decrements_on_turn_end(self):
        """Duration should decrease by 1 on each turn end."""
        owner = Mock()
        owner.name = "TestEntity"
        
        effect = PoisonEffect(owner=owner, duration=5)
        effect.apply()
        
        effect.process_turn_end()
        assert effect.duration == 4
        
        effect.process_turn_end()
        assert effect.duration == 3
    
    def test_poison_expires_at_zero_duration(self):
        """Effect should expire when duration reaches 0."""
        owner = Mock()
        owner.name = "TestEntity"
        
        effect = PoisonEffect(owner=owner, duration=1)
        effect.apply()
        
        effect.process_turn_end()
        assert effect.duration == 0
        # Duration <= 0 means effect should be removed by StatusEffectManager


class TestPoisonRefreshBehavior:
    """Tests for non-stacking refresh behavior."""
    
    def test_reapply_refreshes_duration(self):
        """Reapplying poison should refresh duration, not stack."""
        owner = Mock()
        owner.name = "TestEntity"
        owner.equipment = None
        owner.get_component_optional = Mock(return_value=None)
        
        manager = StatusEffectManager(owner)
        
        # Apply first poison
        poison1 = PoisonEffect(owner=owner, duration=6)
        manager.add_effect(poison1)
        
        # Tick down duration
        effect = manager.get_effect('poison')
        effect.process_turn_end()
        effect.process_turn_end()
        assert manager.get_effect('poison').duration == 4
        
        # Reapply poison
        poison2 = PoisonEffect(owner=owner, duration=6)
        manager.add_effect(poison2)
        
        # Duration should be refreshed to 6 (new effect replaces old)
        assert manager.get_effect('poison').duration == 6
    
    def test_only_one_poison_active(self):
        """Only one poison effect should be active at a time."""
        owner = Mock()
        owner.name = "TestEntity"
        owner.equipment = None
        owner.get_component_optional = Mock(return_value=None)
        
        manager = StatusEffectManager(owner)
        
        # Apply multiple poisons
        for _ in range(3):
            poison = PoisonEffect(owner=owner)
            manager.add_effect(poison)
        
        # Should only have one poison effect
        assert 'poison' in manager.active_effects
        assert len([k for k in manager.active_effects if k == 'poison']) == 1


class TestPoisonResistance:
    """Tests for poison resistance damage reduction."""
    
    def test_zero_resistance_full_damage(self):
        """With 0% resistance, full damage should be taken."""
        owner = Mock()
        owner.name = "TestEntity"
        owner.poison_resistance_pct = 0
        owner.get_component_optional = Mock(return_value=None)
        
        effect = PoisonEffect(owner=owner, damage_per_tick=2)
        
        damage = effect._calculate_damage_after_resistance()
        assert damage == 2
    
    def test_fifty_percent_resistance_halves_damage(self):
        """With 50% resistance, damage should be halved (rounded down)."""
        owner = Mock()
        owner.name = "TestEntity"
        owner.poison_resistance_pct = 50
        owner.get_component_optional = Mock(return_value=None)
        
        effect = PoisonEffect(owner=owner, damage_per_tick=2)
        
        damage = effect._calculate_damage_after_resistance()
        assert damage == 1
    
    def test_hundred_percent_resistance_zero_damage(self):
        """With 100% resistance (immunity), no damage should be taken."""
        owner = Mock()
        owner.name = "TestEntity"
        owner.poison_resistance_pct = 100
        owner.get_component_optional = Mock(return_value=None)
        
        effect = PoisonEffect(owner=owner, damage_per_tick=5)
        
        damage = effect._calculate_damage_after_resistance()
        assert damage == 0
    
    def test_resistance_from_fighter_component(self):
        """Resistance can come from fighter component."""
        owner = Mock()
        owner.name = "TestEntity"
        owner.poison_resistance_pct = 0  # No entity-level resistance
        
        # Fighter has resistance
        fighter = Mock()
        fighter.poison_resistance_pct = 75
        owner.get_component_optional = Mock(return_value=fighter)
        
        effect = PoisonEffect(owner=owner, damage_per_tick=4)
        
        damage = effect._calculate_damage_after_resistance()
        assert damage == 1  # 4 * 0.25 = 1
    
    def test_resistance_caps_at_100_percent(self):
        """Resistance should cap at 100% (no negative damage)."""
        owner = Mock()
        owner.name = "TestEntity"
        owner.poison_resistance_pct = 150  # Over 100%
        owner.get_component_optional = Mock(return_value=None)
        
        effect = PoisonEffect(owner=owner, damage_per_tick=10)
        
        damage = effect._calculate_damage_after_resistance()
        assert damage == 0
    
    def test_damage_rounds_down(self):
        """Damage after resistance should round down."""
        owner = Mock()
        owner.name = "TestEntity"
        owner.poison_resistance_pct = 33  # 1 * 0.67 = 0.67 -> 0
        owner.get_component_optional = Mock(return_value=None)
        
        effect = PoisonEffect(owner=owner, damage_per_tick=1)
        
        damage = effect._calculate_damage_after_resistance()
        assert damage == 0  # 1 * 0.67 rounds down to 0


class TestPoisonDamageApplication:
    """Tests for poison damage application."""
    
    def test_process_turn_start_deals_damage(self):
        """process_turn_start should deal poison damage."""
        owner = Mock()
        owner.name = "TestEntity"
        owner.poison_resistance_pct = 0
        
        fighter = Mock()
        fighter.take_damage = Mock(return_value=[])
        fighter.poison_resistance_pct = 0
        fighter.hp = 20  # Enough HP for non-lethal damage
        owner.get_component_optional = Mock(return_value=fighter)
        
        effect = PoisonEffect(owner=owner, damage_per_tick=2)
        effect.apply()
        
        with patch('logger_config.get_logger'):
            results = effect.process_turn_start(state_manager=None)
        
        # Fighter.take_damage should have been called with the damage
        fighter.take_damage.assert_called_once_with(2, damage_type="poison")
    
    @patch('services.scenario_metrics.get_active_metrics_collector')
    @patch('services.damage_service.apply_damage')
    def test_routes_through_damage_service_with_state_manager(
        self, mock_apply_damage, mock_get_collector
    ):
        """With state_manager, damage should route through damage_service."""
        owner = Mock()
        owner.name = "TestEntity"
        owner.poison_resistance_pct = 0
        owner.get_component_optional = Mock(return_value=None)
        
        mock_collector = Mock()
        mock_get_collector.return_value = mock_collector
        mock_apply_damage.return_value = []
        
        state_manager = Mock()
        
        effect = PoisonEffect(owner=owner, damage_per_tick=2)
        effect.apply()
        
        effect.process_turn_start(state_manager=state_manager)
        
        mock_apply_damage.assert_called_once()
        call_kwargs = mock_apply_damage.call_args[1]
        assert call_kwargs['state_manager'] == state_manager
        assert call_kwargs['target_entity'] == owner
        assert call_kwargs['amount'] == 2
        assert call_kwargs['cause'] == 'poison_dot'
        assert call_kwargs['damage_type'] == 'poison'
    
    def test_ticks_processed_increments(self):
        """ticks_processed counter should increment each turn."""
        owner = Mock()
        owner.name = "TestEntity"
        owner.poison_resistance_pct = 0
        
        fighter = Mock()
        fighter.take_damage = Mock(return_value=[])
        fighter.poison_resistance_pct = 0  # Set resistance on fighter
        fighter.hp = 20  # Enough HP for non-lethal damage
        owner.get_component_optional = Mock(return_value=fighter)
        
        effect = PoisonEffect(owner=owner)
        effect.apply()
        
        assert effect.ticks_processed == 0
        
        with patch('logger_config.get_logger'):
            effect.process_turn_start(state_manager=None)
        assert effect.ticks_processed == 1
        
        with patch('logger_config.get_logger'):
            effect.process_turn_start(state_manager=None)
        assert effect.ticks_processed == 2
    
    def test_total_damage_tracked(self):
        """total_damage_dealt should track cumulative damage."""
        owner = Mock()
        owner.name = "TestEntity"
        owner.poison_resistance_pct = 0
        
        fighter = Mock()
        fighter.take_damage = Mock(return_value=[])
        fighter.poison_resistance_pct = 0  # Set resistance on fighter
        fighter.hp = 20  # Enough HP for non-lethal damage
        owner.get_component_optional = Mock(return_value=fighter)
        
        effect = PoisonEffect(owner=owner, damage_per_tick=3)
        effect.apply()
        
        with patch('logger_config.get_logger'):
            effect.process_turn_start(state_manager=None)
            effect.process_turn_start(state_manager=None)
        
        assert effect.total_damage_dealt == 6  # 3 + 3


class TestPoisonDeathFinalization:
    """Tests for death finalization from poison."""
    
    @patch('services.scenario_metrics.get_active_metrics_collector')
    @patch('services.damage_service.apply_damage')
    def test_poison_kill_records_metric(self, mock_apply_damage, mock_get_collector):
        """Poison kills should record poison_kills metric."""
        owner = Mock()
        owner.name = "TestEntity"
        owner.poison_resistance_pct = 0
        owner.get_component_optional = Mock(return_value=None)
        
        mock_collector = Mock()
        mock_get_collector.return_value = mock_collector
        
        # Simulate death from damage
        mock_apply_damage.return_value = [{'dead': owner}]
        
        state_manager = Mock()
        
        effect = PoisonEffect(owner=owner)
        effect.apply()
        
        effect.process_turn_start(state_manager=state_manager)
        
        # Should have recorded poison_kills metric
        mock_collector.increment.assert_any_call('poison_kills')
    
    def test_lethal_damage_without_state_manager_clamps_to_nonlethal(self):
        """Lethal damage without state_manager should clamp to non-lethal."""
        owner = Mock()
        owner.name = "TestEntity"
        owner.poison_resistance_pct = 0
        
        fighter = Mock()
        fighter.take_damage = Mock(return_value=[])
        fighter.poison_resistance_pct = 0  # Set resistance on fighter
        fighter.hp = 1  # Only 1 HP - poison would be lethal
        owner.get_component_optional = Mock(return_value=fighter)
        
        effect = PoisonEffect(owner=owner, damage_per_tick=5)  # Would kill
        effect.apply()
        
        with patch('logger_config.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            effect.process_turn_start(state_manager=None)
            
            # Should have logged a CLAMP warning
            mock_logger.error.assert_called()
            error_msg = mock_logger.error.call_args[0][0]
            assert 'POISON_LETHAL_CLAMP' in error_msg
            
            # Should NOT have called take_damage (clamped to 0 damage at 1 HP)
            fighter.take_damage.assert_not_called()


class TestPoisonMessages:
    """Tests for poison effect messages."""
    
    def test_apply_message(self):
        """apply() should return poison message."""
        owner = Mock()
        owner.name = "TestEntity"
        
        effect = PoisonEffect(owner=owner)
        results = effect.apply()
        
        assert len(results) == 1
        assert 'message' in results[0]
        msg_text = str(results[0]['message'])
        assert 'poison' in msg_text.lower()
    
    def test_remove_message(self):
        """remove() should return cure message."""
        owner = Mock()
        owner.name = "TestEntity"
        
        effect = PoisonEffect(owner=owner)
        effect.apply()
        results = effect.remove()
        
        assert len(results) == 1
        assert 'message' in results[0]
        msg_text = str(results[0]['message'])
        assert 'wears off' in msg_text.lower()
    
    def test_damage_tick_message(self):
        """Damage tick should include damage message."""
        owner = Mock()
        owner.name = "TestEntity"
        owner.poison_resistance_pct = 0
        
        fighter = Mock()
        fighter.take_damage = Mock(return_value=[])
        fighter.poison_resistance_pct = 0  # Set resistance on fighter
        fighter.hp = 20  # Enough HP for non-lethal damage
        owner.get_component_optional = Mock(return_value=fighter)
        
        effect = PoisonEffect(owner=owner, damage_per_tick=2)
        effect.apply()
        
        with patch('logger_config.get_logger'):
            results = effect.process_turn_start(state_manager=None)
        
        # First result should be the damage message
        assert len(results) >= 1
        assert 'message' in results[0]
        msg_text = str(results[0]['message'])
        assert '2' in msg_text  # Damage amount
        assert 'poison' in msg_text.lower()


class TestPoisonRepr:
    """Tests for PoisonEffect string representation."""
    
    def test_repr_format(self):
        """__repr__ should show duration and damage."""
        owner = Mock()
        owner.name = "TestEntity"
        
        effect = PoisonEffect(owner=owner, duration=5, damage_per_tick=2)
        
        repr_str = repr(effect)
        assert '5' in repr_str
        assert '2' in repr_str
        assert 'PoisonEffect' in repr_str

