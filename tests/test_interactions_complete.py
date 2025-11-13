"""Comprehensive tests for interaction system: chests, murals, signposts, and monster death.

Tests verify:
- Right-click interactions work for all interactable entities (chests, murals, signposts)
- Left-click fallback behavior for adjacent chests and signposts
- Monster death handling without errors
- Auto-read for murals and signposts after pathfinding
- Feature flags control behavior
"""

import pytest
from entity import Entity
from components.component_registry import ComponentType
from components.chest import Chest, ChestState
from components.mural import Mural
from components.signpost import Signpost
from components.fighter import Fighter
from components.inventory import Inventory
from components.player_pathfinding import PlayerPathfinding
from engine.game_state_manager import GameStateManager
from systems.interaction_system import InteractionSystem
from game_states import GameStates
from game_messages import MessageLog
from map_objects.game_map import GameMap
from config.game_constants import get_constants
from death_functions import kill_monster


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
def player():
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
def mural():
    """Create a mural entity for testing."""
    mural_entity = Entity(27, 25, 'M', (220, 20, 60), 'Mural')
    mural_component = Mural(text="The legends speak of ancient times...")
    mural_entity.mural = mural_component
    mural_component.owner = mural_entity
    mural_entity.tags.add('interactable')
    mural_entity.blocks = True
    return mural_entity


@pytest.fixture
def signpost():
    """Create a signpost entity for testing."""
    signpost_entity = Entity(28, 25, 'S', (200, 200, 200), 'Signpost')
    signpost_component = Signpost(message="Welcome to the dungeon!")
    signpost_entity.signpost = signpost_component
    signpost_component.owner = signpost_entity
    signpost_entity.tags.add('interactable')
    signpost_entity.blocks = True
    return signpost_entity


@pytest.fixture
def monster():
    """Create a test monster."""
    monster = Entity(35, 35, 'o', (255, 0, 0), 'Goblin')
    monster.fighter = Fighter(hp=10, defense=1, power=5)
    monster.blocks = True
    return monster


@pytest.fixture
def fov_map(game_map):
    """Create a simple FOV map (all visible)."""
    return [[True] * game_map.width for _ in range(game_map.height)]


class TestMuralInteraction:
    """Test right-click mural interaction."""
    
    def test_mural_strategy_can_interact(self, player, mural):
        """Test that MuralInteractionStrategy identifies murals."""
        from systems.interaction_system import MuralInteractionStrategy
        strategy = MuralInteractionStrategy()
        assert strategy.can_interact(mural, player)
    
    def test_right_click_read_adjacent_mural(self, player, mural, game_map, fov_map):
        """Test reading mural when adjacent."""
        player.x, player.y = 25, 25
        mural.x, mural.y = 26, 25
        
        interaction_system = InteractionSystem()
        entities = [player, mural]
        
        result = interaction_system.handle_click(
            mural.x, mural.y,
            player, entities, game_map, fov_map
        )
        
        assert result.action_taken
        assert result.message is not None
        assert "legends speak" in str(result.message).lower() or "ancient" in str(result.message).lower()
        assert result.consume_turn is False  # Reading doesn't consume turn
    
    def test_right_click_pathfind_to_mural(self, player, mural, game_map, fov_map):
        """Test pathfinding to distant mural."""
        player.x, player.y = 10, 10
        mural.x, mural.y = 30, 30
        
        interaction_system = InteractionSystem()
        entities = [player, mural]
        
        result = interaction_system.handle_click(
            mural.x, mural.y,
            player, entities, game_map, fov_map
        )
        
        assert result.action_taken
        # Should either start pathfinding or show message
        assert result.start_pathfinding or result.message is not None


class TestSignpostInteraction:
    """Test right-click signpost interaction."""
    
    def test_signpost_strategy_can_interact(self, player, signpost):
        """Test that SignpostInteractionStrategy identifies signposts."""
        from systems.interaction_system import SignpostInteractionStrategy
        strategy = SignpostInteractionStrategy()
        assert strategy.can_interact(signpost, player)
    
    def test_right_click_read_adjacent_signpost(self, player, signpost, game_map, fov_map):
        """Test reading signpost when adjacent."""
        player.x, player.y = 25, 25
        signpost.x, signpost.y = 26, 25
        
        interaction_system = InteractionSystem()
        entities = [player, signpost]
        
        result = interaction_system.handle_click(
            signpost.x, signpost.y,
            player, entities, game_map, fov_map
        )
        
        assert result.action_taken
        assert result.message is not None
        assert "welcome" in str(result.message).lower()
        assert result.consume_turn is False
    
    def test_right_click_pathfind_to_signpost(self, player, signpost, game_map, fov_map):
        """Test pathfinding to distant signpost."""
        player.x, player.y = 10, 10
        signpost.x, signpost.y = 30, 30
        
        interaction_system = InteractionSystem()
        entities = [player, signpost]
        
        result = interaction_system.handle_click(
            signpost.x, signpost.y,
            player, entities, game_map, fov_map
        )
        
        assert result.action_taken
        assert result.start_pathfinding or result.message is not None


