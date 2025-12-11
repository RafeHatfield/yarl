# Catacombs of YARL – Roadmap (Dec 2025)

Scope: documentation refresh only; gameplay/architecture work continues on dedicated branches.

## Status Snapshot
- In active development; core loop, ECS, and scenario harnesses are stable.
- Scenario harness + `ecosystem_sanity.py` run in CI for regression/balance checks.
- ETP budgets + loot/pity sanity harnesses exist (`etp_sanity.py`, `loot_sanity.py`).
- Combat metrics + dueling pit/orc swarm scenarios are in place for speed/momentum tuning.
- Bot soak harness + personas documented; headless mode works for automation.
- Architecture refactors (TurnStateAdapter/GameCore) tracked elsewhere; see `ARCHITECTURE_OVERVIEW.md` (locked).

## ✅ Delivered Foundations
- Scenario harness coverage: plague arena, backstab training, dueling pit, orc swarm baselines, and related JSON baselines in repo.
- Ecosystem sanity CI target to catch regressions across multiple scenarios.
- ETP-based encounter budgeting with pity/loot sanity tooling for drops and pacing.
- Combat metrics collectors + reporting for duels and swarm runs (supports speed/momentum tuning).
- Bot soak/autoplay harness with documented personas for overnight stability checks.
- Documentation set for YAML constants/templates and component best practices.

## 🔜 Near-Term Focus (docs + alignment)
- Keep this roadmap aligned with actual scenario harness coverage and CI targets.
- Expand/check scenario docs: include portal stress, speed bonus, plague/backstab variants.
- Surface how to run key harnesses from Makefile/CLI in README and guides.
- Mark historical phase docs clearly and point contributors to current workflow.
- Record balance checkpoints from ecosystem/loot/ETP runs as they land.

## 📌 Historical / Archived
- Phase 4/5/portal development docs live under `docs/development/` and are historical snapshots.
- Older phase/feature plans remain in `docs/planning/` and `archive/` for context only.
- Traditional roguelike feature wishlists remain in `TRADITIONAL_ROGUELIKE_FEATURES.md` (reference, not a promise).

## Where to Look Next
- Architecture details: `ARCHITECTURE_OVERVIEW.md` (do not edit here).
- Combat metrics and scenarios: `docs/COMBAT_METRICS_GUIDE.md`, dueling/orc swarm baselines in repo.
- Scenario harness + CI usage: `ecosystem_sanity.py`, `docs/BOT_SOAK_HARNESS.md`, `HEADLESS_MODE.md`.
- YAML/config references: `docs/YAML_CONSTANTS_GUIDE.md`, `docs/YAML_ROOM_GENERATION_SYSTEM.md`, `docs/balance/*`.

---
Update cadence: adjust after major scenario/harness changes or balance passes. Keep DONE/TODO markers honest and tightly scoped to what is actually implemented.
