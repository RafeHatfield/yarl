# Bot Design Documentation

## Overview

The bot system provides automated gameplay for testing, telemetry collection, and soak testing. It consists of two main components:

1. **BotBrain** (`io_layer/bot_brain.py`): Decision-making state machine (EXPLORE, COMBAT, LOOT)
2. **BotInputSource** (`io_layer/bot_input.py`): Input source adapter that delegates to BotBrain

## BotBrain Architecture

### State Machine

BotBrain implements a simple state machine with three states:

- **EXPLORE**: Systematic dungeon exploration using AutoExplore component
- **COMBAT**: Attack enemies within range (Manhattan distance ≤ 8)
- **LOOT**: Pick up items when standing on them

### EXPLORE State Contract

**Critical Contract:** BotBrain.EXPLORE delegates entirely to AutoExplore.

**Behavior:**
1. BotBrain.EXPLORE checks if AutoExplore is active via `AutoExplore.is_active()`
2. If NOT active: Returns `{"start_auto_explore": True}` to start AutoExplore once
3. If ACTIVE: Returns `{}` (empty dict) to let AutoExplore handle movement
4. BotBrain does NOT interfere with AutoExplore while it's running
5. BotBrain does NOT restart AutoExplore unless AutoExplore has stopped for a valid reason

**Why This Design:**
- AutoExplore owns all exploration logic (pathfinding, room-by-room exploration, stop conditions)
- BotBrain is a thin wrapper that starts AutoExplore and then stands back
- This prevents restart loops and ensures exploration completes correctly

**Restart Behavior:**
- BotBrain should NEVER restart AutoExplore if AutoExplore stopped with "All areas explored"
- AutoExplore.start() now checks for unexplored tiles BEFORE activating
- If no unexplored tiles exist, AutoExplore refuses to activate (returns "Nothing left to explore")
- BotBrain receives `{}` (no-ops) when AutoExplore is inactive after completion

### COMBAT State

**Behavior:**
- Enters COMBAT when enemies are within Manhattan distance ≤ 8
- Attacks adjacent enemies immediately
- Moves toward non-adjacent enemies
- Includes anti-stuck logic to prevent infinite loops:
  - Oscillation detection (A ↔ B ↔ A ↔ B pattern)
  - Stuck counter (no progress for N turns)
  - No-op fail-safe (consecutive no-op actions)

**Stuck Handling:**
- COMBAT anti-stuck logic lives in BotBrain (not in EXPLORE)
- EXPLORE does NOT have anti-stuck logic (AutoExplore handles its own termination)
- When stuck in COMBAT, BotBrain drops to EXPLORE state

### LOOT State

**Behavior:**
- Enters LOOT when player is standing on an item
- Returns `{"pickup": True}` action
- Transitions back to EXPLORE after pickup

## AutoExplore Integration

### Contract

AutoExplore component (`components/auto_explore.py`) provides the exploration engine:

1. **Start Contract:**
   - `AutoExplore.start()` checks for unexplored tiles BEFORE activating
   - If no unexplored tiles exist: `active=False`, `stop_reason="All areas explored"`, returns "Nothing left to explore"
   - If unexplored tiles exist: `active=True`, begins exploration

2. **Runtime Contract:**
   - Each turn: `AutoExplore.get_next_action()` returns `{'dx': dx, 'dy': dy}` or `None`
   - When complete: `active=False`, `stop_reason` set to reason (e.g., "All areas explored")

3. **Stop Reasons:**
   - "All areas explored" - Map fully explored (terminal condition)
   - "Monster spotted" - Hostile enemy detected
   - "Found chest" - Chest discovered
   - "Damage taken" - Player took damage
   - Other stop conditions as needed

### Lifecycle

```
BotBrain.EXPLORE → Check AutoExplore.is_active()
    │
    ├─→ NOT active → Return {"start_auto_explore": True}
    │                  → ActionProcessor calls AutoExplore.start()
    │                  → AutoExplore checks unexplored tiles
    │                     ├─→ None found → Refuses to activate, returns "Nothing left to explore"
    │                     └─→ Found → Activates, begins exploration
    │
    └─→ ACTIVE → Return {} (no-op)
                 → ActionProcessor calls AutoExplore.get_next_action()
                 → AutoExplore returns movement or None
                 → When None: AutoExplore stops, active=False
```

