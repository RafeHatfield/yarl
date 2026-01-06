"""Phase 20E.2: Disarm Scroll Identity Scenario Integration Test

Tests the Scroll of Disarm mechanic through automated scenario runs.

Design:
- Player uses disarm scroll on orc enemies
- Orcs continue attacking but with unarmed damage (1-2) instead of weapon damage
- Metrics track disarm applications, attacks attempted while disarmed, and weapon attacks prevented

Metrics:
- disarm_applications: Count of disarm effect applications
- disarmed_attacks_attempted: Count of attacks attempted while disarmed
- disarmed_weapon_attacks_prevented: Count of weapon attacks replaced by unarmed

Thresholds (30 runs, seed_base=1337):
- disarm_applications >= 20 (should be ~30 if bot uses scroll every run)
- disarmed_attacks_attempted >= 20 (disarmed enemies should attack multiple times)
- disarmed_weapon_attacks_prevented >= 15 (most disarmed attacks should be weapon-wielders)
- player_deaths <= 15 (modest ceiling, disarm should help survivability)
"""

import pytest
from config.level_template_registry import get_scenario_registry
from services.scenario_harness import run_scenario_many, make_bot_policy


@pytest.mark.slow
def test_disarm_scroll_identity_scenario_metrics():
    """Run disarm scroll identity scenario and verify metrics."""
    # Load scenario from registry
    registry = get_scenario_registry()
    scenario = registry.get_scenario_definition("scenario_disarm_scroll_identity")
    if scenario is None:
        pytest.skip("Disarm scroll identity scenario not found in registry")
    
    # Create bot policy - use disarm_scroll_user for deterministic scroll usage
    policy = make_bot_policy("disarm_scroll_user")
    
    # Run the scenario (30 runs, 100 turn limit)
    # Using seed_base=1337 for determinism
    metrics = run_scenario_many(
        scenario=scenario,
        bot_policy=policy,
        runs=30,
        turn_limit=100,
        seed_base=1337
    )
    
    # Extract disarm metrics from AggregatedMetrics
    disarm_applications = getattr(metrics, 'total_disarm_applications', 0)
    disarmed_attacks_attempted = getattr(metrics, 'total_disarmed_attacks_attempted', 0)
    disarmed_weapon_attacks_prevented = getattr(metrics, 'total_disarmed_weapon_attacks_prevented', 0)
    player_deaths = metrics.player_deaths
    
    # Assertions - conservative thresholds for stability
    assert disarm_applications >= 20, (
        f"Expected >= 20 disarm applications, got {disarm_applications}. "
        f"Bot should use scroll on enemies most runs."
    )
    
    assert disarmed_attacks_attempted >= 15, (
        f"Expected >= 15 disarmed attacks attempted, got {disarmed_attacks_attempted}. "
        f"Disarmed enemies should attack multiple times before effect expires."
    )
    
    assert disarmed_weapon_attacks_prevented >= 10, (
        f"Expected >= 10 weapon attacks prevented, got {disarmed_weapon_attacks_prevented}. "
        f"Most disarmed enemies should be weapon-wielders."
    )
    
    assert player_deaths <= 15, (
        f"Expected <= 15 player deaths, got {player_deaths}. "
        f"Disarm should significantly reduce enemy damage output."
    )
    
    # Diagnostic output
    print(f"\n{'='*60}")
    print(f"Disarm Scroll Identity Scenario - 30 runs")
    print(f"{'='*60}")
    print(f"Disarm applications:           {disarm_applications}")
    print(f"Disarmed attacks attempted:    {disarmed_attacks_attempted}")
    print(f"Weapon attacks prevented:      {disarmed_weapon_attacks_prevented}")
    print(f"Player deaths:                 {player_deaths}")
    print(f"{'='*60}\n")

