"""Test for bot+AutoExplore corridor pacing bug.

This test reproduces the issue where the bot gets stuck pacing back and forth
in a corridor when using EXPLORE mode, even though manual autoexplore works fine.
"""

import pytest
import logging
from typing import List, Tuple

from components.auto_explore import AutoExplore
from components.component_registry import ComponentType
from entity import Entity
from game_states import GameStates
from io_layer.bot_brain import BotBrain
from map_objects.game_map import GameMap
from map_objects.tile import Tile

# Enable debug logging for this test
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class MockGameState:
    """Mock game state for testing bot+autoexplore integration."""
    
    def __init__(self, game_map: GameMap, player: Entity, entities: List[Entity]):
        self.game_map = game_map
        self.player = player
        self.entities = entities
        self.current_state = GameStates.PLAYERS_TURN
        self.fov_map = None  # We'll use explored tiles instead
        self.constants = {}
        
        # Initialize FOV map (simplified - just mark explored tiles as visible)
        import tcod
        self.fov_map = tcod.map.Map(game_map.width, game_map.height)
        for x in range(game_map.width):
            for y in range(game_map.height):
                tile = game_map.tiles[x][y]
                self.fov_map.transparent[y, x] = not tile.block_sight
                self.fov_map.walkable[y, x] = not tile.blocked


def make_corridor_map(width: int = 20, height: int = 20) -> Tuple[GameMap, Entity]:
    """Create a simple map with a straight corridor for testing.
    
    Layout:
    - Walls all around except a corridor in the middle
    - Corridor runs vertically from y=5 to y=15 at x=10
    - Player starts at one end
    
    Returns:
        Tuple of (game_map, player_entity)
    """
    # Create GameMap (it will initialize hazard_manager automatically)
    game_map = GameMap(width, height, dungeon_level=1)
    
    # Create tiles - all walls initially
    tiles = [[Tile(blocked=True, block_sight=True) for _ in range(height)] for _ in range(width)]
    
    # Create vertical corridor at x=10, from y=5 to y=15
    for y in range(5, 16):
        tiles[10][y] = Tile(blocked=False, block_sight=False)
        # Mark as not explored yet so AutoExplore can explore them
        tiles[10][y].explored = False
    
    game_map.tiles = tiles
    
    # Create player at start of corridor
    from components.fighter import Fighter
    from components.faction import Faction
    
    player = Entity(10, 5, '@', 'white', 'Player', blocks=True,
                   fighter=Fighter(hp=100, defense=10, power=5),
                   faction=Faction.PLAYER)
    
    # Mark player's starting position as explored (as would happen in real game)
    game_map.tiles[player.x][player.y].explored = True
    
    return game_map, player


