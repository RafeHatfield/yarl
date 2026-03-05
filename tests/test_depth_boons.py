"""Phase 23: Depth Boons scaffold unit tests.

All tests are marked ``fast`` (no scenario harness, no network, no disk I/O).

Test coverage:
- apply_boon: each starter boon mutates the correct Fighter field
- apply_boon: unknown boon_id raises ValueError
- apply_boon: missing Fighter component returns False (no raise)
- apply_depth_boon_if_eligible: first visit grants boon + records state
- apply_depth_boon_if_eligible: second visit to same depth → no re-grant
- ascending/descending: simulated revisit → no re-grant
- depth with no DEPTH_BOON_MAP entry → visited_depths updated but no boon
- disable_depth_boons flag prevents auto grant
- Statistics serialization round-trip (visited_depths, boons_applied, disable flag)
- _apply_player_boons scenario loader helper
- Determinism: depths 1–5 always yield the canonical boon sequence
- RunMetrics export includes boons_applied (integration via run_scenario_once)
"""

import pytest
from entity import Entity
from components.fighter import Fighter
from components.statistics import Statistics
from components.component_registry import ComponentType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_player(hp: int = 30, defense: int = 2, power: int = 5,
                 damage_min: int = 1, accuracy: int = 2) -> Entity:
    """Create a minimal player-like entity with Fighter and Statistics."""
    player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
    player.fighter = Fighter(
        hp=hp,
        defense=defense,
        power=power,
        damage_min=damage_min,
        accuracy=accuracy,
    )
    stats = Statistics(owner=player)
    player.statistics = stats
    player.components.add(ComponentType.STATISTICS, stats)
    return player


# ---------------------------------------------------------------------------
# apply_boon — individual boon effects
# ---------------------------------------------------------------------------

@pytest.mark.fast
def test_apply_boon_fortitude_10():
    """fortitude_10 adds 10 to base_max_hp and heals 10 HP."""
    from balance.depth_boons import apply_boon

    player = _make_player(hp=30)
    base_max = player.fighter.base_max_hp
    base_hp = player.fighter.hp
    assert apply_boon(player, "fortitude_10") is True
    assert player.fighter.base_max_hp == base_max + 10
    assert player.fighter.hp == base_hp + 10


@pytest.mark.fast
def test_apply_boon_fortitude_10_hp_capped_at_new_max():
    """HP after fortitude_10 cannot exceed the new max_hp."""
    from balance.depth_boons import apply_boon

    player = _make_player(hp=30)
    # Damage the player so HP is below max
    player.fighter.hp = 10
    apply_boon(player, "fortitude_10")
    # HP should be 10 + 10 = 20, max is 30 + 10 = 40 — within range
    assert player.fighter.hp == 20
    assert player.fighter.base_max_hp == 40


@pytest.mark.fast
def test_apply_boon_accuracy_1():
    """accuracy_1 adds 2 to fighter.accuracy."""
    from balance.depth_boons import apply_boon

    player = _make_player(accuracy=2)
    assert apply_boon(player, "accuracy_1") is True
    assert player.fighter.accuracy == 4


@pytest.mark.fast
def test_apply_boon_defense_1():
    """defense_1 adds 1 to fighter.base_defense."""
    from balance.depth_boons import apply_boon

    player = _make_player(defense=2)
    assert apply_boon(player, "defense_1") is True
    assert player.fighter.base_defense == 3


@pytest.mark.fast
def test_apply_boon_damage_1():
    """damage_1 adds 1 to fighter.damage_min."""
    from balance.depth_boons import apply_boon

    player = _make_player(damage_min=1)
    assert apply_boon(player, "damage_1") is True
    assert player.fighter.damage_min == 2


@pytest.mark.fast
def test_apply_boon_resilience_5():
    """resilience_5 adds 10 to base_max_hp and heals 10 HP."""
    from balance.depth_boons import apply_boon

    player = _make_player(hp=30)
    base_max = player.fighter.base_max_hp
    apply_boon(player, "resilience_5")
    assert player.fighter.base_max_hp == base_max + 10
    assert player.fighter.hp == player.fighter.base_max_hp  # was at full HP


