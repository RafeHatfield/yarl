"""Tests for character screen functionality."""

import unittest
from unittest.mock import Mock

from components.fighter import Fighter
from components.equipment import Equipment
from components.equippable import Equippable
from equipment_slots import EquipmentSlots
from entity import Entity
from menus import _get_attack_display_text, _get_defense_display_text


class TestCharacterScreenDisplay:
    """Test character screen display functions."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create basic fighter and equipment
        self.fighter = Fighter(hp=100, defense=2, power=5)
        self.equipment = Equipment()
        
        # Create player entity
        self.player = Entity(0, 0, "@", (255, 255, 255), "Player")
        self.player.fighter = self.fighter
        self.player.equipment = self.equipment
        self.fighter.owner = self.player

    def test_attack_display_no_weapon(self):
        """Test attack display with no weapon equipped."""
        result = _get_attack_display_text(self.player)
        assert result == "Attack: 5"

    def test_attack_display_with_variable_damage_weapon(self):
        """Test attack display with variable damage weapon."""
        # Create weapon with variable damage
        weapon_equippable = Equippable(
            slot=EquipmentSlots.MAIN_HAND,
            power_bonus=2,
            damage_min=1,
            damage_max=4
        )
        weapon = Entity(0, 0, "/", (255, 255, 255), "Sword", equippable=weapon_equippable)
        
        # Equip weapon
        self.equipment.toggle_equip(weapon)
        
        result = _get_attack_display_text(self.player)
        # Should show: base power + weapon range = total range
        # 5 + 1-4 = 6-9
        assert result == "Attack: 5 + 1-4 = 6-9"

    def test_attack_display_with_power_bonus_only(self):
        """Test attack display with weapon that has power bonus but no damage range."""
        # Create weapon with only power bonus (legacy weapon)
        weapon_equippable = Equippable(
            slot=EquipmentSlots.MAIN_HAND,
            power_bonus=3
        )
        weapon = Entity(0, 0, "/", (255, 255, 255), "Sword", equippable=weapon_equippable)
        
        # Equip weapon
        self.equipment.toggle_equip(weapon)
        
        result = _get_attack_display_text(self.player)
        # Should show: base power + power bonus = total (fallback to power bonus since damage_max = 0)
        # 5 + 3 = 8
        assert result == "Attack: 5 + 3 = 8"

    def test_defense_display_no_armor(self):
        """Test defense display with no armor equipped."""
        result = _get_defense_display_text(self.player)
        assert result == "Defense: 2"

    def test_defense_display_with_variable_defense_armor(self):
        """Test defense display with variable defense armor."""
        # Create armor with variable defense
        armor_equippable = Equippable(
            slot=EquipmentSlots.OFF_HAND,
            defense_bonus=1,
            defense_min=1,
            defense_max=3
        )
        armor = Entity(0, 0, "[", (255, 255, 255), "Shield", equippable=armor_equippable)
        
        # Equip armor
        self.equipment.toggle_equip(armor)
        
        result = _get_defense_display_text(self.player)
        # Should show: base defense + armor range = total range
        # 2 + 1-3 = 3-5
        assert result == "Defense: 2 + 1-3 = 3-5"

    def test_defense_display_with_defense_bonus_only(self):
        """Test defense display with armor that has defense bonus but no defense range."""
        # Create armor with only defense bonus (legacy armor)
        armor_equippable = Equippable(
            slot=EquipmentSlots.OFF_HAND,
            defense_bonus=2
        )
        armor = Entity(0, 0, "[", (255, 255, 255), "Shield", equippable=armor_equippable)
        
        # Equip armor
        self.equipment.toggle_equip(armor)
        
        result = _get_defense_display_text(self.player)
        # Should show: base defense + defense bonus = total
        # 2 + 2 = 4
        assert result == "Defense: 2 + 2 = 4"

    def test_attack_display_with_both_power_bonus_and_damage_range(self):
        """Test attack display when weapon has both power bonus and damage range."""
        # Create weapon with both power bonus and damage range
        weapon_equippable = Equippable(
            slot=EquipmentSlots.MAIN_HAND,
            power_bonus=2,
            damage_min=2,
            damage_max=5
        )
        weapon = Entity(0, 0, "/", (255, 255, 255), "Sword", equippable=weapon_equippable)
        
        # Equip weapon
        self.equipment.toggle_equip(weapon)
        
        result = _get_attack_display_text(self.player)
        # Should prioritize damage range over power bonus
        # 5 + 2-5 = 7-10
        assert result == "Attack: 5 + 2-5 = 7-10"

    def test_defense_display_with_both_defense_bonus_and_defense_range(self):
        """Test defense display when armor has both defense bonus and defense range."""
        # Create armor with both defense bonus and defense range
        armor_equippable = Equippable(
            slot=EquipmentSlots.OFF_HAND,
            defense_bonus=1,
            defense_min=2,
            defense_max=4
        )
        armor = Entity(0, 0, "[", (255, 255, 255), "Shield", equippable=armor_equippable)
        
        # Equip armor
        self.equipment.toggle_equip(armor)
        
        result = _get_defense_display_text(self.player)
        # Should prioritize defense range over defense bonus
        # 2 + 2-4 = 4-6
        assert result == "Defense: 2 + 2-4 = 4-6"

    def test_attack_display_with_zero_damage_range(self):
        """Test attack display when weapon has zero damage range."""
        # Create weapon with zero damage range (should fall back to power bonus)
        weapon_equippable = Equippable(
            slot=EquipmentSlots.MAIN_HAND,
            power_bonus=3,
            damage_min=0,
            damage_max=0
        )
        weapon = Entity(0, 0, "/", (255, 255, 255), "Sword", equippable=weapon_equippable)
        
        # Equip weapon
        self.equipment.toggle_equip(weapon)
        
        result = _get_attack_display_text(self.player)
        # Should fall back to power bonus
        # 5 + 3 = 8
        assert result == "Attack: 5 + 3 = 8"

    def test_defense_display_with_zero_defense_range(self):
        """Test defense display when armor has zero defense range."""
        # Create armor with zero defense range (should fall back to defense bonus)
        armor_equippable = Equippable(
            slot=EquipmentSlots.OFF_HAND,
            defense_bonus=2,
            defense_min=0,
            defense_max=0
        )
        armor = Entity(0, 0, "[", (255, 255, 255), "Shield", equippable=armor_equippable)
        
        # Equip armor
        self.equipment.toggle_equip(armor)
        
        result = _get_defense_display_text(self.player)
        # Should fall back to defense bonus
        # 2 + 2 = 4
        assert result == "Defense: 2 + 2 = 4"
