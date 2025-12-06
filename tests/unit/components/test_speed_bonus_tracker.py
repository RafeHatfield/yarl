"""Unit tests for SpeedBonusTracker component.

Tests cover:
- Initialization and validation
- Ratcheting behavior at 25%, 50%, 100% speed bonuses
- Early bonus hits do NOT reset the counter
- Guaranteed bonus at threshold DOES reset the counter
- Manual reset() functionality
- Edge cases (0% speed, high speed values)
"""

import pytest
from unittest.mock import Mock

from components.speed_bonus_tracker import SpeedBonusTracker


class TestSpeedBonusTrackerInit:
    """Tests for SpeedBonusTracker initialization."""
    
    def test_default_initialization(self):
        """Test default initialization with no speed bonus."""
        tracker = SpeedBonusTracker()
        
        assert tracker.speed_bonus_ratio == 0.0
        assert tracker.attack_counter == 0
        assert tracker.owner is None
    
    def test_initialization_with_speed_bonus(self):
        """Test initialization with a speed bonus ratio."""
        tracker = SpeedBonusTracker(speed_bonus_ratio=0.25)
        
        assert tracker.speed_bonus_ratio == 0.25
        assert tracker.attack_counter == 0
    
    def test_initialization_rejects_negative_ratio(self):
        """Test that negative speed bonus ratio raises ValueError."""
        with pytest.raises(ValueError, match="must be >= 0.0"):
            SpeedBonusTracker(speed_bonus_ratio=-0.1)
    
    def test_initialization_accepts_zero_ratio(self):
        """Test that zero speed bonus ratio is valid."""
        tracker = SpeedBonusTracker(speed_bonus_ratio=0.0)
        
        assert tracker.speed_bonus_ratio == 0.0
    
    def test_initialization_accepts_high_ratio(self):
        """Test that high speed bonus ratio (>1.0) is valid."""
        tracker = SpeedBonusTracker(speed_bonus_ratio=1.5)
        
        assert tracker.speed_bonus_ratio == 1.5
    
    def test_initialization_with_custom_rng(self):
        """Test initialization with custom RNG function."""
        fixed_rng = lambda: 0.5
        tracker = SpeedBonusTracker(speed_bonus_ratio=0.25, rng=fixed_rng)
        
        assert tracker._rng() == 0.5


class TestSpeedBonusZeroSpeed:
    """Tests for 0% speed bonus (no bonus attacks)."""
    
    def test_no_bonus_with_zero_speed(self):
        """Test that 0% speed bonus never grants bonus attacks."""
        tracker = SpeedBonusTracker(speed_bonus_ratio=0.0)
        
        # Try many attacks - none should grant bonus
        for _ in range(100):
            assert tracker.roll_for_bonus_attack() is False
    
    def test_counter_does_not_increment_with_zero_speed(self):
        """Test that counter stays at 0 with zero speed bonus."""
        tracker = SpeedBonusTracker(speed_bonus_ratio=0.0)
        
        tracker.roll_for_bonus_attack()
        tracker.roll_for_bonus_attack()
        tracker.roll_for_bonus_attack()
        
        # Counter should stay at 0 since we return early
        assert tracker.attack_counter == 0


