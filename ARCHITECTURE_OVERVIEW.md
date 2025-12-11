# Catacombs of YARL — Architecture Overview

This document summarizes the current architecture, highlights coupling/tech-debt hotspots, and proposes a staged refactor roadmap. It also names concrete refactor candidates that can be tackled independently. Scope is descriptive and planning-only; no code changes are proposed here.

## How to Use This Doc
- Audience: engineers/planners deciding where to change or not change the game.
- Read order: skim High-Level Architecture → Subsystems for entry points → Guardrails to avoid off-limits areas → Roadmap/Candidates for actionable refactors.
- Purpose: a map and a safety rail; it is not a mandate to rewrite systems.

## High-Level Architecture
- **Core loop & state**: Legacy `engine.py` game loop orchestrating input → action processing → AI/environment turns → rendering. Newer `engine/game_engine.py` + `engine_integration.py` provide a migration path toward system-based orchestration with `TurnManager` and protocolized IO.
- **ECS**: Entities with typed components (`components/*`, `ComponentRegistry`, `ComponentType`); systems/services operate on components. Entities still expose legacy attributes for compatibility.
- **Systems**: In `engine/systems` (AI, render, input, environment, performance) extending `System` base; legacy helpers in `systems/turn_controller.py` coordinate turn transitions with `GameStates` and optional `TurnManager`.
- **Services (gameplay logic)**: Single-source-of-truth modules (e.g., `services/movement_service.py`, `services/portal_manager.py`, `services/loot_controller.py`, `services/encounter_budget_engine.py`, `services/faction_engine.py`, `services/floor_state_manager.py`, `services/pickup_service.py`, `services/movement_service.py`, `services/mural_manager.py`, `services/telemetry_service.py`). These encapsulate mechanics that were formerly scattered.
- **Content/data**: YAML-driven entities, levels, scenarios (`config/*.yaml`, `config/entity_factory.py`, `config/level_template_registry.py`, `config/levels/scenario_*.yaml`). Loader layer in `loader_functions/initialize_new_game.py` and `loader_functions/data_loaders.py`.
- **Combat/Balance**: Combat math (`components/fighter.py`, `balance/hit_model.py`), ETP encounter budgeting (`balance/etp.py` + services), loot pity and tag system (`balance/pity.py`, `balance/loot_tags.py`).
- **Map generation**: `map_objects/game_map.py`, `map_objects/room_generators.py`, `map_objects/secret_door.py`, `config/level_templates.yaml` with template registry overrides.
- **Events**: `events/core.py`, `events/game_events.py` define an event bus and typed game events. Some systems use direct calls rather than events; the bus exists for decoupling.
- **Rendering/Input abstraction (IO layer)**: Protocols in `io_layer/interfaces.py`; concrete `ConsoleRenderer`, `KeyboardInputSource`, `BotInputSource` (`io_layer/console_renderer.py`, `io_layer/keyboard_input.py`, `io_layer/bot_input.py`). Main loop is decoupled from libtcod via `engine_integration.py`.
- **BotBrain / autoplay**: Bot decision engine (`io_layer/bot_brain.py`) used by `BotInputSource`; supports personas and soak/testing modes. Integrated with telemetry and scenario harness.
- **Scenario harness**: Scenario YAML + loader + invariants + metrics (`services/scenario_harness.py`, `services/scenario_level_loader.py`, `services/scenario_invariants.py`, `services/scenario_metrics.py`, configs in `config/levels/scenario_*.yaml`). Provides automated, CI-friendly simulations with metrics aggregation.
- **State management**: `state_management/*` and `state_machine/*` handle state definitions and transitions; `GameStates` remains the primary enum.
- **Memory/perf**: `memory/*`, `performance/*` for pooling, GC tuning, instrumentation.
- **Screens/UI**: `screens/*`, `ui/*`, `rendering/*`, `render_functions.py`, `death_screen.py`. Rendering is intended read-only; gameplay logic should live in services/systems.

### Rendering Boundary Guardrail (IO-only rendering)
- libtcod imports and console drawing live ONLY in renderer implementations (`io_layer/*renderer*.py`), `render_functions.py`, or entrypoints (`engine.py`, `engine/soak_harness.py`).
- Core logic (components, services, systems, GameCore/TurnStateAdapter) must not call libtcod or write to consoles; they surface data the renderer consumes.
- Visual effects are queued in core (`visual_effect_queue.py`) and rendered in IO (`io_layer/effect_renderer.py`); future sprite/screenshot frontends plug in by implementing `Renderer` and consuming the same queue/state without touching gameplay code.
- **Telemetry/metrics**: `instrumentation/*`, `services/telemetry_service.py`, run metrics in `instrumentation/run_metrics.py`, bot results logging in `engine_integration.py`.

