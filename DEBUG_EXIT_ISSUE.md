# Debugging the "Kicked to Startup Screen" Issue

## What We've Fixed So Far

1. ✅ **Pathfinding Bug** - Monsters now move correctly
2. ✅ **JSON Serialization** - Game saves/loads properly  
3. ✅ **Off-screen Actions** - Monsters only act when in player FOV
4. ✅ **Item Pickup** - Monsters must be on same tile, not adjacent

## What We've Added for Debugging

### Logging System
The game now has comprehensive logging for exit triggers:

**Log Format:**
```
WARNING: === GAME EXIT TRIGGERED ===
WARNING: Action: {'exit': True}
WARNING: Mouse action: {}
WARNING: Current state: GameStates.PLAYERS_TURN
WARNING: Exit action in actions: True
WARNING: ========================
```

### Where to Look

**When the game kicks you to startup screen:**
1. Check your terminal/console window
2. Look for `WARNING` level messages
3. The logs will show:
   - What action triggered the exit
   - What game state you were in
   - Whether it was a keyboard or mouse action

## How to Test

1. **Start the game in testing mode:**
   ```bash
   python engine.py --testing
   ```

2. **Play normally until the exit happens**

3. **Check the terminal for WARNING logs**

4. **Report back:**
   - What were you doing when it exited?
   - What did the WARNING logs show?
   - What actions did you take (movement, attack, inventory, etc.)?

## Possible Causes

Based on the code review, unexpected exits could be triggered by:

1. **ESCAPE key during PLAYERS_TURN** 
   - Should return `{"exit": True}` 
   - This is expected behavior
   - Logs will confirm this

2. **ESCAPE key during ENEMY_TURN**
   - Might have unexpected behavior
   - Logs will show if this is happening

3. **Exception in action processing**
   - Could cause state corruption
   - Would show in error logs

4. **Player death detection**
   - Player dead state transitions to main menu
   - Logs will show state = PLAYER_DEAD

5. **Corrupted key object**
   - Key presses being misinterpreted
   - Logs will show exact action dict

## Next Steps

After you report what the logs show, we can:
- Add more specific logging if needed
- Fix the root cause once identified
- Add regression tests to prevent it recurring

## Files Changed

- `engine_integration.py` - Added exit trigger logging
- `engine.py` - Changed log level to WARNING
- `components/ai.py` - Restored FOV check for SlimeAI
- `components/item_seeking_ai.py` - Fixed adjacent pickup bug