def test_bot_autoexplore_corridor_does_not_pace():
    """Test that bot+AutoExplore doesn't get stuck pacing in a corridor.
    
    This test:
    1. Creates a simple straight corridor
    2. Uses BotBrain in EXPLORE mode
    3. Runs until AutoExplore stops or max turns reached
    4. Fails if bot oscillates (revisits same positions too many times)
    """
    # Setup
    game_map, player = make_corridor_map(width=20, height=20)
    entities = [player]
    game_state = MockGameState(game_map, player, entities)
    
    bot_brain = BotBrain(debug=True)
    
    # Track player positions to detect oscillation
    position_history: List[Tuple[int, int]] = []
    max_turns = 100
    
    logger.info("=" * 60)
    logger.info("STARTING BOT AUTOEXPLORE CORRIDOR TEST")
    logger.info("=" * 60)
    
    for turn in range(max_turns):
        pos = (player.x, player.y)
        position_history.append(pos)
        
        logger.info(f"\n--- Turn {turn + 1} ---")
        logger.info(f"Player position: {pos}")
        
        # Get AutoExplore component state BEFORE bot decision
        auto_explore = player.get_component_optional(ComponentType.AUTO_EXPLORE)
        is_active = auto_explore and auto_explore.is_active()
        logger.info(f"AutoExplore active (before bot decision): {is_active}")
        
        # If AutoExplore is active, let it move the player FIRST (like ActionProcessor does)
        if auto_explore and auto_explore.is_active():
            logger.info("Processing AutoExplore turn...")
            move_action = auto_explore.get_next_action(game_map, entities, game_state.fov_map)
            
            if move_action:
                dx = move_action.get('dx', 0)
                dy = move_action.get('dy', 0)
                new_x = player.x + dx
                new_y = player.y + dy
                
                if not game_map.is_blocked(new_x, new_y):
                    player.x = new_x
                    player.y = new_y
                    game_map.tiles[new_x][new_y].explored = True
                    logger.info(f"AutoExplore moved to ({new_x}, {new_y})")
            else:
                logger.info(f"AutoExplore returned None - stopped: {auto_explore.stop_reason}")
                # If it stopped because all areas are explored, we're done!
                if auto_explore.stop_reason == "All areas explored":
                    logger.info("Exploration complete!")
                    break
            
            # After AutoExplore moves, continue to next turn (don't also process bot action)
            continue
        
        # If AutoExplore is NOT active, let BotBrain decide
        logger.info("AutoExplore not active, asking BotBrain for action...")
        action = bot_brain.decide_action(game_state)
        logger.info(f"BotBrain action: {action}")
        
        # Check if we should stop
        if not action or action == {}:
            logger.info("BotBrain returned empty action, checking if we should stop...")
            if auto_explore and not is_active:
                logger.info(f"AutoExplore stopped: {auto_explore.stop_reason}")
                # This is normal - autoexplore finished
                break
            logger.info("No action, continuing...")
        
        # Process BotBrain action
        if action.get('start_auto_explore'):
            # Simulate ActionProcessor._handle_start_auto_explore
            logger.info("BotBrain wants to start AutoExplore")
            if not auto_explore:
                auto_explore = AutoExplore()
                auto_explore.owner = player
                player.auto_explore = auto_explore
                player.components.add(ComponentType.AUTO_EXPLORE, auto_explore)
            
            quote = auto_explore.start(game_map, entities, game_state.fov_map)
            logger.info(f"AutoExplore started: {quote}")
            # Don't move this turn - just started autoexplore
            
            # If AutoExplore refused to start because there's nothing to explore, we're done!
            if quote == "Nothing left to explore":
                logger.info("Exploration complete! Bot has nothing more to do.")
                break
            
        elif action.get('move'):
            # Direct movement from BotBrain (combat mode)
            dx, dy = action['move']
            new_x = player.x + dx
            new_y = player.y + dy
            
            if not game_map.is_blocked(new_x, new_y):
                player.x = new_x
                player.y = new_y
                game_map.tiles[new_x][new_y].explored = True
                logger.info(f"BotBrain moved to ({new_x}, {new_y})")
        
        # Check for oscillation: if we've visited the same 2-tile area more than 10 times
        if len(position_history) >= 20:
            recent_positions = position_history[-20:]
            unique_positions = set(recent_positions)
            
            if len(unique_positions) <= 2:
                # Bot is stuck oscillating between 2 positions
                pytest.fail(
                    f"Bot is oscillating in corridor! Turn {turn + 1}, "
                    f"positions in last 20 turns: {unique_positions}\n"
                    f"Full history: {position_history}"
                )
    
    # If we got here, check that we actually explored the corridor
    # The corridor has 11 tiles (y=5 to y=15), we should have explored most of them
    explored_count = sum(1 for y in range(5, 16) if game_map.tiles[10][y].explored)
    
    logger.info(f"\nTest completed in {len(position_history)} turns")
    logger.info(f"Explored {explored_count}/11 corridor tiles")
    logger.info(f"Position history: {position_history}")
    
    # We should have explored at least 8 tiles (allowing for some early stop conditions)
    assert explored_count >= 8, f"Bot should have explored most of corridor, but only explored {explored_count}/11 tiles"
    
    # We shouldn't take more than 50 turns to explore a simple 11-tile corridor
    assert len(position_history) <= 50, f"Bot took {len(position_history)} turns to explore 11-tile corridor (should be ~11-20)"


