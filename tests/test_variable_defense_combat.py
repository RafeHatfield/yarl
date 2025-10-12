"""Tests for variable defense in combat system.

This module tests that armor provides variable defense values during combat,
that combat messages properly show absorbed damage, and that the defense
calculation integrates correctly with the existing combat system.
"""

import pytest
from unittest.mock import Mock, patch

from components.fighter import Fighter
from components.equipment import Equipment
from components.equippable import Equippable
from equipment_slots import EquipmentSlots
from game_messages import Message
from components.component_registry import ComponentType


class TestVariableDefenseCombat:
    """Test variable defense system in combat."""

    def setup_method(self):
        """Set up test entities with fighter and equipment components."""
        # Create attacker with equipment
        self.attacker = Mock()
        self.attacker.name = "orc"
        self.attacker.fighter = Fighter(hp=20, defense=0, power=4)
        self.attacker.fighter.owner = self.attacker
        # Equipment for attacker (empty for simpler testing)
        self.attacker.equipment = Equipment()
        self.attacker.equipment.owner = self.attacker
        # Mock get_component_optional to return None for BOSS (not a boss)
        self.attacker.get_component_optional = Mock(return_value=None)
        
        # Create target with equipment
        self.target = Mock()
        self.target.name = "player"
        self.target.fighter = Fighter(hp=30, defense=1, power=2)
        self.target.fighter.owner = self.target
        
        # Create equipment component for target
        self.target.equipment = Equipment()
        self.target.equipment.owner = self.target
        # Mock get_component_optional to return None for BOSS (not a boss)
        self.target.get_component_optional = Mock(return_value=None)

    def test_variable_defense_applied_in_combat(self):
        """Test that variable defense from armor is applied during combat."""
        # Create armor with variable defense
        armor = Mock()
        armor.equippable = Equippable(
            slot=EquipmentSlots.OFF_HAND,
            defense_bonus=1,
            defense_min=2,
            defense_max=4
        )
        
        # Equip armor
        self.target.equipment.off_hand = armor
        
        # Mock armor to return specific defense value
        with patch.object(armor.equippable, 'roll_defense', return_value=3):
            results = self.attacker.fighter.attack(self.target)
        
        # Verify damage calculation: attacker power(4) - target base_defense(1) - armor_defense(3) = 0
        expected_damage = 4 - 1 - 3  # = 0 (minimum damage is 0)
        
        # Should result in completely blocked attack
        assert len(results) == 1
        assert "message" in results[0]
        message_text = results[0]["message"].text
        assert "attack blocked!" in message_text
        assert "orc attacks player" in message_text.lower()

    def test_variable_defense_with_partial_absorption(self):
        """Test that variable defense partially absorbs damage."""
        # Create armor with lower defense range
        armor = Mock()
        armor.equippable = Equippable(
            slot=EquipmentSlots.OFF_HAND,
            defense_bonus=1,
            defense_min=1,
            defense_max=2
        )
        
        # Equip armor
        self.target.equipment.off_hand = armor
        
        # Mock armor to return specific defense value
        with patch.object(armor.equippable, 'roll_defense', return_value=1):
            results = self.attacker.fighter.attack(self.target)
        
        # Verify damage calculation: attacker power(4) - target defense(1+1=2) - armor_defense(1) = 1
        # target.fighter.defense includes base_defense(1) + defense_bonus(1) = 2
        expected_damage = 4 - 2 - 1  # = 1
        
        # Should result in damage with armor absorption message
        assert len(results) >= 1
        assert "message" in results[0]
        message_text = results[0]["message"].text
        assert "1 damage" in message_text
        assert "(2 base + 1 armor)" in message_text
        assert "orc attacks player" in message_text.lower()

    def test_no_armor_defense_message(self):
        """Test combat message when no armor is equipped."""
        # No armor equipped (off_hand is None)
        
        results = self.attacker.fighter.attack(self.target)
        
        # Verify damage calculation: attacker power(4) - target defense(1+0=1) - armor_defense(0) = 3
        expected_damage = 4 - 1 - 0  # = 3
        
        # Should result in damage without armor absorption message
        assert len(results) >= 1
        assert "message" in results[0]
        message_text = results[0]["message"].text
        assert "3 damage" in message_text
        assert "absorbed by armor" not in message_text
        assert "orc attacks player" in message_text.lower()

    def test_armor_with_zero_defense_range(self):
        """Test armor that has no variable defense (defense_min/max = 0)."""
        # Create armor with only defense_bonus, no variable defense
        armor = Mock()
        armor.equippable = Equippable(
            slot=EquipmentSlots.OFF_HAND,
            defense_bonus=2,
            defense_min=0,
            defense_max=0
        )
        
        # Equip armor
        self.target.equipment.off_hand = armor
        
        results = self.attacker.fighter.attack(self.target)
        
        # roll_defense should return 0 for armor with no variable defense
        # Damage calculation: attacker power(4) - target base_defense(1) - armor_defense(0) = 3
        # Note: defense_bonus is handled separately by the defense property
        
        assert len(results) >= 1
        assert "message" in results[0]
        message_text = results[0]["message"].text
        assert "damage" in message_text
        assert "absorbed by armor" not in message_text  # No variable defense to show

    def test_multiple_armor_pieces_defense(self):
        """Test that both main_hand and off_hand armor contribute to defense."""
        # Create armor for off_hand
        off_hand_armor = Mock()
        off_hand_armor.equippable = Equippable(
            slot=EquipmentSlots.OFF_HAND,
            defense_bonus=1,
            defense_min=1,
            defense_max=2
        )
        
        # Equip off_hand armor
        self.target.equipment.off_hand = off_hand_armor
        
        # Note: Currently _get_armor_defense only checks off_hand
        # This test verifies current behavior and documents potential future enhancement
        
        with patch.object(off_hand_armor.equippable, 'roll_defense', return_value=2):
            results = self.attacker.fighter.attack(self.target)
        
        # Verify only off_hand armor defense is applied
        # Damage calculation: attacker power(4) - target defense(1+1=2) - armor_defense(2) = 0
        assert len(results) >= 1
        assert "message" in results[0]
        message_text = results[0]["message"].text
        assert "attack blocked!" in message_text

    def test_high_armor_defense_blocks_all_damage(self):
        """Test that high armor defense can completely block attacks."""
        # Create very strong armor
        armor = Mock()
        armor.equippable = Equippable(
            slot=EquipmentSlots.OFF_HAND,
            defense_bonus=1,
            defense_min=5,
            defense_max=8
        )
        
        # Equip armor
        self.target.equipment.off_hand = armor
        
        # Mock high defense roll
        with patch.object(armor.equippable, 'roll_defense', return_value=7):
            results = self.attacker.fighter.attack(self.target)
        
        # Damage calculation: attacker power(4) - target base_defense(1) - armor_defense(7) = -4 → 0
        
        assert len(results) == 1
        assert "message" in results[0]
        message_text = results[0]["message"].text
        assert "attack blocked!" in message_text

    def test_variable_defense_randomness(self):
        """Test that armor defense varies between rolls."""
        # Create armor with range
        armor = Mock()
        armor.equippable = Equippable(
            slot=EquipmentSlots.OFF_HAND,
            defense_bonus=1,
            defense_min=1,
            defense_max=3
        )
        
        # Equip armor
        self.target.equipment.off_hand = armor
        
        # Test multiple rolls produce different results
        defense_values = []
        for _ in range(10):
            defense_val = armor.equippable.roll_defense()
            defense_values.append(defense_val)
        
        # Should get values in range [1, 3]
        assert all(1 <= val <= 3 for val in defense_values)
        
        # With 10 rolls, we should see some variation (not all the same)
        # This is probabilistic but very likely to pass
        unique_values = set(defense_values)
        assert len(unique_values) > 1, f"Expected variation, got all {defense_values[0]}"


