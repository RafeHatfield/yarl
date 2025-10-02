"""Tests for dice rolling utilities."""

import pytest
from dice import parse_dice, roll_dice, get_dice_average, get_dice_min_max, dice_to_range_string


class TestParseDice:
    """Test dice notation parsing."""
    
    def test_simple_dice(self):
        """Test parsing simple dice notation."""
        assert parse_dice("1d4") == (1, 4, 0)
        assert parse_dice("1d6") == (1, 6, 0)
        assert parse_dice("1d8") == (1, 8, 0)
        assert parse_dice("1d10") == (1, 10, 0)
        assert parse_dice("1d12") == (1, 12, 0)
        assert parse_dice("1d20") == (1, 20, 0)
    
    def test_multiple_dice(self):
        """Test parsing multiple dice."""
        assert parse_dice("2d6") == (2, 6, 0)
        assert parse_dice("3d4") == (3, 4, 0)
        assert parse_dice("4d6") == (4, 6, 0)
    
    def test_dice_with_positive_modifier(self):
        """Test parsing dice with positive modifiers."""
        assert parse_dice("1d4+1") == (1, 4, 1)
        assert parse_dice("1d6+2") == (1, 6, 2)
        assert parse_dice("2d6+3") == (2, 6, 3)
    
    def test_dice_with_negative_modifier(self):
        """Test parsing dice with negative modifiers."""
        assert parse_dice("1d4-1") == (1, 4, -1)
        assert parse_dice("1d6-2") == (1, 6, -2)
    
    def test_dice_without_number(self):
        """Test that 'd6' defaults to '1d6'."""
        assert parse_dice("d6") == (1, 6, 0)
        assert parse_dice("d20") == (1, 20, 0)
    
    def test_case_insensitive(self):
        """Test that parsing is case-insensitive."""
        assert parse_dice("1D6") == (1, 6, 0)
        assert parse_dice("1D20+5") == (1, 20, 5)
    
    def test_whitespace_handling(self):
        """Test that whitespace is ignored."""
        assert parse_dice(" 1d6 ") == (1, 6, 0)
        assert parse_dice("  2d8+2  ") == (2, 8, 2)
    
    def test_invalid_format(self):
        """Test that invalid formats raise ValueError."""
        with pytest.raises(ValueError, match="Invalid dice notation"):
            parse_dice("invalid")
        with pytest.raises(ValueError, match="Invalid dice notation"):
            parse_dice("1+2")
        with pytest.raises(ValueError, match="Invalid dice notation"):
            parse_dice("d")
        with pytest.raises(ValueError, match="Invalid dice notation"):
            parse_dice("1d")
    
    def test_invalid_values(self):
        """Test that invalid values raise ValueError."""
        with pytest.raises(ValueError, match="Number of dice must be"):
            parse_dice("0d6")
        with pytest.raises(ValueError, match="Die size must be"):
            parse_dice("1d1")
        with pytest.raises(ValueError, match="Die size must be"):
            parse_dice("1d0")


class TestRollDice:
    """Test dice rolling."""
    
    def test_roll_in_range(self):
        """Test that rolls are within expected range."""
        for _ in range(100):
            roll = roll_dice("1d6")
            assert 1 <= roll <= 6
        
        for _ in range(100):
            roll = roll_dice("2d6")
            assert 2 <= roll <= 12
    
    def test_roll_with_modifier(self):
        """Test that modifiers are applied correctly."""
        for _ in range(100):
            roll = roll_dice("1d6+2")
            assert 3 <= roll <= 8
        
        for _ in range(100):
            roll = roll_dice("1d6-1")
            assert 0 <= roll <= 5
    
    def test_roll_distribution(self):
        """Test that rolls have reasonable distribution."""
        # Roll 1d6 many times, should see all numbers
        rolls = [roll_dice("1d6") for _ in range(1000)]
        
        # Should have seen all values 1-6
        assert min(rolls) == 1
        assert max(rolls) == 6
        
        # Average should be close to 3.5
        average = sum(rolls) / len(rolls)
        assert 3.0 < average < 4.0


class TestGetDiceAverage:
    """Test dice average calculation."""
    
    def test_simple_dice_average(self):
        """Test average for simple dice."""
        assert get_dice_average("1d4") == 2.5  # (1+4)/2
        assert get_dice_average("1d6") == 3.5  # (1+6)/2
        assert get_dice_average("1d8") == 4.5  # (1+8)/2
        assert get_dice_average("1d10") == 5.5
        assert get_dice_average("1d12") == 6.5
        assert get_dice_average("1d20") == 10.5
    
    def test_multiple_dice_average(self):
        """Test average for multiple dice."""
        assert get_dice_average("2d6") == 7.0  # 2 * 3.5
        assert get_dice_average("3d6") == 10.5  # 3 * 3.5
    
    def test_dice_with_modifier_average(self):
        """Test average with modifiers."""
        assert get_dice_average("1d6+2") == 5.5  # 3.5 + 2
        assert get_dice_average("2d6+3") == 10.0  # 7.0 + 3


class TestGetDiceMinMax:
    """Test min/max calculation."""
    
    def test_simple_dice_min_max(self):
        """Test min/max for simple dice."""
        assert get_dice_min_max("1d4") == (1, 4)
        assert get_dice_min_max("1d6") == (1, 6)
        assert get_dice_min_max("1d20") == (1, 20)
    
    def test_multiple_dice_min_max(self):
        """Test min/max for multiple dice."""
        assert get_dice_min_max("2d6") == (2, 12)
        assert get_dice_min_max("3d4") == (3, 12)
    
    def test_dice_with_modifier_min_max(self):
        """Test min/max with modifiers."""
        assert get_dice_min_max("1d6+2") == (3, 8)
        assert get_dice_min_max("2d6+3") == (5, 15)
        assert get_dice_min_max("1d6-1") == (0, 5)


class TestDiceToRangeString:
    """Test dice to range string conversion."""
    
    def test_simple_dice_to_range(self):
        """Test conversion for simple dice."""
        assert dice_to_range_string("1d4") == "1-4"
        assert dice_to_range_string("1d6") == "1-6"
        assert dice_to_range_string("1d8") == "1-8"
    
    def test_multiple_dice_to_range(self):
        """Test conversion for multiple dice."""
        assert dice_to_range_string("2d6") == "2-12"
        assert dice_to_range_string("3d4") == "3-12"
    
    def test_dice_with_modifier_to_range(self):
        """Test conversion with modifiers."""
        assert dice_to_range_string("1d6+2") == "3-8"
        assert dice_to_range_string("2d6+3") == "5-15"
    
    def test_fixed_value(self):
        """Test that fixed values show as single number."""
        # A die with min == max should show single number
        # This can happen with modifiers that make range equal
        # For now, our system won't create this, but test the display
        pass  # Not applicable with current system


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

