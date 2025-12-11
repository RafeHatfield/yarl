# World Generation Overview

This note explains how the world (maps, rooms, monsters, items) is generated, where spawn decisions live, and how to sanity-check outputs without changing gameplay balance. It is intentionally high level and renderer-agnostic.

## High-Level Flow

- **Inputs:** requested dungeon depth (and optional testing knobs).
- **Mapgen:** `GameMap.make_map` (`map_objects/game_map.py`) carves rectangular rooms, connects them with tunnels, and tracks rooms/metadata for later spawn accounting.
- **Spawn planning:** `SpawnService` (`services/spawn_service.py`) builds chance tables and per-room spawn counts using depth + band data, ETP budgets, loot tags, and pity hooks (owned by balance modules).
- **Placement:** `GameMap.place_entities` (and helpers) uses the spawn plan to place monsters/items, respecting exclusions (e.g., stair tile), vault designations, secrets, traps, and template overrides.
- **Outputs:** a populated `GameMap` with stairs, hazards, rooms metadata, and entities list.
- **Guards:** `worldgen_sanity.py` (headless harness) and `tests/test_world_invariants.py` validate reachability, walkable %, spawn bounds, and structural invariants.

```
depth → mapgen (rooms/corridors) → SpawnService (spawn tables + counts)
     → GameMap.place_entities(...) → worldgen_sanity + invariants/tests
```

## Map Generation (rooms and corridors)

- Room attempts, sizes, and tunnel carving live in `GameMap.make_map`. Rectangular rooms are carved, then linked by horizontal/vertical tunnels.
- First room is the player start; last room hosts stairs down. Secret doors, traps, treasure vault designations, and level-template overrides are applied after core carving.
- Rendering is read-only; all mutation stays inside mapgen and placement.

## Spawn Boundary: `SpawnService`

- `services/spawn_service.py` is the spawn decision surface. It:
  - Builds **monster** and **item** chance tables based on depth, band, loot tags, and balance multipliers.
  - Produces per-room spawn counts (`RoomSpawnPlan`) bounded by `max_monsters`/`max_items` and encounter budgets (`EncounterBudget`).
  - Leaves placement to `GameMap` (which also applies pity/ETP checks, room exclusions, and vault rules).
- Balance systems:
  - **ETP**: `balance/etp.py` provides budgets, band lookup, and monster ETP values. SpawnService uses these to stay within allowed threat ranges.
  - **Pity/Loot**: `balance/pity.py` and `balance/loot_tags.py` adjust availability but are owned by balance modules; worldgen docs do not redefine them.

## Invariants and Safety Nets

Worldgen should maintain:
- **Walkable coverage:** Map has a non-trivial walkable fraction (GameMap offers `get_walkable_stats`). Harness surfaces walkable % and warns when extremely low.
- **Reachability:** BFS from player spawn covers the walkable region; no isolated orphan regions.
- **Valid placements:** Entities/items are within bounds, not on walls, and avoid excluded tiles (stairs center when required).
- **Structural requirements:** Stairs exist and are on-map; rooms have consistent metadata; no duplicate player entities.
- **Spawn sanity:** Monster/item counts stay within configured caps; per-room ETP is accounted for but not altered here.

Tests and harnesses:
- `tests/test_world_invariants.py` validates stairs presence, player spawn, entity bounds, and basic map sanity.
- `worldgen_sanity.py` (headless) generates multiple runs and reports walkable %, reachable %, monster/item counts, and per-room ETP totals.

## Using `worldgen_sanity.py`

CLI (headless, no renderer):
- `python3 worldgen_sanity.py --runs 10 --depth 3`
- `python3 worldgen_sanity.py --runs 20 --depth 3 --export-json worldgen_depth3_20runs.json`
- `python3 worldgen_sanity.py --depth-range 1-3 --runs 5 --verbose`

Outputs:
- Console summary per depth:
  - Walkable % (avg/min/max), reachable %, avg monsters/items.
  - Warnings when walkable % is extremely low.
- JSON export (stable fields):
  - `runs`: list of per-run metrics (`depth`, `run`, `width`, `height`, `walkable`, `total_tiles`, `walkable_percent`, `reachable_tiles`, `reachable_percent`, `monsters`, `items`, `rooms[room_id, area, monsters, items, monster_etp]`).
  - `aggregates`: per-depth aggregates (`depth`, `runs`, `walkable_avg/min/max`, `reachable_avg`, `monsters_avg`, `items_avg`).

## Make Targets (shortcuts)

- `make worldgen-quick` — fast smoke: `python3 worldgen_sanity.py --runs 10 --depth 3`.
- `make worldgen-ci` — CI-style sampler with JSON: `python3 worldgen_sanity.py --runs 20 --depth 3 --export-json worldgen_depth3_20runs.json`.
- `make worldgen-report` — heavier manual report: `python3 worldgen_sanity.py --runs 50 --depth 3 --export-json worldgen_depth3_50runs.json`.

When to run:
- Before mapgen/spawn changes.
- After balance/ETP/pity tweaks.
- When adjusting room templates or door/trap rules to ensure reachability and walkable % stay sane.

## Related References

- High-level architecture: `ARCHITECTURE_OVERVIEW.md`.
- Scenario harnesses: `ecosystem_sanity.py`, Make eco targets.
- Balance/ETP: `balance/etp.py`, `balance/loot_tags.py`, `balance/pity.py`.
- YAML/content guides: `docs/YAML_ROOM_GENERATION_SYSTEM.md`, `docs/balance/`.
