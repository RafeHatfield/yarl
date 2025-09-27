"""
Unit tests for random_utils.py

Tests the random utility functions including:
- Weighted random selection from lists and dictionaries
- Dungeon level-based value lookup with progression tables
- Edge cases and boundary conditions
"""

import pytest
from unittest.mock import patch

from random_utils import random_choice_index, random_choice_from_dict, from_dungeon_level


class TestRandomChoiceIndex:
    """Test random_choice_index function for weighted selection."""

    @patch('random_utils.randint')
    def test_random_choice_index_first_choice(self, mock_randint):
        """Test selecting the first choice."""
        mock_randint.return_value = 1
        chances = [50, 30, 20]
        
        result = random_choice_index(chances)
        
        assert result == 0
        mock_randint.assert_called_once_with(1, 100)

    @patch('random_utils.randint')
    def test_random_choice_index_middle_choice(self, mock_randint):
        """Test selecting a middle choice."""
        mock_randint.return_value = 75
        chances = [50, 30, 20]
        
        result = random_choice_index(chances)
        
        assert result == 1

    @patch('random_utils.randint')
    def test_random_choice_index_last_choice(self, mock_randint):
        """Test selecting the last choice."""
        mock_randint.return_value = 100
        chances = [50, 30, 20]
        
        result = random_choice_index(chances)
        
        assert result == 2

    @patch('random_utils.randint')
    def test_random_choice_index_boundary_values(self, mock_randint):
        """Test boundary values for selection."""
        chances = [25, 25, 50]
        
        # Test exact boundary at 25
        mock_randint.return_value = 25
        assert random_choice_index(chances) == 0
        
        # Test exact boundary at 50
        mock_randint.return_value = 50
        assert random_choice_index(chances) == 1
        
        # Test exact boundary at 100
        mock_randint.return_value = 100
        assert random_choice_index(chances) == 2

    @patch('random_utils.randint')
    def test_random_choice_index_single_choice(self, mock_randint):
        """Test with only one choice."""
        mock_randint.return_value = 1
        chances = [100]
        
        result = random_choice_index(chances)
        
        assert result == 0

    @patch('random_utils.randint')
    def test_random_choice_index_zero_weight(self, mock_randint):
        """Test with zero weights in the list."""
        mock_randint.return_value = 30
        chances = [0, 50, 0, 30, 0]
        
        result = random_choice_index(chances)
        
        # With running sum: 0, 50, 50, 80, 80
        # randint(30) <= 50, so should select index 1
        assert result == 1

    @patch('random_utils.randint')
    def test_random_choice_index_uneven_weights(self, mock_randint):
        """Test with uneven weight distribution."""
        chances = [1, 99]
        
        # Should select first option
        mock_randint.return_value = 1
        assert random_choice_index(chances) == 0
        
        # Should select second option
        mock_randint.return_value = 2
        assert random_choice_index(chances) == 1

    def test_random_choice_index_empty_list(self):
        """Test with empty chances list."""
        chances = []
        
        # Should not crash, but behavior is undefined
        # This tests the function's robustness
        try:
            result = random_choice_index(chances)
            # If it doesn't crash, result should be reasonable
            assert isinstance(result, int)
        except (IndexError, ValueError):
            # These exceptions are acceptable for edge case
            pass


