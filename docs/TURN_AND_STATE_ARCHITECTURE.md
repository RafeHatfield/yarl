# Turn Manager & Game States Architecture

**Status:** Production | **Last Updated:** January 2025

## Purpose

This document explains the relationship between `TurnPhase` (turn sequencing) and `GameStates` (UI modes), why both exist, and how they work together.

---

## Executive Summary

**TL;DR:** `TurnPhase` and `GameStates` serve **different purposes** and should coexist:

| System | Purpose | Examples | Lifecycle |
|--------|---------|----------|-----------|
| **TurnPhase** | Turn sequencing & combat flow | PLAYER → ENEMY → ENVIRONMENT | Cycles continuously during gameplay |
| **GameStates** | UI mode & input routing | SHOW_INVENTORY, TARGETING, CHARACTER_SCREEN | Changes based on player input |

---

## The Two Systems

### 1. TurnPhase (Turn Sequencing)

**File:** `engine/turn_manager.py`

**Purpose:** Manage the combat turn sequence - who acts when?

```python
class TurnPhase(Enum):
    PLAYER = "player"           # Player's turn to act
    ENEMY = "enemy"             # AI monsters act
    ENVIRONMENT = "environment" # Hazards, traps, weather
```

**Lifecycle:**
```
Turn 1: PLAYER → ENEMY → ENVIRONMENT
Turn 2: PLAYER → ENEMY → ENVIRONMENT
Turn 3: PLAYER → ENEMY → ENVIRONMENT
... (repeats forever during gameplay)
```

**Responsibilities:**
- ✅ Turn sequencing (who acts next?)
- ✅ Combat flow (player → enemies → environment)
- ✅ Turn counter (what turn number are we on?)
- ✅ Phase listeners (systems register to act during specific phases)

**When it matters:**
- During active gameplay
- Combat encounters
- Real-time action processing

---

### 2. GameStates (UI Modes)

**File:** `game_states.py`

**Purpose:** Manage UI modes and input routing - what screen is the player looking at?

```python
class GameStates(Enum):
    PLAYERS_TURN = 1        # Normal gameplay (playing)
    ENEMY_TURN = 2          # Watching AI act
    PLAYER_DEAD = 3         # Game over screen
    SHOW_INVENTORY = 4      # Inventory menu open
    DROP_INVENTORY = 5      # Drop item menu open
    TARGETING = 6           # Targeting spell/item
    LEVEL_UP = 7            # Level up menu
    CHARACTER_SCREEN = 8    # Character stats screen
```

**Lifecycle:**
```
PLAYERS_TURN                # Playing normally
  → SHOW_INVENTORY         # Press 'i' to open inventory
    → PLAYERS_TURN         # Press ESC to close
  → TARGETING              # Use targeting spell
    → PLAYERS_TURN         # Cancel or complete targeting
  → CHARACTER_SCREEN       # Press 'c' for stats
    → PLAYERS_TURN         # Press ESC to close
```

**Responsibilities:**
- ✅ UI mode (what menu is open?)
- ✅ Input routing (where do keypresses go?)
- ✅ Rendering mode (what to draw?)
- ✅ Pause state (game paused while in menus)

**When it matters:**
- Input handling (different keys do different things in different states)
- Rendering (draw inventory overlay vs normal game view)
- Game logic (pause combat while in menus)

---

## How They Work Together

### Example: Player Opens Inventory During Combat

```python
# Current state
TurnPhase: PLAYER
GameState: PLAYERS_TURN

# Player presses 'i' to open inventory
TurnPhase: PLAYER           # ← Turn phase doesn't change!
GameState: SHOW_INVENTORY   # ← GameState changes to show menu

# Player closes inventory
TurnPhase: PLAYER           # ← Still player's turn
GameState: PLAYERS_TURN     # ← Back to normal gameplay

# Player takes action (attacks enemy)
TurnPhase: ENEMY            # ← Turn advances to enemy phase
GameState: ENEMY_TURN       # ← GameState shows "enemies acting..."

# AI completes
TurnPhase: ENVIRONMENT      # ← Hazards process
GameState: ENEMY_TURN       # ← Still showing enemy turn

# Environment completes
TurnPhase: PLAYER           # ← Back to player's turn (Turn 2!)
GameState: PLAYERS_TURN     # ← Back to normal gameplay
```

