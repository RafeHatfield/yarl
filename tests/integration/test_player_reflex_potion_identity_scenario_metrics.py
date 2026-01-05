"""Integration test for Adrenaline Potion reflex identity scenario metrics.

This test validates that the Reflex Potion scenario meets minimum thresholds
for potion use and bonus attacks, proving the Phase 20C.1 Reflex mechanics work.
"""

import pytest
from config.level_template_registry import get_scenario_registry
from services.scenario_harness import run_scenario_many, make_bot_policy


@pytest.mark.slow
def test_player_reflex_potion_identity_scenario_metrics():
    """Verify Reflex Potion scenario meets minimum thresholds (30 runs).
    
    This test enforces regression guardrails for Phase 20C.1 Reflex:
    - reflex_potions_used: At least 25 across 30 runs (bot drinks potion)
    - bonus_attacks_while_reflexes_active: At least 20 across 30 runs
    """
    
    # Load scenario from registry
    registry = get_scenario_registry()
    scenario = registry.get_scenario_definition("player_reflex_potion_identity")
    if scenario is None:
        pytest.skip("Reflex potion scenario not found in registry")
    
    # Create bot policy (reflex_potion_user uses adrenaline potion turn 1, then fights)
    policy = make_bot_policy("reflex_potion_user")
    
    # Run the scenario (30 runs, 100 turn limit, seed_base=1337 for determinism)
    metrics = run_scenario_many(
        scenario=scenario,
        bot_policy=policy,
        runs=30,
        turn_limit=100,
        seed_base=1337
    )
    
    # Extract reflex metrics from AggregatedMetrics
    reflex_potions_used = getattr(metrics, 'total_reflex_potions_used', 0)
    bonus_attacks = getattr(metrics, 'total_bonus_attacks_while_reflexes_active', 0)
    player_deaths = metrics.player_deaths
    
    # Print metrics for debugging
    print(f"\n=== Reflex Potion Identity Metrics (30 runs) ===")
    print(f"Reflex Potions Used: {reflex_potions_used}")
    print(f"Bonus Attacks (while active): {bonus_attacks}")
    print(f"Player Deaths: {player_deaths}")
    
    # === REFLEX POTION USE VALIDATION ===
    # 30 runs, 1 potion per run
    assert reflex_potions_used >= 25, (
        f"Reflex potions used too low: {reflex_potions_used}. "
        f"Expected at least 25 across 30 runs. "
        f"Check that bot is picking up and using adrenaline_potion."
    )
    
    # === BONUS ATTACKS VALIDATION ===
    # +50% bonus attack chance for 15 turns
    # Expect at least 20 bonus attacks across 30 runs (very conservative)
    assert bonus_attacks >= 20, (
        f"Bonus attacks while active too low: {bonus_attacks}. "
        f"Expected at least 20 across 30 runs. "
        f"Check that lightning_reflexes is boosting speed bonus."
    )

