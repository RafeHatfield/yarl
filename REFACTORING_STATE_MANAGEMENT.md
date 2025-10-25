# 🔧 State Management Refactoring Sprint

**Status:** 🎯 Ready to Start  
**Priority:** HIGH (blocks future victory phases cleanly)  
**Estimated Time:** 2-3 days  
**Branch:** `refactor/state-management-system`

---

## 🎯 **Goals**

1. **Make adding new game states as easy as adding new equipment**
2. **Eliminate duplicated state logic across files**
3. **Centralize turn flow management**
4. **Establish clear API conventions**

---

## 📋 **Refactoring Tasks**

### **Phase 1: State Configuration System** (Day 1)

#### **Task 1.1: Create State Config Module**
**File:** `state_management/state_config.py` (NEW)

```python
"""
Centralized game state configuration.

This is the SINGLE SOURCE OF TRUTH for game state behavior.
All systems consult this config instead of hardcoding state checks.
"""

from enum import Enum
from typing import Dict, Any, Callable, Optional
from game_states import GameStates

class StateConfig:
    """Configuration for a single game state."""
    
    def __init__(
        self,
        input_handler: Optional[Callable],
        allows_movement: bool = False,
        allows_pickup: bool = False,
        allows_inventory: bool = False,
        transition_to_enemy: bool = False,
        preserve_after_enemy_turn: bool = False,
        ai_processes: bool = False,
        description: str = ""
    ):
        self.input_handler = input_handler
        self.allows_movement = allows_movement
        self.allows_pickup = allows_pickup
        self.allows_inventory = allows_inventory
        self.transition_to_enemy = transition_to_enemy
        self.preserve_after_enemy_turn = preserve_after_enemy_turn
        self.ai_processes = ai_processes
        self.description = description


# Import handlers
from input_handlers import (
    handle_player_turn_keys,
    handle_targeting_keys,
    handle_inventory_keys,
    handle_player_dead_keys,
    handle_level_up_menu,
    handle_character_screen,
)

# THE SINGLE SOURCE OF TRUTH
STATE_CONFIGURATIONS: Dict[GameStates, StateConfig] = {
    GameStates.PLAYERS_TURN: StateConfig(
        input_handler=handle_player_turn_keys,
        allows_movement=True,
        allows_pickup=True,
        allows_inventory=True,
        transition_to_enemy=True,
        description="Normal player turn - can move, act, use inventory"
    ),
    
    GameStates.AMULET_OBTAINED: StateConfig(
        input_handler=handle_player_turn_keys,  # Same controls as PLAYERS_TURN
        allows_movement=True,
        allows_pickup=True,
        allows_inventory=True,
        transition_to_enemy=True,
        preserve_after_enemy_turn=True,  # KEY: Don't reset to PLAYERS_TURN!
        description="Player has amulet - looking for portal"
    ),
    
    GameStates.ENEMY_TURN: StateConfig(
        input_handler=None,  # No player input during enemy turn
        allows_movement=False,
        allows_pickup=False,
        allows_inventory=False,
        ai_processes=True,
        description="Enemies taking their turns"
    ),
    
    GameStates.TARGETING: StateConfig(
        input_handler=handle_targeting_keys,
        allows_movement=False,  # Targeting, not moving
        description="Selecting spell/wand target"
    ),
    
    GameStates.SHOW_INVENTORY: StateConfig(
        input_handler=handle_inventory_keys,
        allows_movement=False,
        description="Viewing inventory"
    ),
    
    GameStates.DROP_INVENTORY: StateConfig(
        input_handler=handle_inventory_keys,
        allows_movement=False,
        description="Dropping items"
    ),
    
    GameStates.PLAYER_DEAD: StateConfig(
        input_handler=handle_player_dead_keys,
        allows_movement=False,
        description="Player is dead"
    ),
    
    GameStates.LEVEL_UP: StateConfig(
        input_handler=handle_level_up_menu,
        allows_movement=False,
        description="Choosing level up bonus"
    ),
    
    GameStates.CHARACTER_SCREEN: StateConfig(
        input_handler=handle_character_screen,
        allows_movement=False,
        description="Viewing character stats"
    ),
    
    GameStates.CONFRONTATION: StateConfig(
        input_handler=None,  # Handled by confrontation screen directly
        allows_movement=False,
        description="Entity confrontation choice"
    ),
    
    GameStates.VICTORY: StateConfig(
        input_handler=None,
        allows_movement=False,
        description="Victory screen"
    ),
    
    GameStates.FAILURE: StateConfig(
        input_handler=None,
        allows_movement=False,
        description="Failure screen"
    ),
}


class StateManager:
    """
    Centralized state query interface.
    
    All systems should use this instead of hardcoding state checks.
    """
    
    @staticmethod
    def get_config(state: GameStates) -> StateConfig:
        """Get configuration for a state."""
        if state not in STATE_CONFIGURATIONS:
            raise ValueError(f"No configuration for state: {state}")
        return STATE_CONFIGURATIONS[state]
    
    @staticmethod
    def allows_movement(state: GameStates) -> bool:
        """Can player move in this state?"""
        return StateManager.get_config(state).allows_movement
    
    @staticmethod
    def allows_pickup(state: GameStates) -> bool:
        """Can player pick up items in this state?"""
        return StateManager.get_config(state).allows_pickup
    
    @staticmethod
    def allows_inventory(state: GameStates) -> bool:
        """Can player access inventory in this state?"""
        return StateManager.get_config(state).allows_inventory
    
    @staticmethod
    def get_input_handler(state: GameStates) -> Optional[Callable]:
        """Get the input handler for this state."""
        return StateManager.get_config(state).input_handler
    
    @staticmethod
    def should_preserve_after_enemy_turn(state: GameStates) -> bool:
        """Should this state be restored after enemy turn?"""
        return StateManager.get_config(state).preserve_after_enemy_turn
    
    @staticmethod
    def should_transition_to_enemy(state: GameStates) -> bool:
        """Should actions in this state transition to enemy turn?"""
        return StateManager.get_config(state).transition_to_enemy
    
    @staticmethod
    def ai_processes_in_state(state: GameStates) -> bool:
        """Do AI entities process turns in this state?"""
        return StateManager.get_config(state).ai_processes
```

