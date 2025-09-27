"""
Unit tests for Equippable component.

Tests the equippable item component including:
- Equippable component initialization
- Stat bonus properties (power, defense, max HP)
- Equipment slot assignment
- Integration with equipment system
"""

import pytest

from components.equippable import Equippable
from equipment_slots import EquipmentSlots


class TestEquippable:
    """Test Equippable component functionality."""

    def test_equippable_initialization_defaults(self):
        """Test Equippable component initializes with default values."""
        equippable = Equippable(EquipmentSlots.MAIN_HAND)
        
        assert equippable.slot == EquipmentSlots.MAIN_HAND
        assert equippable.power_bonus == 0
        assert equippable.defense_bonus == 0
        assert equippable.max_hp_bonus == 0

    def test_equippable_initialization_with_bonuses(self):
        """Test Equippable component initializes with custom bonuses."""
        equippable = Equippable(
            slot=EquipmentSlots.OFF_HAND,
            power_bonus=2,
            defense_bonus=3,
            max_hp_bonus=10
        )
        
        assert equippable.slot == EquipmentSlots.OFF_HAND
        assert equippable.power_bonus == 2
        assert equippable.defense_bonus == 3
        assert equippable.max_hp_bonus == 10

    def test_equippable_main_hand_weapon(self):
        """Test creating a main hand weapon."""
        sword = Equippable(EquipmentSlots.MAIN_HAND, power_bonus=3)
        
        assert sword.slot == EquipmentSlots.MAIN_HAND
        assert sword.power_bonus == 3
        assert sword.defense_bonus == 0
        assert sword.max_hp_bonus == 0

    def test_equippable_off_hand_shield(self):
        """Test creating an off hand shield."""
        shield = Equippable(EquipmentSlots.OFF_HAND, defense_bonus=2)
        
        assert shield.slot == EquipmentSlots.OFF_HAND
        assert shield.power_bonus == 0
        assert shield.defense_bonus == 2
        assert shield.max_hp_bonus == 0

    def test_equippable_balanced_item(self):
        """Test creating an item with balanced stats."""
        balanced_weapon = Equippable(
            EquipmentSlots.MAIN_HAND,
            power_bonus=2,
            defense_bonus=1,
            max_hp_bonus=5
        )
        
        assert balanced_weapon.slot == EquipmentSlots.MAIN_HAND
        assert balanced_weapon.power_bonus == 2
        assert balanced_weapon.defense_bonus == 1
        assert balanced_weapon.max_hp_bonus == 5

    def test_equippable_negative_bonuses(self):
        """Test creating cursed items with negative bonuses."""
        cursed_item = Equippable(
            EquipmentSlots.MAIN_HAND,
            power_bonus=-1,
            defense_bonus=-2,
            max_hp_bonus=-5
        )
        
        assert cursed_item.slot == EquipmentSlots.MAIN_HAND
        assert cursed_item.power_bonus == -1
        assert cursed_item.defense_bonus == -2
        assert cursed_item.max_hp_bonus == -5

    def test_equippable_zero_bonuses(self):
        """Test creating items with explicitly zero bonuses."""
        zero_item = Equippable(
            EquipmentSlots.OFF_HAND,
            power_bonus=0,
            defense_bonus=0,
            max_hp_bonus=0
        )
        
        assert zero_item.slot == EquipmentSlots.OFF_HAND
        assert zero_item.power_bonus == 0
        assert zero_item.defense_bonus == 0
        assert zero_item.max_hp_bonus == 0

    def test_equippable_large_bonuses(self):
        """Test creating items with large bonuses."""
        legendary_item = Equippable(
            EquipmentSlots.MAIN_HAND,
            power_bonus=100,
            defense_bonus=50,
            max_hp_bonus=200
        )
        
        assert legendary_item.slot == EquipmentSlots.MAIN_HAND
        assert legendary_item.power_bonus == 100
        assert legendary_item.defense_bonus == 50
        assert legendary_item.max_hp_bonus == 200


class TestEquippableSlotTypes:
    """Test Equippable with different slot types."""

    def test_main_hand_slot_assignment(self):
        """Test main hand slot assignment."""
        main_hand_items = [
            Equippable(EquipmentSlots.MAIN_HAND, power_bonus=1),
            Equippable(EquipmentSlots.MAIN_HAND, power_bonus=5),
            Equippable(EquipmentSlots.MAIN_HAND, defense_bonus=2)
        ]
        
        for item in main_hand_items:
            assert item.slot == EquipmentSlots.MAIN_HAND

    def test_off_hand_slot_assignment(self):
        """Test off hand slot assignment."""
        off_hand_items = [
            Equippable(EquipmentSlots.OFF_HAND, defense_bonus=1),
            Equippable(EquipmentSlots.OFF_HAND, defense_bonus=3),
            Equippable(EquipmentSlots.OFF_HAND, max_hp_bonus=10)
        ]
        
        for item in off_hand_items:
            assert item.slot == EquipmentSlots.OFF_HAND

    def test_slot_immutability(self):
        """Test that slot assignment is immutable after creation."""
        equippable = Equippable(EquipmentSlots.MAIN_HAND, power_bonus=3)
        original_slot = equippable.slot
        
        # Slot should remain the same
        assert equippable.slot == original_slot
        assert equippable.slot == EquipmentSlots.MAIN_HAND


