# Turn Manager System Design

## Current Problems

### 1. Scattered Turn Logic
Turn sequencing is spread across multiple files:
- `game_actions.py`: Sets `ENEMY_TURN` after player actions (lines 193, 246)
- `engine/systems/ai_system.py`: Sets `PLAYERS_TURN` after AI completes (line 123)
- `state_machine/game_states.py`: Defines state transitions
- `mouse_movement.py`: Sets `ENEMY_TURN` after pathfinding

**Finding**: `ENEMY_TURN` and `PLAYERS_TURN` are referenced in ~50+ locations across the codebase.

### 2. Implicit Turn Transitions
No centralized authority on "what comes next". Each system decides independently:
```python
# game_actions.py
self.state_manager.set_game_state(GameStates.ENEMY_TURN)

# ai_system.py  
state_manager.set_game_state(GameStates.PLAYERS_TURN)
```

### 3. Hard to Extend
Adding new turn phases (environment, NPCs, timed events) requires:
- New `GameStates` enum value
- New state class
- Update all transition logic
- Update all systems that check current state

### 4. Yo_Mama Bug Example
The recent yo_mama bug would have been easier to debug with a TurnManager:
- Clear logging: "Turn 1: Player → Enemy → Player"
- Explicit phase tracking: "Monsters active during ENEMY phase"
- Single source of truth for "whose turn is it?"

---

## Proposed Solution: TurnManager

### Architecture

```
┌─────────────────────────────────────────┐
│          TurnManager                    │
│  - Current Phase                        │
│  - Turn Counter                         │
│  - Phase Subscribers                    │
│  - advance_turn()                       │
│  - register_listener()                  │
└─────────────────────────────────────────┘
         ↓                ↓              ↓
    ┌────────┐    ┌───────────┐   ┌───────────┐
    │ Player │    │  Enemy    │   │   Hazard  │
    │ System │    │  System   │   │   System  │
    └────────┘    └───────────┘   └───────────┘
```

### Core Classes

#### 1. TurnPhase Enum
```python
class TurnPhase(Enum):
    PLAYER = "player"           # Player input and action
    ENEMY = "enemy"             # AI processing
    ENVIRONMENT = "environment" # Hazards, timed events
    # Future: NPC, MERCHANT, etc.
```

#### 2. TurnManager Class
```python
class TurnManager:
    def __init__(self):
        self.current_phase: TurnPhase = TurnPhase.PLAYER
        self.turn_number: int = 1
        self.phase_listeners: Dict[TurnPhase, List[Callable]] = {}
    
    def advance_turn(self, to_phase: Optional[TurnPhase] = None) -> TurnPhase:
        """Advance to next turn phase."""
        # Auto-advance if no phase specified
        if not to_phase:
            to_phase = self._get_next_phase()
        
        # Notify listeners of phase end
        self._notify_phase_end(self.current_phase)
        
        # Switch phase
        old_phase = self.current_phase
        self.current_phase = to_phase
        
        # Notify listeners of phase start
        self._notify_phase_start(to_phase)
        
        # Increment turn counter when cycle completes
        if old_phase == TurnPhase.ENVIRONMENT and to_phase == TurnPhase.PLAYER:
            self.turn_number += 1
        
        return to_phase
    
    def register_listener(self, phase: TurnPhase, 
                         callback: Callable, 
                         event: str = "start") -> None:
        """Register callback for phase events (start/end)."""
        pass
    
    def _get_next_phase(self) -> TurnPhase:
        """Get next phase in sequence."""
        sequence = [TurnPhase.PLAYER, TurnPhase.ENEMY, TurnPhase.ENVIRONMENT]
        current_idx = sequence.index(self.current_phase)
        next_idx = (current_idx + 1) % len(sequence)
        return sequence[next_idx]
```

#### 3. TurnPhaseListener (Protocol)
```python
from typing import Protocol

class TurnPhaseListener(Protocol):
    def on_phase_start(self, phase: TurnPhase) -> None:
        """Called when phase starts."""
        ...
    
    def on_phase_end(self, phase: TurnPhase) -> None:
        """Called when phase ends."""
        ...
```

---

## Integration Plan

### Phase 1: Foundation (30 min)
1. Create `engine/turn_manager.py`
2. Implement `TurnPhase` enum
3. Implement `TurnManager` class
4. Write unit tests

### Phase 2: AISystem Integration (45 min)
1. Update `AISystem` to listen to turn manager
2. Replace `GameStates.ENEMY_TURN` checks with `turn_manager.is_phase(ENEMY)`
3. Call `turn_manager.advance_turn()` instead of `set_game_state()`
4. Test AI behavior

