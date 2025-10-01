"""Tests for player creation migration to EntityFactory.

This module tests that the new EntityFactory-based player creation
produces identical results to the old hardcoded player creation.
"""

import pytest
from unittest.mock import Mock, patch

from loader_functions.initialize_new_game import get_game_variables, get_constants
from config.entity_registry import get_entity_registry, load_entity_config
from config.entity_factory import get_entity_factory
from components.fighter import Fighter
from components.inventory import Inventory
from components.level import Level
from components.equipment import Equipment


class TestPlayerMigrationCompatibility:
    """Test that new EntityFactory produces identical player to old system."""

    def setup_method(self):
        """Set up test fixtures."""
        # Load entity configuration
        load_entity_config()

    def test_player_stats_match_hardcoded_values(self):
        """Test that EntityFactory returns same player stats as hardcoded version."""
        factory = get_entity_factory()
        player_stats = factory.get_player_stats()
        
        # Verify stats match the current values (updated for d20 combat rebalancing)
        assert player_stats.hp == 60  # Rebalanced: was 30, now 60 for survivability
        assert player_stats.power == 0  # New system uses damage_min/max instead of power
        assert player_stats.defense == 1  # DEFAULT_DEFENSE + 1 = 0 + 1 = 1
        assert player_stats.xp == 0

    def test_player_creation_uses_config_stats(self):
        """Test that player creation now uses configuration stats."""
        constants = get_constants()
        
        # Mock the EntityFactory to return test stats
        with patch('loader_functions.initialize_new_game.get_entity_factory') as mock_get_factory:
            mock_factory = Mock()
            mock_stats = Mock()
            mock_stats.hp = 150  # Different from hardcoded 100
            mock_stats.power = 5  # Different from hardcoded 2
            mock_stats.defense = 3  # Different from hardcoded 1
            mock_factory.get_player_stats.return_value = mock_stats
            mock_get_factory.return_value = mock_factory
            
            # Create game variables
            player, entities, game_map, message_log, game_state = get_game_variables(constants)
            
            # Verify EntityFactory was called
            mock_get_factory.assert_called_once()
            mock_factory.get_player_stats.assert_called_once()
            
            # Verify player uses the mock stats
            assert player.fighter.base_max_hp == 150
            assert player.fighter.base_power == 5
            assert player.fighter.base_defense == 3

    def test_player_creation_end_to_end(self):
        """Test complete player creation flow with real configuration."""
        constants = get_constants()
        
        # Create game variables using real configuration
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        
        # Verify player was created correctly
        assert player is not None
        assert player.name == "Player"
        assert player.char == "@"
        assert player.color == (255, 255, 255)
        
        # Verify player stats match configuration (rebalanced for d20 combat)
        assert player.fighter.base_max_hp == 60  # Rebalanced: was 30, now 60
        assert player.fighter.base_power == 0
        assert player.fighter.base_defense == 1
        
        # Verify other components are still created
        assert player.inventory is not None
        assert player.level is not None
        assert player.equipment is not None
        assert player.pathfinding is not None
        
        # Verify player is in entities list
        assert player in entities
        assert entities[0] is player

    def test_player_components_unchanged(self):
        """Test that non-fighter components are unchanged by migration."""
        constants = get_constants()
        
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        
        # Verify inventory component
        assert isinstance(player.inventory, Inventory)
        assert player.inventory.capacity == 26  # DEFAULT_INVENTORY_CAPACITY
        
        # Verify level component
        assert isinstance(player.level, Level)
        assert player.level.level_up_base == 200  # DEFAULT_LEVEL_UP_BASE
        assert player.level.level_up_factor == 150  # DEFAULT_LEVEL_UP_FACTOR
        
        # Verify equipment component
        assert isinstance(player.equipment, Equipment)
        
        # Verify pathfinding component
        assert player.pathfinding is not None
        assert player.pathfinding.owner is player

    def test_player_starting_equipment_unchanged(self):
        """Test that player starting equipment creation is unchanged."""
        constants = get_constants()
        
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        
        # Verify player has starting dagger equipped
        assert player.equipment.main_hand is not None
        dagger = player.equipment.main_hand
        
        # Verify dagger properties
        assert dagger.name == "Dagger"
        assert dagger.equippable.power_bonus == 0  # Basic weapons no longer have magic bonuses
        assert dagger.equippable.damage_min == 3  # Updated to match current YAML
        assert dagger.equippable.damage_max == 5  # Updated to match current YAML
        
        # Verify dagger is in inventory
        assert dagger in player.inventory.items


