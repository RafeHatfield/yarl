"""Tests for right-click chest interactions.

Tests verify:
- Right-click opens chest when adjacent
- Right-click initiates pathfinding when far from chest
- Right-click respects non-openable entities (current behavior preserved)
- Auto-open occurs after pathfinding completes
"""

import pytest
from entity import Entity
from components.component_registry import ComponentType
from components.chest import Chest, ChestState
from components.fighter import Fighter
from components.inventory import Inventory
from components.item import Item
from components.player_pathfinding import PlayerPathfinding
from engine.game_state_manager import GameStateManager
from systems.interaction_system import (
    InteractionSystem, ChestInteractionStrategy, InteractionResult
)
from game_states import GameStates
from game_messages import MessageLog
from map_objects.game_map import GameMap


@pytest.fixture
def state_manager():
    """Create a game state manager for testing."""
    manager = GameStateManager()
    return manager


@pytest.fixture
def game_map():
    """Create a simple game map for testing."""
    game_map = GameMap(width=50, height=50)
    # Make all tiles walkable for simplicity
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
    
    # Components are auto-registered via __setattr__, so no need to manually add
    # Add player tag
    player.tags.add('player')
    
    return player


@pytest.fixture
def closed_chest():
    """Create a closed chest for testing."""
    chest_entity = Entity(26, 25, 'C', (139, 69, 19), 'Chest')
    chest_component = Chest(
        state=ChestState.CLOSED,
        loot=[],
        loot_quality='common'
    )
    chest_entity.chest = chest_component
    chest_component.owner = chest_entity
    chest_entity.tags.add('openable')
    # Component is auto-registered via __setattr__
    return chest_entity


@pytest.fixture
def open_chest():
    """Create an already-open chest."""
    chest_entity = Entity(27, 25, 'C', (139, 69, 19), 'Empty Chest')
    chest_component = Chest(
        state=ChestState.OPEN,
        loot=[],
        loot_quality='common'
    )
    chest_entity.chest = chest_component
    chest_component.owner = chest_entity
    chest_entity.tags.add('openable')
    # Component is auto-registered via __setattr__
    return chest_entity


@pytest.fixture
def trapped_chest():
    """Create a trapped chest."""
    chest_entity = Entity(28, 25, 'C', (139, 69, 19), 'Trapped Chest')
    chest_component = Chest(
        state=ChestState.TRAPPED,
        loot=[],
        trap_type='damage',
        loot_quality='common'
    )
    chest_entity.chest = chest_component
    chest_component.owner = chest_entity
    chest_entity.tags.add('openable')
    # Component is auto-registered via __setattr__
    return chest_entity


@pytest.fixture
def message_log():
    """Create a message log."""
    return MessageLog(x=0, y=0, width=100, height=100)


@pytest.fixture
def fov_map(game_map):
    """Create a simple FOV map (all visible)."""
    fov_map = [[True] * game_map.width for _ in range(game_map.height)]
    return fov_map


class TestChestInteractionStrategy:
    """Test the ChestInteractionStrategy."""
    
    def test_can_interact_with_closed_chest(self, player, closed_chest):
        """Test that strategy recognizes closed chests as interactable."""
        strategy = ChestInteractionStrategy()
        assert strategy.can_interact(closed_chest, player)
    
    def test_can_interact_with_open_chest(self, player, open_chest):
        """Test that strategy recognizes open chests (interact method handles them)."""
        strategy = ChestInteractionStrategy()
        # Note: We return True for open chests so interact() can show a message
        assert strategy.can_interact(open_chest, player)
    
    def test_cannot_interact_with_non_openable(self, player):
        """Test that strategy rejects entities without openable tag."""
        stone = Entity(25, 26, '#', (128, 128, 128), 'Stone')
        strategy = ChestInteractionStrategy()
        assert not strategy.can_interact(stone, player)
    
    def test_priority(self):
        """Test that chest priority is between enemies and items."""
        strategy = ChestInteractionStrategy()
        # Should be 0.5 (between Enemy 0 and Item 1)
        assert strategy.get_priority() == 0.5


