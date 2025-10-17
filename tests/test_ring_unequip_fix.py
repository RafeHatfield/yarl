"""Test ring equipping/unequipping logic - regression test for the double-ring bug.

This test verifies the fix for the issue where:
- Trying to unequip the right ring would unequip the left ring instead
- Second attempt would put the same ring on both fingers
"""
import pytest
from entity import Entity
from components.equipment import Equipment, EquipmentSlots
from components.equippable import Equippable
from components.inventory import Inventory
from components.item import Item
from components.ring import Ring, RingEffect


def test_unequip_right_ring_correctly():
    """Test that unequipping the right ring doesn't affect the left ring."""
    # Create player with equipment and inventory
    player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
    player.equipment = Equipment(player)
    player.inventory = Inventory(26)
    
    # Create two different rings
    ring1 = Entity(0, 0, '=', (255, 215, 0), 'Ring of Strength', blocks=False)
    ring1.equippable = Equippable(EquipmentSlots.RING, strength_bonus=2)
    ring1.item = Item(use_function=None, stack_size=1)
    ring1.ring = Ring(RingEffect.STRENGTH, effect_strength=2, owner=ring1)
    
    ring2 = Entity(0, 0, '=', (255, 100, 100), 'Ring of Protection', blocks=False)
    ring2.equippable = Equippable(EquipmentSlots.RING, armor_bonus=2)
    ring2.item = Item(use_function=None, stack_size=1)
    ring2.ring = Ring(RingEffect.PROTECTION, effect_strength=2, owner=ring2)
    
    # Equip ring1 to left finger
    results = player.equipment.toggle_equip(ring1)
    assert any(r.get('equipped') == ring1 for r in results)
    assert player.equipment.left_ring == ring1
    assert player.equipment.right_ring is None
    
    # Equip ring2 to right finger
    results = player.equipment.toggle_equip(ring2)
    assert any(r.get('equipped') == ring2 for r in results)
    assert player.equipment.left_ring == ring1
    assert player.equipment.right_ring == ring2
    
    # Now unequip the RIGHT ring (ring2)
    results = player.equipment.toggle_equip(ring2)
    assert any(r.get('dequipped') == ring2 for r in results)
    
    # Verify: left ring should still be equipped, right ring should be empty
    assert player.equipment.left_ring == ring1, "Left ring should still be ring1!"
    assert player.equipment.right_ring is None, "Right ring should be empty!"
    
    # Try again - unequip the LEFT ring (ring1)
    results = player.equipment.toggle_equip(ring1)
    assert any(r.get('dequipped') == ring1 for r in results)
    
    # Verify: both rings should be empty now
    assert player.equipment.left_ring is None
    assert player.equipment.right_ring is None


def test_unequip_left_ring_correctly():
    """Test that unequipping the left ring works correctly."""
    # Create player with equipment
    player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
    player.equipment = Equipment(player)
    player.inventory = Inventory(26)
    
    # Create two rings
    ring1 = Entity(0, 0, '=', (255, 215, 0), 'Ring of Strength', blocks=False)
    ring1.equippable = Equippable(EquipmentSlots.RING, strength_bonus=2)
    ring1.item = Item(use_function=None, stack_size=1)
    ring1.ring = Ring(RingEffect.STRENGTH, effect_strength=2, owner=ring1)
    
    ring2 = Entity(0, 0, '=', (255, 100, 100), 'Ring of Protection', blocks=False)
    ring2.equippable = Equippable(EquipmentSlots.RING, armor_bonus=2)
    ring2.item = Item(use_function=None, stack_size=1)
    ring2.ring = Ring(RingEffect.PROTECTION, effect_strength=2, owner=ring2)
    
    # Equip both rings
    player.equipment.toggle_equip(ring1)  # Left
    player.equipment.toggle_equip(ring2)  # Right
    
    # Unequip the LEFT ring
    results = player.equipment.toggle_equip(ring1)
    assert any(r.get('dequipped') == ring1 for r in results)
    
    # Verify: left should be empty, right should still have ring2
    assert player.equipment.left_ring is None
    assert player.equipment.right_ring == ring2


