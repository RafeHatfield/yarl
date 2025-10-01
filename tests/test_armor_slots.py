"""Tests for the new armor equipment slots (HEAD, CHEST, FEET).

This test suite validates:
- New equipment slots work correctly
- Armor pieces can be equipped/unequipped
- AC bonuses from armor are properly calculated
- Multiple armor pieces stack bonuses correctly
"""

import unittest
from equipment_slots import EquipmentSlots
from components.equipment import Equipment
from components.equippable import Equippable
from components.fighter import Fighter
from entity import Entity


class TestArmorSlots(unittest.TestCase):
    """Test the new armor equipment slots."""

    def setUp(self):
        """Set up test fixtures."""
        # Create test armor items
        self.helmet = Entity(0, 0, '^', (255, 255, 255), 'Helmet')
        self.helmet.equippable = Equippable(
            EquipmentSlots.HEAD,
            armor_class_bonus=1
        )

        self.chest = Entity(0, 0, '[', (255, 255, 255), 'Chest Armor')
        self.chest.equippable = Equippable(
            EquipmentSlots.CHEST,
            armor_class_bonus=2
        )

        self.boots = Entity(0, 0, ']', (255, 255, 255), 'Boots')
        self.boots.equippable = Equippable(
            EquipmentSlots.FEET,
            armor_class_bonus=1
        )

    def test_armor_slots_exist(self):
        """Test that new armor slots are defined."""
        self.assertEqual(EquipmentSlots.HEAD.value, 3)
        self.assertEqual(EquipmentSlots.CHEST.value, 4)
        self.assertEqual(EquipmentSlots.FEET.value, 5)

    def test_equipment_initialization_with_armor(self):
        """Test Equipment component initializes with armor slots."""
        eq = Equipment(head=self.helmet, chest=self.chest, feet=self.boots)
        
        self.assertEqual(eq.head, self.helmet)
        self.assertEqual(eq.chest, self.chest)
        self.assertEqual(eq.feet, self.boots)

    def test_equip_helmet(self):
        """Test equipping a helmet."""
        eq = Equipment()
        results = eq.toggle_equip(self.helmet)

        self.assertEqual(len(results), 1)
        self.assertIn('equipped', results[0])
        self.assertEqual(results[0]['equipped'], self.helmet)
        self.assertEqual(eq.head, self.helmet)

    def test_equip_chest_armor(self):
        """Test equipping chest armor."""
        eq = Equipment()
        results = eq.toggle_equip(self.chest)

        self.assertEqual(len(results), 1)
        self.assertIn('equipped', results[0])
        self.assertEqual(results[0]['equipped'], self.chest)
        self.assertEqual(eq.chest, self.chest)

    def test_equip_boots(self):
        """Test equipping boots."""
        eq = Equipment()
        results = eq.toggle_equip(self.boots)

        self.assertEqual(len(results), 1)
        self.assertIn('equipped', results[0])
        self.assertEqual(results[0]['equipped'], self.boots)
        self.assertEqual(eq.feet, self.boots)

    def test_unequip_helmet(self):
        """Test unequipping a helmet."""
        eq = Equipment(head=self.helmet)
        results = eq.toggle_equip(self.helmet)

        self.assertEqual(len(results), 1)
        self.assertIn('dequipped', results[0])
        self.assertEqual(results[0]['dequipped'], self.helmet)
        self.assertIsNone(eq.head)

    def test_replace_chest_armor(self):
        """Test replacing chest armor."""
        old_chest = Entity(0, 0, '[', (100, 100, 100), 'Old Armor')
        old_chest.equippable = Equippable(EquipmentSlots.CHEST, armor_class_bonus=1)

        eq = Equipment(chest=old_chest)
        results = eq.toggle_equip(self.chest)

        self.assertEqual(len(results), 2)
        self.assertIn('dequipped', results[0])
        self.assertEqual(results[0]['dequipped'], old_chest)
        self.assertIn('equipped', results[1])
        self.assertEqual(results[1]['equipped'], self.chest)
        self.assertEqual(eq.chest, self.chest)

    def test_equip_full_armor_set(self):
        """Test equipping a complete armor set."""
        eq = Equipment()
        
        eq.toggle_equip(self.helmet)
        eq.toggle_equip(self.chest)
        eq.toggle_equip(self.boots)

        self.assertEqual(eq.head, self.helmet)
        self.assertEqual(eq.chest, self.chest)
        self.assertEqual(eq.feet, self.boots)


