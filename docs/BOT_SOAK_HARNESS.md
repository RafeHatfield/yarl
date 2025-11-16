# Phase 1.6: Bot Soak Harness

## Overview

The Bot Soak Harness enables running multiple bot games back-to-back for stability testing, telemetry collection, and performance analysis. This feature is designed for unattended execution and produces structured output for analysis.

## Features

- **Multiple Sequential Runs**: Execute N bot games in sequence
- **Per-Run Metrics**: Capture run_metrics and telemetry for each run
- **Session Aggregation**: Compute aggregate statistics across all runs
- **JSONL Output**: Write per-run telemetry to structured JSONL format
- **Crash Handling**: Gracefully handle and report bot crashes
- **Clean State**: Reset global state between runs for independence

## Usage

### Basic Usage

Run 10 bot games (default):

```bash
python3 engine.py --bot-soak
```

### Custom Number of Runs

Run a specific number of games:

```bash
python3 engine.py --bot-soak --runs 50
```

### Custom Telemetry Path

Specify telemetry output location:

```bash
python3 engine.py --bot-soak --runs 20 --telemetry-json telemetry/my_soak.json
```

This will create:
- `telemetry/my_soak_soak_YYYYMMDD_HHMMSS.jsonl` - Per-run telemetry

## Output

### Session Summary (stdout)

After all runs complete, a summary is printed:

```
============================================================
🧪 Bot Soak Session Summary
============================================================
   Runs: 10
   Completed: 10
   Crashes: 0

   Session Duration: 450.3s
   Avg Run Duration: 45.0s
   Avg Deepest Floor: 2.8
   Avg Floors per Run: 2.8
   Total Monsters Killed: 42
============================================================

📋 Per-Run Breakdown:
Run   Outcome      Duration   Floor   Kills   Exception
----------------------------------------------------------------------
1     death        42.1s      3       5       
2     death        48.3s      2       3       
3     death        44.5s      3       6       
...
```

### JSONL Telemetry Output

Each line in the JSONL file is a complete JSON object for one run:

```json
{
  "run_metrics": {
    "run_id": "abc123...",
    "mode": "bot",
    "outcome": "death",
    "duration_seconds": 42.1,
    "deepest_floor": 3,
    "floors_visited": 3,
    "monsters_killed": 5,
    "tiles_explored": 234,
    "steps_taken": 567,
    "start_time_utc": "2025-11-16T12:00:00Z",
    "end_time_utc": "2025-11-16T12:00:42Z"
  },
  "telemetry": {
    "floor_count": 3,
    "avg_etp_per_floor": 25.5,
    "total_traps": 2,
    "total_secrets": 1,
    "total_doors": 5,
    "total_keys": 2
  },
  "timestamp": "2025-11-16T12:00:42.123456Z"
}
```

## Architecture

### Key Components

#### `SoakRunResult`
Per-run metrics snapshot combining:
- RunMetrics (from instrumentation/run_metrics.py)
- Telemetry stats (from services/telemetry_service.py)
- Exception info if run crashed

#### `SoakSessionResult`
Aggregate session statistics:
- Total/completed/crashed runs
- Average duration, floor depth, kills
- Per-run breakdown

#### `run_bot_soak()`
Main orchestration function:
1. Loop over N runs
2. For each run:
   - Reset global singletons (run_metrics, telemetry)
   - Create new game with bot mode enabled
   - Call `play_game_with_engine()` (reuses existing game loop)
   - Capture metrics and telemetry
   - Write to JSONL
3. Compute session aggregates
4. Print summary

### State Reset Between Runs

To ensure each run is independent, the harness resets:
- `reset_run_metrics_recorder()` - Clear previous run metrics
- `reset_telemetry_service()` - Clear previous telemetry data

This prevents data accumulation across runs.

### Integration Points

The harness integrates cleanly with existing systems:
- **Bot Mode**: Uses existing `BotInputSource` (Phase 1 auto-explore)
- **Run Metrics**: Reuses `RunMetricsRecorder` (Phase 1.5)
- **Telemetry**: Reuses `TelemetryService` (Phase 1.5b)
- **Game Loop**: Calls `play_game_with_engine()` directly (no duplication)

## Testing

### Unit Tests

7 tests in `tests/test_bot_soak.py`:

1. **SoakRunResult**:
   - `test_from_run_metrics_and_telemetry_with_valid_metrics`
   - `test_from_run_metrics_and_telemetry_with_none_metrics`

