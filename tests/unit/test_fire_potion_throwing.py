"""Unit tests for Fire Potion throw delivery."""

from types import SimpleNamespace

from components.component_registry import ComponentType
from components.fighter import Fighter
from components.status_effects import BurningEffect
from config.entity_registry import load_entity_config
from config.factories import EntityFactory
from entity import Entity
from map_objects.game_map import GameMap
from services.scenario_metrics import scoped_metrics_collector
from throwing import throw_item


def _make_open_map(width=5, height=5):
    game_map = GameMap(width, height)
    for x in range(width):
        for y in range(height):
            game_map.tiles[x][y].blocked = False
            game_map.tiles[x][y].block_sight = False
    return game_map


def _make_thrower():
    return Entity(1, 1, "@", (255, 255, 255), "Thrower")


def _make_target(x, y):
    fighter = Fighter(hp=6, defense=0, power=0)
    return Entity(x, y, "t", (255, 0, 0), "Target", blocks=True, fighter=fighter)


def test_fire_potion_throw_applies_burning_on_hit():
    load_entity_config()
    factory = EntityFactory()
    potion = factory.create_spell_item("fire_potion", 0, 0)
    assert potion is not None
    
    game_map = _make_open_map()
    thrower = _make_thrower()
    target = _make_target(3, 1)
    entities = [thrower, target]
    metrics = SimpleNamespace()
    
    with scoped_metrics_collector(metrics):
        throw_item(thrower, potion, target.x, target.y, entities, game_map, fov_map=None)
    
    status_effects = target.get_component_optional(ComponentType.STATUS_EFFECTS)
    assert status_effects is not None
    assert isinstance(status_effects.get_effect("burning"), BurningEffect)
    assert metrics.burning_applications == 1


def test_fire_potion_throw_miss_does_not_apply_burning():
    load_entity_config()
    factory = EntityFactory()
    potion = factory.create_spell_item("fire_potion", 0, 0)
    assert potion is not None
    
    game_map = _make_open_map()
    thrower = _make_thrower()
    target = _make_target(4, 4)
    entities = [thrower, target]
    
    throw_item(thrower, potion, 3, 3, entities, game_map, fov_map=None)
    
    status_effects = target.get_component_optional(ComponentType.STATUS_EFFECTS)
    assert status_effects is None or not status_effects.has_effect("burning")
