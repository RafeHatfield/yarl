"""Tests for centralized game settings configuration."""

import os
import pytest
from pathlib import Path

from config.settings import (
    GameSettings,
    initialize_settings,
    get_settings,
    reset_settings,
)


class TestGameSettingsDefaults:
    """Test default GameSettings values."""
    
    def test_default_settings_created(self):
        """Test that GameSettings can be created with defaults."""
        settings = GameSettings()
        assert settings is not None
    
    def test_default_testing_mode_disabled(self):
        """Test testing mode is disabled by default."""
        settings = GameSettings()
        assert settings.testing_mode is False
    
    def test_default_debug_mode_disabled(self):
        """Test debug mode is disabled by default."""
        settings = GameSettings()
        assert settings.debug_mode is False
    
    def test_default_log_level_warning(self):
        """Test default log level is WARNING."""
        settings = GameSettings()
        assert settings.log_level == "WARNING"
    
    def test_default_debug_logging_disabled(self):
        """Test debug logging disabled by default."""
        settings = GameSettings()
        assert settings.debug_logging is False
    
    def test_default_max_dungeon_level(self):
        """Test default max dungeon level is 25."""
        settings = GameSettings()
        assert settings.max_dungeon_level == 25
    
    def test_default_save_path(self):
        """Test default save path is 'saves'."""
        settings = GameSettings()
        assert settings.save_game_path == "saves"


class TestGameSettingsForTesting:
    """Test GameSettings.for_testing() method."""
    
    def test_for_testing_returns_settings(self):
        """Test for_testing() returns GameSettings instance."""
        settings = GameSettings.for_testing()
        assert isinstance(settings, GameSettings)
    
    def test_for_testing_enables_testing_mode(self):
        """Test for_testing() enables testing mode."""
        settings = GameSettings.for_testing()
        assert settings.testing_mode is True
    
    def test_for_testing_disables_debug_mode(self):
        """Test for_testing() disables debug mode."""
        settings = GameSettings.for_testing()
        assert settings.debug_mode is False
    
    def test_for_testing_shorter_dungeon(self):
        """Test for_testing() uses shorter dungeon."""
        settings = GameSettings.for_testing()
        assert settings.max_dungeon_level == 3
    
    def test_for_testing_separate_save_path(self):
        """Test for_testing() uses separate save path."""
        settings = GameSettings.for_testing()
        assert "tests" in settings.save_game_path


class TestGameSettingsForDebugging:
    """Test GameSettings.for_debugging() method."""
    
    def test_for_debugging_returns_settings(self):
        """Test for_debugging() returns GameSettings instance."""
        settings = GameSettings.for_debugging()
        assert isinstance(settings, GameSettings)
    
    def test_for_debugging_enables_debug_mode(self):
        """Test for_debugging() enables debug mode."""
        settings = GameSettings.for_debugging()
        assert settings.debug_mode is True
    
    def test_for_debugging_enables_all_debug_flags(self):
        """Test for_debugging() enables all debug features."""
        settings = GameSettings.for_debugging()
        assert settings.debug_logging is True
        assert settings.monster_ai_debug is True
        assert settings.resistance_debug is True
        assert settings.show_fps is True
        assert settings.show_debug_menu is True
    
    def test_for_debugging_debug_log_level(self):
        """Test for_debugging() sets DEBUG log level."""
        settings = GameSettings.for_debugging()
        assert settings.log_level == "DEBUG"


