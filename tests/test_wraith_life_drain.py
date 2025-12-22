"""Unit tests for Phase 19 Wraith Life Drain mechanics.

Tests:
1. Life drain healing calculation (50% of damage dealt, ceil)
2. Life drain capping at missing HP (no overheal)
3. Life drain only applies when damage > 0
4. Ward Against Drain effect blocks life drain completely
5. Ward scroll application and removal
6. Metrics tracking for drain attempts, heals, and blocks
"""

import pytest
from unittest.mock import Mock, patch
from components.fighter import Fighter
from components.status_effects import WardAgainstDrainEffect
from entity import Entity
from components.component_registry import ComponentType
from item_functions import use_ward_scroll


class TestLifeDrainMechanics:
    """Test wraith life drain damage-to-heal conversion."""
    
    def setup_method(self):
        """Create test entities with Fighter components."""
        # Create wraith with life_drain_pct
        self.wraith = Entity(x=0, y=0, char='W', color=(255, 255, 255), name="Wraith", blocks=True)
        self.wraith.fighter = Fighter(hp=20, defense=4, power=3, xp=100)
        self.wraith.fighter.owner = self.wraith
        # Entity.__setattr__ auto-registers components, no manual add needed
        self.wraith.life_drain_pct = 0.50  # 50% life drain
        
        # Create player target
        self.player = Entity(x=1, y=0, char='@', color=(255, 255, 255), name="Player", blocks=True)
        self.player.fighter = Fighter(hp=50, defense=1, power=0, xp=0)
        self.player.fighter.owner = self.player
        # Entity.__setattr__ auto-registers components, no manual add needed
    
    def test_life_drain_heals_50_percent_of_damage(self):
        """Wraith should heal for ceil(50% of damage dealt)."""
        # Damage wraith to give it missing HP
        self.wraith.fighter.hp = 10  # 10/20 HP
        
        # Apply drain with damage_dealt = 10
        results = self.wraith.fighter._apply_life_drain_effects(self.player, damage_dealt=10)
        
        # Should heal for ceil(10 * 0.5) = 5 HP
        assert self.wraith.fighter.hp == 15
        assert len(results) > 0
        assert "wraith drains your life" in results[0]['message'].text.lower()
    
    def test_life_drain_uses_ceil(self):
        """Drain amount should use ceiling (round up)."""
        self.wraith.fighter.hp = 10  # 10/20 HP
        
        # Apply drain with damage_dealt = 7 (would be 3.5 without ceil)
        results = self.wraith.fighter._apply_life_drain_effects(self.player, damage_dealt=7)
        
        # Should heal for ceil(7 * 0.5) = 4 HP
        assert self.wraith.fighter.hp == 14
    
    def test_life_drain_caps_at_missing_hp(self):
        """Drain should not overheal (capped at missing HP)."""
        self.wraith.fighter.hp = 18  # 18/20 HP (only 2 missing)
        
        # Apply drain with damage_dealt = 10 (would heal 5 without cap)
        results = self.wraith.fighter._apply_life_drain_effects(self.player, damage_dealt=10)
        
        # Should heal only 2 HP (capped at missing HP)
        assert self.wraith.fighter.hp == 20
    
    def test_life_drain_does_not_apply_when_damage_zero(self):
        """No drain when damage_dealt <= 0."""
        self.wraith.fighter.hp = 10  # 10/20 HP
        
        results = self.wraith.fighter._apply_life_drain_effects(self.player, damage_dealt=0)
        
        # No healing should occur
        assert self.wraith.fighter.hp == 10
        assert len(results) == 0
    
    def test_life_drain_does_not_apply_when_full_hp(self):
        """No drain message when wraith at full HP (missing_hp = 0)."""
        self.wraith.fighter.hp = 20  # 20/20 HP (full)
        
        results = self.wraith.fighter._apply_life_drain_effects(self.player, damage_dealt=10)
        
        # HP stays the same (can't overheal)
        assert self.wraith.fighter.hp == 20
        # No drain message (drain_amount was 0)
        assert len(results) == 0
    
    def test_life_drain_does_not_apply_without_life_drain_pct(self):
        """Entities without life_drain_pct should not drain."""
        # Create normal orc without life_drain_pct
        orc = Entity(x=0, y=0, char='o', color=(255, 255, 255), name="Orc", blocks=True)
        orc.fighter = Fighter(hp=15, defense=0, power=0, xp=35)
        orc.fighter.owner = orc
        # Entity.__setattr__ auto-registers components
        # No life_drain_pct attribute
        
        results = orc.fighter._apply_life_drain_effects(self.player, damage_dealt=10)
        
        # No healing
        assert orc.fighter.hp == 15
        assert len(results) == 0


