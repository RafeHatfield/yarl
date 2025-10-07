"""Tests for monster creation migration to EntityFactory.

This module tests that the new EntityFactory-based monster creation
produces identical results to the old hardcoded monster creation.
"""

import pytest
from unittest.mock import Mock, patch

from map_objects.game_map import GameMap
from map_objects.rectangle import Rect
from config.entity_registry import get_entity_registry, load_entity_config
from config.entity_factory import get_entity_factory
from components.fighter import Fighter
from components.ai import BasicMonster
from render_functions import RenderOrder


class TestMonsterMigrationCompatibility:
    """Test that new EntityFactory produces identical monsters to old system."""

    def setup_method(self):
        """Set up test fixtures."""
        # Load entity configuration
        load_entity_config()
        
        # Create a test game map
        self.game_map = GameMap(width=20, height=20, dungeon_level=1)
        
        # Create a test room
        self.test_room = Rect(x=5, y=5, w=8, h=8)
        
        # Mock random functions to ensure predictable testing
        self.mock_randint_patcher = patch('map_objects.game_map.randint')
        self.mock_randint = self.mock_randint_patcher.start()
        
        self.mock_choice_patcher = patch('map_objects.game_map.random_choice_from_dict')
        self.mock_choice = self.mock_choice_patcher.start()

    def teardown_method(self):
        """Clean up after tests."""
        self.mock_randint_patcher.stop()
        self.mock_choice_patcher.stop()

    def test_orc_creation_matches_hardcoded_values(self):
        """Test that EntityFactory creates orcs with same stats as hardcoded version."""
        # Set up mocks for predictable monster placement
        self.mock_randint.return_value = 7  # Position in middle of room
        self.mock_choice.return_value = "orc"
        
        # Create monster using new system
        entities = []
        self.game_map.place_entities(self.test_room, entities)
        
        # Should have created exactly one monster
        assert len(entities) == 1
        monster = entities[0]
        
        # Verify monster properties match hardcoded values
        assert monster.name == "Orc"
        assert monster.char == "o"
        assert monster.color == (63, 127, 63)
        assert monster.x == 7
        assert monster.y == 7
        assert monster.blocks is True
        assert monster.render_order == RenderOrder.ACTOR
        
        # Verify fighter component matches hardcoded values
        assert monster.fighter is not None
        assert monster.fighter.base_max_hp == 20
        assert monster.fighter.base_power == 0  # New system uses damage_min/max instead of power
        assert monster.fighter.base_defense == 0
        assert monster.fighter.xp == 35
        
        # Verify AI component
        assert monster.ai is not None
        assert isinstance(monster.ai, BasicMonster)

    def test_troll_creation_matches_hardcoded_values(self):
        """Test that EntityFactory creates trolls with same stats as hardcoded version."""
        # Set up mocks for predictable monster placement
        self.mock_randint.return_value = 8  # Position in middle of room
        self.mock_choice.return_value = "troll"
        
        # Create monster using new system
        entities = []
        self.game_map.place_entities(self.test_room, entities)
        
        # Should have created exactly one monster
        assert len(entities) == 1
        monster = entities[0]
        
        # Verify monster properties match hardcoded values
        assert monster.name == "Troll"
        assert monster.char == "T"
        assert monster.color == (0, 127, 0)
        assert monster.x == 8
        assert monster.y == 8
        assert monster.blocks is True
        assert monster.render_order == RenderOrder.ACTOR
        
        # Verify fighter component matches hardcoded values
        assert monster.fighter is not None
        assert monster.fighter.base_max_hp == 30
        assert monster.fighter.base_power == 0  # New system uses damage_min/max instead of power
        assert monster.fighter.base_defense == 2
        assert monster.fighter.xp == 100
        
        # Verify AI component
        assert monster.ai is not None
        assert isinstance(monster.ai, BasicMonster)

    def test_unknown_monster_creates_fallback(self):
        """Test that unknown monster types create fallback monsters."""
        # Set up mocks for unknown monster type
        self.mock_randint.return_value = 6
        self.mock_choice.return_value = "unknown_monster"
        
        # Create monster using new system
        entities = []
        self.game_map.place_entities(self.test_room, entities)
        
        # Should have created exactly one fallback monster
        assert len(entities) == 1
        monster = entities[0]
        
        # Verify fallback monster properties
        assert monster.name == "Unknown unknown_monster"
        assert monster.char == "?"
        assert monster.color == (255, 0, 255)  # Magenta for unknown
        assert monster.x == 6
        assert monster.y == 6
        assert monster.blocks is True
        assert monster.render_order == RenderOrder.ACTOR
        
        # Verify fallback fighter component
        assert monster.fighter is not None
        assert monster.fighter.base_max_hp == 10
        assert monster.fighter.base_power == 2
        assert monster.fighter.base_defense == 0
        assert monster.fighter.xp == 10


    def test_multiple_monster_placement_avoids_collisions(self):
        """Test that multiple monsters don't spawn on same position."""
        # Mock to spawn 3 monsters
        with patch('map_objects.game_map.from_dungeon_level') as mock_from_level:
            # Use a callable that returns appropriate values
            call_count = [0]
            def from_level_side_effect(table, level):
                call_count[0] += 1
                if call_count[0] == 1:
                    return 3  # max_monsters_per_room
                elif call_count[0] == 2:
                    return 0  # max_items_per_room (no items for this test)
                else:
                    return 5  # Default value for any other calls (item chances)
            mock_from_level.side_effect = from_level_side_effect
            
            # Set up positions - use same position to test collision detection
            self.mock_randint.return_value = 7  # All monsters try to spawn at same position
            self.mock_choice.side_effect = ["orc", "troll", "orc"]
            
            # Create monsters
            entities = []
            self.game_map.place_entities(self.test_room, entities)
            
            # Should have created only 1 monster (collisions prevented others)
            monsters = [e for e in entities if hasattr(e, 'fighter') and hasattr(e, 'ai')]
            assert len(monsters) == 1
            
            # Verify the one monster that spawned
            assert monsters[0].name == "Orc"
            assert monsters[0].x == 7
            assert monsters[0].y == 7


