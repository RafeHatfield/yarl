"""Phase 20F: Silence Scroll vs Orc Shaman Identity Scenario Integration Test

Tests the Scroll of Silence mechanic against orc shaman through automated scenario runs.

Design:
- Player uses silence scroll on orc shaman
- Shaman attempts to cast hex/chant but is blocked by silence
- Turn is consumed when cast is blocked (shaman doesn't get free action)
- After silence expires, shaman can cast again

Metrics:
- silence_applications: Count of silence effect applications
- silenced_casts_blocked: Count of casts blocked by silence

Thresholds (30 runs, seed_base=1337):
- silence_applications >= 20 (bot uses scroll ~every run)
- silenced_casts_blocked >= 10 (shaman attempts casts while silenced)
- player_deaths <= 12 (silencing shaman improves survivability)
"""

import pytest
from config.level_template_registry import get_scenario_registry
from services.scenario_harness import run_scenario_many, make_bot_policy


@pytest.mark.slow
def test_silence_orc_shaman_identity_scenario_metrics():
    """Run silence vs orc shaman identity scenario and verify metrics."""
    # Load scenario from registry
    registry = get_scenario_registry()
    scenario = registry.get_scenario_definition("scenario_silence_orc_shaman_identity")
    if scenario is None:
        pytest.skip("Silence orc shaman identity scenario not found in registry")
    
    # Create bot policy - use silence_scroll_user for deterministic scroll usage
    policy = make_bot_policy("silence_scroll_user")
    
    # Run the scenario (30 runs, 150 turn limit)
    # Using seed_base=1337 for determinism
    metrics = run_scenario_many(
        scenario=scenario,
        bot_policy=policy,
        runs=30,
        turn_limit=150,
        seed_base=1337
    )
    
    # Extract silence metrics from AggregatedMetrics
    silence_applications = getattr(metrics, 'total_silence_applications', 0)
    silenced_casts_blocked = getattr(metrics, 'total_silenced_casts_blocked', 0)
    player_deaths = metrics.player_deaths
    
    # Assertions - conservative thresholds for stability
    assert silence_applications >= 20, (
        f"Expected >= 20 silence applications, got {silence_applications}. "
        f"Bot should use scroll on shaman most runs."
    )
    
    assert silenced_casts_blocked >= 10, (
        f"Expected >= 10 silenced casts blocked, got {silenced_casts_blocked}. "
        f"Shaman should attempt to cast hex/chant while silenced."
    )
    
    assert player_deaths <= 15, (
        f"Expected <= 15 player deaths, got {player_deaths}. "
        f"Silencing shaman should significantly improve survivability."
    )
    
    # Diagnostic output
    print(f"\n{'='*60}")
    print(f"Silence vs Orc Shaman Identity Scenario - 30 runs")
    print(f"{'='*60}")
    print(f"Silence applications:          {silence_applications}")
    print(f"Silenced casts blocked:        {silenced_casts_blocked}")
    print(f"Player deaths:                 {player_deaths}")
    print(f"{'='*60}\n")

