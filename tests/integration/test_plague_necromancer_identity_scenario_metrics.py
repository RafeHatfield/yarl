"""Integration test for Plague Necromancer identity scenario metrics enforcement."""

import pytest
from config.level_template_registry import get_scenario_registry
from services.scenario_harness import run_scenario_many, make_bot_policy


@pytest.mark.slow
def test_plague_necromancer_identity_scenario_metrics():
    """Verify Plague Necromancer scenario meets minimum thresholds (30 runs)."""
    
    registry = get_scenario_registry()
    scenario = registry.get_scenario_definition("monster_plague_necromancer_identity")
    if scenario is None:
        pytest.skip("Plague Necromancer scenario not found in registry")
    
    policy = make_bot_policy("tactical_fighter")
    
    metrics = run_scenario_many(
        scenario=scenario,
        bot_policy=policy,
        runs=30,
        turn_limit=250,
        seed_base=None
    )
    
    # THRESHOLD 1: Plague raise success frequency
    plague_raise_successes = getattr(metrics, 'total_plague_raise_successes', 0)
    assert plague_raise_successes >= 15, (
        f"Plague necromancer should successfully raise plague zombies (at least 15 across 30 runs). "
        f"Got {plague_raise_successes}, expected >= 15."
    )
    
    # THRESHOLD 2: Plague zombies spawned
    plague_zombies_spawned = getattr(metrics, 'total_plague_zombies_spawned', 0)
    assert plague_zombies_spawned >= 15, (
        f"Plague zombies should be spawned (at least 15 across 30 runs). "
        f"Got {plague_zombies_spawned}, expected >= 15."
    )
    
    # THRESHOLD 3: Player deaths should be moderate-high (plague is dangerous)
    player_deaths = getattr(metrics, 'player_deaths', 0)
    assert 8 <= player_deaths <= 25, (
        f"Player deaths should be moderate-high for 30 runs (plague is dangerous). "
        f"Got {player_deaths}, expected 8-25."
    )
    
    print(f"\n✅ Plague Necromancer scenario metrics validated:")
    print(f"   - Plague raise successes: {plague_raise_successes} (>= 15)")
    print(f"   - Plague zombies spawned: {plague_zombies_spawned} (>= 15)")
    print(f"   - Player deaths: {player_deaths} (8-25)")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
