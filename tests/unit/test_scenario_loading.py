"""
Unit tests for Phase 12A: Scenario-Aware Level Templates

Tests the ScenarioDefinition dataclass and ScenarioRegistry class
for loading and managing scenario YAML files.
"""

import os
import tempfile
import pytest

from config.level_template_registry import (
    ScenarioDefinition,
    ScenarioRegistry,
    ScenarioLoadError,
    get_scenario_registry,
    list_scenarios,
    get_scenario_definition,
)


class TestScenarioDefinition:
    """Tests for ScenarioDefinition dataclass."""
    
    def test_create_minimal_scenario(self):
        """Test creating a scenario with minimal required fields."""
        scenario = ScenarioDefinition(
            scenario_id="test_scenario",
            name="Test Scenario"
        )
        
        assert scenario.scenario_id == "test_scenario"
        assert scenario.name == "Test Scenario"
        assert scenario.description is None
        assert scenario.depth is None
        assert scenario.defaults == {}
        assert scenario.expected == {}
        assert scenario.rooms == []
        assert scenario.monsters == []
        assert scenario.items == []
        assert scenario.source_file == ""
    
    def test_create_full_scenario(self):
        """Test creating a scenario with all fields."""
        scenario = ScenarioDefinition(
            scenario_id="full_test",
            name="Full Test Scenario",
            description="A fully configured test scenario",
            depth=5,
            defaults={"turn_limit": 200, "player_bot": "observe_only"},
            expected={"surprise_attacks_min": 1},
            rooms=[{"id": "room1", "type": "corridor"}],
            monsters=[{"type": "orc", "count": 1}],
            items=[{"type": "healing_potion", "count": 2}],
            player={"position": [1, 1]},
            hazards=[{"type": "trap", "damage": 5}],
            victory_conditions=[{"type": "kill_all"}],
            defeat_conditions=[{"type": "player_death"}],
            source_file="/path/to/scenario.yaml"
        )
        
        assert scenario.scenario_id == "full_test"
        assert scenario.name == "Full Test Scenario"
        assert scenario.description == "A fully configured test scenario"
        assert scenario.depth == 5
        assert scenario.defaults["turn_limit"] == 200
        assert scenario.expected["surprise_attacks_min"] == 1
        assert len(scenario.rooms) == 1
        assert len(scenario.monsters) == 1
        assert len(scenario.items) == 1
        assert scenario.player["position"] == [1, 1]
        assert len(scenario.hazards) == 1
        assert len(scenario.victory_conditions) == 1
        assert len(scenario.defeat_conditions) == 1
        assert scenario.source_file == "/path/to/scenario.yaml"
    
    def test_get_default_with_existing_key(self):
        """Test get_default returns value for existing key."""
        scenario = ScenarioDefinition(
            scenario_id="test",
            name="Test",
            defaults={"turn_limit": 200}
        )
        
        assert scenario.get_default("turn_limit") == 200
    
    def test_get_default_with_missing_key(self):
        """Test get_default returns fallback for missing key."""
        scenario = ScenarioDefinition(
            scenario_id="test",
            name="Test",
            defaults={}
        )
        
        assert scenario.get_default("turn_limit") is None
        assert scenario.get_default("turn_limit", 100) == 100
    
    def test_get_expected_with_existing_key(self):
        """Test get_expected returns value for existing key."""
        scenario = ScenarioDefinition(
            scenario_id="test",
            name="Test",
            expected={"surprise_attacks_min": 3}
        )
        
        assert scenario.get_expected("surprise_attacks_min") == 3
    
    def test_get_expected_with_missing_key(self):
        """Test get_expected returns fallback for missing key."""
        scenario = ScenarioDefinition(
            scenario_id="test",
            name="Test",
            expected={}
        )
        
        assert scenario.get_expected("surprise_attacks_min") is None
        assert scenario.get_expected("surprise_attacks_min", 0) == 0
    
    def test_has_victory_conditions(self):
        """Test has_victory_conditions returns correct boolean."""
        scenario_with = ScenarioDefinition(
            scenario_id="test",
            name="Test",
            victory_conditions=[{"type": "kill_all"}]
        )
        scenario_without = ScenarioDefinition(
            scenario_id="test",
            name="Test"
        )
        
        assert scenario_with.has_victory_conditions() is True
        assert scenario_without.has_victory_conditions() is False
    
    def test_has_defeat_conditions(self):
        """Test has_defeat_conditions returns correct boolean."""
        scenario_with = ScenarioDefinition(
            scenario_id="test",
            name="Test",
            defeat_conditions=[{"type": "player_death"}]
        )
        scenario_without = ScenarioDefinition(
            scenario_id="test",
            name="Test"
        )
        
        assert scenario_with.has_defeat_conditions() is True
        assert scenario_without.has_defeat_conditions() is False


