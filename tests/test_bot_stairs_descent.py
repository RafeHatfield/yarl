"""Unit tests for bot stairs descent behavior.

This test suite validates that the bot walks to stairs and descends them when
floor exploration is complete.

Test cases:
- Bot descends when standing on stairs and floor complete
- Bot walks toward stairs when floor complete but not on stairs
- Bot takes stairs after walking there (path exhausted)
- Bot doesn't descend when floor not complete
- Bot clears stairs path when enemies appear (falls back to combat)
- Bot doesn't descend on pathfinding failures (Movement blocked)
- Bot doesn't restart AutoExplore after floor complete
"""

import pytest
from unittest.mock import Mock, patch
import numpy as np

from io_layer.bot_brain import BotBrain, BotState, TERMINAL_EXPLORE_REASONS
from game_states import GameStates
from components.component_registry import ComponentType


def create_mock_game_map(width=20, height=20):
    """Create a mock game map for pathfinding tests."""
    game_map = Mock()
    game_map.width = width
    game_map.height = height
    
    # Create tiles array with all tiles walkable
    tiles = [[Mock() for _ in range(height)] for _ in range(width)]
    for x in range(width):
        for y in range(height):
            tiles[x][y].blocked = False
    game_map.tiles = tiles
    
    # Mock hazard manager
    game_map.hazard_manager = Mock()
    game_map.hazard_manager.has_hazard_at = Mock(return_value=False)
    
    return game_map