## Subsystems (Responsibilities, Entry Points, Interactions)
- **ECS / Entities & Components**
  - Responsibilities: Entity composition, typed component lookup, ownership wiring.
  - Key entry points: `entity.py`, `components/component_registry.py`, components under `components/`.
  - Interactions: Services and systems fetch components via `ComponentType`; legacy attributes remain for compatibility.

.- **Turn & State**
  - Responsibilities: Turn sequencing, game-state transitions.
  - Key entry points: `GameStates`, `state_management/state_config.py`, `engine/turn_manager.py` (phased), `systems/turn_controller.py`.
  - Interactions: AISystem and Movement/Action processing consult `GameStates`/`TurnManager`; Render/Input systems obey state for mode-specific behavior.
  - Preferred API: `engine/turn_state_adapter.py` now fronts turn/phase queries and sync, wrapping `GameStates` + `TurnManager`.
  - Implementation note: TurnController and AISystem call `TurnManager.advance_turn()` directly (without explicit phase targeting) for sequential phase advancement, ensuring proper turn counting and listener notifications. The adapter's `advance_to_*_phase()` methods are idempotent helpers for specific use cases.
  - GameCore boundary: `engine/game_core.py` is the IO-agnostic façade holding `state_manager`, `turn_manager`, and a `TurnStateAdapter`. Entry loops hand it input actions and ask if the world should tick; it keeps `GameStates`/TurnManager phases aligned and surfaces the current frame state for renderers. New or migrated entrypoints should route turn orchestration through this façade instead of duplicating loop logic.

.- **Input**
  - Responsibilities: Acquire player intent, map to `ActionDict`.
  - Key entry points: `io_layer/keyboard_input.py`, `io_layer/bot_input.py`, `io_layer/interfaces.py`.
  - Interactions: `engine_integration.play_game_with_engine` pulls from `InputSource`; actions are processed into game logic (movement, inventory, targeting).

.- **Rendering**
  - Responsibilities: Visualizing state; no mutation.
  - Key entry points: `io_layer/console_renderer.py`, legacy `render_functions.py`, `rendering/*`, `engine/systems/render_system.py` (now mainly FOV/state updates, drawing bypassed when using renderer abstraction).
  - Interactions: Reads `game_state` (map, entities, messages, UI layout). Should avoid mutating gameplay state.

.- **AI System**
  - Responsibilities: Enemy turn processing, strategy dispatch, anti-recursion guards.
  - Key entry points: `engine/systems/ai_system.py` (turn queue, `_process_ai_turns`, per-entity processing).
  - Interactions: Uses `GameStates`/`TurnManager`, components (AI, Fighter, Pathfinding), services (status effects, turn controller).

.- **Combat & Effects**
  - Responsibilities: Attack/defense resolution, status effects, throwing, spells.
  - Key entry points: `components/fighter.py`, `throwing.py`, `spells/*`, `balance/hit_model.py`.
  - Interactions: Message log, stats tracking, faction checks, loot/XP, telemetry.

.- **Movement**
  - Responsibilities: Single-source player movement handling.
  - Key entry points: `services/movement_service.py`.
  - Interactions: Game map collision, door/portal/secret handling, camera updates, FOV recompute, status effects, message log, portal manager.

.- **Portals**
  - Responsibilities: Creation, linking, collision/teleportation, victory portal.
  - Key entry points: `services/portal_manager.py`, `engine/portal_system.py`, `components/portal.py`.
  - Interactions: MovementService, AISystem (portals in enemy pathing), services/visual effects, victory flow.

.- **Map Generation & World**
  - Responsibilities: Map tiles, room generation, secret doors, stair placement, entity spawn.
  - Key entry points: `map_objects/game_map.py`, `map_objects/room_generators.py`, `config/level_templates.yaml`, `config/level_template_registry.py`.
  - Interactions: Balance (ETP/pity), entity factory, services/floor_state_manager, faction tags, loot tags.

.- **Balance Systems (ETP, Loot/Pity, Knowledge)**
  - Responsibilities: Encounter budgeting, loot banding, pity mechanics, monster knowledge.
  - Key entry points: `balance/etp.py`, `services/encounter_budget_engine.py`, `balance/pity.py`, `balance/loot_tags.py`, `services/monster_knowledge.py`.
  - Interactions: Mapgen spawn decisions, loot drops, telemetry, tests/CI gating scripts.

.- **Inventory/Items/Equipment**
  - Responsibilities: Items, equipment slots, identification, usage effects.
  - Key entry points: `components/item.py`, `components/inventory.py`, `components/equipment.py`, `components/equippable.py`, `item_functions.py`, `equipment_slots.py`.
  - Interactions: Combat, messaging, UI, BotBrain decisions, pity/loot tags, identification manager.