# ---------------------------------------------------------------------------
# apply_boon — error cases
# ---------------------------------------------------------------------------

@pytest.mark.fast
def test_apply_boon_unknown_raises_value_error():
    """Passing an unrecognised boon_id raises ValueError (fail-loud)."""
    from balance.depth_boons import apply_boon

    player = _make_player()
    with pytest.raises(ValueError, match="Unknown boon_id"):
        apply_boon(player, "totally_made_up_boon")


@pytest.mark.fast
def test_apply_boon_no_fighter_returns_false():
    """If the entity has no Fighter component, apply_boon returns False without raising."""
    from balance.depth_boons import apply_boon

    # Entity with NO fighter component
    entity = Entity(0, 0, 'x', (255, 0, 0), 'No Fighter', blocks=False)
    assert apply_boon(entity, "fortitude_10") is False


# ---------------------------------------------------------------------------
# apply_depth_boon_if_eligible — core gating logic
# ---------------------------------------------------------------------------

@pytest.mark.fast
def test_first_visit_grants_boon():
    """First visit to depth 1 grants fortitude_10 and updates state correctly."""
    from balance.depth_boons import apply_depth_boon_if_eligible, DEPTH_BOON_MAP

    player = _make_player(hp=30)
    base_max = player.fighter.base_max_hp

    result = apply_depth_boon_if_eligible(player, 1)

    assert result == "fortitude_10"
    assert result == DEPTH_BOON_MAP[1]
    # Stat mutation
    assert player.fighter.base_max_hp == base_max + 10
    # State recorded
    assert 1 in player.statistics.visited_depths
    assert player.statistics.boons_applied == ["fortitude_10"]


@pytest.mark.fast
def test_second_visit_no_reapplication():
    """Calling apply_depth_boon_if_eligible twice for the same depth does not stack."""
    from balance.depth_boons import apply_depth_boon_if_eligible

    player = _make_player(hp=30)
    base_max = player.fighter.base_max_hp

    apply_depth_boon_if_eligible(player, 1)
    second = apply_depth_boon_if_eligible(player, 1)

    assert second is None
    # HP increased exactly once
    assert player.fighter.base_max_hp == base_max + 10
    # Log has exactly one entry
    assert player.statistics.boons_applied == ["fortitude_10"]


@pytest.mark.fast
def test_ascending_descending_no_farm():
    """Revisiting depth 1 after going to depth 2 and back does not re-grant."""
    from balance.depth_boons import apply_depth_boon_if_eligible

    player = _make_player(hp=30)
    base_max = player.fighter.base_max_hp

    # Descend: depth 1, then depth 2
    apply_depth_boon_if_eligible(player, 1)
    apply_depth_boon_if_eligible(player, 2)
    # Ascend back to depth 1
    third = apply_depth_boon_if_eligible(player, 1)

    assert third is None
    # Only two boons total
    assert len(player.statistics.boons_applied) == 2
    assert player.statistics.boons_applied == ["fortitude_10", "accuracy_1"]
    # visited_depths includes both
    assert player.statistics.visited_depths == {1, 2}


@pytest.mark.fast
def test_depth_with_no_boon_mapping():
    """A depth outside DEPTH_BOON_MAP (e.g. 6) still marks visited but returns None."""
    from balance.depth_boons import apply_depth_boon_if_eligible

    player = _make_player(hp=30)
    result = apply_depth_boon_if_eligible(player, 6)

    assert result is None
    assert 6 in player.statistics.visited_depths
    assert player.statistics.boons_applied == []


@pytest.mark.fast
def test_no_statistics_component_returns_none():
    """An entity without Statistics silently returns None (safe no-op)."""
    from balance.depth_boons import apply_depth_boon_if_eligible

    # Entity with Fighter but no Statistics
    entity = Entity(0, 0, '@', (255, 255, 255), 'NoStats', blocks=True)
    entity.fighter = Fighter(hp=30, defense=2, power=5)

    result = apply_depth_boon_if_eligible(entity, 1)
    assert result is None