class TestBotStairsDescent:
    """Test bot automatic stairs descent for multi-floor runs."""
    
    def test_bot_descends_when_standing_on_stairs_and_floor_complete(self):
        """Bot should descend stairs when standing on them and floor is fully explored."""
        brain = BotBrain()
        
        # Setup: Player standing on stairs, floor complete
        game_state = Mock()
        game_state.current_state = GameStates.PLAYERS_TURN
        game_state.fov_map = Mock()
        game_state.game_map = create_mock_game_map()
        
        # Mock player at (10, 10)
        player = Mock()
        player.x = 10
        player.y = 10
        player.faction = Mock()
        player.components = Mock()
        player.components.has = Mock(return_value=False)
        
        # Mock healthy fighter (so bot doesn't try to drink potions)
        mock_fighter = Mock()
        mock_fighter.hp = 100
        mock_fighter.max_hp = 100
        
        # Mock AutoExplore - stopped due to floor complete
        mock_auto_explore = Mock()
        mock_auto_explore.is_active = Mock(return_value=False)
        mock_auto_explore.stop_reason = "All areas explored"
        
        # Mock stairs at player position
        stairs = Mock()
        stairs.x = 10
        stairs.y = 10
        stairs.blocks = False
        stairs.components = Mock()
        stairs.components.has = Mock(side_effect=lambda ct: ct == ComponentType.STAIRS)
        
        game_state.entities = [player, stairs]
        
        # Setup player get_component_optional
        def get_component(comp_type):
            if comp_type == ComponentType.FIGHTER:
                return mock_fighter
            elif comp_type == ComponentType.AUTO_EXPLORE:
                return mock_auto_explore
            return None
        
        player.get_component_optional = Mock(side_effect=get_component)
        game_state.player = player
        
        # Act
        action = brain.decide_action(game_state)
        
        # Assert: Should descend stairs
        assert action == {'take_stairs': True}, \
            f"Expected bot to descend stairs, got {action}"
    
    def test_bot_walks_toward_stairs_when_floor_complete_but_not_on_stairs(self):
        """Bot should walk toward stairs when floor complete but not standing on stairs."""
        brain = BotBrain()
        
        # Setup: Player at (10, 10), stairs at (12, 10) - NOT on stairs
        game_state = Mock()
        game_state.current_state = GameStates.PLAYERS_TURN
        game_state.fov_map = Mock()
        game_state.game_map = create_mock_game_map()
        
        # Mock player
        player = Mock()
        player.x = 10
        player.y = 10
        player.blocks = False
        player.faction = Mock()
        player.components = Mock()
        player.components.has = Mock(return_value=False)
        
        # Mock healthy fighter
        mock_fighter = Mock()
        mock_fighter.hp = 100
        mock_fighter.max_hp = 100
        
        # Mock AutoExplore - stopped due to floor complete
        mock_auto_explore = Mock()
        mock_auto_explore.is_active = Mock(return_value=False)
        mock_auto_explore.stop_reason = "Cannot reach unexplored areas"
        
        # Mock stairs at (12, 10) - 2 tiles away (NOT on stairs)
        stairs = Mock()
        stairs.x = 12
        stairs.y = 10
        stairs.blocks = False
        stairs.components = Mock()
        stairs.components.has = Mock(side_effect=lambda ct: ct == ComponentType.STAIRS)
        
        game_state.entities = [player, stairs]
        
        # Setup player get_component_optional
        def get_component(comp_type):
            if comp_type == ComponentType.FIGHTER:
                return mock_fighter
            elif comp_type == ComponentType.AUTO_EXPLORE:
                return mock_auto_explore
            return None
        
        player.get_component_optional = Mock(side_effect=get_component)
        game_state.player = player
        
        # Act
        action = brain.decide_action(game_state)
        
        # Assert: Should move toward stairs (dx=1, dy=0)
        assert 'move' in action, \
            f"Expected bot to move toward stairs, got {action}"
        dx, dy = action['move']
        assert dx == 1, f"Expected dx=1 (toward stairs at x=12), got dx={dx}"
        assert dy == 0, f"Expected dy=0, got dy={dy}"
    
    def test_bot_takes_stairs_after_walking_to_them(self):
        """Bot should take stairs after walking the full path to them."""
        brain = BotBrain()
        
        # Setup: Player at (11, 10), stairs at (12, 10) - one step away
        game_state = Mock()
        game_state.current_state = GameStates.PLAYERS_TURN
        game_state.fov_map = Mock()
        game_state.game_map = create_mock_game_map()
        
        # Mock player
        player = Mock()
        player.x = 11
        player.y = 10
        player.blocks = False
        player.faction = Mock()
        player.components = Mock()
        player.components.has = Mock(return_value=False)
        
        # Mock healthy fighter
        mock_fighter = Mock()
        mock_fighter.hp = 100
        mock_fighter.max_hp = 100
        
        # Mock AutoExplore - floor complete
        mock_auto_explore = Mock()
        mock_auto_explore.is_active = Mock(return_value=False)
        mock_auto_explore.stop_reason = "All areas explored"
        
        # Mock stairs at (12, 10)
        stairs = Mock()
        stairs.x = 12
        stairs.y = 10
        stairs.blocks = False
        stairs.components = Mock()
        stairs.components.has = Mock(side_effect=lambda ct: ct == ComponentType.STAIRS)
        
        game_state.entities = [player, stairs]
        
        # Setup player get_component_optional
        def get_component(comp_type):
            if comp_type == ComponentType.FIGHTER:
                return mock_fighter
            elif comp_type == ComponentType.AUTO_EXPLORE:
                return mock_auto_explore
            return None
        
        player.get_component_optional = Mock(side_effect=get_component)
        game_state.player = player
        
        # Act: First action should move to stairs
        action1 = brain.decide_action(game_state)
        assert 'move' in action1, f"First action should be a move, got {action1}"
        
        # Simulate player moved to stairs position
        player.x = 12
        player.y = 10
        
        # Act: Second action should descend stairs
        action2 = brain.decide_action(game_state)
        assert action2 == {'take_stairs': True}, \
            f"Expected bot to descend stairs after walking to them, got {action2}"
    
    def test_bot_does_not_descend_when_floor_not_complete(self):
        """Bot should NOT descend stairs when floor is not fully explored."""
        brain = BotBrain()
        
        # Setup: Player standing on stairs, but floor NOT complete
        game_state = Mock()
        game_state.current_state = GameStates.PLAYERS_TURN
        game_state.fov_map = Mock()
        game_state.game_map = create_mock_game_map()
        
        # Mock player at (10, 10)
        player = Mock()
        player.x = 10
        player.y = 10
        player.faction = Mock()
        player.components = Mock()
        player.components.has = Mock(return_value=False)
        
        # Mock healthy fighter
        mock_fighter = Mock()
        mock_fighter.hp = 100
        mock_fighter.max_hp = 100
        
        # Mock AutoExplore - still active (floor not complete)
        mock_auto_explore = Mock()
        mock_auto_explore.is_active = Mock(return_value=True)
        mock_auto_explore.stop_reason = None
        
        # Mock stairs at player position
        stairs = Mock()
        stairs.x = 10
        stairs.y = 10
        stairs.components = Mock()
        stairs.components.has = Mock(side_effect=lambda ct: ct == ComponentType.STAIRS)
        
        game_state.entities = [player, stairs]
        
        # Setup player get_component_optional
        def get_component(comp_type):
            if comp_type == ComponentType.FIGHTER:
                return mock_fighter
            elif comp_type == ComponentType.AUTO_EXPLORE:
                return mock_auto_explore
            return None
        
        player.get_component_optional = Mock(side_effect=get_component)
        game_state.player = player
        
        # Act
        action = brain.decide_action(game_state)
        
        # Assert: Should NOT descend (floor not complete), should return empty (AutoExplore active)
        assert action != {'take_stairs': True}, \
            f"Bot should NOT descend when floor not complete, got {action}"
        assert action == {}, \
            f"Expected empty action (AutoExplore active), got {action}"
    
    def test_bot_does_not_descend_on_movement_blocked(self):
        """Bot should NOT descend when AutoExplore stopped with 'Movement blocked'."""
        brain = BotBrain()
        
        # Setup: Player standing on stairs, but AutoExplore stopped due to movement failure
        game_state = Mock()
        game_state.current_state = GameStates.PLAYERS_TURN
        game_state.fov_map = Mock()
        game_state.game_map = create_mock_game_map()
        
        # Mock player
        player = Mock()
        player.x = 10
        player.y = 10
        player.faction = Mock()
        player.components = Mock()
        player.components.has = Mock(return_value=False)
        
        # Mock healthy fighter
        mock_fighter = Mock()
        mock_fighter.hp = 100
        mock_fighter.max_hp = 100
        
        # Mock AutoExplore - stopped with "Movement blocked" (NOT floor complete)
        mock_auto_explore = Mock()
        mock_auto_explore.is_active = Mock(return_value=False)
        mock_auto_explore.stop_reason = "Movement blocked"
        
        # Mock stairs at player position
        stairs = Mock()
        stairs.x = 10
        stairs.y = 10
        stairs.components = Mock()
        stairs.components.has = Mock(side_effect=lambda ct: ct == ComponentType.STAIRS)
        
        game_state.entities = [player, stairs]
        
        # Setup player get_component_optional
        def get_component(comp_type):
            if comp_type == ComponentType.FIGHTER:
                return mock_fighter
            elif comp_type == ComponentType.AUTO_EXPLORE:
                return mock_auto_explore
            return None
        
        player.get_component_optional = Mock(side_effect=get_component)
        game_state.player = player
        
        # Act
        action = brain.decide_action(game_state)
        
        # Assert: Should NOT descend (Movement blocked is not floor complete)
        # Movement blocked counter should eventually trigger abort
        assert action != {'take_stairs': True}, \
            f"Bot should NOT descend on Movement blocked, got {action}"
    
    def test_bot_clears_path_and_enters_combat_when_enemies_appear(self):
        """Bot should clear stairs path and fall back to combat when enemies appear."""
        brain = BotBrain()
        
        # Setup: Player walking to stairs, then enemy appears
        game_state = Mock()
        game_state.current_state = GameStates.PLAYERS_TURN
        game_state.fov_map = Mock()
        game_state.game_map = create_mock_game_map()
        
        # Mock player at (10, 10)
        player = Mock()
        player.x = 10
        player.y = 10
        player.blocks = False
        player.faction = Mock()
        player.components = Mock()
        player.components.has = Mock(return_value=False)
        
        # Mock healthy fighter
        mock_fighter = Mock()
        mock_fighter.hp = 100
        mock_fighter.max_hp = 100
        
        # Mock AutoExplore - floor complete
        mock_auto_explore = Mock()
        mock_auto_explore.is_active = Mock(return_value=False)
        mock_auto_explore.stop_reason = "All areas explored"
        
        # Mock stairs at (15, 10) - far away
        stairs = Mock()
        stairs.x = 15
        stairs.y = 10
        stairs.blocks = False
        stairs.components = Mock()
        stairs.components.has = Mock(side_effect=lambda ct: ct == ComponentType.STAIRS)
        
        game_state.entities = [player, stairs]
        
        # Setup player get_component_optional
        def get_component(comp_type):
            if comp_type == ComponentType.FIGHTER:
                return mock_fighter
            elif comp_type == ComponentType.AUTO_EXPLORE:
                return mock_auto_explore
            return None
        
        player.get_component_optional = Mock(side_effect=get_component)
        game_state.player = player
        
        # First: Bot should start walking to stairs
        action1 = brain.decide_action(game_state)
        assert 'move' in action1, f"Expected move toward stairs, got {action1}"
        
        # Verify a stairs path was created
        assert brain._stairs_path is not None or brain._stairs_path == [], \
            "Expected stairs path to be set after first action"
        
        # Now: Add an enemy that appears while walking
        enemy = Mock()
        enemy.x = 11
        enemy.y = 10  # Adjacent to player
        enemy.blocks = True
        enemy.faction = Mock()
        enemy.components = Mock()
        enemy.components.has = Mock(side_effect=lambda ct: ct == ComponentType.AI)
        
        mock_enemy_fighter = Mock()
        mock_enemy_fighter.hp = 20
        enemy.get_component_optional = Mock(side_effect=lambda ct:
            mock_enemy_fighter if ct == ComponentType.FIGHTER else None)
        
        game_state.entities = [player, stairs, enemy]
        
        # Mock FOV: enemy is visible at adjacent position
        def mock_is_in_fov(fov_map, x, y):
            return (x, y) == (11, 10)
        
        with patch('io_layer.bot_brain.map_is_in_fov', side_effect=mock_is_in_fov), \
             patch('io_layer.bot_brain.are_factions_hostile', return_value=True):
            action2 = brain.decide_action(game_state)
        
        # Assert: Should attack adjacent enemy (move toward enemy), not continue walking to stairs
        assert 'move' in action2, f"Expected combat move, got {action2}"
        assert brain.state == BotState.COMBAT, f"Expected COMBAT state, got {brain.state}"
        # Stairs path should be cleared
        assert brain._stairs_path is None, "Expected stairs path to be cleared when enemy appears"
    
    def test_bot_aborts_when_no_stairs_found(self):
        """Bot should abort run when floor complete but no stairs exist."""
        brain = BotBrain()
        
        # Setup: Player at (10, 10), floor complete, NO stairs on map
        game_state = Mock()
        game_state.current_state = GameStates.PLAYERS_TURN
        game_state.fov_map = Mock()
        game_state.game_map = create_mock_game_map()
        
        # Mock player
        player = Mock()
        player.x = 10
        player.y = 10
        player.faction = Mock()
        player.components = Mock()
        player.components.has = Mock(return_value=False)
        
        # Mock healthy fighter
        mock_fighter = Mock()
        mock_fighter.hp = 100
        mock_fighter.max_hp = 100
        
        # Mock AutoExplore - floor complete
        mock_auto_explore = Mock()
        mock_auto_explore.is_active = Mock(return_value=False)
        mock_auto_explore.stop_reason = "All areas explored"
        
        # NO stairs in entities
        game_state.entities = [player]
        
        # Setup player get_component_optional
        def get_component(comp_type):
            if comp_type == ComponentType.FIGHTER:
                return mock_fighter
            elif comp_type == ComponentType.AUTO_EXPLORE:
                return mock_auto_explore
            return None
        
        player.get_component_optional = Mock(side_effect=get_component)
        game_state.player = player
        
        # Act
        action = brain.decide_action(game_state)
        
        # Assert: Should abort run (no stairs found)
        assert action == {'bot_abort_run': True}, \
            f"Expected bot to abort run when no stairs found, got {action}"
    
    def test_bot_does_not_restart_auto_explore_after_floor_complete(self):
        """Bot should NOT restart AutoExplore after floor exploration is complete."""
        brain = BotBrain()
        
        # Simulate: pre-set a stairs path (as if we're walking to stairs)
        brain._stairs_path = [(11, 10), (12, 10)]
        
        # Setup: game_state in PLAYERS_TURN
        game_state = Mock()
        game_state.current_state = GameStates.PLAYERS_TURN
        game_state.entities = []
        game_state.fov_map = Mock()
        game_state.game_map = create_mock_game_map()
        
        # Mock player
        player = Mock()
        player.x = 10
        player.y = 10
        player.faction = Mock()
        player.components = Mock()
        player.components.has = Mock(return_value=False)
        
        # Mock healthy fighter
        mock_fighter = Mock()
        mock_fighter.hp = 100
        mock_fighter.max_hp = 100
        
        # Mock AutoExplore - floor complete
        mock_auto_explore = Mock()
        mock_auto_explore.is_active = Mock(return_value=False)
        mock_auto_explore.stop_reason = "All areas explored"
        
        # Setup player get_component_optional
        def get_component(comp_type):
            if comp_type == ComponentType.FIGHTER:
                return mock_fighter
            elif comp_type == ComponentType.AUTO_EXPLORE:
                return mock_auto_explore
            return None
        
        player.get_component_optional = Mock(side_effect=get_component)
        game_state.player = player
        
        # Act: Call _handle_explore directly
        action = brain._handle_explore(player, game_state)
        
        # Assert: Should NOT emit start_auto_explore (floor is complete, walking to stairs)
        assert action != {'start_auto_explore': True}, \
            f"Bot should NOT restart AutoExplore when walking to stairs, got {action}"
        assert action == {}, \
            f"Expected empty action while walking to stairs, got {action}"


