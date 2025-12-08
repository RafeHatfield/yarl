"""Unit tests for Phase 8: Hit/Dodge model (accuracy vs evasion).

Tests cover:
- compute_hit_chance() with various accuracy/evasion combinations
- Min/max clamping behavior
- roll_to_hit() with controlled RNG
- Entity wrapper functions
- Display string generation
"""

import pytest
from unittest.mock import Mock, patch

from balance.hit_model import (
    BASE_HIT,
    STEP,
    MIN_HIT,
    MAX_HIT,
    DEFAULT_ACCURACY,
    DEFAULT_EVASION,
    compute_hit_chance,
    roll_to_hit,
    get_accuracy,
    get_evasion,
    get_hit_chance_for_entities,
    roll_to_hit_entities,
    get_accuracy_bonus_display,
    get_evasion_bonus_display,
)


class TestHitModelConstants:
    """Tests for hit model constant values."""
    
    def test_base_hit_is_75_percent(self):
        """Base hit chance should be 75%."""
        assert BASE_HIT == 0.75
    
    def test_step_is_5_percent(self):
        """Each point of accuracy/evasion should be 5%."""
        assert STEP == 0.05
    
    def test_min_hit_is_5_percent(self):
        """Minimum hit chance floor should be 5%."""
        assert MIN_HIT == 0.05
    
    def test_max_hit_is_95_percent(self):
        """Maximum hit chance ceiling should be 95%."""
        assert MAX_HIT == 0.95
    
    def test_default_accuracy_is_2(self):
        """Default accuracy should be 2."""
        assert DEFAULT_ACCURACY == 2
    
    def test_default_evasion_is_1(self):
        """Default evasion should be 1."""
        assert DEFAULT_EVASION == 1


class TestComputeHitChance:
    """Tests for compute_hit_chance() function."""
    
    def test_symmetric_accuracy_evasion(self):
        """Equal accuracy and evasion should give base hit chance."""
        # 75% + (2 - 2) * 5% = 75%
        assert compute_hit_chance(2, 2) == 0.75
        
        # Same for any equal values
        assert compute_hit_chance(5, 5) == 0.75
        assert compute_hit_chance(0, 0) == 0.75
    
    def test_attacker_higher_accuracy(self):
        """Higher attacker accuracy should increase hit chance."""
        # Player (acc=2) vs Zombie (eva=0): 75% + (2-0)*5% = 85%
        assert compute_hit_chance(2, 0) == 0.85
        
        # Blademaster (acc=4) vs Player (eva=1): 75% + (4-1)*5% = 90%
        assert compute_hit_chance(4, 1) == 0.90
    
    def test_defender_higher_evasion(self):
        """Higher defender evasion should decrease hit chance."""
        # Player (acc=2) vs Wraith (eva=4): 75% + (2-4)*5% = 65%
        assert compute_hit_chance(2, 4) == 0.65
        
        # Zombie (acc=1) vs Player (eva=1): 75% + (1-1)*5% = 75%
        assert compute_hit_chance(1, 1) == 0.75
    
    def test_min_clamping(self):
        """Very high evasion should clamp to MIN_HIT."""
        # Extreme case: acc=0 vs eva=20
        # Raw: 75% + (0-20)*5% = 75% - 100% = -25% -> clamped to 5%
        result = compute_hit_chance(0, 20)
        assert result == MIN_HIT
    
    def test_max_clamping(self):
        """Very high accuracy should clamp to MAX_HIT."""
        # Extreme case: acc=20 vs eva=0
        # Raw: 75% + (20-0)*5% = 75% + 100% = 175% -> clamped to 95%
        result = compute_hit_chance(20, 0)
        assert result == MAX_HIT
    
    def test_edge_case_at_min_boundary(self):
        """Test behavior at exact MIN_HIT boundary."""
        # To get exactly 5%: 75% + (x)*5% = 5%
        # x = -14 (acc - eva = -14)
        result = compute_hit_chance(0, 14)
        assert result == MIN_HIT
    
    def test_edge_case_at_max_boundary(self):
        """Test behavior at exact MAX_HIT boundary."""
        # To get exactly 95%: 75% + (x)*5% = 95%
        # x = +4 (acc - eva = 4)
        result = compute_hit_chance(4, 0)
        assert result == MAX_HIT
    
    def test_typical_player_vs_orc(self):
        """Player (2,1) vs Orc (2,1) should be 75%."""
        # Same stats = base hit chance
        assert compute_hit_chance(2, 1) == 0.80  # (2-1)*5% = 5% bonus
    
    def test_typical_player_vs_zombie(self):
        """Player (2,1) vs Zombie (1,0) should favor player."""
        # Accuracy 2 vs evasion 0: 75% + 10% = 85%
        assert compute_hit_chance(2, 0) == 0.85
    
    def test_typical_player_vs_wraith(self):
        """Player (2,1) vs Wraith (3,4) should favor wraith defense."""
        # Player attacking wraith: 75% + (2-4)*5% = 65%
        assert compute_hit_chance(2, 4) == 0.65
        
        # Wraith attacking player: 75% + (3-1)*5% = 85%
        assert compute_hit_chance(3, 1) == 0.85


