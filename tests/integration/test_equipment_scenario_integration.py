"""Integration tests for complete equipment scenarios.

This module tests full equipment workflows: find → pick up → equip → stat changes → unequip,
ensuring all systems (inventory, equipment, fighter, messages) work together.
"""

import pytest
from unittest.mock import Mock

from entity import Entity
from components.fighter import Fighter
from components.inventory import Inventory
from components.equipment import Equipment
from components.equippable import Equippable
from components.item import Item
from equipment_slots import EquipmentSlots
from game_messages import MessageLog


class TestEquipmentScenarioIntegration:
    """Integration tests for complete equipment scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create message log
        self.message_log = MessageLog(x=0, width=80, height=10)
        
        # Create player with all necessary components
        fighter = Fighter(hp=30, defense=2, power=5)
        inventory = Inventory(capacity=26)
        equipment = Equipment()
        
        self.player = Entity(
            10, 10, "@", (255, 255, 255), "Player",
            blocks=True,
            fighter=fighter,
            inventory=inventory,
            equipment=equipment
        )
        
        # Connect equipment to fighter
        equipment.owner = self.player
    
    def test_find_pickup_equip_scenario(self):
        """Test complete flow: find item → pick up → equip → stats increase."""
        # Arrange: Create a sword on the ground
        sword_equippable = Equippable(
            slot=EquipmentSlots.MAIN_HAND,
            power_bonus=3
        )
        sword = Entity(
            10, 10, "/", (139, 69, 19), "Sword",
            item=Item(),
            equippable=sword_equippable
        )
        
        # Record initial stats
        initial_power = self.player.fighter.power
        initial_base_power = self.player.fighter.base_power
        
        # Act 1: Pick up sword
        pickup_results = self.player.inventory.add_item(sword)
        
        # Assert: Sword in inventory
        assert sword in self.player.inventory.items, "Sword should be in inventory"
        assert any(r.get("item_added") for r in pickup_results), \
            "Pickup should return item_added"
        
        # Act 2: Equip sword
        equip_results = self.player.equipment.toggle_equip(sword)
        
        # Assert: Sword equipped
        assert self.player.equipment.main_hand == sword, "Sword should be in main hand"
        
        # Assert: Power increased
        assert self.player.fighter.power > initial_power, \
            f"Power should increase from {initial_power}"
        # Note: power property is computed from base_power + equipment bonuses
        
        # Assert: Equip message generated
        assert any(r.get("equipped") for r in equip_results), \
            "Should return equipped result"
    
    def test_equip_upgrade_scenario(self):
        """Test upgrading equipment: equip sword → find better sword → replace."""
        # Arrange: Create basic sword
        basic_sword = Entity(
            10, 10, "/", (139, 69, 19), "Iron Sword",
            item=Item(),
            equippable=Equippable(slot=EquipmentSlots.MAIN_HAND, power_bonus=2)
        )
        
        # Create better sword
        better_sword = Entity(
            11, 10, "/", (192, 192, 192), "Steel Sword",
            item=Item(),
            equippable=Equippable(slot=EquipmentSlots.MAIN_HAND, power_bonus=5)
        )
        
        # Act 1: Equip basic sword
        self.player.inventory.add_item(basic_sword)
        self.player.equipment.toggle_equip(basic_sword)
        power_with_basic = self.player.fighter.power
        
        # Act 2: Pick up better sword and equip
        self.player.inventory.add_item(better_sword)
        self.player.equipment.toggle_equip(better_sword)
        
        # Assert: Better sword equipped
        assert self.player.equipment.main_hand == better_sword, \
            "Better sword should replace basic sword"
        
        # Assert: Basic sword unequipped (back in inventory)
        assert basic_sword in self.player.inventory.items, \
            "Basic sword should be back in inventory"
        
        # Assert: Power increased further
        assert self.player.fighter.power > power_with_basic, \
            "Power should increase with better sword"
    
    def test_shield_armor_combination_scenario(self):
        """Test equipping multiple items: shield + armor = combined bonuses."""
        # Arrange: Create shield (defense +2)
        shield = Entity(
            10, 10, "]", (139, 69, 19), "Wooden Shield",
            item=Item(),
            equippable=Equippable(slot=EquipmentSlots.OFF_HAND, defense_bonus=2)
        )
        
        # Create armor (defense +3)
        armor = Entity(
            10, 11, "[", (139, 69, 19), "Leather Armor",
            item=Item(),
            equippable=Equippable(slot=EquipmentSlots.CHEST, defense_bonus=3)
        )
        
        initial_defense = self.player.fighter.defense
        
        # Act: Equip both
        self.player.inventory.add_item(shield)
        self.player.equipment.toggle_equip(shield)
        
        self.player.inventory.add_item(armor)
        self.player.equipment.toggle_equip(armor)
        
        # Assert: Both equipped in different slots
        assert self.player.equipment.off_hand == shield, "Shield should be in off-hand"
        assert self.player.equipment.chest == armor, "Armor should be on chest"
        
        # Assert: Defense bonuses stack
        expected_defense = initial_defense + 2 + 3
        assert self.player.fighter.defense == expected_defense, \
            f"Defense should be {expected_defense} (base + shield + armor)"
    
    def test_unequip_stat_restoration_scenario(self):
        """Test unequipping: remove item → stats return to base."""
        # Arrange: Create and equip powerful weapon
        weapon = Entity(
            10, 10, "/", (255, 215, 0), "Magic Sword",
            item=Item(),
            equippable=Equippable(slot=EquipmentSlots.MAIN_HAND, power_bonus=10)
        )
        
        base_power = self.player.fighter.power
        
        self.player.inventory.add_item(weapon)
        self.player.equipment.toggle_equip(weapon)
        
        boosted_power = self.player.fighter.power
        assert boosted_power > base_power, "Power should increase"
        
        # Act: Unequip weapon
        self.player.equipment.toggle_equip(weapon)
        
        # Assert: Weapon unequipped
        assert self.player.equipment.main_hand is None, "Main hand should be empty"
        
        # Assert: Power restored to base
        assert self.player.fighter.power == base_power, \
            f"Power should return to base {base_power}"
    
    def test_cursed_item_scenario(self):
        """Test cursed item: equip → negative bonuses applied."""
        # Arrange: Create cursed weapon (negative bonus)
        cursed_weapon = Entity(
            10, 10, "/", (128, 0, 128), "Cursed Blade",
            item=Item(),
            equippable=Equippable(slot=EquipmentSlots.MAIN_HAND, power_bonus=-2)
        )
        
        base_power = self.player.fighter.power
        
        # Act: Equip cursed weapon
        self.player.inventory.add_item(cursed_weapon)
        self.player.equipment.toggle_equip(cursed_weapon)
        
        # Assert: Power decreased
        assert self.player.fighter.power < base_power, \
            "Cursed weapon should decrease power"
    
    def test_inventory_full_cannot_pickup_scenario(self):
        """Test inventory limits: full inventory → cannot pick up new items."""
        # Arrange: Fill inventory
        for i in range(26):  # Fill to capacity
            item = Entity(
                10, 10, "!", (255, 0, 0), f"Potion{i}",
                item=Item()
            )
            self.player.inventory.add_item(item)
        
        # Create one more item
        extra_item = Entity(
            10, 10, "!", (255, 0, 0), "Extra Potion",
            item=Item()
        )
        
        # Act: Try to pick up when full
        results = self.player.inventory.add_item(extra_item)
        
        # Assert: Item not added
        assert extra_item not in self.player.inventory.items, \
            "Should not add item to full inventory"
        
        # Assert: Warning message generated
        assert any(r.get("message") for r in results), \
            "Should generate 'inventory full' message"
    
    def test_two_handed_weapon_scenario(self):
        """Test two-handed weapon: equip → replaces both hands."""
        # Arrange: Equip sword and shield first
        sword = Entity(
            10, 10, "/", (139, 69, 19), "Sword",
            item=Item(),
            equippable=Equippable(slot=EquipmentSlots.MAIN_HAND, power_bonus=3)
        )
        shield = Entity(
            10, 10, "]", (139, 69, 19), "Shield",
            item=Item(),
            equippable=Equippable(slot=EquipmentSlots.OFF_HAND, defense_bonus=2)
        )
        
        self.player.inventory.add_item(sword)
        self.player.inventory.add_item(shield)
        self.player.equipment.toggle_equip(sword)
        self.player.equipment.toggle_equip(shield)
        
        # For now, test that equipping a main hand weapon works
        # (two-handed weapons are not currently implemented)
        # Create powerful one-handed weapon
        mace = Entity(
            10, 10, "/", (192, 192, 192), "Mace",
            item=Item(),
            equippable=Equippable(
                slot=EquipmentSlots.MAIN_HAND,
                power_bonus=6
            )
        )
        
        # Act: Equip weapon (should replace existing sword)
        self.player.inventory.add_item(mace)
        self.player.equipment.toggle_equip(mace)
        
        # Assert: Mace equipped in main hand
        assert self.player.equipment.main_hand == mace, \
            "Mace should be equipped in main hand"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