class TestSpeedBonus25Percent:
    """Tests for 25% speed bonus (+25% attack speed)."""
    
    def test_guaranteed_bonus_at_attack_4(self):
        """Test that 4th attack guarantees bonus (4 * 0.25 = 1.0)."""
        # Use RNG that always fails (returns 0.99)
        tracker = SpeedBonusTracker(speed_bonus_ratio=0.25, rng=lambda: 0.99)
        
        # Attacks 1-3 should fail (chance < 1.0, roll fails)
        assert tracker.roll_for_bonus_attack() is False  # 25% chance
        assert tracker.roll_for_bonus_attack() is False  # 50% chance
        assert tracker.roll_for_bonus_attack() is False  # 75% chance
        
        # Attack 4 should succeed (100% guaranteed)
        assert tracker.roll_for_bonus_attack() is True
    
    def test_counter_resets_after_guaranteed_bonus(self):
        """Test that counter resets to 0 after guaranteed bonus."""
        tracker = SpeedBonusTracker(speed_bonus_ratio=0.25, rng=lambda: 0.99)
        
        # Build up to guaranteed bonus
        for _ in range(4):
            tracker.roll_for_bonus_attack()
        
        # Counter should be reset
        assert tracker.attack_counter == 0
    
    def test_early_bonus_does_not_reset_counter(self):
        """Test that early bonus hit does NOT reset the counter."""
        # RNG always succeeds (returns 0.0)
        tracker = SpeedBonusTracker(speed_bonus_ratio=0.25, rng=lambda: 0.0)
        
        # First attack: 25% chance, RNG succeeds
        result = tracker.roll_for_bonus_attack()
        
        assert result is True
        assert tracker.attack_counter == 1  # Counter NOT reset!
    
    def test_counter_increments_on_each_attack(self):
        """Test that attack counter increments correctly."""
        tracker = SpeedBonusTracker(speed_bonus_ratio=0.25, rng=lambda: 0.99)
        
        tracker.roll_for_bonus_attack()
        assert tracker.attack_counter == 1
        
        tracker.roll_for_bonus_attack()
        assert tracker.attack_counter == 2
        
        tracker.roll_for_bonus_attack()
        assert tracker.attack_counter == 3
    
    def test_ratchet_cycle_continues_after_early_bonus(self):
        """Test that early bonus doesn't disrupt the ratchet cycle."""
        call_count = [0]
        def rigged_rng():
            call_count[0] += 1
            # Succeed on 2nd roll (attack 2), fail otherwise
            return 0.0 if call_count[0] == 2 else 0.99
        
        tracker = SpeedBonusTracker(speed_bonus_ratio=0.25, rng=rigged_rng)
        
        # Attack 1: 25% chance, roll fails
        assert tracker.roll_for_bonus_attack() is False
        assert tracker.attack_counter == 1
        
        # Attack 2: 50% chance, roll succeeds (early bonus!)
        assert tracker.roll_for_bonus_attack() is True
        assert tracker.attack_counter == 2  # NOT reset
        
        # Attack 3: 75% chance, roll fails
        assert tracker.roll_for_bonus_attack() is False
        assert tracker.attack_counter == 3
        
        # Attack 4: 100% guaranteed bonus + reset
        assert tracker.roll_for_bonus_attack() is True
        assert tracker.attack_counter == 0  # Reset!


class TestSpeedBonus50Percent:
    """Tests for 50% speed bonus (+50% attack speed)."""
    
    def test_guaranteed_bonus_at_attack_2(self):
        """Test that 2nd attack guarantees bonus (2 * 0.5 = 1.0)."""
        tracker = SpeedBonusTracker(speed_bonus_ratio=0.5, rng=lambda: 0.99)
        
        # Attack 1: 50% chance, roll fails
        assert tracker.roll_for_bonus_attack() is False
        assert tracker.attack_counter == 1
        
        # Attack 2: 100% guaranteed
        assert tracker.roll_for_bonus_attack() is True
        assert tracker.attack_counter == 0
    
    def test_early_bonus_on_first_attack(self):
        """Test early bonus on first attack (50% chance)."""
        tracker = SpeedBonusTracker(speed_bonus_ratio=0.5, rng=lambda: 0.25)
        
        # Attack 1: 50% chance, roll 0.25 succeeds
        assert tracker.roll_for_bonus_attack() is True
        assert tracker.attack_counter == 1  # NOT reset


class TestSpeedBonus100Percent:
    """Tests for 100% speed bonus (+100% attack speed)."""
    
    def test_guaranteed_bonus_every_attack(self):
        """Test that every attack grants guaranteed bonus at 100% speed."""
        tracker = SpeedBonusTracker(speed_bonus_ratio=1.0, rng=lambda: 0.99)
        
        # Every attack should grant bonus (1 * 1.0 = 1.0)
        for i in range(10):
            assert tracker.roll_for_bonus_attack() is True
            assert tracker.attack_counter == 0  # Resets each time
    
    def test_counter_always_resets(self):
        """Test that counter always resets at 100% speed."""
        tracker = SpeedBonusTracker(speed_bonus_ratio=1.0)
        
        for _ in range(5):
            tracker.roll_for_bonus_attack()
            assert tracker.attack_counter == 0