**Key Insight:** Opening menus **pauses turn progression** but doesn't change the turn phase!

---

## Why Both Systems?

### Attempt to Remove GameStates

**Initial Plan:** "Remove GameStates, use only TurnPhase"

**Problem:** TurnPhase can't represent UI states!

```python
# This doesn't make sense:
TurnPhase.SHOW_INVENTORY  # ❌ Inventory isn't a turn phase
TurnPhase.TARGETING       # ❌ Targeting isn't a turn phase
TurnPhase.CHARACTER_SCREEN # ❌ Character screen isn't a turn phase
```

**UI states are orthogonal to turn phases:**
- You can open inventory during `PLAYER` phase
- You can open character screen during `PLAYER` phase
- You can't open inventory during `ENEMY` or `ENVIRONMENT` phase (game is busy)

---

## Design Patterns

### Pattern 1: Phase-Specific Processing

```python
# Systems register to process during specific phases
turn_manager.register_listener(TurnPhase.ENEMY, ai_system.process, "start")
turn_manager.register_listener(TurnPhase.ENVIRONMENT, env_system.process, "start")
```

### Pattern 2: State-Specific Input Handling

```python
# Input handlers route keys based on GameState
if game_state == GameStates.PLAYERS_TURN:
    # Normal movement keys (arrows, vi keys)
    handle_movement_keys(key)
elif game_state == GameStates.SHOW_INVENTORY:
    # Inventory menu keys (a-z to use items)
    handle_inventory_keys(key)
elif game_state == GameStates.TARGETING:
    # Targeting keys (arrows to move cursor, Enter to confirm)
    handle_targeting_keys(key)
```

### Pattern 3: Synchronized State Changes

```python
# When player ends turn, both systems advance
def end_player_turn():
    # Advance turn phase
    turn_manager.advance_turn()  # PLAYER → ENEMY
    
    # Update game state to show enemy turn
    game_state_manager.set_game_state(GameStates.ENEMY_TURN)
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    GAME ENGINE                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────┐         ┌──────────────────┐    │
│  │  TurnManager    │         │ GameStateManager │    │
│  │  (Turn Phase)   │         │   (UI Mode)      │    │
│  ├─────────────────┤         ├──────────────────┤    │
│  │ - PLAYER        │         │ - PLAYERS_TURN   │    │
│  │ - ENEMY         │         │ - SHOW_INVENTORY │    │
│  │ - ENVIRONMENT   │         │ - TARGETING      │    │
│  └─────────────────┘         │ - CHARACTER_SCREEN│   │
│         │                     │ - PLAYER_DEAD    │    │
│         │                     └──────────────────┘    │
│         │                              │              │
│         ▼                              ▼              │
│  ┌─────────────────┐         ┌──────────────────┐    │
│  │  Systems        │         │ Input Handlers   │    │
│  ├─────────────────┤         ├──────────────────┤    │
│  │ - AISystem      │         │ - Movement       │    │
│  │ - EnvSystem     │         │ - Inventory      │    │
│  │ - ActionProc    │         │ - Targeting      │    │
│  └─────────────────┘         └──────────────────┘    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## FAQ

### Q: Why not merge them into one system?

**A:** They have fundamentally different responsibilities:
- **TurnPhase**: Combat sequencing (time-based, cycles continuously)
- **GameStates**: UI mode (event-based, changes on user input)

Merging them would create a confusing enum like:
```python
class MixedState(Enum):
    PLAYER_TURN_NORMAL = 1
    PLAYER_TURN_INVENTORY = 2
    PLAYER_TURN_TARGETING = 3
    PLAYER_TURN_CHARACTER_SCREEN = 4
    ENEMY_TURN = 5
    ENVIRONMENT_TURN = 6
    # ❌ This is confusing and hard to maintain