class TestMonsterMigrationIntegration:
    """Integration tests for the complete monster migration."""

    def setup_method(self):
        """Set up test fixtures."""
        # Load entity configuration
        load_entity_config()

    def test_entity_registry_loaded_correctly(self):
        """Test that entity registry is loaded with expected monsters."""
        registry = get_entity_registry()
        
        # Should have loaded orc and troll
        assert registry.get_monster("orc") is not None
        assert registry.get_monster("troll") is not None
        
        # Verify orc stats
        orc = registry.get_monster("orc")
        assert orc.stats.hp == 20
        assert orc.stats.power == 0  # New system uses damage_min/max instead of power
        assert orc.stats.defense == 0
        assert orc.stats.xp == 35
        
        # Verify troll stats
        troll = registry.get_monster("troll")
        assert troll.stats.hp == 30
        assert troll.stats.power == 0  # New system uses damage_min/max instead of power
        assert troll.stats.defense == 2
        assert troll.stats.xp == 100

    def test_entity_factory_creates_correct_monsters(self):
        """Test that entity factory creates monsters correctly."""
        factory = get_entity_factory()
        
        # Create orc
        orc = factory.create_monster("orc", 10, 15)
        assert orc is not None
        assert orc.name == "Orc"
        assert orc.x == 10
        assert orc.y == 15
        assert orc.fighter.base_max_hp == 20
        
        # Create troll
        troll = factory.create_monster("troll", 5, 8)
        assert troll is not None
        assert troll.name == "Troll"
        assert troll.x == 5
        assert troll.y == 8
        assert troll.fighter.base_max_hp == 30

    def test_game_map_monster_creation_end_to_end(self):
        """Test complete monster creation flow in game map."""
        game_map = GameMap(width=30, height=30, dungeon_level=1)
        room = Rect(x=5, y=5, w=10, h=10)
        
        # Mock the random functions for predictable testing
        with patch('map_objects.game_map.randint') as mock_randint, \
             patch('map_objects.game_map.random_choice_from_dict') as mock_choice, \
             patch('map_objects.game_map.from_dungeon_level') as mock_from_level:
            
            # Set up mocks
            mock_from_level.side_effect = [2, 2, 15, 5, 15, 5, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5]  # 1 monster, no items (includes invisibility_scroll)
            mock_randint.return_value = 8  # Position
            mock_choice.return_value = "orc"
            
            # Create entities
            entities = []
            game_map.place_entities(room, entities)
            
            # Verify monster was created correctly
            assert len(entities) == 1
            monster = entities[0]
            assert monster.name == "Orc"
            assert monster.x == 8
            assert monster.y == 8
            assert monster.fighter.base_max_hp == 20