class TestScenarioRegistry:
    """Tests for ScenarioRegistry class."""
    
    def test_empty_registry(self):
        """Test registry starts empty."""
        registry = ScenarioRegistry()
        registry._loaded = True  # Skip auto-load
        
        assert registry.list_scenarios() == []
        assert registry.get_scenario_definition("nonexistent") is None
        assert registry.has_scenario("nonexistent") is False
    
    def test_load_from_nonexistent_directory(self):
        """Test loading from nonexistent directory doesn't crash."""
        registry = ScenarioRegistry()
        registry.load_scenarios("/nonexistent/path/to/scenarios")
        
        assert registry.list_scenarios() == []
    
    def test_load_valid_scenario_file(self):
        """Test loading a valid scenario YAML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a valid scenario file
            scenario_content = """
scenario_id: test_backstab
name: "Test Backstab Scenario"
description: "A test scenario for backstab mechanics"
depth: 5
defaults:
  turn_limit: 200
  player_bot: "observe_only"
expected:
  surprise_attacks_min: 1
rooms:
  - id: "corridor"
    type: "corridor"
monsters:
  - type: "orc"
    count: 1
items:
  - type: "healing_potion"
    count: 2
"""
            filepath = os.path.join(tmpdir, "scenario_backstab_test.yaml")
            with open(filepath, "w") as f:
                f.write(scenario_content)
            
            registry = ScenarioRegistry()
            registry.load_scenarios(tmpdir)
            
            # Verify scenario was loaded
            assert "test_backstab" in registry.list_scenarios()
            
            scenario = registry.get_scenario_definition("test_backstab")
            assert scenario is not None
            assert scenario.name == "Test Backstab Scenario"
            assert scenario.description == "A test scenario for backstab mechanics"
            assert scenario.depth == 5
            assert scenario.defaults["turn_limit"] == 200
            assert scenario.expected["surprise_attacks_min"] == 1
            assert len(scenario.rooms) == 1
            assert len(scenario.monsters) == 1
            assert len(scenario.items) == 1
            assert scenario.items[0]["count"] == 2  # One item entry with count=2
            assert scenario.source_file == filepath
    
    def test_load_multiple_scenarios(self):
        """Test loading multiple scenario files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create two scenario files
            for i, name in enumerate(["alpha", "beta"]):
                content = f"""
scenario_id: scenario_{name}
name: "Scenario {name.upper()}"
depth: {i + 1}
"""
                filepath = os.path.join(tmpdir, f"scenario_{name}.yaml")
                with open(filepath, "w") as f:
                    f.write(content)
            
            registry = ScenarioRegistry()
            registry.load_scenarios(tmpdir)
            
            scenarios = registry.list_scenarios()
            assert len(scenarios) == 2
            assert "scenario_alpha" in scenarios
            assert "scenario_beta" in scenarios
    
    def test_missing_required_field_scenario_id(self):
        """Test that missing scenario_id produces clear error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = """
name: "Missing ID Scenario"
"""
            filepath = os.path.join(tmpdir, "scenario_missing_id.yaml")
            with open(filepath, "w") as f:
                f.write(content)
            
            registry = ScenarioRegistry()
            registry.load_scenarios(tmpdir)
            
            # Should not crash, but scenario should not be loaded
            assert registry.list_scenarios() == []
    
    def test_missing_required_field_name(self):
        """Test that missing name produces clear error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = """
scenario_id: missing_name
"""
            filepath = os.path.join(tmpdir, "scenario_missing_name.yaml")
            with open(filepath, "w") as f:
                f.write(content)
            
            registry = ScenarioRegistry()
            registry.load_scenarios(tmpdir)
            
            # Should not crash, but scenario should not be loaded
            assert registry.list_scenarios() == []
    
    def test_invalid_defaults_type(self):
        """Test that invalid defaults type produces clear error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = """
