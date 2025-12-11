# Catacombs of YARL — Architecture Refactor Backlog

_Purpose_: Track future architecture work once we resume refactors. Keep changes small, respect existing guardrails, and align with `ARCHITECTURE_OVERVIEW.md` and `ROADMAP.md`.

## Do Not Touch Without Human Approval
- Scenario harness core loop
- `ecosystem_sanity` and `worldgen_sanity` invariants
- Portal invariants
- `item_component` / `equip_component` structure
- Balance YAML formats (schema level)
- Mapgen topology rules

## Safe Entry Points for Refactors
- IO layer (renderers, input sources)
- AISystem → adapter transitions
- TurnController → adapter transitions
- `spawn_service` expansion
- `portal_manager` logic improvements (not schema)

## Recommended Next Refactors (when ready)
- **Phase 14A – Input path unification** — High value: retire duplicate input paths; stabilizes action ingestion. Tests: golden path, `engine_integration` smoke, input handler unit tests. Blast: input handlers, `engine_integration`, bot input. Tag: Codex-scale refactor.
- **Phase 14B – Render responsibility hardening** — High value: enforce render-as-read-only, prevent double-render. Tests: golden path visuals checks, `worldgen_sanity` for FOV stability. Blast: `RenderSystem`, `ConsoleRenderer`, IO layer. Tag: Codex-scale refactor.
- **Phase 14C – Turn authority consolidation** — High value: single authority for turn/phase via `TurnStateAdapter`. Tests: AI turns, portal invariants, golden path. Blast: AISystem, TurnManager, TurnController callers. Tag: Codex-scale refactor.
- **Phase 14D – GameMap sprawl extraction** — High value: isolate spawn/ETP/pity hooks to reduce coupling. Tests: `ecosystem_sanity.py`, `worldgen_sanity.py`, ETP/loot CI scripts. Blast: mapgen, balance, spawn_service. Tag: Codex-scale refactor.
- **Phase 14E – Portal pathway audit** — Medium value: ensure all portal interactions go through PortalManager. Tests: `services/portal_invariants.py`, portal_network scenario. Blast: MovementService, AISystem pathing, portal visuals. Tag: Safe for small model with guidance.
- **Phase 14F – BotBrain hook points** — Medium value: add extension hooks without changing personas. Tests: soak harness, golden path, telemetry summaries. Blast: BotBrain, BotInputSource, telemetry. Tag: Safe for small model.
- **Phase 14G – Component registry drift checks** — Medium value: add assertions/wrappers to prevent legacy attr desync. Tests: component unit tests, golden path. Blast: entity creation helpers, components. Tag: Safe for small model.
- **Phase 14H – System/service ownership notes** — Low value, cheap clarity: add ownership notes; reduce overlap. Tests: none required; verify via lint/docs. Blast: comments/docs only. Tag: Safe for small model.
- **Phase 14I – Event bus adoption pilot** — Medium value: add thin event hooks where direct calls cause coupling. Tests: targeted unit tests; golden path. Blast: services touching mapgen/combat events. Tag: Codex-scale refactor.

## Subsystem Backlog (responsibilities, hotspots, opportunities)

### Engine Entrypoints & GameCore / TurnStateAdapter
- Responsibilities: Orchestrate loop via `engine_integration.py` and `engine/game_engine.py`; `GameCore` + `TurnStateAdapter` keep `GameStates` and `TurnManager` aligned; IO-agnostic frame handoff.
- Hotspots:
  - Dual entry loops (`engine.py` vs `engine_integration`) cause drift.
  - Turn-state authority split among `GameStates`, `TurnManager`, `TurnController`.
  - Replay/soak paths share code partially.
- Opportunities:
  - **Turn authority consolidation** — Risk: Medium; Blast: AISystem, TurnController, tests around turns; Approach: route all turn checks through adapter, add invariants; Guards: golden path, portal invariants; Tag: Codex-scale refactor.
  - **Single orchestrator wrapper** — Risk: Medium; Blast: entry scripts, renderer/input wiring; Approach: thin wrapper that always uses GameCore; Guards: golden path; Tag: Human-only / design-doc first.

### ECS & ComponentRegistry
- Responsibilities: Typed component lookup, registry invariants, legacy attrs for compatibility.
- Hotspots:
  - Duplicate state between registry and legacy attributes.
  - Ad-hoc component attachment bypassing helpers.
- Opportunities:
  - **Component registry drift checks** — Risk: Medium; Blast: entity creation; Approach: small helper/assert during attach; Guards: unit tests, golden path; Tag: Safe for small model.
  - **Migration helpers for legacy attrs** — Risk: Medium; Blast: components/services relying on attrs; Approach: add shims, log mismatches; Guards: golden path; Tag: Codex-scale refactor.

### Systems (movement, combat, AI, environment, render/input systems)
- Responsibilities: Phase-based updates over ECS state; should avoid gameplay duplication with services.
- Hotspots:
  - Overlap between systems and services (render/input/turn logic).
  - AISystem touching turn advancement directly.
  - RenderSystem still doing some FOV/state work.
- Opportunities:
  - **Render responsibility hardening** — Risk: Medium; Blast: RenderSystem, renderer; Approach: enforce read-only render, FOV-only in system; Guards: golden path visuals, `worldgen_sanity`; Tag: Codex-scale refactor.
  - **Input path unification** — Risk: Medium; Blast: InputSystem, InputSource; Approach: feature-flag legacy path off; Guards: golden path input tests; Tag: Codex-scale refactor.
  - **Turn calls via adapter** — Risk: Medium; Blast: AISystem; Approach: replace direct TurnManager calls with adapter; Guards: AI turn tests; Tag: Safe for small model.