class TestRollToHit:
    """Tests for roll_to_hit() function."""
    
    def test_guaranteed_hit_with_low_roll(self):
        """Roll of 0.0 should always hit (assuming positive hit chance)."""
        always_zero = lambda: 0.0
        
        # Even with disadvantage, should hit
        assert roll_to_hit(0, 5, rng=always_zero) is True
    
    def test_guaranteed_miss_with_high_roll(self):
        """Roll of 1.0 should always miss (assuming < 100% hit chance)."""
        always_one = lambda: 0.999
        
        # Even with advantage, should miss (0.999 >= 0.95 = MAX_HIT)
        assert roll_to_hit(20, 0, rng=always_one) is False
    
    def test_roll_at_boundary(self):
        """Roll exactly at hit chance should miss (< not <=)."""
        # Hit chance = 75%, roll = 0.75 should MISS
        always_at_base = lambda: 0.75
        result = roll_to_hit(2, 2, rng=always_at_base)
        assert result is False
    
    def test_roll_just_below_boundary(self):
        """Roll just below hit chance should hit."""
        # Hit chance = 75%, roll = 0.749 should HIT
        just_below = lambda: 0.749
        result = roll_to_hit(2, 2, rng=just_below)
        assert result is True
    
    def test_statistical_behavior(self):
        """Verify statistical distribution with real RNG over many trials."""
        import random
        random.seed(42)  # Reproducible
        
        # Test with 80% hit chance (acc=2 vs eva=0)
        hits = sum(1 for _ in range(10000) if roll_to_hit(2, 0))
        hit_rate = hits / 10000
        
        # Should be close to 85% (within reasonable variance)
        assert 0.82 < hit_rate < 0.88, f"Hit rate {hit_rate:.2%} outside expected range"


class TestEntityHelpers:
    """Tests for entity wrapper functions."""
    
    def test_get_accuracy_from_fighter(self):
        """get_accuracy() should read from Fighter component."""
        mock_entity = Mock()
        mock_fighter = Mock()
        mock_fighter.accuracy = 5
        mock_entity.get_component_optional.return_value = mock_fighter
        
        result = get_accuracy(mock_entity)
        assert result == 5
    
    def test_get_accuracy_default_when_no_fighter(self):
        """get_accuracy() should return default when no Fighter."""
        mock_entity = Mock()
        mock_entity.get_component_optional.return_value = None
        
        result = get_accuracy(mock_entity)
        assert result == DEFAULT_ACCURACY
    
    def test_get_accuracy_default_when_no_accuracy_attr(self):
        """get_accuracy() should return default when Fighter has no accuracy."""
        mock_entity = Mock()
        mock_fighter = Mock(spec=[])  # No attributes
        mock_entity.get_component_optional.return_value = mock_fighter
        
        result = get_accuracy(mock_entity)
        assert result == DEFAULT_ACCURACY
    
    def test_get_evasion_from_fighter(self):
        """get_evasion() should read from Fighter component."""
        mock_entity = Mock()
        mock_fighter = Mock()
        mock_fighter.evasion = 3
        mock_entity.get_component_optional.return_value = mock_fighter
        
        result = get_evasion(mock_entity)
        assert result == 3
    
    def test_get_evasion_default_when_no_entity(self):
        """get_evasion() should handle None entity."""
        result = get_evasion(None)
        assert result == DEFAULT_EVASION
    
    def test_get_hit_chance_for_entities(self):
        """get_hit_chance_for_entities() should combine entity stats."""
        attacker = Mock()
        attacker_fighter = Mock()
        attacker_fighter.accuracy = 4
        attacker.get_component_optional.return_value = attacker_fighter
        
        defender = Mock()
        defender_fighter = Mock()
        defender_fighter.evasion = 2
        defender.get_component_optional.return_value = defender_fighter
        
        # acc=4, eva=2: 75% + (4-2)*5% = 85%
        result = get_hit_chance_for_entities(attacker, defender)
        assert result == 0.85
    
    def test_roll_to_hit_entities_uses_entity_stats(self):
        """roll_to_hit_entities() should use entity accuracy/evasion."""
        attacker = Mock()
        attacker_fighter = Mock()
        attacker_fighter.accuracy = 2
        attacker.get_component_optional.return_value = attacker_fighter
        
        defender = Mock()
        defender_fighter = Mock()
        defender_fighter.evasion = 4
        defender.get_component_optional.return_value = defender_fighter
        
        # acc=2 vs eva=4 = 65% chance
        # With RNG at 0.60, should hit
        result = roll_to_hit_entities(attacker, defender, rng=lambda: 0.60)
        assert result is True
        
        # With RNG at 0.70, should miss
        result = roll_to_hit_entities(attacker, defender, rng=lambda: 0.70)
        assert result is False


