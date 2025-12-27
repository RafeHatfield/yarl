"""Integration test for Orc Shaman identity scenario metrics enforcement.

This test validates that the Orc Shaman scenario meets minimum thresholds
for ability usage, proving the mechanics are working as designed.

Marked as @pytest.mark.slow - runs with full test suite, not default quick tests.
"""

import pytest
from config.level_template_registry import get_scenario_registry
from services.scenario_harness import run_scenario_many, make_bot_policy


@pytest.mark.slow
def test_orc_shaman_identity_scenario_metrics():
    """Verify Orc Shaman scenario meets minimum thresholds (30 runs).
    
    This test enforces regression guardrails for:
    - Hex casting frequency
    - Chant usage frequency  
    - Chant interruptibility (counterplay)
    - Chant completion (not over-interrupted)
    
    Thresholds are derived from Phase 19 design spec:
    - Hex: at least 1 per run (30 total)
    - Chant: at least 50% of runs (15 total)
    - Interrupts: at least 5 across 30 runs (proves counterplay viable)
    - Expiries: at least 5 across 30 runs (proves not all interrupted)
    """
    
    # Load scenario from registry
    registry = get_scenario_registry()
    scenario = registry.get_scenario_definition("monster_orc_shaman_identity")
    if scenario is None:
        pytest.skip("Orc Shaman scenario not found in registry")
    
    # Create bot policy
    policy = make_bot_policy("tactical_fighter")
    
    # Run the scenario (30 runs, 200 turn limit)
    metrics = run_scenario_many(
        scenario=scenario,
        bot_policy=policy,
        runs=30,
        turn_limit=200,
        seed_base=None  # Non-deterministic for broader coverage
    )
    
    # Extract metrics from AggregatedMetrics object
    # Metrics are stored as attributes on the AggregatedMetrics dataclass
    # Note: Aggregated metrics use "total_" prefix
    
    # THRESHOLD 1: Hex casting frequency
    hex_casts = getattr(metrics, 'total_shaman_hex_casts', 0)
    assert hex_casts >= 30, (
        f"Shaman should cast hex at least once per run (30 runs). "
        f"Got {hex_casts}, expected >= 30"
    )
    
    # THRESHOLD 2: Chant usage frequency
    chant_starts = getattr(metrics, 'total_shaman_chant_starts', 0)
    assert chant_starts >= 15, (
        f"Shaman should start chant in at least 50% of runs (15/30). "
        f"Got {chant_starts}, expected >= 15"
    )
    
    # THRESHOLD 3: Chant interruptibility (counterplay exists)
    chant_interrupts = getattr(metrics, 'total_shaman_chant_interrupts', 0)
    assert chant_interrupts >= 5, (
        f"Counterplay should be viable - at least 5 interrupts across 30 runs. "
        f"Got {chant_interrupts}, expected >= 5. "
        f"This proves player can interrupt chant with ranged damage."
    )
    
    # THRESHOLD 4: Chant completion (not over-interrupted)
    chant_expiries = getattr(metrics, 'total_shaman_chant_expiries', 0)
    assert chant_expiries >= 5, (
        f"Some chants should complete naturally - at least 5 across 30 runs. "
        f"Got {chant_expiries}, expected >= 5. "
        f"This proves chants aren't trivially interrupted every time."
    )
    
    # SANITY CHECK: All started chants should either be interrupted or expire
    # Allow for minor drift (±1-2) due to edge cases:
    # - Shaman dies while channeling (chant started but no outcome)
    # - Scenario ends mid-channel (turn limit reached)
    total_outcomes = chant_interrupts + chant_expiries
    diff = abs(total_outcomes - chant_starts)
    assert diff <= 2, (
        f"Started chants should nearly equal outcomes (allow ±2 for edge cases). "
        f"Starts: {chant_starts}, Interrupts: {chant_interrupts}, "
        f"Expiries: {chant_expiries}, Total outcomes: {total_outcomes}, Diff: {diff}. "
        f"Large diff indicates channeling state machine bug."
    )
    
    # SUCCESS: All thresholds met
    print(f"\n✅ Orc Shaman scenario metrics validated:")
    print(f"   - Hex casts: {hex_casts} (>= 30)")
    print(f"   - Chant starts: {chant_starts} (>= 15)")
    print(f"   - Chant interrupts: {chant_interrupts} (>= 5)")
    print(f"   - Chant expiries: {chant_expiries} (>= 5)")
    print(f"   - Chant accounting: {total_outcomes} starts = {chant_interrupts} interrupts + {chant_expiries} expiries")


if __name__ == '__main__':
    # Allow running this test directly for debugging
    pytest.main([__file__, '-v', '-s'])