**Tests:** `tests/test_state_config.py`
- Test all state configs are valid
- Test state manager query methods
- Test that all GameStates have configs

---

#### **Task 1.2: Update Input System**
**File:** `engine/systems/input_system.py`

**Changes:**
```python
# BEFORE (line 52-61)
self.key_handlers = {
    GameStates.PLAYERS_TURN: handle_player_turn_keys,
    GameStates.AMULET_OBTAINED: handle_player_turn_keys,  # DUPLICATE!
    GameStates.PLAYER_DEAD: handle_player_dead_keys,
    # ... etc
}

# AFTER
from state_management.state_config import StateManager

# NO MORE key_handlers dict! Use config instead:
def update(self, delta_time: float):
    key = self.key_queue.pop(0) if self.key_queue else None
    if key:
        state = self.engine.state_manager.state.current_state
        handler = StateManager.get_input_handler(state)  # ← FROM CONFIG!
        if handler:
            action = handler(key)
            # ... process action
```

**Benefits:**
- Eliminates duplicate mapping
- Adding new state = update config only
- Single source of truth

---

#### **Task 1.3: Update Input Handlers**
**File:** `input_handlers.py`

**Changes:**
```python
# BEFORE (line 24-25)
if game_state in (GameStates.PLAYERS_TURN, GameStates.AMULET_OBTAINED):
    return handle_player_turn_keys(key)

# AFTER
from state_management.state_config import StateManager

handler = StateManager.get_input_handler(game_state)
if handler:
    return handler(key)
return {}
```

**Benefits:**
- No more hardcoded state lists
- Config handles all routing

---

#### **Task 1.4: Update AI System**
**File:** `engine/systems/ai_system.py`

**Changes:**
```python
# BEFORE (line 149-169) - Complex conditionals
if player and hasattr(player, 'victory') and player.victory and player.victory.amulet_obtained:
    state_manager.set_game_state(GameStates.AMULET_OBTAINED)
else:
    state_manager.set_game_state(GameStates.PLAYERS_TURN)

# AFTER
from state_management.state_config import StateManager

# Get the state we're transitioning FROM
previous_state = state_manager.state.current_state

# Should we preserve it?
if StateManager.should_preserve_after_enemy_turn(previous_state):
    state_manager.set_game_state(previous_state)  # Restore!
else:
    state_manager.set_game_state(GameStates.PLAYERS_TURN)  # Normal
```

**Benefits:**
- No more player.victory checks in AI system
- Config declares preservation intent
- Easy to add more preserved states

---

#### **Task 1.5: Update Game Actions**
**File:** `game_actions.py`

**Changes:**
```python
# BEFORE (line 355-358) - Movement handler
if current_state not in (GameStates.PLAYERS_TURN, GameStates.AMULET_OBTAINED):
    return

# AFTER
from state_management.state_config import StateManager

if not StateManager.allows_movement(current_state):
    return

# Similar for pickup:
if not StateManager.allows_pickup(current_state):
    return
```

**Benefits:**
- Self-documenting (allows_movement vs state list)
- Config handles all state checks

---

### **Phase 2: Turn Controller** (Day 2)

#### **Task 2.1: Create Turn Controller**
**File:** `systems/turn_controller.py` (NEW)