.- **Services (Gameplay Glue)**
  - Responsibilities: Movement, pickup, portal manager, floor state, faction/hostility, encounter budget, loot controller, teleport visuals, telemetry.
  - Key entry points: `services/*.py`.
  - Interactions: Systems and input handlers call into these single-source modules to avoid drift.

.- **BotBrain / Autoplay (first-class)**
  - Responsibilities: Automated decision making for soak/bot runs; personas; stuck detection.
  - Key entry points: `io_layer/bot_brain.py`, `io_layer/bot_input.py`.
  - Interactions: Uses `GameStates`, FOV, factions, inventory heuristics; feeds actions through the same pipeline as keyboard input; integrates with telemetry and run metrics logging in `engine_integration.py`.

.- **Scenario Harness (first-class)**
  - Responsibilities: Scenario definitions, invariant checks, map building, metrics aggregation.
  - Key entry points: `services/scenario_harness.py`, `services/scenario_level_loader.py`, `services/scenario_invariants.py`, `services/scenario_metrics.py`, scenario YAML in `config/levels/scenario_*.yaml`.
  - Interactions: Uses entity factory and level templates to build controlled maps; can run with Bot policies; emits metrics for CI and balance regression; relies on existing action/turn pipeline.

.- **Telemetry & Instrumentation**
  - Responsibilities: Run metrics, floor metrics, bot summaries, profiling.
  - Key entry points: `services/telemetry_service.py`, `instrumentation/run_metrics.py`, `engine_integration._log_bot_results_summary`.
  - Interactions: Called on death/victory, during floors, and in soak runs; outputs logs/JSON for CI artifacts.

.- **UI / Screens**
  - Responsibilities: Panels, menus, death screen, sidebar, dialog.
  - Key entry points: `screens/*`, `ui/*`, `rendering/*`, `death_screen.py`.
  - Interactions: Renderers consume state; should remain read-only relative to gameplay.

.- **Input Handlers (legacy)**
  - Responsibilities: Map keyboard/mouse to actions (pre-abstraction).
  - Key entry points: `input_handlers.py`, `input/*`, `mouse_movement.py`.
  - Interactions: Largely superseded by `KeyboardInputSource` but still present; double paths can cause drift.

.- **CI & Scripts**
  - Responsibilities: Quick vs balance CI, ETP/loot checks, golden path, critical tests.
  - Key entry points: `.github/workflows/ci.yml`, `scripts/ci_quick.sh`, `run_golden_path_tests.py`, `run_critical_tests.py`, `scripts/ci_run_etp.sh`, `scripts/ci_run_loot.sh`.

## Coupling & Tech-Debt Hotspots
- **Dual turn/state pathways**: `GameStates` plus `TurnManager` and `TurnController` coexist; AISystem checks both. Risk of divergence; needs consolidation plan.
- **Legacy render/input paths**: `RenderSystem` still present for FOV/state updates; legacy input handlers coexist with `InputSource` abstraction. Potential for double-handling or drift.
- **GameMap sprawl**: `map_objects/game_map.py` mixes generation, ETP integration, loot pity hooks, secret doors, hazard managers, and spawn logic. High coupling to balance services and YAML overrides.
- **Engine entry duplication**: Legacy `engine.py` loop plus `engine_integration.play_game_with_engine()` and `engine/game_engine.py` coexist; migration not complete.
- **Component registry + legacy attrs**: Entities maintain both typed registry and direct attributes; potential for desync if not set through common helpers.
- **Services vs systems overlap**: Some responsibilities are split (e.g., rendering/FOV in system vs renderer; input in system vs InputSource). Clear ownership is improving but not finished.
- **Portal handling spread**: PortalManager is canonical, but MovementService and AISystem both touch portal transitions; ensure all portal interactions route through PortalManager.
- **Events underused**: Event bus exists but many flows use direct calls; mixed patterns increase coupling.
- **Tests/config coupling**: Mapgen and balance are tightly bound to YAML content; changing spawning or pity logic requires awareness of ETP tests and scenario invariants.

## What Not to Change Right Now (explicit guardrails)
- **Scenario harness**: Keep architecture and APIs stable; no re-architecture this year. Treat it as a first-class subsystem; only incremental hardening/coverage is acceptable.
- **BotBrain/autoplay**: Keep personas, decision pipeline, and BotInputSource intact; no major redesign. Iterations should be additive (heuristics, hooks) without breaking existing soak/CI usage.
- **Rendering/input abstraction contracts**: Do not remove the protocol layer (`io_layer/interfaces.py`) or revert to libtcod-coupled loops; avoid large rewrites of renderer/input unless extending via the protocol.
- **PortalManager contracts**: Do not create portals outside `PortalManager.create_portal_entity`; keep collision/linkage centralized.
- **ComponentRegistry invariants**: Do not bypass registry contracts or allow duplicate components; keep ComponentType mapping stable unless coordinated.
- **Balance engines (ETP/pity)**: Avoid wholesale redesign; changes must respect existing CI checks and tests.
- **Mapgen core algorithms**: No radical rework of room/tunnel generation; focus on targeted extraction/cleanup if needed.

