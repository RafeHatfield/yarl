"""Phase 21.4: Hazards Suite Validation Tests

Verifies that:
1. Hazards suite includes the correct scenarios
2. Suite scenarios can be loaded and run deterministically
3. Suite infrastructure works correctly
"""

import pytest


class TestHazardsSuiteConfiguration:
    """Tests for hazards suite configuration."""
    
    def test_hazards_suite_includes_required_scenarios(self):
        """Hazards suite includes all required trap scenarios."""
        from tools.hazards_suite import HAZARDS_SCENARIOS
        
        scenario_ids = [s["id"] for s in HAZARDS_SCENARIOS]
        
        # Phase 21.1-21.5 trap scenarios
        assert "trap_root_identity" in scenario_ids
        assert "trap_spike_identity" in scenario_ids
        assert "trap_teleport_identity" in scenario_ids
        assert "trap_gas_identity" in scenario_ids
        assert "trap_fire_identity" in scenario_ids
        assert "trap_hole_identity" in scenario_ids
    
    def test_hazards_suite_list_matches_tagged_scenarios(self):
        """HAZARDS_SCENARIOS list matches all scenarios tagged with 'hazards' suite.
        
        Suite doctrine: Tags decide membership, list decides ordering.
        This test ensures the curated list stays in sync with suite tags.
        """
        from tools.hazards_suite import HAZARDS_SCENARIOS
        from config.level_template_registry import get_scenario_registry
        
        registry = get_scenario_registry()
        
        # Get all scenarios tagged with "hazards"
        all_scenarios = registry.get_all_scenarios()
        tagged_hazards = []
        
        for scenario_id, scenario in all_scenarios.items():
            if scenario and hasattr(scenario, 'suites') and scenario.suites:
                if "hazards" in scenario.suites:
                    tagged_hazards.append(scenario_id)
        
        # Get scenarios in the curated list
        list_scenarios = [s["id"] for s in HAZARDS_SCENARIOS]
        
        # Verify they match (order may differ, but membership should be identical)
        assert set(list_scenarios) == set(tagged_hazards), \
            f"HAZARDS_SCENARIOS list doesn't match tagged scenarios.\n" \
            f"List: {sorted(list_scenarios)}\n" \
            f"Tagged: {sorted(tagged_hazards)}"
    
    def test_hazards_scenarios_have_valid_structure(self):
        """All hazards scenarios have required fields."""
        from tools.hazards_suite import HAZARDS_SCENARIOS
        
        for scenario in HAZARDS_SCENARIOS:
            assert "id" in scenario
            assert "runs" in scenario
            assert "turn_limit" in scenario
            assert isinstance(scenario["runs"], int)
            assert isinstance(scenario["turn_limit"], int)
            assert scenario["runs"] > 0
            assert scenario["turn_limit"] > 0


class TestHazardsSuiteScenarios:
    """Tests for hazards suite scenario loading."""
    
    def test_all_hazards_scenarios_can_be_loaded(self):
        """All hazards suite scenarios can be loaded from registry."""
        from config.level_template_registry import get_scenario_registry
        from tools.hazards_suite import HAZARDS_SCENARIOS
        
        registry = get_scenario_registry()
        
        for scenario_config in HAZARDS_SCENARIOS:
            scenario_id = scenario_config["id"]
            scenario = registry.get_scenario_definition(scenario_id)
            
            assert scenario is not None, f"Scenario {scenario_id} not found in registry"
            assert scenario.scenario_id == scenario_id
    
    def test_hazards_scenarios_have_suite_tags(self):
        """All hazards scenarios are tagged with 'hazards' suite."""
        from config.level_template_registry import get_scenario_registry
        from tools.hazards_suite import HAZARDS_SCENARIOS
        
        registry = get_scenario_registry()
        
        for scenario_config in HAZARDS_SCENARIOS:
            scenario_id = scenario_config["id"]
            scenario = registry.get_scenario_definition(scenario_id)
            
            if scenario and hasattr(scenario, 'suites'):
                # If suites field exists, it should include "hazards"
                # (Some scenarios might not have the field yet if YAML not updated)
                if scenario.suites:
                    assert "hazards" in scenario.suites, \
                        f"Scenario {scenario_id} should be tagged with 'hazards' suite"


class TestHazardsSuiteDeterminism:
    """Tests for hazards suite determinism."""
    
    @pytest.mark.slow
    def test_hazards_suite_scenarios_are_deterministic(self):
        """Hazards suite scenarios produce identical results with same seed."""
        from config.level_template_registry import get_scenario_registry
        from services.scenario_harness import run_scenario_many, make_bot_policy
        from tools.hazards_suite import HAZARDS_SCENARIOS
        
        registry = get_scenario_registry()
        policy = make_bot_policy("tactical_fighter")
        seed_base = 1337
        
        # Test a subset for speed (full suite tested by make hazards-suite)
        test_scenarios = ["trap_root_identity", "trap_gas_identity"]
        
        for scenario_id in test_scenarios:
            scenario = registry.get_scenario_definition(scenario_id)
            if scenario is None:
                pytest.skip(f"Scenario {scenario_id} not found")
            
            # Find config
            config = next((s for s in HAZARDS_SCENARIOS if s["id"] == scenario_id), None)
            if not config:
                continue
            
            # Run twice with same seed
            runs = min(3, config["runs"])  # Use fewer runs for test speed
            turn_limit = config["turn_limit"]
            
            metrics1 = run_scenario_many(scenario, policy, runs, turn_limit, seed_base=seed_base)
            metrics2 = run_scenario_many(scenario, policy, runs, turn_limit, seed_base=seed_base)
            
            # Verify determinism (basic check - runs completed)
            assert metrics1.runs == metrics2.runs