@pytest.mark.fast
def test_disable_flag_prevents_auto_grant():
    """disable_depth_boons=True prevents any automatic boon from firing."""
    from balance.depth_boons import apply_depth_boon_if_eligible

    player = _make_player(hp=30)
    base_max = player.fighter.base_max_hp
    player.statistics.disable_depth_boons = True

    result = apply_depth_boon_if_eligible(player, 1)

    assert result is None
    assert player.fighter.base_max_hp == base_max   # unchanged
    assert player.statistics.boons_applied == []


# ---------------------------------------------------------------------------
# Statistics serialization round-trip
# ---------------------------------------------------------------------------

@pytest.mark.fast
def test_statistics_serialization_round_trip():
    """visited_depths, boons_applied, and disable_depth_boons survive to_dict/from_dict."""
    stats = Statistics()
    stats.visited_depths = {1, 3, 5}
    stats.boons_applied = ["fortitude_10", "defense_1", "resilience_5"]
    stats.disable_depth_boons = True

    data = stats.to_dict()
    restored = Statistics.from_dict(data)

    assert restored.visited_depths == {1, 3, 5}
    assert restored.boons_applied == ["fortitude_10", "defense_1", "resilience_5"]
    assert restored.disable_depth_boons is True


@pytest.mark.fast
def test_statistics_serialization_defaults():
    """A fresh Statistics round-trips cleanly with zero/empty boon state."""
    stats = Statistics()
    data = stats.to_dict()
    restored = Statistics.from_dict(data)

    assert restored.visited_depths == set()
    assert restored.boons_applied == []
    assert restored.disable_depth_boons is False


@pytest.mark.fast
def test_statistics_from_dict_old_save_missing_boon_fields():
    """from_dict handles old save data that has no boon fields (backward compat)."""
    # Simulate an old save dict without the Phase 23 fields
    old_data = {
        'monsters_killed': {},
        'total_kills': 0,
        'deepest_level': 3,
        # visited_depths, boons_applied, disable_depth_boons intentionally absent
    }
    restored = Statistics.from_dict(old_data)
    assert restored.visited_depths == set()
    assert restored.boons_applied == []
    assert restored.disable_depth_boons is False


# ---------------------------------------------------------------------------
# Scenario loader wiring
# ---------------------------------------------------------------------------

@pytest.mark.fast
def test_apply_player_boons_explicit():
    """_apply_player_boons applies listed boons and records them in statistics."""
    from services.scenario_level_loader import _apply_player_boons

    player = _make_player(defense=2)
    _apply_player_boons(player, {"boons": ["defense_1"], "disable_depth_boons": False})

    assert player.fighter.base_defense == 3
    assert player.statistics.boons_applied == ["defense_1"]
    assert player.statistics.disable_depth_boons is False


@pytest.mark.fast
def test_apply_player_boons_sets_disable_flag():
    """_apply_player_boons sets disable_depth_boons when the flag is True."""
    from services.scenario_level_loader import _apply_player_boons

    player = _make_player()
    _apply_player_boons(player, {"boons": [], "disable_depth_boons": True})

    assert player.statistics.disable_depth_boons is True


@pytest.mark.fast
def test_apply_player_boons_unknown_boon_warns_not_raises(caplog):
    """_apply_player_boons logs a warning for unknown boon IDs instead of crashing."""
    import logging
    from services.scenario_level_loader import _apply_player_boons

    player = _make_player()
    with caplog.at_level(logging.WARNING):
        _apply_player_boons(player, {"boons": ["totally_fake_boon"]})

    assert "totally_fake_boon" in caplog.text
    assert player.statistics.boons_applied == []


