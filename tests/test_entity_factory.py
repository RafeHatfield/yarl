"""Tests for the entity factory system.

This module tests entity creation functionality provided by the EntityFactory class.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from config.entity_factory import EntityFactory, get_entity_factory, set_entity_factory
from config.entity_registry import (
    EntityRegistry,
    EntityStats,
    MonsterDefinition,
    WeaponDefinition,
    ArmorDefinition,
    SpellDefinition
)
from entity import Entity
from components.fighter import Fighter
from components.ai import BasicMonster
from components.item import Item
from components.equippable import Equippable
from equipment_slots import EquipmentSlots
from render_functions import RenderOrder


class TestEntityFactory:
    """Test EntityFactory functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create mock registry
        self.mock_registry = Mock(spec=EntityRegistry)
        self.factory = EntityFactory(self.mock_registry)

        # Create test definitions
        self.test_monster_stats = EntityStats(hp=20, power=4, defense=0, xp=35)
        self.test_monster_def = MonsterDefinition(
            name="Orc",
            stats=self.test_monster_stats,
            char="o",
            color=(63, 127, 63),
            ai_type="basic",
            render_order="actor",
            blocks=True
        )

        self.test_weapon_def = WeaponDefinition(
            name="Sword",
            power_bonus=3,
            damage_min=2,
            damage_max=5,
            slot="main_hand",
            char="/",
            color=(192, 192, 192)
        )

        self.test_armor_def = ArmorDefinition(
            name="Shield",
            defense_bonus=1,
            defense_min=1,
            defense_max=3,
            slot="off_hand",
            char="[",
            color=(139, 69, 19)
        )

        self.test_spell_def = SpellDefinition(
            name="Healing Potion",
            spell_type="heal",
            heal_amount=40,
            char="!",
            color=(127, 0, 255)
        )

        self.test_player_stats = EntityStats(hp=100, power=2, defense=1, xp=0)

    def test_create_monster_success(self):
        """Test successful monster creation."""
        self.mock_registry.get_monster.return_value = self.test_monster_def

        monster = self.factory.create_monster("orc", 5, 10)

        assert monster is not None
        assert monster.name == "Orc"
        assert monster.x == 5
        assert monster.y == 10
        assert monster.char == "o"
        assert monster.color == (63, 127, 63)
        assert monster.blocks is True
        assert monster.fighter is not None
        assert monster.fighter.base_max_hp == 20
        assert monster.fighter.base_power == 4
        assert monster.fighter.base_defense == 0
        assert monster.fighter.xp == 35
        assert monster.ai is not None
        assert isinstance(monster.ai, BasicMonster)

    def test_create_monster_not_found(self):
        """Test monster creation when definition not found."""
        self.mock_registry.get_monster.return_value = None

        monster = self.factory.create_monster("unknown_monster", 5, 10)

        assert monster is not None
        assert monster.name == "Unknown unknown_monster"
        assert monster.char == "?"
        assert monster.color == (255, 0, 255)
        assert monster.fighter is not None
        assert monster.ai is not None

    def test_create_weapon_success(self):
        """Test successful weapon creation."""
        self.mock_registry.get_weapon.return_value = self.test_weapon_def

        weapon = self.factory.create_weapon("sword", 3, 7)

        assert weapon is not None
        assert weapon.name == "Sword"
        assert weapon.x == 3
        assert weapon.y == 7
        assert weapon.char == "/"
        assert weapon.color == (192, 192, 192)
        assert weapon.equippable is not None
        assert weapon.equippable.slot == EquipmentSlots.MAIN_HAND
        assert weapon.equippable.power_bonus == 3
        assert weapon.equippable.damage_min == 2
        assert weapon.equippable.damage_max == 5

    def test_create_weapon_not_found(self):
        """Test weapon creation when definition not found."""
        self.mock_registry.get_weapon.return_value = None

        weapon = self.factory.create_weapon("unknown_weapon", 3, 7)

        assert weapon is not None
        assert weapon.name == "Unknown unknown_weapon"
        assert weapon.char == "?"
        assert weapon.color == (255, 0, 255)
        assert weapon.equippable is not None

    def test_create_armor_success(self):
        """Test successful armor creation."""
        self.mock_registry.get_armor.return_value = self.test_armor_def

        armor = self.factory.create_armor("shield", 2, 8)

        assert armor is not None
        assert armor.name == "Shield"
        assert armor.x == 2
        assert armor.y == 8
        assert armor.char == "["
        assert armor.color == (139, 69, 19)
        assert armor.equippable is not None
        assert armor.equippable.slot == EquipmentSlots.OFF_HAND
        assert armor.equippable.defense_bonus == 1
        assert armor.equippable.defense_min == 1
        assert armor.equippable.defense_max == 3

    def test_create_armor_not_found(self):
        """Test armor creation when definition not found."""
        self.mock_registry.get_armor.return_value = None

        armor = self.factory.create_armor("unknown_armor", 2, 8)

        assert armor is not None
        assert armor.name == "Unknown unknown_armor"
        assert armor.char == "?"
        assert armor.color == (255, 0, 255)
        assert armor.equippable is not None

    @patch('item_functions.heal')
    def test_create_spell_item_healing_potion(self, mock_heal):
        """Test creating healing potion spell item."""
        self.mock_registry.get_spell.return_value = self.test_spell_def

        spell_item = self.factory.create_spell_item("healing_potion", 1, 1)

        assert spell_item is not None
        assert spell_item.name == "Healing Potion"
        assert spell_item.x == 1
        assert spell_item.y == 1
        assert spell_item.char == "!"
        assert spell_item.color == (127, 0, 255)
        assert spell_item.item is not None

    def test_create_spell_item_not_found(self):
        """Test spell item creation when definition not found."""
        self.mock_registry.get_spell.return_value = None

        spell_item = self.factory.create_spell_item("unknown_spell", 1, 1)

        assert spell_item is not None
        assert spell_item.name == "Unknown unknown_spell"
        assert spell_item.char == "?"
        assert spell_item.color == (255, 0, 255)
        assert spell_item.item is not None

    def test_get_player_stats_success(self):
        """Test getting player stats from registry."""
        self.mock_registry.get_player_stats.return_value = self.test_player_stats

        stats = self.factory.get_player_stats()

        assert stats is not None
        assert stats.hp == 100
        assert stats.power == 2
        assert stats.defense == 1
        assert stats.xp == 0

    def test_get_player_stats_not_found(self):
        """Test getting player stats when not configured."""
        self.mock_registry.get_player_stats.return_value = None

        stats = self.factory.get_player_stats()

        assert stats is not None
        assert stats.hp == 100  # Fallback values
        assert stats.power == 0  # Updated to new system
        assert stats.defense == 1
        assert stats.xp == 0

    def test_create_ai_component_basic(self):
        """Test creating basic AI component."""
        ai = self.factory._create_ai_component("basic")
        assert isinstance(ai, BasicMonster)

    def test_create_ai_component_unknown(self):
        """Test creating AI component with unknown type."""
        ai = self.factory._create_ai_component("unknown")
        assert isinstance(ai, BasicMonster)  # Should fallback to basic

    def test_get_render_order_actor(self):
        """Test converting render order string."""
        render_order = self.factory._get_render_order("actor")
        assert render_order == RenderOrder.ACTOR

    def test_get_render_order_unknown(self):
        """Test converting unknown render order string."""
        render_order = self.factory._get_render_order("unknown")
        assert render_order == RenderOrder.ACTOR  # Should fallback

    def test_get_equipment_slot_main_hand(self):
        """Test converting equipment slot string."""
        slot = self.factory._get_equipment_slot("main_hand")
        assert slot == EquipmentSlots.MAIN_HAND

    def test_get_equipment_slot_off_hand(self):
        """Test converting equipment slot string."""
        slot = self.factory._get_equipment_slot("off_hand")
        assert slot == EquipmentSlots.OFF_HAND

    def test_get_equipment_slot_unknown(self):
        """Test converting unknown equipment slot string."""
        slot = self.factory._get_equipment_slot("unknown")
        assert slot == EquipmentSlots.MAIN_HAND  # Should fallback


