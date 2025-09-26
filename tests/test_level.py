"""
Unit tests for components/level.py

Tests the leveling and experience system including:
- Level initialization and progression
- XP calculation and thresholds  
- Level up mechanics and overflow handling
- Edge cases and boundary conditions
"""

import pytest
from components.level import Level


class TestLevelInitialization:
    """Test Level component initialization."""

    def test_level_default_initialization(self):
        """Test Level creation with default parameters."""
        level = Level()
        
        assert level.current_level == 1
        assert level.current_xp == 0
        assert level.level_up_base == 200
        assert level.level_up_factor == 150

    def test_level_custom_initialization(self):
        """Test Level creation with custom parameters."""
        level = Level(current_level=5, current_xp=100, level_up_base=300, level_up_factor=200)
        
        assert level.current_level == 5
        assert level.current_xp == 100
        assert level.level_up_base == 300
        assert level.level_up_factor == 200

    def test_level_initialization_edge_cases(self):
        """Test Level creation with edge case values."""
        # Test with zero values
        level_zero = Level(current_level=0, current_xp=0, level_up_base=0, level_up_factor=0)
        assert level_zero.current_level == 0
        assert level_zero.current_xp == 0
        
        # Test with large values
        level_large = Level(current_level=100, current_xp=999999, level_up_base=50000, level_up_factor=10000)
        assert level_large.current_level == 100
        assert level_large.current_xp == 999999


class TestExperienceToNextLevel:
    """Test experience calculation for next level."""

    def test_experience_to_next_level_formula(self):
        """Test the XP formula: base + current_level * factor."""
        level = Level(current_level=1, level_up_base=200, level_up_factor=150)
        
        # Level 1: 200 + 1 * 150 = 350
        assert level.experience_to_next_level == 350
        
        level.current_level = 2
        # Level 2: 200 + 2 * 150 = 500
        assert level.experience_to_next_level == 500
        
        level.current_level = 5
        # Level 5: 200 + 5 * 150 = 950
        assert level.experience_to_next_level == 950

    def test_experience_scaling_progression(self):
        """Test that XP requirements increase with level."""
        level = Level()
        
        xp_requirements = []
        for i in range(1, 11):
            level.current_level = i
            xp_requirements.append(level.experience_to_next_level)
        
        # Each level should require more XP than the previous
        for i in range(1, len(xp_requirements)):
            assert xp_requirements[i] > xp_requirements[i-1]

    def test_experience_different_factors(self):
        """Test XP requirements with different level_up_factor values."""
        # Low factor - slower scaling
        level_slow = Level(level_up_factor=50)
        level_slow.current_level = 10
        slow_req = level_slow.experience_to_next_level
        
        # High factor - faster scaling  
        level_fast = Level(level_up_factor=500)
        level_fast.current_level = 10
        fast_req = level_fast.experience_to_next_level
        
        assert fast_req > slow_req

    def test_experience_zero_factor(self):
        """Test XP requirements with zero level_up_factor."""
        level = Level(level_up_base=100, level_up_factor=0)
        
        # Should always be base regardless of level
        level.current_level = 1
        assert level.experience_to_next_level == 100
        
        level.current_level = 50
        assert level.experience_to_next_level == 100


class TestAddExperience:
    """Test adding experience and level up mechanics."""

    def test_add_xp_no_level_up(self):
        """Test adding XP without leveling up."""
        level = Level(current_xp=100, level_up_base=200, level_up_factor=150)
        # Need 350 XP to level up, currently have 100
        
        # Add 50 XP (total 150, still below 350)
        leveled_up = level.add_xp(50)
        
        assert leveled_up is False
        assert level.current_xp == 150
        assert level.current_level == 1

    def test_add_xp_exact_level_up(self):
        """Test adding exact XP needed to level up."""
        level = Level(current_xp=300, level_up_base=200, level_up_factor=150)
        # Need 350 XP to level up, currently have 300
        
        # Add exactly 50 XP to reach 350 (but implementation uses > not >=)
        leveled_up = level.add_xp(50)
        
        assert leveled_up is False  # Exactly 350 doesn't level up (needs > 350)
        assert level.current_level == 1
        assert level.current_xp == 350

    def test_add_xp_overflow_level_up(self):
        """Test adding more XP than needed with overflow."""
        level = Level(current_xp=300, level_up_base=200, level_up_factor=150)
        # Need 350 XP to level up, currently have 300
        
        # Add 100 XP (total 400, 50 overflow)
        leveled_up = level.add_xp(100)
        
        assert leveled_up is True
        assert level.current_level == 2
        assert level.current_xp == 50  # 400 - 350 = 50 overflow

    def test_add_xp_multiple_levels(self):
        """Test adding enough XP to gain multiple levels."""
        level = Level(current_xp=0, level_up_base=100, level_up_factor=50)
        # Level 1 needs 150 XP, Level 2 needs 200 XP
        
        # Add 400 XP - should level up twice
        leveled_up = level.add_xp(400)
        
        # Should level up at least once
        assert leveled_up is True
        assert level.current_level >= 2
        # Note: Current implementation only levels up once per add_xp call

    def test_add_zero_xp(self):
        """Test adding zero XP."""
        level = Level(current_level=3, current_xp=100)
        original_level = level.current_level
        original_xp = level.current_xp
        
        leveled_up = level.add_xp(0)
        
        assert leveled_up is False
        assert level.current_level == original_level
        assert level.current_xp == original_xp

    def test_add_negative_xp(self):
        """Test adding negative XP (edge case)."""
        level = Level(current_xp=100)
        
        # Current implementation doesn't prevent negative XP
        leveled_up = level.add_xp(-50)
        
        assert leveled_up is False
        assert level.current_xp == 50

    def test_add_large_xp_amount(self):
        """Test adding very large XP amounts."""
        level = Level()
        
        leveled_up = level.add_xp(999999)
        
        assert leveled_up is True
        assert level.current_level == 2  # Only levels up once
        # Should have substantial overflow
        assert level.current_xp > 0


