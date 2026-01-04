"""Integration test for Fire Beetle burning identity scenario metrics enforcement.

This test validates that the Fire Beetle scenario meets minimum thresholds
for burning application and damage, proving the Phase 20B.1 DOT mechanics work.

Marked as @pytest.mark.slow - runs with full test suite, not default quick tests.
"""

import pytest
from config.level_template_registry import get_scenario_registry
from services.scenario_harness import run_scenario_many, make_bot_policy


@pytest.mark.slow
def test_fire_beetle_burning_identity_scenario_metrics():
    """Verify Fire Beetle scenario meets minimum burning thresholds (30 runs).
    
    This test enforces regression guardrails for Phase 20B.1 Burning DOT:
    - Burning applications: At least 20 across 30 runs (beetles apply burning on hit)
    - Burning damage dealt: At least 30 across 30 runs (burning ticks for damage)
    - Burning ticks processed: At least 30 across 30 runs (burning ticks each turn)
    - Player deaths: <= 15 (beetles are fragile, player should win mostly)
    
    Thresholds are intentionally conservative to avoid flaky tests.
    The canonical DOT model should produce consistent burning application.
    """
    
    # Load scenario from registry
    registry = get_scenario_registry()
    scenario = registry.get_scenario_definition("monster_fire_beetle_identity")
    if scenario is None:
        pytest.skip("Fire beetle scenario not found in registry")
    
    # Create bot policy
    policy = make_bot_policy("tactical_fighter")
    
    # Run the scenario (30 runs, 150 turn limit)
    # Using seed_base=1337 for determinism as requested
    metrics = run_scenario_many(
        scenario=scenario,
        bot_policy=policy,
        runs=30,
        turn_limit=150,
        seed_base=1337
    )
    
    # Extract burning metrics from AggregatedMetrics
    burning_applications = getattr(metrics, 'total_burning_applications', 0)
    burning_damage_dealt = getattr(metrics, 'total_burning_damage_dealt', 0)
    burning_ticks_processed = getattr(metrics, 'total_burning_ticks_processed', 0)
    burning_kills = getattr(metrics, 'total_burning_kills', 0)
    player_deaths = metrics.player_deaths
    
    # Print metrics for debugging
    print(f"\n=== Fire Beetle Burning Identity Metrics (30 runs) ===")
    print(f"Burning Applications: {burning_applications}")
    print(f"Burning Damage Dealt: {burning_damage_dealt}")
    print(f"Burning Ticks Processed: {burning_ticks_processed}")
    print(f"Burning Kills: {burning_kills}")
    print(f"Player Deaths: {player_deaths}")
    
    # === BURNING APPLICATION VALIDATION ===
    # With 3 beetles per run and 30 runs:
    # - At minimum, expect 20+ applications across 30 runs (conservative)
    assert burning_applications >= 20, (
        f"Burning applications too low: {burning_applications}. "
        f"Expected at least 20 across 30 runs. "
        f"Check that fire_beetle has burning_attack ability and hits are landing."
    )
    
    # === BURNING DAMAGE VALIDATION ===
    # Burning deals 1 damage per tick over 4 turns
    # With 20+ applications, expect at least 30 total damage
    assert burning_damage_dealt >= 30, (
        f"Burning damage too low: {burning_damage_dealt}. "
        f"Expected at least 30 across 30 runs. "
        f"Check that burning is ticking correctly in process_turn_start."
    )
    
    # === BURNING TICKS VALIDATION ===
    # Each burning application should tick at least a few times
    assert burning_ticks_processed >= 30, (
        f"Burning ticks too low: {burning_ticks_processed}. "
        f"Expected at least 30 across 30 runs. "
        f"Check that burning ticks are being processed each turn."
    )
    
    # === PLAYER DEATH RATE VALIDATION ===
    # Beetles are fragile (12 HP) but there are 3 of them
    # Player should win consistently - max 15 deaths across 30 runs
    assert player_deaths <= 15, (
        f"Player deaths too high: {player_deaths}. "
        f"Expected <= 15 across 30 runs. "
        f"Fire beetles should be manageable for tactical_fighter bot."
    )