class TestVariableDefenseIntegration:
    """Test integration of variable defense with existing systems."""

    def setup_method(self):
        """Set up test entities."""
        self.attacker = Mock()
        self.attacker.name = "troll"
        self.attacker.fighter = Fighter(hp=30, defense=2, power=8)
        self.attacker.fighter.owner = self.attacker
        self.attacker.equipment = Equipment()
        self.attacker.equipment.owner = self.attacker
        # Mock get_component_optional to return None for BOSS (not a boss)
        self.attacker.get_component_optional = Mock(return_value=None)
        
        self.target = Mock()
        self.target.name = "player"
        self.target.fighter = Fighter(hp=100, defense=1, power=3)
        self.target.fighter.owner = self.target
        # Mock get_component_optional to return None for BOSS (not a boss)
        self.target.get_component_optional = Mock(return_value=None)
        
        self.target.equipment = Equipment()
        self.target.equipment.owner = self.target

    def test_variable_defense_with_weapon_damage(self):
        """Test variable defense against variable weapon damage."""
        # Give attacker a weapon
        weapon = Mock()
        weapon.equippable = Equippable(
            slot=EquipmentSlots.MAIN_HAND,
            power_bonus=2,
            damage_min=2,
            damage_max=5
        )
        
        self.attacker.equipment = Equipment(main_hand=weapon)
        self.attacker.equipment.owner = self.attacker
        
        # Give target armor
        armor = Mock()
        armor.equippable = Equippable(
            slot=EquipmentSlots.OFF_HAND,
            defense_bonus=1,
            defense_min=1,
            defense_max=4
        )
        
        self.target.equipment.off_hand = armor
        
        # Mock specific rolls for predictable testing
        with patch.object(weapon.equippable, 'roll_damage', return_value=3), \
             patch.object(armor.equippable, 'roll_defense', return_value=2):
            
            results = self.attacker.fighter.attack(self.target)
        
        # Damage calculation:
        # Total attack = attacker.power (8 + 2) + weapon_damage(3) = 13
        # Total defense = target.defense (1 + 1) + armor_defense(2) = 4  
        # Final damage = 13 - 4 = 9
        
        assert len(results) >= 1
        message_text = results[0]["message"].text
        assert "9 damage" in message_text
        assert "(10 power + 3 weapon)" in message_text
        assert "(2 base + 2 armor)" in message_text

    def test_base_defense_still_applied(self):
        """Test that base defense from Fighter is still applied along with armor."""
        # Create target with higher base defense
        self.target.fighter = Fighter(hp=100, defense=3, power=3)
        self.target.fighter.owner = self.target
        
        # Add armor
        armor = Mock()
        armor.equippable = Equippable(
            slot=EquipmentSlots.OFF_HAND,
            defense_bonus=1,
            defense_min=1,
            defense_max=2
        )
        
        self.target.equipment = Equipment(off_hand=armor)
        self.target.equipment.owner = self.target
        
        with patch.object(armor.equippable, 'roll_defense', return_value=1):
            results = self.attacker.fighter.attack(self.target)
        
        # Damage calculation: attacker power(8) - target defense(3+1=4) - armor_defense(1) = 3
        # target.fighter.defense includes base_defense(3) + defense_bonus(1) = 4
        expected_damage = 8 - 4 - 1  # = 3
        
        assert len(results) >= 1
        message_text = results[0]["message"].text
        assert "3 damage" in message_text
        assert "(4 base + 1 armor)" in message_text

    def test_legacy_defense_bonus_compatibility(self):
        """Test that the system works with equipment that only has defense_bonus."""
        # Create old-style armor with only defense_bonus (no variable defense)
        armor = Mock()
        armor.equippable = Equippable(
            slot=EquipmentSlots.OFF_HAND,
            defense_bonus=2,  # Only static bonus
            defense_min=0,    # No variable defense
            defense_max=0
        )
        
        self.target.equipment = Equipment(off_hand=armor)
        self.target.equipment.owner = self.target
        
        # Test with legacy equipment (no variable defense, just static defense_bonus)
        results = self.attacker.fighter.attack(self.target)
        
        # Damage calculation: attacker power(8) - target defense(1+2=3) - armor_defense(0) = 5
        # Note: defense_bonus is handled by the defense property, not by roll_defense
        
        assert len(results) >= 1
        message_text = results[0]["message"].text
        assert "damage" in message_text
        # No "(X absorbed by armor)" message since roll_defense returns 0


