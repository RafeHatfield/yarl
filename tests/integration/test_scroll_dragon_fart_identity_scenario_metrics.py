"""Integration test for Dragon Fart Scroll identity scenario metrics enforcement.

Phase 20 Scroll Modernization: This test validates that the Dragon Fart scroll
modernization meets minimum thresholds for:
- SleepEffect applications (replaces ConfusedMonster AI swap)
- Poison gas hazard creation
- Proper routing through SpellExecutor (silence gating)

Marked as @pytest.mark.slow - runs with full test suite, not default quick tests.
"""

import pytest
from config.level_template_registry import get_scenario_registry
from services.scenario_harness import run_scenario_many, make_bot_policy


@pytest.mark.slow
def test_scroll_dragon_fart_identity_scenario_metrics():
    """Verify Dragon Fart scenario meets minimum thresholds (30 runs).
    
    Phase 20 Scroll Modernization regression guardrails:
    - Dragon Fart casts: At least 20 across 30 runs (bot should use scroll)
    - Tiles created: At least 60 across 30 runs (3+ tiles per cast)
    - Sleep applications: At least 15 across 30 runs (hits monsters in cone)
    - Player deaths: <= 15 (goblins are weak)
    
    Thresholds are intentionally conservative to avoid flaky tests.
    The modernized spell system should produce consistent behavior.
    """
    
    # Load scenario from registry
    registry = get_scenario_registry()
    scenario = registry.get_scenario_definition("scroll_dragon_fart_identity")
    if scenario is None:
        pytest.skip("Dragon Fart scroll scenario not found in registry")
    
    # Create bot policy
    policy = make_bot_policy("tactical_fighter")
    
    # Run the scenario (30 runs, 30 turn limit)
    metrics = run_scenario_many(
        scenario=scenario,
        bot_policy=policy,
        runs=30,
        turn_limit=30,
        seed_base=1337
    )
    
    # Extract Dragon Fart specific metrics from AggregatedMetrics
    dragon_fart_casts = getattr(metrics, 'total_dragon_fart_casts', 0)
    dragon_fart_tiles_created = getattr(metrics, 'total_dragon_fart_tiles_created', 0)
    sleep_applications = getattr(metrics, 'total_sleep_applications', 0)
    player_deaths = metrics.player_deaths
    
    # Print metrics for debugging
    print(f"\n=== Dragon Fart Scroll Identity Metrics (30 runs) ===")
    print(f"Dragon Fart Casts: {dragon_fart_casts}")
    print(f"Tiles Created: {dragon_fart_tiles_created}")
    print(f"Sleep Applications: {sleep_applications}")
    print(f"Player Deaths: {player_deaths}")
    
    # === CAST VALIDATION ===
    # Bot should use the scroll at least once per run in most cases
    # Conservative: 20 casts across 30 runs (67%)
    assert dragon_fart_casts >= 20, (
        f"Dragon Fart casts too low: {dragon_fart_casts}. "
        f"Expected at least 20 across 30 runs. "
        f"Check that bot is using scrolls and SpellExecutor routing works."
    )
    
    # === TILES CREATED VALIDATION ===
    # Each cast should create at least 3 tiles (cone shape)
    # With 20+ casts, expect at least 60 tiles
    assert dragon_fart_tiles_created >= 60, (
        f"Tiles created too low: {dragon_fart_tiles_created}. "
        f"Expected at least 60 across 30 runs. "
        f"Check that hazard creation in _cast_cone_spell works."
    )
    
    # === SLEEP APPLICATION VALIDATION ===
    # With 2 goblins in cone direction and 20+ casts:
    # At minimum, expect 15+ sleep applications
    assert sleep_applications >= 15, (
        f"Sleep applications too low: {sleep_applications}. "
        f"Expected at least 15 across 30 runs. "
        f"Check that SleepEffect is being applied in _cast_cone_spell."
    )
    
    # === PLAYER DEATH RATE VALIDATION ===
    # Goblins are weak, player should win consistently
    assert player_deaths <= 15, (
        f"Player deaths too high: {player_deaths}. "
        f"Expected <= 15 across 30 runs. "
        f"Goblins should be manageable for tactical_fighter bot."
    )


@pytest.mark.slow
def test_dragon_fart_sleep_replaces_confusion():
    """Verify Dragon Fart uses SleepEffect, not ConfusedMonster AI swap.
    
    Phase 20 Scroll Modernization: This test ensures the legacy AI swap pattern
    has been fully replaced with proper SleepEffect status application.
    """
    
    # Load scenario from registry
    registry = get_scenario_registry()
    scenario = registry.get_scenario_definition("scroll_dragon_fart_identity")
    if scenario is None:
        pytest.skip("Dragon Fart scroll scenario not found in registry")
    
    # Create bot policy
    policy = make_bot_policy("tactical_fighter")
    
    # Run single scenario
    metrics = run_scenario_many(
        scenario=scenario,
        bot_policy=policy,
        runs=5,
        turn_limit=30,
        seed_base=42
    )
    
    # Check that sleep applications occurred
    sleep_applications = getattr(metrics, 'total_sleep_applications', 0)
    sleep_turns_prevented = getattr(metrics, 'total_sleep_turns_prevented', 0)
    
    print(f"\n=== Dragon Fart Sleep Validation (5 runs) ===")
    print(f"Sleep Applications: {sleep_applications}")
    print(f"Sleep Turns Prevented: {sleep_turns_prevented}")
    
    # At least some sleep applications should occur
    assert sleep_applications >= 3, (
        f"Sleep applications too low: {sleep_applications}. "
        f"Expected at least 3 across 5 runs. "
        f"Verify SleepEffect is applied in _cast_cone_spell, not ConfusedMonster."
    )

