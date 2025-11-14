# Weapon Flicker Analysis

## Your Observation
- **Bodies alone**: No flicker
- **Bodies with weapons**: Flicker appears
- **Weapons alone**: Flicker appears

## Root Cause Hypothesis

The flicker is likely caused by **items (weapons/loot) appearing and disappearing from the entities list frame-to-frame**, not the corpse itself.

### Why This Happens

When a monster dies:
1. `kill_monster()` is called (death_functions.py:175)
2. Loot is dropped and stored in `monster._dropped_loot` (line 220)
3. Loot is NOT immediately added to entities
4. Later, in the AI system (ai_system.py:404-410), loot is added to entities
5. But this happens **during game logic, not rendering**

### The Flicker Pattern

If loot adding is asynchronous or happens at unpredictable times relative to rendering:

```
Frame 100: entities = [corpse at (30,15)]
           -> render_tooltip -> "Orc Corpse"
           -> AI system adds loot
           
Frame 101: entities = [corpse at (30,15), weapon at (30,15)]
           -> render_tooltip -> "Orc Corpse\n  Longsword" (multi-entity)
           -> some condition causes loot removal?
           
Frame 102: entities = [corpse at (30,15)]  
           -> render_tooltip -> "Orc Corpse"
           -> loot re-added?
           
Frame 103: entities = [corpse at (30,15), weapon at (30,15)]
           -> render_tooltip -> "Orc Corpse\n  Longsword"
```

This would create **visible flicker** where the tooltip alternates between single and multi-entity view.

## Key Questions to Answer

1. **When is loot actually added to entities?**
   - Is it every frame?
   - Is it only once after death?
   - Is it conditional on something?

2. **Is there any code that removes items from entities?**
   - Could items be getting removed each frame?
   - Could there be a garbage collection issue?

3. **Is the entity list being copied/reset somewhere?**
   - Could a fresh entities list be created each frame?
   - Could old loot be getting filtered out?

## Investigation Steps

### Step 1: Add Simple Loot Tracking
Add basic logging to see when loot is added/removed:

```python
# In ai_system.py, around line 404
if hasattr(dead_entity, '_dropped_loot') and dead_entity._dropped_loot:
    print(f"[LOOT_ADD] frame=??? dead={dead_entity.name} loot_count={len(dead_entity._dropped_loot)}")
    game_state.entities.extend(dead_entity._dropped_loot)
```

### Step 2: Track Entity List Size
In render_functions.py tooltip section:

```python
# Around line 365
print(f"[ENTITIES_AT_POS] pos=({world_x},{world_y}) total_entities={len(entities)} tooltip_count={len(entities_at_position)}")
```

### Step 3: Check Entity Filtering
Look for any code that filters the entities list:

```bash
grep -r "entities\s*=" engine/ services/ --include="*.py" | grep -v ".pyc"
```

Does the entities list get recreated anywhere?

## Proposed Quick Fix

If loot adding is the issue, we could try:

1. **Ensure loot is added immediately after death** (not delayed)
2. **Check that loot isn't being removed anywhere**
3. **Add protection to prevent items from being added multiple times**

## Next Steps

1. Add print statements to track loot addition
2. Monitor whether loot count fluctuates each frame
3. If it does, find where it's being removed
4. Fix the removal logic or add guards to prevent it

---

**Your observation about weapons flickering is the KEY insight.** This tells us the problem is NOT with corpse rendering (which is stable), but with **item appearance/disappearance** in the entity list.

