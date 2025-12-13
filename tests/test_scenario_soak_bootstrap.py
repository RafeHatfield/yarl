"""Tests for scenario-based soak bootstrap functionality.

These tests verify that:
1. Scenario maps are properly loaded from YAML (not from procedural worldgen)
2. Expected monsters from scenarios are present at correct positions
3. scenario_id is properly recorded in run_metrics
4. The is_scenario_run flag is set to prevent worldgen fallback

Phase 17B: Scenario Bootstrap Fix
"""

import pytest
from unittest.mock import patch, MagicMock

from engine.scenario_bootstrap import (
    create_scenario_session,
    validate_scenario_map_not_overwritten,
    ScenarioMonsterMarker,
    ScenarioRunContext,
)
from instrumentation.run_metrics import (
    RunMetrics,
    RunMetricsRecorder,
    initialize_run_metrics_recorder,
    get_run_metrics_recorder,
    reset_run_metrics_recorder,
)


class TestScenarioMonsterMarker:
    """Tests for ScenarioMonsterMarker dataclass."""
    
    def test_marker_stores_position(self):
        """Marker should store monster type and position."""
        marker = ScenarioMonsterMarker(
            monster_type="orc_chieftain",
            x=5,
            y=4
        )
        assert marker.monster_type == "orc_chieftain"
        assert marker.x == 5
        assert marker.y == 4


class TestScenarioRunContext:
    """Tests for ScenarioRunContext validation."""
    
    def test_context_stores_scenario_info(self):
        """Context should store scenario metadata."""
        context = ScenarioRunContext(
            scenario_id="orc_swarm_tight",
            scenario_name="Orc Swarm – Tight",
            depth=5,
            expected_monsters=[
                ScenarioMonsterMarker("orc_chieftain", 5, 4),
                ScenarioMonsterMarker("orc_veteran", 3, 4),
            ]
        )
        assert context.scenario_id == "orc_swarm_tight"
        assert context.depth == 5
        assert len(context.expected_monsters) == 2
        assert not context.is_validated
    
    def test_validate_monsters_present_finds_entities(self):
        """Validation should find entities at expected positions."""
        # Create mock entities with positions and Fighter components
        mock_entity_1 = MagicMock()
        mock_entity_1.x = 5
        mock_entity_1.y = 4
        mock_entity_1.get_component_optional.return_value = MagicMock()  # Has fighter
        
        mock_entity_2 = MagicMock()
        mock_entity_2.x = 3
        mock_entity_2.y = 4
        mock_entity_2.get_component_optional.return_value = MagicMock()  # Has fighter
        
        context = ScenarioRunContext(
            scenario_id="test",
            scenario_name="Test",
            depth=1,
            expected_monsters=[
                ScenarioMonsterMarker("orc_chieftain", 5, 4),
                ScenarioMonsterMarker("orc_veteran", 3, 4),
            ]
        )
        
        is_valid, message = context.validate_monsters_present([mock_entity_1, mock_entity_2])
        assert is_valid
        assert context.is_validated
        assert "Validated 2/2" in message
    
    def test_validate_monsters_missing_fails(self):
        """Validation should fail when expected monsters are missing."""
        # Create mock entity at wrong position
        mock_entity = MagicMock()
        mock_entity.x = 10
        mock_entity.y = 10
        mock_entity.get_component_optional.return_value = MagicMock()
        
        context = ScenarioRunContext(
            scenario_id="test",
            scenario_name="Test",
            depth=1,
            expected_monsters=[
                ScenarioMonsterMarker("orc_chieftain", 5, 4),
            ]
        )
        
        is_valid, message = context.validate_monsters_present([mock_entity])
        assert not is_valid
        assert "Missing expected monsters" in message
        assert not context.is_validated


class TestRunMetricsScenarioId:
    """Tests for scenario_id in RunMetrics."""
    
    def setup_method(self):
        """Reset run metrics before each test."""
        reset_run_metrics_recorder()
    
    def teardown_method(self):
        """Reset run metrics after each test."""
        reset_run_metrics_recorder()
    
    def test_run_metrics_includes_scenario_id(self):
        """RunMetrics should include scenario_id when set."""
        metrics = RunMetrics(
            run_id="test123",
            mode="bot",
            scenario_id="orc_swarm_tight"
        )
        assert metrics.scenario_id == "orc_swarm_tight"
        
        # Check serialization
        data = metrics.to_dict()
        assert data["scenario_id"] == "orc_swarm_tight"
    
    def test_run_metrics_recorder_accepts_scenario_id(self):
        """RunMetricsRecorder should accept and store scenario_id."""
        recorder = RunMetricsRecorder(
            mode="bot",
            seed=12345,
            start_floor=5,
            scenario_id="test_scenario"
        )
        assert recorder.scenario_id == "test_scenario"
    
    def test_initialize_run_metrics_recorder_with_scenario_id(self):
        """initialize_run_metrics_recorder should accept scenario_id."""
        recorder = initialize_run_metrics_recorder(
            mode="bot",
            seed=12345,
            start_floor=5,
            scenario_id="orc_swarm_tight"
        )
        assert recorder.scenario_id == "orc_swarm_tight"
        
        # Verify global singleton is set
        global_recorder = get_run_metrics_recorder()
        assert global_recorder is recorder
        assert global_recorder.scenario_id == "orc_swarm_tight"


