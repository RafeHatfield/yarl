"""
Unit tests for the Level Template Registry system.

Tests loading, parsing, and managing level templates from YAML files.
"""

import os
import tempfile
import pytest
from unittest.mock import patch

from config.level_template_registry import (
    LevelTemplateRegistry,
    GuaranteedSpawn,
    LevelOverride,
    get_level_template_registry,
    load_level_templates
)


class TestGuaranteedSpawn:
    """Test GuaranteedSpawn dataclass."""
    
    def test_creation(self):
        """Test creating a GuaranteedSpawn."""
        spawn = GuaranteedSpawn(entity_type="slime", count_min=3, count_max=3)
        assert spawn.entity_type == "slime"
        assert spawn.count_min == 3
        assert spawn.count_max == 3
        
    def test_get_random_count_fixed(self):
        """Test get_random_count with fixed count."""
        spawn = GuaranteedSpawn(entity_type="orc", count_min=5, count_max=5)
        for _ in range(10):
            assert spawn.get_random_count() == 5
            
    def test_get_random_count_range(self):
        """Test get_random_count with range."""
        spawn = GuaranteedSpawn(entity_type="slime", count_min=3, count_max=8)
        counts = [spawn.get_random_count() for _ in range(100)]
        # All values should be in range
        assert all(3 <= c <= 8 for c in counts)
        # Should have some variety (not all the same)
        assert len(set(counts)) > 1


class TestLevelOverride:
    """Test LevelOverride dataclass."""
    
    def test_creation(self):
        """Test creating a LevelOverride."""
        monsters = [GuaranteedSpawn("orc", 2, 2)]
        items = [GuaranteedSpawn("healing_potion", 1, 1)]
        equipment = [GuaranteedSpawn("sword", 1, 1)]
        
        override = LevelOverride(
            level_number=1,
            mode="additional",
            guaranteed_monsters=monsters,
            guaranteed_items=items,
            guaranteed_equipment=equipment
        )
        
        assert override.level_number == 1
        assert override.mode == "additional"
        assert len(override.guaranteed_monsters) == 1
        assert len(override.guaranteed_items) == 1
        assert len(override.guaranteed_equipment) == 1
        
    def test_all_guaranteed_spawns(self):
        """Test getting all spawns combined."""
        monsters = [GuaranteedSpawn("orc", 2, 2), GuaranteedSpawn("troll", 1, 1)]
        items = [GuaranteedSpawn("healing_potion", 3, 3)]
        equipment = [GuaranteedSpawn("sword", 1, 1), GuaranteedSpawn("shield", 1, 1)]
        
        override = LevelOverride(
            level_number=5,
            mode="additional",
            guaranteed_monsters=monsters,
            guaranteed_items=items,
            guaranteed_equipment=equipment
        )
        
        all_spawns = override.all_guaranteed_spawns
        assert len(all_spawns) == 5  # 2 monsters + 1 item + 2 equipment


class TestLevelTemplateRegistry:
    """Test LevelTemplateRegistry class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.registry = LevelTemplateRegistry()
        
    def test_initialization(self):
        """Test registry initialization."""
        assert self.registry.overrides == {}
        assert self.registry.version is None
        
    def test_parse_level_override_basic(self):
        """Test parsing a basic level override."""
        data = {
            'guaranteed_spawns': {
                'mode': 'additional',
                'monsters': [
                    {'type': 'slime', 'count': 2}
                ],
                'items': [
                    {'type': 'healing_potion', 'count': 1}
                ],
                'equipment': [
                    {'type': 'dagger', 'count': 1}
                ]
            }
        }
        
        override = self.registry._parse_level_override(1, data)
        
        assert override.level_number == 1
        assert override.mode == 'additional'
        assert len(override.guaranteed_monsters) == 1
        assert override.guaranteed_monsters[0].entity_type == 'slime'
        assert override.guaranteed_monsters[0].count_min == 2
        assert override.guaranteed_monsters[0].count_max == 2
        assert len(override.guaranteed_items) == 1
        assert len(override.guaranteed_equipment) == 1
        
    def test_parse_level_override_replace_mode(self):
        """Test parsing a level override with replace mode."""
        data = {
            'guaranteed_spawns': {
                'mode': 'replace',
                'monsters': [
                    {'type': 'orc', 'count': 5}
                ],
                'items': [],
                'equipment': []
            }
        }
        
        override = self.registry._parse_level_override(2, data)
        
        assert override.mode == 'replace'
        assert len(override.guaranteed_monsters) == 1
        
    def test_parse_level_override_invalid_mode(self):
        """Test parsing with invalid mode defaults to 'additional'."""
        data = {
            'guaranteed_spawns': {
                'mode': 'invalid_mode',
                'monsters': [],
                'items': [],
                'equipment': []
            }
        }
        
        override = self.registry._parse_level_override(1, data)
        
        assert override.mode == 'additional'  # Should default
        
    def test_parse_level_override_missing_mode(self):
        """Test parsing without mode defaults to 'additional'."""
        data = {
            'guaranteed_spawns': {
                'monsters': [],
                'items': [],
                'equipment': []
            }
        }
        
        override = self.registry._parse_level_override(1, data)
        
        assert override.mode == 'additional'
        
    def test_parse_level_override_empty_lists(self):
        """Test parsing with empty spawn lists."""
        data = {
            'guaranteed_spawns': {
                'mode': 'additional',
                'monsters': [],
                'items': [],
                'equipment': []
            }
        }
        
        override = self.registry._parse_level_override(3, data)
        
        assert len(override.guaranteed_monsters) == 0
        assert len(override.guaranteed_items) == 0
        assert len(override.guaranteed_equipment) == 0
        
    def test_load_template_file_not_found(self):
        """Test loading a non-existent file logs and continues."""
        self.registry._load_template_file('/nonexistent/path.yaml')
        
        # Should not raise exception, just log
        assert len(self.registry.overrides) == 0
        
    def test_load_template_file_empty(self):
        """Test loading an empty YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write('')
            temp_path = f.name
            
        try:
            self.registry._load_template_file(temp_path)
            assert len(self.registry.overrides) == 0
        finally:
            os.unlink(temp_path)
            
    def test_load_template_file_valid(self):
        """Test loading a valid template file."""
        yaml_content = """
version: "1.0"
level_overrides:
  1:
    guaranteed_spawns:
      mode: "additional"
      monsters:
        - type: "slime"
          count: 2
      items:
        - type: "healing_potion"
          count: 1
      equipment: []
  2:
    guaranteed_spawns:
      mode: "replace"
      monsters:
        - type: "orc"
          count: 3
      items: []
      equipment: []
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
            
        try:
            self.registry._load_template_file(temp_path)
            
            assert self.registry.version == "1.0"
            assert len(self.registry.overrides) == 2
            assert 1 in self.registry.overrides
            assert 2 in self.registry.overrides
            
            level_1 = self.registry.overrides[1]
            assert level_1.mode == "additional"
            assert len(level_1.guaranteed_monsters) == 1
            assert level_1.guaranteed_monsters[0].entity_type == "slime"
            
            level_2 = self.registry.overrides[2]
            assert level_2.mode == "replace"
            assert len(level_2.guaranteed_monsters) == 1
            
        finally:
            os.unlink(temp_path)
            
    def test_testing_file_overrides_normal(self):
        """Test that testing template overrides normal template."""
        normal_yaml = """