class TestVariableDefenseEdgeCases:
    """Test edge cases and error conditions for variable defense."""

    def test_no_equipment_component(self):
        """Test _get_armor_defense when target has no equipment component."""
        attacker = Mock()
        attacker.name = "orc"
        attacker.fighter = Fighter(hp=20, defense=0, power=4)
        attacker.fighter.owner = attacker
        attacker.equipment = Equipment()
        attacker.equipment.owner = attacker
        # Mock get_component_optional to return None for BOSS (not a boss)
        attacker.get_component_optional = Mock(return_value=None)
        
        # Create a target with no equipment by using a real object with None equipment
        target = Mock()
        target.name = "goblin"
        target.fighter = Fighter(hp=10, defense=0, power=2)
        # Mock get_component_optional to return None for BOSS (not a boss)
        target.get_component_optional = Mock(return_value=None)
        target.fighter.owner = target
        target.equipment = None  # Explicitly set to None instead of missing
        
        results = attacker.fighter.attack(target)
        
        # Should work without error, armor_defense = 0
        assert len(results) >= 1
        message_text = results[0]["message"].text
        assert "4 damage" in message_text  # full damage, no armor
        assert "absorbed by armor" not in message_text

    def test_equipment_with_no_off_hand(self):
        """Test _get_armor_defense when equipment has no off_hand item."""
        attacker = Mock()
        attacker.name = "orc"
        attacker.fighter = Fighter(hp=20, defense=0, power=4)
        attacker.fighter.owner = attacker
        attacker.equipment = Equipment()
        attacker.equipment.owner = attacker
        attacker.get_component_optional = Mock(return_value=None)
        
        target = Mock()
        target.name = "player"
        target.fighter = Fighter(hp=30, defense=1, power=2)
        target.fighter.owner = target
        target.equipment = Equipment()
        target.equipment.owner = target
        target.get_component_optional = Mock(return_value=None)
        
        # Equipment with no off_hand
        target.equipment = Equipment()
        target.equipment.owner = target
        
        results = attacker.fighter.attack(target)
        
        # Should work without error, armor_defense = 0
        assert len(results) >= 1
        message_text = results[0]["message"].text
        assert "3 damage" in message_text  # power(4) - defense(1) = 3
        assert "absorbed by armor" not in message_text

    def test_off_hand_with_no_equippable(self):
        """Test _get_armor_defense when off_hand item has no equippable component."""
        attacker = Mock()
        attacker.name = "orc"
        attacker.fighter = Fighter(hp=20, defense=0, power=4)
        attacker.fighter.owner = attacker
        attacker.equipment = Equipment()
        attacker.equipment.owner = attacker
        attacker.get_component_optional = Mock(return_value=None)
        
        target = Mock()
        target.name = "player"
        target.fighter = Fighter(hp=30, defense=1, power=2)
        target.fighter.owner = target
        target.equipment = Equipment()
        target.equipment.owner = target
        target.get_component_optional = Mock(return_value=None)
        
        # Equipment with off_hand item that has no equippable component
        off_hand_item = Mock()
        off_hand_item.equippable = None
        
        target.equipment = Equipment(off_hand=off_hand_item)
        target.equipment.owner = target
        
        results = attacker.fighter.attack(target)
        
        # Should work without error, armor_defense = 0
        assert len(results) >= 1
        message_text = results[0]["message"].text
        assert "3 damage" in message_text
        assert "absorbed by armor" not in message_text

    def test_zero_damage_attack_with_armor_message(self):
        """Test that zero damage attacks show appropriate blocking message."""
        # Weak attacker
        attacker = Mock()
        attacker.name = "weak_goblin"
        attacker.fighter = Fighter(hp=5, defense=0, power=1)
        attacker.fighter.owner = attacker
        attacker.equipment = Equipment()
        attacker.equipment.owner = attacker
        attacker.get_component_optional = Mock(return_value=None)
        
        # Strong target with good armor
        target = Mock()
        target.name = "armored_knight"
        target.fighter = Fighter(hp=50, defense=2, power=5)
        target.fighter.owner = target
        target.get_component_optional = Mock(return_value=None)
        
        # Strong armor
        armor = Mock()
        armor.equippable = Equippable(
            slot=EquipmentSlots.OFF_HAND,
            defense_bonus=2,
            defense_min=3,
            defense_max=5
        )
        
        target.equipment = Equipment(off_hand=armor)
        target.equipment.owner = target
        
        with patch.object(armor.equippable, 'roll_defense', return_value=4):
            results = attacker.fighter.attack(target)
        
        # Damage: power(1) - base_defense(2) - armor_defense(4) = -5 → 0
        
        assert len(results) == 1
        message_text = results[0]["message"].text
        assert "attack blocked!" in message_text
        assert "weak_goblin attacks armored_knight" in message_text.lower()


