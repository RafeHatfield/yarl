#!/usr/bin/env python3
"""
Debug script to test portal entry detection in isolation.

This script simulates the exact scenario: player steps on portal after obtaining amulet.
"""

import sys
sys.path.insert(0, '.')

from victory_manager import get_victory_manager
from entity import Entity
from components.item import Item
from game_states import GameStates
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_portal_entry_scenario():
    """Simulate the exact scenario the user is experiencing."""
    
    print("="*80)
    print("TESTING PORTAL ENTRY SCENARIO")
    print("="*80)
    
    # Create player
    player = Entity(x=10, y=10, char='@', color=(255, 255, 255), name="Player", blocks=True)
    print(f"✅ Player created at ({player.x}, {player.y})")
    
    # Create portal (on ground, adjacent to player)
    portal = Entity(x=11, y=10, char='O', color=(255, 0, 255), name="Entity Portal", blocks=False)
    portal.is_portal = True
    portal.item = Item()  # Portal is pickupable
    print(f"✅ Portal created at ({portal.x}, {portal.y})")
    print(f"   Portal has is_portal={portal.is_portal}")
    
    # Entities list (portal on ground)
    entities = [portal]
    print(f"✅ Entities list has {len(entities)} entities")
    
    # Get victory manager
    victory_mgr = get_victory_manager()
    print(f"✅ Victory manager created")
    
    # Test 1: Player NOT on portal (adjacent)
    print("\n" + "-"*80)
    print("TEST 1: Player adjacent to portal (NOT on it)")
    print("-"*80)
    print(f"Player at ({player.x}, {player.y}), Portal at ({portal.x}, {portal.y})")
    result = victory_mgr.check_portal_entry(player, entities)
    print(f"Result: {result}")
    print(f"Expected: False")
    print(f"✅ PASS" if result == False else f"❌ FAIL")
    
    # Test 2: Player moves onto portal
    print("\n" + "-"*80)
    print("TEST 2: Player moves onto portal")
    print("-"*80)
    print(f"Moving player from ({player.x}, {player.y}) to ({portal.x}, {portal.y})")
    player.x = portal.x
    player.y = portal.y
    print(f"Player now at ({player.x}, {player.y}), Portal at ({portal.x}, {portal.y})")
    result = victory_mgr.check_portal_entry(player, entities)
    print(f"Result: {result}")
    print(f"Expected: True")
    print(f"✅ PASS" if result == True else f"❌ FAIL")
    
    # Test 3: Portal in inventory (not on ground)
    print("\n" + "-"*80)
    print("TEST 3: Portal in inventory (picked up)")
    print("-"*80)
    entities_empty = []  # Portal removed from ground
    print(f"Entities list now has {len(entities_empty)} entities (portal in inventory)")
    result = victory_mgr.check_portal_entry(player, entities_empty)
    print(f"Result: {result}")
    print(f"Expected: False (portal must be on ground)")
    print(f"✅ PASS" if result == False else f"❌ FAIL")
    
    # Test 4: Portal dropped back on ground at player location
    print("\n" + "-"*80)
    print("TEST 4: Portal dropped at player's feet")
    print("-"*80)
    portal.x = player.x
    portal.y = player.y
    entities = [portal]  # Portal back on ground
    print(f"Player at ({player.x}, {player.y}), Portal at ({portal.x}, {portal.y})")
    print(f"Entities list has {len(entities)} entities")
    result = victory_mgr.check_portal_entry(player, entities)
    print(f"Result: {result}")
    print(f"Expected: True")
    print(f"✅ PASS" if result == True else f"❌ FAIL")
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print("If all tests pass, the check_portal_entry() logic is working correctly.")
    print("If portal entry doesn't work in-game, the issue is likely:")
    print("1. Game state not set to AMULET_OBTAINED")
    print("2. Movement handler not calling check_portal_entry")
    print("3. Portal coordinates don't match player coordinates")
    print("4. Portal not in entities list (picked up and in inventory)")
    print("="*80)

if __name__ == '__main__':
    test_portal_entry_scenario()

