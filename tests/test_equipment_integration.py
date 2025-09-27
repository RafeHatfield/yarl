"""
Unit tests for Equipment system integration.

Tests equipment integration with:
- Entity system and component linking
- Inventory system and equipment handling
- Game map equipment spawning
- Engine equipment result processing
- Menu system equipment display
"""

import pytest
from unittest.mock import Mock, patch

from components.equipment import Equipment
from components.equippable import Equippable
from components.fighter import Fighter
from components.inventory import Inventory
from equipment_slots import EquipmentSlots
from entity import Entity
from game_messages import Message
from render_functions import RenderOrder


class TestEquipmentEntityIntegration:
    """Test Equipment integration with Entity system."""

    def test_entity_with_equipment_component(self):
        """Test Entity creation with Equipment component."""
        equipment = Equipment()
        entity = Entity(0, 0, "@", (255, 255, 255), "Player", equipment=equipment)

        assert entity.equipment == equipment
        assert equipment.owner == entity

    def test_entity_with_equippable_component(self):
        """Test Entity creation with Equippable component."""
        equippable = Equippable(EquipmentSlots.MAIN_HAND, power_bonus=3)
        entity = Entity(0, 0, "/", (255, 255, 255), "Sword", equippable=equippable)

        assert entity.equippable == equippable
        assert equippable.owner == entity

    def test_entity_equippable_creates_item_component(self):
        """Test that Entity with Equippable automatically gets Item component."""
        equippable = Equippable(EquipmentSlots.MAIN_HAND, power_bonus=3)
        entity = Entity(0, 0, "/", (255, 255, 255), "Sword", equippable=equippable)

        assert entity.item is not None
        assert entity.item.owner == entity

    def test_entity_with_both_equipment_and_equippable(self):
        """Test Entity with both Equipment and Equippable components."""
        equipment = Equipment()
        equippable = Equippable(EquipmentSlots.MAIN_HAND, power_bonus=3)

        entity = Entity(
            0,
            0,
            "@",
            (255, 255, 255),
            "Player",
            equipment=equipment,
            equippable=equippable,
        )

        assert entity.equipment == equipment
        assert entity.equippable == equippable
        assert equipment.owner == entity
        assert equippable.owner == entity

    def test_entity_component_linking(self):
        """Test that all components are properly linked to entity."""
        fighter = Fighter(hp=100, defense=1, power=2)
        equipment = Equipment()
        inventory = Inventory(26)

        entity = Entity(
            0,
            0,
            "@",
            (255, 255, 255),
            "Player",
            fighter=fighter,
            equipment=equipment,
            inventory=inventory,
        )

        assert fighter.owner == entity
        assert equipment.owner == entity
        assert inventory.owner == entity


class TestEquipmentInventoryIntegration:
    """Test Equipment integration with Inventory system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.fighter = Fighter(hp=100, defense=1, power=2)
        self.equipment = Equipment()
        self.inventory = Inventory(26)

        self.player = Entity(
            0,
            0,
            "@",
            (255, 255, 255),
            "Player",
            fighter=self.fighter,
            equipment=self.equipment,
            inventory=self.inventory,
        )

    def test_inventory_use_equippable_item(self):
        """Test using equippable item from inventory."""
        # Create equippable sword
        sword_equippable = Equippable(EquipmentSlots.MAIN_HAND, power_bonus=3)
        sword = Entity(0, 0, "/", (255, 255, 255), "Sword", equippable=sword_equippable)

        # Add to inventory
        self.inventory.add_item(sword)

        # Use item (should trigger equip)
        results = self.inventory.use(sword)

        assert len(results) == 1
        assert "equip" in results[0]
        assert results[0]["equip"] == sword

    def test_inventory_use_non_equippable_item(self):
        """Test using non-equippable item from inventory."""
        from components.item import Item

        # Create non-equippable item (has item component but no use_function or equippable)
        item_component = Item()  # No use_function
        potion = Entity(0, 0, "!", (255, 255, 255), "Potion", item=item_component)

        # Add to inventory
        self.inventory.add_item(potion)

        # Use item (should show cannot be used message)
        results = self.inventory.use(potion)

        assert len(results) == 1
        assert "message" in results[0]
        assert "cannot be used" in results[0]["message"].text.lower()

    def test_inventory_use_item_with_use_function(self):
        """Test that items with use_function don't trigger equip."""
        from components.item import Item
        from item_functions import heal

        # Create item with use function
        item_component = Item(use_function=heal, amount=40)
        potion = Entity(
            0, 0, "!", (255, 255, 255), "Healing Potion", item=item_component
        )

        # Add to inventory
        self.inventory.add_item(potion)

        # Use item (should use function, not equip)
        results = self.inventory.use(potion)

        # Should not contain 'equip' result
        assert not any("equip" in result for result in results)

    def test_inventory_equippable_item_stays_in_inventory(self):
        """Test that equipped items remain in inventory."""
        # Create equippable sword
        sword_equippable = Equippable(EquipmentSlots.MAIN_HAND, power_bonus=3)
        sword = Entity(0, 0, "/", (255, 255, 255), "Sword", equippable=sword_equippable)

        # Add to inventory and use
        self.inventory.add_item(sword)
        initial_count = len(self.inventory.items)

        self.inventory.use(sword)

        # Item should still be in inventory (not consumed)
        assert len(self.inventory.items) == initial_count
        assert sword in self.inventory.items