class TestChestInteractionAdjacent:
    """Test right-click chest opening when adjacent."""
    
    def test_right_click_open_adjacent_chest(self, player, closed_chest, game_map, fov_map):
        """Test opening chest when adjacent (Manhattan distance ≤ 1)."""
        # Position player next to chest
        player.x, player.y = 25, 25
        closed_chest.x, closed_chest.y = 26, 25  # Adjacent
        
        # Create interaction system
        interaction_system = InteractionSystem()
        entities = [player, closed_chest]
        
        # Handle right-click on chest
        result = interaction_system.handle_click(
            closed_chest.x, closed_chest.y,
            player, entities, game_map, fov_map
        )
        
        # Verify interaction was handled
        assert result.action_taken
        assert result.consume_turn
        # Chest should now be open
        assert closed_chest.chest.state == ChestState.OPEN
    
    def test_adjacent_chest_generates_message(self, player, closed_chest, game_map, fov_map):
        """Test that opening adjacent chest produces a message."""
        player.x, player.y = 25, 25
        closed_chest.x, closed_chest.y = 25, 26
        
        interaction_system = InteractionSystem()
        entities = [player, closed_chest]
        
        result = interaction_system.handle_click(
            closed_chest.x, closed_chest.y,
            player, entities, game_map, fov_map
        )
        
        # Verify message was generated
        assert result.message is not None


class TestChestInteractionPathfinding:
    """Test right-click chest pathfinding when far away."""
    
    def test_right_click_far_chest_initiates_pathfinding(self, player, closed_chest, game_map, fov_map):
        """Test that right-clicking far chest attempts pathfinding.
        
        Note: Pathfinding may fail if the destination is unreachable,
        but the interaction system should try to initiate it.
        """
        # Position player and chest far apart
        player.x, player.y = 10, 10
        closed_chest.x, closed_chest.y = 30, 30
        
        interaction_system = InteractionSystem()
        entities = [player, closed_chest]
        
        # Handle right-click on distant chest
        result = interaction_system.handle_click(
            closed_chest.x, closed_chest.y,
            player, entities, game_map, fov_map
        )
        
        # Interaction should be handled (either success or failure message)
        assert result.action_taken
        # Either pathfinding started or we got a message about unreachable location
        # The key is that the chest interaction was recognized
        if result.start_pathfinding:
            assert player.pathfinding.auto_open_target == closed_chest
        else:
            # Pathfinding failed, but we still got a message
            assert result.message is not None
    
    def test_auto_open_target_cleared_on_interrupt(self, player, closed_chest):
        """Test that auto_open_target is cleared on movement interrupt."""
        player.pathfinding.auto_open_target = closed_chest
        # Set is_moving=True so interrupt actually works
        player.pathfinding.is_moving = True
        
        # Interrupt movement
        player.pathfinding.interrupt_movement()
        
        # auto_open_target should be cleared
        assert player.pathfinding.auto_open_target is None
    
    def test_auto_open_target_cleared_on_cancel(self, player, closed_chest):
        """Test that auto_open_target is cleared on movement cancel."""
        player.pathfinding.auto_open_target = closed_chest
        
        # Cancel movement
        player.pathfinding.cancel_movement()
        
        # auto_open_target should be cleared
        assert player.pathfinding.auto_open_target is None


class TestChestInteractionNonOpenable:
    """Test that non-openable tiles preserve current behavior."""
    
    def test_right_click_empty_tile(self, player, game_map, fov_map):
        """Test right-click on empty tile (no entities)."""
        player.x, player.y = 25, 25
        empty_tile_x, empty_tile_y = 26, 26
        
        interaction_system = InteractionSystem()
        entities = [player]
        
        # Right-click empty tile
        result = interaction_system.handle_click(
            empty_tile_x, empty_tile_y,
            player, entities, game_map, fov_map
        )
        
        # Should not handle interaction
        assert not result.action_taken
    
    def test_right_click_stone_tile(self, player, game_map, fov_map):
        """Test right-click on non-interactive entity (stone)."""
        player.x, player.y = 25, 25
        
        # Create non-openable stone
        stone = Entity(26, 25, '#', (128, 128, 128), 'Stone')
        
        interaction_system = InteractionSystem()
        entities = [player, stone]
        
        # Right-click stone (no 'openable' tag)
        result = interaction_system.handle_click(
            stone.x, stone.y,
            player, entities, game_map, fov_map
        )
        
        # Should not handle as chest interaction
        assert not result.action_taken


