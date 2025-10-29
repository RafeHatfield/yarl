"""Critical path tests for Phase 5 - MUST ALWAYS PASS.

These tests cover the absolute core functionality that should never break.
Run these before every commit to prevent regression.

Usage:
    pytest tests/test_phase5_critical_paths.py -v
    
Add to pre-commit hook:
    pytest tests/test_phase5_critical_paths.py --tb=short || exit 1
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
sys.path.insert(0, '/Users/rafehatfield/development/rlike')

from entity import Entity
from components.fighter import Fighter
from components.victory import Victory
from game_states import GameStates
from map_objects.game_map import GameMap
from game_messages import MessageLog
from fov_functions import initialize_fov


class TestPhase5CriticalPath:
    """Critical path tests - if these fail, Phase 5 is broken."""
    
    @pytest.fixture
    def minimal_game_state(self):
        """Minimal game state for testing."""
        from components.inventory import Inventory
        from components.component_registry import ComponentType
        
        # Reset service singletons to avoid state leakage between tests
        import services.movement_service
        import services.pickup_service
        services.movement_service._movement_service = None
        services.pickup_service._pickup_service = None
        
        # Create player with victory component
        player = Entity(
            x=10, y=10, char='@', color=(255, 255, 255), name='Player',
            blocks=True, fighter=Fighter(hp=100, defense=5, power=5, xp=0)
        )
        
        # Add inventory
        player.inventory = Inventory(capacity=25)
        player.components.add(ComponentType.INVENTORY, player.inventory)
        
        # Add victory component
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
        
        from engine.game_state_manager import GameStateManager
        state_manager = GameStateManager()
        
        # Initialize state using update_state (state is read-only property)
        state_manager.update_state(
            player=player,
            entities=entities,
            game_map=game_map,
            message_log=message_log,
            fov_map=fov_map
        )
        state_manager.set_game_state(GameStates.PLAYERS_TURN)
        
        return {
            'player': player,
            'entities': entities,
            'game_map': game_map,
            'message_log': message_log,
            'fov_map': fov_map,
            'state_manager': state_manager
        }
    
    @patch('victory_manager.VictoryManager.handle_ruby_heart_pickup')
    def test_CRITICAL_pickup_ruby_heart_spawns_portal(self, mock_handle_heart, minimal_game_state):
        """CRITICAL: Picking up Ruby Heart MUST spawn portal."""
        player = minimal_game_state['player']
        entities = minimal_game_state['entities']
        game_map = minimal_game_state['game_map']
        message_log = minimal_game_state['message_log']
        state_manager = minimal_game_state['state_manager']
        
        # Mock portal spawning (bypass entity registry requirement)
        def mock_spawn_portal(player, entities, game_map, message_log):
            """Mock that creates a portal when called."""
            portal = Entity(
                x=11, y=10, char='O', color=(255, 0, 255), name="Entity's Portal",
                blocks=False
            )
            portal.is_portal = True
            entities.append(portal)
            # Mark Ruby Heart as obtained
            player.victory.obtain_ruby_heart(player.x, player.y)
            return True
        
        mock_handle_heart.side_effect = mock_spawn_portal
        
        # Create Ruby Heart at player location
        from components.item import Item
        
        ruby_heart = Entity(
            x=10, y=10, char='♥', color=(220, 20, 60), name='Ruby Heart',
            blocks=False
        )
        ruby_heart.item = Item(use_function=None)
        ruby_heart.triggers_victory = True
        ruby_heart.is_quest_item = True
        ruby_heart.cannot_drop = True
        entities.append(ruby_heart)
        
        # Update state_manager with new entities list
        state_manager.update_state(entities=entities)
        
        # Use PickupService to pick up heart
        from services.pickup_service import get_pickup_service
        pickup_service = get_pickup_service(state_manager)
        result = pickup_service.execute_pickup(source="test")
        
        # CRITICAL ASSERTION 1: Pickup succeeded
        assert result.success, "Ruby Heart pickup must succeed"
        
        # CRITICAL ASSERTION 2: Victory triggered
        assert result.victory_triggered, "Victory must be triggered"
        
        # CRITICAL ASSERTION 3: Portal spawned
        portal = next((e for e in entities if hasattr(e, 'is_portal') and e.is_portal), None)
        assert portal is not None, "CRITICAL: Portal MUST spawn after Ruby Heart pickup"
        
        # CRITICAL ASSERTION 4: State transitioned
        assert state_manager.state.current_state == GameStates.RUBY_HEART_OBTAINED, \
            f"State must be RUBY_HEART_OBTAINED, got {state_manager.state.current_state}"
        
        print(f"✅ CRITICAL PATH PASS: Portal spawned at ({portal.x}, {portal.y})")
    
    def test_CRITICAL_step_on_portal_triggers_confrontation(self, minimal_game_state):
        """CRITICAL: Stepping on portal MUST trigger confrontation."""
        player = minimal_game_state['player']
        entities = minimal_game_state['entities']
        state_manager = minimal_game_state['state_manager']
        
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
        
        print(f"Setup: Player at ({player.x}, {player.y}), Portal at ({portal.x}, {portal.y})")
        
        # Use MovementService to move onto portal
        from services.movement_service import get_movement_service
        movement_service = get_movement_service(state_manager)
        result = movement_service.execute_movement(1, 0, source="test")  # Move right
        
        # CRITICAL ASSERTION 1: Movement succeeded
        assert result.success, "Movement onto portal must succeed"
        
        # CRITICAL ASSERTION 2: Portal entry detected
        assert result.portal_entry, "CRITICAL: Portal entry MUST be detected when stepping on portal"
        
        # CRITICAL ASSERTION 3: Player is on portal
        assert player.x == portal.x and player.y == portal.y, \
            f"Player must be on portal: player ({player.x}, {player.y}), portal ({portal.x}, {portal.y})"
        
        print(f"✅ CRITICAL PATH PASS: Portal entry detected, player at ({player.x}, {player.y})")
    
    def test_CRITICAL_full_flow_keyboard(self, minimal_game_state):
        """CRITICAL: Full flow from pickup to portal entry (keyboard simulation)."""
        player = minimal_game_state['player']
        entities = minimal_game_state['entities']
        game_map = minimal_game_state['game_map']
        state_manager = minimal_game_state['state_manager']
        
        # Step 1: Create Ruby Heart
        from components.item import Item
        
        ruby_heart = Entity(
            x=10, y=10, char='♥', color=(220, 20, 60), name='Ruby Heart',
            blocks=False
        )
        ruby_heart.item = Item(use_function=None)
        ruby_heart.triggers_victory = True
        ruby_heart.is_quest_item = True
        
        # Add to entities BEFORE updating state manager
        entities.append(ruby_heart)
        state_manager.update_state(entities=entities)
        
        # Verify Ruby Heart is in state
        assert ruby_heart in state_manager.state.entities, "Ruby Heart not in state_manager.state.entities"
        print(f"  Entities in state: {len(state_manager.state.entities)}")
        print(f"  Ruby Heart in entities: {ruby_heart in state_manager.state.entities}")
        
        # Step 2: Pick up Ruby Heart
        # Mock portal spawning (bypass entity registry)
        from unittest.mock import patch
        
        def mock_spawn_portal(player, entities, game_map, message_log):
            portal = Entity(
                x=11, y=10, char='O', color=(255, 0, 255), name="Entity's Portal",
                blocks=False
            )
            portal.is_portal = True
            entities.append(portal)
            player.victory.obtain_ruby_heart(player.x, player.y)
            return True
        
        with patch('victory_manager.VictoryManager.handle_ruby_heart_pickup', side_effect=mock_spawn_portal):
            from services.pickup_service import get_pickup_service
            pickup_service = get_pickup_service(state_manager)
            pickup_result = pickup_service.execute_pickup(source="test")
        
        assert pickup_result.success, "Step 1 failed: Ruby Heart pickup"
        assert pickup_result.victory_triggered, "Step 1 failed: Victory trigger"
        
        # Step 3: Find portal
        portal = next((e for e in entities if hasattr(e, 'is_portal') and e.is_portal), None)
        assert portal is not None, "Step 2 failed: Portal spawn"
        
        print(f"Portal found at ({portal.x}, {portal.y}), moving player there...")
        
        # Step 4: Move to portal
        from services.movement_service import get_movement_service
        movement_service = get_movement_service(state_manager)
        
        dx = portal.x - player.x
        dy = portal.y - player.y
        move_result = movement_service.execute_movement(dx, dy, source="test")
        
        assert move_result.success, f"Step 3 failed: Movement to portal"
        assert move_result.portal_entry, "Step 3 failed: Portal entry detection"
        
        print(f"✅ CRITICAL FULL FLOW PASS: Pickup → Portal spawn → Portal entry")
    
    def test_CRITICAL_portal_only_works_with_ruby_heart(self, minimal_game_state):
        """CRITICAL: Portal should NOT work without Ruby Heart."""
        player = minimal_game_state['player']
        entities = minimal_game_state['entities']
        state_manager = minimal_game_state['state_manager']
        
        # Create portal but DON'T give player Ruby Heart
        portal = Entity(
            x=11, y=10, char='O', color=(255, 0, 255), name="Entity's Portal",
            blocks=False
        )
        portal.is_portal = True
        entities.append(portal)
        
        # Player is in normal turn state (not RUBY_HEART_OBTAINED)
        state_manager.set_game_state(GameStates.PLAYERS_TURN)
        
        # Try to move onto portal
        from services.movement_service import get_movement_service
        movement_service = get_movement_service(state_manager)
        result = movement_service.execute_movement(1, 0, source="test")
        
        # CRITICAL ASSERTION: Portal entry NOT triggered
        assert not result.portal_entry, \
            "Portal must NOT trigger without Ruby Heart"
        
        print(f"✅ CRITICAL PATH PASS: Portal correctly ignored without Ruby Heart")


def run_critical_tests():
    """Run critical tests and report results."""
    print("\n" + "="*80)
    print("RUNNING PHASE 5 CRITICAL PATH TESTS")
    print("="*80 + "\n")
    
    import subprocess
    result = subprocess.run(
        ["pytest", __file__, "-v", "--tb=short"],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        print("\n❌ CRITICAL TESTS FAILED - DO NOT COMMIT")
        return False
    else:
        print("\n✅ ALL CRITICAL TESTS PASSED - SAFE TO COMMIT")
        return True


if __name__ == "__main__":
    import sys
    passed = run_critical_tests()
    sys.exit(0 if passed else 1)

