"""Tests for the monster item usage system.

This module tests monster usage of consumable items including:
- Scroll usage with failure mechanics
- Strategic item usage decisions
- Extensible design for future potion usage
- Integration with existing AI systems
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import random

from components.monster_item_usage import MonsterItemUsage, create_monster_item_usage
from components.ai import BasicMonster
from components.inventory import Inventory
from game_messages import Message


class TestMonsterItemUsage(unittest.TestCase):
    """Test the MonsterItemUsage component."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock monster with inventory
        from components.component_registry import ComponentType
        self.monster = Mock()
        self.monster.name = "orc"
        self.monster.x = 5
        self.monster.y = 5
        self.monster.inventory = Mock()
        self.monster.inventory.items = []
        self.monster.equipment = Mock()
        self.monster.equipment.main_hand = None
        self.monster.equipment.off_hand = None
        
        # Mock component access helpers
        def get_component(comp_type):
            if comp_type == ComponentType.INVENTORY:
                return self.monster.inventory
            elif comp_type == ComponentType.EQUIPMENT:
                return self.monster.equipment
            return None
        self.monster.get_component_optional = Mock(side_effect=get_component)
        # Also mock old method for backward compatibility
        self.monster.components = Mock()
        self.monster.components.get = Mock(side_effect=get_component)
        
        # Mock player
        self.player = Mock()
        self.player.x = 7
        self.player.y = 7
        
        # Mock game map
        self.game_map = Mock()
        
        # Create item usage component
        self.item_usage = MonsterItemUsage(self.monster)

    def test_initialization(self):
        """Test MonsterItemUsage initialization."""
        usage = MonsterItemUsage(self.monster)
        
        self.assertEqual(usage.monster, self.monster)
        self.assertTrue(usage.can_use_scrolls)
        self.assertFalse(usage.can_use_potions)  # Disabled for balance

    def test_no_inventory_returns_none(self):
        """Test that monsters without inventory can't use items."""
        self.monster.inventory = None
        
        result = self.item_usage.get_item_usage_action(self.player, self.game_map, [])
        
        self.assertIsNone(result)

    def test_empty_inventory_returns_none(self):
        """Test that monsters with empty inventory can't use items."""
        self.monster.inventory.items = []
        
        result = self.item_usage.get_item_usage_action(self.player, self.game_map, [])
        
        self.assertIsNone(result)

    def test_find_usable_scrolls(self):
        """Test finding usable scroll items."""
        # Create mock scrolls
        lightning_scroll = Mock()
        lightning_scroll.name = "Lightning Scroll"
        lightning_scroll.item = Mock()
        lightning_scroll.item.use_function = Mock()
        
        healing_potion = Mock()
        healing_potion.name = "Healing Potion"
        healing_potion.item = Mock()
        healing_potion.item.use_function = Mock()
        
        non_usable = Mock()
        non_usable.name = "Sword"
        non_usable.item = None
        
        self.monster.inventory.items = [lightning_scroll, healing_potion, non_usable]
        
        usable_items = self.item_usage._find_usable_items()
        
        # Should find only the scroll (potions disabled for balance)
        self.assertEqual(len(usable_items), 1)
        self.assertEqual(usable_items[0], lightning_scroll)

    def test_should_use_offensive_scroll_when_close(self):
        """Test using offensive scrolls when player is nearby."""
        # Lightning scroll
        lightning_scroll = Mock()
        lightning_scroll.name = "Lightning Scroll"
        lightning_scroll.item = Mock()
        lightning_scroll.item.use_function = Mock()
        
        # Player is close (distance ~2.8)
        self.player.x = 7
        self.player.y = 7
        
        should_use, item = self.item_usage._should_use_item([lightning_scroll], self.player, [])
        
        self.assertTrue(should_use)
        self.assertEqual(item, lightning_scroll)

    def test_should_not_use_offensive_scroll_when_far(self):
        """Test not using offensive scrolls when player is far."""
        # Lightning scroll
        lightning_scroll = Mock()
        lightning_scroll.name = "Lightning Scroll"
        lightning_scroll.item = Mock()
        lightning_scroll.item.use_function = Mock()
        
        # Player is far (distance ~7.1)
        self.player.x = 10
        self.player.y = 10
        
        should_use, item = self.item_usage._should_use_item([lightning_scroll], self.player, [])
        
        self.assertFalse(should_use)
        self.assertIsNone(item)

    def test_should_use_enhancement_scroll_with_equipment(self):
        """Test using enhancement scrolls when monster has equipment."""
        # Enhancement scroll
        enhance_scroll = Mock()
        enhance_scroll.name = "Enhance Weapon Scroll"
        enhance_scroll.item = Mock()
        enhance_scroll.item.use_function = Mock()
        
        # Monster has weapon equipped
        self.monster.equipment = Mock()
        self.monster.equipment.main_hand = Mock()
        self.monster.equipment.off_hand = None
        
        should_use, item = self.item_usage._should_use_item([enhance_scroll], self.player, [])
        
        self.assertTrue(should_use)
        self.assertEqual(item, enhance_scroll)

    def test_should_not_use_enhancement_scroll_without_equipment(self):
        """Test not using enhancement scrolls when monster has no equipment."""
        # Enhancement scroll
        enhance_scroll = Mock()
        enhance_scroll.name = "Enhance Weapon Scroll"
        enhance_scroll.item = Mock()
        enhance_scroll.item.use_function = Mock()
        
        # Monster has no equipment
        self.monster.equipment = None
        
        should_use, item = self.item_usage._should_use_item([enhance_scroll], self.player, [])
        
        self.assertFalse(should_use)
        self.assertIsNone(item)

    @patch('random.random')
    def test_successful_item_usage(self, mock_random):
        """Test successful item usage (no failure)."""
        mock_random.return_value = 0.8  # Above failure rate (0.75)
        
        # Mock scroll
        scroll = Mock()
        scroll.name = "Lightning Scroll"
        scroll.item = Mock()
        scroll.item.use_function = Mock(return_value=[{"damage": 40}])
        scroll.item.function_kwargs = {}
        
        self.monster.inventory.items = [scroll]
        
        results = self.item_usage.use_item_with_failure(scroll, self.player, [])
        
        # Should call use function and generate success message
        scroll.item.use_function.assert_called_once()
        self.assertEqual(len(results), 2)  # Use result + success message
        self.assertIn("uses Lightning Scroll", results[1]["message"].text)

    @patch('random.random')
    @patch('random.choice')
    def test_fizzle_failure(self, mock_choice, mock_random):
        """Test fizzle failure mode."""
        mock_random.return_value = 0.3  # Below failure rate (0.5)
        mock_choice.return_value = 'fizzle'
        
        scroll = Mock()
        scroll.name = "Lightning Scroll"
        self.monster.inventory.items = [scroll]
        
        results = self.item_usage.use_item_with_failure(scroll, self.player, [])
        
        # Should generate fizzle message
        self.assertEqual(len(results), 1)
        self.assertIn("fizzles harmlessly", results[0]["message"].text)

    @patch('components.monster_item_usage.random.choice')
    @patch('random.random')
    def test_wrong_target_failure_beneficial_scroll(self, mock_random, mock_choice_in_module):
        """Test wrong target failure with beneficial scroll."""
        mock_random.return_value = 0.3  # Below failure rate
        mock_choice_in_module.return_value = 'wrong_target'
        
        # Enhancement scroll (beneficial)
        scroll = Mock()
        scroll.name = "enhance_weapon_scroll"
        scroll.item = Mock()
        scroll.item.use_function = Mock(return_value=[])
        scroll.item.function_kwargs = {}
        
        self.monster.inventory.items = [scroll]
        
        results = self.item_usage.use_item_with_failure(scroll, self.player, [])
        
        # Should call use function with player as target (wrong target)
        scroll.item.use_function.assert_called_once()
        call_args = scroll.item.use_function.call_args
        self.assertEqual(call_args[1]['target_entity'], self.player)
        
        # Should generate backfire message
        self.assertTrue(any("backfires on player" in result.get("message", Mock()).text 
                          for result in results if "message" in result))

    @patch('random.random')
    @patch('random.choice')
    def test_wrong_target_failure_harmful_scroll(self, mock_choice, mock_random):
        """Test wrong target failure with harmful scroll."""
        mock_random.return_value = 0.3  # Below failure rate
        mock_choice.return_value = 'wrong_target'
        
        # Lightning scroll (harmful)
        scroll = Mock()
        scroll.name = "Lightning Scroll"
        scroll.item = Mock()
        scroll.item.use_function = Mock(return_value=[])
        scroll.item.function_kwargs = {}
        
        self.monster.inventory.items = [scroll]
        
        results = self.item_usage.use_item_with_failure(scroll, self.player, [])
        
        # Should call use function with monster as target (backfire)
        scroll.item.use_function.assert_called_once()
        call_args = scroll.item.use_function.call_args
        self.assertEqual(call_args[1]['target_entity'], self.monster)
        
        # Should generate backfire message
        self.assertTrue(any("backfires on themselves" in result.get("message", Mock()).text 
                          for result in results if "message" in result))

    @patch('components.monster_item_usage.random.choice')
    @patch('random.random')
    def test_equipment_damage_failure(self, mock_random, mock_choice_in_module):
        """Test equipment damage failure mode."""
        mock_random.return_value = 0.3  # Below failure rate
        
        # Create a simple class to hold equipment stats
        class MockEquippable:
            def __init__(self):
                self.damage_min = 3
                self.damage_max = 5
        
        # Mock equipped weapon with variable damage
        weapon = Mock()
        weapon.name = "Sword"
        weapon.equippable = MockEquippable()
        
        self.monster.equipment = Mock()
        self.monster.equipment.main_hand = weapon
        self.monster.equipment.off_hand = None
        
        # Mock the choice function to return our weapon when selecting equipment to damage
        mock_choice_in_module.side_effect = [
            'equipment_damage',  # First call: failure mode selection
            ('weapon', weapon)   # Second call: equipment selection
        ]
        
        scroll = Mock()
        scroll.name = "Lightning Scroll"
        self.monster.inventory.items = [scroll]
        
        results = self.item_usage.use_item_with_failure(scroll, self.player, [])
        
        # Should damage weapon
        self.assertEqual(weapon.equippable.damage_min, 2)  # Reduced by 1
        self.assertEqual(weapon.equippable.damage_max, 4)  # Reduced by 1
        
        # Should generate damage message
        self.assertTrue(any("weakened by the backfire" in result.get("message", Mock()).text 
                          for result in results if "message" in result))

    @patch('random.random')
    def test_item_removed_after_use(self, mock_random):
        """Test that items are removed from inventory after use."""
        # Force success to avoid failure mode complications
        mock_random.return_value = 0.6  # Above failure rate
        
        scroll = Mock()
        scroll.name = "Lightning Scroll"
        scroll.item = Mock()
        scroll.item.use_function = Mock(return_value=[])
        scroll.item.function_kwargs = {}
        
        self.monster.inventory.items = [scroll]
        
        self.item_usage.use_item_with_failure(scroll, self.player, [])
        
        # Item should be removed from inventory
        self.assertNotIn(scroll, self.monster.inventory.items)