version: "1.0"
level_overrides:
  1:
    guaranteed_spawns:
      mode: "additional"
      monsters:
        - type: "orc"
          count: 1
      items: []
      equipment: []
"""
        
        testing_yaml = """
version: "1.0"
level_overrides:
  1:
    guaranteed_spawns:
      mode: "replace"
      monsters:
        - type: "slime"
          count: 5
      items: []
      equipment: []
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(normal_yaml)
            normal_path = f.name
            
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f2:
            f2.write(testing_yaml)
            testing_path = f2.name
            
        try:
            # Load normal first
            self.registry._load_template_file(normal_path, is_testing=False)
            assert self.registry.overrides[1].mode == "additional"
            assert self.registry.overrides[1].guaranteed_monsters[0].entity_type == "orc"
            
            # Load testing, should override
            self.registry._load_template_file(testing_path, is_testing=True)
            assert self.registry.overrides[1].mode == "replace"
            assert self.registry.overrides[1].guaranteed_monsters[0].entity_type == "slime"
            assert self.registry.overrides[1].guaranteed_monsters[0].count_min == 5
            assert self.registry.overrides[1].guaranteed_monsters[0].count_max == 5
            
        finally:
            os.unlink(normal_path)
            os.unlink(testing_path)
            
    def test_get_level_override_exists(self):
        """Test getting an override that exists."""
        override = LevelOverride(
            level_number=5,
            mode="additional",
            guaranteed_monsters=[],
            guaranteed_items=[],
            guaranteed_equipment=[]
        )
        self.registry.overrides[5] = override
        
        result = self.registry.get_level_override(5)
        assert result is override
        
    def test_get_level_override_not_exists(self):
        """Test getting an override that doesn't exist."""
        result = self.registry.get_level_override(99)
        assert result is None
        
    def test_has_override(self):
        """Test checking if override exists."""
        override = LevelOverride(
            level_number=3,
            mode="additional",
            guaranteed_monsters=[],
            guaranteed_items=[],
            guaranteed_equipment=[]
        )
        self.registry.overrides[3] = override
        
        assert self.registry.has_override(3) is True
        assert self.registry.has_override(7) is False
        
    def test_clear(self):
        """Test clearing the registry."""
        self.registry.version = "1.0"
        self.registry.overrides[1] = LevelOverride(
            level_number=1,
            mode="additional",
            guaranteed_monsters=[],
            guaranteed_items=[],
            guaranteed_equipment=[]
        )
        
        self.registry.clear()
        
        assert self.registry.version is None
        assert len(self.registry.overrides) == 0


class TestGlobalRegistry:
    """Test global registry functions."""
    
    def test_get_level_template_registry(self):
        """Test getting the global registry instance."""
        # Clear any existing instance
        import config.level_template_registry as ltr_module
        ltr_module._level_template_registry = None
        
        registry1 = get_level_template_registry()
        registry2 = get_level_template_registry()
        
        # Should be the same instance
        assert registry1 is registry2
        
    @patch('config.level_template_registry.LevelTemplateRegistry')
    def test_load_level_templates(self, mock_registry_class):
        """Test load_level_templates creates a new instance."""
        mock_instance = mock_registry_class.return_value
        
        load_level_templates()
        
        mock_registry_class.assert_called_once()
        mock_instance.load_templates.assert_called_once()

