"""Integration test for Web Spider slow identity scenario metrics enforcement.

This test validates that the Web Spider scenario meets minimum thresholds
for slow application and skipped turns, proving the Phase 20C.1 Slow mechanics work.
"""

import pytest
from config.level_template_registry import get_scenario_registry
from services.scenario_harness import run_scenario_many, make_bot_policy


@pytest.mark.slow
def test_web_spider_slow_identity_scenario_metrics():
    """Verify Web Spider scenario meets minimum slow thresholds (30 runs).
    
    This test enforces regression guardrails for Phase 20C.1 Slow:
    - slow_applications: At least 20 across 30 runs (spiders apply slow on hit)
    - slow_turns_skipped: At least 40 across 30 runs (slow skips every other turn)
    - player_deaths: <= 10 (player should win consistently)
    """
    
    # Load scenario from registry
    registry = get_scenario_registry()
    scenario = registry.get_scenario_definition("monster_web_spider_identity")
    if scenario is None:
        pytest.skip("Web spider scenario not found in registry")
    
    # Create bot policy
    policy = make_bot_policy("tactical_fighter")
    
    # Run the scenario (30 runs, 150 turn limit, seed_base=1337 for determinism)
    metrics = run_scenario_many(
        scenario=scenario,
        bot_policy=policy,
        runs=30,
        turn_limit=150,
        seed_base=1337
    )
    
    # Extract slow metrics from AggregatedMetrics
    # Metrics are prefixed with 'total_' in AggregatedMetrics
    slow_applications = getattr(metrics, 'total_slow_applications', 0)
    slow_turns_skipped = getattr(metrics, 'total_slow_turns_skipped', 0)
    player_deaths = metrics.player_deaths
    
    # Print metrics for debugging
    print(f"\n=== Web Spider Slow Identity Metrics (30 runs) ===")
    print(f"Slow Applications: {slow_applications}")
    print(f"Slow Turns Skipped: {slow_turns_skipped}")
    print(f"Player Deaths: {player_deaths}")
    
    # === SLOW APPLICATION VALIDATION ===
    # With 2 spiders per run and 30 runs:
    # Expect 20+ applications across 30 runs (conservative)
    assert slow_applications >= 20, (
        f"Slow applications too low: {slow_applications}. "
        f"Expected at least 20 across 30 runs. "
        f"Check that web_spider has web_spit ability and hits are landing."
    )
    
    # === SLOW TURNS SKIPPED VALIDATION ===
    # Each slow application lasts for 6 turns, meaning 3 turns skipped.
    # 20 applications × 2-3 skips avg = 40+ skips minimum
    assert slow_turns_skipped >= 40, (
        f"Slow turns skipped too low: {slow_turns_skipped}. "
        f"Expected at least 40 across 30 runs. "
        f"Check that slow effect is skipping turns correctly."
    )
    
    # === PLAYER DEATH RATE VALIDATION ===
    assert player_deaths <= 10, (
        f"Player deaths too high: {player_deaths}. "
        f"Expected <= 10 across 30 runs."
    )