class TestMonsterItemUsageCreation(unittest.TestCase):
    """Test creation of MonsterItemUsage components."""

    def test_create_monster_item_usage_success(self):
        """Test successful creation of MonsterItemUsage."""
        monster = Mock()
        monster.inventory = Mock()
        
        usage = create_monster_item_usage(monster)
        
        self.assertIsNotNone(usage)
        self.assertIsInstance(usage, MonsterItemUsage)

    def test_create_monster_item_usage_no_inventory(self):
        """Test creation when monster has no inventory."""
        from components.component_registry import ComponentType
        monster = Mock()
        monster.inventory = None
        monster.get_component_optional = Mock(return_value=None)
        monster.components = Mock()
        monster.components.get = Mock(return_value=None)
        
        usage = create_monster_item_usage(monster)
        
        self.assertIsNone(usage)


class TestBasicMonsterItemUsageIntegration(unittest.TestCase):
    """Test integration of item usage with BasicMonster AI."""

    def setUp(self):
        """Set up test fixtures."""
        from entity import Entity
        from components.fighter import Fighter
        from components.component_registry import ComponentType
        
        # Create a real Entity with Fighter (required by ComponentRegistry patterns)
        fighter = Fighter(hp=30, defense=2, power=5)
        self.monster = Entity(5, 5, 'o', (0, 255, 0), 'orc', blocks=True, fighter=fighter)
        
        # Mock methods that we need to track
        self.monster.distance_to = Mock(return_value=3)
        self.monster.move_astar = Mock()
        self.monster.fighter.attack = Mock(return_value=[])
        
        # Mock has_status_effect to prevent immobilized check from failing
        self.monster.has_status_effect = Mock(return_value=False)
        
        self.player = Mock()
        self.player.x = 7
        self.player.y = 7
        self.player.fighter = Mock()
        self.player.fighter.hp = 100
        
        self.ai = BasicMonster()
        self.ai.owner = self.monster
        
        self.fov_map = Mock()
        self.game_map = Mock()
        self.entities = [self.monster, self.player]

    @patch('components.ai.map_is_in_fov')
    def test_item_usage_overrides_other_actions(self, mock_fov):
        """Test that item usage takes priority over other actions."""
        from components.component_registry import ComponentType
        
        mock_fov.return_value = True
        
        # Mock item usage that returns an action and register it with ComponentRegistry
        mock_item_usage = Mock()
        mock_item_usage.get_item_usage_action.return_value = {
            "use_item": Mock(name="Lightning Scroll"),
            "target": self.player
        }
        mock_item_usage.use_item_with_failure.return_value = [
            {"message": Message("Orc uses Lightning Scroll!", (255, 255, 0))}
        ]
        self.monster.item_usage = mock_item_usage
        self.monster.components.add(ComponentType.ITEM_USAGE, mock_item_usage)
        
        results = self.ai.take_turn(self.player, self.fov_map, self.game_map, self.entities)
        
        # Should use item, not move or attack
        mock_item_usage.use_item_with_failure.assert_called_once()
        self.monster.move_astar.assert_not_called()
        self.monster.fighter.attack.assert_not_called()
        
        # Should return usage results
        self.assertEqual(len(results), 1)
        self.assertIn("message", results[0])

    @patch('components.ai.map_is_in_fov')
    def test_normal_behavior_without_item_usage(self, mock_fov):
        """Test normal AI behavior when no item usage component is present."""
        mock_fov.return_value = True
        self.monster.item_usage = None
        self.monster.item_seeking_ai = None
        
        results = self.ai.take_turn(self.player, self.fov_map, self.game_map, self.entities)
        
        # Should use normal pathfinding
        self.monster.move_astar.assert_called_once()


