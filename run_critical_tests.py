#!/usr/bin/env python3
"""Run Phase 5 critical path tests without pytest dependency.

This is a simple test runner that can be executed directly to verify
critical functionality is working.

Usage:
    python3 run_critical_tests.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from entity import Entity
from components.fighter import Fighter
from components.victory import Victory
from game_states import GameStates
from map_objects.game_map import GameMap
from game_messages import MessageLog
from fov_functions import initialize_fov


def setup_minimal_game():
    """Create minimal game state for testing."""
    # Create player with victory component
    player = Entity(
        x=10, y=10, char='@', color=(255, 255, 255), name='Player',
        blocks=True, fighter=Fighter(hp=100, defense=5, power=5, xp=0)
    )
    player.victory = Victory()
    player.victory.owner = player
    
    # Create empty 30x30 map
    game_map = GameMap(width=30, height=30, dungeon_level=25)
    for x in range(30):
        for y in range(30):
            game_map.tiles[x][y].blocked = False
            game_map.tiles[x][y].block_sight = False
    
    entities = [player]
    message_log = MessageLog(x=0, width=40, height=5)
    fov_map = initialize_fov(game_map)
    
    from engine.game_state_manager import GameStateManager, GameState
    state_manager = GameStateManager()
    game_state = GameState(
        player=player,
        entities=entities,
        game_map=game_map,
        message_log=message_log,
        fov_map=fov_map,
        current_state=GameStates.PLAYERS_TURN
    )
    state_manager.state = game_state
    
    return player, entities, game_map, message_log, state_manager


def test_pickup_ruby_heart():
    """Test 1: Picking up Ruby Heart spawns portal."""
    print("\n" + "="*80)
    print("TEST 1: Ruby Heart Pickup → Portal Spawn")
    print("="*80)
    
    player, entities, game_map, message_log, state_manager = setup_minimal_game()
    
    # Create Ruby Heart at player location
    ruby_heart = Entity(
        x=10, y=10, char='♥', color=(220, 20, 60), name='Ruby Heart',
        blocks=False
    )
    ruby_heart.triggers_victory = True
    ruby_heart.is_quest_item = True
    entities.append(ruby_heart)
    
    print(f"  Setup: Player at ({player.x}, {player.y}), Ruby Heart at ({ruby_heart.x}, {ruby_heart.y})")
    
    # Use PickupService
    from services.pickup_service import get_pickup_service
    pickup_service = get_pickup_service(state_manager)
    result = pickup_service.execute_pickup(source="test")
    
    print(f"  Pickup result: success={result.success}, victory_triggered={result.victory_triggered}")
    
    # Check assertions
    portal = next((e for e in entities if hasattr(e, 'is_portal') and e.is_portal), None)
    
    if not result.success:
        print("  ❌ FAIL: Ruby Heart pickup failed")
        return False
    
    if not result.victory_triggered:
        print("  ❌ FAIL: Victory not triggered")
        return False
    
    if portal is None:
        print(f"  ❌ FAIL: Portal not spawned (found {len(entities)} entities)")
        for e in entities:
            print(f"    - {e.name} at ({e.x}, {e.y}), is_portal={getattr(e, 'is_portal', False)}")
        return False
    
    if state_manager.state.current_state != GameStates.RUBY_HEART_OBTAINED:
        print(f"  ❌ FAIL: State is {state_manager.state.current_state}, expected RUBY_HEART_OBTAINED")
        return False
    
    print(f"  ✅ PASS: Portal spawned at ({portal.x}, {portal.y}), state = {state_manager.state.current_state}")
    return True


def test_portal_entry():
    """Test 2: Stepping on portal triggers confrontation."""
    print("\n" + "="*80)
    print("TEST 2: Step on Portal → Confrontation Triggered")
    print("="*80)
    
    player, entities, game_map, message_log, state_manager = setup_minimal_game()
    
    # Setup: Player has Ruby Heart
    player.victory.obtain_ruby_heart(player.x, player.y)
    state_manager.set_game_state(GameStates.RUBY_HEART_OBTAINED)
    
    # Create portal at adjacent tile
    portal = Entity(
        x=11, y=10, char='O', color=(255, 0, 255), name="Entity's Portal",
        blocks=False
    )
    portal.is_portal = True
    entities.append(portal)
    
    print(f"  Setup: Player at ({player.x}, {player.y}), Portal at ({portal.x}, {portal.y})")
    print(f"  State: {state_manager.state.current_state}")
    print(f"  Player has Ruby Heart: {player.victory.has_ruby_heart}")
    
    # Use MovementService to move onto portal
    from services.movement_service import get_movement_service
    movement_service = get_movement_service(state_manager)
    result = movement_service.execute_movement(1, 0, source="test")
    
    print(f"  Movement result: success={result.success}, portal_entry={result.portal_entry}")
    print(f"  Player moved to: ({player.x}, {player.y})")
    
    # Check assertions
    if not result.success:
        print("  ❌ FAIL: Movement failed")
        return False
    
    if not result.portal_entry:
        print("  ❌ FAIL: Portal entry not detected")
        print(f"    Player at ({player.x}, {player.y}), Portal at ({portal.x}, {portal.y})")
        print(f"    Same coords? {player.x == portal.x and player.y == portal.y}")
        return False
    
    if player.x != portal.x or player.y != portal.y:
        print(f"  ❌ FAIL: Player not on portal")
        return False
    
    print(f"  ✅ PASS: Portal entry detected, player at ({player.x}, {player.y})")
    return True


def test_full_flow():
    """Test 3: Full flow from pickup to portal entry."""
    print("\n" + "="*80)
    print("TEST 3: Full Flow - Pickup → Portal Spawn → Portal Entry")
    print("="*80)
    
    player, entities, game_map, message_log, state_manager = setup_minimal_game()
    
    # Step 1: Create Ruby Heart
    ruby_heart = Entity(
        x=10, y=10, char='♥', color=(220, 20, 60), name='Ruby Heart',
        blocks=False
    )
    ruby_heart.triggers_victory = True
    entities.append(ruby_heart)
    
    print(f"  Step 1: Picking up Ruby Heart at ({ruby_heart.x}, {ruby_heart.y})")
    
    # Step 2: Pick up Ruby Heart
    from services.pickup_service import get_pickup_service
    pickup_service = get_pickup_service(state_manager)
    pickup_result = pickup_service.execute_pickup(source="test")
    
    if not pickup_result.success or not pickup_result.victory_triggered:
        print(f"  ❌ FAIL at Step 1: Pickup failed")
        return False
    
    # Step 3: Find portal
    portal = next((e for e in entities if hasattr(e, 'is_portal') and e.is_portal), None)
    if portal is None:
        print(f"  ❌ FAIL at Step 2: Portal not spawned")
        return False
    
    print(f"  Step 2: Portal spawned at ({portal.x}, {portal.y})")
    print(f"  Step 3: Moving player to portal...")
    
    # Step 4: Move to portal
    from services.movement_service import get_movement_service
    movement_service = get_movement_service(state_manager)
    
    dx = portal.x - player.x
    dy = portal.y - player.y
    move_result = movement_service.execute_movement(dx, dy, source="test")
    
    if not move_result.success:
        print(f"  ❌ FAIL at Step 3: Movement failed")
        return False
    
    if not move_result.portal_entry:
        print(f"  ❌ FAIL at Step 3: Portal entry not detected")
        print(f"    Player at ({player.x}, {player.y}), Portal at ({portal.x}, {portal.y})")
        return False
    
    print(f"  ✅ PASS: Full flow complete - player at ({player.x}, {player.y})")
    return True


def main():
    """Run all critical tests."""
    print("\n" + "█"*80)
    print("█" + " "*78 + "█")
    print("█" + "  PHASE 5 CRITICAL PATH TESTS".center(78) + "█")
    print("█" + " "*78 + "█")
    print("█"*80)
    
    tests = [
        ("Ruby Heart Pickup", test_pickup_ruby_heart),
        ("Portal Entry", test_portal_entry),
        ("Full Flow", test_full_flow),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed, None))
        except Exception as e:
            print(f"  ❌ EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False, str(e)))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for name, passed, error in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {name}")
        if error:
            print(f"         Error: {error}")
    
    total = len(results)
    passed_count = sum(1 for _, p, _ in results if p)
    
    print("\n" + "="*80)
    if passed_count == total:
        print(f"✅ ALL {total} TESTS PASSED - Phase 5 is working correctly!")
        print("="*80 + "\n")
        return 0
    else:
        print(f"❌ {total - passed_count}/{total} TESTS FAILED - Phase 5 is broken!")
        print("="*80 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())

