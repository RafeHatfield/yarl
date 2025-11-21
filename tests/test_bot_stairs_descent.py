"""Unit tests for bot stairs descent behavior.

This test suite validates that the bot automatically descends stairs
when floor exploration is complete, enabling multi-floor soak testing.

Test cases:
- Bot descends when standing on stairs and floor complete
- Bot walks to nearby stairs when floor complete
- Bot doesn't descend when floor not complete
- Bot doesn't seek stairs beyond radius
- Bot doesn't descend when enemies visible
"""

import pytest
from unittest.mock import Mock

from io_layer.bot_brain import BotBrain, BotState, BOT_STAIRS_RADIUS
from game_states import GameStates
from components.component_registry import ComponentType


class TestBotStairsDescent:
    """Test bot automatic stairs descent for multi-floor runs."""
    
    def test_bot_descends_when_standing_on_stairs_and_floor_complete(self):
        """Bot should descend stairs when standing on them and floor is fully explored."""
        brain = BotBrain()
        
        # Setup: Player standing on stairs, floor complete
        game_state = Mock()
        game_state.current_state = GameStates.PLAYERS_TURN
        game_state.fov_map = Mock()
        
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
    
    def test_bot_walks_to_stairs_when_floor_complete_and_stairs_nearby(self):
        """Bot should walk to nearby stairs when floor complete."""
        brain = BotBrain()
        
        # Setup: Player at (10, 10), stairs at (12, 10) - 2 tiles away
        game_state = Mock()
        game_state.current_state = GameStates.PLAYERS_TURN
        game_state.fov_map = Mock()
        
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
        
        # Mock AutoExplore - stopped due to floor complete
        mock_auto_explore = Mock()
        mock_auto_explore.is_active = Mock(return_value=False)
        mock_auto_explore.stop_reason = "Cannot reach unexplored areas"
        
        # Mock stairs at (12, 10) - 2 tiles east
        stairs = Mock()
        stairs.x = 12
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
        
        # Assert: Should move toward stairs (east)
        assert action == {'move': (1, 0)}, \
            f"Expected bot to move toward stairs, got {action}"
    
    def test_bot_does_not_descend_when_floor_not_complete(self):
        """Bot should NOT descend stairs when floor is not fully explored."""
        brain = BotBrain()
        
        # Setup: Player standing on stairs, but floor NOT complete
        game_state = Mock()
        game_state.current_state = GameStates.PLAYERS_TURN
        game_state.fov_map = Mock()
        
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
    
    def test_bot_ignores_stairs_beyond_radius(self):
        """Bot should ignore stairs beyond BOT_STAIRS_RADIUS."""
        brain = BotBrain()
        
        # Setup: Player at (10, 10), stairs beyond radius
        game_state = Mock()
        game_state.current_state = GameStates.PLAYERS_TURN
        game_state.fov_map = Mock()
        
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
        
        # Mock stairs far away (beyond radius)
        stairs = Mock()
        stairs.x = 10 + BOT_STAIRS_RADIUS + 5  # Well beyond radius
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
        
        # Assert: Should NOT seek stairs (too far), should try to restart AutoExplore
        assert action != {'move': (1, 0)}, \
            f"Bot should NOT seek stairs beyond radius, got {action}"
        # Will try to start AutoExplore (which will fail, but that's OK)
    
    def test_bot_does_not_descend_when_enemies_visible(self):
        """Bot should NOT descend stairs when enemies are visible (unsafe)."""
        brain = BotBrain()
        
        # Setup: Player on stairs, floor complete, but enemy visible
        game_state = Mock()
        game_state.current_state = GameStates.PLAYERS_TURN
        game_state.fov_map = Mock()
        
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
        
        # Mock AutoExplore - floor complete
        mock_auto_explore = Mock()
        mock_auto_explore.is_active = Mock(return_value=False)
        mock_auto_explore.stop_reason = "All areas explored"
        
        # Mock stairs at player position
        stairs = Mock()
        stairs.x = 10
        stairs.y = 10
        stairs.components = Mock()
        stairs.components.has = Mock(side_effect=lambda ct: ct == ComponentType.STAIRS)
        
        # Mock enemy (visible)
        enemy = Mock()
        enemy.x = 15
        enemy.y = 10
        enemy.faction = Mock()
        enemy.components = Mock()
        enemy.components.has = Mock(side_effect=lambda ct: ct == ComponentType.AI)
        
        mock_enemy_fighter = Mock()
        mock_enemy_fighter.hp = 20
        enemy.get_component_optional = Mock(side_effect=lambda ct:
            mock_enemy_fighter if ct == ComponentType.FIGHTER else None)
        
        game_state.entities = [player, stairs, enemy]
        
        # Setup player get_component_optional
        def get_component(comp_type):
            if comp_type == ComponentType.FIGHTER:
                return mock_fighter
            elif comp_type == ComponentType.AUTO_EXPLORE:
                return mock_auto_explore
            return None
        
        player.get_component_optional = Mock(side_effect=get_component)
        game_state.player = player
        
        # Mock FOV: enemy is visible
        from unittest.mock import patch
        def mock_is_in_fov(fov_map, x, y):
            return (x, y) == (15, 10)
        
        with patch('io_layer.bot_brain.map_is_in_fov', side_effect=mock_is_in_fov), \
             patch('io_layer.bot_brain.are_factions_hostile', return_value=True):
            # Act
            action = brain.decide_action(game_state)
        
        # Assert: Should NOT descend (enemy visible), should enter COMBAT
        assert action != {'take_stairs': True}, \
            f"Bot should NOT descend when enemy visible, got {action}"
        assert brain.state == BotState.COMBAT
    
    def test_bot_prefers_closer_stairs_when_multiple_available(self):
        """Bot should prefer nearest stairs when multiple are available."""
        brain = BotBrain()
        
        # Setup: Player at (10, 10), two stairs at different distances
        game_state = Mock()
        game_state.current_state = GameStates.PLAYERS_TURN
        game_state.fov_map = Mock()
        
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
        
        # Mock near stairs at (12, 10) - 2 tiles east
        near_stairs = Mock()
        near_stairs.x = 12
        near_stairs.y = 10
        near_stairs.components = Mock()
        near_stairs.components.has = Mock(side_effect=lambda ct: ct == ComponentType.STAIRS)
        
        # Mock far stairs at (10, 15) - 5 tiles south
        far_stairs = Mock()
        far_stairs.x = 10
        far_stairs.y = 15
        far_stairs.components = Mock()
        far_stairs.components.has = Mock(side_effect=lambda ct: ct == ComponentType.STAIRS)
        
        game_state.entities = [player, near_stairs, far_stairs]
        
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
        
        # Assert: Should move toward nearer stairs (east)
        assert action == {'move': (1, 0)}, \
            f"Expected bot to move toward nearer stairs (east), got {action}"


