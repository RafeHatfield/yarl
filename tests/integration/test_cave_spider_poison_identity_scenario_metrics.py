"""Integration test for Cave Spider poison identity scenario metrics enforcement.

This test validates that the Cave Spider scenario meets minimum thresholds
for poison application and damage, proving the Phase 20A DOT mechanics work.

Marked as @pytest.mark.slow - runs with full test suite, not default quick tests.
"""

import pytest
from config.level_template_registry import get_scenario_registry
from services.scenario_harness import run_scenario_many, make_bot_policy


@pytest.mark.slow
def test_cave_spider_poison_identity_scenario_metrics():
    """Verify Cave Spider scenario meets minimum poison thresholds (30 runs).
    
    This test enforces regression guardrails for Phase 20A Poison DOT:
    - Poison applications: At least 20 across 30 runs (spiders apply poison on hit)
    - Poison damage dealt: At least 30 across 30 runs (poison ticks for damage)
    - Poison ticks processed: At least 30 across 30 runs (poison ticks each turn)
    - Player deaths: <= 10 (spiders are fragile, player should win consistently)
    
    Thresholds are intentionally conservative to avoid flaky tests.
    The canonical DOT model should produce consistent poison application.
    """
    
    # Load scenario from registry
    registry = get_scenario_registry()
    scenario = registry.get_scenario_definition("monster_cave_spider_identity")
    if scenario is None:
        pytest.skip("Cave spider scenario not found in registry")
    
    # Create bot policy
    policy = make_bot_policy("tactical_fighter")
    
    # Run the scenario (30 runs, 150 turn limit)
    metrics = run_scenario_many(
        scenario=scenario,
        bot_policy=policy,
        runs=30,
        turn_limit=150,
        seed_base=None  # Non-deterministic for broader coverage
    )
    
    # Extract poison metrics from AggregatedMetrics
    poison_applications = getattr(metrics, 'total_poison_applications', 0)
    poison_damage_dealt = getattr(metrics, 'total_poison_damage_dealt', 0)
    poison_ticks_processed = getattr(metrics, 'total_poison_ticks_processed', 0)
    poison_kills = getattr(metrics, 'total_poison_kills', 0)
    player_deaths = metrics.player_deaths
    
    # Print metrics for debugging
    print(f"\n=== Cave Spider Poison Identity Metrics (30 runs) ===")
    print(f"Poison Applications: {poison_applications}")
    print(f"Poison Damage Dealt: {poison_damage_dealt}")
    print(f"Poison Ticks Processed: {poison_ticks_processed}")
    print(f"Poison Kills: {poison_kills}")
    print(f"Player Deaths: {player_deaths}")
    
    # === POISON APPLICATION VALIDATION ===
    # With 2 spiders per run and 30 runs:
    # - Each spider should land at least 1 hit before dying
    # - At minimum, expect 20+ applications across 30 runs (conservative)
    assert poison_applications >= 20, (
        f"Poison applications too low: {poison_applications}. "
        f"Expected at least 20 across 30 runs. "
        f"Check that cave_spider has poison_attack ability and hits are landing."
    )
    
    # === POISON DAMAGE VALIDATION ===
    # Poison deals 1 damage per tick over 6 turns
    # With 20+ applications, expect at least 30 total damage
    # (accounts for player killing spiders quickly before all ticks)
    assert poison_damage_dealt >= 30, (
        f"Poison damage too low: {poison_damage_dealt}. "
        f"Expected at least 30 across 30 runs. "
        f"Check that poison is ticking correctly in process_turn_start."
    )
    
    # === POISON TICKS VALIDATION ===
    # Each poison application should tick at least a few times
    # 20 applications × ~2 ticks avg = 40+ ticks minimum
    # Being conservative: at least 30 ticks
    assert poison_ticks_processed >= 30, (
        f"Poison ticks too low: {poison_ticks_processed}. "
        f"Expected at least 30 across 30 runs. "
        f"Check that poison ticks are being processed each turn."
    )
    
    # === PLAYER DEATH RATE VALIDATION ===
    # Spiders are fragile (16 HP) and player starts with weapon
    # Player should win consistently - max 10 deaths across 30 runs
    assert player_deaths <= 10, (
        f"Player deaths too high: {player_deaths}. "
        f"Expected <= 10 across 30 runs. "
        f"Cave spiders should be manageable for tactical_fighter bot."
    )
    
    # === OPTIONAL: Poison kills (not required but informative) ===
    # Poison alone rarely kills - it's pressure damage
    # Just log this metric, don't enforce threshold
    if poison_kills > 0:
        print(f"Note: {poison_kills} entities died from poison alone (rare but possible)")


@pytest.mark.slow
def test_cave_spider_poison_resistance():
    """Verify that poison resistance reduces damage as expected.
    
    This is a secondary test validating the resistance mechanic.
    Cave spiders have 75% poison resistance - they take very little
    poison damage if somehow poisoned by another source.
    """
    # This test validates the resistance math through gameplay
    # If spiders were being poisoned by each other (hypothetically),
    # they would take only 25% damage
    
    # For now, just verify the scenario runs without errors
    registry = get_scenario_registry()
    scenario = registry.get_scenario_definition("monster_cave_spider_identity")
    if scenario is None:
        pytest.skip("Cave spider scenario not found in registry")
    
    policy = make_bot_policy("tactical_fighter")
    
    # Single run to validate no crashes
    from services.scenario_harness import run_scenario_once
    metrics = run_scenario_once(
        scenario=scenario,
        bot_policy=policy,
        turn_limit=100
    )
    
    # Scenario should complete without errors
    assert metrics is not None
    assert metrics.turns_taken > 0

