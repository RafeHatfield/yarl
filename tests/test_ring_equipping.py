"""Tests for ring equipping functionality.

This test suite verifies that rings can be equipped when:
1. Clicked in sidebar
2. Used from inventory menu
3. Used via keyboard shortcut

Bug Report: User clicking on Ring of Regeneration in sidebar doesn't equip it
"""

import pytest
from entity import Entity
from components.fighter import Fighter
from components.inventory import Inventory
from components.equipment import Equipment
from components.equippable import Equippable
from components.ring import Ring, RingEffect
from components.item import Item
from components.component_registry import ComponentType
from equipment_slots import EquipmentSlots


def create_test_player():
    """Create a test player with inventory and equipment."""
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


def create_test_ring(name="Test Ring", ring_effect=RingEffect.REGENERATION):
    """Create a test ring entity."""
    ring_component = Ring(
        ring_effect=ring_effect,
        effect_strength=1
    )
    
    equippable_component = Equippable(
        slot=EquipmentSlots.RING
    )
    
    item_component = Item()
    
    ring_entity = Entity(
        x=0, y=0,
        char='=',
        color=(200, 200, 200),
        name=name,
        item=item_component,
        equippable=equippable_component
    )
    
    # Attach ring component
    ring_entity.ring = ring_component
    ring_component.owner = ring_entity
    ring_entity.components.add(ComponentType.RING, ring_component)
    
    return ring_entity


class TestRingComponentRegistration:
    """Test that rings have proper component registration."""
    
    def test_ring_has_equippable_component(self):
        """Ring should have an Equippable component."""
        ring = create_test_ring()
        
        assert ring.equippable is not None, "Ring should have equippable component"
        assert ring.equippable.slot == EquipmentSlots.RING
    
    def test_ring_equippable_in_component_registry(self):
        """Ring's Equippable component should be in ComponentRegistry."""
        ring = create_test_ring()
        
        # Check if equippable is registered in component registry
        assert ring.components.has(ComponentType.EQUIPPABLE), \
            "Ring's Equippable component should be in ComponentRegistry"
        
        equippable = ring.components.get(ComponentType.EQUIPPABLE)
        assert equippable is not None
        assert equippable == ring.equippable
    
    def test_ring_has_item_component(self):
        """Ring should have an Item component."""
        ring = create_test_ring()
        
        assert ring.item is not None, "Ring should have item component"
        assert ring.components.has(ComponentType.ITEM), \
            "Ring's Item component should be in ComponentRegistry"
    
    def test_ring_has_ring_component(self):
        """Ring should have a Ring component."""
        ring = create_test_ring()
        
        assert ring.ring is not None, "Ring should have ring component"
        assert ring.components.has(ComponentType.RING), \
            "Ring's Ring component should be in ComponentRegistry"


class TestRingEquipping:
    """Test that rings can be equipped properly."""
    
    def test_ring_can_be_equipped(self):
        """Player should be able to equip a ring."""
        player = create_test_player()
        ring = create_test_ring("Ring of Protection")
        
        # Add ring to player's inventory
        player.inventory.add_item(ring)
        
        # Equip the ring
        results = player.equipment.toggle_equip(ring)
        
        # Check that ring is equipped
        assert player.equipment.left_ring == ring or player.equipment.right_ring == ring, \
            "Ring should be equipped in left or right ring slot"
        
        # Check for success message
        assert any('equipped' in str(result.get('message', '')).lower() for result in results), \
            "Should have success message about equipping"
    
    def test_ring_toggle_equip_works(self):
        """toggle_equip should equip then unequip ring."""
        player = create_test_player()
        ring = create_test_ring()
        
        player.inventory.add_item(ring)
        
        # First toggle: equip
        results = player.equipment.toggle_equip(ring)
        assert player.equipment.left_ring == ring or player.equipment.right_ring == ring
        
        # Second toggle: unequip
        results = player.equipment.toggle_equip(ring)
        assert player.equipment.left_ring != ring and player.equipment.right_ring != ring
    
    def test_can_equip_two_rings(self):
        """Player should be able to equip two different rings."""
        player = create_test_player()
        ring1 = create_test_ring("Ring of Protection", RingEffect.PROTECTION)
        ring2 = create_test_ring("Ring of Strength", RingEffect.STRENGTH)
        
        player.inventory.add_item(ring1)
        player.inventory.add_item(ring2)
        
        # Equip first ring
        player.equipment.toggle_equip(ring1)
        
        # Equip second ring
        player.equipment.toggle_equip(ring2)
        
        # Both should be equipped
        equipped_rings = {player.equipment.left_ring, player.equipment.right_ring}
        assert ring1 in equipped_rings, "First ring should be equipped"
        assert ring2 in equipped_rings, "Second ring should be equipped"
    
    def test_third_ring_replaces_first(self):
        """Equipping a third ring should replace the left ring slot."""
        player = create_test_player()
        ring1 = create_test_ring("Ring 1", RingEffect.PROTECTION)
        ring2 = create_test_ring("Ring 2", RingEffect.STRENGTH)
        ring3 = create_test_ring("Ring 3", RingEffect.DEXTERITY)
        
        for ring in [ring1, ring2, ring3]:
            player.inventory.add_item(ring)
        
        # Equip first two rings
        player.equipment.toggle_equip(ring1)
        player.equipment.toggle_equip(ring2)
        
        # Equip third ring (should replace left ring = ring1)
        results = player.equipment.toggle_equip(ring3)
        
        # Ring3 should be equipped, ring1 should not be
        equipped_rings = {player.equipment.left_ring, player.equipment.right_ring}
        assert ring3 in equipped_rings, "Third ring should be equipped"
        assert ring1 not in equipped_rings, "First ring should be unequipped"
        assert ring2 in equipped_rings, "Second ring should still be equipped"


