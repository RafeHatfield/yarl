import pytest

from components.equipment import Equipment
from components.fighter import Fighter
from components.inventory import Inventory
from components.level import Level
from config.factories import get_entity_factory
from config.level_template_registry import ScenarioDefinition
from entity import Entity
from map_objects.game_map import GameMap
from services.scenario_invariants import ScenarioInvariantError, validate_scenario_instance


def _open_floor_map(width: int = 10, height: int = 10, dungeon_level: int = 1) -> GameMap:
    game_map = GameMap(width, height, dungeon_level=dungeon_level)
    for x in range(width):
        for y in range(height):
            tile = game_map.get_tile(x, y)
            if tile:
                tile.blocked = False
                tile.block_sight = False
    return game_map


def _basic_player(x: int, y: int) -> Entity:
    fighter = Fighter(hp=10, defense=1, power=2, damage_min=1, damage_max=3, strength=10, dexterity=10, constitution=10)
    inventory = Inventory(10)
    level = Level(level_up_base=100, level_up_factor=150)
    equipment = Equipment()
    player = Entity.create_player(x=x, y=y, fighter=fighter, inventory=inventory, level=level, equipment=equipment)
    return player


def _base_scenario(**kwargs):
    defaults = dict(
        scenario_id="scenario_test",
        name="Test Scenario",
        description=None,
        depth=None,
        defaults={},
        expected={},
        rooms=[],
        monsters=[],
        items=[],
        player=None,
        hazards=[],
        victory_conditions=[],
        defeat_conditions=[],
        source_file="",
    )
    defaults.update(kwargs)
    return ScenarioDefinition(**defaults)


def test_valid_scenario_passes():
    scenario = _base_scenario(
        monsters=[{"type": "orc", "count": 1, "position": [2, 2]}],
        items=[{"type": "healing_potion", "count": 1, "position": [3, 3]}],
    )
    game_map = _open_floor_map()
    player = _basic_player(1, 1)

    factory = get_entity_factory()
    monster = factory.create_monster("orc", 2, 2)
    item = factory.create_spell_item("healing_potion", 3, 3)
    entities = [player, monster, item]

    validate_scenario_instance(scenario, game_map, player, entities)


def test_player_out_of_bounds():
    scenario = _base_scenario()
    game_map = _open_floor_map()
    player = _basic_player(20, 20)
    entities = [player]

    with pytest.raises(ScenarioInvariantError):
        validate_scenario_instance(scenario, game_map, player, entities)


def test_monster_on_blocked_tile():
    scenario = _base_scenario(monsters=[{"type": "orc"}])
    game_map = _open_floor_map()
    game_map.tiles[2][2].blocked = True
    player = _basic_player(1, 1)
    factory = get_entity_factory()
    monster = factory.create_monster("orc", 2, 2)
    entities = [player, monster]

    with pytest.raises(ScenarioInvariantError):
        validate_scenario_instance(scenario, game_map, player, entities)


def test_duplicate_monster_tile():
    scenario = _base_scenario(monsters=[{"type": "orc", "count": 2}])
    game_map = _open_floor_map()
    player = _basic_player(1, 1)
    factory = get_entity_factory()
    m1 = factory.create_monster("orc", 2, 2)
    m2 = factory.create_monster("orc", 2, 2)
    entities = [player, m1, m2]

    with pytest.raises(ScenarioInvariantError):
        validate_scenario_instance(scenario, game_map, player, entities)


def test_invalid_item_type():
    scenario = _base_scenario(items=[{"type": "definitely_fake_item"}])
    game_map = _open_floor_map()
    player = _basic_player(1, 1)
    entities = [player]

    with pytest.raises(ScenarioInvariantError):
        validate_scenario_instance(scenario, game_map, player, entities)
