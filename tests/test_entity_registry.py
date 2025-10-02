"""Tests for the entity registry system.

This module tests the entity configuration loading, validation, and lookup
functionality provided by the EntityRegistry class.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from config.entity_registry import (
    EntityRegistry,
    EntityStats,
    MonsterDefinition,
    WeaponDefinition,
    ArmorDefinition,
    SpellDefinition,
    get_entity_registry,
    load_entity_config
)


class TestEntityStats:
    """Test EntityStats validation and creation."""

    def test_valid_entity_stats(self):
        """Test creating valid entity stats."""
        stats = EntityStats(hp=100, power=5, defense=2, xp=50)
        assert stats.hp == 100
        assert stats.power == 5
        assert stats.defense == 2
        assert stats.xp == 50

    def test_entity_stats_with_damage_range(self):
        """Test entity stats with valid damage range."""
        stats = EntityStats(
            hp=20, power=4, defense=0, xp=35,
            damage_min=2, damage_max=6
        )
        assert stats.damage_min == 2
        assert stats.damage_max == 6

    def test_entity_stats_with_defense_range(self):
        """Test entity stats with valid defense range."""
        stats = EntityStats(
            hp=20, power=4, defense=0, xp=35,
            defense_min=1, defense_max=3
        )
        assert stats.defense_min == 1
        assert stats.defense_max == 3

    def test_invalid_hp_raises_error(self):
        """Test that invalid HP raises ValueError."""
        with pytest.raises(ValueError, match="Entity HP must be >= 1"):
            EntityStats(hp=0, power=5, defense=2)

    def test_negative_power_raises_error(self):
        """Test that negative power raises ValueError."""
        with pytest.raises(ValueError, match="Entity power must be >= 0"):
            EntityStats(hp=100, power=-1, defense=2)

    def test_negative_defense_raises_error(self):
        """Test that negative defense raises ValueError."""
        with pytest.raises(ValueError, match="Entity defense must be >= 0"):
            EntityStats(hp=100, power=5, defense=-1)

    def test_negative_xp_raises_error(self):
        """Test that negative XP raises ValueError."""
        with pytest.raises(ValueError, match="Entity XP must be >= 0"):
            EntityStats(hp=100, power=5, defense=2, xp=-10)

    def test_invalid_damage_range_raises_error(self):
        """Test that invalid damage range raises ValueError."""
        with pytest.raises(ValueError, match="damage_min .* cannot be greater than damage_max"):
            EntityStats(hp=20, power=4, defense=0, damage_min=6, damage_max=2)

    def test_negative_damage_min_raises_error(self):
        """Test that negative damage_min raises ValueError."""
        with pytest.raises(ValueError, match="damage_min must be >= 0"):
            EntityStats(hp=20, power=4, defense=0, damage_min=-1, damage_max=5)

    def test_invalid_defense_range_raises_error(self):
        """Test that invalid defense range raises ValueError."""
        with pytest.raises(ValueError, match="defense_min .* cannot be greater than defense_max"):
            EntityStats(hp=20, power=4, defense=0, defense_min=3, defense_max=1)

    def test_negative_defense_min_raises_error(self):
        """Test that negative defense_min raises ValueError."""
        with pytest.raises(ValueError, match="defense_min must be >= 0"):
            EntityStats(hp=20, power=4, defense=0, defense_min=-1, defense_max=3)


class TestWeaponDefinition:
    """Test WeaponDefinition validation."""

    def test_valid_weapon_definition(self):
        """Test creating valid weapon definition."""
        weapon = WeaponDefinition(
            name="Sword",
            power_bonus=3,
            damage_min=2,
            damage_max=5,
            slot="main_hand"
        )
        assert weapon.name == "Sword"
        assert weapon.power_bonus == 3
        assert weapon.damage_min == 2
        assert weapon.damage_max == 5
        assert weapon.slot == "main_hand"

    def test_negative_power_bonus_raises_error(self):
        """Test that negative power bonus raises ValueError."""
        with pytest.raises(ValueError, match="Weapon power_bonus must be >= 0"):
            WeaponDefinition(name="Bad Weapon", power_bonus=-1)

    def test_negative_damage_min_raises_error(self):
        """Test that negative damage_min raises ValueError."""
        with pytest.raises(ValueError, match="Weapon damage_min must be >= 0"):
            WeaponDefinition(name="Bad Weapon", damage_min=-1)

    def test_invalid_damage_range_raises_error(self):
        """Test that invalid damage range raises ValueError."""
        with pytest.raises(ValueError, match="Weapon damage_max .* cannot be less than damage_min"):
            WeaponDefinition(name="Bad Weapon", damage_min=5, damage_max=2)

    def test_invalid_slot_raises_error(self):
        """Test that invalid slot raises ValueError."""
        with pytest.raises(ValueError, match="Weapon slot must be 'main_hand' or 'off_hand'"):
            WeaponDefinition(name="Bad Weapon", slot="invalid_slot")


class TestArmorDefinition:
    """Test ArmorDefinition validation."""

    def test_valid_armor_definition(self):
        """Test creating valid armor definition."""
        armor = ArmorDefinition(
            name="Shield",
            defense_bonus=2,
            defense_min=1,
            defense_max=3,
            slot="off_hand"
        )
        assert armor.name == "Shield"
        assert armor.defense_bonus == 2
        assert armor.defense_min == 1
        assert armor.defense_max == 3
        assert armor.slot == "off_hand"

    def test_negative_defense_bonus_raises_error(self):
        """Test that negative defense bonus raises ValueError."""
        with pytest.raises(ValueError, match="Armor defense_bonus must be >= 0"):
            ArmorDefinition(name="Bad Armor", defense_bonus=-1)

    def test_invalid_defense_range_raises_error(self):
        """Test that invalid defense range raises ValueError."""
        with pytest.raises(ValueError, match="Armor defense_max .* cannot be less than defense_min"):
            ArmorDefinition(name="Bad Armor", defense_min=3, defense_max=1)


class TestSpellDefinition:
    """Test SpellDefinition validation."""

    def test_valid_spell_definition(self):
        """Test creating valid spell definition."""
        spell = SpellDefinition(
            name="Lightning Bolt",
            spell_type="damage",
            damage=40,
            maximum_range=5
        )
        assert spell.name == "Lightning Bolt"
        assert spell.spell_type == "damage"
        assert spell.damage == 40
        assert spell.maximum_range == 5

    def test_healing_spell_definition(self):
        """Test creating valid healing spell definition."""
        spell = SpellDefinition(
            name="Healing Potion",
            spell_type="heal",
            heal_amount=40
        )
        assert spell.name == "Healing Potion"
        assert spell.spell_type == "heal"
        assert spell.heal_amount == 40

    def test_negative_damage_raises_error(self):
        """Test that negative damage raises ValueError."""
        with pytest.raises(ValueError, match="Spell damage must be >= 0"):
            SpellDefinition(name="Bad Spell", spell_type="damage", damage=-10)

    def test_negative_heal_amount_raises_error(self):
        """Test that negative heal amount raises ValueError."""
        with pytest.raises(ValueError, match="Spell heal_amount must be >= 0"):
            SpellDefinition(name="Bad Spell", spell_type="heal", heal_amount=-10)


class TestEntityRegistry:
    """Test EntityRegistry functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = EntityRegistry()
        
        # Create a test configuration
        self.test_config = {
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
                "test_heal": {
                    "spell_type": "heal",
                    "heal_amount": 40,
                    "char": "!",
                    "color": [127, 0, 255]
                }
            }
        }

    def test_empty_registry_initially(self):
        """Test that registry starts empty."""
        assert len(self.registry.monsters) == 0
        assert len(self.registry.weapons) == 0
        assert len(self.registry.armor) == 0
        assert len(self.registry.spells) == 0
        assert self.registry.player_stats is None
        assert not self.registry.is_loaded()

    def test_process_config_data(self):
        """Test processing configuration data."""
        self.registry._process_config_data(self.test_config)
        
        # Check player stats
        assert self.registry.player_stats is not None
        assert self.registry.player_stats.hp == 100
        assert self.registry.player_stats.power == 2
        
        # Check monster
        assert "test_orc" in self.registry.monsters
        orc = self.registry.monsters["test_orc"]
        assert orc.name == "Test_Orc"
        assert orc.stats.hp == 20
        assert orc.char == "o"
        
        # Check weapon
        assert "test_sword" in self.registry.weapons
        sword = self.registry.weapons["test_sword"]
        assert sword.name == "Test_Sword"
        assert sword.power_bonus == 3
        assert sword.damage_min == 2
        
        # Check armor
        assert "test_shield" in self.registry.armor
        shield = self.registry.armor["test_shield"]
        assert shield.name == "Test_Shield"
        assert shield.defense_bonus == 1
        
        # Check spell
        assert "test_heal" in self.registry.spells
        heal = self.registry.spells["test_heal"]
        assert heal.name == "Test Heal"  # Uses .replace('_', ' ').title()
        assert heal.heal_amount == 40

    def test_get_methods(self):
        """Test entity lookup methods."""
        self.registry._process_config_data(self.test_config)
        
        # Test successful lookups
        assert self.registry.get_monster("test_orc") is not None
        assert self.registry.get_weapon("test_sword") is not None
        assert self.registry.get_armor("test_shield") is not None
        assert self.registry.get_spell("test_heal") is not None
        assert self.registry.get_player_stats() is not None
        
        # Test failed lookups
        assert self.registry.get_monster("nonexistent") is None
        assert self.registry.get_weapon("nonexistent") is None
        assert self.registry.get_armor("nonexistent") is None
        assert self.registry.get_spell("nonexistent") is None

    def test_get_all_ids_methods(self):
        """Test methods that return all entity IDs."""
        self.registry._process_config_data(self.test_config)
        
        assert "test_orc" in self.registry.get_all_monster_ids()
        assert "test_sword" in self.registry.get_all_weapon_ids()
        assert "test_shield" in self.registry.get_all_armor_ids()
        assert "test_heal" in self.registry.get_all_spell_ids()

    def test_load_from_file_success(self):
        """Test successful file loading."""
        # Create temporary YAML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