### IO Layer (renderers, input sources, bot input)
- Responsibilities: IO abstraction (Renderer/InputSource); BotInputSource uses BotBrain; KeyboardInputSource; ConsoleRenderer.
- Hotspots:
  - Legacy input handlers still reachable.
  - Renderer vs RenderSystem overlap; potential double-render.
  - Bot input path should stay identical to keyboard pipeline.
- Opportunities:
  - **Input path unification** — Risk: Medium; Blast: input handlers, bot input; Approach: gate legacy handlers, assert InputSource usage; Guards: golden path, soak harness; Tag: Codex-scale refactor.
  - **Bot input parity checks** — Risk: Low; Blast: bot/keyboard parity; Approach: add invariant to ensure shared pipeline; Guards: soak harness; Tag: Safe for small model.

### Map Generation & spawn_service
- Responsibilities: Map tiles/rooms, spawn population, secret doors; spawn_service now centralizes spawning decisions.
- Hotspots:
  - `map_objects/game_map.py` sprawl (generation, ETP, pity, secrets, hazards).
  - Tight coupling to balance YAML and services.
- Opportunities:
  - **GameMap sprawl extraction** — Risk: Medium; Blast: mapgen, balance services, spawn_service; Approach: extract spawn/ETP/pity helpers called by GameMap; Guards: `ecosystem_sanity.py`, `worldgen_sanity.py`, ETP/loot CI; Tag: Codex-scale refactor.
  - **Spawn_service consolidation** — Risk: Medium; Blast: entity factory, balance; Approach: ensure spawn decisions route through spawn_service APIs; Guards: same as above; Tag: Safe for small model.

### Scenario Harness + ecosystem_sanity + worldgen_sanity
- Responsibilities: Scenario definitions/loading, invariants, metrics; sanity harnesses guard worldgen/balance.
- Hotspots:
  - Coupling to YAML templates; brittle if mapgen contracts change.
  - Metrics/invariants spread across files.
- Opportunities:
  - **Scenario invariant cataloging** — Risk: Low; Blast: docs/tests only; Approach: document invariants and expected contracts; Guards: scenario invariants; Tag: Safe for small model.
  - **Harness extensibility hooks** — Risk: Medium; Blast: scenario harness; Approach: add optional extension points without altering core; Guards: existing invariants; Tag: Human-only / design-doc first.

### BotBrain / Bot soak harness
- Responsibilities: Automated decision-making; integrates with InputSource; used by soak/CI.
- Hotspots:
  - Heuristics intertwined; limited hook points.
  - Telemetry/logging paths partially duplicated.
- Opportunities:
  - **BotBrain hook points** — Risk: Low/Medium; Blast: BotBrain, telemetry; Approach: add callbacks for engage/loot/retreat; Guards: soak harness; Tag: Safe for small model.
  - **Stuck detection hardening** — Risk: Medium; Blast: bot runs; Approach: add invariants for repeated states; Guards: soak harness; Tag: Codex-scale refactor.

### Portals and PortalManager
- Responsibilities: Creation/linking, movement collisions, victory portal; invariants in `portal_invariants`.
- Hotspots:
  - MovementService and AISystem touch portal transitions; risk of bypassing PortalManager.
  - Visual effects and collisions intertwined.
- Opportunities:
  - **Portal pathway audit** — Risk: Medium; Blast: MovementService, AISystem, portal visuals; Approach: assert all teleports go through PortalManager; Guards: `portal_invariants.py`, portal_network scenario; Tag: Safe for small model.
  - **Portal visual/logic split** — Risk: Medium; Blast: portal visuals, services; Approach: separate VFX queueing from logic; Guards: portal invariants; Tag: Codex-scale refactor.

### Balance / ETP / Loot / Pity infrastructure
- Responsibilities: Encounter budgeting, loot banding/pity, tag-driven drops, monster knowledge.
- Hotspots:
  - Coupled to mapgen and spawn decisions; YAML-sensitive.
  - Shared utilities between `balance/*` and services can drift.
- Opportunities:
  - **Balance API surface cleanup** — Risk: Medium/High; Blast: mapgen, loot drops, tests; Approach: thin interface layer used by mapgen/spawn; Guards: ETP/loot CI, ecosystem/worldgen sanity; Tag: Human-only / design-doc first.
  - **Pity hooks isolation** — Risk: Medium; Blast: drop tables; Approach: isolate pity decisions behind service call; Guards: loot CI; Tag: Codex-scale refactor.

### Scenario/Portal/Bot Cross-cutting Tests & Invariants (reference)
- `ecosystem_sanity.py`, `worldgen_sanity.py` — mapgen/balance safety nets.
- `services/portal_invariants.py` + portal_network scenario — portal correctness.
- Scenario harness (`services/scenario_harness.py`, configs in `config/levels/scenario_*.yaml`) — deterministic simulations.
- Soak harness (`engine/soak_harness.py`) — long-run stability; bot parity.
- Golden path scripts (`run_golden_path_tests.py`) — overall regressions.

## Pre-flight Checklist Before Any Codex Refactor
- Before changes:
  - Run `pytest` — everything green?
  - Run `make eco-ci` — green?
  - Run `make worldgen-ci` — green?
  - Run scenario_portal_network — invariants hold?
- After changes:
  - Repeat all four and compare outputs.

## Guidance for tackling items
- Favor incremental slices; add invariants/tests before behavior changes.
- Keep rendering IO-only and route all gameplay through services/systems (see `ARCHITECTURE_OVERVIEW.md` Rendering Boundary Guardrail).
- Prefer extending existing abstractions over introducing new patterns.

## Relationships to other docs
- See `ARCHITECTURE_OVERVIEW.md` for current architecture, guardrails, and the phased roadmap up to Phase 14.
- See `ROADMAP.md` for feature/balance planning; align refactors with feature work to minimize churn.