class TestRandomChoiceFromDict:
    """Test random_choice_from_dict function."""

    @patch('random_utils.random_choice_index')
    def test_random_choice_from_dict_basic(self, mock_choice_index):
        """Test basic dictionary choice selection."""
        mock_choice_index.return_value = 1
        choice_dict = {'orc': 80, 'troll': 20}
        
        result = random_choice_from_dict(choice_dict)
        
        assert result == 'troll'
        mock_choice_index.assert_called_once_with([80, 20])

    @patch('random_utils.random_choice_index')
    def test_random_choice_from_dict_single_item(self, mock_choice_index):
        """Test with single item dictionary."""
        mock_choice_index.return_value = 0
        choice_dict = {'healing_potion': 100}
        
        result = random_choice_from_dict(choice_dict)
        
        assert result == 'healing_potion'

    @patch('random_utils.random_choice_index')
    def test_random_choice_from_dict_multiple_items(self, mock_choice_index):
        """Test with multiple items."""
        mock_choice_index.return_value = 2
        choice_dict = {'orc': 50, 'troll': 30, 'dragon': 20}
        
        result = random_choice_from_dict(choice_dict)
        
        assert result == 'dragon'
        mock_choice_index.assert_called_once_with([50, 30, 20])

    @patch('random_utils.random_choice_index')
    def test_random_choice_from_dict_zero_weights(self, mock_choice_index):
        """Test with zero weights in dictionary."""
        mock_choice_index.return_value = 1
        choice_dict = {'unavailable': 0, 'available': 100, 'also_unavailable': 0}
        
        result = random_choice_from_dict(choice_dict)
        
        assert result == 'available'

    def test_random_choice_from_dict_empty_dict(self):
        """Test with empty dictionary."""
        choice_dict = {}
        
        # Should raise ValueError due to empty range in randint(1, 1)
        with pytest.raises(ValueError, match="empty range"):
            random_choice_from_dict(choice_dict)

    @patch('random_utils.random_choice_index')
    def test_random_choice_from_dict_preserves_key_order(self, mock_choice_index):
        """Test that key-value relationships are preserved."""
        choice_dict = {'first': 10, 'second': 20, 'third': 30}
        
        # Test each possible index
        for i, expected_key in enumerate(['first', 'second', 'third']):
            mock_choice_index.return_value = i
            result = random_choice_from_dict(choice_dict)
            assert result == expected_key


class TestFromDungeonLevel:
    """Test from_dungeon_level function for level-based progression."""

    def test_from_dungeon_level_basic_progression(self):
        """Test basic level progression."""
        table = [[2, 1], [3, 4], [5, 6]]
        
        # Level 1: should get 2
        assert from_dungeon_level(table, 1) == 2
        
        # Level 4: should get 3
        assert from_dungeon_level(table, 4) == 3
        
        # Level 6: should get 5
        assert from_dungeon_level(table, 6) == 5

    def test_from_dungeon_level_exact_thresholds(self):
        """Test exact threshold values."""
        table = [[10, 1], [20, 5], [30, 10]]
        
        # Exact threshold matches
        assert from_dungeon_level(table, 1) == 10
        assert from_dungeon_level(table, 5) == 20
        assert from_dungeon_level(table, 10) == 30

    def test_from_dungeon_level_between_thresholds(self):
        """Test levels between thresholds."""
        table = [[1, 1], [2, 5], [3, 10]]
        
        # Between thresholds should use previous value
        assert from_dungeon_level(table, 3) == 1  # Between 1 and 5
        assert from_dungeon_level(table, 7) == 2  # Between 5 and 10
        assert from_dungeon_level(table, 15) == 3  # Above 10

    def test_from_dungeon_level_high_levels(self):
        """Test very high dungeon levels."""
        table = [[5, 1], [10, 5], [20, 10]]
        
        # High levels should use highest available value
        assert from_dungeon_level(table, 50) == 20
        assert from_dungeon_level(table, 100) == 20

    def test_from_dungeon_level_below_minimum(self):
        """Test levels below minimum threshold."""
        table = [[10, 5], [20, 10]]
        
        # Below minimum should return 0
        assert from_dungeon_level(table, 1) == 0
        assert from_dungeon_level(table, 4) == 0

    def test_from_dungeon_level_single_entry(self):
        """Test with single table entry."""
        table = [[100, 1]]
        
        assert from_dungeon_level(table, 1) == 100
        assert from_dungeon_level(table, 10) == 100

    def test_from_dungeon_level_empty_table(self):
        """Test with empty table."""
        table = []
        
        assert from_dungeon_level(table, 1) == 0
        assert from_dungeon_level(table, 10) == 0

    def test_from_dungeon_level_zero_level(self):
        """Test with zero dungeon level."""
        table = [[10, 1], [20, 5]]
        
        assert from_dungeon_level(table, 0) == 0

    def test_from_dungeon_level_negative_level(self):
        """Test with negative dungeon level."""
        table = [[10, 1], [20, 5]]
        
        assert from_dungeon_level(table, -1) == 0

    def test_from_dungeon_level_monster_progression(self):
        """Test realistic monster progression table."""
        # Troll chances: 15% at level 3, 30% at level 5, 60% at level 7
        table = [[15, 3], [30, 5], [60, 7]]
        
        assert from_dungeon_level(table, 1) == 0   # No trolls early
        assert from_dungeon_level(table, 2) == 0   # No trolls early
        assert from_dungeon_level(table, 3) == 15  # 15% at level 3
        assert from_dungeon_level(table, 4) == 15  # Still 15%
        assert from_dungeon_level(table, 5) == 30  # 30% at level 5
        assert from_dungeon_level(table, 6) == 30  # Still 30%
        assert from_dungeon_level(table, 7) == 60  # 60% at level 7
        assert from_dungeon_level(table, 10) == 60 # Still 60%

    def test_from_dungeon_level_spawn_rate_progression(self):
        """Test realistic spawn rate progression table."""
        # Max monsters: 2 at level 1, 3 at level 4, 5 at level 6
        table = [[2, 1], [3, 4], [5, 6]]
        
        assert from_dungeon_level(table, 1) == 2
        assert from_dungeon_level(table, 3) == 2
        assert from_dungeon_level(table, 4) == 3
        assert from_dungeon_level(table, 5) == 3
        assert from_dungeon_level(table, 6) == 5
        assert from_dungeon_level(table, 10) == 5

    def test_from_dungeon_level_item_unlock_progression(self):
        """Test realistic item unlock progression."""
        # Lightning scrolls: 25% chance starting at level 4
        table = [[25, 4]]
        
        assert from_dungeon_level(table, 1) == 0   # Not available
        assert from_dungeon_level(table, 3) == 0   # Not available
        assert from_dungeon_level(table, 4) == 25  # Available at 25%
        assert from_dungeon_level(table, 10) == 25 # Still 25%