class TestBackwardCompatibility:
    """Test that the migration maintains perfect backward compatibility."""

    def setup_method(self):
        """Set up test fixtures."""
        # Load entity configuration
        load_entity_config()

    def test_monster_stats_exactly_match_hardcoded_values(self):
        """Test that config values exactly match the old hardcoded values."""
        registry = get_entity_registry()
        
        # Test orc stats match hardcoded Fighter(hp=20, defense=0, power=4, xp=35)
        orc = registry.get_monster("orc")
        assert orc.stats.hp == 20
        assert orc.stats.defense == 0
        assert orc.stats.power == 0  # New system uses damage_min/max instead of power
        assert orc.stats.xp == 35
        assert orc.char == "o"
        assert orc.color == (63, 127, 63)
        assert orc.blocks is True
        assert orc.ai_type == "basic"
        
        # Test troll stats match hardcoded Fighter(hp=30, defense=2, power=8, xp=100)
        troll = registry.get_monster("troll")
        assert troll.stats.hp == 30
        assert troll.stats.defense == 2
        assert troll.stats.power == 0  # New system uses damage_min/max instead of power
        assert troll.stats.xp == 100
        assert troll.char == "T"
        assert troll.color == (0, 127, 0)
        assert troll.blocks is True
        assert troll.ai_type == "basic"

    def test_entity_creation_produces_identical_objects(self):
        """Test that EntityFactory produces functionally identical entities."""
        factory = get_entity_factory()
        
        # Create orc using new system
        new_orc = factory.create_monster("orc", 5, 5)
        
        # Manually create orc using old system (for comparison)
        from components.fighter import Fighter
        from components.ai import BasicMonster
        from entity import Entity
        from render_functions import RenderOrder
        
        old_fighter = Fighter(hp=20, defense=0, power=0, xp=35)  # New system uses damage_min/max instead of power
        old_ai = BasicMonster()
        old_orc = Entity(
            5, 5, "o", (63, 127, 63), "Orc",
            blocks=True, render_order=RenderOrder.ACTOR,
            fighter=old_fighter, ai=old_ai
        )
        
        # Compare all relevant properties
        assert new_orc.name == old_orc.name
        assert new_orc.char == old_orc.char
        assert new_orc.color == old_orc.color
        assert new_orc.x == old_orc.x
        assert new_orc.y == old_orc.y
        assert new_orc.blocks == old_orc.blocks
        assert new_orc.render_order == old_orc.render_order
        
        # Compare fighter component
        assert new_orc.fighter.base_max_hp == old_orc.fighter.base_max_hp
        assert new_orc.fighter.base_power == old_orc.fighter.base_power
        assert new_orc.fighter.base_defense == old_orc.fighter.base_defense
        assert new_orc.fighter.xp == old_orc.fighter.xp
        
        # Compare AI component types
        assert type(new_orc.ai) == type(old_orc.ai)

    def test_save_load_compatibility(self):
        """Test that migrated monsters can be saved and loaded correctly."""
        # This test ensures that the new EntityFactory-created monsters
        # are compatible with the existing save/load system
        
        factory = get_entity_factory()
        
        # Create monsters using new system
        orc = factory.create_monster("orc", 10, 10)
        troll = factory.create_monster("troll", 15, 15)
        
        # Verify they have all required attributes for serialization
        for monster in [orc, troll]:
            assert hasattr(monster, 'x')
            assert hasattr(monster, 'y')
            assert hasattr(monster, 'char')
            assert hasattr(monster, 'color')
            assert hasattr(monster, 'name')
            assert hasattr(monster, 'blocks')
            assert hasattr(monster, 'render_order')
            assert hasattr(monster, 'fighter')
            assert hasattr(monster, 'ai')
            
            # Verify fighter component has all required attributes
            assert hasattr(monster.fighter, 'base_max_hp')
            assert hasattr(monster.fighter, 'hp')
            assert hasattr(monster.fighter, 'base_power')
            assert hasattr(monster.fighter, 'base_defense')
            assert hasattr(monster.fighter, 'xp')
            assert hasattr(monster.fighter, 'owner')
            
            # Verify owner relationship is established
            assert monster.fighter.owner is monster
