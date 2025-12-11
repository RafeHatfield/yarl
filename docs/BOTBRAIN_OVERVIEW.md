# BotBrain & Soak Pipeline (Phase 15A)

## Data flow
- `BotBrain.decide_action(game_state)` (policy, state machine, personas)  
  → `BotInputSource.next_action()` (throttle, action source abstraction, telemetry tap)  
  → `engine_integration.create_renderer_and_input_source()` (selects bot input when `input_config.bot_enabled` or soak)  
  → Turn pipeline (`InputSystem` → `ActionProcessor` → ECS systems)  
  → Optional soak harness wrapping multiple runs.

## Telemetry
- Bot-specific telemetry stays in `io_layer/bot_metrics.py`.
- `BotInputSource` records per-decision telemetry (action type, reason, context flags) via `BotMetricsRecorder` when provided in `constants["bot_metrics_recorder"]`.
- `BotRunSummary` aggregates:
  - `total_steps`, `floors_seen`
  - `action_counts` (move/attack/auto-explore/potion/etc.)
  - Context counters (combat/explore/loot/low_hp/floor_complete)
  - Reason counts (e.g., `heal_low_hp`, `combat_engage`, `descend`)

## Soak harness
- `engine/soak_harness.run_bot_soak(...)` now instantiates a bot metrics recorder per run and passes it through `constants` to bot input.
- Summaries are attached to `SoakRunResult` (CSV fields: `bot_steps`, `bot_floors`, `bot_actions`, `bot_contexts`, `bot_reasons`) and JSONL entries (`bot_summary`).
- Existing soak metrics (run_metrics, TelemetryService) remain unchanged; bot telemetry is additive and opt-in to soak.
