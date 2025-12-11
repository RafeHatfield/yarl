import pytest

from components.portal import Portal
from entity import Entity
from map_objects.game_map import GameMap
from services.portal_invariants import validate_portals, PortalInvariantError


def _open_floor_map(w: int = 20, h: int = 10) -> GameMap:
    g = GameMap(w, h, dungeon_level=1)
    for x in range(w):
        for y in range(h):
            tile = g.get_tile(x, y)
            tile.blocked = False
            tile.block_sight = False
    return g


def _portal_entity(x: int, y: int, portal_type: str) -> Entity:
    ent = Entity(x=x, y=y, char="[", color=(255, 255, 255), name=f"{portal_type}-portal", blocks=False)
    p = Portal(portal_type)
    ent.portal = p
    p.owner = ent
    return ent


def test_valid_linked_pair_passes():
    game_map = _open_floor_map()
    entrance = _portal_entity(2, 2, "entrance")
    exit_portal = _portal_entity(5, 5, "exit")

    entrance.portal.linked_portal = exit_portal.portal
    exit_portal.portal.linked_portal = entrance.portal

    validate_portals(game_map, [entrance, exit_portal])


def test_missing_link_raises():
    game_map = _open_floor_map()
    entrance = _portal_entity(2, 2, "entrance")
    exit_portal = _portal_entity(5, 5, "exit")
    entrance.portal.linked_portal = None
    exit_portal.portal.linked_portal = entrance.portal

    with pytest.raises(PortalInvariantError):
        validate_portals(game_map, [entrance, exit_portal])


def test_blocked_destination_raises():
    game_map = _open_floor_map()
    game_map.get_tile(5, 5).blocked = True
    entrance = _portal_entity(2, 2, "entrance")
    exit_portal = _portal_entity(5, 5, "exit")
    entrance.portal.linked_portal = exit_portal.portal
    exit_portal.portal.linked_portal = entrance.portal

    with pytest.raises(PortalInvariantError):
        validate_portals(game_map, [entrance, exit_portal])


def test_owner_mismatch_raises():
    game_map = _open_floor_map()
    entrance = _portal_entity(2, 2, "entrance")
    exit_portal = _portal_entity(5, 5, "exit")
    fake_entity = Entity(0, 0, "!", (255, 0, 0), "fake")

    entrance.portal.owner = fake_entity
    entrance.portal.linked_portal = exit_portal.portal
    exit_portal.portal.linked_portal = entrance.portal

    with pytest.raises(PortalInvariantError):
        validate_portals(game_map, [entrance, exit_portal])
