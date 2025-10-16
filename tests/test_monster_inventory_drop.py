"""Test that monsters drop all inventory items when they die.

CRITICAL REGRESSION TEST for bug where monsters would pick up items but not drop
them on death, causing items to be permanently lost from the game world.

This is especially important for key items, scrolls, and other critical loot.
"""

import pytest
from entity import Entity
from components.fighter import Fighter
from components.inventory import Inventory
from components.equipment import Equipment
from components.ai import BasicMonster
from components.item import Item
from components.component_registry import ComponentType
from components.faction import Faction
from death_functions import kill_monster
from render_functions import RenderOrder


def create_test_monster_with_inventory():
    """Create a test monster with inventory capability."""
    fighter = Fighter(hp=10, defense=0, power=2, xp=10)
    ai = BasicMonster()
    inventory = Inventory(5)
    equipment = Equipment()
    
    monster = Entity(
        x=5, y=5, char='o', color=(63, 127, 63), name='Orc',
        blocks=True, render_order=RenderOrder.ACTOR,
        faction=Faction.NEUTRAL,  # Neutral monsters attack player
        fighter=fighter, ai=ai, inventory=inventory, equipment=equipment
    )
    
    return monster


def create_test_item(name="Test Item"):
    """Create a simple test item."""
    item_component = Item()
    item = Entity(
        x=5, y=5, char='!', color=(255, 0, 0), name=name,
        item=item_component
    )
    item_component.owner = item
    return item


class TestMonsterInventoryDrop:
    """Test that monster inventory items are dropped on death."""
    
    def test_monster_drops_picked_up_item(self):
        """Test that an item picked up by a monster is dropped when monster dies."""
        # Create monster and item
        monster = create_test_monster_with_inventory()
        item = create_test_item("Important Scroll")
        
        # Create entities list (simulating game world)
        entities = [monster, item]
        
        # Monster picks up the item (simulating what happens in game)
        monster.inventory.add_item(item)
        
        # CRITICAL: When monsters pick up items, they're removed from entities
        # (see components/ai.py _pickup_item line 548-549)
        entities.remove(item)
        
        # Verify item is in monster's inventory and NOT in entities
        assert item in monster.inventory.items, "Item should be in monster inventory"
        assert item not in entities, "Item should be removed from world when picked up"
        
        # Monster dies
        death_message = kill_monster(monster, game_map=None, entities=entities)
        
        # Check if dropped items are stored on monster
        dropped_items = getattr(monster, '_dropped_loot', [])
        
        # CRITICAL TEST: The picked-up item MUST be in dropped_items
        assert item in dropped_items, \
            f"Item picked up by monster MUST be dropped on death! " \
            f"Monster inventory had {len(monster.inventory.items if monster.inventory else [])} items, " \
            f"but only {len(dropped_items)} items were dropped"
        
        # Verify item has correct position (should be near monster's death location)
        assert item.x in range(monster.x - 2, monster.x + 3), "Item should be near monster"
        assert item.y in range(monster.y - 2, monster.y + 3), "Item should be near monster"
    
    def test_monster_drops_multiple_inventory_items(self):
        """Test that ALL items in monster inventory are dropped."""
        monster = create_test_monster_with_inventory()
        items = [
            create_test_item("Healing Potion"),
            create_test_item("Fireball Scroll"),
            create_test_item("Magic Ring"),
        ]
        
        # Monster picks up all items
        entities = [monster] + items
        for item in items:
            monster.inventory.add_item(item)
            entities.remove(item)  # Simulate pickup removal
        
        # Verify all items in inventory, none in entities
        assert len(monster.inventory.items) == 3
        for item in items:
            assert item not in entities
        
        # Monster dies
        kill_monster(monster, game_map=None, entities=entities)
        dropped_items = getattr(monster, '_dropped_loot', [])
        
        # ALL items must be dropped (might have bonus loot too, which is fine)
        assert len(dropped_items) >= 3, \
            f"Monster had 3 items in inventory but only dropped {len(dropped_items)}"
        
        # Verify each inventory item was dropped
        for item in items:
            assert item in dropped_items, f"{item.name} was not dropped!"
    
    def test_monster_drops_both_equipped_and_inventory_items(self):
        """Test that monsters drop BOTH equipped items AND inventory items."""
        monster = create_test_monster_with_inventory()
        
        # Create equipment
        from components.equippable import Equippable
        from equipment_slots import EquipmentSlots
        
        weapon = create_test_item("Iron Sword")
        weapon.equippable = Equippable(slot=EquipmentSlots.MAIN_HAND, power_bonus=2)
        
        shield = create_test_item("Wooden Shield")
        shield.equippable = Equippable(slot=EquipmentSlots.OFF_HAND, defense_bonus=1)
        
        # Inventory item (not equipped)
        potion = create_test_item("Healing Potion")
        
        entities = [monster, weapon, shield, potion]
        
        # Equip weapon and shield
        monster.equipment.toggle_equip(weapon)
        monster.equipment.toggle_equip(shield)
        
        # Add potion to inventory (not equipped)
        monster.inventory.add_item(potion)
        entities.remove(potion)  # Simulate pickup removal
        
        # Verify setup
        assert monster.equipment.main_hand == weapon
        assert monster.equipment.off_hand == shield
        assert potion in monster.inventory.items
        assert potion not in entities
        
        # Monster dies
        kill_monster(monster, game_map=None, entities=entities)
        dropped_items = getattr(monster, '_dropped_loot', [])
        
        # Should drop AT LEAST 3 items: equipped weapon + equipped shield + inventory potion
        # (might have bonus loot too)
        assert len(dropped_items) >= 3, \
            f"Expected at least 3 items (2 equipped + 1 inventory) but got {len(dropped_items)}"
        
        # Verify each expected item was dropped
        assert weapon in dropped_items, "Equipped weapon must be dropped"
        assert shield in dropped_items, "Equipped shield must be dropped"
        assert potion in dropped_items, "Inventory potion must be dropped"
    
    def test_empty_inventory_monster_still_drops_equipped_items(self):
        """Test that monsters with empty inventory still drop equipped items."""
        monster = create_test_monster_with_inventory()
        
        from components.equippable import Equippable
        from equipment_slots import EquipmentSlots
        
        weapon = create_test_item("Rusty Dagger")
        weapon.equippable = Equippable(slot=EquipmentSlots.MAIN_HAND, power_bonus=1)
        
        # Equip weapon (inventory remains empty)
        monster.equipment.toggle_equip(weapon)
        
        # Verify inventory is empty
        assert len(monster.inventory.items) == 0, "Inventory should be empty"
        assert monster.equipment.main_hand == weapon
        
        # Monster dies
        kill_monster(monster, game_map=None, entities=[monster, weapon])
        dropped_items = getattr(monster, '_dropped_loot', [])
        
        # Should drop the equipped weapon (might have bonus loot too)
        assert len(dropped_items) >= 1, "Should drop at least the equipped weapon"
        assert weapon in dropped_items, "Equipped weapon must be in dropped items"

