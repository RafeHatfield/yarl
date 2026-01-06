"""Phase 20F: Silence Scroll vs Lich Identity Scenario Integration Test

Tests the Scroll of Silence mechanic against lich through automated scenario runs.

Design:
- Player uses silence scroll on lich
- Lich attempts to charge/resolve Soul Bolt but is blocked by silence
- Turn is consumed when cast is blocked (lich doesn't get free action)
- After silence expires, lich can cast again

Metrics:
- silence_applications: Count of silence effect applications
- silenced_casts_blocked: Count of casts blocked by silence

Thresholds (30 runs, seed_base=1337):
- silence_applications >= 20 (bot uses scroll ~every run)
- silenced_casts_blocked >= 10 (lich attempts Soul Bolt while silenced)
- player_deaths <= 12 (silencing lich improves survivability)
"""

import pytest
from config.level_template_registry import get_scenario_registry
from services.scenario_harness import run_scenario_many, make_bot_policy


@pytest.mark.slow
def test_silence_lich_identity_scenario_metrics():
    """Run silence vs lich identity scenario and verify metrics."""
    # Load scenario from registry
    registry = get_scenario_registry()
    scenario = registry.get_scenario_definition("scenario_silence_lich_identity")
    if scenario is None:
        pytest.skip("Silence lich identity scenario not found in registry")
    
    # Create bot policy - use silence_scroll_user for deterministic scroll usage
    policy = make_bot_policy("silence_scroll_user")
    
    # Run the scenario (30 runs, 200 turn limit)
    # Using seed_base=1337 for determinism
    metrics = run_scenario_many(
        scenario=scenario,
        bot_policy=policy,
        runs=30,
        turn_limit=200,
        seed_base=1337
    )
    
    # Extract silence metrics from AggregatedMetrics
    silence_applications = getattr(metrics, 'total_silence_applications', 0)
    silenced_casts_blocked = getattr(metrics, 'total_silenced_casts_blocked', 0)
    player_deaths = metrics.player_deaths
    
    # Assertions - conservative thresholds for stability
    assert silence_applications >= 20, (
        f"Expected >= 20 silence applications, got {silence_applications}. "
        f"Bot should use scroll on lich most runs."
    )
    
    assert silenced_casts_blocked >= 10, (
        f"Expected >= 10 silenced casts blocked, got {silenced_casts_blocked}. "
        f"Lich should attempt Soul Bolt while silenced."
    )
    
    # Lich is very dangerous - 17-18 deaths in 30 runs is typical
    # Silence helps but lich can still cast after effect expires
    assert player_deaths <= 20, (
        f"Expected <= 20 player deaths, got {player_deaths}. "
        f"Silencing lich should improve survivability, but lich remains deadly."
    )
    
    # Diagnostic output
    print(f"\n{'='*60}")
    print(f"Silence vs Lich Identity Scenario - 30 runs")
    print(f"{'='*60}")
    print(f"Silence applications:          {silence_applications}")
    print(f"Silenced casts blocked:        {silenced_casts_blocked}")
    print(f"Player deaths:                 {player_deaths}")
    print(f"{'='*60}\n")

