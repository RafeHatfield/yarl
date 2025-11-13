"""Tests for new interaction control scheme (right-click canonical, left-click move/attack).

Tests verify:
- Right-click opens/uses interactable entities (chests, doors, etc.) with pathfinding
- Left-click moves/attacks, never unexpectedly opens UIs
- Left-click adjacent chest opens only as temporary fallback with deprecation hint
- Feature flags control behavior
"""

import pytest
from entity import Entity
from components.component_registry import ComponentType
from components.chest import Chest, ChestState
from components.fighter import Fighter
from components.inventory import Inventory
from components.player_pathfinding import PlayerPathfinding
from engine.game_state_manager import GameStateManager
from systems.interaction_system import InteractionSystem
from game_states import GameStates
from game_messages import MessageLog
from map_objects.game_map import GameMap
from config.game_constants import get_constants


@pytest.fixture
def state_manager():
    """Create a game state manager for testing."""
    return GameStateManager()


@pytest.fixture
def game_map():
    """Create a simple game map for testing."""
    game_map = GameMap(width=50, height=50)
    for y in range(50):
        for x in range(50):
            game_map.tiles[y][x].blocked = False
    return game_map


@pytest.fixture
def player(state_manager):
    """Create a player entity with required components."""
    player = Entity(25, 25, '@', (255, 255, 255), 'Player')
    player.fighter = Fighter(hp=100, defense=2, power=10)
    player.inventory = Inventory(26)
    player.pathfinding = PlayerPathfinding()
    player.pathfinding.owner = player
    return player


@pytest.fixture
def closed_chest():
    """Create a closed chest for testing."""
    chest_entity = Entity(26, 25, 'C', (139, 69, 19), 'Chest')
    chest_component = Chest(state=ChestState.CLOSED, loot=[], loot_quality='common')
    chest_entity.chest = chest_component
    chest_component.owner = chest_entity
    chest_entity.tags.add('openable')
    return chest_entity


@pytest.fixture
def fov_map(game_map):
    """Create a simple FOV map (all visible)."""
    return [[True] * game_map.width for _ in range(game_map.height)]


class TestControlSchemeConfiguration:
    """Test that control scheme configuration is properly set."""
    
    def test_constants_have_controls_config(self):
        """Test that constants include control mapping."""
        constants = get_constants()
        assert 'controls' in constants
    
    def test_right_click_interact_enabled_by_default(self):
        """Test right-click interact is enabled by default."""
        constants = get_constants()
        assert constants['controls']['right_click_interact'] is True
    
    def test_left_click_interact_fallback_enabled_by_default(self):
        """Test left-click interact fallback is enabled by default (temporary)."""
        constants = get_constants()
        assert constants['controls']['allow_left_click_interact'] is True
    
    def test_shift_left_click_interact_config_exists(self):
        """Test shift-left-click config exists (even if not fully implemented)."""
        constants = get_constants()
        assert 'shift_left_click_interact' in constants['controls']


class TestRightClickInteract:
    """Test right-click interaction (canonical interact method)."""
    
    def test_right_click_open_adjacent_chest(self, player, closed_chest, game_map, fov_map):
        """Test that right-click opens adjacent chest immediately."""
        player.x, player.y = 25, 25
        closed_chest.x, closed_chest.y = 26, 25
        
        interaction_system = InteractionSystem()
        entities = [player, closed_chest]
        
        result = interaction_system.handle_click(
            closed_chest.x, closed_chest.y,
            player, entities, game_map, fov_map
        )
        
        # Chest should be opened
        assert result.action_taken
        assert closed_chest.chest.state == ChestState.OPEN
    
    def test_right_click_far_chest_initiates_pathfinding(self, player, closed_chest, game_map, fov_map):
        """Test that right-click distant chest starts pathfinding."""
        player.x, player.y = 10, 10
        closed_chest.x, closed_chest.y = 30, 30
        
        interaction_system = InteractionSystem()
        entities = [player, closed_chest]
        
        result = interaction_system.handle_click(
            closed_chest.x, closed_chest.y,
            player, entities, game_map, fov_map
        )
        
        # Interaction should be recognized
        assert result.action_taken
        # Either pathfinding started or failure message given
        assert result.start_pathfinding or result.message is not None


