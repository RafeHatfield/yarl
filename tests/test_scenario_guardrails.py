"""Scenario guardrail tests — enforce explicit monster IDs in suite scenarios.

Phase 22.3.2 follow-up: Prevent regression where scenarios accidentally use
the generic "orc" family placeholder instead of the explicit "orc_grunt" ID.

Why this matters — semantic clarity, not determinism enforcement:
  Scenario monster spawning goes through factory.create_monster() directly,
  so variant resolution (pick_monster → _resolve_orc_variant) is worldgen-only
  and never affected scenarios. However, someone reading type: "orc" in a
  scenario reasonably assumes "this might produce variant orcs", which creates
  ambiguity about intent. Using "orc_grunt" makes the intent unambiguous:
  "I want exactly the plain baseline orc, nothing else."

  The balance guardrail is strict (MUST NOT) because balance scenarios need
  reviewable, unambiguous monster composition. The identity guardrail is a
  policy preference with an opt-out for scenarios that intentionally want
  orc family variety.
"""

import os
import re

import pytest
import yaml


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SCENARIO_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "config", "levels"
)


def _load_scenario_yaml(path: str) -> dict:
    """Load a scenario YAML file and return the parsed dict."""
    with open(path, "r") as f:
        return yaml.safe_load(f)


def _get_monster_types(scenario: dict) -> list[str]:
    """Extract all monster type strings from a scenario dict."""
    types = []
    for monster in scenario.get("monsters", []):
        if "type" in monster:
            types.append(monster["type"])
    return types


def _scenario_path(scenario_id: str) -> str:
    """Resolve a scenario ID to its YAML file path."""
    # Try with and without "scenario_" prefix
    for prefix in ["scenario_", ""]:
        path = os.path.join(_SCENARIO_DIR, f"{prefix}{scenario_id}.yaml")
        if os.path.exists(path):
            return path
    return ""


# ---------------------------------------------------------------------------
# Balance suite guardrail
# ---------------------------------------------------------------------------

class TestBalanceSuiteGuardrails:
    """Balance suite scenarios MUST NOT use the generic 'orc' family placeholder."""

    def test_balance_scenarios_use_explicit_orc_ids(self):
        """No balance suite scenario should spawn type: 'orc'.

        Generic 'orc' triggers variant resolution (brute/shaman/skirmisher mix),
        which makes balance measurements non-deterministic with respect to the
        monster composition. Balance scenarios must use 'orc_grunt' for the
        plain baseline orc.
        """
        from tools.balance_suite import SCENARIO_MATRIX

        violations = []

        for scenario_config in SCENARIO_MATRIX:
            scenario_id = scenario_config["id"]
            path = _scenario_path(scenario_id)
            if not path:
                continue  # Skip scenarios that don't have YAML files

            scenario = _load_scenario_yaml(path)
            monster_types = _get_monster_types(scenario)

            for mtype in monster_types:
                if mtype == "orc":
                    violations.append(scenario_id)
                    break  # One violation per scenario is enough

        assert violations == [], (
            f"Balance suite scenarios must not use generic 'orc' (triggers variant "
            f"resolution). Use 'orc_grunt' instead.\n"
            f"Violations: {sorted(set(violations))}"
        )


class TestIdentitySuiteGuardrails:
    """Identity suite scenarios should prefer explicit orc IDs."""

    def test_identity_scenarios_prefer_explicit_orc_ids(self):
        """Identity suite scenarios should use 'orc_grunt' instead of generic 'orc'.

        This is about semantic clarity, not determinism enforcement.
        Scenario spawning bypasses variant resolution entirely (it goes through
        factory.create_monster, not pick_monster). But type: "orc" in a
        scenario YAML is ambiguous — a reader can't tell whether the author
        intended "plain orc" or "orc family variety". Using "orc_grunt" makes
        the intent explicit.

        Scenarios that intentionally want orc family variety should annotate
        their metadata with 'uses_orc_family: true' to suppress this check.
        """
        from tools.identity_suite import IDENTITY_SCENARIOS

        violations = []

        for scenario_config in IDENTITY_SCENARIOS:
            scenario_id = scenario_config["id"]
            path = _scenario_path(scenario_id)
            if not path:
                continue

            scenario = _load_scenario_yaml(path)

            # Allow opt-out via metadata annotation
            metadata = scenario.get("metadata", {})
            if metadata.get("uses_orc_family"):
                continue

            monster_types = _get_monster_types(scenario)

            for mtype in monster_types:
                if mtype == "orc":
                    violations.append(scenario_id)
                    break

        assert violations == [], (
            f"Identity suite scenarios should use 'orc_grunt' instead of generic "
            f"'orc' for deterministic spawns. Add 'uses_orc_family: true' to "
            f"metadata if orc family variety is intentional.\n"
            f"Violations: {sorted(set(violations))}"
        )
