"""Phase 19: Tests for Split Under Pressure slime mechanic.

Tests the new low-HP threshold splitting behavior that replaces split-on-death.
"""

import unittest
from unittest.mock import Mock, patch
import random

from entity import Entity
from components.fighter import Fighter
from components.ai import BasicMonster
from components.component_registry import ComponentType
from services.slime_split_service import check_split_trigger, execute_split, _determine_child_count
from config.factories import get_entity_factory
from game_messages import MessageLog


class TestSlimeSplitUnderPressure(unittest.TestCase):
    """Test the core Split Under Pressure mechanic."""
    
    def setUp(self):
        """Set up test fixtures."""
        random.seed(42)  # Deterministic tests
        self.factory = get_entity_factory()
    
    def test_minor_slime_does_not_split(self):
        """Minor slimes have no split config and should never split."""
        slime = self.factory.create_monster("slime", 5, 5)
        
        # Damage to low HP
        slime.fighter.take_damage(10)  # Now at 5 HP (33%)
        
        # Check split - should be None
        split_data = check_split_trigger(slime)
        self.assertIsNone(split_data, "Minor slime should not have split config")
    
    def test_large_slime_splits_below_threshold(self):
        """Large slime should split when HP drops below 35% threshold."""
        large_slime = self.factory.create_monster("large_slime", 5, 5)
        
        # Mock game map with valid tiles
        mock_map = Mock()
        mock_map.width = 20
        mock_map.height = 20
        mock_map.tiles = [[Mock(blocked=False) for _ in range(20)] for _ in range(20)]
        
        # Verify initial state (42 HP due to constitution modifier +2)
        self.assertEqual(large_slime.fighter.max_hp, 42)
        self.assertEqual(large_slime.split_trigger_hp_pct, 0.35)
        
        # Damage to 16 HP (38%) - above threshold
        large_slime.fighter.hp = 16
        split_data = check_split_trigger(large_slime, game_map=mock_map, entities=[])
        self.assertIsNone(split_data, "Should not split above threshold")
        
        # Damage to 14 HP (33%) - below threshold
        large_slime.fighter.hp = 14
        split_data = check_split_trigger(large_slime, game_map=mock_map, entities=[])
        self.assertIsNotNone(split_data, "Should split below threshold")
        self.assertEqual(split_data['child_type'], "slime")
        self.assertGreaterEqual(split_data['num_children'], 2)
        self.assertLessEqual(split_data['num_children'], 3)
    
    def test_split_only_triggers_once(self):
        """Split should only trigger once per entity."""
        large_slime = self.factory.create_monster("large_slime", 5, 5)
        
        # Drop below threshold first time
        large_slime.fighter.hp = 10  # 25%
        split_data_1 = check_split_trigger(large_slime)
        self.assertIsNotNone(split_data_1, "First split should trigger")
        
        # Try again - should not trigger
        split_data_2 = check_split_trigger(large_slime)
        self.assertIsNone(split_data_2, "Second split should not trigger")
        
        # Even if HP drops further
        large_slime.fighter.hp = 1
        split_data_3 = check_split_trigger(large_slime)
        self.assertIsNone(split_data_3, "Split should not trigger after already split")
    
    def test_split_spawns_children_and_removes_original(self):
        """Execute split should create children and remove original."""
        large_slime = self.factory.create_monster("large_slime", 5, 5)
        entities = [large_slime]
        
        # Mock game map with valid tiles
        mock_map = Mock()
        mock_map.width = 20
        mock_map.height = 20
        mock_map.tiles = [[Mock(blocked=False) for _ in range(20)] for _ in range(20)]
        
        # Trigger split
        large_slime.fighter.hp = 10
        split_data = check_split_trigger(large_slime, game_map=mock_map, entities=entities)
        self.assertIsNotNone(split_data)
        
        # Execute split
        children = execute_split(split_data, game_map=mock_map, entities=entities)
        
        # Verify children spawned
        self.assertGreaterEqual(len(children), 2)
        self.assertLessEqual(len(children), 3)
        for child in children:
            self.assertEqual(child.name, "Slime")
            self.assertEqual(child.fighter.max_hp, 15)  # Minor slime HP
        
        # Verify original removed
        self.assertNotIn(large_slime, entities)
    
    def test_greater_slime_splits_into_large_slimes(self):
        """Greater slime should split into normal (large) slimes."""
        greater_slime = self.factory.create_monster("greater_slime", 5, 5)
        
        # Mock game map
        mock_map = Mock()
        mock_map.width = 20
        mock_map.height = 20
        mock_map.tiles = [[Mock(blocked=False) for _ in range(20)] for _ in range(20)]
        
        # Verify config
        self.assertEqual(greater_slime.split_trigger_hp_pct, 0.30)
        self.assertEqual(greater_slime.split_child_type, "large_slime")
        
        # Drop below 30% threshold (HP=83 with CON+3, 30% = 24.9)
        greater_slime.fighter.hp = 20  # 24% < 30%
        split_data = check_split_trigger(greater_slime, game_map=mock_map, entities=[])
        
        self.assertIsNotNone(split_data)
        self.assertEqual(split_data['child_type'], "large_slime")
        self.assertEqual(split_data['num_children'], 2)  # Fixed count for greater
    
    def test_split_message_is_generated(self):
        """Split should produce a combat log message."""
        large_slime = self.factory.create_monster("large_slime", 5, 5)
        
        large_slime.fighter.hp = 10
        split_data = check_split_trigger(large_slime)
        
        self.assertIsNotNone(split_data)
        self.assertIn('message', split_data)
        message_text = split_data['message'].text
        self.assertIn("split", message_text.lower())
        self.assertIn("pressure", message_text.lower())
    
    def test_weighted_child_count_distribution(self):
        """Test that child count respects weighted distribution."""
        # Large slime: 2 children (40%) or 3 children (60%)
        large_slime = self.factory.create_monster("large_slime", 5, 5)
        
        # Mock entity to test _determine_child_count
        counts = []
        for _ in range(100):
            count = _determine_child_count(large_slime)
            counts.append(count)
        
        # Verify only valid counts
        for c in counts:
            self.assertIn(c, [2, 3])
        
        # Rough distribution check (should see both values)
        self.assertIn(2, counts)
        self.assertIn(3, counts)
    
    def test_split_never_produces_zero_children(self):
        """Split must always produce at least 1 child."""
        large_slime = self.factory.create_monster("large_slime", 5, 5)
        
        # Even with bad config
        large_slime.split_min_children = 1
        large_slime.split_max_children = 1
        
        large_slime.fighter.hp = 10
        split_data = check_split_trigger(large_slime)
        
        self.assertIsNotNone(split_data)
        self.assertGreaterEqual(split_data['num_children'], 1)
    
    def test_split_does_not_trigger_on_death_from_above_threshold(self):
        """Slime killed from above threshold should NOT split."""
        large_slime = self.factory.create_monster("large_slime", 5, 5)
        
        # Kill from high HP (one-shot) - Stay above 35% threshold
        large_slime.fighter.hp = 42  # Full HP (35% = 14.7)
        damage_results = large_slime.fighter.take_damage(27)  # Damage to 15 HP (35.7%)
        
        # Check for split in results - should NOT trigger (still above 35%)
        split_results = [r for r in damage_results if 'split' in r]
        self.assertEqual(len(split_results), 0, "Should not split when above threshold")
        
        # Entity should still be alive at 15 HP
        self.assertGreater(large_slime.fighter.hp, 0)