class TestRandomUtilsIntegration:
    """Integration tests for random_utils functions working together."""

    def test_monster_selection_integration(self):
        """Test realistic monster selection scenario."""
        # Simulate level 5 monster selection
        monster_chances = {
            'orc': 80,
            'troll': from_dungeon_level([[15, 3], [30, 5], [60, 7]], 5)
        }
        
        # At level 5, troll chance should be 30
        assert monster_chances['troll'] == 30
        
        # Test that random selection works with these chances
        with patch('random_utils.randint') as mock_randint:
            # Select orc (80 out of 110 total weight)
            mock_randint.return_value = 50
            result = random_choice_from_dict(monster_chances)
            assert result == 'orc'
            
            # Select troll (last 30 out of 110 total weight)
            mock_randint.return_value = 100
            result = random_choice_from_dict(monster_chances)
            assert result == 'troll'

    def test_item_selection_integration(self):
        """Test realistic item selection scenario."""
        # Simulate level 6 item selection
        item_chances = {
            'healing_potion': 35,
            'lightning_scroll': from_dungeon_level([[25, 4]], 6),
            'fireball_scroll': from_dungeon_level([[25, 6]], 6),
            'confusion_scroll': from_dungeon_level([[10, 2]], 6)
        }
        
        # At level 6, all items should be available
        assert item_chances['lightning_scroll'] == 25
        assert item_chances['fireball_scroll'] == 25
        assert item_chances['confusion_scroll'] == 10
        
        # Total weight: 35 + 25 + 25 + 10 = 95
        with patch('random_utils.randint') as mock_randint:
            mock_randint.return_value = 95  # Last item
            result = random_choice_from_dict(item_chances)
            assert result == 'confusion_scroll'

    def test_progression_consistency(self):
        """Test that progression tables are consistent and logical."""
        # Monster spawn rates should increase
        spawn_table = [[2, 1], [3, 4], [5, 6]]
        
        prev_value = 0
        for level in range(1, 11):
            current_value = from_dungeon_level(spawn_table, level)
            assert current_value >= prev_value  # Should never decrease
            prev_value = current_value

    def test_early_game_balance(self):
        """Test that early game (levels 1-3) has appropriate balance."""
        # Level 1-3 should have limited monster types and items
        for level in [1, 2, 3]:
            troll_chance = from_dungeon_level([[15, 3], [30, 5], [60, 7]], level)
            lightning_chance = from_dungeon_level([[25, 4]], level)
            fireball_chance = from_dungeon_level([[25, 6]], level)
            
            if level < 3:
                assert troll_chance == 0  # No trolls before level 3
            if level < 4:
                assert lightning_chance == 0  # No lightning before level 4
            if level < 6:
                assert fireball_chance == 0  # No fireball before level 6