version: "1.0"
player:
  hp: 100
  power: 2
  defense: 1
monsters:
  orc:
    stats:
      hp: 20
      power: 4
      defense: 0
      xp: 35
    char: "o"
    color: [63, 127, 63]
""")
            temp_file = f.name

        try:
            self.registry.load_from_file(temp_file)
            
            assert self.registry.is_loaded()
            assert self.registry.get_monster("orc") is not None
            assert self.registry.get_player_stats() is not None
            
        finally:
            os.unlink(temp_file)

    def test_load_from_file_not_found(self):
        """Test file not found error."""
        with pytest.raises(FileNotFoundError, match="Entity configuration file not found"):
            self.registry.load_from_file("nonexistent.yaml")

    @patch('config.entity_registry.YAML_AVAILABLE', False)
    def test_load_from_file_no_yaml_support(self):
        """Test error when YAML support is not available."""
        with pytest.raises(RuntimeError, match="YAML support not available"):
            self.registry.load_from_file("test.yaml")

    def test_invalid_player_stats_raises_error(self):
        """Test that invalid player stats raise appropriate errors."""
        invalid_config = {
            "player": {
                "hp": -10,  # Invalid HP
                "power": 2,
                "defense": 1
            }
        }
        
        with pytest.raises(ValueError, match="Invalid player configuration"):
            self.registry._process_config_data(invalid_config)

    def test_invalid_monster_stats_raises_error(self):
        """Test that invalid monster configuration raises errors."""
        invalid_config = {
            "monsters": {
                "bad_orc": {
                    "stats": {
                        "hp": -10,  # Invalid HP
                        "power": 4,
                        "defense": 0
                    },
                    "char": "o",
                    "color": [63, 127, 63]
                }
            }
        }
        
        with pytest.raises(ValueError, match="Invalid.*monster configuration"):
            self.registry._process_config_data(invalid_config)


class TestEntityRegistryIntegration:
    """Integration tests for the entity registry system."""

    def test_load_actual_config_file(self):
        """Test loading the actual entities.yaml configuration file."""
        # Get path to actual config file
        config_dir = Path(__file__).parent.parent / "config"
        config_path = config_dir / "entities.yaml"
        
        if config_path.exists():
            registry = EntityRegistry()
            registry.load_from_file(str(config_path))
            
            # Verify expected entities are loaded
            assert registry.is_loaded()
            assert registry.get_player_stats() is not None
            
            # Check for expected monsters
            assert registry.get_monster("orc") is not None
            assert registry.get_monster("troll") is not None
            
            # Check for expected weapons
            assert registry.get_weapon("dagger") is not None
            assert registry.get_weapon("sword") is not None
            
            # Check for expected armor
            assert registry.get_armor("shield") is not None

    def test_config_values_match_hardcoded_values(self):
        """Test that configuration values match current hardcoded values.
        
        This test ensures we maintain backward compatibility during migration.
        """
        config_dir = Path(__file__).parent.parent / "config"
        config_path = config_dir / "entities.yaml"
        
        if config_path.exists():
            registry = EntityRegistry()
            registry.load_from_file(str(config_path))
            
            # Verify player stats match current values (updated for new power system)
            player_stats = registry.get_player_stats()
            assert player_stats.hp == 60  # Updated: rebalanced for d20 combat
            assert player_stats.power == 0  # Updated: new power system baseline
            assert player_stats.defense == 1
            
            # Verify orc stats match current values (updated for new power system)
            orc = registry.get_monster("orc")
            assert orc.stats.hp == 20
            assert orc.stats.power == 0  # Updated: new power system baseline
            assert orc.stats.defense == 0
            assert orc.stats.xp == 35
            
            # Verify troll stats match current values (updated for new power system)
            troll = registry.get_monster("troll")
            assert troll.stats.hp == 30
            assert troll.stats.power == 0  # Updated: new power system baseline
            assert troll.stats.defense == 2
            assert troll.stats.xp == 100
            
            # Verify weapon stats use new dice system
            dagger = registry.get_weapon("dagger")
            assert dagger.power_bonus == 0
            assert dagger.damage_dice == "1d4"
            assert dagger.damage_min == 1  # Calculated from 1d4
            assert dagger.damage_max == 4
            assert dagger.to_hit_bonus == 1  # Finesse weapon
            
            sword = registry.get_weapon("sword")
            assert sword.power_bonus == 0
            assert sword.damage_dice == "1d8"
            assert sword.damage_min == 1  # Calculated from 1d8
            assert sword.damage_max == 8
            
            # Verify armor stats match hardcoded values
            shield = registry.get_armor("shield")
            assert shield.defense_bonus == 0  # Basic armor no longer has magic bonuses
            assert shield.defense_min == 1
            assert shield.defense_max == 3


class TestGlobalEntityRegistry:
    """Test global entity registry functions."""

    def test_get_entity_registry(self):
        """Test getting the global entity registry."""
        registry = get_entity_registry()
        assert isinstance(registry, EntityRegistry)
        
        # Should return the same instance
        registry2 = get_entity_registry()
        assert registry is registry2

    @patch('config.entity_registry._entity_registry')
    def test_load_entity_config_default_path(self, mock_registry):
        """Test loading entity config with default path."""
        mock_registry.load_from_file = MagicMock()
        
        load_entity_config()
        
        # Should call load_from_file with default path
        mock_registry.load_from_file.assert_called_once()
        args = mock_registry.load_from_file.call_args[0]
        assert args[0].endswith("entities.yaml")

    @patch('config.entity_registry._entity_registry')
    def test_load_entity_config_custom_path(self, mock_registry):
        """Test loading entity config with custom path."""
        mock_registry.load_from_file = MagicMock()
        
        load_entity_config("custom/path.yaml")
        
        mock_registry.load_from_file.assert_called_once_with("custom/path.yaml")