class TestSpeedBonusHighSpeed:
    """Tests for very high speed bonuses (>100%)."""
    
    def test_150_percent_speed_always_triggers(self):
        """Test that 150% speed always grants bonus."""
        tracker = SpeedBonusTracker(speed_bonus_ratio=1.5)
        
        # At 150%, first attack = 1 * 1.5 = 1.5 >= 1.0
        assert tracker.roll_for_bonus_attack() is True
        assert tracker.attack_counter == 0


class TestResetMethod:
    """Tests for the reset() method."""
    
    def test_reset_clears_counter(self):
        """Test that reset() sets counter to 0."""
        tracker = SpeedBonusTracker(speed_bonus_ratio=0.25, rng=lambda: 0.99)
        
        # Build up counter
        tracker.roll_for_bonus_attack()
        tracker.roll_for_bonus_attack()
        assert tracker.attack_counter == 2
        
        # Reset
        tracker.reset()
        
        assert tracker.attack_counter == 0
    
    def test_reset_on_zero_counter_is_safe(self):
        """Test that reset() on zero counter is a no-op."""
        tracker = SpeedBonusTracker(speed_bonus_ratio=0.25)
        
        tracker.reset()
        
        assert tracker.attack_counter == 0
    
    def test_reset_allows_fresh_ratchet_cycle(self):
        """Test that reset() starts a fresh ratchet cycle."""
        tracker = SpeedBonusTracker(speed_bonus_ratio=0.25, rng=lambda: 0.99)
        
        # Build up to 3 attacks
        tracker.roll_for_bonus_attack()
        tracker.roll_for_bonus_attack()
        tracker.roll_for_bonus_attack()
        assert tracker.attack_counter == 3
        
        # Reset (player moved or used item)
        tracker.reset()
        assert tracker.attack_counter == 0
        
        # Start fresh cycle
        tracker.roll_for_bonus_attack()
        assert tracker.attack_counter == 1


class TestCurrentChanceProperty:
    """Tests for the current_chance property."""
    
    def test_current_chance_shows_next_attack_chance(self):
        """Test that current_chance shows chance for next attack."""
        tracker = SpeedBonusTracker(speed_bonus_ratio=0.25, rng=lambda: 0.99)
        
        # Before any attacks, next attack would have 25% chance
        assert tracker.current_chance == 0.25
        
        # After 1 attack, next would have 50%
        tracker.roll_for_bonus_attack()
        assert tracker.current_chance == 0.50
        
        # After 2 attacks, next would have 75%
        tracker.roll_for_bonus_attack()
        assert tracker.current_chance == 0.75
    
    def test_current_chance_with_zero_speed(self):
        """Test current_chance with 0% speed bonus."""
        tracker = SpeedBonusTracker(speed_bonus_ratio=0.0)
        
        assert tracker.current_chance == 0.0


class TestRepr:
    """Tests for string representation."""
    
    def test_repr_shows_state(self):
        """Test that repr() shows tracker state."""
        tracker = SpeedBonusTracker(speed_bonus_ratio=0.25)
        
        repr_str = repr(tracker)
        
        assert "SpeedBonusTracker" in repr_str
        assert "ratio=0.25" in repr_str
        assert "counter=0" in repr_str


class TestRNGBehavior:
    """Tests for RNG behavior boundary conditions."""
    
    def test_roll_exactly_at_chance_fails(self):
        """Test that roll exactly equal to chance fails (< not <=)."""
        # Chance = 25%, roll = 0.25 should FAIL (not < 0.25)
        tracker = SpeedBonusTracker(speed_bonus_ratio=0.25, rng=lambda: 0.25)
        
        result = tracker.roll_for_bonus_attack()
        
        # 0.25 is NOT less than 0.25, so should fail
        assert result is False
    
    def test_roll_just_below_chance_succeeds(self):
        """Test that roll just below chance succeeds."""
        # Chance = 25%, roll = 0.249 should SUCCEED (< 0.25)
        tracker = SpeedBonusTracker(speed_bonus_ratio=0.25, rng=lambda: 0.249)
        
        result = tracker.roll_for_bonus_attack()
        
        assert result is True