```python
"""
Centralized turn flow management.

Handles transition logic, state preservation, and turn economy.
"""

from game_states import GameStates
from state_management.state_config import StateManager

class TurnController:
    """Manages game turn flow and state transitions."""
    
    def __init__(self, state_manager, turn_manager=None):
        self.state_manager = state_manager
        self.turn_manager = turn_manager
        self.preserved_state = None
    
    def end_player_action(self, action_consumed_turn: bool = True):
        """
        Handle end of player action.
        
        Determines if turn should transition to enemy, and if so,
        whether current state should be preserved.
        
        Args:
            action_consumed_turn: Did this action consume a turn?
        """
        if not action_consumed_turn:
            return  # No turn transition
        
        current_state = self.state_manager.state.current_state
        
        # Should this state transition to enemy turn?
        if not StateManager.should_transition_to_enemy(current_state):
            return  # State doesn't cause turn transitions
        
        # Should we preserve this state?
        if StateManager.should_preserve_after_enemy_turn(current_state):
            self.preserved_state = current_state
        
        # Transition to enemy turn
        self._transition_to_enemy_turn()
    
    def end_enemy_turn(self):
        """
        Handle end of enemy turn.
        
        Restores preserved state or returns to PLAYERS_TURN.
        """
        if self.preserved_state:
            # Restore preserved state (e.g., AMULET_OBTAINED)
            self.state_manager.set_game_state(self.preserved_state)
            self.preserved_state = None
        else:
            # Normal: back to PLAYERS_TURN
            self.state_manager.set_game_state(GameStates.PLAYERS_TURN)
    
    def _transition_to_enemy_turn(self):
        """Internal: Transition to enemy turn."""
        if self.turn_manager:
            from engine.turn_manager import TurnPhase
            self.turn_manager.advance_turn(TurnPhase.ENEMY)
        
        self.state_manager.set_game_state(GameStates.ENEMY_TURN)
```

**Tests:** `tests/test_turn_controller.py`
- Test normal turn transitions
- Test state preservation
- Test no-turn-consumed actions

---

#### **Task 2.2: Integrate Turn Controller**

**Update:** `game_actions.py`

```python
# BEFORE - Every action handler has:
_transition_to_enemy_turn(self.state_manager, self.turn_manager)
# OR
return  # Don't transition!

# AFTER - Every action handler has:
self.turn_controller.end_player_action(action_consumed_turn=True)
```

**Update:** `engine/systems/ai_system.py`

```python
# BEFORE - Complex state restoration logic

# AFTER
self.turn_controller.end_enemy_turn()  # Handles everything!
```

---

### **Phase 3: Cleanup & Documentation** (Day 3)

#### **Task 3.1: Remove Duplicated Logic**
- Remove `_transition_to_enemy_turn` helper (now in TurnController)
- Remove hardcoded state lists from all files
- Consolidate all state checks to use StateManager

#### **Task 3.2: API Conventions Document**
**File:** `docs/API_CONVENTIONS.md` (NEW)

Document:
- MessageBuilder methods (what exists, what doesn't)
- Console references (when to use 0 vs context)
- Tile access (always use `.blocked`, never `['blocked']`)
- State checks (always use StateManager, never hardcode)

#### **Task 3.3: Update Tests**
- All existing tests should still pass
- Add new tests for state config
- Add new tests for turn controller

---

## ✅ **Success Criteria**

### **Before Refactoring:**
```python
# Adding new state requires:
# 1. Update GameStates enum
# 2. Update input_handlers.py (add to state list)
# 3. Update input_system.py (add to key_handlers dict)
# 4. Update ai_system.py (add state restoration logic)
# 5. Update game_actions.py (add to movement check, pickup check, etc.)
# 6. Add return statements if state should persist
# 7. Test everything, find bugs, fix bugs
```

### **After Refactoring:**
```python
# Adding new state requires:
# 1. Update GameStates enum
# 2. Add config to STATE_CONFIGURATIONS dict:
GameStates.NEW_STATE: StateConfig(
    input_handler=handle_player_turn_keys,
    allows_movement=True,
    preserve_after_enemy_turn=True,  # If needed
    description="What this state does"
)
# 3. Done! All systems use config automatically.
```

---

## 📊 **Testing Plan**

### **Regression Tests**
- All 48 existing victory tests must pass
- All other existing tests must pass

### **New Tests**
- `test_state_config.py` - Config system
- `test_turn_controller.py` - Turn flow
- `test_state_integration.py` - End-to-end

### **Manual Testing**
- Victory condition still works
- All game states still work
- No regressions in gameplay

---

## 🚀 **Rollout Plan**

### **Day 1: State Config**
- Morning: Create state_config.py
- Afternoon: Update input_system, input_handlers
- Evening: Update ai_system, game_actions
- End of day: Commit, run tests

### **Day 2: Turn Controller**
- Morning: Create turn_controller.py
- Afternoon: Integrate with game_actions
- Evening: Integrate with ai_system
- End of day: Commit, run tests

### **Day 3: Cleanup**
- Morning: Remove duplicated code
- Afternoon: Write API conventions doc
- Evening: Final testing, merge

---

## 🎯 **Benefits**

### **Immediate:**
- ✅ No more bugs when adding states
- ✅ Single source of truth
- ✅ Self-documenting code
- ✅ Easier testing

### **Long-term:**
- ✅ Phase 2-15 of victory condition (15 more phases!)
- ✅ Portal system with complex state
- ✅ Assassin system with turn timers
- ✅ Any future state-based features

---

## 📝 **Notes**

- Keep victory branch commits for reference
- Victory system should still work identically after refactor
- Focus on eliminating duplication, not adding features
- When in doubt, consult Equipment refactoring as example

---

**Ready to start?** Create branch `refactor/state-management-system` and begin!