@pytest.mark.fast
def test_apply_player_boons_multiple_boons():
    """_apply_player_boons applies all listed boons in order."""
    from services.scenario_level_loader import _apply_player_boons

    player = _make_player(hp=30, defense=2)
    _apply_player_boons(player, {"boons": ["fortitude_10", "defense_1"]})

    assert player.fighter.base_max_hp == 40   # 30 + 10
    assert player.fighter.base_defense == 3   # 2 + 1
    assert player.statistics.boons_applied == ["fortitude_10", "defense_1"]


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

@pytest.mark.fast
def test_determinism_depth_sequence():
    """Depths 1–5 always yield the canonical boon sequence regardless of RNG state."""
    import random
    from balance.depth_boons import apply_depth_boon_if_eligible, DEPTH_BOON_MAP

    expected = [DEPTH_BOON_MAP[d] for d in range(1, 6)]

    for seed in (1337, 42, 0, 99999):
        random.seed(seed)
        player = _make_player()
        result = [apply_depth_boon_if_eligible(player, d) for d in range(1, 6)]
        assert result == expected, f"Sequence mismatch at seed={seed}: {result}"


# ---------------------------------------------------------------------------
# RunMetrics export (integration with scenario harness)
# ---------------------------------------------------------------------------

@pytest.mark.fast
def test_run_metrics_boon_export():
    """run_scenario_once on boon_identity yields metrics.boons_applied == ['fortitude_10']."""
    import random
    from config.level_template_registry import get_scenario_registry
    from services.scenario_harness import run_scenario_once, make_bot_policy

    random.seed(1337)
    registry = get_scenario_registry()
    scenario = registry.get_scenario_definition("boon_identity")
    if scenario is None:
        pytest.skip("boon_identity scenario not registered")
    policy = make_bot_policy("observe_only")
    metrics = run_scenario_once(scenario, policy, turn_limit=5)

    assert metrics.boons_applied == ["fortitude_10"]


@pytest.mark.fast
def test_run_metrics_to_dict_includes_boons():
    """RunMetrics.to_dict() always has a 'boons_applied' key."""
    from services.scenario_harness import RunMetrics
    from collections import defaultdict

    m = RunMetrics(
        turns_taken=1,
        player_died=False,
        kills_by_faction=defaultdict(int),
        kills_by_source=defaultdict(int),
        boons_applied=["fortitude_10"],
    )
    d = m.to_dict()
    assert "boons_applied" in d
    assert d["boons_applied"] == ["fortitude_10"]


@pytest.mark.fast
def test_run_metrics_to_dict_empty_boons_present():
    """RunMetrics.to_dict() has 'boons_applied' even when no boons were applied."""
    from services.scenario_harness import RunMetrics
    from collections import defaultdict

    m = RunMetrics(
        turns_taken=0,
        player_died=False,
        kills_by_faction=defaultdict(int),
        kills_by_source=defaultdict(int),
    )
    d = m.to_dict()
    assert "boons_applied" in d
    assert d["boons_applied"] == []


# ---------------------------------------------------------------------------
# AggregatedMetrics export — run_details includes per-run boons_applied
# ---------------------------------------------------------------------------

@pytest.mark.fast
def test_aggregated_metrics_run_details_include_boons():
    """run_scenario_many on boon_identity exports run_details with boons_applied."""
    import random
    from config.level_template_registry import get_scenario_registry
    from services.scenario_harness import run_scenario_many, make_bot_policy

    random.seed(1337)
    registry = get_scenario_registry()
    scenario = registry.get_scenario_definition("boon_identity")
    if scenario is None:
        pytest.skip("boon_identity scenario not registered")
    policy = make_bot_policy("observe_only")
    aggregated = run_scenario_many(scenario, policy, runs=2, turn_limit=5, seed_base=1337)

    d = aggregated.to_dict()
    assert "run_details" in d, "AggregatedMetrics.to_dict() must include run_details when populated"
    assert len(d["run_details"]) == 2
    for run_dict in d["run_details"]:
        assert "boons_applied" in run_dict
        assert run_dict["boons_applied"] == ["fortitude_10"]