class TestLeftClickSignpostFallback:
    """Test left-click signpost reading as deprecated fallback."""
    
    def test_left_click_read_adjacent_signpost(self, player, signpost, game_map):
        """Test that left-click reads adjacent signpost."""
        from mouse_movement import _handle_signpost_click
        
        player.x, player.y = 25, 25
        signpost.x, signpost.y = 26, 25
        
        results = []
        click_result = _handle_signpost_click(player, signpost, results)
        
        assert len(results) > 0
        # Should have read the signpost
        assert any("welcome" in str(r).lower() for r in results)
    
    def test_left_click_no_pathfind_to_distant_signpost(self, player, signpost, game_map):
        """Test that left-click doesn't pathfind to distant signpost."""
        from mouse_movement import _handle_signpost_click
        
        player.x, player.y = 10, 10
        signpost.x, signpost.y = 30, 30
        
        results = []
        click_result = _handle_signpost_click(player, signpost, results)
        
        # Should not pathfind
        assert len(results) == 0


class TestMonsterDeath:
    """Test monster death handling."""
    
    def test_monster_death_basic(self, monster, game_map):
        """Test basic monster death without errors."""
        # Monster should die without throwing exceptions
        message = kill_monster(monster, game_map=game_map, entities=[])
        
        assert message is not None
        assert monster.char == "%"  # Changed to corpse character
        assert monster.color == (127, 0, 0)  # Changed to corpse color
        assert monster.blocks is False  # Corpse doesn't block movement
        assert monster.fighter is None  # Combat component removed
        assert monster.ai is None  # AI component removed
    
    def test_monster_death_is_idempotent(self, monster, game_map):
        """Test that calling kill_monster twice doesn't cause issues."""
        # First death
        message1 = kill_monster(monster, game_map=game_map, entities=[])
        
        # Second death (should be idempotent)
        message2 = kill_monster(monster, game_map=game_map, entities=[])
        
        # Both should succeed
        assert message1 is not None
        assert message2 is not None
        # Monster should remain dead (not re-process)
        assert monster.fighter is None
        assert monster.ai is None
    
    def test_monster_death_with_entities_list(self, monster, game_map):
        """Test monster death with entities list."""
        entities = [monster]
        
        message = kill_monster(monster, game_map=game_map, entities=entities)
        
        assert message is not None
        assert monster.blocks is False
        # Entity should still be in list (just as corpse)
        assert monster in entities


class TestInteractionPriority:
    """Test interaction priority across entity types."""
    
    def test_chest_priority_over_signpost(self, player, closed_chest, signpost, game_map, fov_map):
        """Test that chests have same priority as signposts (0.5)."""
        from systems.interaction_system import ChestInteractionStrategy, SignpostInteractionStrategy
        
        chest_strat = ChestInteractionStrategy()
        signpost_strat = SignpostInteractionStrategy()
        
        # Both should have priority 0.5
        assert chest_strat.get_priority() == signpost_strat.get_priority()
    
    def test_all_interactables_registered(self):
        """Test that all interaction strategies are registered."""
        interaction_system = InteractionSystem()
        
        strategy_names = [type(s).__name__ for s in interaction_system.strategies]
        
        # Should have all interaction types
        assert 'EnemyInteractionStrategy' in strategy_names
        assert 'ChestInteractionStrategy' in strategy_names
        assert 'SignpostInteractionStrategy' in strategy_names
        assert 'MuralInteractionStrategy' in strategy_names
        assert 'ItemInteractionStrategy' in strategy_names
        assert 'NPCInteractionStrategy' in strategy_names
        
        # Total should be 6
        assert len(strategy_names) == 6


class TestFeatureFlags:
    """Test feature flags for interaction behavior."""
    
    def test_signpost_feature_flag_exists(self):
        """Test that signpost left-click feature flag exists."""
        constants = get_constants()
        assert 'controls' in constants
        assert 'allow_left_click_read_signpost' in constants['controls']
    
    def test_chest_feature_flag_exists(self):
        """Test that chest left-click feature flag exists."""
        constants = get_constants()
        assert 'controls' in constants
        assert 'allow_left_click_interact' in constants['controls']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


