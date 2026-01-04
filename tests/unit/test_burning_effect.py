"""Unit tests for BurningEffect (Fire Potion DOT)."""

import logging
from types import SimpleNamespace

from components.component_registry import ComponentType
from components.fighter import Fighter
from components.status_effects import BurningEffect, StatusEffectManager
from entity import Entity
from services.scenario_metrics import scoped_metrics_collector


def _make_entity(name="Dummy", hp=5, resistances=None):
    fighter = Fighter(hp=hp, defense=0, power=0, resistances=resistances)
    entity = Entity(0, 0, "d", (255, 255, 255), name, blocks=True, fighter=fighter)
    entity.status_effects = StatusEffectManager(entity)
    entity.components.add(ComponentType.STATUS_EFFECTS, entity.status_effects)
    return entity


def test_burning_effect_ticks_and_expires():
    entity = _make_entity()
    effect = BurningEffect(duration=4, owner=entity)
    entity.status_effects.add_effect(effect)
    
    for _ in range(4):
        entity.status_effects.process_turn_start(state_manager=None)
        entity.status_effects.process_turn_end()
    
    assert not entity.status_effects.has_effect("burning")


def test_burning_effect_refreshes_without_stacking():
    entity = _make_entity()
    entity.status_effects.add_effect(BurningEffect(duration=4, owner=entity))
    entity.status_effects.add_effect(BurningEffect(duration=4, owner=entity))
    
    assert len(entity.status_effects.active_effects) == 1
    assert entity.status_effects.get_effect("burning").duration == 4


def test_burning_effect_resistance_reduces_damage():
    entity = _make_entity(resistances={"fire": 100})
    effect = BurningEffect(duration=1, owner=entity)
    
    starting_hp = entity.fighter.hp
    effect.process_turn_start(state_manager=None)
    
    assert entity.fighter.hp == starting_hp


def test_burning_effect_lethal_clamp_without_state_manager(caplog):
    entity = _make_entity(hp=1)
    effect = BurningEffect(duration=1, owner=entity)
    
    caplog.set_level(logging.ERROR)
    effect.process_turn_start(state_manager=None)
    
    assert entity.fighter.hp == 1
    assert any("BURNING_LETHAL_CLAMP" in record.message for record in caplog.records)


def test_burning_effect_metrics_increment():
    entity = _make_entity()
    metrics = SimpleNamespace()
    
    with scoped_metrics_collector(metrics):
        effect = BurningEffect(duration=1, owner=entity)
        effect.apply()
        effect.process_turn_start(state_manager=None)
    
    assert metrics.burning_applications == 1
    assert metrics.burning_ticks_processed == 1
