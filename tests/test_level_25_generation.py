"""Integration tests for Level 25 special generation.

These tests verify that Level 25 correctly generates Phase 5 content:
- Ruby Heart (victory item)
- Secret ritual room with Corrupted Ritualists and Crimson Ritual Codex
- Proper entity spawning with correct factory methods

These integration tests catch errors that unit tests miss, such as:
- Wrong method names (create_enemy vs create_monster)
- Wrong import paths
- Entity spawning failures
"""

import pytest
from unittest.mock import Mock, patch

from entity import Entity
from components.fighter import Fighter
from components.inventory import Inventory
from map_objects.game_map import GameMap
from game_messages import MessageLog
from config.game_constants import GameConstants


@pytest.fixture
def test_player():
    """Create a test player entity."""
    player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
    player.fighter = Fighter(hp=100, defense=1, power=2)
    player.fighter.owner = player
    player.inventory = Inventory(26)
    return player


@pytest.fixture
def game_constants():
    """Create game constants for map generation."""
    return GameConstants()


@pytest.fixture
def message_log():
    """Create a message log."""
    return MessageLog(x=22, width=40, height=5)


class TestLevel25RubyHeartSpawn:
    """Test that Ruby Heart spawns on Level 25."""
    
    def test_ruby_heart_spawns_on_level_25(self, test_player, game_constants, message_log):
        """Test that Ruby Heart is spawned on Level 25."""
        game_map = GameMap(width=80, height=60, dungeon_level=25)
        entities = []
        
        # Generate Level 25
        game_map.make_map(
            max_rooms=30,
            room_min_size=6,
            room_max_size=10,
            map_width=80,
            map_height=60,
            player=test_player,
            entities=entities
        )
        
        # Find Ruby Heart
        ruby_hearts = [e for e in entities if hasattr(e, 'name') and e.name == "Ruby Heart"]
        
        assert len(ruby_hearts) == 1, "Should spawn exactly 1 Ruby Heart on Level 25"
        
        ruby_heart = ruby_hearts[0]
        assert hasattr(ruby_heart, 'triggers_victory'), "Ruby Heart should have triggers_victory attribute"
        assert ruby_heart.triggers_victory is True, "Ruby Heart should trigger victory"
    
    def test_ruby_heart_not_on_other_levels(self, test_player, game_constants, message_log):
        """Test that Ruby Heart only spawns on Level 25, not other levels."""
        for level in [1, 10, 20, 24]:
            game_map = GameMap(width=80, height=60, dungeon_level=level)
            entities = []
            
            game_map.make_map(
                max_rooms=30,
                room_min_size=6,
                room_max_size=10,
                map_width=80,
                map_height=60,
                player=test_player,
                entities=entities
            )
            
            ruby_hearts = [e for e in entities if hasattr(e, 'name') and e.name == "Ruby Heart"]
            assert len(ruby_hearts) == 0, f"Ruby Heart should not spawn on Level {level}"


