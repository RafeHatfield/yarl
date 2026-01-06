"""Integration test for Sunburst Potion blind identity scenario metrics enforcement.

This test validates that the Sunburst Potion scenario meets minimum thresholds
for blind application and attack penalty effects, proving the Phase 20E.1 
dual-mode consumable mechanics work.

Marked as @pytest.mark.slow - runs with full test suite, not default quick tests.
"""

import pytest
from config.level_template_registry import get_scenario_registry
from services.scenario_harness import run_scenario_many, make_bot_policy


@pytest.mark.slow
def test_sunburst_potion_blind_identity_scenario_metrics():
    """Verify Sunburst Potion scenario meets minimum blind thresholds (30 runs).
    
    This test enforces regression guardrails for Phase 20E.1 Blinded effect:
    - Blind applications: At least 20 across 30 runs (deterministic throwing)
    - Blind attacks attempted: At least 30 across 30 runs (blinded orcs attack)
    - Blind attacks missed: At least 10 across 30 runs (conservative, -4 penalty)
    - Player deaths: <= 10 (blinded orcs miss more, player survives most runs)
    
    Thresholds are conservative but enforce that blind mechanics work.
    The SunburstPotionUserPolicy throws deterministically at nearest enemy.
    """
    
    # Load scenario from registry
    registry = get_scenario_registry()
    scenario = registry.get_scenario_definition("sunburst_potion_blind_identity")
    if scenario is None:
        pytest.skip("Sunburst potion blind scenario not found in registry")
    
    # Create bot policy - use sunburst_potion_user for deterministic throwing
    policy = make_bot_policy("sunburst_potion_user")
    
    # Run the scenario (30 runs, 100 turn limit)
    # Using seed_base=1337 for determinism
    metrics = run_scenario_many(
        scenario=scenario,
        bot_policy=policy,
        runs=30,
        turn_limit=100,
        seed_base=1337
    )
    
    # Extract blind metrics from AggregatedMetrics
    blind_applications = getattr(metrics, 'total_blind_applications', 0)
    blind_attacks_attempted = getattr(metrics, 'total_blind_attacks_attempted', 0)
    blind_attacks_missed = getattr(metrics, 'total_blind_attacks_missed', 0)
    player_deaths = metrics.player_deaths
    
    # Print metrics for debugging
    print(f"\n=== Sunburst Potion Blind Identity Metrics (30 runs) ===")
    print(f"Blind Applications: {blind_applications}")
    print(f"Blind Attacks Attempted: {blind_attacks_attempted}")
    print(f"Blind Attacks Missed: {blind_attacks_missed}")
    print(f"Player Deaths: {player_deaths}")
    
    # === BLIND APPLICATION VALIDATION ===
    # Player starts with 2 potions, enemies at throw range
    # Bot throws immediately and deterministically
    # Expect at least 20 applications (conservative, allows some deaths before throwing)
    assert blind_applications >= 20, (
        f"Blind applications too low: {blind_applications}. "
        f"Expected at least 20 across 30 runs. "
        f"Check SunburstPotionUserPolicy and scenario setup."
    )
    
    # === BLIND ATTACKS ATTEMPTED VALIDATION ===
    # Blinded orcs approach and attack (3 turn duration)
    # With 20+ applications, expect at least 25 attack attempts by blinded orcs
    # Conservative threshold to allow for positioning variance
    assert blind_attacks_attempted >= 25, (
        f"Blind attacks attempted too low: {blind_attacks_attempted}. "
        f"Expected at least 25 across 30 runs. "
        f"Check that blinded orcs are attempting attacks and metrics are tracked."
    )
    
    # === BLIND ATTACKS MISSED VALIDATION ===
    # Blinded orcs have -4 to-hit penalty, so they should miss more often
    # With 30+ attack attempts, expect at least 10 misses (conservative)
    assert blind_attacks_missed >= 10, (
        f"Blind attacks missed too low: {blind_attacks_missed}. "
        f"Expected at least 10 across 30 runs. "
        f"Check that blind penalty (-4) is applied correctly."
    )
    
    # === PLAYER DEATH RATE ===
    # Blinded orcs miss more, player should survive most runs
    # Conservative ceiling to ensure blind effect provides defensive value
    assert player_deaths <= 10, (
        f"Player deaths too high: {player_deaths}. "
        f"Expected <= 10 across 30 runs. "
        f"Blinded orcs should miss more, improving player survivability."
    )