scenario_id: bad_defaults
name: "Bad Defaults"
defaults: "not a dict"
"""
            filepath = os.path.join(tmpdir, "scenario_bad_defaults.yaml")
            with open(filepath, "w") as f:
                f.write(content)
            
            registry = ScenarioRegistry()
            registry.load_scenarios(tmpdir)
            
            # Should not crash, but scenario should not be loaded due to validation
            assert registry.list_scenarios() == []
    
    def test_invalid_expected_type(self):
        """Test that invalid expected type produces clear error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = """
scenario_id: bad_expected
name: "Bad Expected"
expected: ["not", "a", "dict"]
"""
            filepath = os.path.join(tmpdir, "scenario_bad_expected.yaml")
            with open(filepath, "w") as f:
                f.write(content)
            
            registry = ScenarioRegistry()
            registry.load_scenarios(tmpdir)
            
            # Should not crash, but scenario should not be loaded due to validation
            assert registry.list_scenarios() == []
    
    def test_malformed_yaml(self):
        """Test that malformed YAML produces clear error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = """
scenario_id: malformed
name: "Malformed
  - invalid yaml structure
"""
            filepath = os.path.join(tmpdir, "scenario_malformed.yaml")
            with open(filepath, "w") as f:
                f.write(content)
            
            registry = ScenarioRegistry()
            registry.load_scenarios(tmpdir)
            
            # Should not crash, but scenario should not be loaded
            assert registry.list_scenarios() == []
    
    def test_empty_scenario_file(self):
        """Test that empty file produces clear error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "scenario_empty.yaml")
            with open(filepath, "w") as f:
                f.write("")
            
            registry = ScenarioRegistry()
            registry.load_scenarios(tmpdir)
            
            # Should not crash, but scenario should not be loaded
            assert registry.list_scenarios() == []
    
    def test_has_scenario(self):
        """Test has_scenario method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = """
scenario_id: existing
name: "Existing Scenario"
"""
            filepath = os.path.join(tmpdir, "scenario_existing.yaml")
            with open(filepath, "w") as f:
                f.write(content)
            
            registry = ScenarioRegistry()
            registry.load_scenarios(tmpdir)
            
            assert registry.has_scenario("existing") is True
            assert registry.has_scenario("nonexistent") is False
    
    def test_get_all_scenarios(self):
        """Test get_all_scenarios returns dictionary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = """
scenario_id: test_all
name: "Test All"
"""
            filepath = os.path.join(tmpdir, "scenario_test_all.yaml")
            with open(filepath, "w") as f:
                f.write(content)
            
            registry = ScenarioRegistry()
            registry.load_scenarios(tmpdir)
            
            all_scenarios = registry.get_all_scenarios()
            assert isinstance(all_scenarios, dict)
            assert "test_all" in all_scenarios
            assert isinstance(all_scenarios["test_all"], ScenarioDefinition)
    
    def test_clear(self):
        """Test clear method removes all scenarios."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = """
scenario_id: to_clear
name: "To Clear"
"""
            filepath = os.path.join(tmpdir, "scenario_to_clear.yaml")
            with open(filepath, "w") as f:
                f.write(content)
            
            registry = ScenarioRegistry()
            registry.load_scenarios(tmpdir)
            
            assert len(registry.list_scenarios()) == 1
            
            registry.clear()
            
            # After clear, should be empty and not loaded
            assert registry._loaded is False
    
    def test_reload(self):
        """Test reload method reloads scenarios from disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content1 = """
scenario_id: original
name: "Original"
"""
            filepath = os.path.join(tmpdir, "scenario_original.yaml")
            with open(filepath, "w") as f:
                f.write(content1)
            
            registry = ScenarioRegistry()
            registry.load_scenarios(tmpdir)
            
            assert "original" in registry.list_scenarios()
            
            # Add a new file
            content2 = """
scenario_id: new_scenario
name: "New Scenario"
"""
            filepath2 = os.path.join(tmpdir, "scenario_new.yaml")
            with open(filepath2, "w") as f:
                f.write(content2)
            
            registry.reload(tmpdir)
            
            # Both should now be present
            scenarios = registry.list_scenarios()
            assert "original" in scenarios
            assert "new_scenario" in scenarios
    
    def test_only_loads_scenario_prefix_files(self):
        """Test that only scenario_*.yaml files are loaded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a scenario file
            scenario_content = """
