"""Tests for unequipping items by clicking equipment in sidebar.

This test suite verifies that clicking on equipped items in the sidebar
properly unequips them.
"""

import pytest
from entity import Entity
from components.fighter import Fighter
from components.inventory import Inventory
from components.equipment import Equipment
from components.equippable import Equippable
from components.item import Item
from equipment_slots import EquipmentSlots


def create_test_player():
    """Create a test player with equipment."""
    fighter = Fighter(hp=100, defense=10, power=10)
    inventory = Inventory(capacity=20)
    equipment = Equipment()
    
    player = Entity(
        x=0, y=0,
        char='@',
        color=(255, 255, 255),
        name="Test Player",
        blocks=True,
        fighter=fighter,
        inventory=inventory,
        equipment=equipment
    )
    
    return player


def create_test_weapon(name="Test Sword"):
    """Create a test weapon."""
    equippable = Equippable(slot=EquipmentSlots.MAIN_HAND)
    item = Item()
    
    weapon = Entity(
        x=0, y=0,
        char='/',
        color=(139, 69, 19),
        name=name,
        item=item,
        equippable=equippable
    )
    
    return weapon


def create_test_armor(name="Test Armor", slot=EquipmentSlots.CHEST):
    """Create test armor."""
    equippable = Equippable(slot=slot)
    item = Item()
    
    armor = Entity(
        x=0, y=0,
        char='[',
        color=(100, 100, 100),
        name=name,
        item=item,
        equippable=equippable
    )
    
    return armor


class TestSidebarEquipmentUnequip:
    """Test unequipping items via sidebar clicks."""
    
    def test_clicking_equipped_weapon_unequips_it(self):
        """Clicking on equipped weapon in sidebar should unequip it."""
        player = create_test_player()
        weapon = create_test_weapon("Iron Sword")
        
        # Equip the weapon
        player.inventory.add_item(weapon)
        player.equipment.toggle_equip(weapon)
        assert player.equipment.main_hand == weapon, "Weapon should be equipped"
        
        # Simulate clicking on equipped weapon in sidebar
        # (This is what game_actions.py does when equipment_slot is clicked)
        equip_results = player.equipment.toggle_equip(weapon)
        
        # Weapon should now be unequipped
        assert player.equipment.main_hand is None, "Weapon should be unequipped"
        
        # Should have dequipped result
        has_dequip = any('dequipped' in result for result in equip_results)
        assert has_dequip, "Should have dequipped result"
    
    def test_clicking_equipped_armor_unequips_it(self):
        """Clicking on equipped armor in sidebar should unequip it."""
        player = create_test_player()
        armor = create_test_armor("Leather Armor", EquipmentSlots.CHEST)
        
        # Equip the armor
        player.inventory.add_item(armor)
        player.equipment.toggle_equip(armor)
        assert player.equipment.chest == armor
        
        # Click to unequip
        equip_results = player.equipment.toggle_equip(armor)
        
        # Armor should be unequipped
        assert player.equipment.chest is None
        assert any('dequipped' in result for result in equip_results)
    
    def test_clicking_equipped_ring_unequips_it(self):
        """Clicking on equipped ring in sidebar should unequip it."""
        from components.ring import Ring, RingEffect
        from components.component_registry import ComponentType
        
        player = create_test_player()
        
        # Create ring
        ring_component = Ring(RingEffect.PROTECTION, effect_strength=2)
        equippable = Equippable(slot=EquipmentSlots.RING)
        item = Item()
        
        ring = Entity(
            x=0, y=0,
            char='=',
            color=(200, 200, 200),
            name="Ring of Protection",
            item=item,
            equippable=equippable
        )
        ring.ring = ring_component
        ring_component.owner = ring
        ring.components.add(ComponentType.RING, ring_component)
        
        # Equip the ring
        player.inventory.add_item(ring)
        player.equipment.toggle_equip(ring)
        
        # Should be in left or right ring slot
        is_equipped = (player.equipment.left_ring == ring or 
                      player.equipment.right_ring == ring)
        assert is_equipped, "Ring should be equipped"
        
        # Click to unequip
        equip_results = player.equipment.toggle_equip(ring)
        
        # Ring should be unequipped
        assert player.equipment.left_ring != ring, "Ring should not be in left slot"
        assert player.equipment.right_ring != ring, "Ring should not be in right slot"
        assert any('dequipped' in result for result in equip_results)
    
    def test_equip_unequip_cycle_via_sidebar(self):
        """Test full cycle: equip from inventory, unequip from equipment section."""
        player = create_test_player()
        weapon = create_test_weapon("Battle Axe")
        
        player.inventory.add_item(weapon)
        
        # First click: equip (from inventory)
        results1 = player.equipment.toggle_equip(weapon)
        assert player.equipment.main_hand == weapon
        assert any('equipped' in result for result in results1)
        
        # Second click: unequip (from equipment section)
        results2 = player.equipment.toggle_equip(weapon)
        assert player.equipment.main_hand is None
        assert any('dequipped' in result for result in results2)
        
        # Third click: re-equip (from inventory again)
        results3 = player.equipment.toggle_equip(weapon)
        assert player.equipment.main_hand == weapon
        assert any('equipped' in result for result in results3)
    
    def test_unequipping_multiple_items(self):
        """Test unequipping multiple different equipment pieces."""
        player = create_test_player()
        
        weapon = create_test_weapon("Sword")
        helmet = create_test_armor("Helmet", EquipmentSlots.HEAD)
        chest = create_test_armor("Chainmail", EquipmentSlots.CHEST)
        
        # Equip all
        for item in [weapon, helmet, chest]:
            player.inventory.add_item(item)
            player.equipment.toggle_equip(item)
        
        assert player.equipment.main_hand == weapon
        assert player.equipment.head == helmet
        assert player.equipment.chest == chest
        
        # Unequip helmet
        player.equipment.toggle_equip(helmet)
        assert player.equipment.head is None
        assert player.equipment.main_hand == weapon  # Others still equipped
        assert player.equipment.chest == chest
        
        # Unequip weapon
        player.equipment.toggle_equip(weapon)
        assert player.equipment.main_hand is None
        assert player.equipment.chest == chest  # Chest still equipped
        
        # Unequip chest
        player.equipment.toggle_equip(chest)
        assert player.equipment.chest is None


class TestEquipmentToggleLogic:
    """Test the toggle_equip logic for edge cases."""
    
    def test_toggle_equip_on_equipped_item_unequips(self):
        """Calling toggle_equip on already equipped item should unequip it."""
        player = create_test_player()
        weapon = create_test_weapon()
        
        player.inventory.add_item(weapon)
        
        # Equip
        player.equipment.toggle_equip(weapon)
        assert player.equipment.main_hand == weapon
        
        # Toggle again (should unequip)
        player.equipment.toggle_equip(weapon)
        assert player.equipment.main_hand is None
    
    def test_toggle_equip_on_unequipped_item_equips(self):
        """Calling toggle_equip on unequipped item should equip it."""
        player = create_test_player()
        weapon = create_test_weapon()
        
        player.inventory.add_item(weapon)
        
        # Should not be equipped initially
        assert player.equipment.main_hand is None
        
        # Toggle (should equip)
        player.equipment.toggle_equip(weapon)
        assert player.equipment.main_hand == weapon


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