class TestExtensibleDesign(unittest.TestCase):
    """Test the extensible design for future potion usage."""

    def test_potion_usage_disabled_by_default(self):
        """Test that potion usage is disabled by default for balance."""
        monster = Mock()
        monster.inventory = Mock()
        
        usage = MonsterItemUsage(monster)
        
        self.assertFalse(usage.can_use_potions)

    def test_potion_framework_ready_for_future(self):
        """Test that potion usage framework is ready for future activation."""
        from components.component_registry import ComponentType
        monster = Mock()
        monster.inventory = Mock()
        monster.inventory.items = []
        
        # Mock component access helpers to return the inventory
        monster.get_component_optional = Mock(return_value=monster.inventory)
        monster.components = Mock()
        monster.components.get = Mock(return_value=monster.inventory)
        
        # Create mock potion
        potion = Mock()
        potion.name = "Healing Potion"
        potion.item = Mock()
        potion.item.use_function = Mock()
        potion.components = Mock()
        potion.components.has = Mock(return_value=True)
        
        # Set up inventory items list
        monster.inventory.items = [potion]
        
        usage = MonsterItemUsage(monster)
        
        # Temporarily enable potion usage to test framework
        usage.can_use_potions = True
        
        usable_items = usage._find_usable_items()
        
        # Should find the potion when enabled
        self.assertEqual(len(usable_items), 1)
        self.assertEqual(usable_items[0], potion)


if __name__ == '__main__':
    unittest.main()