class TestEquippableRealisticItems:
    """Test Equippable with realistic game item configurations."""

    def test_basic_sword(self):
        """Test basic sword configuration."""
        sword = Equippable(EquipmentSlots.MAIN_HAND, power_bonus=3)
        
        assert sword.slot == EquipmentSlots.MAIN_HAND
        assert sword.power_bonus == 3
        assert sword.defense_bonus == 0
        assert sword.max_hp_bonus == 0

    def test_basic_shield(self):
        """Test basic shield configuration."""
        shield = Equippable(EquipmentSlots.OFF_HAND, defense_bonus=1)
        
        assert shield.slot == EquipmentSlots.OFF_HAND
        assert shield.power_bonus == 0
        assert shield.defense_bonus == 1
        assert shield.max_hp_bonus == 0

    def test_dagger(self):
        """Test dagger configuration (light weapon)."""
        dagger = Equippable(EquipmentSlots.MAIN_HAND, power_bonus=2)
        
        assert dagger.slot == EquipmentSlots.MAIN_HAND
        assert dagger.power_bonus == 2
        assert dagger.defense_bonus == 0
        assert dagger.max_hp_bonus == 0

    def test_magic_sword(self):
        """Test magic sword with multiple bonuses."""
        magic_sword = Equippable(
            EquipmentSlots.MAIN_HAND,
            power_bonus=5,
            defense_bonus=1,
            max_hp_bonus=10
        )
        
        assert magic_sword.slot == EquipmentSlots.MAIN_HAND
        assert magic_sword.power_bonus == 5
        assert magic_sword.defense_bonus == 1
        assert magic_sword.max_hp_bonus == 10

    def test_tower_shield(self):
        """Test tower shield with high defense."""
        tower_shield = Equippable(
            EquipmentSlots.OFF_HAND,
            defense_bonus=3,
            max_hp_bonus=5
        )
        
        assert tower_shield.slot == EquipmentSlots.OFF_HAND
        assert tower_shield.power_bonus == 0
        assert tower_shield.defense_bonus == 3
        assert tower_shield.max_hp_bonus == 5

    def test_cursed_weapon(self):
        """Test cursed weapon with mixed bonuses."""
        cursed_weapon = Equippable(
            EquipmentSlots.MAIN_HAND,
            power_bonus=10,  # High damage
            defense_bonus=-2,  # But reduces defense
            max_hp_bonus=-10   # And reduces health
        )
        
        assert cursed_weapon.slot == EquipmentSlots.MAIN_HAND
        assert cursed_weapon.power_bonus == 10
        assert cursed_weapon.defense_bonus == -2
        assert cursed_weapon.max_hp_bonus == -10

    def test_artifact_item(self):
        """Test artifact-level item with high stats."""
        artifact = Equippable(
            EquipmentSlots.MAIN_HAND,
            power_bonus=8,
            defense_bonus=3,
            max_hp_bonus=25
        )
        
        assert artifact.slot == EquipmentSlots.MAIN_HAND
        assert artifact.power_bonus == 8
        assert artifact.defense_bonus == 3
        assert artifact.max_hp_bonus == 25


class TestEquippableEdgeCases:
    """Test Equippable edge cases and boundary conditions."""

    def test_equippable_with_only_power_bonus(self):
        """Test equippable with only power bonus."""
        power_only = Equippable(EquipmentSlots.MAIN_HAND, power_bonus=5)
        
        assert power_only.power_bonus == 5
        assert power_only.defense_bonus == 0
        assert power_only.max_hp_bonus == 0

    def test_equippable_with_only_defense_bonus(self):
        """Test equippable with only defense bonus."""
        defense_only = Equippable(EquipmentSlots.OFF_HAND, defense_bonus=3)
        
        assert defense_only.power_bonus == 0
        assert defense_only.defense_bonus == 3
        assert defense_only.max_hp_bonus == 0

    def test_equippable_with_only_hp_bonus(self):
        """Test equippable with only HP bonus."""
        hp_only = Equippable(EquipmentSlots.OFF_HAND, max_hp_bonus=15)
        
        assert hp_only.power_bonus == 0
        assert hp_only.defense_bonus == 0
        assert hp_only.max_hp_bonus == 15

    def test_equippable_stat_independence(self):
        """Test that equippable stats are independent."""
        item1 = Equippable(EquipmentSlots.MAIN_HAND, power_bonus=3)
        item2 = Equippable(EquipmentSlots.MAIN_HAND, power_bonus=5)
        
        # Modifying one shouldn't affect the other
        assert item1.power_bonus == 3
        assert item2.power_bonus == 5
        
        # They should be independent objects
        assert item1 is not item2
        assert item1.power_bonus != item2.power_bonus