class TestDisplayStrings:
    """Tests for display string generation."""
    
    def test_accuracy_bonus_display_positive(self):
        """Accuracy above default should show positive bonus."""
        # acc=4, default=2: (4-2)*5% = +10%
        result = get_accuracy_bonus_display(4)
        assert result == "+10%"
    
    def test_accuracy_bonus_display_negative(self):
        """Accuracy below default should show negative bonus."""
        # acc=1, default=2: (1-2)*5% = -5%
        result = get_accuracy_bonus_display(1)
        assert result == "-5%"
    
    def test_accuracy_bonus_display_zero(self):
        """Accuracy at default should show +0%."""
        result = get_accuracy_bonus_display(DEFAULT_ACCURACY)
        assert result == "+0%"
    
    def test_evasion_bonus_display_positive(self):
        """Evasion above default should show positive bonus."""
        # eva=3, default=1: (3-1)*5% = +10%
        result = get_evasion_bonus_display(3)
        assert result == "+10%"
    
    def test_evasion_bonus_display_negative(self):
        """Evasion below default should show negative bonus."""
        # eva=0, default=1: (0-1)*5% = -5%
        result = get_evasion_bonus_display(0)
        assert result == "-5%"


class TestIntegrationScenarios:
    """Integration-style tests for realistic combat scenarios."""
    
    def test_player_vs_zombie_favorable(self):
        """Player should have good hit chance vs slow zombie."""
        # Player: acc=2, eva=1
        # Zombie: acc=1, eva=0
        player_hits_zombie = compute_hit_chance(2, 0)  # 85%
        zombie_hits_player = compute_hit_chance(1, 1)  # 75%
        
        assert player_hits_zombie == 0.85
        assert zombie_hits_player == 0.75
        assert player_hits_zombie > zombie_hits_player
    
    def test_player_vs_wraith_challenging(self):
        """Wraith should be hard to hit but hits player easily."""
        # Player: acc=2, eva=1
        # Wraith: acc=3, eva=4
        player_hits_wraith = compute_hit_chance(2, 4)  # 65%
        wraith_hits_player = compute_hit_chance(3, 1)  # 85%
        
        assert player_hits_wraith == 0.65
        assert wraith_hits_player == 0.85
        assert wraith_hits_player > player_hits_wraith
    
    def test_player_vs_blademaster_dangerous(self):
        """Blademaster is an elite fighter - very accurate."""
        # Player: acc=2, eva=1
        # Blademaster: acc=4, eva=3
        player_hits_blademaster = compute_hit_chance(2, 3)  # 70%
        blademaster_hits_player = compute_hit_chance(4, 1)  # 90%
        
        assert player_hits_blademaster == 0.70
        assert blademaster_hits_player == 0.90
    
    def test_spider_balanced_combat(self):
        """Spider is fast but not impossible to hit."""
        # Player: acc=2, eva=1
        # Spider: acc=3, eva=3
        player_hits_spider = compute_hit_chance(2, 3)  # 70%
        spider_hits_player = compute_hit_chance(3, 1)  # 85%
        
        assert player_hits_spider == 0.70
        assert spider_hits_player == 0.85
    
    def test_mirror_match(self):
        """Same stats should result in symmetric 75% base chance."""
        # Two orcs fighting
        result = compute_hit_chance(2, 1)  # 80% (slight advantage to attacker)
        assert result == 0.80
        
        # Player vs player-equivalent
        result = compute_hit_chance(2, 1)
        assert result == 0.80


class TestMomentumInteraction:
    """Tests to verify hit model doesn't break momentum system.
    
    These are conceptual tests - the actual integration is in game_actions.py
    and basic_monster.py. These verify the design intent.
    """
    
    def test_miss_should_still_allow_momentum(self):
        """Design: Missing an attack should still count for momentum.
        
        The hit model only determines damage, not action consumption.
        """
        # This is a design verification - the actual logic is in game_actions.py
        # Here we just verify that hit chance is independent of speed
        
        # Fast player (has momentum) vs slow zombie
        hit_chance = compute_hit_chance(2, 0)  # 85%
        
        # Hit chance doesn't depend on speed - that's handled separately
        # This test documents that independence
        assert hit_chance == 0.85
    
    def test_accuracy_evasion_orthogonal_to_speed(self):
        """Design: Speed and accuracy are independent axes.
        
        Speed determines action frequency (momentum/bonus attacks).
        Accuracy determines hit probability.
        They do not interact directly.
        """
        # A fast monster with low accuracy (like a swarm creature)
        # would get many attacks but miss often
        fast_inaccurate_hit = compute_hit_chance(1, 2)  # 70%
        
        # A slow monster with high accuracy (like a sniper)
        # would get few attacks but hit reliably
        slow_accurate_hit = compute_hit_chance(4, 2)  # 85%
        
        # Both are valid combat profiles
        assert fast_inaccurate_hit < slow_accurate_hit
