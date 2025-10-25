#!/usr/bin/env python
"""Test script to verify victory sequence triggers correctly."""

import os
os.environ['YARL_TESTING_MODE'] = '1'

from loader_functions.initialize_new_game import get_game_variables, get_constants
from config.testing_config import set_testing_mode
from game_states import GameStates

set_testing_mode(True)
constants = get_constants()
player, entities, game_map, message_log, game_state = get_game_variables(constants)

print("=" * 60)
print("VICTORY SEQUENCE TEST")
print("=" * 60)

# Find the amulet
amulet = None
for entity in entities:
    if entity and hasattr(entity, 'name') and 'yendor' in entity.name.lower():
        amulet = entity
        break

if not amulet:
    print("❌ ERROR: Amulet not found!")
    exit(1)

print(f"\n1. AMULET FOUND:")
print(f"   Name: {amulet.name}")
print(f"   Location: ({amulet.x}, {amulet.y})")
print(f"   Has triggers_victory: {hasattr(amulet, 'triggers_victory')}")
if hasattr(amulet, 'triggers_victory'):
    print(f"   triggers_victory value: {amulet.triggers_victory}")

# Simulate pickup
print(f"\n2. SIMULATING PICKUP...")
print(f"   Before: {len(entities)} entities")
print(f"   Messages before: {len(message_log.messages)}")

# Try adding to inventory
if player.inventory:
    pickup_results = player.inventory.add_item(amulet)
    print(f"   Pickup results: {pickup_results}")
    
    for result in pickup_results:
        item_added = result.get("item_added")
        message = result.get("message")
        print(f"   - item_added: {item_added}")
        print(f"   - message: {message}")
        
        if item_added:
            print(f"\n3. ITEM ADDED TO INVENTORY")
            print(f"   Checking triggers_victory...")
            if hasattr(amulet, 'triggers_victory') and amulet.triggers_victory:
                print(f"   ✅ triggers_victory is True!")
                print(f"\n4. TRIGGERING VICTORY MANAGER...")
                
                from victory_manager import get_victory_manager
                victory_mgr = get_victory_manager()
                
                try:
                    victory_mgr.handle_amulet_pickup(player, entities, game_map, message_log)
                    print(f"   ✅ Victory manager called successfully")
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"   ❌ triggers_victory not found or False!")

print(f"\n5. AFTER PICKUP:")
print(f"   Messages after: {len(message_log.messages)}")
print(f"   Last 5 messages:")
for msg in message_log.messages[-5:]:
    print(f"     - {msg.text}")

print(f"\n6. CHECKING FOR PORTAL:")
portal_found = False
for entity in entities:
    if entity and hasattr(entity, 'is_portal') and entity.is_portal:
        portal_found = True
        print(f"   ✅ Portal found at ({entity.x}, {entity.y})")
        print(f"      Name: {entity.name}")
        print(f"      Character: {entity.char}")
        break

if not portal_found:
    print(f"   ❌ No portal found in entities!")

print(f"\n7. CHECKING PLAYER VICTORY COMPONENT:")
if hasattr(player, 'victory') and player.victory:
    print(f"   ✅ Player has victory component")
    print(f"      has_amulet: {player.victory.has_amulet}")
    print(f"      portal_appeared: {player.victory.portal_appeared}")
    if player.victory.portal_location:
        print(f"      portal_location: {player.victory.portal_location}")
else:
    print(f"   ❌ Player has no victory component!")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)

