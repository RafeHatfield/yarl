# API Conventions Guide

**Date:** October 25, 2025  
**Purpose:** Prevent "trial and error" development by documenting correct API usage

This document captures API conventions learned during the victory condition implementation and state management refactoring. Following these conventions will prevent the types of bugs we encountered.

---

## Table of Contents

1. [MessageBuilder Methods](#messagebuilder-methods)
2. [Console References](#console-references)
3. [Tile Access](#tile-access)
4. [State Management](#state-management)
5. [Turn Flow](#turn-flow)
6. [Component Access](#component-access)

---

## MessageBuilder Methods

### Available Methods

**Use these methods** for message creation:

```python
from message_builder import MessageBuilder as MB

# ✅ CORRECT - These methods exist:
MB.info("Normal information message")
MB.warning("Warning message in yellow")
MB.item_effect("Dramatic positive effect - bright white")
MB.status_effect("Status effect applied - cyan")
MB.combat("Combat message - red")
MB.item_pickup("Item picked up - green")
```

### Non-Existent Methods

**DO NOT use** - These methods don't exist:

```python
# ❌ WRONG - These don't exist:
MB.critical("...")  # Use MB.item_effect() instead
MB.error("...")     # Use MB.warning() instead
MB.success("...")   # Use MB.item_pickup() or MB.item_effect()
```

### When to Use Each Method

| Method | Use For | Color | Example |
|--------|---------|-------|---------|
| `info()` | Normal gameplay messages | Light gray | "You descend the stairs" |
| `warning()` | Warnings, blocked actions | Yellow | "You can't go that way" |
| `item_effect()` | Dramatic positive events | Bright white | "The amulet pulses with power!" |
| `status_effect()` | Status changes | Cyan | "You feel poisoned" |
| `combat()` | Combat results | Red | "The orc hits you for 5 damage" |
| `item_pickup()` | Item acquisition | Green | "You pick up a sword" |

### Bug History

**Bug:** Used `MB.critical()` in victory_manager.py  
**Error:** `AttributeError: type object 'MessageBuilder' has no attribute 'critical'`  
**Fix:** Changed to `MB.item_effect()` for dramatic messages  
**Commit:** 58325a1

---

## Console References

### libtcod Console System

**Root Console Reference:**

```python
# ✅ CORRECT - Root console is referenced as 0 in old libtcod API:
tcod.console_blit(source_console, 0, 0, width, height, 0, x, y, 1.0, 0.8)
#                                                      ^ root console

# ❌ WRONG - These don't exist:
engine.root_console  # GameEngine doesn't have this attribute
context.root_console  # context doesn't expose root console directly
```

### When to Use Root Console (0)

Use `0` for root console when:
- Blitting to the screen
- Drawing to the final output
- In menu/overlay screens

```python
# ✅ Example from confrontation screen:
def confrontation_menu(con, root_console, screen_width, screen_height):
    # Draw to 'con' (local console)
    tcod.console_print(con, x, y, text)
    
    # Blit to root console (0)
    tcod.console_blit(con, 0, 0, width, height, 0, x, y, 1.0, 0.8)
    #                                          ^ use 0, not root_console
```

### Bug History

**Bug:** Used `engine.root_console` in engine_integration.py  
**Error:** `AttributeError: 'GameEngine' object has no attribute 'root_console'`  
**Fix:** Changed to `0` (libtcod convention)  
**Commit:** d679c62

---

## Tile Access

### Correct Tile Access Pattern

**Tiles are objects with attributes, NOT dictionaries:**

```python
# ✅ CORRECT - Access tile properties as attributes:
tile = game_map.tiles[x][y]
if tile.blocked:
    # Tile is blocked
if tile.block_sight:
    # Tile blocks sight

# ❌ WRONG - Don't use dictionary syntax:
if tile['blocked']:  # TypeError: 'Tile' object is not subscriptable
if tile['block_sight']:  # This will crash!
```

### Tile Properties

Common tile attributes:
- `tile.blocked` - Can't walk through
- `tile.block_sight` - Can't see through
- `tile.explored` - Player has seen this tile
- `tile.visible` - Currently in FOV

### Bug History

**Bug:** Used `game_map.tiles[x][y]['blocked']` in victory_manager.py  
**Error:** `TypeError: 'Tile' object is not subscriptable`  
**Fix:** Changed to `game_map.tiles[x][y].blocked`  
**Commit:** 5321d8e

---

## State Management

### Using StateManager (Refactored System)

**Always use StateManager** instead of hardcoding state checks:

```python
from state_management.state_config import StateManager

# ✅ CORRECT - Query StateManager:
if StateManager.allows_movement(current_state):
    # Allow player to move

if StateManager.allows_pickup(current_state):
    # Allow item pickup

handler = StateManager.get_input_handler(current_state)
if handler:
    action = handler(key)

# ❌ WRONG - Don't hardcode state lists:
if current_state in (GameStates.PLAYERS_TURN, GameStates.AMULET_OBTAINED):
    # This is duplication! Use StateManager instead
```

### Adding New Game States

When adding a new game state:

1. **Add to GameStates enum:**
```python
# game_states.py
class GameStates(Enum):
    # ... existing states
    NEW_STATE = 15
```

2. **Add configuration:**
```python
# state_management/state_config.py
STATE_CONFIGURATIONS = {
    # ... existing configs
    GameStates.NEW_STATE: StateConfig(
        input_handler=handle_player_turn_keys,
        allows_movement=True,
        allows_pickup=True,
        preserve_after_enemy_turn=False,  # Set to True if state should persist
        description="What this state does"
    )
}
```

3. **Done!** All systems use StateManager automatically.

### State Preservation

For states that should persist across enemy turns (like AMULET_OBTAINED):

```python
GameStates.AMULET_OBTAINED: StateConfig(
    # ... other settings
    preserve_after_enemy_turn=True,  # ← This makes it preserve!
)
```

TurnController will automatically restore this state after enemy turn.

---

## Turn Flow

### Using TurnController (Refactored System)

**Always use TurnController** for turn transitions:

```python
from systems.turn_controller import get_turn_controller

# ✅ CORRECT - Use TurnController:
turn_controller = get_turn_controller()
turn_controller.end_player_action(turn_consumed=True)

# After enemy turn (in ai_system):
turn_controller.end_enemy_turn()  # Automatic state restoration!

# For special cases (death, victory):
turn_controller.force_state_transition(GameStates.PLAYER_DEAD)

# ❌ WRONG - Don't call old helper:
_transition_to_enemy_turn(state_manager, turn_manager)  # OBSOLETE!
```

### Turn Consumption

Specify whether action consumes a turn:

```python
# Movement, combat, pickup = consume turn
turn_controller.end_player_action(turn_consumed=True)

# Opening inventory, character screen = don't consume turn
turn_controller.end_player_action(turn_consumed=False)
```

### State Preservation During Turns

TurnController handles state preservation automatically:

```python
# Player action in AMULET_OBTAINED state
turn_controller.end_player_action(turn_consumed=True)
# → State preserved (config says preserve_after_enemy_turn=True)
# → Transitions to ENEMY_TURN

# Enemies take turns...

# After enemy turn
turn_controller.end_enemy_turn()
# → Automatically restores AMULET_OBTAINED
# → No manual checks needed!
```

---

## Component Access

### Optional Components

**Always check if component exists before accessing:**

```python
from components.component_registry import ComponentType

# ✅ CORRECT - Check component exists:
if entity.components.has(ComponentType.ITEM) and entity.item:
    if entity.item.use_function:
        # Safe to access

# ❌ WRONG - Assuming component exists:
if entity.item.use_function:  # Crash if entity.item is None!
```

### Component Patterns

```python
# Getting optional component:
pathfinding = player.get_component_optional(ComponentType.PATHFINDING)
if pathfinding:
    # Use pathfinding

# Checking component type:
if entity.components.has(ComponentType.AI):
    # Entity has AI

# Accessing known component:
if hasattr(entity, 'fighter') and entity.fighter:
    damage = entity.fighter.hp
```

---

## Common Patterns

### Checking Multiple Conditions

```python
# ✅ CORRECT - Short-circuit evaluation:
if player and hasattr(player, 'inventory') and player.inventory:
    # Safe to access inventory

# Also correct - get_component_optional:
inventory = player.get_component_optional(ComponentType.INVENTORY)
if inventory:
    # Safe to use
```

### Handling None Values

```python
# ✅ CORRECT - Check for None:
entities = self.state_manager.state.entities
if entities is not None:
    for entity in entities:
        # Process entity

# ❌ WRONG - Assuming not None:
for entity in self.state_manager.state.entities:  # Crash if None!
```

---

## Testing Patterns

### Mocking State Manager

```python
from unittest.mock import Mock

# Create mock state manager:
state_manager = Mock()
state_manager.state = Mock()
state_manager.state.current_state = GameStates.PLAYERS_TURN

# Mock state transition:
state_changes = []
def track(state):
    state_changes.append(state)
state_manager.set_game_state = Mock(side_effect=track)
```

### Testing State Transitions

```python
# Test turn flow:
controller = TurnController(state_manager)
controller.end_player_action(turn_consumed=True)

# Verify state changed:
assert GameStates.ENEMY_TURN in state_changes
```

---

## Quick Reference

### DO's ✅

- **MessageBuilder:** Use `MB.info()`, `MB.warning()`, `MB.item_effect()`
- **Console:** Use `0` for root console in libtcod
- **Tiles:** Access as `tile.blocked` (attribute)
- **States:** Use `StateManager.allows_movement()` (query)
- **Turns:** Use `turn_controller.end_player_action()` (centralized)
- **Components:** Check exists before accessing

### DON'Ts ❌

- **MessageBuilder:** Don't use `MB.critical()` (doesn't exist)
- **Console:** Don't use `engine.root_console` (doesn't exist)
- **Tiles:** Don't use `tile['blocked']` (not a dict)
- **States:** Don't hardcode state lists (use StateManager)
- **Turns:** Don't call `_transition_to_enemy_turn()` (obsolete)
- **Components:** Don't assume components exist (check first)

---

## When in Doubt

1. **Check existing code** for similar patterns
2. **Grep the codebase** to see how it's used elsewhere
3. **Check the test files** for usage examples
4. **Read the module docstrings** for API documentation

---

## Version History

- **v1.0** (Oct 25, 2025) - Initial version based on victory implementation and refactoring
- Documented bugs from commits: 58325a1, d679c62, 5321d8e, and refactoring branch

---

**Remember:** These conventions were learned through bugs. Following them prevents repeating those bugs!