def test_bot_autoexplore_with_branch_does_not_pace():
    """Test that bot+AutoExplore doesn't get stuck when corridor has a branch.
    
    This is a more realistic scenario where the corridor has a T-junction or branch.
    """
    # Create map with T-junction
    width, height = 20, 20
    game_map = GameMap(width, height, dungeon_level=1)
    
    # Create tiles - all walls initially
    tiles = [[Tile(blocked=True, block_sight=True) for _ in range(height)] for _ in range(width)]
    
    # Vertical corridor at x=10, y=5 to y=15
    for y in range(5, 16):
        tiles[10][y] = Tile(blocked=False, block_sight=False)
        tiles[10][y].explored = False
    
    # Horizontal branch at y=10, x=8 to x=12
    for x in range(8, 13):
        tiles[x][10] = Tile(blocked=False, block_sight=False)
        tiles[x][10].explored = False
    
    game_map.tiles = tiles
    
    # Create player at start
    from components.fighter import Fighter
    from components.faction import Faction
    
    player = Entity(10, 5, '@', 'white', 'Player', blocks=True,
                   fighter=Fighter(hp=100, defense=10, power=5),
                   faction=Faction.PLAYER)
    
    # Mark player's starting position as explored
    game_map.tiles[player.x][player.y].explored = True
    
    entities = [player]
    game_state = MockGameState(game_map, player, entities)
    bot_brain = BotBrain(debug=True)
    
    position_history: List[Tuple[int, int]] = []
    max_turns = 150
    
    logger.info("=" * 60)
    logger.info("STARTING BOT AUTOEXPLORE T-JUNCTION TEST")
    logger.info("=" * 60)
    
    for turn in range(max_turns):
        pos = (player.x, player.y)
        position_history.append(pos)
        
        auto_explore = player.get_component_optional(ComponentType.AUTO_EXPLORE)
        is_active = auto_explore and auto_explore.is_active()
        
        action = bot_brain.decide_action(game_state)
        
        if not action or action == {}:
            if auto_explore and not is_active:
                logger.info(f"Turn {turn + 1}: AutoExplore stopped: {auto_explore.stop_reason}")
                break
        
        if action.get('start_auto_explore'):
            if not auto_explore:
                auto_explore = AutoExplore()
                auto_explore.owner = player
                player.auto_explore = auto_explore
                player.components.add(ComponentType.AUTO_EXPLORE, auto_explore)
            
            quote = auto_explore.start(game_map, entities, game_state.fov_map)
            # If AutoExplore refused to start because there's nothing to explore, we're done!
            if quote == "Nothing left to explore":
                logger.info(f"Turn {turn + 1}: Exploration complete! Bot has nothing more to do.")
                break
            
        elif action.get('move'):
            dx, dy = action['move']
            new_x = player.x + dx
            new_y = player.y + dy
            
            if not game_map.is_blocked(new_x, new_y):
                player.x = new_x
                player.y = new_y
                game_map.tiles[new_x][new_y].explored = True
        
        if auto_explore and auto_explore.is_active():
            move_action = auto_explore.get_next_action(game_map, entities, game_state.fov_map)
            
            if move_action:
                dx = move_action.get('dx', 0)
                dy = move_action.get('dy', 0)
                new_x = player.x + dx
                new_y = player.y + dy
                
                if not game_map.is_blocked(new_x, new_y):
                    player.x = new_x
                    player.y = new_y
                    game_map.tiles[new_x][new_y].explored = True
            else:
                # AutoExplore stopped
                if auto_explore.stop_reason == "All areas explored":
                    logger.info(f"Turn {turn + 1}: Exploration complete!")
                    break
        
        # Check for oscillation in last 30 turns
        if len(position_history) >= 30:
            recent_positions = position_history[-30:]
            unique_positions = set(recent_positions)
            
            if len(unique_positions) <= 3:
                pytest.fail(
                    f"Bot is oscillating in T-junction! Turn {turn + 1}, "
                    f"positions in last 30 turns: {unique_positions}"
                )
    
    # Count explored tiles
    explored_count = 0
    for y in range(5, 16):
        if game_map.tiles[10][y].explored:
            explored_count += 1
    for x in range(8, 13):
        if game_map.tiles[x][10].explored:
            explored_count += 1
    
    logger.info(f"\nT-junction test completed in {len(position_history)} turns")
    logger.info(f"Explored {explored_count} tiles")
    
    # Should explore most of the accessible area
    assert explored_count >= 12, f"Bot should have explored most of T-junction, but only explored {explored_count} tiles"
    assert len(position_history) <= 100, f"Bot took {len(position_history)} turns (should be less)"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])

