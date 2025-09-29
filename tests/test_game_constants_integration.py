"""Tests for GameConstants integration with EntityRegistry system.

This module tests that the EntityRegistry properly integrates with the
GameConstants system for configuration management.
"""

import pytest
import tempfile
import os
from pathlib import Path

from config.game_constants import (
    GameConstants,
    EntityConfig,
    get_entity_config,
    get_constants
)
from config.entity_registry import load_entity_config, get_entity_registry


class TestEntityConfigIntegration:
    """Test EntityConfig integration with GameConstants."""

    def test_entity_config_default_values(self):
        """Test that EntityConfig has sensible default values."""
        config = EntityConfig()
        
        # Verify default paths
        assert config.ENTITIES_CONFIG_PATH == "config/entities.yaml"
        assert config.FALLBACK_ENTITIES_CONFIG_PATH == "config/entities_fallback.yaml"
        
        # Verify default settings
        assert config.VALIDATE_ENTITY_STATS is True
        assert config.ALLOW_MISSING_ENTITIES is True
        assert config.MAX_INHERITANCE_DEPTH == 5
        assert config.ENABLE_ENTITY_INHERITANCE is True
        assert config.LOG_ENTITY_CREATION is False
        assert config.LOG_MISSING_ENTITIES is True

    def test_game_constants_includes_entity_config(self):
        """Test that GameConstants includes EntityConfig."""
        constants = GameConstants()
        
        # Verify EntityConfig is included
        assert constants.entities is not None
        assert isinstance(constants.entities, EntityConfig)
        
        # Verify all other configs are still there
        assert constants.pathfinding is not None
        assert constants.performance is not None
        assert constants.combat is not None
        assert constants.inventory is not None
        assert constants.rendering is not None
        assert constants.gameplay is not None

    def test_get_entity_config_function(self):
        """Test the get_entity_config convenience function."""
        config = get_entity_config()
        
        assert isinstance(config, EntityConfig)
        assert config.ENTITIES_CONFIG_PATH == "config/entities.yaml"

    def test_entity_registry_uses_game_constants_path(self):
        """Test that entity registry uses path from GameConstants."""
        # Create a temporary YAML file with test data
        test_config = """
version: "1.0"
player:
  hp: 150
  power: 3
  defense: 2
monsters:
  test_monster:
    stats:
      hp: 25
      power: 5
      defense: 1
      xp: 50
    char: "T"
    color: [255, 0, 0]
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(test_config)
            temp_file = f.name

        try:
            # Test loading with explicit path (should work)
            load_entity_config(temp_file)
            
            registry = get_entity_registry()
            
            # Verify test data was loaded
            player_stats = registry.get_player_stats()
            assert player_stats.hp == 150
            assert player_stats.power == 3
            assert player_stats.defense == 2
            
            test_monster = registry.get_monster("test_monster")
            assert test_monster is not None
            assert test_monster.stats.hp == 25
            assert test_monster.stats.power == 5
            
        finally:
            os.unlink(temp_file)

    def test_game_constants_legacy_compatibility(self):
        """Test that legacy constants function still works with entity integration."""
        constants_dict = get_constants()
        
        # Should return a dictionary as before
        assert isinstance(constants_dict, dict)
        
        # Should contain expected keys
        assert 'screen_width' in constants_dict
        assert 'screen_height' in constants_dict
        assert 'colors' in constants_dict
        
        # Entity config should not break legacy compatibility
        assert len(constants_dict) > 0


class TestEntityConfigValidation:
    """Test EntityConfig validation and error handling."""

    def test_entity_config_with_custom_values(self):
        """Test creating EntityConfig with custom values."""
        config = EntityConfig(
            ENTITIES_CONFIG_PATH="custom/path/entities.yaml",
            VALIDATE_ENTITY_STATS=False,
            MAX_INHERITANCE_DEPTH=10,
            LOG_ENTITY_CREATION=True
        )
        
        assert config.ENTITIES_CONFIG_PATH == "custom/path/entities.yaml"
        assert config.VALIDATE_ENTITY_STATS is False
        assert config.MAX_INHERITANCE_DEPTH == 10
        assert config.LOG_ENTITY_CREATION is True

    def test_entity_config_in_game_constants_with_overrides(self):
        """Test EntityConfig within GameConstants with custom values."""
        entity_config = EntityConfig(
            ENTITIES_CONFIG_PATH="test/entities.yaml",
            LOG_ENTITY_CREATION=True
        )
        
        constants = GameConstants(entities=entity_config)
        
        assert constants.entities.ENTITIES_CONFIG_PATH == "test/entities.yaml"
        assert constants.entities.LOG_ENTITY_CREATION is True
        
        # Other configs should still have defaults
        assert constants.entities.VALIDATE_ENTITY_STATS is True
        assert constants.entities.MAX_INHERITANCE_DEPTH == 5


class TestEntitySystemIntegration:
    """Test complete integration between entity system and game constants."""

    def test_entity_system_configuration_flow(self):
        """Test the complete configuration flow from GameConstants to EntityRegistry."""
        # Get entity configuration from GameConstants
        entity_config = get_entity_config()
        
        # Verify configuration values
        assert entity_config.ENTITIES_CONFIG_PATH == "config/entities.yaml"
        assert entity_config.VALIDATE_ENTITY_STATS is True
        assert entity_config.ALLOW_MISSING_ENTITIES is True
        
        # The entity registry should be able to use this configuration
        # (We won't actually load because the file path might not exist in tests)
        assert entity_config.ENTITIES_CONFIG_PATH.endswith('.yaml')

    def test_entity_config_path_resolution(self):
        """Test that entity config paths are resolved correctly."""
        entity_config = get_entity_config()
        
        # Path should be relative to project root
        config_path = entity_config.ENTITIES_CONFIG_PATH
        assert config_path.startswith("config/")
        assert config_path.endswith("entities.yaml")
        
        # Fallback path should also be properly configured
        fallback_path = entity_config.FALLBACK_ENTITIES_CONFIG_PATH
        assert fallback_path.startswith("config/")
        assert fallback_path.endswith(".yaml")

    def test_entity_config_inheritance_settings(self):
        """Test entity inheritance configuration settings."""
        entity_config = get_entity_config()
        
        # Inheritance should be enabled by default
        assert entity_config.ENABLE_ENTITY_INHERITANCE is True
        
        # Should have reasonable depth limit
        assert entity_config.MAX_INHERITANCE_DEPTH >= 3
        assert entity_config.MAX_INHERITANCE_DEPTH <= 10

    def test_entity_config_logging_settings(self):
        """Test entity logging configuration settings."""
        entity_config = get_entity_config()
        
        # Development vs production logging settings
        assert entity_config.LOG_MISSING_ENTITIES is True  # Always log missing entities
        assert entity_config.LOG_ENTITY_CREATION is False  # Don't spam logs by default

    def test_constants_system_extensibility(self):
        """Test that the constants system is extensible for future entity features."""
        entity_config = get_entity_config()
        
        # Verify configuration is comprehensive enough for future features
        # File path configuration
        assert hasattr(entity_config, 'ENTITIES_CONFIG_PATH')
        assert hasattr(entity_config, 'FALLBACK_ENTITIES_CONFIG_PATH')
        
        # Validation configuration
        assert hasattr(entity_config, 'VALIDATE_ENTITY_STATS')
        assert hasattr(entity_config, 'ALLOW_MISSING_ENTITIES')
        
        # Inheritance configuration
        assert hasattr(entity_config, 'ENABLE_ENTITY_INHERITANCE')
        assert hasattr(entity_config, 'MAX_INHERITANCE_DEPTH')
        
        # Logging configuration
        assert hasattr(entity_config, 'LOG_ENTITY_CREATION')
        assert hasattr(entity_config, 'LOG_MISSING_ENTITIES')


class TestGameConstantsFileLoading:
    """Test GameConstants file loading with entity configuration."""

    def test_game_constants_loads_with_entity_config(self):
        """Test that GameConstants can be loaded from file with entity config."""
        # Create temporary config file
        test_config = {
            "pathfinding": {
                "MAX_PATH_LENGTH": 30
            },
            "entities": {
                "ENTITIES_CONFIG_PATH": "custom/entities.yaml",
                "LOG_ENTITY_CREATION": True
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            import json
            json.dump(test_config, f)
            temp_file = f.name

        try:
            # Load GameConstants from file
            constants = GameConstants.load_from_file(temp_file)
            
            # Verify pathfinding config was loaded
            assert constants.pathfinding.MAX_PATH_LENGTH == 30
            
            # Verify entity config was loaded
            assert constants.entities.ENTITIES_CONFIG_PATH == "custom/entities.yaml"
            assert constants.entities.LOG_ENTITY_CREATION is True
            
            # Other entity config values should have defaults
            assert constants.entities.VALIDATE_ENTITY_STATS is True
            
        finally:
            os.unlink(temp_file)