class TestPlayerMigrationIntegration:
    """Integration tests for the complete player migration."""

    def setup_method(self):
        """Set up test fixtures."""
        # Load entity configuration
        load_entity_config()

    def test_entity_registry_has_player_stats(self):
        """Test that entity registry contains player configuration."""
        registry = get_entity_registry()
        
        player_stats = registry.get_player_stats()
        assert player_stats is not None
        assert player_stats.hp == 60  # Rebalanced for d20 combat
        assert player_stats.power == 0
        assert player_stats.defense == 1
        assert player_stats.xp == 0

    def test_entity_factory_provides_player_stats(self):
        """Test that entity factory provides player stats correctly."""
        factory = get_entity_factory()
        
        player_stats = factory.get_player_stats()
        assert player_stats is not None
        assert player_stats.hp == 60  # Rebalanced for d20 combat
        assert player_stats.power == 0
        assert player_stats.defense == 1
        assert player_stats.xp == 0

    def test_game_initialization_with_config(self):
        """Test that game initialization works with configuration system."""
        constants = get_constants()
        
        # This should not raise any exceptions
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        
        # Basic sanity checks
        assert player is not None
        assert len(entities) >= 1  # At least the player
        assert game_map is not None
        assert message_log is not None
        assert game_state is not None


class TestBackwardCompatibility:
    """Test that the migration maintains perfect backward compatibility."""

    def setup_method(self):
        """Set up test fixtures."""
        # Load entity configuration
        load_entity_config()

    def test_player_stats_exactly_match_hardcoded_values(self):
        """Test that config values match the rebalanced values for d20 combat."""
        factory = get_entity_factory()
        player_stats = factory.get_player_stats()
        
        # These values reflect the d20 combat rebalancing:
        # hp=60 (was 30, rebalanced for survivability)
        # defense=1, power=0 (new damage system)
        assert player_stats.hp == 60  # Rebalanced for d20 combat
        assert player_stats.defense == 1  # 0 + 1
        assert player_stats.power == 0   # New system uses damage_min/max instead of power
        assert player_stats.xp == 0

    def test_player_creation_produces_identical_fighter(self):
        """Test that new player creation produces correct Fighter with rebalanced stats."""
        constants = get_constants()
        
        # Create player using new system
        new_player, _, _, _, _ = get_game_variables(constants)
        
        # Compare with rebalanced system values
        # Rebalanced system: Fighter(hp=60, defense=1, power=0)
        assert new_player.fighter.base_max_hp == 60  # Rebalanced for d20 combat
        assert new_player.fighter.base_defense == 1
        assert new_player.fighter.base_power == 0
        
        # Verify current HP is set to base max HP
        # Note: Actual max_hp will be base_max_hp + CON modifier (60 + 2 = 62)
        assert new_player.fighter.hp == 60  # Current HP starts at base_max_hp

    def test_save_load_compatibility(self):
        """Test that migrated player can be saved and loaded correctly."""
        constants = get_constants()
        player, _, _, _, _ = get_game_variables(constants)
        
        # Verify player has all required attributes for serialization
        assert hasattr(player, 'x')
        assert hasattr(player, 'y')
        assert hasattr(player, 'char')
        assert hasattr(player, 'color')
        assert hasattr(player, 'name')
        assert hasattr(player, 'blocks')
        assert hasattr(player, 'render_order')
        assert hasattr(player, 'fighter')
        assert hasattr(player, 'inventory')
        assert hasattr(player, 'level')
        assert hasattr(player, 'equipment')
        assert hasattr(player, 'pathfinding')
        
        # Verify fighter component has all required attributes
        assert hasattr(player.fighter, 'base_max_hp')
        assert hasattr(player.fighter, 'hp')
        assert hasattr(player.fighter, 'base_power')
        assert hasattr(player.fighter, 'base_defense')
        assert hasattr(player.fighter, 'owner')
        
        # Verify owner relationship is established
        assert player.fighter.owner is player

    def test_game_variables_return_format_unchanged(self):
        """Test that get_game_variables still returns the same format."""
        constants = get_constants()
        
        result = get_game_variables(constants)
        
        # Should return a tuple of 5 elements
        assert isinstance(result, tuple)
        assert len(result) == 5
        
        player, entities, game_map, message_log, game_state = result
        
        # Verify types are as expected
        from entity import Entity
        from map_objects.game_map import GameMap
        from game_messages import MessageLog
        from game_states import GameStates
        
        assert isinstance(player, Entity)
        assert isinstance(entities, list)
        assert isinstance(game_map, GameMap)
        assert isinstance(message_log, MessageLog)
        # game_state is an enum value, so just check it's not None
        assert game_state is not None


class TestPlayerConfigurationFallback:
    """Test fallback behavior when player configuration is missing."""

    def test_fallback_when_no_player_config(self):
        """Test that system provides fallback when player config is missing."""
        # Create a factory with empty registry
        from config.entity_registry import EntityRegistry
        empty_registry = EntityRegistry()
        
        from config.entity_factory import EntityFactory
        factory = EntityFactory(empty_registry)
        
        # Should return fallback stats (old hardcoded values)
        player_stats = factory.get_player_stats()
        assert player_stats is not None
        assert player_stats.hp == 100  # Fallback to old default
        assert player_stats.power == 0
        assert player_stats.defense == 1
        assert player_stats.xp == 0