2. **SoakSessionResult**:
   - `test_compute_aggregates_with_multiple_runs`
   - `test_compute_aggregates_filters_crashed_runs`
   - `test_print_summary_does_not_crash`

3. **Integration**:
   - `test_run_bot_soak_completes_multiple_runs`
   - `test_run_bot_soak_handles_exceptions`

All tests use mocking to avoid actual game execution.

### Regression Tests

Existing tests still pass:
- `tests/test_run_metrics.py` (23 tests)
- `tests/test_telemetry_floors.py` (15 tests)

## Use Cases

### Stability Testing

Run 100+ games overnight to detect crashes:

```bash
nohup python3 engine.py --bot-soak --runs 100 &
```

Check for non-zero `bot_crashes` in summary.

### Performance Profiling

Measure average run characteristics:

```bash
python3 engine.py --bot-soak --runs 50 --telemetry-json telemetry/profile.json
```

Analyze JSONL for duration trends, floor depth distribution, etc.

### Telemetry Collection

Gather large datasets for balance analysis:

```bash
python3 engine.py --bot-soak --runs 200 --telemetry-json telemetry/balance_data.json
```

Parse JSONL to compute:
- ETP distribution per floor
- Average TTK/TTD
- Item/trap/secret spawn rates

## Safety & Constraints

### What This Does NOT Change

- ✅ AI system logic (enemies still disabled in bot mode per Phase 0)
- ✅ Rendering system (still uses existing renderers)
- ✅ Input system (still uses BotInputSource)
- ✅ Run metrics structure (reuses existing RunMetrics)
- ✅ Telemetry structure (reuses existing TelemetryService)

### Additive Design

All changes are additive:
- New CLI flags (`--bot-soak`, `--runs`)
- New module (`engine/soak_harness.py`)
- New tests (`tests/test_bot_soak.py`)
- No modifications to existing game logic

### Known Limitations

1. **Headless-ish Mode**: Still initializes libtcod consoles (not fully headless)
2. **Sequential Only**: Runs execute sequentially, not in parallel
3. **Bot Phase 1**: Only auto-explore, no combat (enemies disabled)

## Future Enhancements

Potential improvements (not in Phase 1.6):

- `--max-duration-seconds X` per-run timeout
- `--parallel N` to run N bots simultaneously
- `--soak-out DIR` to separate output directory
- Full headless mode (no console initialization)
- Bot combat once enemies are enabled (post-Phase 1)

## Development Notes

### Branch

Feature developed in: `phase-1.6-bot-soak-harness`

### Commit Message

```
Phase 1.6: Implement Bot Soak Harness

- Add CLI flags: --bot-soak and --runs N
- Create engine/soak_harness.py with SoakRunResult/SoakSessionResult
- Orchestrate N sequential bot runs with state reset between runs
- Output JSONL telemetry + session summary to stdout
- 7 new tests, all existing tests pass
- Additive only - no changes to AI, rendering, input logic
```

### Testing Workflow

1. Run unit tests:
   ```bash
   python3 -m pytest tests/test_bot_soak.py -v
   ```

2. Run integration tests:
   ```bash
   python3 -m pytest tests/test_bot_soak.py tests/test_run_metrics.py tests/test_telemetry_floors.py -v
   ```

3. Manual smoke test:
   ```bash
   python3 engine.py --bot-soak --runs 3
   ```

### Files Modified

- `engine.py`: Add CLI flags, hook soak harness in main()
- `engine/soak_harness.py`: New module (230 lines)
- `tests/test_bot_soak.py`: New test file (350+ lines)

### Files NOT Modified

- AI system (`engine/systems/ai_system.py`)
- Rendering (`rendering/*`, `io_layer/console_renderer.py`)
- Input (`io_layer/bot_input.py`, `io_layer/keyboard_input.py`)
- Run metrics structure (`instrumentation/run_metrics.py`)
- Telemetry structure (`services/telemetry_service.py`)

## See Also

- [Phase 1: Bot Mode (Auto-Explore)](BOT_MODE_PHASE1_AUTO_EXPLORE.md)
- [Phase 1.5: Run Metrics](RUN_METRICS_IMPLEMENTATION.md)
- [Phase 1.5b: Telemetry Floor Wiring](INSTRUMENTATION_SUMMARY.md)

