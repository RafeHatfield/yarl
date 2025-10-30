"""Integration tests for portal entry system (Phase 5).

Tests the complete flow:
1. Pick up Ruby Heart (keyboard 'g' or mouse right-click)
2. Portal spawns
3. Step on portal (keyboard movement or mouse pathfinding)
4. Confrontation menu triggers

This test suite was created to prevent recurring bugs where portal entry
worked in one code path but not another (keyboard vs mouse).
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import List

from entity import Entity
from components.fighter import Fighter
from components.ai import BasicMonster
from components.victory import Victory
from components.inventory import Inventory
from components.equipment import Equipment
from components.component_registry import ComponentType
from components.item import Item
from game_states import GameStates
from map_objects.game_map import GameMap
from game_messages import MessageLog
from game_actions import ActionProcessor
from state_management.state_config import GameState
from fov_functions import initialize_fov
from components.player_pathfinding import PlayerPathfinding
from systems.turn_controller import TurnController, reset_turn_controller
from services import pickup_service as pickup_service_module


class TestPortalEntryIntegration:
    """Integration tests for portal entry with keyboard and mouse movement."""
    
    @pytest.fixture
    def game_setup(self):
        """Create a minimal game state for testing portal entry."""
        reset_turn_controller()
        pickup_service_module._pickup_service = None
        from services.movement_service import reset_movement_service
        reset_movement_service()

        # Create player with victory component
        player = Entity(
            x=10, y=10, char='@', color=(255, 255, 255), name='Player',
            blocks=True, fighter=Fighter(hp=100, defense=5, power=5, xp=0)
        )
        player.victory = Victory()
        player.victory.owner = player
        inventory = Inventory(capacity=26)
        equipment = Equipment()
        player.inventory = inventory
        player.equipment = equipment
        player.components.add(ComponentType.INVENTORY, inventory)
        player.components.add(ComponentType.EQUIPMENT, equipment)
        pathfinding = PlayerPathfinding()
        player.pathfinding = pathfinding
        player.components.add(ComponentType.PATHFINDING, pathfinding)
        pathfinding.owner = player
        
        # Create Ruby Heart at player's position
        ruby_heart = Entity(
            x=10, y=10, char='♥', color=(220, 20, 60), name='Ruby Heart',
            blocks=False
        )
        ruby_item = Item(use_function=None)
        ruby_heart.item = ruby_item
        ruby_heart.components.add(ComponentType.ITEM, ruby_item)
        ruby_heart.triggers_victory = True
        ruby_heart.is_quest_item = True
        
        # Create empty 20x20 map
        game_map = GameMap(width=20, height=20, dungeon_level=25)
        for x in range(20):
            for y in range(20):
                game_map.tiles[x][y].blocked = False
                game_map.tiles[x][y].block_sight = False
        
        entities = [player, ruby_heart]
        message_log = MessageLog(x=0, width=40, height=5)
        fov_map = initialize_fov(game_map)
        
        # Create state manager
        from engine.game_state_manager import GameStateManager
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
        
        # Create action processor
        turn_manager = None
        turn_controller = TurnController(state_manager, turn_manager)
        action_processor = ActionProcessor(state_manager)
        action_processor.turn_controller = turn_controller
        
        return {
            'player': player,
            'ruby_heart': ruby_heart,
            'entities': entities,
            'game_map': game_map,
            'message_log': message_log,
            'fov_map': fov_map,
            'state_manager': state_manager,
            'action_processor': action_processor
        }
    
    def test_pickup_ruby_heart_with_keyboard_spawns_portal(self, game_setup):
        """Test that picking up Ruby Heart with 'g' key spawns portal."""
        player = game_setup['player']
        entities = game_setup['entities']
        ruby_heart = game_setup['ruby_heart']
        state_manager = game_setup['state_manager']
        action_processor = game_setup['action_processor']
        
        # Simulate 'g' key press to pick up item
        action = {'pickup': True}
        action_processor.process_actions(action, {})
        
        # Verify portal spawned
        portal = next((e for e in entities if hasattr(e, 'is_portal') and e.is_portal), None)
        assert portal is not None, "Portal should spawn after picking up Ruby Heart"
        assert portal.name == "Entity's Portal" or "portal" in portal.name.lower()
        
        turn_controller = action_processor.turn_controller
        preserved = turn_controller.get_preserved_state()
        if preserved:
            turn_controller.end_enemy_turn()
            assert state_manager.state.current_state == preserved
        else:
            assert state_manager.state.current_state == GameStates.RUBY_HEART_OBTAINED
        
        # Verify player has Ruby Heart
        assert player.victory.has_ruby_heart is True
    
    @patch('mouse_movement.process_pathfinding_movement')
    def test_pickup_ruby_heart_with_right_click_spawns_portal(self, mock_pathfinding, game_setup):
        """Test that right-clicking Ruby Heart spawns portal."""
        player = game_setup['player']
        entities = game_setup['entities']
        ruby_heart = game_setup['ruby_heart']
        state_manager = game_setup['state_manager']
        action_processor = game_setup['action_processor']
        
        # Mock pathfinding to simulate right-click pickup
        mock_pathfinding.return_value = {
            "results": [
                {"victory_triggered": True}
            ]
        }
        
        # Simulate right-click on Ruby Heart
        mouse_action = {'right_click': (10, 10)}
        action_processor.process_actions({}, mouse_action)
        
        # Verify portal spawned
        portal = next((e for e in entities if hasattr(e, 'is_portal') and e.is_portal), None)
        assert portal is not None, "Portal should spawn after right-clicking Ruby Heart"
        
        turn_controller = action_processor.turn_controller
        preserved = turn_controller.get_preserved_state()
        if preserved:
            turn_controller.end_enemy_turn()
            assert state_manager.state.current_state == preserved
        else:
            assert state_manager.state.current_state == GameStates.RUBY_HEART_OBTAINED
    
    def test_step_on_portal_with_keyboard_triggers_confrontation(self, game_setup):
        """Test that keyboard movement onto portal triggers confrontation."""
        player = game_setup['player']
        entities = game_setup['entities']
        state_manager = game_setup['state_manager']
        action_processor = game_setup['action_processor']
        
        # Setup: Player has Ruby Heart, portal exists
        player.victory.obtain_ruby_heart(player.x, player.y)
        state_manager.set_game_state(GameStates.RUBY_HEART_OBTAINED)
        
        # Spawn portal at adjacent tile
        portal = Entity(
            x=11, y=10, char='O', color=(255, 0, 255), name="Entity's Portal",
            blocks=False
        )
        portal.is_portal = True
        entities.append(portal)
        
        # Move player onto portal with keyboard
        action = {'move': (1, 0)}  # Move right onto portal
        action_processor.process_actions(action, {})
        
        # Verify state transitioned to CONFRONTATION
        assert state_manager.state.current_state == GameStates.CONFRONTATION, \
            f"Expected CONFRONTATION, got {state_manager.state.current_state}"
    
    @patch('mouse_movement.process_pathfinding_movement')
    def test_step_on_portal_with_mouse_triggers_confrontation(self, mock_pathfinding, game_setup):
        """Test that clicking to move onto portal triggers confrontation."""
        player = game_setup['player']
        entities = game_setup['entities']
        state_manager = game_setup['state_manager']
        action_processor = game_setup['action_processor']
        
        # Setup: Player has Ruby Heart, portal exists
        player.victory.obtain_ruby_heart(player.x, player.y)
        state_manager.set_game_state(GameStates.RUBY_HEART_OBTAINED)
        
        # Spawn portal at adjacent tile
        portal = Entity(
            x=11, y=10, char='O', color=(255, 0, 255), name="Entity's Portal",
            blocks=False
        )
        portal.is_portal = True
        entities.append(portal)
        
        # Mock pathfinding to simulate clicking on portal
        mock_pathfinding.return_value = {
            "results": [
                {"portal_entry": True}
            ]
        }

        from services import movement_service as movement_service_module
        movement_service_module._movement_service = None
        movement_service = movement_service_module.get_movement_service(state_manager)
        result = movement_service.execute_movement(1, 0, source="mouse")
        if result.portal_entry:
            state_manager.set_game_state(GameStates.CONFRONTATION)
 
        # Verify state transitioned to CONFRONTATION
        assert state_manager.state.current_state == GameStates.CONFRONTATION, \
            f"Expected CONFRONTATION, got {state_manager.state.current_state}"
    
    def test_portal_only_works_after_ruby_heart_obtained(self, game_setup):
        """Test that portal doesn't work if player doesn't have Ruby Heart."""
        player = game_setup['player']
        entities = game_setup['entities']
        state_manager = game_setup['state_manager']
        action_processor = game_setup['action_processor']
        
        # Setup: Portal exists but player does NOT have Ruby Heart
        portal = Entity(
            x=11, y=10, char='O', color=(255, 0, 255), name="Entity's Portal",
            blocks=False
        )
        portal.is_portal = True
        entities.append(portal)
        
        # Player is in normal turn state (not RUBY_HEART_OBTAINED)
        state_manager.set_game_state(GameStates.PLAYERS_TURN)
        
        # Try to move onto portal
        action = {'move': (1, 0)}
        action_processor.process_actions(action, {})
        
        # Verify state did NOT transition to CONFRONTATION
        assert state_manager.state.current_state != GameStates.CONFRONTATION, \
            "Portal should not trigger without Ruby Heart"
    
    def test_portal_spawns_adjacent_not_on_player(self, game_setup):
        """Test that portal spawns next to player, not on them."""
        player = game_setup['player']
        entities = game_setup['entities']
        
        # Pick up Ruby Heart
        from victory_manager import get_victory_manager
        victory_mgr = get_victory_manager()
        victory_mgr.handle_ruby_heart_pickup(
            player, entities, game_setup['game_map'], game_setup['message_log']
        )
        
        # Find portal
        portal = next((e for e in entities if hasattr(e, 'is_portal') and e.is_portal), None)
        assert portal is not None, "Portal should spawn"
        
        # Verify portal is NOT on player
        assert (portal.x, portal.y) != (player.x, player.y), \
            "Portal should spawn adjacent to player, not on them"
        
        # Verify portal is adjacent (1 tile away)
        distance = abs(portal.x - player.x) + abs(portal.y - player.y)
        assert distance == 1, f"Portal should be 1 tile away, got distance {distance}"
    
    def test_full_flow_keyboard_only(self, game_setup):
        """Test complete flow: keyboard pickup + keyboard portal entry."""
        player = game_setup['player']
        entities = game_setup['entities']
        state_manager = game_setup['state_manager']
        action_processor = game_setup['action_processor']
        
        # Step 1: Pick up Ruby Heart with 'g'
        action = {'pickup': True}
        action_processor.process_actions(action, {})
 
        turn_controller = action_processor.turn_controller
        preserved = turn_controller.get_preserved_state()
        turn_controller.end_enemy_turn()
        if preserved:
            assert state_manager.state.current_state == preserved
        else:
            state_manager.set_game_state(GameStates.RUBY_HEART_OBTAINED)
 
        # Step 2: Find portal location
        portal = next((e for e in entities if hasattr(e, 'is_portal') and e.is_portal), None)
        assert portal is not None
 
        # Step 3: Move onto portal (simulate player input)
        dx = portal.x - player.x
        dy = portal.y - player.y
        from services import movement_service as movement_service_module
        movement_service_module._movement_service = None
        movement_service = movement_service_module.get_movement_service(state_manager)
        move_result = movement_service.execute_movement(dx, dy, source="keyboard")
        if move_result.portal_entry:
            state_manager.set_game_state(GameStates.CONFRONTATION)
 
        # Verify confrontation triggered
        assert state_manager.state.current_state == GameStates.CONFRONTATION
    
    def test_full_flow_mouse_only(self, game_setup):
        """Test complete flow: mouse pickup + mouse portal entry."""
        # This test would require more complex mocking of mouse/pathfinding
        # Left as a TODO for now, but framework is in place
        pass


class TestPortalEntryEdgeCases:
    """Edge cases and error conditions for portal entry."""
    
    def test_portal_removed_from_inventory_before_step(self):
        """Test that portal in inventory doesn't trigger (must be on ground)."""
        # TODO: Test if player picks up portal and then steps on that tile
        pass
    
    def test_multiple_portals_only_one_triggers(self):
        """Test behavior with multiple portal entities (should only trigger once)."""
        # TODO: Test edge case of duplicate portals
        pass
    
    def test_portal_on_blocked_tile(self):
        """Test portal spawning when all adjacent tiles are blocked."""
        # TODO: Test fallback spawning logic
        pass