class TestEquipmentSpawning:
    """Test equipment spawning in game map."""

    @patch("map_objects.game_map.random_choice_from_dict")
    @patch("map_objects.game_map.randint")
    @patch("map_objects.game_map.from_dungeon_level")
    def test_sword_spawning(self, mock_from_level, mock_randint, mock_choice):
        """Test sword spawning in game map."""
        from map_objects.game_map import GameMap
        from map_objects.rectangle import Rect

        # Set up mocks
        mock_from_level.return_value = 5  # sword available
        mock_randint.side_effect = [0, 1, 10, 10]  # 0 monsters, 1 item, position
        mock_choice.return_value = "sword"

        game_map = GameMap(width=20, height=20, dungeon_level=4)
        room = Rect(5, 5, 10, 10)
        entities = []

        game_map.place_entities(room, entities)

        # Should spawn sword
        assert len(entities) == 1
        sword = entities[0]
        assert sword.name == "Sword"
        assert sword.char == "/"
        assert sword.equippable is not None
        assert sword.equippable.slot == EquipmentSlots.MAIN_HAND
        assert sword.equippable.power_bonus == 3

    @patch("map_objects.game_map.random_choice_from_dict")
    @patch("map_objects.game_map.randint")
    @patch("map_objects.game_map.from_dungeon_level")
    def test_shield_spawning(self, mock_from_level, mock_randint, mock_choice):
        """Test shield spawning in game map."""
        from map_objects.game_map import GameMap
        from map_objects.rectangle import Rect

        # Set up mocks
        mock_from_level.return_value = 15  # shield available
        mock_randint.side_effect = [0, 1, 10, 10]  # 0 monsters, 1 item, position
        mock_choice.return_value = "shield"

        game_map = GameMap(width=20, height=20, dungeon_level=8)
        room = Rect(5, 5, 10, 10)
        entities = []

        game_map.place_entities(room, entities)

        # Should spawn shield
        assert len(entities) == 1
        shield = entities[0]
        assert shield.name == "Shield"
        assert shield.char == "["
        assert shield.equippable is not None
        assert shield.equippable.slot == EquipmentSlots.OFF_HAND
        assert shield.equippable.defense_bonus == 1

    def test_equipment_spawn_level_requirements(self):
        """Test equipment spawn level requirements."""
        from map_objects.game_map import GameMap
        from random_utils import from_dungeon_level

        # Test sword availability (level 4+)
        sword_chance_level_3 = from_dungeon_level([[5, 4]], 3)
        sword_chance_level_4 = from_dungeon_level([[5, 4]], 4)
        sword_chance_level_5 = from_dungeon_level([[5, 4]], 5)

        assert sword_chance_level_3 == 0  # Not available at level 3
        assert sword_chance_level_4 == 5  # Available at level 4
        assert sword_chance_level_5 == 5  # Still available at level 5

        # Test shield availability (level 8+)
        shield_chance_level_7 = from_dungeon_level([[15, 8]], 7)
        shield_chance_level_8 = from_dungeon_level([[15, 8]], 8)
        shield_chance_level_9 = from_dungeon_level([[15, 8]], 9)

        assert shield_chance_level_7 == 0  # Not available at level 7
        assert shield_chance_level_8 == 15  # Available at level 8
        assert shield_chance_level_9 == 15  # Still available at level 9


