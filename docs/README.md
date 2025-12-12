# YARL Documentation Hub

This folder is the index for stable docs. Architecture refactors continue elsewhere; this hub focuses on current, reliable references.

## Quick Navigation
- Root overview: `README.md`
- Roadmap (docs branch): `ROADMAP.md`
- Architecture reference: `ARCHITECTURE_OVERVIEW.md` (locked)
- Combat metrics & scenarios: `docs/COMBAT_METRICS_GUIDE.md`
- Difficulty curve tooling: `reports/difficulty_dashboard.md` (generated) and `tools/difficulty_curve_visualizer.py` (supports family filters and speed-variant exclusion)
- Scenario/bot harnesses: `docs/BOT_SOAK_HARNESS.md`, `HEADLESS_MODE.md`
- YAML/config references: `docs/YAML_CONSTANTS_GUIDE.md`, `docs/YAML_ROOM_GENERATION_SYSTEM.md`, `docs/balance/`
- Testing: `docs/testing/GOLDEN_PATH_IMPLEMENTATION.md`, `docs/testing/GOLDEN_PATH_QUICKSTART.md`

## Developer Maps
- `docs/architecture/` – portal system, renderer/input abstraction, architecture notes.
- `docs/balance/` – balance system overview, loot baselines, tuning cheat sheets.
- `docs/guides/` – playtesting guidance and checklists.
- `docs/reference/` – item and potion references.
- `docs/testing/` – golden path strategy and quickstart.
- `docs/development/` – historical phase documents (Phase4/Phase5/Portal). Treat as history; see `ROADMAP.md` for current plans.
- `docs/planning/` – older planning notes (victory condition phases, dungeon/vault plans); archived for context.

## Historical Archives
- `docs/archive/` and `archive/` contain legacy plans, bug fixes, and release notes. Useful for archaeology; do not treat as current truth.

## How to Add Docs
- Put canonical, evergreen references in the root or relevant subfolder above.
- If a doc is temporary or speculative, mark it clearly and plan to archive or delete it after use.
- Keep terminology aligned with code (Scenario harness, Ecosystem sanity, ETP/loot, RunMetrics/AggregatedMetrics, etc.).

## Pointers
- For architecture questions, start at `ARCHITECTURE_OVERVIEW.md` (read-only here).
- For scenario harness usage, see `ecosystem_sanity.py`, `etp_sanity.py`, `loot_sanity.py`, `docs/BOT_SOAK_HARNESS.md`, and `HEADLESS_MODE.md`.
- For combat metrics and dueling/orc swarm scenarios (including new `orc_swarm_tight` and `zombie_horde` probes), see `docs/COMBAT_METRICS_GUIDE.md` and baseline JSONs in the repo.
