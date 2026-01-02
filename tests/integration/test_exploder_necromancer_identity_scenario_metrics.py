"""Integration test for Exploder Necromancer identity scenario metrics enforcement."""

import pytest
from config.level_template_registry import get_scenario_registry
from services.scenario_harness import run_scenario_many, make_bot_policy


@pytest.mark.slow
def test_exploder_necromancer_identity_scenario_metrics():
    """Verify Exploder Necromancer scenario meets minimum thresholds (30 runs)."""
    
    registry = get_scenario_registry()
    scenario = registry.get_scenario_definition("monster_exploder_necromancer_identity")
    if scenario is None:
        pytest.skip("Exploder Necromancer scenario not found in registry")
    
    policy = make_bot_policy("tactical_fighter")
    
    metrics = run_scenario_many(
        scenario=scenario,
        bot_policy=policy,
        runs=30,
        turn_limit=250,
        seed_base=None
    )
    
    # THRESHOLD 1: Corpse explosions cast
    explosions_cast = getattr(metrics, 'total_corpse_explosions_cast', 0)
    assert explosions_cast >= 10, (
        f"Exploder necromancer should cast corpse explosions (at least 10 across 30 runs). "
        f"Got {explosions_cast}, expected >= 10."
    )
    
    # THRESHOLD 2: Spent corpses consumed
    spent_corpses = getattr(metrics, 'total_spent_corpses_consumed', 0)
    assert spent_corpses >= 10, (
        f"Spent corpses should be consumed by explosions (at least 10 across 30 runs). "
        f"Got {spent_corpses}, expected >= 10."
    )
    
    # THRESHOLD 3: Explosion damage dealt
    explosion_damage = getattr(metrics, 'total_explosion_damage_total', 0)
    assert explosion_damage >= 40, (
        f"Explosions should deal damage (at least 40 total across 30 runs). "
        f"Got {explosion_damage}, expected >= 40."
    )
    
    # THRESHOLD 4: Player deaths should be moderate
    player_deaths = getattr(metrics, 'player_deaths', 0)
    assert 5 <= player_deaths <= 20, (
        f"Player deaths should be moderate for 30 runs. "
        f"Got {player_deaths}, expected 5-20."
    )
    
    print(f"\n✅ Exploder Necromancer scenario metrics validated:")
    print(f"   - Corpse explosions cast: {explosions_cast} (>= 10)")
    print(f"   - Spent corpses consumed: {spent_corpses} (>= 10)")
    print(f"   - Explosion damage dealt: {explosion_damage} (>= 40)")
    print(f"   - Player deaths: {player_deaths} (5-20)")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