class TestArmorDefenseMethod:
    """Test the _get_armor_defense method specifically."""

    def setup_method(self):
        """Set up test fighter with equipment."""
        self.entity = Mock()
        self.entity.fighter = Fighter(hp=30, defense=1, power=2)
        self.entity.fighter.owner = self.entity
        
        self.entity.equipment = Equipment()
        self.entity.equipment.owner = self.entity
        # Mock get_component_optional to return None for BOSS (not a boss)
        self.entity.get_component_optional = Mock(return_value=None)

    def test_get_armor_defense_with_armor(self):
        """Test _get_armor_defense returns roll_defense value."""
        armor = Mock()
        armor.equippable = Equippable(
            slot=EquipmentSlots.OFF_HAND,
            defense_min=2,
            defense_max=4
        )
        
        self.entity.equipment.off_hand = armor
        
        with patch.object(armor.equippable, 'roll_defense', return_value=3):
            defense = self.entity.fighter._get_armor_defense()
        
        assert defense == 3

    def test_get_armor_defense_no_armor(self):
        """Test _get_armor_defense returns 0 when no armor equipped."""
        # No off_hand armor
        defense = self.entity.fighter._get_armor_defense()
        assert defense == 0

    def test_get_armor_defense_no_equipment(self):
        """Test _get_armor_defense when entity has no equipment component."""
        # Remove equipment component
        delattr(self.entity, 'equipment')
        
        defense = self.entity.fighter._get_armor_defense()
        assert defense == 0

    def test_get_armor_defense_calls_roll_defense(self):
        """Test that _get_armor_defense calls equippable.roll_defense()."""
        armor = Mock()
        armor.equippable = Mock()
        armor.equippable.roll_defense = Mock(return_value=5)
        
        self.entity.equipment.off_hand = armor
        
        defense = self.entity.fighter._get_armor_defense()
        
        assert defense == 5
        armor.equippable.roll_defense.assert_called_once()
