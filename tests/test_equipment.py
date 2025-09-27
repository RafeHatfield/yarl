"""
Unit tests for Equipment component.

Tests the equipment system including:
- Equipment slot management (main hand, off hand)
- Stat bonus calculations (HP, power, defense)
- Equipment toggling (equip/unequip)
- Equipment swapping and replacement
"""

import pytest
from unittest.mock import Mock

from components.equipment import Equipment
from components.equippable import Equippable
from equipment_slots import EquipmentSlots
from entity import Entity


class TestEquipment:
    """Test Equipment component functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.equipment = Equipment()

    def test_equipment_initialization(self):
        """Test Equipment component initializes correctly."""
        assert self.equipment.main_hand is None
        assert self.equipment.off_hand is None

    def test_equipment_initialization_with_items(self):
        """Test Equipment component initializes with items."""
        main_hand = Mock()
        off_hand = Mock()
        equipment = Equipment(main_hand=main_hand, off_hand=off_hand)
        
        assert equipment.main_hand == main_hand
        assert equipment.off_hand == off_hand

    def test_max_hp_bonus_no_equipment(self):
        """Test max HP bonus with no equipment."""
        assert self.equipment.max_hp_bonus == 0

    def test_max_hp_bonus_main_hand_only(self):
        """Test max HP bonus with main hand equipment only."""
        main_hand = Mock()
        main_hand.equippable = Mock()
        main_hand.equippable.max_hp_bonus = 10
        
        self.equipment.main_hand = main_hand
        
        assert self.equipment.max_hp_bonus == 10

    def test_max_hp_bonus_off_hand_only(self):
        """Test max HP bonus with off hand equipment only."""
        off_hand = Mock()
        off_hand.equippable = Mock()
        off_hand.equippable.max_hp_bonus = 5
        
        self.equipment.off_hand = off_hand
        
        assert self.equipment.max_hp_bonus == 5

    def test_max_hp_bonus_both_hands(self):
        """Test max HP bonus with both hands equipped."""
        main_hand = Mock()
        main_hand.equippable = Mock()
        main_hand.equippable.max_hp_bonus = 10
        
        off_hand = Mock()
        off_hand.equippable = Mock()
        off_hand.equippable.max_hp_bonus = 5
        
        self.equipment.main_hand = main_hand
        self.equipment.off_hand = off_hand
        
        assert self.equipment.max_hp_bonus == 15

    def test_max_hp_bonus_no_equippable_component(self):
        """Test max HP bonus with equipment that has no equippable component."""
        main_hand = Mock()
        main_hand.equippable = None
        
        self.equipment.main_hand = main_hand
        
        assert self.equipment.max_hp_bonus == 0

    def test_power_bonus_no_equipment(self):
        """Test power bonus with no equipment."""
        assert self.equipment.power_bonus == 0

    def test_power_bonus_main_hand_only(self):
        """Test power bonus with main hand equipment only."""
        main_hand = Mock()
        main_hand.equippable = Mock()
        main_hand.equippable.power_bonus = 3
        
        self.equipment.main_hand = main_hand
        
        assert self.equipment.power_bonus == 3

    def test_power_bonus_off_hand_only(self):
        """Test power bonus with off hand equipment only."""
        off_hand = Mock()
        off_hand.equippable = Mock()
        off_hand.equippable.power_bonus = 1
        
        self.equipment.off_hand = off_hand
        
        assert self.equipment.power_bonus == 1

    def test_power_bonus_both_hands(self):
        """Test power bonus with both hands equipped."""
        main_hand = Mock()
        main_hand.equippable = Mock()
        main_hand.equippable.power_bonus = 3
        
        off_hand = Mock()
        off_hand.equippable = Mock()
        off_hand.equippable.power_bonus = 1
        
        self.equipment.main_hand = main_hand
        self.equipment.off_hand = off_hand
        
        assert self.equipment.power_bonus == 4

    def test_defense_bonus_no_equipment(self):
        """Test defense bonus with no equipment."""
        assert self.equipment.defense_bonus == 0

    def test_defense_bonus_main_hand_only(self):
        """Test defense bonus with main hand equipment only."""
        main_hand = Mock()
        main_hand.equippable = Mock()
        main_hand.equippable.defense_bonus = 1
        
        self.equipment.main_hand = main_hand
        
        assert self.equipment.defense_bonus == 1

    def test_defense_bonus_off_hand_only(self):
        """Test defense bonus with off hand equipment only."""
        off_hand = Mock()
        off_hand.equippable = Mock()
        off_hand.equippable.defense_bonus = 2
        
        self.equipment.off_hand = off_hand
        
        assert self.equipment.defense_bonus == 2

    def test_defense_bonus_both_hands(self):
        """Test defense bonus with both hands equipped."""
        main_hand = Mock()
        main_hand.equippable = Mock()
        main_hand.equippable.defense_bonus = 1
        
        off_hand = Mock()
        off_hand.equippable = Mock()
        off_hand.equippable.defense_bonus = 2
        
        self.equipment.main_hand = main_hand
        self.equipment.off_hand = off_hand
        
        assert self.equipment.defense_bonus == 3


class TestEquipmentToggling:
    """Test equipment toggling functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.equipment = Equipment()

    def test_equip_main_hand_empty_slot(self):
        """Test equipping item to empty main hand slot."""
        weapon = Mock()
        weapon.equippable = Mock()
        weapon.equippable.slot = EquipmentSlots.MAIN_HAND
        
        results = self.equipment.toggle_equip(weapon)
        
        assert self.equipment.main_hand == weapon
        assert len(results) == 1
        assert results[0]['equipped'] == weapon

    def test_equip_off_hand_empty_slot(self):
        """Test equipping item to empty off hand slot."""
        shield = Mock()
        shield.equippable = Mock()
        shield.equippable.slot = EquipmentSlots.OFF_HAND
        
        results = self.equipment.toggle_equip(shield)
        
        assert self.equipment.off_hand == shield
        assert len(results) == 1
        assert results[0]['equipped'] == shield

    def test_unequip_main_hand(self):
        """Test unequipping item from main hand."""
        weapon = Mock()
        weapon.equippable = Mock()
        weapon.equippable.slot = EquipmentSlots.MAIN_HAND
        
        # First equip
        self.equipment.toggle_equip(weapon)
        assert self.equipment.main_hand == weapon
        
        # Then unequip
        results = self.equipment.toggle_equip(weapon)
        
        assert self.equipment.main_hand is None
        assert len(results) == 1
        assert results[0]['dequipped'] == weapon

    def test_unequip_off_hand(self):
        """Test unequipping item from off hand."""
        shield = Mock()
        shield.equippable = Mock()
        shield.equippable.slot = EquipmentSlots.OFF_HAND
        
        # First equip
        self.equipment.toggle_equip(shield)
        assert self.equipment.off_hand == shield
        
        # Then unequip
        results = self.equipment.toggle_equip(shield)
        
        assert self.equipment.off_hand is None
        assert len(results) == 1
        assert results[0]['dequipped'] == shield

    def test_replace_main_hand_equipment(self):
        """Test replacing main hand equipment with new item."""
        old_weapon = Mock()
        old_weapon.equippable = Mock()
        old_weapon.equippable.slot = EquipmentSlots.MAIN_HAND
        
        new_weapon = Mock()
        new_weapon.equippable = Mock()
        new_weapon.equippable.slot = EquipmentSlots.MAIN_HAND
        
        # Equip first weapon
        self.equipment.toggle_equip(old_weapon)
        assert self.equipment.main_hand == old_weapon
        
        # Replace with new weapon
        results = self.equipment.toggle_equip(new_weapon)
        
        assert self.equipment.main_hand == new_weapon
        assert len(results) == 2
        assert results[0]['dequipped'] == old_weapon
        assert results[1]['equipped'] == new_weapon

    def test_replace_off_hand_equipment(self):
        """Test replacing off hand equipment with new item."""
        old_shield = Mock()
        old_shield.equippable = Mock()
        old_shield.equippable.slot = EquipmentSlots.OFF_HAND
        
        new_shield = Mock()
        new_shield.equippable = Mock()
        new_shield.equippable.slot = EquipmentSlots.OFF_HAND
        
        # Equip first shield
        self.equipment.toggle_equip(old_shield)
        assert self.equipment.off_hand == old_shield
        
        # Replace with new shield
        results = self.equipment.toggle_equip(new_shield)
        
        assert self.equipment.off_hand == new_shield
        assert len(results) == 2
        assert results[0]['dequipped'] == old_shield
        assert results[1]['equipped'] == new_shield

    def test_equip_multiple_different_slots(self):
        """Test equipping items to different slots simultaneously."""
        weapon = Mock()
        weapon.equippable = Mock()
        weapon.equippable.slot = EquipmentSlots.MAIN_HAND
        
        shield = Mock()
        shield.equippable = Mock()
        shield.equippable.slot = EquipmentSlots.OFF_HAND
        
        # Equip weapon
        weapon_results = self.equipment.toggle_equip(weapon)
        assert len(weapon_results) == 1
        assert weapon_results[0]['equipped'] == weapon
        
        # Equip shield
        shield_results = self.equipment.toggle_equip(shield)
        assert len(shield_results) == 1
        assert shield_results[0]['equipped'] == shield
        
        # Both should be equipped
        assert self.equipment.main_hand == weapon
        assert self.equipment.off_hand == shield