class TestWardAgainstDrain:
    """Test Ward Against Drain effect and scroll."""
    
    def setup_method(self):
        """Create test entities."""
        # Create wraith with life_drain_pct
        self.wraith = Entity(x=0, y=0, char='W', color=(255, 255, 255), name="Wraith", blocks=True)
        self.wraith.fighter = Fighter(hp=10, defense=4, power=3, xp=100)
        self.wraith.fighter.owner = self.wraith
        self.wraith.fighter.base_max_hp = 20  # Set max HP explicitly
        # Entity.__setattr__ auto-registers components
        self.wraith.life_drain_pct = 0.50
        
        # Create player with status effects
        self.player = Entity(x=1, y=0, char='@', color=(255, 255, 255), name="Player", blocks=True)
        self.player.fighter = Fighter(hp=50, defense=1, power=0, xp=0)
        self.player.fighter.owner = self.player
        # Entity.__setattr__ auto-registers components
        self.player.status_effects = self.player.get_status_effect_manager()
    
    def test_ward_blocks_life_drain_completely(self):
        """Ward Against Drain should block all life drain healing."""
        # Apply ward to player
        ward = WardAgainstDrainEffect(duration=10, owner=self.player)
        self.player.add_status_effect(ward)
        
        # Wraith attempts to drain
        results = self.wraith.fighter._apply_life_drain_effects(self.player, damage_dealt=10)
        
        # Wraith should NOT heal (still at 10/20 HP)
        assert self.wraith.fighter.hp == 10
        # Should have message about ward repelling drain
        assert len(results) > 0
        assert "ward repels" in results[0]['message'].text.lower()
    
    def test_ward_scroll_applies_effect(self):
        """Using ward scroll should apply WardAgainstDrainEffect."""
        results = use_ward_scroll(self.player, duration=10)
        
        # Should have ward effect
        assert self.player.status_effects.has_effect('ward_against_drain')
        
        # Effect should have correct duration
        ward = self.player.status_effects.get_effect('ward_against_drain')
        assert ward.duration == 10
        
        # Scroll consumed
        consumed = any(r.get('consumed') for r in results)
        assert consumed
    
    def test_ward_effect_applies_and_removes_messages(self):
        """Ward effect should emit messages on apply and remove."""
        ward = WardAgainstDrainEffect(duration=10, owner=self.player)
        
        # Apply
        apply_results = ward.apply()
        assert len(apply_results) > 0
        assert "pale ward" in apply_results[0]['message'].text.lower()
        
        # Remove
        remove_results = ward.remove()
        assert len(remove_results) > 0
        assert "fades" in remove_results[0]['message'].text.lower()
    
    def test_life_drain_works_without_ward(self):
        """Without ward, life drain should work normally."""
        # NO ward applied
        
        results = self.wraith.fighter._apply_life_drain_effects(self.player, damage_dealt=10)
        
        # Wraith should heal (10 + 5 = 15 HP)
        assert self.wraith.fighter.hp == 15
        assert len(results) > 0
        assert "wraith drains" in results[0]['message'].text.lower()


class TestLifeDrainMetrics:
    """Test metrics tracking for wraith life drain."""
    
    def setup_method(self):
        """Create test entities and mock metrics collector."""
        self.wraith = Entity(x=0, y=0, char='W', color=(255, 255, 255), name="Wraith", blocks=True)
        self.wraith.fighter = Fighter(hp=10, defense=4, power=3, xp=100)
        self.wraith.fighter.owner = self.wraith
        self.wraith.fighter.base_max_hp = 20
        # Entity.__setattr__ auto-registers components
        self.wraith.life_drain_pct = 0.50
        
        self.player = Entity(x=1, y=0, char='@', color=(255, 255, 255), name="Player", blocks=True)
        self.player.fighter = Fighter(hp=50, defense=1, power=0, xp=0)
        self.player.fighter.owner = self.player
        # Entity.__setattr__ auto-registers components
        self.player.status_effects = self.player.get_status_effect_manager()
    
    @patch('services.scenario_metrics.get_active_metrics_collector')
    def test_metrics_recorded_on_successful_drain(self, mock_get_collector):
        """Successful drain should record metrics."""
        mock_collector = Mock()
        mock_get_collector.return_value = mock_collector
        
        self.wraith.fighter._apply_life_drain_effects(self.player, damage_dealt=10)
        
        # Should record drain attempt with heal_amount=5, blocked=False
        mock_collector.record_life_drain_attempt.assert_called_once()
        call_args = mock_collector.record_life_drain_attempt.call_args
        assert call_args[1]['heal_amount'] == 5
        assert call_args[1]['blocked'] is False
    
    @patch('services.scenario_metrics.get_active_metrics_collector')
    def test_metrics_recorded_on_blocked_drain(self, mock_get_collector):
        """Blocked drain should record metrics with blocked=True."""
        mock_collector = Mock()
        mock_get_collector.return_value = mock_collector
        
        # Apply ward
        ward = WardAgainstDrainEffect(duration=10, owner=self.player)
        self.player.add_status_effect(ward)
        
        self.wraith.fighter._apply_life_drain_effects(self.player, damage_dealt=10)
        
        # Should record blocked attempt
        mock_collector.record_life_drain_attempt.assert_called_once()
        call_args = mock_collector.record_life_drain_attempt.call_args
        assert call_args[1]['heal_amount'] == 0
        assert call_args[1]['blocked'] is True


class TestLifeDrainIntegration:
    """Integration tests for life drain in combat flow."""
    
    def test_life_drain_in_attack_d20_flow(self):
        """Life drain should trigger after successful attack_d20 hit."""
        # This test verifies that _apply_life_drain_effects is called
        # in the attack_d20 flow after damage is applied
        
        wraith = Entity(x=0, y=0, char='W', color=(255, 255, 255), name="Wraith", blocks=True)
        wraith.fighter = Fighter(hp=10, defense=4, power=3, xp=100)
        wraith.fighter.owner = wraith
        wraith.fighter.base_max_hp = 20
        # Entity.__setattr__ auto-registers components
        wraith.life_drain_pct = 0.50
        
        player = Entity(x=1, y=0, char='@', color=(255, 255, 255), name="Player", blocks=True)
        player.fighter = Fighter(hp=50, defense=1, power=0, xp=0)
        player.fighter.owner = player
        # Entity.__setattr__ auto-registers components
        
        # Mock successful hit with guaranteed damage
        with patch('random.randint', return_value=20):  # Guaranteed crit
            results = wraith.fighter.attack_d20(player)
        
        # Wraith should have healed from life drain
        # (exact amount depends on damage roll, but should be > 10)
        assert wraith.fighter.hp > 10
        
        # Should have drain message in results
        drain_message = any('drain' in r.get('message', Mock(text='')).text.lower() for r in results)
        assert drain_message


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