class TestValidateScenarioMapNotOverwritten:
    """Tests for the defensive validation function."""
    
    def test_skips_non_scenario_runs(self):
        """Should skip validation for non-scenario runs."""
        mock_map = MagicMock()
        mock_map.is_scenario_run = False
        
        # Should not raise
        validate_scenario_map_not_overwritten(mock_map, [])
    
    def test_raises_on_missing_monsters(self):
        """Should raise AssertionError when expected monsters are missing."""
        mock_map = MagicMock()
        mock_map.is_scenario_run = True
        mock_map.scenario_context = ScenarioRunContext(
            scenario_id="test",
            scenario_name="Test",
            depth=1,
            expected_monsters=[
                ScenarioMonsterMarker("orc_chieftain", 5, 4),
            ]
        )
        
        # No entities at expected position
        with pytest.raises(AssertionError, match="SCENARIO MAP VALIDATION FAILED"):
            validate_scenario_map_not_overwritten(mock_map, [])
    
    def test_passes_when_monsters_present(self):
        """Should pass when all expected monsters are present."""
        mock_map = MagicMock()
        mock_map.is_scenario_run = True
        mock_map.scenario_context = ScenarioRunContext(
            scenario_id="test",
            scenario_name="Test",
            depth=1,
            expected_monsters=[
                ScenarioMonsterMarker("orc_chieftain", 5, 4),
            ]
        )
        
        # Create entity at expected position
        mock_entity = MagicMock()
        mock_entity.x = 5
        mock_entity.y = 4
        mock_entity.get_component_optional.return_value = MagicMock()  # Has fighter
        
        # Should not raise
        validate_scenario_map_not_overwritten(mock_map, [mock_entity])


class TestCreateScenarioSession:
    """Tests for create_scenario_session function."""
    
    def setup_method(self):
        """Reset run metrics before each test."""
        reset_run_metrics_recorder()
    
    def teardown_method(self):
        """Reset run metrics after each test."""
        reset_run_metrics_recorder()
    
    def test_raises_for_unknown_scenario(self):
        """Should raise ValueError for unknown scenario ID."""
        constants = {
            "message_x": 0,
            "message_width": 40,
            "message_height": 5,
            "input_config": {"bot_enabled": True},
            "soak_config": {},
        }
        
        with pytest.raises(ValueError, match="not found"):
            create_scenario_session("nonexistent_scenario", constants)
    
    @pytest.mark.slow
    def test_creates_session_with_scenario_map(self):
        """Should create a session using the scenario map, not worldgen.
        
        This test verifies the core fix: scenario runs should use the
        scenario-defined map and monsters, not procedural generation.
        """
        # This test requires actual scenario files to exist
        # Skip if orc_swarm_tight doesn't exist
        from config.level_template_registry import get_scenario_registry
        
        registry = get_scenario_registry()
        if not registry.has_scenario("orc_swarm_tight"):
            pytest.skip("orc_swarm_tight scenario not found")
        
        constants = {
            "message_x": 0,
            "message_width": 40,
            "message_height": 5,
            "input_config": {"bot_enabled": True},
            "soak_config": {"max_turns": 100},
        }
        
        player, entities, game_map, message_log, game_state = create_scenario_session(
            "orc_swarm_tight",
            constants
        )
        
        # Verify is_scenario_run flag is set
        assert getattr(game_map, 'is_scenario_run', False) is True
        
        # Verify scenario_context is set
        assert hasattr(game_map, 'scenario_context')
        assert game_map.scenario_context.scenario_id == "orc_swarm_tight"
        
        # Verify run metrics has scenario_id
        recorder = get_run_metrics_recorder()
        assert recorder is not None
        assert recorder.scenario_id == "orc_swarm_tight"
        
        # Verify expected monsters are in entities list
        # orc_swarm_tight should have 1 orc_chieftain and 2 orc_veterans
        from components.component_registry import ComponentType
        monster_count = sum(
            1 for e in entities 
            if e.get_component_optional(ComponentType.FIGHTER) and e != player
        )
        assert monster_count >= 3, f"Expected at least 3 monsters, got {monster_count}"
    
    @pytest.mark.slow
    def test_scenario_session_records_kills(self):
        """Scenario sessions should be able to record monster kills.
        
        This is a minimal integration test to verify the scenario map
        is properly connected to the combat/statistics systems.
        """
        from config.level_template_registry import get_scenario_registry
        
        registry = get_scenario_registry()
        if not registry.has_scenario("orc_swarm_tight"):
            pytest.skip("orc_swarm_tight scenario not found")
        
        constants = {
            "message_x": 0,
            "message_width": 40,
            "message_height": 5,
            "input_config": {"bot_enabled": True},
            "soak_config": {"max_turns": 100},
        }
        
        player, entities, game_map, message_log, game_state = create_scenario_session(
            "orc_swarm_tight",
            constants
        )
        
        # Verify the player has a Statistics component (needed for tracking kills)
        from components.component_registry import ComponentType
        stats = player.get_component_optional(ComponentType.STATISTICS)
        assert stats is not None, "Player should have Statistics component"
        
        # Initial kill count should be 0
        assert stats.total_kills == 0