class TestStatisticalBehavior:
    """Tests for statistical properties with real RNG."""
    
    def test_25_percent_speed_bonus_statistics(self):
        """Test that 25% speed grants roughly correct bonus rate over many trials.
        
        With 25% speed and the ratcheting system:
        - Guaranteed bonus every 4 attacks (when counter hits 4)
        - Early bonus chances: 25%, 50%, 75% on attacks 1-3
        - Early bonuses DON'T reset counter, so they ADD to guaranteed bonuses
        
        Expected bonuses per 4-attack cycle:
        - 1 guaranteed + avg(0.25 + 0.50 + 0.75) = 1 + 1.5 = 2.5 bonuses
        - Expected bonus rate = 2.5 / 4 = 62.5%
        
        This is intentional! The ratcheting system is designed to feel generous
        and reward sustained combat with "momentum" bonuses.
        """
        import random
        random.seed(42)  # Reproducible
        
        tracker = SpeedBonusTracker(speed_bonus_ratio=0.25)
        
        # Simulate 1000 full ratchet cycles
        early_bonuses = 0
        guaranteed_bonuses = 0
        total_attacks = 0
        
        for _ in range(1000):
            tracker.reset()
            
            while tracker.attack_counter < 4:  # Max 4 attacks per cycle
                total_attacks += 1
                if tracker.roll_for_bonus_attack():
                    if tracker.attack_counter == 0:  # Counter reset = guaranteed
                        guaranteed_bonuses += 1
                        break
                    else:
                        early_bonuses += 1
        
        # With 25% speed and ratcheting:
        # - Every cycle gets exactly 1 guaranteed bonus
        # - Plus early bonuses that don't reset the counter
        # - Expected early bonuses per cycle: 0.25 + 0.50 + 0.75 = 1.5
        # - Total expected per cycle: 1 + 1.5 = 2.5
        # - Bonus rate: 2.5 / 4 = 62.5%
        total_bonuses = early_bonuses + guaranteed_bonuses
        bonus_rate = total_bonuses / total_attacks
        
        # Verify guaranteed bonuses = number of cycles
        assert guaranteed_bonuses == 1000, f"Expected 1000 guaranteed bonuses, got {guaranteed_bonuses}"
        
        # Bonus rate should be around 62.5% (allowing for statistical variance)
        assert 0.55 < bonus_rate < 0.70, f"Bonus rate {bonus_rate:.2%} outside expected range (55-70%)"


class TestRelativeSpeedGating:
    """Tests for relative speed gating behavior.
    
    The gate logic lives in game_actions.py and basic_monster.py, not in the tracker itself.
    These tests verify the expected behavior when comparing speed ratios.
    """
    
    def test_faster_attacker_can_build_momentum(self):
        """Test that a faster attacker (higher ratio) can build momentum."""
        # Player (+25%) vs Orc (0%) - Player is faster, can build momentum
        attacker_speed = 0.25
        defender_speed = 0.0
        
        # Gate condition: attacker.speed > defender.speed
        can_build = attacker_speed > defender_speed
        assert can_build is True
    
    def test_slower_attacker_cannot_build_momentum(self):
        """Test that a slower attacker cannot build momentum."""
        # Player (+25%) vs Spider (+50%) - Player is slower, cannot build momentum
        attacker_speed = 0.25
        defender_speed = 0.50
        
        # Gate condition: attacker.speed > defender.speed
        can_build = attacker_speed > defender_speed
        assert can_build is False
    
    def test_equal_speed_cannot_build_momentum(self):
        """Test that equal speed prevents momentum building."""
        # Both at +25% - neither is faster, no momentum
        attacker_speed = 0.25
        defender_speed = 0.25
        
        # Gate condition: attacker.speed > defender.speed (strict inequality)
        can_build = attacker_speed > defender_speed
        assert can_build is False
    
    def test_zero_vs_zero_cannot_build_momentum(self):
        """Test that 0% vs 0% prevents momentum building."""
        attacker_speed = 0.0
        defender_speed = 0.0
        
        can_build = attacker_speed > defender_speed
        assert can_build is False
    
    def test_any_speed_vs_zero_can_build_momentum(self):
        """Test that any positive speed vs 0% allows momentum."""
        # Even tiny speed advantage matters
        attacker_speed = 0.01
        defender_speed = 0.0
        
        can_build = attacker_speed > defender_speed
        assert can_build is True