### Phase 3: ActionProcessor Integration (45 min)
1. Update `ActionProcessor` to use turn manager
2. Replace state changes with turn manager calls
3. Update pathfinding to work with turn manager
4. Test player actions

### Phase 4: Environment Phase (30 min)
1. Move hazard processing to ENVIRONMENT phase
2. Add environment phase between ENEMY and PLAYER
3. Test hazard damage timing
4. Verify turn counter

### Phase 5: Cleanup & Testing (30 min)
1. Remove redundant state checks
2. Add comprehensive integration tests
3. Update documentation
4. Performance profiling

**Total Estimated Time:** 3 hours

---

## Benefits

### 1. Clarity
```python
# Before:
if game_state.current_state == GameStates.ENEMY_TURN:
    # Process AI
    self.state_manager.set_game_state(GameStates.PLAYERS_TURN)

# After:
if turn_manager.is_phase(TurnPhase.ENEMY):
    # Process AI
    turn_manager.advance_turn()  # Clear intent!
```

### 2. Debugging
```python
# Turn manager provides rich logging:
Turn 1 [PLAYER] → Player moved north
Turn 1 [ENEMY] → 3 monsters acted
Turn 1 [ENVIRONMENT] → 2 hazards processed
Turn 2 [PLAYER] → Player used scroll
```

### 3. Extensibility
```python
# Easy to add new phases:
class TurnPhase(Enum):
    PLAYER = "player"
    ENEMY = "enemy"
    ENVIRONMENT = "environment"
    NPC = "npc"  # ← Just add it!
    MERCHANT = "merchant"
    TIMED_EVENT = "timed_event"
```

### 4. Testing
```python
# Easy to test turn sequences:
def test_turn_sequence():
    manager = TurnManager()
    assert manager.current_phase == TurnPhase.PLAYER
    
    manager.advance_turn()
    assert manager.current_phase == TurnPhase.ENEMY
    
    manager.advance_turn()
    assert manager.current_phase == TurnPhase.ENVIRONMENT
    
    manager.advance_turn()
    assert manager.current_phase == TurnPhase.PLAYER
    assert manager.turn_number == 2  # Cycle complete!
```

---

## Backward Compatibility

### GameStates Integration
Keep existing `GameStates` enum but sync with TurnManager:

```python
# In state_manager.py:
def _sync_game_state_with_turn_phase(self, phase: TurnPhase) -> None:
    """Sync GameStates with TurnPhase during migration."""
    mapping = {
        TurnPhase.PLAYER: GameStates.PLAYERS_TURN,
        TurnPhase.ENEMY: GameStates.ENEMY_TURN,
        TurnPhase.ENVIRONMENT: GameStates.PLAYERS_TURN,  # Transparent to old code
    }
    self.set_game_state(mapping[phase])
```

This allows gradual migration without breaking existing code.

---

## Future Enhancements

### 1. Turn Listeners
```python
# Systems can listen to specific phases:
turn_manager.register_listener(
    TurnPhase.ENVIRONMENT,
    hazard_system.process_hazards,
    event="start"
)
```

### 2. Turn Skipping
```python
# Skip phases that have no work:
if not any_enemies_alive():
    turn_manager.skip_phase(TurnPhase.ENEMY)
```

### 3. Async Phases
```python
# Support for longer-running phases:
async def process_ai_phase(turn_manager):
    for monster in monsters:
        await monster.ai.take_turn()
        if turn_manager.phase_interrupted:
            break
```

### 4. Turn History
```python
# Track turn history for replay/debug:
turn_manager.history[0]  # Turn 1: [PLAYER: moved, ENEMY: 3 acted, ENV: 1 hazard]
turn_manager.history[1]  # Turn 2: [PLAYER: attacked, ENEMY: 2 acted, ENV: 0]
```

---

## Success Criteria

- ✅ All existing tests pass
- ✅ Turn sequencing more explicit and debuggable
- ✅ Easy to add new turn phases
- ✅ Performance impact < 1ms per turn
- ✅ Zero regressions in gameplay
- ✅ Documentation updated

---

## Notes

- Keep it simple for Phase 1 - just the core classes
- Don't try to add all features at once
- Focus on making the yo_mama-style bugs easier to debug
- Environment phase can be added incrementally

---

## Questions

1. Should turn counter track overall turns or player-specific turns?
   - **Answer**: Overall turns (full cycle of all phases)

2. How to handle interrupted phases (player death mid-turn)?
   - **Answer**: `advance_turn()` should check for game-ending conditions

3. Should we deprecate `GameStates.ENEMY_TURN` immediately?
   - **Answer**: No, keep it for backward compat during migration