class TestInventoryActionWithRing:
    """Test _handle_inventory_action logic with rings."""
    
    def test_ring_has_equippable_component_check(self):
        """Verify that rings pass the equippable component check."""
        ring = create_test_ring()
        
        # This is the check from _use_inventory_item in game_actions.py
        has_equippable = ring.components.has(ComponentType.EQUIPPABLE)
        
        assert has_equippable, \
            "Ring should have EQUIPPABLE component in registry"
    
    def test_ring_not_usable_as_consumable(self):
        """Rings should not have a use_function (they're not consumables)."""
        ring = create_test_ring()
        
        # Rings don't have use_function - they're equipped, not consumed
        assert not hasattr(ring.item, 'use_function') or ring.item.use_function is None, \
            "Rings should not have use_function"
    
    def test_equipment_toggle_equip_accepts_ring(self):
        """Equipment.toggle_equip should accept rings."""
        player = create_test_player()
        ring = create_test_ring()
        
        player.inventory.add_item(ring)
        
        # This should not raise an exception
        try:
            results = player.equipment.toggle_equip(ring)
            assert True, "toggle_equip should work with rings"
        except Exception as e:
            pytest.fail(f"toggle_equip raised exception for ring: {e}")


class TestSidebarClickScenario:
    """Test the exact scenario from the bug report."""
    
    def test_sidebar_click_on_ring(self):
        """Simulate sidebar click on Ring of Regeneration."""
        player = create_test_player()
        ring = create_test_ring("Ring Of Regeneration", RingEffect.REGENERATION)
        
        # Add ring to inventory
        player.inventory.add_item(ring)
        
        # Get sorted inventory (this is what sidebar and game_actions do)
        sorted_items = sorted(player.inventory.items, key=lambda item: item.get_display_name().lower())
        
        # Find ring index
        ring_index = sorted_items.index(ring)
        
        # Simulate what _handle_inventory_action does
        item = sorted_items[ring_index]
        
        # Check if it's equippable
        has_equippable = item.components.has(ComponentType.EQUIPPABLE)
        
        assert has_equippable, \
            f"Ring should have EQUIPPABLE component. Ring components: {list(item.components._components.keys())}"
        
        # Try to equip it
        if has_equippable:
            results = player.equipment.toggle_equip(item)
            
            # Verify it was equipped
            assert player.equipment.left_ring == ring or player.equipment.right_ring == ring, \
                "Ring should be equipped after toggle_equip"
        else:
            pytest.fail("Ring doesn't have EQUIPPABLE component!")
    
    def test_identify_missing_component_registration(self):
        """Debug test to identify if components are properly registered."""
        ring = create_test_ring("Debug Ring")
        
        print(f"\n=== Debug Ring Component Registration ===")
        print(f"Ring name: {ring.name}")
        print(f"ring.equippable attribute: {ring.equippable}")
        print(f"ring.item attribute: {ring.item}")
        print(f"ring.ring attribute: {ring.ring}")
        print(f"\nComponent Registry contents:")
        
        for comp_type in [ComponentType.EQUIPPABLE, ComponentType.ITEM, ComponentType.RING]:
            has_it = ring.components.has(comp_type)
            print(f"  {comp_type.name}: {has_it}")
            if has_it:
                comp = ring.components.get(comp_type)
                print(f"    -> {comp}")
        
        # Assertions
        assert ring.equippable is not None, "Ring should have equippable attribute"
        assert ring.components.has(ComponentType.EQUIPPABLE), \
            "Ring's EQUIPPABLE should be in ComponentRegistry"


class TestRingEquippingBugFix:
    """Regression tests for the ring equipping bug (Oct 2025)."""
    
    def test_ring_with_generic_RING_slot_can_equip(self):
        """
        BUG FIX: Rings created with slot=EquipmentSlots.RING (generic) should equip.
        
        The bug was that toggle_equip checked slot_map.get(slot) BEFORE handling
        the special RING case, causing it to return empty results.
        """
        player = create_test_player()
        
        # Create ring with generic RING slot (this is what entity_factory does)
        ring = create_test_ring("Ring of Testing", RingEffect.PROTECTION)
        assert ring.equippable.slot == EquipmentSlots.RING, \
            "Ring should have generic RING slot"
        
        player.inventory.add_item(ring)
        
        # This should NOT return empty results
        results = player.equipment.toggle_equip(ring)
        
        assert len(results) > 0, \
            "toggle_equip should return results (not empty list)"
        
        # Ring should be equipped
        assert player.equipment.left_ring == ring or player.equipment.right_ring == ring, \
            "Ring should be equipped in left or right slot"
        
        # Should have a success message
        assert any('equipped' in str(result).lower() for result in results), \
            "Should have equipped message in results"
    
    def test_toggle_equip_does_not_early_return_for_ring_slot(self):
        """Verify that RING slot doesn't trigger the 'unknown slot' early return."""
        player = create_test_player()
        ring = create_test_ring()
        
        player.inventory.add_item(ring)
        
        # Call toggle_equip
        results = player.equipment.toggle_equip(ring)
        
        # Before the fix, this returned [] (empty list)
        # After the fix, it should return at least one result
        assert results != [], \
            "toggle_equip should NOT return empty list for rings"
        assert len(results) >= 1, \
            f"toggle_equip should return at least 1 result, got {len(results)}"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])

