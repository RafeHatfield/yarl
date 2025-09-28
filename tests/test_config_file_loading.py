"""Tests for configuration file loading functionality.

This module tests the JSON/YAML configuration file loading and saving
capabilities added to the GameConstants class.
"""

import unittest
import tempfile
import os
import json
from unittest.mock import patch

from config.game_constants import GameConstants


class TestConfigFileLoading(unittest.TestCase):
    """Test configuration file loading and saving."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.json_config_path = os.path.join(self.temp_dir, "test_config.json")
        self.yaml_config_path = os.path.join(self.temp_dir, "test_config.yaml")
        
        # Sample configuration data
        self.sample_config = {
            "performance": {
                "TARGET_FPS": 120,
                "SPATIAL_GRID_SIZE": 16
            },
            "combat": {
                "DEFAULT_HP": 50,
                "DEFAULT_POWER": 5
            },
            "rendering": {
                "DEFAULT_SCREEN_WIDTH": 100,
                "DEFAULT_SCREEN_HEIGHT": 60
            }
        }
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temporary files
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_load_from_file_default(self):
        """Test loading default configuration when no file is provided."""
        config = GameConstants.load_from_file()
        
        self.assertIsInstance(config, GameConstants)
        self.assertEqual(config.performance.TARGET_FPS, 60)  # Default value
        self.assertEqual(config.combat.DEFAULT_HP, 1)        # Default value
    
    def test_load_from_json_file(self):
        """Test loading configuration from JSON file."""
        # Create JSON config file
        with open(self.json_config_path, 'w') as f:
            json.dump(self.sample_config, f)
        
        # Load configuration
        config = GameConstants.load_from_file(self.json_config_path)
        
        # Verify loaded values
        self.assertEqual(config.performance.TARGET_FPS, 120)
        self.assertEqual(config.performance.SPATIAL_GRID_SIZE, 16)
        self.assertEqual(config.combat.DEFAULT_HP, 50)
        self.assertEqual(config.combat.DEFAULT_POWER, 5)
        self.assertEqual(config.rendering.DEFAULT_SCREEN_WIDTH, 100)
        self.assertEqual(config.rendering.DEFAULT_SCREEN_HEIGHT, 60)
    
    @patch('config.game_constants.YAML_AVAILABLE', True)
    @patch('config.game_constants.yaml')
    def test_load_from_yaml_file(self, mock_yaml):
        """Test loading configuration from YAML file."""
        # Create YAML config file
        with open(self.yaml_config_path, 'w') as f:
            f.write("# test yaml file")
        
        # Mock YAML loading
        mock_yaml.safe_load.return_value = self.sample_config
        
        # Load configuration
        config = GameConstants.load_from_file(self.yaml_config_path)
        
        # Verify YAML was called
        mock_yaml.safe_load.assert_called_once()
        
        # Verify loaded values
        self.assertEqual(config.performance.TARGET_FPS, 120)
        self.assertEqual(config.combat.DEFAULT_HP, 50)
    
    def test_load_from_nonexistent_file(self):
        """Test loading from non-existent file raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            GameConstants.load_from_file("/nonexistent/path/config.json")
    
    def test_load_from_invalid_json(self):
        """Test loading invalid JSON raises ValueError."""
        # Create invalid JSON file
        with open(self.json_config_path, 'w') as f:
            f.write("{ invalid json }")
        
        with self.assertRaises(ValueError) as context:
            GameConstants.load_from_file(self.json_config_path)
        
        self.assertIn("Invalid configuration file format", str(context.exception))
    
    def test_load_from_unsupported_format(self):
        """Test loading unsupported file format raises ValueError."""
        unsupported_path = os.path.join(self.temp_dir, "config.txt")
        with open(unsupported_path, 'w') as f:
            f.write("some content")
        
        with self.assertRaises(ValueError) as context:
            GameConstants.load_from_file(unsupported_path)
        
        self.assertIn("Unsupported configuration file format", str(context.exception))
    
    @patch('config.game_constants.YAML_AVAILABLE', False)
    def test_load_yaml_without_support(self):
        """Test loading YAML without PyYAML raises ValueError."""
        # Create YAML config file
        with open(self.yaml_config_path, 'w') as f:
            f.write("# test yaml file")
        
        with self.assertRaises(ValueError) as context:
            GameConstants.load_from_file(self.yaml_config_path)
        
        self.assertIn("YAML support not available", str(context.exception))
    
    def test_save_to_json_file(self):
        """Test saving configuration to JSON file."""
        config = GameConstants()
        config.performance.TARGET_FPS = 120
        config.combat.DEFAULT_HP = 50
        
        # Save to JSON
        config.save_to_file(self.json_config_path, 'json')
        
        # Verify file was created and contains correct data
        self.assertTrue(os.path.exists(self.json_config_path))
        
        with open(self.json_config_path, 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data['performance']['TARGET_FPS'], 120)
        self.assertEqual(saved_data['combat']['DEFAULT_HP'], 50)
    
    @patch('config.game_constants.YAML_AVAILABLE', True)
    @patch('config.game_constants.yaml')
    def test_save_to_yaml_file(self, mock_yaml):
        """Test saving configuration to YAML file."""
        config = GameConstants()
        
        # Save to YAML
        config.save_to_file(self.yaml_config_path, 'yaml')
        
        # Verify YAML dump was called
        mock_yaml.dump.assert_called_once()
    
    def test_save_unsupported_format(self):
        """Test saving with unsupported format raises ValueError."""
        config = GameConstants()
        
        with self.assertRaises(ValueError) as context:
            config.save_to_file(self.json_config_path, 'xml')
        
        self.assertIn("Unsupported format", str(context.exception))
    
    @patch('config.game_constants.YAML_AVAILABLE', False)
    def test_save_yaml_without_support(self):
        """Test saving YAML without PyYAML raises ValueError."""
        config = GameConstants()
        
        with self.assertRaises(ValueError) as context:
            config.save_to_file(self.yaml_config_path, 'yaml')
        
        self.assertIn("YAML support not available", str(context.exception))
    
    def test_to_dict(self):
        """Test converting configuration to dictionary."""
        config = GameConstants()
        config_dict = config.to_dict()
        
        # Verify structure
        self.assertIn('pathfinding', config_dict)
        self.assertIn('performance', config_dict)
        self.assertIn('combat', config_dict)
        self.assertIn('inventory', config_dict)
        self.assertIn('rendering', config_dict)
        self.assertIn('gameplay', config_dict)
        
        # Verify values
        self.assertEqual(config_dict['performance']['TARGET_FPS'], 60)
        self.assertEqual(config_dict['combat']['DEFAULT_HP'], 1)
    
    def test_partial_config_loading(self):
        """Test loading partial configuration (only some sections)."""
        partial_config = {
            "performance": {
                "TARGET_FPS": 90
            }
            # Missing other sections
        }
        
        # Create JSON config file
        with open(self.json_config_path, 'w') as f:
            json.dump(partial_config, f)
        
        # Load configuration
        config = GameConstants.load_from_file(self.json_config_path)
        
        # Verify loaded section
        self.assertEqual(config.performance.TARGET_FPS, 90)
        
        # Verify other sections use defaults
        self.assertEqual(config.combat.DEFAULT_HP, 1)  # Default value
        self.assertEqual(config.rendering.DEFAULT_SCREEN_WIDTH, 80)  # Default value
    
    def test_invalid_config_values_ignored(self):
        """Test that invalid configuration values are ignored."""
        invalid_config = {
            "performance": {
                "TARGET_FPS": 120,
                "INVALID_FIELD": "should_be_ignored"
            },
            "invalid_section": {
                "some_field": "ignored"
            }
        }
        
        # Create JSON config file
        with open(self.json_config_path, 'w') as f:
            json.dump(invalid_config, f)
        
        # Load configuration (should not raise error)
        config = GameConstants.load_from_file(self.json_config_path)
        
        # Verify valid values were loaded
        self.assertEqual(config.performance.TARGET_FPS, 120)
        
        # Verify invalid field was ignored (no attribute created)
        self.assertFalse(hasattr(config.performance, 'INVALID_FIELD'))
    
    def test_roundtrip_json_config(self):
        """Test saving and loading configuration maintains values."""
        # Create config with custom values
        original_config = GameConstants()
        original_config.performance.TARGET_FPS = 144
        original_config.combat.DEFAULT_HP = 75
        original_config.rendering.DEFAULT_SCREEN_WIDTH = 120
        
        # Save to file
        original_config.save_to_file(self.json_config_path, 'json')
        
        # Load from file
        loaded_config = GameConstants.load_from_file(self.json_config_path)
        
        # Verify values match
        self.assertEqual(loaded_config.performance.TARGET_FPS, 144)
        self.assertEqual(loaded_config.combat.DEFAULT_HP, 75)
        self.assertEqual(loaded_config.rendering.DEFAULT_SCREEN_WIDTH, 120)


if __name__ == '__main__':
    unittest.main()
