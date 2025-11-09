#!/usr/bin/env python3
"""Quick Phase 5 functionality test - NO dependencies, runs in seconds.

This test validates the ACTUAL game code without needing to play through manually.

Usage:
    python3 test_phase5_quick.py

Returns:
    0 if all tests pass
    1 if any test fails
"""

from __future__ import annotations

import sys
import os
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _print_header() -> None:
    print("\n" + "=" * 80)
    print("PHASE 5 QUICK VALIDATION TEST")
    print("=" * 80 + "\n")


def _failure(message: str, *, exception: Optional[BaseException] = None) -> int:
    print(message)
    if exception is not None:
        import traceback

        traceback.print_exc()
    return 1


def run_phase5_quick_validation() -> int:
    """Execute the quick validation script and return an exit code."""
    _print_header()

    # Test 1: Can we import the services?
    print("Test 1: Importing services...")
    try:
        from services.movement_service import MovementService, get_movement_service
        from services.pickup_service import PickupService, get_pickup_service
        print("  ✅ Services import successfully\n")
    except Exception as exc:  # pragma: no cover - the detail is printed for humans
        return _failure(f"  ❌ FAIL: Cannot import services: {exc}\n", exception=exc)

    # Test 2: Can we create a minimal game state?
    print("Test 2: Creating minimal game state...")
    try:
        from entity import Entity
        from components.get_component_optional(ComponentType.FIGHTER) import Fighter
        from components.victory import Victory
        from components.require_component(ComponentType.INVENTORY) import Inventory
        from components.component_registry import ComponentType
        from game_states import GameStates

        player = Entity(
            x=10,
            y=10,
            char='@',
            color=(255, 255, 255),
            name='Player',
            blocks=True,
            fighter=Fighter(hp=100, defense=5, power=5, xp=0)
        )

        # Add inventory
        player.inventory = Inventory(capacity=25)
        player.components.add(ComponentType.INVENTORY, player.require_component(ComponentType.INVENTORY))

        # Add victory component
        player.victory = Victory()
        player.victory.owner = player

        entities = [player]

        print(f"  ✅ Player created at ({player.x}, {player.y})\n")
    except Exception as exc:  # pragma: no cover - diagnostics only
        return _failure(f"  ❌ FAIL: Cannot create game state: {exc}\n", exception=exc)

    # Test 3: Create Ruby Heart
    print("Test 3: Creating Ruby Heart...")
    try:
        ruby_heart = Entity(
            x=10,
            y=10,
            char='♥',
            color=(220, 20, 60),
            name='Ruby Heart',
            blocks=False
        )
        from components.get_component_optional(ComponentType.ITEM) import Item

        ruby_heart.item = Item(use_function=None)
        ruby_heart.triggers_victory = True
        ruby_heart.is_quest_item = True
        ruby_heart.cannot_drop = True
        entities.append(ruby_heart)

        print(f"  ✅ Ruby Heart created at ({ruby_heart.x}, {ruby_heart.y})")
        print(f"     triggers_victory = {ruby_heart.triggers_victory}\n")
    except Exception as exc:  # pragma: no cover - diagnostics only
        return _failure(f"  ❌ FAIL: Cannot create Ruby Heart: {exc}\n", exception=exc)

    # Test 4: Create state manager and services
    print("Test 4: Creating state manager and services...")
    try:
        from engine.game_state_manager import GameStateManager, GameState
        from map_objects.game_map import GameMap
        from game_messages import MessageLog
        from fov_functions import initialize_fov

        # Create minimal map
        game_map = GameMap(width=30, height=30, dungeon_level=25)
        # Make all tiles walkable for testing
        for x in range(30):
            for y in range(30):
                game_map.tiles[x][y].blocked = False
                game_map.tiles[x][y].block_sight = False

        message_log = MessageLog(x=0, width=40, height=5)
        fov_map = initialize_fov(game_map)

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

        pickup_service = get_pickup_service(state_manager)
        movement_service = get_movement_service(state_manager)

        print(f"  ✅ Services initialized\n")
    except Exception as exc:  # pragma: no cover - diagnostics only
        return _failure(f"  ❌ FAIL: Cannot create services: {exc}\n", exception=exc)

    # Test 5: Pick up Ruby Heart
    print("Test 5: Picking up Ruby Heart with PickupService...")
    print(f"  Player at: ({player.x}, {player.y})")
    print(f"  Ruby Heart at: ({ruby_heart.x}, {ruby_heart.y})")
    print(f"  Entities before: {len(entities)}")

    try:
        result = pickup_service.execute_pickup(source="test")

        print("  Pickup result:")
        print(f"    - success: {result.success}")
        print(f"    - victory_triggered: {result.victory_triggered}")
        print(f"    - messages: {len(result.messages)}")

        if not result.success:
            print("  ❌ FAIL: Pickup failed\n")
            return 1

        if not result.victory_triggered:
            print("  ❌ FAIL: Victory not triggered\n")
            return 1

        # Check if portal spawned
        portal = next((e for e in entities if hasattr(e, 'is_portal') and e.is_portal), None)
        if portal is None:
            print("  ❌ FAIL: Portal not spawned")
            print(f"  Entities after: {len(entities)}")
            for entity in entities:
                print(
                    f"    - {entity.name} at ({entity.x}, {entity.y}), "
                    f"is_portal={getattr(entity, 'is_portal', False)}"
                )
            print()
            return 1

        print(f"  ✅ Portal spawned at ({portal.x}, {portal.y})")
        print(f"  ✅ State is now: {state_manager.state.current_state}\n")

    except Exception as exc:  # pragma: no cover - diagnostics only
        return _failure(f"  ❌ FAIL: Exception during pickup: {exc}\n", exception=exc)

    # Test 6: Move onto portal
    print("Test 6: Moving onto portal with MovementService...")
    print(f"  Player at: ({player.x}, {player.y})")
    print(f"  Portal at: ({portal.x}, {portal.y})")
    print(f"  Current state: {state_manager.state.current_state}")
    print(f"  Player has Ruby Heart: {player.victory.has_ruby_heart}")

    dx = portal.x - player.x
    dy = portal.y - player.y
    print(f"  Movement delta: ({dx}, {dy})")

    try:
        result = movement_service.execute_movement(dx, dy, source="test")

        print("  Movement result:")
        print(f"    - success: {result.success}")
        print(f"    - portal_entry: {result.portal_entry}")
        print(f"    - new_position: {result.new_position}")
        print(f"    - messages: {len(result.messages)}")

        if not result.success:
            print(f"    - blocked_by_wall: {result.blocked_by_wall}")
            print(f"    - blocked_by_entity: {result.blocked_by_entity}")
            print("  ❌ FAIL: Movement failed\n")
            return 1

        if not result.portal_entry:
            print("  ❌ FAIL: Portal entry not detected")
            print(f"  Player final position: ({player.x}, {player.y})")
            print(f"  Portal position: ({portal.x}, {portal.y})")
            print(f"  Positions match: {player.x == portal.x and player.y == portal.y}")
            print()
            return 1

        print("  ✅ Portal entry detected!")
        print(f"  ✅ Player on portal at ({player.x}, {player.y})\n")
    except Exception as exc:  # pragma: no cover - diagnostics only
        return _failure(f"  ❌ FAIL: Exception during movement: {exc}\n", exception=exc)

    print("=" * 80)
    print("✅ ALL TESTS PASSED - Phase 5 core functionality is working!")
    print("=" * 80 + "\n")
    print("If portal isn't working in the actual game:")
    print("  1. Restart the game (code may not have reloaded)")
    print("  2. Check console for errors during game startup")
    print("  3. Verify you're in RUBY_HEART_OBTAINED state (check sidebar)\n")

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    sys.exit(run_phase5_quick_validation())