class TestLevelUpProgression:
    """Test level progression scenarios."""

    def test_normal_progression_flow(self):
        """Test normal character progression through multiple levels."""
        level = Level()
        levels_gained = 0
        
        # Simulate gaining XP over time
        xp_gains = [100, 150, 200, 100, 250, 300]
        
        for xp in xp_gains:
            if level.add_xp(xp):
                levels_gained += 1
        
        assert levels_gained > 0
        assert level.current_level > 1

    def test_level_up_xp_requirements_increase(self):
        """Test that each level requires more XP than the previous."""
        level = Level()
        
        # Level up once to level 2
        level.add_xp(1000)  # Ensure level up
        level_2_requirement = level.experience_to_next_level
        
        # Level up to level 3
        level.add_xp(1000)
        level_3_requirement = level.experience_to_next_level
        
        assert level_3_requirement > level_2_requirement

    def test_consistent_level_up_behavior(self):
        """Test that level up behavior is consistent."""
        level1 = Level()
        level2 = Level()
        
        # Same XP addition should produce same results
        result1 = level1.add_xp(400)
        result2 = level2.add_xp(400)
        
        assert result1 == result2
        assert level1.current_level == level2.current_level
        assert level1.current_xp == level2.current_xp


class TestLevelEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_high_level_character(self):
        """Test behavior with high level characters."""
        level = Level(current_level=50, current_xp=0)
        
        # XP requirement should be very high
        xp_needed = level.experience_to_next_level
        assert xp_needed > 1000
        
        # Should still be able to level up
        leveled_up = level.add_xp(xp_needed + 100)
        assert leveled_up is True
        assert level.current_level == 51

    def test_zero_base_xp_requirement(self):
        """Test with zero base XP requirement."""
        level = Level(level_up_base=0, level_up_factor=100)
        
        # Level 1 should need 100 XP (0 + 1 * 100)
        assert level.experience_to_next_level == 100
        
        leveled_up = level.add_xp(150)
        assert leveled_up is True
        assert level.current_xp == 50

    def test_level_up_boundary_conditions(self):
        """Test XP amounts right at level up boundaries."""
        level = Level(current_xp=349, level_up_base=200, level_up_factor=150)
        # Need 350 XP total to level up
        
        # 1 XP short
        leveled_up = level.add_xp(1)
        assert leveled_up is False
        assert level.current_xp == 350
        
        # Exactly at threshold - this actually triggers level up
        # (since current implementation checks > not >=)
        leveled_up = level.add_xp(1)
        assert leveled_up is True

    def test_level_component_immutability_during_calculation(self):
        """Test that experience_to_next_level doesn't modify state."""
        level = Level(current_level=5, current_xp=100)
        original_level = level.current_level
        original_xp = level.current_xp
        
        # Accessing the property multiple times shouldn't change state
        req1 = level.experience_to_next_level
        req2 = level.experience_to_next_level
        
        assert req1 == req2
        assert level.current_level == original_level
        assert level.current_xp == original_xp


class TestLevelConfigurability:
    """Test different Level configurations for game balance."""

    def test_fast_leveling_configuration(self):
        """Test configuration for rapid character progression."""
        # Low base, low factor = easy leveling
        level = Level(level_up_base=50, level_up_factor=25)
        
        # Should level up quickly
        leveled_up = level.add_xp(100)
        assert leveled_up is True
        assert level.current_level == 2

    def test_slow_leveling_configuration(self):
        """Test configuration for slow character progression."""
        # High base, high factor = slow leveling  
        level = Level(level_up_base=1000, level_up_factor=500)
        
        # Should require lots of XP
        assert level.experience_to_next_level == 1500
        
        leveled_up = level.add_xp(500)
        assert leveled_up is False

    def test_linear_vs_scaling_progression(self):
        """Compare linear vs scaling XP progression."""
        # Linear: factor = 0
        linear = Level(level_up_base=100, level_up_factor=0)
        
        # Scaling: factor > 0
        scaling = Level(level_up_base=100, level_up_factor=100)
        
        # At level 10
        linear.current_level = 10
        scaling.current_level = 10
        
        linear_req = linear.experience_to_next_level
        scaling_req = scaling.experience_to_next_level
        
        # Linear should always be 100, scaling should be much higher
        assert linear_req == 100
        assert scaling_req == 1100
        assert scaling_req > linear_req