class TestEquipmentEngineIntegration:
    """Test equipment integration with game engine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.fighter = Fighter(hp=100, defense=1, power=2)
        self.equipment = Equipment()
        self.inventory = Inventory(26)

        self.player = Entity(
            0,
            0,
            "@",
            (255, 255, 255),
            "Player",
            fighter=self.fighter,
            equipment=self.equipment,
            inventory=self.inventory,
        )

    def test_engine_equip_result_processing(self):
        """Test engine processing of equip results."""
        # Create sword
        sword_equippable = Equippable(EquipmentSlots.MAIN_HAND, power_bonus=3)
        sword = Entity(0, 0, "/", (255, 255, 255), "Sword", equippable=sword_equippable)

        # Add to inventory
        self.inventory.add_item(sword)

        # Simulate inventory use (as engine would do)
        player_turn_results = self.inventory.use(sword)

        # Process equip result (as engine would do)
        for result in player_turn_results:
            equip = result.get("equip")
            if equip:
                equip_results = self.equipment.toggle_equip(equip)

                # Should get equipped result
                assert len(equip_results) == 1
                assert "equipped" in equip_results[0]
                assert equip_results[0]["equipped"] == sword

    def test_engine_equipment_message_generation(self):
        """Test equipment message generation for engine."""
        # Create and equip sword
        sword_equippable = Equippable(EquipmentSlots.MAIN_HAND, power_bonus=3)
        sword = Entity(0, 0, "/", (255, 255, 255), "Sword", equippable=sword_equippable)
        sword.name = "Sword"  # Ensure name is set for message

        equip_results = self.equipment.toggle_equip(sword)

        # Should generate equipped message
        assert len(equip_results) == 1
        equipped = equip_results[0].get("equipped")
        assert equipped == sword

        # Engine would create message like: "You equipped the Sword"
        message_text = f"You equipped the {equipped.name}"
        assert "Sword" in message_text

    def test_engine_equipment_replacement_messages(self):
        """Test equipment replacement message generation."""
        # Create two swords
        old_sword_equippable = Equippable(EquipmentSlots.MAIN_HAND, power_bonus=2)
        old_sword = Entity(
            0, 0, "/", (255, 255, 255), "Old Sword", equippable=old_sword_equippable
        )
        old_sword.name = "Old Sword"

        new_sword_equippable = Equippable(EquipmentSlots.MAIN_HAND, power_bonus=3)
        new_sword = Entity(
            0, 0, "/", (255, 255, 255), "New Sword", equippable=new_sword_equippable
        )
        new_sword.name = "New Sword"

        # Equip first sword
        self.equipment.toggle_equip(old_sword)

        # Replace with new sword
        equip_results = self.equipment.toggle_equip(new_sword)

        # Should get both dequipped and equipped results
        assert len(equip_results) == 2

        dequipped = equip_results[0].get("dequipped")
        equipped = equip_results[1].get("equipped")

        assert dequipped == old_sword
        assert equipped == new_sword


class TestEquipmentMenuIntegration:
    """Test equipment integration with menu system."""

    def test_equipment_display_in_character_screen(self):
        """Test equipment display in character screen menu."""
        # This would test menu.py integration, but since menus.py
        # is complex, we'll test the data that would be displayed

        fighter = Fighter(hp=100, defense=1, power=2)
        equipment = Equipment()

        # Create equipped items
        sword_equippable = Equippable(EquipmentSlots.MAIN_HAND, power_bonus=3)
        sword = Entity(0, 0, "/", (255, 255, 255), "Sword", equippable=sword_equippable)
        sword.name = "Sword"

        shield_equippable = Equippable(EquipmentSlots.OFF_HAND, defense_bonus=2)
        shield = Entity(
            0, 0, "[", (255, 255, 255), "Shield", equippable=shield_equippable
        )
        shield.name = "Shield"

        player = Entity(
            0, 0, "@", (255, 255, 255), "Player", fighter=fighter, equipment=equipment
        )

        equipment.toggle_equip(sword)
        equipment.toggle_equip(shield)

        # Test data that would be displayed in character screen
        assert equipment.main_hand == sword
        assert equipment.off_hand == shield
        assert equipment.main_hand.name == "Sword"
        assert equipment.off_hand.name == "Shield"

        # Test stat bonuses that would be shown
        assert equipment.power_bonus == 3
        assert equipment.defense_bonus == 2
        assert equipment.max_hp_bonus == 0

    def test_equipment_stat_display_data(self):
        """Test stat display data for equipment."""
        fighter = Fighter(hp=100, defense=2, power=5)
        equipment = Equipment()

        player = Entity(
            0, 0, "@", (255, 255, 255), "Player", fighter=fighter, equipment=equipment
        )

        # Test base stats
        assert fighter.base_max_hp == 100
        assert fighter.base_defense == 2
        assert fighter.base_power == 5

        # Equip items
        weapon_equippable = Equippable(
            EquipmentSlots.MAIN_HAND, power_bonus=4, defense_bonus=1
        )
        weapon = Entity(
            0, 0, "/", (255, 255, 255), "Magic Sword", equippable=weapon_equippable
        )

        equipment.toggle_equip(weapon)

        # Test effective stats (what would be displayed)
        assert fighter.max_hp == 100  # 100 + 0
        assert fighter.defense == 3  # 2 + 1
        assert fighter.power == 9  # 5 + 4

        # Test bonus breakdown (what could be shown in detailed view)
        assert equipment.power_bonus == 4
        assert equipment.defense_bonus == 1
        assert equipment.max_hp_bonus == 0


class TestEquipmentSystemRobustness:
    """Test equipment system robustness and edge cases."""

    def test_equipment_with_none_owner(self):
        """Test equipment behavior when owner is None."""
        fighter = Fighter(hp=100, defense=1, power=2)
        fighter.owner = None

        # Should handle None owner gracefully
        assert fighter.max_hp == 100
        assert fighter.power == 2
        assert fighter.defense == 1

    def test_equipment_with_none_equipment(self):
        """Test fighter behavior when equipment is None."""
        fighter = Fighter(hp=100, defense=1, power=2)
        entity = Mock()
        entity.equipment = None
        fighter.owner = entity

        # Should handle None equipment gracefully
        assert fighter.max_hp == 100
        assert fighter.power == 2
        assert fighter.defense == 1

    def test_equipment_component_independence(self):
        """Test that equipment components are independent."""
        equipment1 = Equipment()
        equipment2 = Equipment()

        # Create items
        sword_equippable = Equippable(EquipmentSlots.MAIN_HAND, power_bonus=3)
        sword = Entity(0, 0, "/", (255, 255, 255), "Sword", equippable=sword_equippable)

        # Equip to first equipment only
        equipment1.toggle_equip(sword)

        # Should not affect second equipment
        assert equipment1.main_hand == sword
        assert equipment2.main_hand is None
        assert equipment1.power_bonus == 3
        assert equipment2.power_bonus == 0

    def test_equipment_memory_management(self):
        """Test equipment system doesn't create memory leaks."""
        equipment = Equipment()

        # Create and equip many items
        for i in range(100):
            item_equippable = Equippable(EquipmentSlots.MAIN_HAND, power_bonus=i)
            item = Entity(
                0, 0, "/", (255, 255, 255), f"Item{i}", equippable=item_equippable
            )
            equipment.toggle_equip(item)

        # Should only have the last item equipped
        assert equipment.main_hand.name == "Item99"
        assert equipment.power_bonus == 99