class TestChestInteractionTrappedChest:
    """Test interactions with trapped chests."""
    
    def test_right_click_trapped_chest_adjacent(self, player, trapped_chest, game_map, fov_map):
        """Test opening trapped chest reveals trap message and opens."""
        player.x, player.y = 25, 25
        trapped_chest.x, trapped_chest.y = 26, 25
        
        interaction_system = InteractionSystem()
        entities = [player, trapped_chest]
        
        result = interaction_system.handle_click(
            trapped_chest.x, trapped_chest.y,
            player, entities, game_map, fov_map
        )
        
        # Interaction should be handled
        assert result.action_taken
        # Chest state should change from TRAPPED to OPEN (trap sprung and chest opens)
        # The trap is sprung, then the chest opens
        assert trapped_chest.chest.state == ChestState.OPEN


class TestChestInteractionAlreadyOpen:
    """Test interactions with already-open chests."""
    
    def test_right_click_open_chest_shows_already_empty_message(self, player, open_chest, game_map, fov_map):
        """Test that right-clicking already-open chest shows 'already empty' message."""
        player.x, player.y = 25, 25
        open_chest.x, open_chest.y = 26, 25
        
        interaction_system = InteractionSystem()
        entities = [player, open_chest]
        
        result = interaction_system.handle_click(
            open_chest.x, open_chest.y,
            player, entities, game_map, fov_map
        )
        
        # Should show a message but not consume a turn
        assert result.action_taken
        assert result.message is not None
        assert "empty" in str(result.message).lower()
        assert result.consume_turn is False


class TestChestInteractionPriority:
    """Test that chest interactions respect priority ordering."""
    
    def test_chest_priority_over_items(self, player, closed_chest, game_map, fov_map):
        """Test that chest takes priority over item on same tile."""
        player.x, player.y = 25, 25
        closed_chest.x, closed_chest.y = 26, 25
        
        # Create an item at same location (should not be chosen)
        item_entity = Entity(26, 25, '*', (255, 255, 0), 'Gold Coin')
        item_component = Item()
        item_entity.item = item_component
        # Component is auto-registered via __setattr__
        
        interaction_system = InteractionSystem()
        entities = [player, closed_chest, item_entity]
        
        # Find which entity is interacted with
        result = interaction_system.handle_click(
            26, 25, player, entities, game_map, fov_map
        )
        
        # Should handle chest (higher priority than items)
        assert result.action_taken
        # Chest should be opened
        assert closed_chest.chest.state == ChestState.OPEN
    
    def test_enemy_priority_over_chest(self, player, closed_chest, game_map, fov_map):
        """Test that enemy has higher priority than chest."""
        player.x, player.y = 25, 25
        closed_chest.x, closed_chest.y = 26, 25
        
        # Create an enemy at same location
        enemy = Entity(26, 25, 'o', (255, 0, 0), 'Goblin')
        fighter = Fighter(hp=10, defense=1, power=5)
        enemy.fighter = fighter
        # Component is auto-registered via __setattr__
        
        interaction_system = InteractionSystem()
        entities = [player, enemy, closed_chest]
        
        result = interaction_system.handle_click(
            26, 25, player, entities, game_map, fov_map
        )
        
        # Should handle enemy (throw menu)
        assert result.action_taken
        # Chest should NOT be opened (enemy had priority)
        assert closed_chest.chest.state == ChestState.CLOSED


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

