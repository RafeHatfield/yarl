# Catacombs of YARL

> A turn-based Python roguelike with rich factions, experimental AI, and a heavy focus on simulation-first testing.

## What This Project Delivers
- Turn-based dungeon crawler built on an ECS architecture.
- Scenario harnesses (`ecosystem_sanity.py`) for balance/regression across curated scenarios (plague arena, backstab training, dueling pits, orc swarms).
- ETP-based encounter budgeting plus loot/pity sanity scripts (`etp_sanity.py`, `loot_sanity.py`).
- Combat metrics + dueling/orc swarm baselines for speed/momentum tuning (see baseline JSONs in repo).
- Bot/autoplay harness and personas for soak testing; headless mode for automation.
- YAML-driven content (monsters, loot, rooms) with guides for constants and room generation.

## Project Status
- Active development; architecture refactors (TurnStateAdapter/GameCore) live on other branches. This branch focuses on documentation and hygiene.
- Scenario harness + ecosystem sanity runs in CI to guard regressions.

## Getting Started
1. Install prerequisites: Python 3.12+, `pip`, and a C compiler for native deps.
2. Create and activate a virtualenv:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   # Optional dev tooling
   pip install -r requirements-dev.txt
   ```
4. Run the game:
   ```bash
   python engine.py            # normal
   python engine.py --testing  # testing-friendly setup
   ```

## Tests and Checks
- Unit/integration tests: `pytest` (add `-q` for quiet; include `-m 'not slow'` to skip slow cases).
- Quick CI parity: `./scripts/ci_quick.sh`.
- ETP sanity: `./scripts/ci_run_etp.sh` or `python etp_sanity.py --help`.
- Loot/pity sanity: `./scripts/ci_run_loot.sh` or `python loot_sanity.py --help`.
- Ecosystem sanity (CI mirror): `make eco-ci`.

## Scenario Harness Shortcuts (Make)
- `make eco-quick` – plague arena, backstab training, dueling pit baseline.
- `make eco-all` – full dueling + plague/backstab set (no JSON export).
- `make eco-report` – run all key scenarios and export JSON baselines.
- Individual scenarios:
  - `make eco-plague`, `make eco-backstab`
  - `make eco-duel-baseline`, `make eco-duel-speed-light`, `make eco-duel-speed-full`
  - `make eco-duel-slow-zombie-baseline`, `make eco-duel-slow-zombie-full`

## Bot / Headless / Soak
- Headless mode and bot personas are supported for automation.
- Examples:
  ```bash
  python engine.py --bot --bot-persona tactical_fighter
  python engine.py --bot-soak --runs 10 --bot-persona balanced
  ```
- See `HEADLESS_MODE.md` and `docs/BOT_SOAK_HARNESS.md` for details.

## Documentation Map
- High-level docs: `DOCS_CLEANUP_CHECKLIST.md`, `ROADMAP.md`, `docs/README.md`.
- Architecture reference: `ARCHITECTURE_OVERVIEW.md` (read-only in this branch), `docs/architecture/`.
- Combat metrics & scenarios: `docs/COMBAT_METRICS_GUIDE.md` and baseline JSONs.
- Scenario harness + bots: `docs/BOT_SOAK_HARNESS.md`, `docs/BOT_PERSONAS.md`, `HEADLESS_MODE.md`.
- YAML/config: `docs/YAML_CONSTANTS_GUIDE.md`, `docs/YAML_ROOM_GENERATION_SYSTEM.md`, `docs/balance/`.
- Testing: `docs/testing/GOLDEN_PATH_IMPLEMENTATION.md`, `docs/testing/GOLDEN_PATH_QUICKSTART.md`.
- Component and messaging guides: `docs/COMPONENT_TYPE_BEST_PRACTICES.md`, `docs/MESSAGE_BUILDER_GUIDE.md`, `docs/LOGGING.md`.

## Contributing
- Branch from `main`, keep changes small, and run `pytest` + `make eco-ci` (or the relevant harnesses) before opening a PR.
- Architecture adjustments should align with existing ECS boundaries; avoid renderer/input mutations from gameplay logic.

## Support / Questions
- Architecture questions: start with `ARCHITECTURE_OVERVIEW.md` (locked) and `docs/architecture/`.
- Scenario harness issues: check `ecosystem_sanity.py` and the Make targets above.
- Balance/ETP/loot: see `etp_sanity.py`, `loot_sanity.py`, and `docs/balance/`.