## Phased Refactor Roadmap (pragmatic, incremental)
### Phase 1 — Low-risk hygiene and clarity
- Objectives: Reduce drift between duplicate paths; clarify ownership; improve naming/docs.
- Tasks:
  - Document current owner for input/render vs system responsibilities (short OWNERSHIP notes in relevant modules).
  - Add lightweight wrappers/helpers to ensure entities register components via ComponentRegistry (and optionally assert sync in debug).
  - Extract small helpers from `game_map.py` (e.g., ETP spawn checks, pity hooks) into thin functions/modules without changing behavior.
  - Add comments/tests to lock portal interactions to PortalManager (smoke tests ensuring MovementService uses it).
- Benefits: Less accidental drift; clearer contracts; safer future edits.
- Risks: Minimal; guard with tests already in place.

### Phase 2 — Boundary hardening
- Objectives: Sharpen separation between core logic and IO/render; reduce dual-path complexity.
- Tasks:
  - Consolidate input handling to `InputSource` path; deprecate or gate legacy `InputSystem` usage where safe (feature-flag or testing path).
  - Make `RenderSystem` explicitly non-drawing (FOV/state only) and ensure renderer handles drawing; assert against double-render.
  - Clarify turn-state authority: introduce a single adapter that keeps `GameStates` and `TurnManager` in sync; route AISystem checks through it.
- Benefits: Fewer entry paths; clearer layering; easier to swap render/input backends.
- Risks: State transition regressions; mitigate with golden-path and AI/portal tests.

### Phase 3 — Structural cleanup in high-coupling areas
- Objectives: Modularize mapgen/balance seams; reduce sprawl in `game_map.py`.
- Tasks:
  - Extract spawn/ETP concerns into a `spawn_controller` helper that `GameMap` calls (no behavior change).
  - Move pity/loot band decisions behind a small interface used by mapgen and drop code.
  - Add thin event hooks (or service calls) for mapgen post-processing (secrets/doors) to reduce cross-file imports.
- Benefits: Localizes balance touchpoints; easier to reason about mapgen changes; lowers risk of circular imports.
- Risks: Must preserve existing spawn distributions; rely on ETP/loot CI and scenario invariants.

### Phase 4 — Optional consolidation (only if/when safe)
- Objectives: Align the engine loop with the system architecture without breaking legacy flows.
- Tasks:
  - Define a single orchestrator entry (engine integration) that wires Renderer/InputSource and systems, keeping `engine.py` as thin wrapper.
  - Gradually retire unused legacy `InputSystem`/render draw paths once parity is proven.
- Benefits: Cleaner entrypoint; simpler mental model.
- Risks: Medium; defer until prior phases stable.

## Concrete Refactor Candidates (Codex-ready, self-contained)
- **Turn state adapter**: Create a `TurnStateAdapter` that provides `is_enemy_phase()`, `advance_to_player()`, and keeps `GameStates`/`TurnManager` consistent. Update AISystem and TurnController to depend on it.
- **Render responsibility clarification**: Guard `RenderSystem` to skip drawing and only handle FOV/state prep; add a small test to ensure `ConsoleRenderer` is the sole drawing path when abstraction is enabled.
- **Input path unification**: Add a feature flag to disable legacy input handlers during normal runs; ensure all inputs go through `InputSource` and action processing; add a smoke test that asserts no `handle_keys` path is hit when the flag is on.
- **Mapgen spawn extraction**: Extract ETP/pity spawn decisions from `GameMap` into a `spawn_rules` module used by `make_map`; no behavior change, but isolates balance logic.
- **Portal pipeline audit**: Add a portal interaction test that ensures MovementService and AISystem route through PortalManager (no direct teleports), preventing future drift.
- **BotBrain hooks**: Add extension hooks (callbacks) for BotBrain decisions (e.g., on engage/loot/retreat) without changing personas; enables future tuning while keeping current behavior.

## Notes on Scenario Harness & BotBrain Placement
- **Scenario harness** is a first-class subsystem for deterministic, CI-friendly simulations. It builds maps from scenario YAML, enforces invariants, runs with bot policies, and aggregates metrics. Keep it stable; use it as the proving ground for balance and regression, not as an experimental playground.
- **BotBrain/autoplay** is a first-class input provider. It must continue to use the same action pipeline as keyboard input, honoring state/turn rules. Treat personas and stuck detection as user-facing stability features; extensions should be additive and guarded by tests/soak runs.

## Future Axes (enabled by a clean GameCore boundary)
- Screensaver/autoplay frontend (headless or minimal-UI loop driven by BotBrain/InputSource).
- Sprite renderer (alternate Renderer impl behind the existing protocol).


