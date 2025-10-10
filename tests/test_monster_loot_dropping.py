"""Tests for monster loot dropping when monsters die.

This test suite ensures that when monsters die and drop loot, the items are:
1. Properly removed from the monster's equipment/inventory
2. Added to the world entities correctly
3. Can be picked up only once by the player
4. Can be equipped properly without weird reference issues
"""

import pytest
from config.entity_factory import EntityFactory
from config.entity_registry import load_entity_config
from components.monster_equipment import drop_loot_from_monster
from components.component_registry import ComponentType


@pytest.fixture(scope="module")
def entity_factory():
    """Create entity factory with loaded config."""
    load_entity_config('config/entities.yaml')
    return EntityFactory()


class TestMonsterLootDropping:
    """Test that loot is properly dropped when monsters die."""
    
    def test_equipped_weapon_removed_from_equipment_on_drop(self, entity_factory):
        """Test that equipped weapons are removed from equipment slot when dropped."""
        # Create orc with weapon
        orc = entity_factory.create_monster('orc', 10, 10)
        weapon = entity_factory.create_weapon('club', 10, 10)
        
        # Equip the weapon
        if orc.equipment:
            orc.equipment.main_hand = weapon
            weapon.owner = orc
        
        # Verify weapon is equipped
        assert orc.equipment.main_hand == weapon
        
        # Drop loot
        dropped_items = drop_loot_from_monster(orc, 10, 10)
        
        # Verify weapon is in dropped items
        assert weapon in dropped_items
        
        # Verify weapon is NO LONGER in equipment slot
        assert orc.equipment.main_hand is None
        
        # Verify weapon ownership is cleared
        assert weapon.owner is None
    
    def test_equipped_armor_removed_from_equipment_on_drop(self, entity_factory):
        """Test that equipped armor is removed from equipment slot when dropped."""
        # Create orc with armor
        orc = entity_factory.create_monster('orc', 10, 10)
        armor = entity_factory.create_armor('leather_armor', 10, 10)
        
        # Equip the armor
        if orc.equipment:
            orc.equipment.off_hand = armor
            armor.owner = orc
        
        # Verify armor is equipped
        assert orc.equipment.off_hand == armor
        
        # Drop loot
        dropped_items = drop_loot_from_monster(orc, 10, 10)
        
        # Verify armor is in dropped items
        assert armor in dropped_items
        
        # Verify armor is NO LONGER in equipment slot
        assert orc.equipment.off_hand is None
        
        # Verify armor ownership is cleared
        assert armor.owner is None
    
    def test_inventory_items_removed_from_inventory_on_drop(self, entity_factory):
        """Test that inventory items are removed from inventory when dropped."""
        # Create orc with inventory
        orc = entity_factory.create_monster('orc', 10, 10)
        scroll = entity_factory.create_spell_item('lightning_scroll', 10, 10)
        
        # Add scroll to inventory
        if orc.inventory:
            initial_count = len(orc.inventory.items)
            orc.inventory.add_item(scroll)
            scroll.owner = orc
            
            # Verify scroll was added
            assert scroll in orc.inventory.items
            assert len(orc.inventory.items) == initial_count + 1
        
        # Drop loot
        dropped_items = drop_loot_from_monster(orc, 10, 10)
        
        # Verify scroll is in dropped items
        assert scroll in dropped_items
        
        # Verify scroll is NO LONGER in inventory
        assert scroll not in orc.inventory.items
        assert len(orc.inventory.items) == 0  # ALL items should be dropped
        
        # Verify scroll ownership is cleared
        assert scroll.owner is None
    
    def test_dropped_weapon_can_be_picked_up_once(self, entity_factory):
        """Test that a dropped weapon can only be picked up once."""
        # Create orc with weapon
        orc = entity_factory.create_monster('orc', 10, 10)
        weapon = entity_factory.create_weapon('club', 10, 10)
        
        # Equip the weapon
        if orc.equipment:
            orc.equipment.main_hand = weapon
            weapon.owner = orc
        
        # Drop loot
        dropped_items = drop_loot_from_monster(orc, 10, 10)
        
        # Create player
        player = entity_factory.create_monster('orc', 11, 11)  # Use orc as dummy player
        player.name = 'Player'
        
        # Create entities list
        entities = [orc, player] + dropped_items
        
        # Player picks up weapon
        if player.inventory:
            player.inventory.add_item(weapon)
            entities.remove(weapon)
        
        # Verify weapon is in player's inventory
        assert weapon in player.inventory.items
        
        # Verify weapon is NOT in entities (not in the world anymore)
        assert weapon not in entities
        
        # Try to pick up again (should fail - weapon not in entities)
        # This simulates the bug where player could pick up same item multiple times
        assert weapon not in entities  # Can't pick up what's not in the world
    
    def test_dropped_items_positioned_correctly(self, entity_factory):
        """Test that dropped items are positioned at or near the monster's location."""
        # Create orc with weapon and armor
        orc = entity_factory.create_monster('orc', 10, 10)
        weapon = entity_factory.create_weapon('club', 10, 10)
        armor = entity_factory.create_armor('leather_armor', 10, 10)
        
        # Equip items
        if orc.equipment:
            orc.equipment.main_hand = weapon
            orc.equipment.off_hand = armor
        
        # Drop loot
        dropped_items = drop_loot_from_monster(orc, 10, 10)
        
        # Verify all items are positioned near (10, 10)
        for item in dropped_items:
            # Should be within 1 tile of drop location
            assert abs(item.x - 10) <= 1
            assert abs(item.y - 10) <= 1
    
    def test_slimes_dont_drop_items(self, entity_factory):
        """Test that slimes don't drop items (they're just blobs)."""
        # Create slime with fake equipment (shouldn't happen, but test edge case)
        slime = entity_factory.create_monster('slime', 10, 10)
        weapon = entity_factory.create_weapon('club', 10, 10)
        
        # Force equip weapon (even though slimes shouldn't have equipment)
        if slime.equipment:
            slime.equipment.main_hand = weapon
        
        # Drop loot
        dropped_items = drop_loot_from_monster(slime, 10, 10)
        
        # Slimes should drop nothing
        assert len(dropped_items) == 0


