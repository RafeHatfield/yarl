# Victory Condition Testing Guide

## Quick Test - Level 1 Victory Sequence

The Amulet of Yendor has been added to the Level 1 testing template so you can test the complete victory sequence immediately!

### How to Test

1. **Enable Testing Mode:**
   ```bash
   export YARL_TESTING_MODE=1
   python engine.py --testing
   ```
   
   Or simply:
   ```bash
   python engine.py --testing
   ```

2. **Start a New Game:**
   - Press 'a' for "Play a new game"
   - You'll start on Level 1 with testing configuration

3. **Find the Amulet:**
   - The golden Amulet of Yendor (") spawns somewhere on Level 1
   - Walk around to find it (it's in one of the rooms)
   - Pick it up with 'g'

4. **Experience the Victory Sequence:**
   - **Dramatic Moment!** Entity reacts: "AT LAST! You've done it!"
   - **Portal Spawns:** Magenta portal (O) appears at your location
   - **Entity Dialogue:** "Now... bring it to me. QUICKLY."

5. **Test Delay (Optional):**
   - Walk around with the amulet (don't enter portal yet)
   - Entity gets anxious after delays:
     - 10 turns: "What took you so long?"
     - 50 turns: "Where have you BEEN?!"
     - 100 turns: "FINALLY! Give. It. To. Me."

6. **Enter the Portal:**
   - Step on the magenta portal (O)
   - Transported to Entity's Throne Room
   - Confrontation screen appears

7. **Make Your Choice:**
   - **Press 'a'**: Give Amulet → **Bad Ending** (you become trapped)
   - **Press 'b'**: Keep Amulet → **Good Ending** (you escape)

8. **View Ending:**
   - Watch the dramatic ending cinematic
   - See your statistics (deaths, turns, etc.)
   - Press 'R' to restart or 'ESC' to quit

9. **Check Hall of Fame:**
   - From main menu, press 'c'
   - See your victory recorded!

---

## What to Test

### Core Functionality
- [ ] Amulet spawns on Level 1
- [ ] Amulet is visible and pickable (golden " symbol)
- [ ] Picking up amulet triggers Entity dialogue
- [ ] Portal appears immediately after pickup
- [ ] Portal is visible (magenta O symbol)
- [ ] Can move around with amulet (not forced into portal)
- [ ] Stepping on portal transitions to confrontation

### Confrontation Screen
- [ ] Confrontation screen displays correctly
- [ ] Entity's dialogue appears
- [ ] Two choices visible (a and b)
- [ ] Can press 'a' to give amulet
- [ ] Can press 'b' to keep amulet
- [ ] ESC key doesn't exit (stays in confrontation)

### Endings
- [ ] **Bad Ending (Give Amulet):**
  - [ ] Entity's betrayal dialogue plays
  - [ ] "YOU FAILED - Bound for Eternity" screen
  - [ ] Statistics display correctly
  - [ ] Can press 'R' to restart
  - [ ] Can press 'ESC' to quit
  - [ ] Returns to main menu after choice

- [ ] **Good Ending (Keep Amulet):**
  - [ ] Entity's shock dialogue plays
  - [ ] "VICTORY - You Are Free" screen
  - [ ] Statistics display correctly
  - [ ] Can press 'R' to restart
  - [ ] Can press 'ESC' to quit
  - [ ] Victory recorded in Hall of Fame

### Hall of Fame
- [ ] Accessible from main menu (press 'c')
- [ ] Shows recent victories
- [ ] Good endings recorded correctly
- [ ] Bad endings NOT recorded (failure, not victory)
- [ ] Statistics accurate
- [ ] Can return to main menu

---

## Known Testing Caveats

### Statistics Tracking
Currently, some statistics show as 0:
- **Deaths**: Not yet tracked (shows 0)
- **Kills**: Not yet tracked (shows 0)
- **Turns**: Not yet tracked (shows 0)

This is expected for Phase 1 MVP. These will be added in future phases.

### Entity Anxiety
Entity anxiety levels track correctly internally, but reactive messages during gameplay aren't fully implemented yet. You'll see:
- ✅ Anxiety changes in confrontation dialogue (if you delay)
- ❌ No anxiety messages during exploration (coming in Phase 2)

---

## Testing Different Scenarios

### Scenario 1: Immediate Confrontation
1. Pick up amulet
2. Immediately step on portal
3. Make choice
4. Test both endings (restart between)

### Scenario 2: Delayed Confrontation
1. Pick up amulet
2. Explore for 10+ turns
3. Portal should still be there
4. Enter portal when ready

### Scenario 3: Multiple Playthroughs
1. Complete a good ending
2. Check Hall of Fame (should see entry)
3. Start new game
4. Complete a bad ending
5. Check Hall of Fame (should only show good ending)
6. Start new game
7. Complete another good ending
8. Hall of Fame should show both victories

---

## Troubleshooting

### Amulet Doesn't Spawn
- **Solution**: Make sure you're in testing mode (`--testing` flag or `YARL_TESTING_MODE=1`)
- **Check**: Level 1 should have LOTS of items (20 healing potions, etc.)
- **Verify**: Look in multiple rooms, amulet is golden " symbol

### Portal Doesn't Appear
- **Check**: Did you actually pick up the amulet (press 'g')?
- **Check**: Is there a magenta O near where you picked up the amulet?
- **Debug**: Look for Entity's dialogue messages

### Confrontation Screen Doesn't Show
- **Check**: Did you step ON the portal (same tile)?
- **Check**: Game state should change when you step on it

### Hall of Fame is Empty
- **Reason**: Bad endings don't record in Hall of Fame (only victories)
- **Solution**: Complete a good ending (keep the amulet)

### Stats Show Zero
- **Expected**: Deaths/kills/turns tracking not implemented yet
- **Still Works**: The victory sequence works, stats just aren't tracked yet

---

## Reverting Testing Changes

After testing, if you want the amulet to ONLY spawn on level 25 (normal gameplay):

1. **Option A: Disable Testing Mode**
   - Just run without `--testing` flag
   - Amulet won't spawn on level 1 in normal mode

2. **Option B: Remove from Testing Template** (if desired)
   - Edit `config/level_templates_testing.yaml`
   - Remove lines 66-69 (the amulet entry)
   - Amulet will no longer appear in testing mode

**Recommended:** Keep testing mode as-is! It's extremely useful for future development and doesn't affect normal gameplay.

---

## Normal Gameplay Testing

To test the victory sequence in actual gameplay (25 levels):

1. **Start Normal Game** (no `--testing` flag)
2. **Play Through 25 Levels** (this will take hours!)
3. **Find Amulet on Level 25** (spawns near stairs in final room)
4. **Complete Victory Sequence** (same as above)

This is the "real" experience, but testing mode lets you verify everything works without the time investment.

---

## Next Steps After Testing

Once you've verified Phase 1 works:

1. **Report Issues**: Any bugs or unexpected behavior
2. **Feedback**: Does the Entity's dialogue feel right?
3. **Balance**: Are the endings satisfying?
4. **UI**: Is the confrontation screen clear?

Then we can move to:
- **Phase 2**: Entity depth-reactive dialogue (more personality)
- **Phase 3**: Guide system (mysterious hints)
- **Phase 4**: Environmental lore (murals)
- **Phase 5**: More endings (Mercy, Sacrifice)

---

## Technical Notes for Developers

### Files Modified for Testing
- `config/level_templates_testing.yaml` - Added amulet to level 1
- `map_objects/game_map.py` - Added `create_unique_item` to spawn chain

### Testing Template System
The testing template system is powerful:
- Only active when `YARL_TESTING_MODE=1` or `--testing` flag
- Overrides normal level generation
- Doesn't affect normal gameplay at all
- Perfect for rapid feature iteration

### Why Level 1?
- Instant access (no grinding)
- Safe environment (few enemies)
- Full item selection (test with any build)
- Fast iteration (restart in seconds)

---

**Happy Testing!** 🐉

_"At last. You've done it. Now, bring it to me... QUICKLY."_  
— The Entity

---

## Quick Reference

| Key | Action |
|-----|--------|
| `g` | Pick up item (amulet) |
| Walk onto `O` | Enter portal |
| `a` | Give amulet (bad ending) |
| `b` | Keep amulet (good ending) |
| `R` | Restart game |
| `ESC` | Quit to menu |
| `c` (main menu) | Hall of Fame |

| Symbol | Meaning |
|--------|---------|
| `"` (gold) | Amulet of Yendor |
| `O` (magenta) | Entity's Portal |
| `>` | Stairs down |
| `@` | You (the player) |