class TestEquipmentIntegration:
    """Test Equipment integration with other components."""

    def test_equipment_with_real_equippable_components(self):
        """Test Equipment with real Equippable components."""
        equipment = Equipment()
        
        # Create sword with real Equippable component
        sword_equippable = Equippable(EquipmentSlots.MAIN_HAND, power_bonus=3, defense_bonus=1)
        sword = Mock()
        sword.equippable = sword_equippable
        
        # Create shield with real Equippable component
        shield_equippable = Equippable(EquipmentSlots.OFF_HAND, defense_bonus=2, max_hp_bonus=5)
        shield = Mock()
        shield.equippable = shield_equippable
        
        # Equip both
        equipment.toggle_equip(sword)
        equipment.toggle_equip(shield)
        
        # Test bonuses
        assert equipment.power_bonus == 3
        assert equipment.defense_bonus == 3  # 1 from sword + 2 from shield
        assert equipment.max_hp_bonus == 5

    def test_equipment_bonus_calculation_edge_cases(self):
        """Test equipment bonus calculations with edge cases."""
        equipment = Equipment()
        
        # Test with zero bonuses
        zero_bonus_equippable = Equippable(EquipmentSlots.MAIN_HAND, power_bonus=0, defense_bonus=0, max_hp_bonus=0)
        zero_item = Mock()
        zero_item.equippable = zero_bonus_equippable
        
        equipment.toggle_equip(zero_item)
        
        assert equipment.power_bonus == 0
        assert equipment.defense_bonus == 0
        assert equipment.max_hp_bonus == 0

    def test_equipment_with_negative_bonuses(self):
        """Test equipment with negative bonuses (cursed items)."""
        equipment = Equipment()
        
        # Create cursed item with negative bonuses
        cursed_equippable = Equippable(EquipmentSlots.MAIN_HAND, power_bonus=-1, defense_bonus=-2, max_hp_bonus=-5)
        cursed_item = Mock()
        cursed_item.equippable = cursed_equippable
        
        equipment.toggle_equip(cursed_item)
        
        assert equipment.power_bonus == -1
        assert equipment.defense_bonus == -2
        assert equipment.max_hp_bonus == -5

    def test_equipment_mixed_positive_negative_bonuses(self):
        """Test equipment with mixed positive and negative bonuses."""
        equipment = Equipment()
        
        # Powerful but cursed weapon
        cursed_weapon_equippable = Equippable(EquipmentSlots.MAIN_HAND, power_bonus=5, defense_bonus=-1)
        cursed_weapon = Mock()
        cursed_weapon.equippable = cursed_weapon_equippable
        
        # Protective shield
        shield_equippable = Equippable(EquipmentSlots.OFF_HAND, defense_bonus=3)
        shield = Mock()
        shield.equippable = shield_equippable
        
        equipment.toggle_equip(cursed_weapon)
        equipment.toggle_equip(shield)
        
        assert equipment.power_bonus == 5
        assert equipment.defense_bonus == 2  # -1 + 3 = 2
        assert equipment.max_hp_bonus == 0


class TestEquipmentSlots:
    """Test EquipmentSlots enum."""

    def test_equipment_slots_values(self):
        """Test EquipmentSlots enum values."""
        assert EquipmentSlots.MAIN_HAND.value == 1
        assert EquipmentSlots.OFF_HAND.value == 2

    def test_equipment_slots_comparison(self):
        """Test EquipmentSlots enum comparison."""
        assert EquipmentSlots.MAIN_HAND != EquipmentSlots.OFF_HAND
        assert EquipmentSlots.MAIN_HAND == EquipmentSlots.MAIN_HAND
        assert EquipmentSlots.OFF_HAND == EquipmentSlots.OFF_HAND