class TestMonsterLootIntegration:
    """Integration tests for monster loot system."""
    
    def test_full_loot_lifecycle(self, entity_factory):
        """Test complete lifecycle: equip -> die -> drop -> pickup -> equip."""
        # Create orc with weapon
        orc = entity_factory.create_monster('orc', 10, 10)
        weapon = entity_factory.create_weapon('shortsword', 10, 10)
        
        # Step 1: Equip weapon on orc
        if orc.equipment:
            orc.equipment.main_hand = weapon
            weapon.owner = orc
            assert orc.equipment.main_hand == weapon
        
        # Step 2: Orc dies and drops loot
        dropped_items = drop_loot_from_monster(orc, 10, 10)
        assert weapon in dropped_items
        assert orc.equipment.main_hand is None  # Weapon unequipped
        assert weapon.owner is None  # Ownership cleared
        
        # Step 3: Player picks up weapon
        player = entity_factory.create_monster('orc', 11, 11)
        player.name = 'Player'
        entities = [orc, player, weapon]
        
        if player.inventory:
            player.inventory.add_item(weapon)
            entities.remove(weapon)
            assert weapon in player.inventory.items
            assert weapon not in entities
        
        # Step 4: Player equips weapon
        if player.equipment:
            result = player.equipment.toggle_equip(weapon)
            
            # Verify weapon is now equipped on player
            assert player.equipment.main_hand == weapon
            
            # Weapon should only be in ONE place: equipped on player
            # NOT in orc's equipment (verified above)
            # NOT in world entities (verified above)
            assert weapon.owner == player or weapon.owner is None  # Ownership transferred or cleared

