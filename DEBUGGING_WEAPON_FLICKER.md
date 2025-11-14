# Debugging Weapon Flicker — Diagnostic Output Added

## Your Key Observation ✅
- **Bodies alone**: No flicker ✓
- **Bodies with weapons**: Flicker ✓  
- **Weapons alone**: Flicker ✓

**This tells us the problem is specifically with ITEMS/WEAPONS, not corpses.**

## Root Cause Hypothesis

The flicker is likely caused by **weapons/items appearing and disappearing from the entity list**, possibly because:

1. **Loot is added to entities list asynchronously** (not on the same frame as death)
2. **Loot is being removed or lost somehow** (could be a bug in the entities list management)
3. **Entity list is being copied/recreated** each frame, losing dropped items
4. **Multiple instances of the same loot are being added** (duplicates causing issues)

## Diagnostic Output Added

I've added simple `print()` statements to help us trace **exactly what's happening** with weapons/items:

### 1. Loot Addition Tracking
**File:** `engine/systems/ai_system.py` (lines 406-408)

When a monster dies and drops loot, you'll now see:
```
[LOOT_DEBUG] Adding 2 items from Orc Corpse at (30, 15)
  -> Item: Longsword at (30, 15)
  -> Item: Leather Armor at (30, 15)
```

This shows:
- How many items were dropped
- The exact names and positions of each item
- When they were added to the entity list

### 2. Tooltip Rendering Tracking
**File:** `render_functions.py` (lines 384-393)

When hovering over a corpse or weapon, you'll now see:
```
[TOOLTIP_RENDER] frame=100 pos=(30,15) count=2 entities=[('Orc Corpse', 'corpse'), ('Longsword', 'item')]
[TOOLTIP_RENDER] frame=101 pos=(30,15) count=1 entities=[('Orc Corpse', 'corpse')]
[TOOLTIP_RENDER] frame=102 pos=(30,15) count=2 entities=[('Orc Corpse', 'corpse'), ('Longsword', 'item')]
```

This shows:
- Each frame that a tooltip is rendered
- How many entities are at that position
- Whether the count is **alternating** (FLICKER!) or stable

## How to Capture the Diagnostic Output

### Step 1: Run the Game
```bash
python engine.py --testing 2>&1 | tee /tmp/flicker_debug.log
```

(The `2>&1 | tee` captures all output to both screen and file)

### Step 2: Reproduce the Flicker
1. Kill first orc (baseline)
2. Kill second orc (flicker appears)
3. Hover over the corpse + weapon

### Step 3: Watch for Patterns
Look for:

**PATTERN A - Loot Only Added Once:**
```
[LOOT_DEBUG] Adding 2 items from Orc Corpse at (30, 15)
  -> Item: Longsword at (30, 15)
  -> Item: Leather Armor at (30, 15)

[TOOLTIP_RENDER] frame=100 pos=(30,15) count=2 ...
[TOOLTIP_RENDER] frame=101 pos=(30,15) count=2 ...
[TOOLTIP_RENDER] frame=102 pos=(30,15) count=1 ... ← LOOT DISAPPEARED!
[TOOLTIP_RENDER] frame=103 pos=(30,15) count=2 ... ← LOOT REAPPEARED!
```
**Diagnosis:** Loot is being removed/lost between frames

**PATTERN B - Loot Added Multiple Times:**
```
[LOOT_DEBUG] Adding 2 items from Orc Corpse at (30, 15)
[LOOT_DEBUG] Adding 2 items from Orc Corpse at (30, 15) ← ADDED AGAIN!
[LOOT_DEBUG] Adding 2 items from Orc Corpse at (30, 15) ← AND AGAIN!
```
**Diagnosis:** Same loot is being added repeatedly (likely causing entity list growth)

**PATTERN C - Count Alternates:**
```
[TOOLTIP_RENDER] frame=100 pos=(30,15) count=2 ...
[TOOLTIP_RENDER] frame=101 pos=(30,15) count=2 ...
[TOOLTIP_RENDER] frame=102 pos=(30,15) count=1 ... ← ALTERNATES!
[TOOLTIP_RENDER] frame=103 pos=(30,15) count=2 ...
[TOOLTIP_RENDER] frame=104 pos=(30,15) count=1 ...
```
**Diagnosis:** Entity list is fluctuating (items appearing/disappearing)

## Step 4: Analyze the Logs

Save the output:
```bash
grep "\[TOOLTIP_RENDER\]" /tmp/flicker_debug.log > /tmp/tooltips.txt
grep "\[LOOT_DEBUG\]" /tmp/flicker_debug.log > /tmp/loot.txt
```

Then check:
1. **Does LOOT_DEBUG appear only once, or repeatedly?**
2. **Does TOOLTIP_RENDER count alternate, or stay stable?**
3. **Are items at the right position each time?**

## Expected Output (Stable - No Flicker)

```
[LOOT_DEBUG] Adding 1 items from Orc Corpse at (30, 15)
  -> Item: Longsword at (30, 15)

[TOOLTIP_RENDER] frame=100 pos=(30,15) count=2 entities=[('Orc Corpse', 'corpse'), ('Longsword', 'item')]
[TOOLTIP_RENDER] frame=101 pos=(30,15) count=2 entities=[('Orc Corpse', 'corpse'), ('Longsword', 'item')]
[TOOLTIP_RENDER] frame=102 pos=(30,15) count=2 entities=[('Orc Corpse', 'corpse'), ('Longsword', 'item')]
[TOOLTIP_RENDER] frame=103 pos=(30,15) count=2 entities=[('Orc Corpse', 'corpse'), ('Longsword', 'item')]
```

Notice: **Count stays at 2, LOOT_DEBUG appears once, entities are consistent**

## Expected Output (Flicker - What We'll See)

The count will alternate or items will disappear/reappear.

## Where the Fix Will Likely Be

Based on this analysis, the fix will probably be in one of:

1. **`engine/systems/ai_system.py`** - Loot is being added multiple times or at wrong times
2. **`engine_integration.py` or game loop** - Entity list is being copied/reset
3. **`entity.py`** - Something is removing items from the entity list
4. **`death_functions.py`** - Loot dropping logic has a timing issue

## Next: Send Me the Output

Once you run the game with the diagnostic output enabled:

1. Reproduce the flicker while hovering over the corpse+weapon
2. Let it run for 10-15 frames showing the flicker
3. Copy the output (especially the [TOOLTIP_RENDER] and [LOOT_DEBUG] lines)
4. Show me the pattern

This will tell us **EXACTLY** what's causing the weapon flicker! 🎯

---

**Files Modified:**
- `engine/systems/ai_system.py` - Added loot tracking
- `render_functions.py` - Added tooltip entity count tracking
- `WEAPON_FLICKER_ANALYSIS.md` - Analysis of the issue

**To Remove Diagnostics Later:** Just delete the `print()` statements from those two files.

