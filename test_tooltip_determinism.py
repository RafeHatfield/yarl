#!/usr/bin/env python3
"""Quick test to verify tooltip ordering is deterministic and stable.

This test creates a scenario with a corpse + weapon and verifies that
get_all_entities_at_position returns the same ordering across multiple calls.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from entity import Entity
from components.component_registry import ComponentType
from components.fighter import Fighter
from components.item import Item
from components.equippable import Equippable
from render_functions import RenderOrder
from equipment_slots import EquipmentSlots
from ui.tooltip import get_all_entities_at_position

def test_deterministic_ordering():
    """Test that tooltip ordering is stable across calls."""
    print("Testing deterministic tooltip ordering...")
    
    # Create a simple weapon (club)
    club = Entity(1, 1, 'c', (200, 200, 100), 'Club')
    club.render_order = RenderOrder.ITEM
    eq = Equippable(
        slot=EquipmentSlots.MAIN_HAND,
        defense_bonus=None,
        to_hit_bonus=0,
        damage_dice="1d6"
    )
    club.equippable = eq
    club.item = Item(use_function=None, identified=True)
    
    # Create a corpse (orc that died)
    corpse = Entity(1, 1, 'o', (100, 100, 100), 'Remains of Orc')
    corpse.render_order = RenderOrder.CORPSE
    
    # Create a player (to exclude from results)
    player = Entity(0, 0, '@', (255, 255, 255), 'Player')
    fighter = Fighter(hp=30, defense=2, power=5)
    player.fighter = fighter
    
    # Create entities list
    entities = [player, corpse, club]
    
    # Test 1: Call get_all_entities_at_position multiple times
    print("\nTest 1: Calling get_all_entities_at_position 5 times...")
    results = []
    for i in range(5):
        result = get_all_entities_at_position(1, 1, entities, player, fov_map=None)
        entity_names = [f"{e.name}(ro:{e.render_order.name})" for e in result]
        results.append(entity_names)
        print(f"  Call {i+1}: {entity_names}")
    
    # Verify all calls returned identical ordering
    all_same = all(r == results[0] for r in results)
    if all_same:
        print("✓ PASS: All calls returned identical ordering")
    else:
        print("✗ FAIL: Ordering varies across calls!")
        for i, r in enumerate(results):
            if r != results[0]:
                print(f"  Call {i+1} differs: {r}")
        return False
    
    # Test 2: Verify corpse comes after weapon (items before corpses)
    expected_order = ["Club(ro:ITEM)", "Remains of Orc(ro:CORPSE)"]
    actual_order = results[0]
    if actual_order == expected_order:
        print(f"✓ PASS: Correct ordering (items before corpses): {actual_order}")
    else:
        print(f"✗ FAIL: Expected {expected_order}, got {actual_order}")
        return False
    
    # Test 3: Shuffle entities list and verify same ordering
    print("\nTest 2: Shuffling entities list order...")
    entities_shuffled = [club, player, corpse]  # Different order
    result_shuffled = get_all_entities_at_position(1, 1, entities_shuffled, player, fov_map=None)
    entity_names_shuffled = [f"{e.name}(ro:{e.render_order.name})" for e in result_shuffled]
    
    if entity_names_shuffled == results[0]:
        print(f"✓ PASS: Shuffled input produces same output: {entity_names_shuffled}")
    else:
        print(f"✗ FAIL: Shuffled input gave different output!")
        print(f"  Expected: {results[0]}")
        print(f"  Got:      {entity_names_shuffled}")
        return False
    
    print("\n✓ All determinism tests passed!")
    return True

if __name__ == '__main__':
    try:
        success = test_deterministic_ordering()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)