class TestTerminalExploreReasons:
    """Tests for TERMINAL_EXPLORE_REASONS constant and floor completion logic."""
    
    def test_terminal_explore_reasons_contains_expected_strings(self):
        """TERMINAL_EXPLORE_REASONS should contain the expected floor completion reasons."""
        assert "All areas explored" in TERMINAL_EXPLORE_REASONS
        assert "Cannot reach unexplored areas" in TERMINAL_EXPLORE_REASONS
        # Verify it's a frozenset (immutable)
        assert isinstance(TERMINAL_EXPLORE_REASONS, frozenset)
    
    def test_movement_blocked_is_not_terminal(self):
        """'Movement blocked' should NOT be a terminal exploration reason."""
        # Movement blocked is a temporary failure, not floor completion
        assert "Movement blocked" not in TERMINAL_EXPLORE_REASONS
    
    def test_floor_complete_triggers_stair_walking(self):
        """Bot should start walking to stairs when stop_reason is 'Cannot reach unexplored areas'."""
        brain = BotBrain()
        
        # Setup minimal game state
        game_state = Mock()
        game_state.current_state = GameStates.PLAYERS_TURN
        game_state.fov_map = Mock()
        game_state.game_map = create_mock_game_map()
        
        player = Mock()
        player.x = 10
        player.y = 10
        player.blocks = False
        player.faction = Mock()
        player.components = Mock()
        player.components.has = Mock(return_value=False)
        
        # Mock healthy fighter
        mock_fighter = Mock()
        mock_fighter.hp = 100
        mock_fighter.max_hp = 100
        
        # Mock AutoExplore stopped with terminal reason
        mock_auto_explore = Mock()
        mock_auto_explore.is_active = Mock(return_value=False)
        mock_auto_explore.stop_reason = "Cannot reach unexplored areas"
        
        # Mock stairs at (15, 10)
        stairs = Mock()
        stairs.x = 15
        stairs.y = 10
        stairs.blocks = False
        stairs.components = Mock()
        stairs.components.has = Mock(side_effect=lambda ct: ct == ComponentType.STAIRS)
        
        game_state.entities = [player, stairs]
        
        def get_component(comp_type):
            if comp_type == ComponentType.FIGHTER:
                return mock_fighter
            elif comp_type == ComponentType.AUTO_EXPLORE:
                return mock_auto_explore
            return None
        
        player.get_component_optional = Mock(side_effect=get_component)
        game_state.player = player
        
        # Act
        action = brain.decide_action(game_state)
        
        # Assert: Should start walking toward stairs (not abort)
        assert 'move' in action, \
            f"Expected move toward stairs for 'Cannot reach unexplored areas', got {action}"