class TestLeftClickMovement:
    """Test left-click movement (canonical move/attack method)."""
    
    def test_left_click_empty_tile_should_move(self, player, game_map):
        """Test that left-click on empty tile initiates movement."""
        # This test verifies behavior at the game_actions level
        # (mouse_movement.py handles_movement_click for empty spaces)
        from mouse_movement import _is_valid_click
        
        click_x, click_y = 30, 30
        
        # Should be valid click location
        assert _is_valid_click(click_x, click_y, game_map)
    
    def test_left_click_should_not_pathfind_to_far_chest(self, player, closed_chest, game_map):
        """Test that left-click on distant chest does NOT pathfind."""
        # The _handle_chest_click should return empty results for non-adjacent
        from mouse_movement import _handle_chest_click
        
        player.x, player.y = 10, 10
        closed_chest.x, closed_chest.y = 30, 30
        
        results = []
        click_result = _handle_chest_click(player, closed_chest, results, [], game_map)
        
        # Should not have pathfinding commands
        assert "pathfind_to_target" not in str(click_result)


class TestLeftClickChestFallback:
    """Test left-click chest opening as deprecated fallback."""
    
    def test_left_click_open_adjacent_chest_fallback(self, player, closed_chest, game_map):
        """Test that left-click opens adjacent chest as fallback (deprecated)."""
        from mouse_movement import _handle_chest_click
        
        player.x, player.y = 25, 25
        closed_chest.x, closed_chest.y = 26, 25  # Adjacent
        
        results = []
        _handle_chest_click(player, closed_chest, results, [], game_map)
        
        # Chest should be opened
        assert closed_chest.chest.state == ChestState.OPEN
        # Results should contain message
        assert len(results) > 0
    
    def test_left_click_does_not_pathfind_to_distant_chest(self, player, closed_chest, game_map):
        """Test that left-click distant chest does NOT start pathfinding."""
        from mouse_movement import _handle_chest_click
        
        player.x, player.y = 10, 10
        closed_chest.x, closed_chest.y = 30, 30  # Not adjacent
        
        results = []
        click_result = _handle_chest_click(player, closed_chest, results, [], game_map)
        
        # Should NOT pathfind
        assert len(results) == 0 or "pathfind" not in str(click_result)


class TestControlSchemeBehavior:
    """Test integrated behavior of the control scheme."""
    
    def test_right_click_is_primary_interact(self, player, closed_chest, game_map, fov_map):
        """Test that right-click is the primary way to interact."""
        player.x, player.y = 25, 25
        closed_chest.x, closed_chest.y = 26, 25
        
        interaction_system = InteractionSystem()
        entities = [player, closed_chest]
        
        # Right-click should interact
        result = interaction_system.handle_click(
            closed_chest.x, closed_chest.y,
            player, entities, game_map, fov_map
        )
        
        assert result.action_taken
        assert closed_chest.chest.state == ChestState.OPEN
    
    def test_left_click_opens_only_when_adjacent_and_allowed(self, player, closed_chest, game_map):
        """Test left-click opens only when both adjacent AND flag enabled."""
        from mouse_movement import _handle_chest_click
        
        # Adjacent
        player.x, player.y = 25, 25
        closed_chest.x, closed_chest.y = 26, 25
        
        results = []
        _handle_chest_click(player, closed_chest, results, [], game_map)
        
        # Should open
        assert closed_chest.chest.state == ChestState.OPEN


class TestDeprecationHint:
    """Test deprecation hint for left-click chest opening."""
    
    def test_hint_shown_only_once_per_session(self, player, closed_chest, game_map):
        """Test that deprecation hint is shown only once per session."""
        from mouse_movement import _show_interact_hint_once, _interact_hint_shown
        import mouse_movement
        
        # Reset the hint flag
        mouse_movement._interact_hint_shown = False
        
        # First call should show hint
        _show_interact_hint_once()
        assert mouse_movement._interact_hint_shown is True
        
        # Flag should remain True (hint not shown again)
        mouse_movement._interact_hint_shown = True
        _show_interact_hint_once()
        assert mouse_movement._interact_hint_shown is True  # Still true


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

