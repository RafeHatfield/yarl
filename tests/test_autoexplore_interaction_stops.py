"""Tests for AutoExplore stopping on chest/signpost/mural interactions.

This test suite verifies that AutoExplore properly stops when the player
interacts with chests, signposts, and murals via the InteractionSystem.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from systems.interaction_system import (
    ChestInteractionStrategy,
    SignpostInteractionStrategy,
    MuralInteractionStrategy,
    PathfindingHelper
)
from components.auto_explore import AutoExplore
from components.chest import Chest, ChestState
from components.signpost import Signpost
from components.mural import Mural
from components.component_registry import ComponentType


class TestChestInteractionStopsAutoExplore:
    """Test that chest interactions stop AutoExplore."""
    
    def test_chest_interaction_sets_stop_reason(self):
        """Test that opening a chest sets auto_explore_stop_reason in result."""
        strategy = ChestInteractionStrategy()
        
        # Create mock player
        player = Mock()
        player.x = 10
        player.y = 10
        player.distance_to = Mock(return_value=1)  # Adjacent
        
        # Create mock chest entity
        chest_entity = Mock()
        chest_entity.name = "Wooden Chest"
        chest_entity.tags = ['openable']
        chest_entity.chest = Mock()
        chest_entity.chest.can_interact = Mock(return_value=True)
        chest_entity.chest.open = Mock(return_value=[
            {"message": "You open the chest!", "loot": []}
        ])
        chest_entity.chest.state = ChestState.CLOSED
        chest_entity.components = Mock()
        chest_entity.components.get = Mock(return_value=chest_entity.chest)
        
        # Create mock game objects
        game_map = Mock()
        entities = []
        fov_map = Mock()
        pathfinder = Mock()
        
        # Call interact
        result = strategy.interact(chest_entity, player, game_map, entities, fov_map, pathfinder)
        
        # Verify result has auto_explore_stop_reason
        assert result.action_taken is True
        assert result.auto_explore_stop_reason == "Found Chest"
    
    def test_chest_already_open_no_stop_reason(self):
        """Test that an already-open chest doesn't set stop reason."""
        strategy = ChestInteractionStrategy()
        
        # Create mock player
        player = Mock()
        player.x = 10
        player.y = 10
        player.distance_to = Mock(return_value=1)  # Adjacent
        
        # Create mock chest entity (already open)
        chest_entity = Mock()
        chest_entity.name = "Wooden Chest"
        chest_entity.tags = ['openable']
        chest_entity.chest = Mock()
        chest_entity.chest.can_interact = Mock(return_value=False)  # Already open
        chest_entity.chest.state = ChestState.OPEN
        chest_entity.components = Mock()
        chest_entity.components.get = Mock(return_value=chest_entity.chest)
        
        # Create mock game objects
        game_map = Mock()
        entities = []
        fov_map = Mock()
        pathfinder = Mock()
        
        # Call interact
        result = strategy.interact(chest_entity, player, game_map, entities, fov_map, pathfinder)
        
        # Verify no stop reason (chest already open, just informational)
        assert result.action_taken is True
        assert result.auto_explore_stop_reason is None


class TestSignpostInteractionStopsAutoExplore:
    """Test that signpost interactions stop AutoExplore."""
    
    def test_signpost_interaction_sets_stop_reason(self):
        """Test that reading a signpost sets auto_explore_stop_reason in result."""
        strategy = SignpostInteractionStrategy()
        
        # Create mock player
        player = Mock()
        player.x = 10
        player.y = 10
        player.distance_to = Mock(return_value=1)  # Adjacent
        
        # Create mock signpost entity
        signpost_entity = Mock()
        signpost_entity.name = "Hint Sign"
        signpost_entity.tags = ['interactable']
        signpost_entity.signpost = Mock()
        signpost_entity.signpost.message = "Beware the dark passages..."
        
        # Create mock game objects
        game_map = Mock()
        entities = []
        fov_map = Mock()
        pathfinder = Mock()
        
        # Call interact
        result = strategy.interact(signpost_entity, player, game_map, entities, fov_map, pathfinder)
        
        # Verify result has auto_explore_stop_reason
        assert result.action_taken is True
        assert result.auto_explore_stop_reason == "Found Hint Sign"
        assert result.consume_turn is False  # Reading doesn't consume turn


