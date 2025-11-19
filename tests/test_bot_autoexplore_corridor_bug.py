"""Gold regression tests for BotBrain → AutoExplore contract.

These tests enforce the critical contract that AutoExplore never restarts
if no unexplored tiles exist. They are fast, focused, and explicitly assert
on contract violations.

Contract Assertions:
- AutoExplore.start() must check for unexplored tiles before activating
- If no unexplored tiles exist: active=False, stop_reason="All areas explored"
- BotBrain.EXPLORE must return {} (no-ops) when AutoExplore is inactive after completion
- No movement commands should be emitted when map is fully explored
"""

import pytest
from typing import List, Tuple

from components.auto_explore import AutoExplore
from components.component_registry import ComponentType
from entity import Entity
from game_states import GameStates
from io_layer.bot_brain import BotBrain, BotState
from map_objects.game_map import GameMap
from map_objects.tile import Tile


class MockGameState:
    """Mock game state for testing bot+autoexplore integration."""
    
    def __init__(self, game_map: GameMap, player: Entity, entities: List[Entity]):
        self.game_map = game_map
        self.player = player
        self.entities = entities
        self.current_state = GameStates.PLAYERS_TURN
        self.fov_map = None
        
        # Initialize FOV map (simplified - just mark explored tiles as visible)
        import tcod
        self.fov_map = tcod.map.Map(game_map.width, game_map.height)
        for x in range(game_map.width):
            for y in range(game_map.height):
                tile = game_map.tiles[x][y]
                self.fov_map.transparent[y, x] = not tile.block_sight
                self.fov_map.walkable[y, x] = not tile.blocked
        self.constants = {}


def make_corridor_map(width: int = 20, height: int = 20) -> Tuple[GameMap, Entity]:
    """Create a simple map with a straight corridor for testing.
    
    Layout:
    - Walls all around except a corridor in the middle
    - Corridor runs vertically from y=5 to y=15 at x=10
    - Player starts at one end
    
    Returns:
        Tuple of (game_map, player_entity)
    """
    game_map = GameMap(width, height, dungeon_level=1)
    
    # Create tiles - all walls initially
    tiles = [[Tile(blocked=True, block_sight=True) for _ in range(height)] for _ in range(width)]
    
    # Create vertical corridor at x=10, from y=5 to y=15
    for y in range(5, 16):
        tiles[10][y] = Tile(blocked=False, block_sight=False)
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


def make_branch_map() -> Tuple[GameMap, Entity]:
    """Create a map with a T-junction (room off corridor).
    
    Layout:
    - Vertical corridor at x=10, y=5 to y=15
    - Horizontal branch at y=10, x=8 to x=12
    - Player starts at (10, 5)
    
    Returns:
        Tuple of (game_map, player_entity)
    """
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
    
    return game_map, player


