# YARL Documentation Hub

Index for stable docs. See `ROADMAP.md` for current phase and direction.

## Quick Navigation
- Project overview: `README.md`
- Current roadmap: `ROADMAP.md` (Phase 24: Data-Driven Balance)
- Architecture reference: `ARCHITECTURE_OVERVIEW.md` (locked)
- Design philosophy: `docs/DESIGN_PRINCIPLES.md`
- Balance pipeline: `balance/`, `analysis/`, `tools/collect_depth_pressure_data.py`
- Balance reports: `reports/depth_pressure/`
- Scenario harness: `ecosystem_sanity.py`
- Bot/soak harness: `docs/BOT_SOAK_HARNESS.md`, `HEADLESS_MODE.md`
- YAML/config: `docs/YAML_CONSTANTS_GUIDE.md`, `docs/YAML_ROOM_GENERATION_SYSTEM.md`
- Testing: `docs/testing/`

## Developer Maps
- `docs/architecture/` – portal system, renderer/input abstraction
- `docs/balance/` – ETP system, loot baselines, tuning cheat sheet
- `docs/guides/` – playtesting guidance and checklists
- `docs/reference/` – item and potion references
- `docs/testing/` – golden path strategy and quickstart, testing strategy
- `docs/INVESTIGATIONS/` – historical investigation reports

## Balance & Tuning (Phase 23+)
- Depth pressure model: `DEPTH_PRESSURE_MODEL.md`
- Depth boons: `DEPTH_BOONS_IMPLEMENTATION.md`
- Gear probes: `EMERGENT_MASTERY_PROBES.md`
- Player progression design: `PLAYER_PROGRESSION_DOCTRINE.md`
- Target bands: `balance/target_bands.py` (Phase 24)

## Historical Archives
- `docs/archive/` – phase implementation notes, fix summaries, release notes, legacy plans
- `docs/development/` – Phase 4/5/portal session notes (historical)
- `docs/planning/` – older planning notes (archived for context)

## Agent Workflow
- Agent definitions: `.claude/agents/` (planner, builder, tester, reviewer, analyst)
- Task tracking: `tasks/`
- Project memory: `.claude/projects/.../memory/`

## How to Add Docs
- Evergreen references go in root or relevant subfolder
- Temporary or speculative docs: mark clearly, archive after use
- Phase implementation notes: archive to `docs/archive/phase-notes/` when phase completes
- Keep terminology aligned with code (scenario harness, ecosystem sanity, ETP, H_PM/H_MP, etc.)
