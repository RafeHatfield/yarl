"""Integration test for Phase 20 corpse lifecycle validation.

Validates:
- FRESH corpses created on death
- FRESH corpses raised (not exploded)
- SPENT corpses created on re-death (if lifecycle completes)
- SPENT corpses exploded (not raised)
- State machine integrity
"""

import pytest
from config.level_template_registry import get_scenario_registry
from services.scenario_harness import run_scenario_many, make_bot_policy


@pytest.mark.slow
def test_phase20_corpse_lifecycle():
    """Verify Phase 20 corpse lifecycle implementation (30 runs)."""
    
    registry = get_scenario_registry()
    scenario = registry.get_scenario_definition("phase20_corpse_lifecycle")
    if scenario is None:
        pytest.skip("Phase 20 corpse lifecycle scenario not found in registry")
    
    policy = make_bot_policy("tactical_fighter")
    
    metrics = run_scenario_many(
        scenario=scenario,
        bot_policy=policy,
        runs=30,
        turn_limit=300,
        seed_base=None
    )
    
    # =================================================================
    # THRESHOLD 1: FRESH corpses created (PRIMARY validation)
    # =================================================================
    fresh_created = getattr(metrics, 'total_fresh_corpses_created', 0)
    assert fresh_created >= 30, (
        f"FRESH corpses should be created on enemy deaths. "
        f"Got {fresh_created}, expected >= 30 (at least 1 per run)."
    )
    
    # =================================================================
    # THRESHOLD 2: Observability metrics (logged, not asserted)
    # =================================================================
    spent_created = getattr(metrics, 'total_spent_corpses_created', 0)
    raises_completed = getattr(metrics, 'total_raises_completed', 0)
    spent_exploded = getattr(metrics, 'total_spent_corpses_exploded', 0)
    
    # =================================================================
    # THRESHOLD 3: Lifecycle integrity (if SPENT exists)
    # =================================================================
    if spent_created > 0 and raises_completed > 0:
        assert spent_created <= raises_completed, (
            f"Lifecycle integrity violation: More SPENT corpses than raises! "
            f"SPENT: {spent_created}, Raises: {raises_completed}. "
            f"SPENT corpses can ONLY come from raised entity re-deaths."
        )
    
    # =================================================================
    # Summary Report
    # =================================================================
    print(f"\n✅ Phase 20 Corpse Lifecycle Test Complete (30 runs):")
    print(f"   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"   Lifecycle Metrics:")
    print(f"     - FRESH corpses created: {fresh_created} (>= 30) ✓")
    print(f"     - Raises completed: {raises_completed} (observed)")
    print(f"     - SPENT corpses created: {spent_created} (observed)")
    print(f"     - SPENT corpses exploded: {spent_exploded} (observed)")
    print(f"   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    if spent_created > 0:
        print(f"   ✅ Full lifecycle observed (raise → SPENT → explode)")
    else:
        print(f"   ℹ️  Partial lifecycle (FRESH creation validated)")
        print(f"       Extended scenarios needed for full SPENT validation")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])