```

### Q: Which system should I use for X?

| Need | Use | Example |
|------|-----|---------|
| "Whose turn is it?" | TurnPhase | `if turn_manager.is_phase(TurnPhase.PLAYER):` |
| "What menu is open?" | GameStates | `if game_state == GameStates.SHOW_INVENTORY:` |
| "Should AI act?" | TurnPhase | `if turn_manager.is_phase(TurnPhase.ENEMY):` |
| "Should I route input?" | GameStates | `if game_state == GameStates.TARGETING:` |
| "Process hazards?" | TurnPhase | `turn_manager.register_listener(TurnPhase.ENVIRONMENT, ...)` |

### Q: What about PLAYERS_TURN and ENEMY_TURN in GameStates?

**A:** Historical overlap. These exist in GameStates for backward compatibility and UI feedback:
- `GameStates.PLAYERS_TURN`: "Show normal UI, player can act"
- `GameStates.ENEMY_TURN`: "Show 'Enemies are acting...' overlay"

They're synchronized with TurnPhase but serve different purposes (UI vs logic).

### Q: Can I add new phases/states?

**Yes!**

**Add Turn Phase (for new gameplay systems):**
```python
class TurnPhase(Enum):
    PLAYER = "player"
    ENEMY = "enemy"
    ENVIRONMENT = "environment"
    NPC = "npc"  # ← New! Non-hostile NPCs act
```

**Add Game State (for new UI modes):**
```python
class GameStates(Enum):
    # ... existing states ...
    SHOP_MENU = 9        # ← New! Shopping interface
    DIALOGUE = 10        # ← New! NPC conversation
```

---

## Best Practices

### ✅ DO

```python
# Check turn phase for combat logic
if turn_manager.is_phase(TurnPhase.PLAYER):
    # Player can take actions

# Check game state for UI logic
if game_state == GameStates.SHOW_INVENTORY:
    # Render inventory overlay

# Synchronize state changes
def end_player_turn():
    turn_manager.advance_turn()  # PLAYER → ENEMY
    game_state_manager.set_game_state(GameStates.ENEMY_TURN)
```

### ❌ DON'T

```python
# Don't use TurnPhase for UI decisions
if turn_manager.is_phase(TurnPhase.PLAYER):
    # ❌ Don't render inventory here - use GameStates

# Don't use GameStates for combat logic
if game_state == GameStates.PLAYERS_TURN:
    # ❌ Don't trigger AI here - use TurnPhase

# Don't forget to synchronize
turn_manager.advance_turn()  # ❌ Forgot to update GameState!
```

---

## Implementation Checklist

When adding features, ensure:

- [ ] **Turn phase advances correctly** (PLAYER → ENEMY → ENVIRONMENT)
- [ ] **Game state updates match turn phase** (synchronized transitions)
- [ ] **UI pauses turn progression** (inventory/menus don't advance turns)
- [ ] **Input routing respects game state** (keys do different things in different states)
- [ ] **Systems register for appropriate phases** (AI in ENEMY, hazards in ENVIRONMENT)

---

## Conclusion

**TurnPhase and GameStates are complementary systems:**

- **TurnPhase:** "Who acts now?" (Combat turn sequence)
- **GameStates:** "What screen is shown?" (UI mode)

Both are needed for a complete game engine. Removing either would create problems:
- Remove TurnPhase → No clean turn sequencing
- Remove GameStates → No way to handle UI modes

**Current architecture is correct.** ✅

---

## Related Documentation

- `docs/TURN_MANAGER_DESIGN.md` - TurnManager implementation details
- `engine/turn_manager.py` - TurnPhase enum and TurnManager class
- `game_states.py` - GameStates enum
- `engine/game_state_manager.py` - GameStateManager class

---

**Last Review:** January 2025  
**Status:** Documented & Finalized  
**Maintainer:** Development Team