class TestEntityFactoryIntegration:
    """Integration tests for EntityFactory with real registry."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create real registry with test data
        self.registry = EntityRegistry()
        
        # Create test configuration
        test_config = {
            "version": "1.0",
            "player": {
                "hp": 100,
                "power": 2,
                "defense": 1,
                "xp": 0
            },
            "monsters": {
                "test_orc": {
                    "stats": {
                        "hp": 20,
                        "power": 4,
                        "defense": 0,
                        "xp": 35
                    },
                    "char": "o",
                    "color": [63, 127, 63],
                    "ai_type": "basic"
                }
            },
            "weapons": {
                "test_sword": {
                    "power_bonus": 3,
                    "damage_min": 2,
                    "damage_max": 5,
                    "slot": "main_hand",
                    "char": "/",
                    "color": [192, 192, 192]
                }
            },
            "armor": {
                "test_shield": {
                    "defense_bonus": 1,
                    "defense_min": 1,
                    "defense_max": 3,
                    "slot": "off_hand",
                    "char": "[",
                    "color": [139, 69, 19]
                }
            },
            "spells": {
                "healing_potion": {
                    "spell_type": "heal",
                    "heal_amount": 40,
                    "char": "!",
                    "color": [127, 0, 255]
                }
            }
        }
        
        self.registry._process_config_data(test_config)
        self.factory = EntityFactory(self.registry)

    def test_end_to_end_monster_creation(self):
        """Test complete monster creation flow."""
        monster = self.factory.create_monster("test_orc", 10, 15)
        
        assert monster is not None
        assert monster.name == "Test_Orc"
        assert monster.x == 10
        assert monster.y == 15
        assert monster.fighter.base_max_hp == 20
        assert monster.fighter.base_power == 4
        assert monster.ai is not None

    def test_end_to_end_weapon_creation(self):
        """Test complete weapon creation flow."""
        weapon = self.factory.create_weapon("test_sword", 5, 5)
        
        assert weapon is not None
        assert weapon.name == "Test_Sword"
        assert weapon.equippable.power_bonus == 3
        assert weapon.equippable.damage_min == 2
        assert weapon.equippable.damage_max == 5

    def test_end_to_end_armor_creation(self):
        """Test complete armor creation flow."""
        armor = self.factory.create_armor("test_shield", 3, 3)
        
        assert armor is not None
        assert armor.name == "Test_Shield"
        assert armor.equippable.defense_bonus == 1
        assert armor.equippable.defense_min == 1
        assert armor.equippable.defense_max == 3

    @patch('item_functions.heal')
    def test_end_to_end_spell_creation(self, mock_heal):
        """Test complete spell creation flow."""
        spell_item = self.factory.create_spell_item("healing_potion", 1, 1)
        
        assert spell_item is not None
        assert spell_item.name == "Healing Potion"
        assert spell_item.item is not None

    def test_end_to_end_player_stats(self):
        """Test getting player stats."""
        stats = self.factory.get_player_stats()
        
        assert stats is not None
        assert stats.hp == 100
        assert stats.power == 2
        assert stats.defense == 1


class TestGlobalEntityFactory:
    """Test global entity factory functions."""

    def test_get_entity_factory(self):
        """Test getting the global entity factory."""
        factory = get_entity_factory()
        assert isinstance(factory, EntityFactory)
        
        # Should return the same instance
        factory2 = get_entity_factory()
        assert factory is factory2

    def test_set_entity_factory(self):
        """Test setting a custom entity factory."""
        custom_factory = EntityFactory()
        set_entity_factory(custom_factory)
        
        factory = get_entity_factory()
        assert factory is custom_factory

    def teardown_method(self):
        """Clean up after tests."""
        # Reset global factory
        set_entity_factory(EntityFactory())