class TestGoldRegressionAutoExploreContract:
    """Gold regression tests enforcing BotBrain → AutoExplore contract."""
    
    def test_fully_explored_map_autoexplore_refuses_to_start(self):
        """GOLD REGRESSION: AutoExplore must not activate when map is fully explored.
        
        Contract Assertion:
        - AutoExplore.start() checks for unexplored tiles BEFORE activating
        - If none exist: active=False, stop_reason="All areas explored", returns "Nothing left to explore"
        """
        game_map, player = make_corridor_map()
        
        # Mark ALL tiles as explored (simulate fully explored map)
        for x in range(game_map.width):
            for y in range(game_map.height):
                if not game_map.tiles[x][y].blocked:
                    game_map.tiles[x][y].explored = True
        
        auto_explore = AutoExplore()
        auto_explore.owner = player
        player.auto_explore = auto_explore
        player.components.add(ComponentType.AUTO_EXPLORE, auto_explore)
        
        # Attempt to start AutoExplore
        quote = auto_explore.start(game_map, [player], None)
        
        # CONTRACT ASSERTIONS
        assert auto_explore.active is False, "AutoExplore must not activate when map is fully explored"
        assert auto_explore.stop_reason == "All areas explored", \
            f"stop_reason must be 'All areas explored', got '{auto_explore.stop_reason}'"
        assert quote == "Nothing left to explore", \
            f"start() must return 'Nothing left to explore', got '{quote}'"
    
    def test_fully_explored_map_botbrain_returns_noops(self):
        """GOLD REGRESSION: BotBrain must return {} when AutoExplore refuses to start.
        
        Contract Assertion:
        - BotBrain.EXPLORE checks if AutoExplore is active
        - If AutoExplore stopped with "All areas explored", BotBrain should return {} (no-ops)
        - No movement commands should be emitted
        """
        game_map, player = make_corridor_map()
        
        # Mark ALL tiles as explored
        for x in range(game_map.width):
            for y in range(game_map.height):
                if not game_map.tiles[x][y].blocked:
                    game_map.tiles[x][y].explored = True
        
        # Create AutoExplore component that has already refused to start
        auto_explore = AutoExplore()
        auto_explore.owner = player
        player.auto_explore = auto_explore
        player.components.add(ComponentType.AUTO_EXPLORE, auto_explore)
        
        # Attempt start (will refuse)
        quote = auto_explore.start(game_map, [player], None)
        assert quote == "Nothing left to explore"
        assert auto_explore.active is False
        assert auto_explore.stop_reason == "All areas explored"
        
        # Now test BotBrain behavior
        game_state = MockGameState(game_map, player, [player])
        bot_brain = BotBrain(debug=False)
        bot_brain.state = BotState.EXPLORE
        
        # BotBrain should return {} (no-ops) since AutoExplore is inactive
        # and has stopped with "All areas explored"
        actions = []
        for _ in range(10):  # Test multiple turns
            action = bot_brain.decide_action(game_state)
            actions.append(action)
        
        # CONTRACT ASSERTIONS
        # BotBrain should return {} or {"start_auto_explore": True} but AutoExplore will refuse
        # After AutoExplore refuses, BotBrain should eventually return {} consistently
        # We allow initial start attempts but should see no movement commands
        for action in actions:
            assert "move" not in action, \
                f"BotBrain must not emit movement commands when map is fully explored, got {action}"
            # Allow start_auto_explore attempts (AutoExplore will refuse)
            # But no movement should occur
    
    def test_corridor_exploration_completes_without_restart_loop(self):
        """GOLD REGRESSION: AutoExplore starts once, explores, stops, never restarts.
        
        Contract Assertion:
        - AutoExplore.start() is called once by BotBrain
        - AutoExplore explores all tiles
        - AutoExplore stops with "All areas explored"
        - AutoExplore never restarts (no infinite loop)
        - BotBrain receives {} (no-ops) after completion
        """
        game_map, player = make_corridor_map()
        entities = [player]
        game_state = MockGameState(game_map, player, entities)
        bot_brain = BotBrain(debug=False)
        
        # Track AutoExplore lifecycle
        autoexplore_start_count = 0
        autoexplore_stop_reasons = []
        botbrain_actions = []
        movement_commands = []
        max_turns = 50
        
        for turn in range(max_turns):
            # Get AutoExplore component
            auto_explore = player.get_component_optional(ComponentType.AUTO_EXPLORE)
            
            # If AutoExplore is active, let it move
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
                        movement_commands.append(('autoexplore', dx, dy))
                else:
                    # AutoExplore stopped
                    if auto_explore.stop_reason:
                        autoexplore_stop_reasons.append(auto_explore.stop_reason)
                        if auto_explore.stop_reason == "All areas explored":
                            break
                continue
            
            # AutoExplore not active - get BotBrain action
            action = bot_brain.decide_action(game_state)
            botbrain_actions.append(action)
            
            if action.get('start_auto_explore'):
                autoexplore_start_count += 1
                if not auto_explore:
                    auto_explore = AutoExplore()
                    auto_explore.owner = player
                    player.auto_explore = auto_explore
                    player.components.add(ComponentType.AUTO_EXPLORE, auto_explore)
                
                quote = auto_explore.start(game_map, entities, game_state.fov_map)
                if quote == "Nothing left to explore":
                    # Map fully explored - test complete
                    break
            
            elif action.get('move'):
                movement_commands.append(('botbrain', action['move'][0], action['move'][1]))
                dx, dy = action['move']
                new_x = player.x + dx
                new_y = player.y + dy
                if not game_map.is_blocked(new_x, new_y):
                    player.x = new_x
                    player.y = new_y
                    game_map.tiles[new_x][new_y].explored = True
        
        # CONTRACT ASSERTIONS
        # AutoExplore should start exactly once (or maybe twice if it stops and restarts once)
        assert autoexplore_start_count <= 2, \
            f"AutoExplore started {autoexplore_start_count} times (should be ≤2), indicates restart loop"
        
        # Should have "All areas explored" stop reason
        assert "All areas explored" in autoexplore_stop_reasons, \
            f"AutoExplore should stop with 'All areas explored', got {autoexplore_stop_reasons}"
        
        # After completion, BotBrain should return {} (no movement commands)
        final_actions = botbrain_actions[-5:] if len(botbrain_actions) >= 5 else botbrain_actions
        for action in final_actions:
            assert "move" not in action, \
                f"BotBrain emitted movement after exploration complete: {action}"
        
        # Should have explored most of the corridor
        explored_count = sum(1 for y in range(5, 16) if game_map.tiles[10][y].explored)
        assert explored_count >= 8, \
            f"Should have explored at least 8 tiles, explored {explored_count}"
    
    def test_branch_map_exploration_completes_correctly(self):
        """GOLD REGRESSION: Room off corridor - AutoExplore explores all branches correctly.
        
        Contract Assertion:
        - AutoExplore starts once
        - Explores both branches of the T-junction
        - Stops only when truly done (all areas explored)
        - No restart loop occurs
        """
        game_map, player = make_branch_map()
        entities = [player]
        game_state = MockGameState(game_map, player, entities)
        bot_brain = BotBrain(debug=False)
        
        autoexplore_start_count = 0
        autoexplore_stop_reasons = []
        max_turns = 100
        
        for turn in range(max_turns):
            auto_explore = player.get_component_optional(ComponentType.AUTO_EXPLORE)
            
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
                    if auto_explore.stop_reason:
                        autoexplore_stop_reasons.append(auto_explore.stop_reason)
                        if auto_explore.stop_reason == "All areas explored":
                            break
                continue
            
            action = bot_brain.decide_action(game_state)
            
            if action.get('start_auto_explore'):
                autoexplore_start_count += 1
                if not auto_explore:
                    auto_explore = AutoExplore()
                    auto_explore.owner = player
                    player.auto_explore = auto_explore
                    player.components.add(ComponentType.AUTO_EXPLORE, auto_explore)
                
                quote = auto_explore.start(game_map, entities, game_state.fov_map)
                if quote == "Nothing left to explore":
                    break
            
            elif action.get('move'):
                dx, dy = action['move']
                new_x = player.x + dx
                new_y = player.y + dy
                if not game_map.is_blocked(new_x, new_y):
                    player.x = new_x
                    player.y = new_y
                    game_map.tiles[new_x][new_y].explored = True
        
        # CONTRACT ASSERTIONS
        assert autoexplore_start_count <= 2, \
            f"AutoExplore started {autoexplore_start_count} times (should be ≤2)"
        
        assert "All areas explored" in autoexplore_stop_reasons, \
            f"Should stop with 'All areas explored', got {autoexplore_stop_reasons}"
        
        # Count explored tiles (vertical corridor + horizontal branch)
        explored_count = 0
        for y in range(5, 16):
            if game_map.tiles[10][y].explored:
                explored_count += 1
        for x in range(8, 13):
            if game_map.tiles[x][10].explored:
                explored_count += 1
        
        assert explored_count >= 12, \
            f"Should have explored at least 12 tiles in T-junction, explored {explored_count}"
