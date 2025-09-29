"""
Unit tests for Fighter component integration with Equipment system.

Tests how Fighter stats are modified by equipped items:
- Base stats vs effective stats with equipment
- HP, power, and defense bonuses from equipment
- Equipment changes affecting combat calculations
- Integration between Fighter and Equipment components
"""

import pytest
from unittest.mock import Mock

from components.fighter import Fighter
from components.equipment import Equipment
from components.equippable import Equippable
from equipment_slots import EquipmentSlots
from entity import Entity


class TestFighterEquipmentIntegration:
    """Test Fighter integration with Equipment system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.fighter = Fighter(hp=100, defense=2, power=5)
        self.equipment = Equipment()

        # Create entity to link components
        self.entity = Mock()
        self.entity.equipment = self.equipment
        self.fighter.owner = self.entity

    def test_fighter_stats_without_equipment(self):
        """Test Fighter stats without any equipment."""
        # No equipment
        self.entity.equipment = None

        assert self.fighter.max_hp == 100
        assert self.fighter.power == 5
        assert self.fighter.defense == 2

    def test_fighter_stats_with_empty_equipment(self):
        """Test Fighter stats with empty equipment slots."""
        assert self.fighter.max_hp == 100
        assert self.fighter.power == 5
        assert self.fighter.defense == 2

    def test_fighter_power_bonus_from_weapon(self):
        """Test Fighter power bonus from equipped weapon."""
        # Create and equip weapon
        weapon = Mock()
        weapon.equippable = Mock()
        weapon.equippable.power_bonus = 3
        weapon.equippable.defense_bonus = 0
        weapon.equippable.max_hp_bonus = 0
        weapon.equippable.slot = EquipmentSlots.MAIN_HAND

        self.equipment.toggle_equip(weapon)

        assert self.fighter.power == 8  # 5 base + 3 bonus
        assert self.fighter.defense == 2  # unchanged
        assert self.fighter.max_hp == 100  # unchanged

    def test_fighter_defense_bonus_from_shield(self):
        """Test Fighter defense bonus from equipped shield."""
        # Create and equip shield
        shield = Mock()
        shield.equippable = Mock()
        shield.equippable.power_bonus = 0
        shield.equippable.defense_bonus = 2
        shield.equippable.max_hp_bonus = 0
        shield.equippable.slot = EquipmentSlots.OFF_HAND

        self.equipment.toggle_equip(shield)

        assert self.fighter.power == 5  # unchanged
        assert self.fighter.defense == 4  # 2 base + 2 bonus
        assert self.fighter.max_hp == 100  # unchanged

    def test_fighter_hp_bonus_from_equipment(self):
        """Test Fighter max HP bonus from equipped items."""
        # Create item with HP bonus
        hp_item = Mock()
        hp_item.equippable = Mock()
        hp_item.equippable.power_bonus = 0
        hp_item.equippable.defense_bonus = 0
        hp_item.equippable.max_hp_bonus = 20
        hp_item.equippable.slot = EquipmentSlots.OFF_HAND

        self.equipment.toggle_equip(hp_item)

        assert self.fighter.power == 5  # unchanged
        assert self.fighter.defense == 2  # unchanged
        assert self.fighter.max_hp == 120  # 100 base + 20 bonus

    def test_fighter_multiple_equipment_bonuses(self):
        """Test Fighter with multiple equipment pieces providing bonuses."""
        # Create weapon with power and defense bonus
        weapon = Mock()
        weapon.equippable = Mock()
        weapon.equippable.power_bonus = 4
        weapon.equippable.defense_bonus = 1
        weapon.equippable.max_hp_bonus = 10
        weapon.equippable.slot = EquipmentSlots.MAIN_HAND

        # Create shield with defense and HP bonus
        shield = Mock()
        shield.equippable = Mock()
        shield.equippable.power_bonus = 0
        shield.equippable.defense_bonus = 3
        shield.equippable.max_hp_bonus = 15
        shield.equippable.slot = EquipmentSlots.OFF_HAND

        self.equipment.toggle_equip(weapon)
        self.equipment.toggle_equip(shield)

        assert self.fighter.power == 9  # 5 + 4 + 0
        assert self.fighter.defense == 6  # 2 + 1 + 3
        assert self.fighter.max_hp == 125  # 100 + 10 + 15

    def test_fighter_equipment_change_updates_stats(self):
        """Test that changing equipment updates Fighter stats."""
        # Equip initial weapon
        weak_weapon = Mock()
        weak_weapon.equippable = Mock()
        weak_weapon.equippable.power_bonus = 2
        weak_weapon.equippable.defense_bonus = 0
        weak_weapon.equippable.max_hp_bonus = 0
        weak_weapon.equippable.slot = EquipmentSlots.MAIN_HAND

        self.equipment.toggle_equip(weak_weapon)
        assert self.fighter.power == 7  # 5 + 2

        # Replace with stronger weapon
        strong_weapon = Mock()
        strong_weapon.equippable = Mock()
        strong_weapon.equippable.power_bonus = 5
        strong_weapon.equippable.defense_bonus = 0
        strong_weapon.equippable.max_hp_bonus = 0
        strong_weapon.equippable.slot = EquipmentSlots.MAIN_HAND

        self.equipment.toggle_equip(strong_weapon)
        assert self.fighter.power == 10  # 5 + 5

    def test_fighter_unequip_removes_bonuses(self):
        """Test that unequipping items removes their bonuses."""
        # Equip weapon
        weapon = Mock()
        weapon.equippable = Mock()
        weapon.equippable.power_bonus = 3
        weapon.equippable.defense_bonus = 1
        weapon.equippable.max_hp_bonus = 5
        weapon.equippable.slot = EquipmentSlots.MAIN_HAND

        self.equipment.toggle_equip(weapon)
        assert self.fighter.power == 8  # 5 + 3
        assert self.fighter.defense == 3  # 2 + 1
        assert self.fighter.max_hp == 105  # 100 + 5

        # Unequip weapon
        self.equipment.toggle_equip(weapon)
        assert self.fighter.power == 5  # back to base
        assert self.fighter.defense == 2  # back to base
        assert self.fighter.max_hp == 100  # back to base

    def test_fighter_negative_equipment_bonuses(self):
        """Test Fighter with cursed equipment (negative bonuses)."""
        # Create cursed item
        cursed_item = Mock()
        cursed_item.equippable = Mock()
        cursed_item.equippable.power_bonus = -1
        cursed_item.equippable.defense_bonus = -2
        cursed_item.equippable.max_hp_bonus = -10
        cursed_item.equippable.slot = EquipmentSlots.MAIN_HAND

        self.equipment.toggle_equip(cursed_item)

        assert self.fighter.power == 4  # 5 - 1
        assert self.fighter.defense == 0  # 2 - 2
        assert self.fighter.max_hp == 90  # 100 - 10

    def test_fighter_base_stats_unchanged_by_equipment(self):
        """Test that base stats remain unchanged when equipment is added."""
        # Equip powerful item
        powerful_item = Mock()
        powerful_item.equippable = Mock()
        powerful_item.equippable.power_bonus = 10
        powerful_item.equippable.defense_bonus = 5
        powerful_item.equippable.max_hp_bonus = 50
        powerful_item.equippable.slot = EquipmentSlots.MAIN_HAND

        self.equipment.toggle_equip(powerful_item)

        # Effective stats should change
        assert self.fighter.power == 15  # 5 + 10
        assert self.fighter.defense == 7  # 2 + 5
        assert self.fighter.max_hp == 150  # 100 + 50

        # Base stats should remain unchanged
        assert self.fighter.base_power == 5
        assert self.fighter.base_defense == 2
        assert self.fighter.base_max_hp == 100


class TestFighterEquipmentCombat:
    """Test Fighter combat calculations with equipment bonuses."""

    def setup_method(self):
        """Set up test fixtures for combat testing."""
        # Create attacker with equipment
        self.attacker_fighter = Fighter(hp=100, defense=1, power=5)
        self.attacker_equipment = Equipment()
        self.attacker = Mock()
        self.attacker.name = "Attacker"
        self.attacker.equipment = self.attacker_equipment
        self.attacker_fighter.owner = self.attacker

        # Create target with equipment
        self.target_fighter = Fighter(hp=50, defense=2, power=3)
        self.target_equipment = Equipment()
        self.target = Mock()
        self.target.name = "Target"
        self.target.equipment = self.target_equipment
        self.target.fighter = (
            self.target_fighter
        )  # Add fighter reference for attack method
        self.target_fighter.owner = self.target

    def test_combat_with_weapon_bonus(self):
        """Test combat damage calculation with weapon bonus."""
        # Equip weapon to attacker
        weapon = Mock()
        weapon.equippable = Mock()
        weapon.equippable.power_bonus = 3
        weapon.equippable.defense_bonus = 0
        weapon.equippable.max_hp_bonus = 0
        weapon.equippable.slot = EquipmentSlots.MAIN_HAND
        weapon.equippable.roll_damage.return_value = 3  # Return weapon damage as integer

        self.attacker_equipment.toggle_equip(weapon)

        # Attack should use enhanced power
        results = self.attacker_fighter.attack(self.target)

        # Damage = ((5 base + 3 power_bonus) - 2 defense) + 3 weapon_damage = 9
        # Base damage: (5 + 3) - 2 = 6, Weapon damage: 3, Total: 6 + 3 = 9
        expected_damage = 9
        assert self.target_fighter.hp == 50 - expected_damage

    def test_combat_with_armor_bonus(self):
        """Test combat damage reduction with armor bonus."""
        # Equip armor to target
        armor = Mock()
        armor.equippable = Mock()
        armor.equippable.power_bonus = 0
        armor.equippable.defense_bonus = 3
        armor.equippable.max_hp_bonus = 0
        armor.equippable.slot = EquipmentSlots.OFF_HAND

        self.target_equipment.toggle_equip(armor)

        # Attack should be reduced by enhanced defense
        results = self.attacker_fighter.attack(self.target)

        # Damage = 5 power - (2 base + 3 armor) = 0 (minimum)
        # No damage should be dealt
        assert self.target_fighter.hp == 50

    def test_combat_with_both_weapon_and_armor(self):
        """Test combat with both attacker weapon and target armor."""
        # Equip weapon to attacker
        weapon = Mock()
        weapon.equippable = Mock()
        weapon.equippable.power_bonus = 4
        weapon.equippable.defense_bonus = 0
        weapon.equippable.max_hp_bonus = 0
        weapon.equippable.slot = EquipmentSlots.MAIN_HAND
        weapon.equippable.roll_damage.return_value = 4  # Return weapon damage as integer

        self.attacker_equipment.toggle_equip(weapon)

        # Equip armor to target
        armor = Mock()
        armor.equippable = Mock()
        armor.equippable.power_bonus = 0
        armor.equippable.defense_bonus = 2
        armor.equippable.max_hp_bonus = 0
        armor.equippable.slot = EquipmentSlots.OFF_HAND

        self.target_equipment.toggle_equip(armor)

        # Attack with both bonuses
        results = self.attacker_fighter.attack(self.target)

        # Damage = ((5 base + 4 power_bonus) - (2 base + 2 defense_bonus)) + 4 weapon_damage = 9
        # Base damage: (5 + 4) - (2 + 2) = 5, Weapon damage: 4, Total: 5 + 4 = 9
        expected_damage = 9
        assert self.target_fighter.hp == 50 - expected_damage

    def test_healing_with_hp_bonus_equipment(self):
        """Test healing respects max HP bonus from equipment."""
        # Damage the fighter first
        self.attacker_fighter.hp = 50

        # Equip item with HP bonus
        hp_item = Mock()
        hp_item.equippable = Mock()
        hp_item.equippable.power_bonus = 0
        hp_item.equippable.defense_bonus = 0
        hp_item.equippable.max_hp_bonus = 25
        hp_item.equippable.slot = EquipmentSlots.OFF_HAND

        self.attacker_equipment.toggle_equip(hp_item)

        # Heal should respect new max HP (100 + 25 = 125)
        self.attacker_fighter.heal(100)  # Heal for more than max

        assert self.attacker_fighter.hp == 125  # Should cap at new max HP


class TestFighterEquipmentRealItems:
    """Test Fighter with realistic equipment configurations."""

    def setup_method(self):
        """Set up test fixtures with realistic items."""
        self.fighter = Fighter(hp=100, defense=1, power=2)  # Starting player stats
        self.equipment = Equipment()

        self.entity = Mock()
        self.entity.equipment = self.equipment
        self.fighter.owner = self.entity

    def test_fighter_with_starting_dagger(self):
        """Test Fighter with starting dagger (as in game initialization)."""
        # Create dagger like in initialize_new_game.py
        dagger_equippable = Equippable(EquipmentSlots.MAIN_HAND, power_bonus=2)
        dagger = Mock()
        dagger.equippable = dagger_equippable

        self.equipment.toggle_equip(dagger)

        assert self.fighter.power == 4  # 2 base + 2 dagger
        assert self.fighter.defense == 1  # unchanged
        assert self.fighter.max_hp == 100  # unchanged

    def test_fighter_with_sword_upgrade(self):
        """Test Fighter upgrading from dagger to sword."""
        # Start with dagger
        dagger_equippable = Equippable(EquipmentSlots.MAIN_HAND, power_bonus=2)
        dagger = Mock()
        dagger.equippable = dagger_equippable

        self.equipment.toggle_equip(dagger)
        assert self.fighter.power == 4

        # Upgrade to sword (as spawned in game_map.py)
        sword_equippable = Equippable(EquipmentSlots.MAIN_HAND, power_bonus=3)
        sword = Mock()
        sword.equippable = sword_equippable

        self.equipment.toggle_equip(sword)
        assert self.fighter.power == 5  # 2 base + 3 sword

    def test_fighter_with_shield_addition(self):
        """Test Fighter adding shield to weapon."""
        # Start with sword
        sword_equippable = Equippable(EquipmentSlots.MAIN_HAND, power_bonus=3)
        sword = Mock()
        sword.equippable = sword_equippable

        self.equipment.toggle_equip(sword)

        # Add shield (as spawned in game_map.py)
        shield_equippable = Equippable(EquipmentSlots.OFF_HAND, defense_bonus=1)
        shield = Mock()
        shield.equippable = shield_equippable

        self.equipment.toggle_equip(shield)

        assert self.fighter.power == 5  # 2 + 3 sword
        assert self.fighter.defense == 2  # 1 + 1 shield
        assert self.fighter.max_hp == 100

    def test_fighter_full_equipment_loadout(self):
        """Test Fighter with full equipment loadout."""
        # Equip magic sword with multiple bonuses
        magic_sword_equippable = Equippable(
            EquipmentSlots.MAIN_HAND, power_bonus=5, defense_bonus=1, max_hp_bonus=20
        )
        magic_sword = Mock()
        magic_sword.equippable = magic_sword_equippable

        # Equip tower shield with defense and HP
        tower_shield_equippable = Equippable(
            EquipmentSlots.OFF_HAND, defense_bonus=3, max_hp_bonus=15
        )
        tower_shield = Mock()
        tower_shield.equippable = tower_shield_equippable

        self.equipment.toggle_equip(magic_sword)
        self.equipment.toggle_equip(tower_shield)

        assert self.fighter.power == 7  # 2 + 5
        assert self.fighter.defense == 5  # 1 + 1 + 3
        assert self.fighter.max_hp == 135  # 100 + 20 + 15