def test_equip_same_ring_twice_not_possible():
    """Test that you can't equip the same ring to both fingers."""
    player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
    player.equipment = Equipment(player)
    player.inventory = Inventory(26)
    
    # Create one ring
    ring = Entity(0, 0, '=', (255, 215, 0), 'Ring of Strength', blocks=False)
    ring.equippable = Equippable(EquipmentSlots.RING, strength_bonus=2)
    ring.item = Item(use_function=None, stack_size=1)
    ring.ring = Ring(RingEffect.STRENGTH, effect_strength=2, owner=ring)
    
    # Equip to left finger
    player.equipment.toggle_equip(ring)
    assert player.equipment.left_ring == ring
    assert player.equipment.right_ring is None
    
    # Try to equip the SAME ring again - should unequip it instead
    results = player.equipment.toggle_equip(ring)
    assert any(r.get('dequipped') == ring for r in results)
    assert player.equipment.left_ring is None
    assert player.equipment.right_ring is None


def test_ring_equipping_priority():
    """Test that rings equip to left finger first, then right finger."""
    player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
    player.equipment = Equipment(player)
    
    ring1 = Entity(0, 0, '=', (255, 215, 0), 'Ring 1', blocks=False)
    ring1.equippable = Equippable(EquipmentSlots.RING)
    ring1.item = Item(use_function=None, stack_size=1)
    ring1.ring = Ring(RingEffect.STRENGTH, effect_strength=2, owner=ring1)
    
    ring2 = Entity(0, 0, '=', (255, 100, 100), 'Ring 2', blocks=False)
    ring2.equippable = Equippable(EquipmentSlots.RING)
    ring2.item = Item(use_function=None, stack_size=1)
    ring2.ring = Ring(RingEffect.PROTECTION, effect_strength=2, owner=ring2)
    
    # First ring goes to left
    player.equipment.toggle_equip(ring1)
    assert player.equipment.left_ring == ring1
    assert player.equipment.right_ring is None
    
    # Second ring goes to right
    player.equipment.toggle_equip(ring2)
    assert player.equipment.left_ring == ring1
    assert player.equipment.right_ring == ring2


def test_replace_ring_when_both_slots_full():
    """Test that when both ring slots are full, equipping a new ring replaces the left one."""
    player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
    player.equipment = Equipment(player)
    
    ring1 = Entity(0, 0, '=', (255, 215, 0), 'Ring 1', blocks=False)
    ring1.equippable = Equippable(EquipmentSlots.RING)
    ring1.item = Item(use_function=None, stack_size=1)
    ring1.ring = Ring(RingEffect.STRENGTH, effect_strength=2, owner=ring1)
    
    ring2 = Entity(0, 0, '=', (255, 100, 100), 'Ring 2', blocks=False)
    ring2.equippable = Equippable(EquipmentSlots.RING)
    ring2.item = Item(use_function=None, stack_size=1)
    ring2.ring = Ring(RingEffect.PROTECTION, effect_strength=2, owner=ring2)
    
    ring3 = Entity(0, 0, '=', (100, 100, 255), 'Ring 3', blocks=False)
    ring3.equippable = Equippable(EquipmentSlots.RING)
    ring3.item = Item(use_function=None, stack_size=1)
    ring3.ring = Ring(RingEffect.REGENERATION, effect_strength=5, owner=ring3)
    
    # Equip two rings
    player.equipment.toggle_equip(ring1)
    player.equipment.toggle_equip(ring2)
    assert player.equipment.left_ring == ring1
    assert player.equipment.right_ring == ring2
    
    # Equip third ring - should replace left ring (ring1)
    results = player.equipment.toggle_equip(ring3)
    assert any(r.get('dequipped') == ring1 for r in results)  # ring1 was dequipped
    assert any(r.get('equipped') == ring3 for r in results)   # ring3 was equipped
    assert player.equipment.left_ring == ring3
    assert player.equipment.right_ring == ring2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

