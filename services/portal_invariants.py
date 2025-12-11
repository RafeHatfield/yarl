"""Portal invariants and validation utilities.

These checks are intentionally conservative and are meant to run in tests or
scenario harness setup to catch structural portal issues early:
- Missing required components/owners
- Invalid positions (out of bounds or on blocked tiles)
- Dangling or asymmetric links
"""

from __future__ import annotations

from typing import Any, Iterable, List, Optional, Tuple

from components.component_registry import ComponentType
from components.portal import Portal


class PortalInvariantError(Exception):
    """Raised when a portal invariant is violated."""


def validate_portals(game_map, entities: Iterable[Any]) -> None:
    """Validate all portal entities currently in the world.

    Raises:
        PortalInvariantError: on the first violation encountered.
    """
    portals = [e for e in entities if hasattr(e, "portal")]
    seen_positions: set[Tuple[int, int]] = set()

    for entity in portals:
        _require_portal_component(entity)
        _require_owner(entity)
        _require_position(entity, game_map)
        _require_unique_position(entity, seen_positions)
        _require_deployed_consistency(entity)

    # Second pass: link symmetry and destination sanity
    for entity in portals:
        _validate_link_sanity(entity, game_map)


def _require_portal_component(entity: Any) -> None:
    if not hasattr(entity, "portal"):
        raise PortalInvariantError(f"Entity {getattr(entity, 'name', '?')} missing portal component")
    if not entity.components.has(ComponentType.PORTAL):
        raise PortalInvariantError(f"Portal entity {getattr(entity, 'name', '?')} not registered in components")


def _require_owner(entity: Any) -> None:
    portal: Portal = entity.portal
    if portal.owner is not entity:
        raise PortalInvariantError(
            f"Portal owner mismatch: expected {entity}, got {portal.owner} for {portal.portal_type}"
        )


def _require_position(entity: Any, game_map) -> None:
    if not hasattr(entity, "x") or not hasattr(entity, "y"):
        raise PortalInvariantError("Portal entity missing coordinates")
    x, y = entity.x, entity.y
    if not game_map or not hasattr(game_map, "is_in_bounds"):
        return
    if not game_map.is_in_bounds(x, y):
        raise PortalInvariantError(f"Portal at ({x}, {y}) is out of bounds")
    tile = game_map.get_tile(x, y)
    if tile is None or getattr(tile, "blocked", False):
        raise PortalInvariantError(f"Portal at ({x}, {y}) is on a blocked tile")


def _require_unique_position(entity: Any, seen_positions: set[Tuple[int, int]]) -> None:
    pos = (entity.x, entity.y)
    if pos in seen_positions:
        raise PortalInvariantError(f"Multiple portals share position {pos}")
    seen_positions.add(pos)


def _require_deployed_consistency(entity: Any) -> None:
    portal: Portal = entity.portal
    if portal.is_deployed is False:
        raise PortalInvariantError(f"Portal {portal.portal_type} at ({entity.x}, {entity.y}) marked not deployed")


def _validate_link_sanity(entity: Any, game_map) -> None:
    portal: Portal = entity.portal

    # Victory portal can be unlinked; skip symmetry for that type
    if portal.portal_type not in ("entrance", "exit"):
        return

    linked: Optional[Portal] = portal.linked_portal
    if linked is None:
        raise PortalInvariantError(f"Portal {portal.portal_type} at ({entity.x}, {entity.y}) has no linked portal")

    if linked.owner is None:
        raise PortalInvariantError(f"Linked portal for {portal.portal_type} has no owner")

    # Symmetry check: the linked portal should point back
    if linked.linked_portal is not portal:
        raise PortalInvariantError(
            f"Portal link asymmetry: {portal.portal_type} at ({entity.x},{entity.y}) "
            f"does not have symmetric link"
        )

    # Destination validity: linked portal coordinates must be in bounds and unblocked
    dest_entity = linked.owner
    if hasattr(game_map, "is_in_bounds"):
        if not game_map.is_in_bounds(dest_entity.x, dest_entity.y):
            raise PortalInvariantError(
                f"Linked portal destination out of bounds: ({dest_entity.x}, {dest_entity.y})"
            )
        dest_tile = game_map.get_tile(dest_entity.x, dest_entity.y)
        if dest_tile is None or getattr(dest_tile, "blocked", False):
            raise PortalInvariantError(
                f"Linked portal destination blocked at ({dest_entity.x}, {dest_entity.y})"
            )