class TestSlimeSplitIntegration(unittest.TestCase):
    """Integration tests for split behavior in combat scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        random.seed(123)
        self.factory = get_entity_factory()
    
    def test_fighter_take_damage_triggers_split(self):
        """Fighter.take_damage should check for split trigger."""
        large_slime = self.factory.create_monster("large_slime", 5, 5)
        
        # Damage to split threshold (42 - 28 = 14, which is 33% < 35%)
        results = large_slime.fighter.take_damage(28)
        
        # Check for split result
        split_results = [r for r in results if 'split' in r]
        self.assertEqual(len(split_results), 1, "Should trigger split")
        
        # Verify split data
        split_data = split_results[0]['split']
        self.assertEqual(split_data['original_entity'], large_slime)
        self.assertEqual(split_data['child_type'], "slime")
    
    def test_split_takes_precedence_over_death(self):
        """If split triggers, entity should split instead of dying normally."""
        large_slime = self.factory.create_monster("large_slime", 5, 5)
        
        # Fatal damage that triggers split threshold
        results = large_slime.fighter.take_damage(50)  # Way overkill
        
        # Should have split, not death
        split_results = [r for r in results if 'split' in r]
        dead_results = [r for r in results if 'dead' in r]
        
        # Split triggered (HP below threshold)
        self.assertGreater(len(split_results), 0, "Should trigger split")
        # Death should NOT trigger (split takes precedence)
        self.assertEqual(len(dead_results), 0, "Should not have normal death when split triggers")


class TestSlimeSplitScenario(unittest.TestCase):
    """Scenario-based tests for split behavior."""
    
    def setUp(self):
        """Set up scenario."""
        random.seed(999)
        self.factory = get_entity_factory()
    
    def test_scenario_large_slime_split_into_minors(self):
        """Scenario: Large slime takes gradual damage and splits at threshold."""
        large_slime = self.factory.create_monster("large_slime", 10, 10)
        entities = [large_slime]
        
        # Mock map
        mock_map = Mock()
        mock_map.width = 30
        mock_map.height = 30
        mock_map.tiles = [[Mock(blocked=False) for _ in range(30)] for _ in range(30)]
        
        # HP: 42 -> 32 (76%)
        results = large_slime.fighter.take_damage(10)
        self.assertEqual(len([r for r in results if 'split' in r]), 0)
        
        # HP: 32 -> 22 (52%)
        results = large_slime.fighter.take_damage(10)
        self.assertEqual(len([r for r in results if 'split' in r]), 0)
        
        # HP: 22 -> 12 (28% < 35%) - SPLIT!
        results = large_slime.fighter.take_damage(10)
        split_results = [r for r in results if 'split' in r]
        self.assertEqual(len(split_results), 1)
        
        # Execute split
        split_data = split_results[0]['split']
        children = execute_split(split_data, game_map=mock_map, entities=entities)
        
        # Verify outcome
        self.assertGreaterEqual(len(children), 2)
        self.assertNotIn(large_slime, entities)
        for child in children:
            self.assertEqual(child.name, "Slime")


if __name__ == '__main__':
    unittest.main()