scenario_id: valid
name: "Valid Scenario"
"""
            with open(os.path.join(tmpdir, "scenario_valid.yaml"), "w") as f:
                f.write(scenario_content)
            
            # Create a non-scenario file
            other_content = """
scenario_id: invalid
name: "Should Not Load"
"""
            with open(os.path.join(tmpdir, "other_file.yaml"), "w") as f:
                f.write(other_content)
            
            registry = ScenarioRegistry()
            registry.load_scenarios(tmpdir)
            
            scenarios = registry.list_scenarios()
            assert "valid" in scenarios
            assert "invalid" not in scenarios


class TestScenarioLoadError:
    """Tests for ScenarioLoadError exception."""
    
    def test_error_without_file_path(self):
        """Test error message without file path."""
        error = ScenarioLoadError("Test error message")
        
        assert "Test error message" in str(error)
        assert error.message == "Test error message"
        assert error.file_path is None
    
    def test_error_with_file_path(self):
        """Test error message includes file path."""
        error = ScenarioLoadError("Test error", "/path/to/file.yaml")
        
        assert "Test error" in str(error)
        assert "/path/to/file.yaml" in str(error)
        assert error.file_path == "/path/to/file.yaml"


class TestGlobalFunctions:
    """Tests for module-level convenience functions."""
    
    def test_list_scenarios_returns_list(self):
        """Test list_scenarios returns a list."""
        # This tests the actual installed scenarios
        scenarios = list_scenarios()
        assert isinstance(scenarios, list)
    
    def test_get_scenario_definition_for_nonexistent(self):
        """Test get_scenario_definition returns None for nonexistent."""
        result = get_scenario_definition("definitely_nonexistent_scenario_xyz")
        assert result is None


class TestInstalledScenarios:
    """Tests for the example scenarios installed with Phase 12A."""
    
    def test_backstab_scenario_loads(self):
        """Test that scenario_backstab.yaml loads successfully."""
        registry = get_scenario_registry()
        scenario = registry.get_scenario_definition("backstab_training")
        
        # If scenario files aren't installed, skip
        if scenario is None:
            pytest.skip("backstab_training scenario not installed")
        
        assert scenario.scenario_id == "backstab_training"
        assert scenario.name == "Backstab Training Grounds"
        assert scenario.description is not None
        assert scenario.depth == 5
        assert "turn_limit" in scenario.defaults
        assert "surprise_attacks_min" in scenario.expected
    
    def test_plague_arena_scenario_loads(self):
        """Test that scenario_plague_arena.yaml loads successfully."""
        registry = get_scenario_registry()
        scenario = registry.get_scenario_definition("plague_arena")
        
        # If scenario files aren't installed, skip
        if scenario is None:
            pytest.skip("plague_arena scenario not installed")
        
        assert scenario.scenario_id == "plague_arena"
        assert scenario.name == "Plague Arena"
        assert scenario.description is not None
        assert scenario.depth == 8
        assert "turn_limit" in scenario.defaults
        assert scenario.has_victory_conditions()
        assert scenario.has_defeat_conditions()
    
    def test_defaults_load_as_dict(self):
        """Test that defaults section loads as dictionary."""
        registry = get_scenario_registry()
        scenarios = registry.list_scenarios()
        
        for scenario_id in scenarios:
            scenario = registry.get_scenario_definition(scenario_id)
            assert isinstance(scenario.defaults, dict), f"defaults should be dict for {scenario_id}"
    
    def test_expected_loads_as_dict(self):
        """Test that expected section loads as dictionary."""
        registry = get_scenario_registry()
        scenarios = registry.list_scenarios()
        
        for scenario_id in scenarios:
            scenario = registry.get_scenario_definition(scenario_id)
            assert isinstance(scenario.expected, dict), f"expected should be dict for {scenario_id}"
