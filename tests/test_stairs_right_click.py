"""Regression tests for stairs right-click interaction.

Tests that stairs can be used via right-click, both when:
- Player is standing on stairs (use immediately)
- Player is distant from stairs (path to stairs, auto-use on arrival)
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from entity import Entity
from components.fighter import Fighter
from components.inventory import Inventory
from components.player_pathfinding import PlayerPathfinding
from components.component_registry import ComponentType
from stairs import Stairs
from map_objects.game_map import GameMap
from systems.interaction_system import InteractionSystem, InteractionResult
from game_states import GameStates
from engine.game_state_manager import GameStateManager


class TestStairsRightClickInteraction(unittest.TestCase):
    """Test stairs interaction via right-click."""

    def setUp(self):
        """Set up test scenario with player and stairs."""
        # Create player at (5, 5)
        self.player = Entity(
            x=5, y=5, char='@', color=(255, 255, 255), name='Player',
            fighter=Fighter(hp=30, defense=2, power=5),
            inventory=Inventory(capacity=26)
        )
        
        # Add pathfinding component
        pathfinding = PlayerPathfinding()
        pathfinding.owner = self.player
        self.player.components.add(ComponentType.PATHFINDING, pathfinding)
        # Also set as attribute for backward compatibility with code that uses player.pathfinding
        object.__setattr__(self.player, 'pathfinding', pathfinding)
        
        # Create stairs at (10, 10) - distant from player
        self.stairs_distant = Entity(
            x=10, y=10, char='>', color=(255, 255, 255), name='Stairs',
            stairs=Stairs(floor=2)
        )
        
        # Create stairs at (5, 5) - same location as player
        self.stairs_on_player = Entity(
            x=5, y=5, char='>', color=(255, 255, 255), name='Stairs',
            stairs=Stairs(floor=2)
        )
        
        # Create game map with walkable tiles
        self.game_map = GameMap(width=80, height=50, dungeon_level=1)
        
        # Make tiles walkable for pathfinding tests
        for x in range(80):
            for y in range(50):
                self.game_map.tiles[x][y].explored = True
                self.game_map.tiles[x][y].blocked = False
                self.game_map.tiles[x][y].block_sight = False
        
        # Create mock FOV map
        self.fov_map = Mock()
        
        # Create interaction system
        self.interaction_system = InteractionSystem()

    def test_stairs_can_interact(self):
        """Test that StairsInteractionStrategy recognizes stairs entities."""
        from systems.interaction_system import StairsInteractionStrategy
        
        strategy = StairsInteractionStrategy()
        
        # Should recognize stairs entity
        self.assertTrue(strategy.can_interact(self.stairs_distant, self.player))
        
        # Should not recognize non-stairs entity
        chest = Entity(x=1, y=1, char='C', color=(255, 255, 0), name='Chest')
        self.assertFalse(strategy.can_interact(chest, self.player))

    def test_stairs_priority(self):
        """Test that stairs have appropriate priority (low, after items)."""
        from systems.interaction_system import StairsInteractionStrategy
        
        strategy = StairsInteractionStrategy()
        priority = strategy.get_priority()
        
        # Stairs should have low priority (1.5 - between items and NPCs)
        self.assertEqual(priority, 1.5)

    def test_right_click_stairs_when_on_stairs(self):
        """Test right-clicking stairs when player is already standing on them."""
        entities = [self.player, self.stairs_on_player]
        
        result = self.interaction_system.handle_click(
            5, 5,  # Click on stairs (same as player position)
            self.player,
            entities,
            self.game_map,
            self.fov_map
        )
        
        # Should trigger immediate stairs use
        self.assertTrue(result.action_taken)
        self.assertTrue(result.use_stairs)
        self.assertFalse(result.start_pathfinding)
        self.assertEqual(result.auto_explore_stop_reason, "Using Stairs")

    def test_right_click_stairs_when_distant(self):
        """Test right-clicking stairs when player is far away."""
        entities = [self.player, self.stairs_distant]
        
        result = self.interaction_system.handle_click(
            10, 10,  # Click on distant stairs
            self.player,
            entities,
            self.game_map,
            self.fov_map
        )
        
        # Should start pathfinding
        self.assertTrue(result.action_taken)
        self.assertTrue(result.start_pathfinding)
        self.assertFalse(result.use_stairs)
        
        # Should have set auto_stairs_target for auto-use on arrival
        pathfinding = self.player.get_component_optional(ComponentType.PATHFINDING)
        self.assertIsNotNone(pathfinding)
        self.assertEqual(pathfinding.auto_stairs_target, self.stairs_distant)

    def test_pathfinding_to_stairs_sets_correct_destination(self):
        """Test that pathfinding to stairs sets destination to stairs tile (not adjacent)."""
        entities = [self.player, self.stairs_distant]
        
        result = self.interaction_system.handle_click(
            10, 10,  # Click on distant stairs
            self.player,
            entities,
            self.game_map,
            self.fov_map
        )
        
        # Verify pathfinding destination is set to stairs tile
        pathfinding = self.player.get_component_optional(ComponentType.PATHFINDING)
        self.assertIsNotNone(pathfinding)
        
        # The destination should be the stairs tile (10, 10), not adjacent
        # This matches Enter key behavior (player must be ON stairs)
        self.assertIsNotNone(pathfinding.destination)
        self.assertEqual(pathfinding.destination, (10, 10))

    def test_auto_stairs_trigger_on_arrival(self):
        """Test that stairs are auto-used when pathfinding completes."""
        from mouse_movement import _check_auto_interactions
        
        entities = [self.player, self.stairs_distant]
        
        # Simulate player arriving at stairs
        self.player.x = 10
        self.player.y = 10
        
        # Set up pathfinding with auto_stairs_target
        pathfinding = self.player.get_component_optional(ComponentType.PATHFINDING)
        pathfinding.auto_stairs_target = self.stairs_distant
        
        # Check auto-interactions
        results = []
        _check_auto_interactions(self.player, entities, self.game_map, pathfinding, results)
        
        # Should have triggered stairs action
        self.assertEqual(len(results), 1)
        self.assertIn("take_stairs", results[0])
        self.assertTrue(results[0]["take_stairs"])
        
        # Should have cleared the auto_stairs_target
        self.assertIsNone(pathfinding.auto_stairs_target)

    def test_auto_stairs_cleared_if_player_not_on_stairs(self):
        """Test that auto_stairs_target is cleared even if player didn't reach stairs."""
        from mouse_movement import _check_auto_interactions
        
        entities = [self.player, self.stairs_distant]
        
        # Player is NOT at stairs position
        self.player.x = 8
        self.player.y = 8
        
        # Set up pathfinding with auto_stairs_target
        pathfinding = self.player.get_component_optional(ComponentType.PATHFINDING)
        pathfinding.auto_stairs_target = self.stairs_distant
        
        # Check auto-interactions
        results = []
        _check_auto_interactions(self.player, entities, self.game_map, pathfinding, results)
        
        # Should NOT have triggered stairs action (player not on stairs)
        self.assertEqual(len(results), 0)
        
        # Should still clear the auto_stairs_target
        self.assertIsNone(pathfinding.auto_stairs_target)

    def test_stairs_interaction_does_not_conflict_with_items(self):
        """Test that stairs interaction doesn't prevent item pickup when item is listed first."""
        # Create an item on the stairs tile
        from components.item import Item
        item_component = Item(use_function=None)
        item = Entity(
            x=10, y=10, char='!', color=(255, 0, 255), name='Potion',
            item=item_component
        )
        
        # IMPORTANT: List item BEFORE stairs in entities list
        # InteractionSystem checks entities in list order, not by strategy priority
        # This is existing behavior (not changed by stairs feature)
        entities = [self.player, item, self.stairs_distant]
        
        # Right-click the tile with both stairs and item
        result = self.interaction_system.handle_click(
            10, 10,
            self.player,
            entities,
            self.game_map,
            self.fov_map
        )
        
        # Should pick up the item (first entity at location that matches a strategy)
        self.assertTrue(result.action_taken)
        # Should start pathfinding to pick up item, NOT use stairs
        self.assertTrue(result.start_pathfinding)
        
        # Check that it's the item being targeted, not stairs
        pathfinding = self.player.get_component_optional(ComponentType.PATHFINDING)
        self.assertIsNotNone(pathfinding.auto_pickup_target)
        self.assertIsNone(getattr(pathfinding, 'auto_stairs_target', None))