## Logging Tiers

BotBrain supports three logging tiers:

1. **SUMMARY** (default): State transitions, AutoExplore lifecycle events
   - State transitions (EXPLORE → COMBAT, etc.)
   - AutoExplore start/stop events
   - Bot run completion reason

2. **DEBUG**: Verbose turn-by-turn details
   - All summary logs plus:
   - Player position, target, visible enemies
   - Action decisions, stuck counters
   - Oscillation detection

3. **ERROR**: Only contract violations or impossible states
   - Should rarely be used
   - Reserved for actual bugs or contract violations

**Usage:**
```python
bot_brain = BotBrain(log_level=LogLevel.SUMMARY)  # Default
bot_brain = BotBrain(log_level=LogLevel.DEBUG)    # Verbose
bot_brain = BotBrain(debug=True)                   # Also sets DEBUG level (backward compat)
```

## Bot Results Summary

After each bot run (when running with `--bot` or `--bot-soak`), a lightweight summary is printed:

```
============================================================
🤖 Bot Run Results
============================================================
   Outcome: Completed (all explored)
   Floors Explored: 3
   Deepest Floor: 3
   Enemies Killed: 12
   Turn Count: 450
   Tiles Explored: 1250
   Duration: 45.3s
============================================================
```

This summary appears:
- On bot run completion (bot_completed outcome)
- On bot death
- On bot quit
- On bot victory

It is only printed when bot mode is enabled (`constants["input_config"]["bot_enabled"] = True`).

## Testing

### Gold Regression Tests

The contract is enforced by gold regression tests in `tests/test_bot_autoexplore_corridor_bug.py`:

1. **test_fully_explored_map_autoexplore_refuses_to_start**: Ensures AutoExplore never activates when map is fully explored
2. **test_fully_explored_map_botbrain_returns_noops**: Ensures BotBrain returns {} when AutoExplore refuses to start
3. **test_corridor_exploration_completes_without_restart_loop**: Ensures AutoExplore starts once, explores, stops, never restarts
4. **test_branch_map_exploration_completes_correctly**: Ensures exploration works correctly with branches (T-junctions)

These tests explicitly assert on:
- AutoExplore not activating when no unexplored tiles exist
- `stop_reason` correctness
- BotBrain receiving {} (no-ops) only
- No movement commands emitted when map is fully explored
- AutoExplore start count ≤ 2 (prevents restart loops)

## Future Improvements

### BotBrain Stop Condition

Currently, BotBrain will keep calling `start_auto_explore` even when it returns "Nothing left to explore". This is harmless (AutoExplore refuses to activate), but could be optimized:

```python
def _handle_explore(self, player: Any, game_state: Any) -> Dict[str, Any]:
    is_active = self._is_autoexplore_active(game_state)
    
    if not is_active:
        # Check if AutoExplore stopped because map is fully explored
        auto_explore = player.get_component_optional(ComponentType.AUTO_EXPLORE)
        if auto_explore and auto_explore.stop_reason == "All areas explored":
            # Map is fully explored - do something else (wait, return to town, etc.)
            return {"wait": True}
        
        # Otherwise, start autoexplore
        return {"start_auto_explore": True}
    else:
        return {}
```

This would allow the bot to recognize completion and transition to another behavior (waiting, returning to town, looking for stairs, etc.).

## Related Documentation

- [BOT_AUTOEXPLORE_FIX_SUMMARY.md](../BOT_AUTOEXPLORE_FIX_SUMMARY.md): Detailed fix documentation with lifecycle flowchart
- [BOT_SOAK_HARNESS.md](BOT_SOAK_HARNESS.md): Bot soak testing harness documentation
- [AutoExplore Component](../components/auto_explore.py): AutoExplore component implementation

