"""Integration test for Bone Necromancer identity scenario metrics enforcement.

This test validates that the Bone Necromancer scenario meets minimum thresholds
for ability usage, proving the mechanics are working as designed.

Marked as @pytest.mark.slow - runs with full test suite, not default quick tests.
"""

import pytest
from config.level_template_registry import get_scenario_registry
from services.scenario_harness import run_scenario_many, make_bot_policy


@pytest.mark.slow
def test_bone_necromancer_identity_scenario_metrics():
    """Verify Bone Necromancer scenario meets minimum thresholds (30 runs).
    
    This test enforces regression guardrails for:
    - Bone raise frequency
    - Bone pile consumption
    - Bone thrall spawning
    - Bone seeking behavior
    - Safety radius enforcement
    
    Thresholds are derived from Phase 19 design spec:
    - Bone raise successes: at least 20 across 30 runs
    - Bone piles consumed: at least 20 across 30 runs
    - Bone thralls spawned: at least 20 across 30 runs
    - Bone seek moves: at least 10 across 30 runs (proves bone-seeking)
    - Player deaths: reasonable (bone necromancer is a moderate threat)
    """
    
    # Load scenario from registry
    registry = get_scenario_registry()
    scenario = registry.get_scenario_definition("monster_bone_necromancer_identity")
    if scenario is None:
        pytest.skip("Bone Necromancer scenario not found in registry")
    
    # Create bot policy
    policy = make_bot_policy("tactical_fighter")
    
    # Run the scenario (30 runs, 250 turn limit)
    metrics = run_scenario_many(
        scenario=scenario,
        bot_policy=policy,
        runs=30,
        turn_limit=250,
        seed_base=None  # Non-deterministic for broader coverage
    )
    
    # Extract metrics from AggregatedMetrics object
    # Metrics are stored as attributes on the AggregatedMetrics dataclass
    # Note: Aggregated metrics use "total_" prefix
    
    # THRESHOLD 1: Bone raise success frequency
    bone_raise_successes = getattr(metrics, 'total_bone_raise_successes', 0)
    assert bone_raise_successes >= 20, (
        f"Bone necromancer should successfully raise bone piles frequently (at least 20 across 30 runs). "
        f"Got {bone_raise_successes}, expected >= 20. "
        f"This proves bone raise mechanic is working."
    )
    
    # THRESHOLD 2: Bone pile consumption
    bone_piles_consumed = getattr(metrics, 'total_bone_piles_consumed', 0)
    assert bone_piles_consumed >= 20, (
        f"Bone piles should be consumed during raises (at least 20 across 30 runs). "
        f"Got {bone_piles_consumed}, expected >= 20. "
        f"This proves bone pile targeting is working."
    )
    
    # THRESHOLD 3: Bone thrall spawning
    bone_thralls_spawned = getattr(metrics, 'total_bone_thralls_spawned', 0)
    assert bone_thralls_spawned >= 20, (
        f"Bone thralls should be spawned from bone piles (at least 20 across 30 runs). "
        f"Got {bone_thralls_spawned}, expected >= 20. "
        f"This proves bone thrall summoning is working."
    )
    
    # THRESHOLD 4: Bone seeking movement
    bone_seek_moves = getattr(metrics, 'total_bone_seek_moves', 0)
    assert bone_seek_moves >= 10, (
        f"Bone necromancer should move toward out-of-range bone piles (at least 10 moves across 30 runs). "
        f"Got {bone_seek_moves}, expected >= 10. "
        f"This proves bone-seeking AI is working."
    )
    
    # THRESHOLD 5: Raise attempts should be >= successes (sanity)
    bone_raise_attempts = getattr(metrics, 'total_bone_raise_attempts', 0)
    assert bone_raise_attempts >= bone_raise_successes, (
        f"Bone raise attempts should be >= bone raise successes. "
        f"Attempts: {bone_raise_attempts}, Successes: {bone_raise_successes}. "
        f"This indicates a logic bug if violated."
    )
    
    # THRESHOLD 6: Player deaths should be in moderate range (not too easy, not too hard)
    player_deaths = getattr(metrics, 'player_deaths', 0)
    assert 5 <= player_deaths <= 20, (
        f"Player deaths should be in moderate range for 30 runs (bone necromancer is real threat but not overwhelming). "
        f"Got {player_deaths}, expected 5-20. "
        f"< 5 = too easy (bone necromancer ineffective), > 20 = too hard (overtuned)."
    )
    
    # OPTIONAL METRIC: Unsafe move blocks (safety radius enforcement)
    # This metric tracks how often necromancer wanted to seek bone pile but was
    # blocked by danger radius. Non-zero proves safety constraint is active.
    unsafe_blocks = getattr(metrics, 'total_necro_unsafe_move_blocks', 0)
    # Note: We don't assert on this - it's informational
    # Zero is fine (bone piles might always be reachable safely)
    
    # SANITY CHECK: Spawned thralls should match consumed piles (they should be equal)
    assert bone_thralls_spawned == bone_piles_consumed, (
        f"Bone thralls spawned should equal bone piles consumed (1:1 ratio). "
        f"Thralls: {bone_thralls_spawned}, Piles: {bone_piles_consumed}. "
        f"This indicates a logic bug if violated."
    )
    
    # SUCCESS: All thresholds met
    print(f"\n✅ Bone Necromancer scenario metrics validated:")
    print(f"   - Bone raise attempts: {bone_raise_attempts}")
    print(f"   - Bone raise successes: {bone_raise_successes} (>= 20)")
    print(f"   - Bone piles consumed: {bone_piles_consumed} (>= 20)")
    print(f"   - Bone thralls spawned: {bone_thralls_spawned} (>= 20)")
    print(f"   - Bone seek moves: {bone_seek_moves} (>= 10)")
    print(f"   - Unsafe move blocks: {unsafe_blocks} (informational)")
    print(f"   - Player deaths: {player_deaths} (5-20)")
    print(f"   - Turns per run (avg): {metrics.average_turns:.1f}")


if __name__ == '__main__':
    # Allow running this test directly for debugging
    pytest.main([__file__, '-v', '-s'])