class TestStairsRightClickIntegrationWithActionProcessor(unittest.TestCase):
    """Integration test with ActionProcessor to verify full right-click flow."""

    def setUp(self):
        """Set up full game state for integration testing."""
        from config.game_constants import get_constants
        
        self.state_manager = GameStateManager()
        self.constants = get_constants()
        
        # Create player
        self.player = Entity(
            x=5, y=5, char='@', color=(255, 255, 255), name='Player',
            fighter=Fighter(hp=30, defense=2, power=5),
            inventory=Inventory(capacity=26)
        )
        
        # Add pathfinding
        pathfinding = PlayerPathfinding()
        pathfinding.owner = self.player
        self.player.components.add(ComponentType.PATHFINDING, pathfinding)
        
        # Create stairs on player
        self.stairs = Entity(
            x=5, y=5, char='>', color=(255, 255, 255), name='Stairs',
            stairs=Stairs(floor=2)
        )
        
        # Create game map
        self.game_map = GameMap(width=80, height=50, dungeon_level=1)
        
        # Create message log
        self.message_log = Mock()
        
        # Create FOV map
        self.fov_map = Mock()
        
        # Set up game state
        self.state_manager.update_state(
            player=self.player,
            entities=[self.player, self.stairs],
            game_map=self.game_map,
            message_log=self.message_log,
            fov_map=self.fov_map,
            current_state=GameStates.PLAYERS_TURN,
        )

    def test_right_click_on_stairs_triggers_handle_stairs(self):
        """Test that right-clicking stairs while on them triggers _handle_stairs."""
        from game_actions import ActionProcessor
        
        processor = ActionProcessor(self.state_manager, self.constants)
        
        # Mock _handle_stairs to verify it's called
        with patch.object(processor, '_handle_stairs') as mock_handle_stairs:
            # Right-click on stairs (same position as player)
            processor._handle_right_click((5, 5))
            
            # Should have called _handle_stairs
            mock_handle_stairs.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