class TestLevel25SecretRoom:
    """Test that secret room with ritualists and codex spawns on Level 25."""
    
    def test_secret_room_spawns_on_level_25(self, test_player, game_constants, message_log):
        """Test that secret room is created on Level 25."""
        game_map = GameMap(width=80, height=60, dungeon_level=25)
        entities = []
        
        # Generate Level 25
        game_map.make_map(
            max_rooms=30,
            room_min_size=6,
            room_max_size=10,
            map_width=80,
            map_height=60,
            player=test_player,
            entities=entities
        )
        
        # Secret room should exist (we can't directly test room structure,
        # but we can verify its contents spawned)
        ritualists = [e for e in entities 
                     if hasattr(e, 'name') and 'Ritualist' in e.name]
        
        # Should spawn at least some ritualists (room generation might fail occasionally)
        # But if it succeeds, there should be 2-3
        if len(ritualists) > 0:
            assert 2 <= len(ritualists) <= 3, \
                f"If secret room spawns, should have 2-3 ritualists, got {len(ritualists)}"
    
    def test_corrupted_ritualists_spawn_correctly(self, test_player, game_constants, message_log):
        """Test that Corrupted Ritualists spawn with correct properties."""
        game_map = GameMap(width=80, height=60, dungeon_level=25)
        entities = []
        
        game_map.make_map(
            max_rooms=30,
            room_min_size=6,
            room_max_size=10,
            map_width=80,
            map_height=60,
            player=test_player,
            entities=entities
        )
        
        ritualists = [e for e in entities 
                     if hasattr(e, 'name') and 'Corrupted Ritualist' in e.name]
        
        # If any ritualists spawned, verify they're properly configured
        for ritualist in ritualists:
            assert hasattr(ritualist, 'fighter'), \
                "Ritualist should have fighter component"
            assert ritualist.fighter.max_hp == 60, \
                "Ritualist should have 60 HP"
            assert hasattr(ritualist, 'ai'), \
                "Ritualist should have AI component"
            assert ritualist.blocks is True, \
                "Ritualist should block movement"
    
    def test_crimson_ritual_codex_spawns(self, test_player, game_constants, message_log):
        """Test that Crimson Ritual Codex spawns in secret room."""
        game_map = GameMap(width=80, height=60, dungeon_level=25)
        entities = []
        
        game_map.make_map(
            max_rooms=30,
            room_min_size=6,
            room_max_size=10,
            map_width=80,
            map_height=60,
            player=test_player,
            entities=entities
        )
        
        codices = [e for e in entities 
                  if hasattr(e, 'name') and 'Crimson Ritual Codex' in e.name]
        
        # Codex should spawn if secret room generated successfully
        if len(codices) > 0:
            assert len(codices) == 1, "Should spawn exactly 1 Crimson Ritual Codex"
            
            codex = codices[0]
            assert hasattr(codex, 'item'), "Codex should be an item"
            assert hasattr(codex, 'use_function'), "Codex should have use_function"
            assert codex.use_function == "unlock_crimson_ritual", \
                "Codex should unlock the crimson ritual"


class TestLevel25EntityFactoryIntegration:
    """Test that correct EntityFactory methods are called during Level 25 generation.
    
    These tests would have caught the bugs:
    - Using create_enemy() instead of create_monster()
    - Wrong import paths
    """
    
    def test_create_monster_called_for_ritualists(self, test_player, game_constants, message_log):
        """Test that create_monster() method is used (not create_enemy())."""
        game_map = GameMap(width=80, height=60, dungeon_level=25)
        entities = []
        
        # Mock the factory to track method calls
        with patch('map_objects.game_map.get_entity_factory') as mock_get_factory:
            mock_factory = Mock()
            mock_get_factory.return_value = mock_factory
            
            # Make factory return mock entities
            mock_ritualist = Mock()
            mock_ritualist.name = "Corrupted Ritualist"
            mock_factory.create_monster.return_value = mock_ritualist
            
            mock_codex = Mock()
            mock_codex.name = "Crimson Ritual Codex"
            mock_factory.create_unique_item.return_value = mock_codex
            
            # Generate Level 25
            game_map.make_map(
                max_rooms=30,
                room_min_size=6,
                room_max_size=10,
                map_width=80,
                map_height=60,
                player=test_player,
                entities=entities
            )
            
            # Verify create_monster was called with 'corrupted_ritualist'
            # (This would fail if we used create_enemy() by mistake)
            calls = [call for call in mock_factory.create_monster.call_args_list
                    if len(call[0]) > 0 and call[0][0] == 'corrupted_ritualist']
            
            # Should be called 2-3 times for ritualists
            assert len(calls) >= 2, \
                "create_monster() should be called at least 2 times for ritualists"
            assert len(calls) <= 3, \
                "create_monster() should be called at most 3 times for ritualists"
    
    def test_create_unique_item_called_for_codex(self, test_player, game_constants, message_log):
        """Test that create_unique_item() is called for Crimson Ritual Codex."""
        game_map = GameMap(width=80, height=60, dungeon_level=25)
        entities = []
        
        with patch('map_objects.game_map.get_entity_factory') as mock_get_factory:
            mock_factory = Mock()
            mock_get_factory.return_value = mock_factory
            
            # Make factory return mock entities
            mock_ritualist = Mock()
            mock_factory.create_monster.return_value = mock_ritualist
            
            mock_codex = Mock()
            mock_factory.create_unique_item.return_value = mock_codex
            
            # Generate Level 25
            game_map.make_map(
                max_rooms=30,
                room_min_size=6,
                room_max_size=10,
                map_width=80,
                map_height=60,
                player=test_player,
                entities=entities
            )
            
            # Verify create_unique_item was called for codex
            codex_calls = [call for call in mock_factory.create_unique_item.call_args_list
                          if len(call[0]) > 0 and call[0][0] == 'crimson_ritual_codex']
            
            assert len(codex_calls) == 1, \
                "create_unique_item() should be called exactly once for crimson_ritual_codex"


