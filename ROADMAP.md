# Catacombs of YARL – Roadmap

Last updated: March 2026 (Phase 24 start)

## Current Phase: 24 – Data-Driven Balance

Phase 23 (depth boons, A/B pressure pipeline, curve visualization, gear probes) is complete. Phase 24 focuses on closing the loop: using harness data to systematically tune the difficulty curve.

### Phase 24 Goals
1. **Target bands** — codified per-depth targets for Death%, H_PM, H_MP in `balance/target_bands.py`
2. **Enhanced reports** — target band overlay, pass/fail indicators, automated diagnosis in depth pressure reports
3. **Balance dashboard** — read-only HTML dashboard for visualizing depth curves, deltas, and failing scenarios
4. **Encounter tuning** — fix depth 4 orc spike (composition issue), assess depth 6 lethality
5. **Item economy** — gear progression curves, loot distribution by depth

### Known Balance Issues (from Phase 23 data)
- **Depth 4 orcs**: 56% death rate with boons (target: 15-30%). Likely composition, not scaling.
- **Depth 6 orcs**: 92% death rate with boons (target: 35-55%). Near-wipe; needs scaling adjustment or more boons/gear.
- **Gear dominance**: weapon +1 eliminates all deaths at depth 3. Intentional but worth monitoring.

## Status Snapshot
- ~3700+ automated tests; fast suite (`pytest -m "not slow"`) is the default
- Deterministic scenario harness with A/B boon testing and gear probes
- Depth pressure pipeline: `tools/collect_depth_pressure_data.py` → `analysis/*.py` → `reports/`
- Five balance-relevant scaling systems: DEFAULT_CURVE, ZOMBIE_CURVE, depth boons, gear, encounter composition
- Bot soak harness with 5 personas for overnight stability
- Claude Code integration with 5 specialized agents (planner, builder, tester, reviewer, analyst)

## Completed Phases (Recent)
- **Phase 23**: Depth boons, A/B pressure pipeline, curve visualization, gear probes
- **Phase 22.4**: Identity suite, suite architecture refactor
- **Phase 22.3**: Skirmisher enemy with leap + fast pressure
- **Phase 22.2**: Ranged combat (quiver, net arrows)
- **Phase 22.1**: Balance suite, oaths system
- **Phase 20-21**: Corpse explosion, traps, hazards suite
- **Phase 19**: Monster identity (Orc Chieftain, Necromancer, Lich, Wraith, Troll, Skeleton)

Earlier phases (4-18) archived in `docs/archive/`.

## Where to Look
- Architecture: `ARCHITECTURE_OVERVIEW.md` (locked reference)
- Balance data: `reports/depth_pressure/`, `balance/`, `analysis/`
- Scenario harness: `ecosystem_sanity.py`, `tools/collect_depth_pressure_data.py`
- Design philosophy: `docs/DESIGN_PRINCIPLES.md`, `PLAYER_PAIN_POINTS.md`
- Testing: `docs/testing/`, fast suite by default
- Agent workflow: `.claude/agents/`, task files in `tasks/`

---
Update cadence: after major balance passes or phase completions.