class TestArmorACBonuses(unittest.TestCase):
    """Test AC bonuses from armor pieces."""

    def setUp(self):
        """Set up test player with fighter component."""
        self.player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
        self.player.fighter = Fighter(hp=30, defense=0, power=0, 
                                     strength=14, dexterity=12, constitution=14)
        self.player.fighter.owner = self.player
        self.player.equipment = Equipment()
        self.player.equipment.owner = self.player

        # Create armor items
        self.helmet = Entity(0, 0, '^', (255, 255, 255), 'Helmet')
        self.helmet.equippable = Equippable(EquipmentSlots.HEAD, armor_class_bonus=1)

        self.chest = Entity(0, 0, '[', (255, 255, 255), 'Chest Armor')
        self.chest.equippable = Equippable(EquipmentSlots.CHEST, armor_class_bonus=2)

        self.boots = Entity(0, 0, ']', (255, 255, 255), 'Boots')
        self.boots.equippable = Equippable(EquipmentSlots.FEET, armor_class_bonus=1)

        self.shield = Entity(0, 0, '[', (255, 255, 255), 'Shield')
        self.shield.equippable = Equippable(EquipmentSlots.OFF_HAND, armor_class_bonus=2)

    def test_ac_with_no_armor(self):
        """Test AC calculation with no armor equipped."""
        # Base AC = 10, DEX 12 = +1 modifier
        expected_ac = 10 + 1  # 11
        self.assertEqual(self.player.fighter.armor_class, expected_ac)

    def test_ac_with_helmet(self):
        """Test AC bonus from helmet."""
        self.player.equipment.head = self.helmet
        
        # Base 10 + DEX +1 + Helmet +1 = 12
        expected_ac = 12
        self.assertEqual(self.player.fighter.armor_class, expected_ac)

    def test_ac_with_chest_armor(self):
        """Test AC bonus from chest armor."""
        self.player.equipment.chest = self.chest
        
        # Base 10 + DEX +1 + Chest +2 = 13
        expected_ac = 13
        self.assertEqual(self.player.fighter.armor_class, expected_ac)

    def test_ac_with_boots(self):
        """Test AC bonus from boots."""
        self.player.equipment.feet = self.boots
        
        # Base 10 + DEX +1 + Boots +1 = 12
        expected_ac = 12
        self.assertEqual(self.player.fighter.armor_class, expected_ac)

    def test_ac_with_shield(self):
        """Test AC bonus from shield."""
        self.player.equipment.off_hand = self.shield
        
        # Base 10 + DEX +1 + Shield +2 = 13
        expected_ac = 13
        self.assertEqual(self.player.fighter.armor_class, expected_ac)

    def test_ac_with_full_armor_set(self):
        """Test AC bonus from complete armor set."""
        self.player.equipment.head = self.helmet      # +1
        self.player.equipment.chest = self.chest      # +2
        self.player.equipment.feet = self.boots       # +1
        self.player.equipment.off_hand = self.shield  # +2
        
        # Base 10 + DEX +1 + Helmet +1 + Chest +2 + Boots +1 + Shield +2 = 17
        expected_ac = 17
        self.assertEqual(self.player.fighter.armor_class, expected_ac)

    def test_ac_with_helmet_and_boots(self):
        """Test AC bonus from multiple armor pieces."""
        self.player.equipment.head = self.helmet
        self.player.equipment.feet = self.boots
        
        # Base 10 + DEX +1 + Helmet +1 + Boots +1 = 13
        expected_ac = 13
        self.assertEqual(self.player.fighter.armor_class, expected_ac)


class TestArmorBonusAccumulation(unittest.TestCase):
    """Test that bonuses from all slots accumulate correctly."""

    def test_max_hp_bonus_with_armor(self):
        """Test that max HP bonuses from armor slots are calculated."""
        helmet = Entity(0, 0, '^', (255, 255, 255), 'Helmet')
        helmet.equippable = Equippable(EquipmentSlots.HEAD, max_hp_bonus=5)

        chest = Entity(0, 0, '[', (255, 255, 255), 'Chest')
        chest.equippable = Equippable(EquipmentSlots.CHEST, max_hp_bonus=10)

        eq = Equipment(head=helmet, chest=chest)
        
        # Should get bonuses from both pieces
        self.assertEqual(eq.max_hp_bonus, 15)

    def test_defense_bonus_with_armor(self):
        """Test that defense bonuses from armor slots are calculated."""
        chest = Entity(0, 0, '[', (255, 255, 255), 'Chest')
        chest.equippable = Equippable(EquipmentSlots.CHEST, defense_bonus=3)

        boots = Entity(0, 0, ']', (255, 255, 255), 'Boots')
        boots.equippable = Equippable(EquipmentSlots.FEET, defense_bonus=1)

        eq = Equipment(chest=chest, feet=boots)
        
        # Should get bonuses from both pieces
        self.assertEqual(eq.defense_bonus, 4)

    def test_power_bonus_with_armor(self):
        """Test that power bonuses from armor slots are calculated."""
        # Technically armor shouldn't give power bonuses, but test the system works
        helmet = Entity(0, 0, '^', (255, 255, 255), 'Spiked Helmet')
        helmet.equippable = Equippable(EquipmentSlots.HEAD, power_bonus=1)

        eq = Equipment(head=helmet)
        
        self.assertEqual(eq.power_bonus, 1)


if __name__ == '__main__':
    unittest.main()