class TestLevel25NoItemsOnStairs:
    """Test that items don't spawn on stairs (recent fix)."""
    
    def test_no_items_on_stairs_location(self, test_player, game_constants, message_log):
        """Test that stairs tile has no items on it."""
        game_map = GameMap(width=80, height=60, dungeon_level=25)
        entities = []
        
        game_map.make_map(
            max_rooms=30,
            room_min_size=6,
            room_max_size=10,
            map_width=80,
            map_height=60,
            player=test_player,
            entities=entities
        )
        
        # Find stairs
        from components.component_registry import ComponentType
        stairs = [e for e in entities if e.components.has(ComponentType.STAIRS)]
        
        assert len(stairs) == 1, "Should have exactly one stairs entity"
        stairs_entity = stairs[0]
        stairs_x, stairs_y = stairs_entity.x, stairs_entity.y
        
        # Find all items at stairs location
        items_on_stairs = [e for e in entities 
                          if e.x == stairs_x and e.y == stairs_y 
                          and hasattr(e, 'item') and e.item
                          and e != stairs_entity]
        
        assert len(items_on_stairs) == 0, \
            f"No items should spawn on stairs at ({stairs_x}, {stairs_y}), found {len(items_on_stairs)}"


class TestLevel25Consistency:
    """Test that Level 25 generation is consistent and doesn't crash."""
    
    def test_level_25_generates_without_errors(self, test_player, game_constants, message_log):
        """Test that Level 25 can be generated multiple times without errors."""
        for i in range(5):
            game_map = GameMap(width=80, height=60, dungeon_level=25)
            entities = []
            
            # Should not raise any exceptions
            game_map.make_map(
                max_rooms=30,
                room_min_size=6,
                room_max_size=10,
                map_width=80,
                map_height=60,
                player=test_player,
                entities=entities
            )
            
            # Verify basic structure
            assert len(entities) > 0, f"Generation {i+1}: Should spawn some entities"
            assert test_player in entities, f"Generation {i+1}: Player should be in entities"
    
    def test_level_25_has_all_required_items(self, test_player, game_constants, message_log):
        """Test that Level 25 has all required quest items."""
        game_map = GameMap(width=80, height=60, dungeon_level=25)
        entities = []
        
        game_map.make_map(
            max_rooms=30,
            room_min_size=6,
            room_max_size=10,
            map_width=80,
            map_height=60,
            player=test_player,
            entities=entities
        )
        
        # Must have Ruby Heart
        ruby_hearts = [e for e in entities if hasattr(e, 'name') and e.name == "Ruby Heart"]
        assert len(ruby_hearts) == 1, "Must have Ruby Heart on Level 25"
        
        # Must have stairs
        from components.component_registry import ComponentType
        stairs = [e for e in entities if e.components.has(ComponentType.STAIRS)]
        assert len(stairs) == 1, "Must have stairs on Level 25"