class TestStairPathfinding:
    """Tests for the stair pathfinding helper methods."""
    
    def test_find_nearest_stairs_returns_closest(self):
        """_find_nearest_stairs should return the closest stairs position."""
        brain = BotBrain()
        
        # Mock player at (10, 10) - NOT stairs
        player = Mock()
        player.x = 10
        player.y = 10
        player.components = Mock()
        player.components.has = Mock(return_value=False)  # Player is NOT stairs
        
        # Mock two stairs: one at (12, 10), one at (20, 20)
        stairs1 = Mock()
        stairs1.x = 12
        stairs1.y = 10
        stairs1.components = Mock()
        stairs1.components.has = Mock(side_effect=lambda ct: ct == ComponentType.STAIRS)
        
        stairs2 = Mock()
        stairs2.x = 20
        stairs2.y = 20
        stairs2.components = Mock()
        stairs2.components.has = Mock(side_effect=lambda ct: ct == ComponentType.STAIRS)
        
        entities = [player, stairs1, stairs2]
        
        # Act
        result = brain._find_nearest_stairs(player, entities)
        
        # Assert: Should return (12, 10) as it's closer
        assert result == (12, 10), f"Expected nearest stairs at (12, 10), got {result}"
    
    def test_find_nearest_stairs_returns_none_when_no_stairs(self):
        """_find_nearest_stairs should return None when no stairs exist."""
        brain = BotBrain()
        
        player = Mock()
        player.x = 10
        player.y = 10
        player.components = Mock()
        player.components.has = Mock(return_value=False)  # Player is NOT stairs
        
        # No stairs in entities
        entities = [player]
        
        # Act
        result = brain._find_nearest_stairs(player, entities)
        
        # Assert
        assert result is None, f"Expected None when no stairs, got {result}"
    
    def test_is_standing_on_stairs_true_when_on_stairs(self):
        """_is_standing_on_stairs should return True when player is on stairs."""
        brain = BotBrain()
        
        player = Mock()
        player.x = 10
        player.y = 10
        player.components = Mock()
        player.components.has = Mock(return_value=False)  # Player is NOT stairs
        
        stairs = Mock()
        stairs.x = 10
        stairs.y = 10
        stairs.components = Mock()
        stairs.components.has = Mock(side_effect=lambda ct: ct == ComponentType.STAIRS)
        
        entities = [player, stairs]
        
        # Act
        result = brain._is_standing_on_stairs(player, entities)
        
        # Assert
        assert result is True
    
    def test_is_standing_on_stairs_false_when_not_on_stairs(self):
        """_is_standing_on_stairs should return False when player is not on stairs."""
        brain = BotBrain()
        
        player = Mock()
        player.x = 10
        player.y = 10
        player.components = Mock()
        player.components.has = Mock(return_value=False)  # Player is NOT stairs
        
        stairs = Mock()
        stairs.x = 12
        stairs.y = 10
        stairs.components = Mock()
        stairs.components.has = Mock(side_effect=lambda ct: ct == ComponentType.STAIRS)
        
        entities = [player, stairs]
        
        # Act
        result = brain._is_standing_on_stairs(player, entities)
        
        # Assert
        assert result is False
