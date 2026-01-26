"""Phase 22.4: Identity Suite Validation Tests

Verifies that:
1. Identity suite includes the correct scenarios
2. Suite scenarios can be loaded and match YAML tags
3. Suite infrastructure works correctly

Doctrine: YAML tags decide membership, IDENTITY_SCENARIOS list decides ordering.
"""

import pytest


class TestIdentitySuiteConfiguration:
    """Tests for identity suite configuration."""

    def test_identity_suite_includes_required_scenarios(self):
        """Identity suite includes key mechanic identity scenarios."""
        from tools.identity_suite import IDENTITY_SCENARIOS

        scenario_ids = [s["id"] for s in IDENTITY_SCENARIOS]

        # Monster identity scenarios (Phase 19)
        assert "monster_slime_identity" in scenario_ids
        assert "monster_skeleton_identity" in scenario_ids
        assert "monster_orc_chieftain_identity" in scenario_ids
        assert "monster_necromancer_identity" in scenario_ids
        assert "monster_lich_identity" in scenario_ids
        assert "troll_identity" in scenario_ids

        # Ability identity scenarios (Phase 20)
        assert "player_reflex_potion_identity" in scenario_ids
        assert "root_potion_entangle_identity" in scenario_ids
        assert "knockback_weapon_identity" in scenario_ids
        assert "scroll_fireball_identity" in scenario_ids

        # Oath identity scenarios (Phase 22.1)
        assert "oath_embers_identity" in scenario_ids
        assert "oath_venom_identity" in scenario_ids
        assert "oath_chains_identity" in scenario_ids

        # Ranged identity scenarios (Phase 22.2)
        assert "ranged_viability_arena" in scenario_ids

        # Skirmisher identity scenarios (Phase 22.3)
        assert "skirmisher_identity" in scenario_ids
        assert "skirmisher_vs_ranged_net_identity" in scenario_ids

    def test_identity_suite_list_matches_tagged_scenarios(self):
        """IDENTITY_SCENARIOS list matches all scenarios tagged with 'identity' suite.

        Suite doctrine: Tags decide membership, list decides ordering.
        This test ensures the curated list stays in sync with suite tags.
        """
        from tools.identity_suite import IDENTITY_SCENARIOS
        from config.level_template_registry import get_scenario_registry

        registry = get_scenario_registry()

        # Get all scenarios tagged with "identity"
        all_scenarios = registry.get_all_scenarios()
        tagged_identity = []

        for scenario_id, scenario in all_scenarios.items():
            if scenario and hasattr(scenario, 'suites') and scenario.suites:
                if "identity" in scenario.suites:
                    tagged_identity.append(scenario_id)

        # Get scenarios in the curated list
        list_scenarios = [s["id"] for s in IDENTITY_SCENARIOS]

        # Verify they match (order may differ, but membership should be identical)
        assert set(list_scenarios) == set(tagged_identity), \
            f"IDENTITY_SCENARIOS list doesn't match tagged scenarios.\n" \
            f"In list but not tagged: {sorted(set(list_scenarios) - set(tagged_identity))}\n" \
            f"Tagged but not in list: {sorted(set(tagged_identity) - set(list_scenarios))}"

    def test_identity_scenarios_have_valid_structure(self):
        """All identity scenarios have required fields."""
        from tools.identity_suite import IDENTITY_SCENARIOS

        for scenario in IDENTITY_SCENARIOS:
            assert "id" in scenario
            assert "runs" in scenario
            assert "turn_limit" in scenario
            assert isinstance(scenario["runs"], int)
            assert isinstance(scenario["turn_limit"], int)
            assert scenario["runs"] > 0
            assert scenario["turn_limit"] > 0


class TestIdentitySuiteScenarios:
    """Tests for identity suite scenario loading."""

    def test_all_identity_scenarios_can_be_loaded(self):
        """All identity suite scenarios can be loaded from registry."""
        from config.level_template_registry import get_scenario_registry
        from tools.identity_suite import IDENTITY_SCENARIOS

        registry = get_scenario_registry()

        for scenario_config in IDENTITY_SCENARIOS:
            scenario_id = scenario_config["id"]
            scenario = registry.get_scenario_definition(scenario_id)

            assert scenario is not None, f"Scenario {scenario_id} not found in registry"
            assert scenario.scenario_id == scenario_id

    def test_identity_scenarios_have_suite_tags(self):
        """All identity scenarios are tagged with 'identity' suite."""
        from config.level_template_registry import get_scenario_registry
        from tools.identity_suite import IDENTITY_SCENARIOS

        registry = get_scenario_registry()

        for scenario_config in IDENTITY_SCENARIOS:
            scenario_id = scenario_config["id"]
            scenario = registry.get_scenario_definition(scenario_id)

            if scenario and hasattr(scenario, 'suites'):
                # If suites field exists, it should include "identity"
                if scenario.suites:
                    assert "identity" in scenario.suites, \
                        f"Scenario {scenario_id} should be tagged with 'identity' suite"


class TestIdentitySuiteNoOverlap:
    """Tests to ensure suites don't overlap incorrectly."""

    def test_identity_and_balance_suites_are_disjoint(self):
        """Identity and balance suites should not share scenarios.

        Balance suite = ecosystem drift / win rate / attrition
        Identity suite = mechanic invariants / trigger logic / determinism
        """
        from tools.identity_suite import IDENTITY_SCENARIOS
        from tools.balance_suite import SCENARIO_MATRIX

        identity_ids = {s["id"] for s in IDENTITY_SCENARIOS}
        balance_ids = {s["id"] for s in SCENARIO_MATRIX}

        overlap = identity_ids & balance_ids
        assert overlap == set(), \
            f"Scenarios appear in both identity and balance suites: {overlap}"

    def test_identity_and_hazards_suites_are_disjoint(self):
        """Identity and hazards suites should not share scenarios.

        Hazards suite = trap/environmental correctness
        Identity suite = mechanic invariants (non-trap)
        """
        from tools.identity_suite import IDENTITY_SCENARIOS
        from tools.hazards_suite import HAZARDS_SCENARIOS

        identity_ids = {s["id"] for s in IDENTITY_SCENARIOS}
        hazards_ids = {s["id"] for s in HAZARDS_SCENARIOS}

        overlap = identity_ids & hazards_ids
        assert overlap == set(), \
            f"Scenarios appear in both identity and hazards suites: {overlap}"