class TestGameSettingsFromEnvironment:
    """Test GameSettings.from_environment() method."""
    
    def test_from_environment_default_values(self, monkeypatch):
        """Test from_environment uses defaults when no env vars set."""
        # Clear all RLIKE_ env vars
        for key in list(os.environ.keys()):
            if key.startswith("RLIKE_"):
                monkeypatch.delenv(key, raising=False)
        
        settings = GameSettings.from_environment()
        assert settings.testing_mode is False
        assert settings.log_level == "WARNING"
    
    def test_from_environment_testing_mode(self, monkeypatch):
        """Test RLIKE_TESTING environment variable."""
        monkeypatch.setenv("RLIKE_TESTING", "1")
        settings = GameSettings.from_environment()
        assert settings.testing_mode is True
    
    def test_from_environment_debug_mode(self, monkeypatch):
        """Test RLIKE_DEBUG environment variable."""
        monkeypatch.setenv("RLIKE_DEBUG", "1")
        settings = GameSettings.from_environment()
        assert settings.debug_mode is True
    
    def test_from_environment_log_level(self, monkeypatch):
        """Test RLIKE_LOG_LEVEL environment variable."""
        monkeypatch.setenv("RLIKE_LOG_LEVEL", "DEBUG")
        settings = GameSettings.from_environment()
        assert settings.log_level == "DEBUG"
    
    def test_from_environment_boolean_true_variants(self, monkeypatch):
        """Test various true representations for boolean env vars."""
        for true_val in ["1", "true", "True", "yes", "YES", "on", "ON"]:
            monkeypatch.setenv("RLIKE_DEBUG_LOGGING", true_val)
            settings = GameSettings.from_environment()
            assert settings.debug_logging is True
    
    def test_from_environment_boolean_false_default(self, monkeypatch):
        """Test false values default to False."""
        monkeypatch.setenv("RLIKE_DEBUG_LOGGING", "0")
        settings = GameSettings.from_environment()
        assert settings.debug_logging is False
    
    def test_from_environment_integer_values(self, monkeypatch):
        """Test integer environment variables."""
        monkeypatch.setenv("RLIKE_MAX_DUNGEON_LEVEL", "50")
        settings = GameSettings.from_environment()
        assert settings.max_dungeon_level == 50
    
    def test_from_environment_integer_invalid_defaults(self, monkeypatch):
        """Test invalid integer env vars use default."""
        monkeypatch.setenv("RLIKE_MAX_DUNGEON_LEVEL", "not_a_number")
        settings = GameSettings.from_environment()
        assert settings.max_dungeon_level == 25
    
    def test_from_environment_string_values(self, monkeypatch):
        """Test string environment variables."""
        monkeypatch.setenv("RLIKE_SAVE_GAME_PATH", "custom/saves")
        settings = GameSettings.from_environment()
        assert settings.save_game_path == "custom/saves"


class TestGameSettingsMethods:
    """Test GameSettings methods."""
    
    def test_get_save_directory_creates_path(self, tmp_path, monkeypatch):
        """Test get_save_directory creates the path if needed."""
        monkeypatch.chdir(tmp_path)
        settings = GameSettings(save_game_path="test_saves")
        save_dir = settings.get_save_directory()
        assert save_dir.exists()
        assert save_dir.is_dir()
    
    def test_get_save_directory_returns_path_object(self):
        """Test get_save_directory returns Path object."""
        settings = GameSettings()
        save_dir = settings.get_save_directory()
        assert isinstance(save_dir, Path)
    
    def test_get_save_directory_uses_configured_path(self):
        """Test get_save_directory uses configured path."""
        settings = GameSettings(save_game_path="my_custom_saves")
        save_dir = settings.get_save_directory()
        assert "my_custom_saves" in str(save_dir)


class TestGlobalSettingsManagement:
    """Test global settings initialization and access."""
    
    def teardown_method(self):
        """Clean up after each test."""
        reset_settings()
    
    def test_initialize_settings_with_none(self):
        """Test initialize_settings with None loads from environment."""
        reset_settings()
        initialize_settings(None)
        settings = get_settings()
        assert isinstance(settings, GameSettings)
    
    def test_initialize_settings_with_instance(self):
        """Test initialize_settings with GameSettings instance."""
        reset_settings()
        custom_settings = GameSettings.for_testing()
        initialize_settings(custom_settings)
        settings = get_settings()
        assert settings is custom_settings
    
    def test_get_settings_raises_when_not_initialized(self):
        """Test get_settings raises when not initialized."""
        reset_settings()
        with pytest.raises(RuntimeError, match="Settings not initialized"):
            get_settings()
    
    def test_get_settings_returns_same_instance(self):
        """Test get_settings returns the same instance."""
        reset_settings()
        initialize_settings(GameSettings.for_testing())
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2
    
    def test_reset_settings(self):
        """Test reset_settings clears global state."""
        initialize_settings(GameSettings())
        reset_settings()
        with pytest.raises(RuntimeError):
            get_settings()


class TestSettingsIntegration:
    """Integration tests for settings system."""
    
    def teardown_method(self):
        """Clean up after each test."""
        reset_settings()
    
    def test_full_workflow_testing(self):
        """Test full workflow with testing settings."""
        reset_settings()
        initialize_settings(GameSettings.for_testing())
        settings = get_settings()
        assert settings.testing_mode is True
        assert settings.max_dungeon_level == 3
    
    def test_full_workflow_debugging(self):
        """Test full workflow with debugging settings."""
        reset_settings()
        initialize_settings(GameSettings.for_debugging())
        settings = get_settings()
        assert settings.debug_mode is True
        assert settings.debug_logging is True
    
    def test_settings_copy_independence(self):
        """Test that modifying one settings doesn't affect others."""
        settings1 = GameSettings.for_testing()
        settings2 = GameSettings()
        settings1.max_dungeon_level = 99
        assert settings2.max_dungeon_level == 25