class TestMuralInteractionStopsAutoExplore:
    """Test that mural interactions stop AutoExplore."""
    
    def test_mural_interaction_sets_stop_reason(self):
        """Test that reading a mural sets auto_explore_stop_reason in result."""
        strategy = MuralInteractionStrategy()
        
        # Create mock player
        player = Mock()
        player.x = 10
        player.y = 10
        player.distance_to = Mock(return_value=1)  # Adjacent
        
        # Create mock mural entity
        mural_entity = Mock()
        mural_entity.name = "Ancient Mural"
        mural_entity.tags = ['interactable']
        mural_entity.mural = Mock()
        mural_entity.mural.text = "Ancient runes tell of a forgotten age..."
        
        # Create mock game objects
        game_map = Mock()
        entities = []
        fov_map = Mock()
        pathfinder = Mock()
        
        # Call interact
        result = strategy.interact(mural_entity, player, game_map, entities, fov_map, pathfinder)
        
        # Verify result has auto_explore_stop_reason
        assert result.action_taken is True
        assert result.auto_explore_stop_reason == "Found Mural"
        assert result.consume_turn is False  # Reading doesn't consume turn


class TestAutoExploreMuralStopCondition:
    """Test that AutoExplore stops when it sees a mural in FOV."""
    
    def test_mural_in_fov_method_detects_murals(self):
        """Test that _mural_in_fov() detects unread murals."""
        auto_explore = AutoExplore()
        
        # Create mock owner (player)
        player = Mock()
        player.x = 10
        player.y = 20
        auto_explore.owner = player
        
        # Create mock game_map
        game_map = Mock()
        game_map.width = 50
        game_map.height = 50
        
        # Create mock mural entity
        mural = Mock()
        mural.x = 12
        mural.y = 21
        mural.name = "Ancient Mural"
        mural.components = Mock()
        mural.components.has = Mock(side_effect=lambda ct: ct == ComponentType.MURAL)
        mural.mural = Mock()
        mural.mural.has_been_read = False
        
        entities = [mural]
        
        # Mock FOV
        def mock_fov(fov, x, y):
            return True  # Everything in FOV
        
        fov_map = Mock()
        
        # Start auto-explore
        auto_explore.explored_tiles_at_start = set()  # Mural not in explored area
        
        with patch('fov_functions.map_is_in_fov', side_effect=mock_fov):
            found_mural = auto_explore._mural_in_fov(entities, fov_map, game_map)
        
        # Should find the mural
        assert found_mural is not None
        assert found_mural.name == "Ancient Mural"
    
    def test_already_read_mural_does_not_stop(self):
        """Test that already-read murals don't trigger stop."""
        auto_explore = AutoExplore()
        
        # Create mock owner (player)
        player = Mock()
        player.x = 10
        player.y = 20
        auto_explore.owner = player
        
        # Create mock game_map
        game_map = Mock()
        game_map.width = 50
        game_map.height = 50
        
        # Create mock mural entity (already read)
        mural = Mock()
        mural.x = 12
        mural.y = 21
        mural.name = "Ancient Mural"
        mural.components = Mock()
        mural.components.has = Mock(side_effect=lambda ct: ct == ComponentType.MURAL)
        mural.mural = Mock()
        mural.mural.has_been_read = True  # Already read!
        
        entities = [mural]
        
        # Mock FOV
        def mock_fov(fov, x, y):
            return True  # Everything in FOV
        
        fov_map = Mock()
        
        # Start auto-explore
        auto_explore.explored_tiles_at_start = set()
        
        with patch('fov_functions.map_is_in_fov', side_effect=mock_fov):
            found_mural = auto_explore._mural_in_fov(entities, fov_map, game_map)
        
        # Should NOT find the mural (already read)
        assert found_mural is None


class TestAutoExploreInteractionIntegration:
    """Integration tests for AutoExplore stopping via ActionProcessor."""
    
    def test_manual_interaction_when_autoexplore_inactive_does_not_crash(self):
        """Test that manual interaction without AutoExplore active works normally."""
        # This is a safety test - manual interactions should work fine
        # even if AutoExplore component exists but is not active
        
        auto_explore = AutoExplore()
        player = Mock()
        player.x = 10
        player.y = 10
        auto_explore.owner = player
        auto_explore.active = False  # NOT active
        
        player.get_component_optional = Mock(return_value=auto_explore)
        
        # Simulate interaction result with stop reason
        from systems.interaction_system import InteractionResult
        result = InteractionResult(
            action_taken=True,
            auto_explore_stop_reason="Found Chest",
            consume_turn=True
        )
        
        # Process like ActionProcessor would
        if result.auto_explore_stop_reason:
            auto_explore_comp = player.get_component_optional(ComponentType.AUTO_EXPLORE)
            if auto_explore_comp and auto_explore_comp.is_active():
                auto_explore_comp.stop(result.auto_explore_stop_reason)
        
        # Should NOT crash, and AutoExplore should still be inactive
        assert not auto_explore.is_active()
        assert auto_explore.stop_reason is None  # Never set because it wasn't active


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

