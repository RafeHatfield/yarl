# Scroll Implementation Plan

## Current Status

### ✅ Already Defined in spell_catalog.py:
1. Haste - uses SpeedEffect (30 turns)
2. Fear - AOE terror effect (15 turns)
3. Blink - short-range teleport (5 range)
4. Light - reveals area
5. Detect Monster - temp monster detection (20 turns)
6. Magic Mapping - reveals dungeon layout
7. Earthquake - AOE damage (3d6, radius 3)
8. Identify - grants identify mode (10 turns) **DONE!**

### ✅ Status Effects Already Implemented:
- SpeedEffect (for Haste)
- IdentifyModeEffect (for Identify) **DONE!**
- All other buff/debuff effects

### ❌ Missing Implementations:

#### 1. HASTE Scroll
- **Status:** Spell defined, SpeedEffect exists
- **TODO:** Add to _cast_buff_spell handler
- **Complexity:** Easy (copy invisibility pattern)

#### 2. FEAR Scroll  
- **Status:** Spell defined, needs FearEffect or special handler
- **TODO:** Decide: Create FearEffect OR make enemies flee via AI
- **Complexity:** Medium (AOE that affects multiple monsters)

#### 3. BLINK Scroll
- **Status:** Spell defined
- **TODO:** Create _cast_blink_spell (like teleport but shorter)
- **Complexity:** Easy (copy teleport pattern)

#### 4. LIGHT Scroll
- **Status:** Spell defined
- **TODO:** Create _cast_light_spell (reveal area in FOV)
- **Complexity:** Medium (need to modify game_map explored status)

#### 5. DETECT MONSTER Scroll
- **Status:** Spell defined
- **TODO:** Create DetectMonsterEffect OR simple one-time reveal
- **Complexity:** Medium-Hard (might need UI changes)

#### 6. MAGIC MAPPING Scroll
- **Status:** Spell defined
- **TODO:** Create _cast_magic_mapping_spell (reveal entire level)
- **Complexity:** Easy (set all tiles to explored)

#### 7. EARTHQUAKE Scroll
- **Status:** Spell defined as AOE offensive
- **TODO:** Verify _cast_aoe_spell handles it correctly
- **Complexity:** Easy (should work already)

#### 8. Registration & Spawn Rates
- **TODO:** Register all scrolls in initialize_new_game.py
- **TODO:** Add spawn rates to game_constants.py
- **Complexity:** Easy

---

## Implementation Order

### Phase 1: Quick Wins (Easy Scrolls)
1. **Haste** - Add to _cast_buff_spell
2. **Blink** - Add _cast_blink_spell
3. **Magic Mapping** - Add _cast_magic_mapping_spell
4. **Earthquake** - Verify existing AOE handler

### Phase 2: Medium Complexity
5. **Light** - Add _cast_light_spell
6. **Fear** - Add AOE fear handler (make enemies flee)

### Phase 3: Advanced (If Needed)
7. **Detect Monster** - Add detection mechanic

### Phase 4: Integration
8. Register all scrolls in initialize_new_game.py
9. Add spawn rates to game_constants.py
10. Write comprehensive tests
11. Playtest!

---

## Design Decisions

### FEAR Scroll:
**Option A:** Create FearEffect status, swap AI to fleeing AI
**Option B:** AOE effect that makes monsters move away for X turns
**Decision:** Option A (more flexible, reusable)

### DETECT MONSTER:
**Option A:** Temp reveal all monsters on map
**Option B:** Create DetectMonsterEffect that shows monsters in radius
**Decision:** Option B (more interesting gameplay)

### LIGHT:
**Option A:** Reveal all tiles in current FOV permanently
**Option B:** Create temporary light effect
**Decision:** Option A (simpler, useful)

---

## Next Steps

Start with Phase 1 (Haste, Blink, Magic Mapping, Earthquake).
These are the quickest wins and will immediately add 4 new scrolls to the game!

