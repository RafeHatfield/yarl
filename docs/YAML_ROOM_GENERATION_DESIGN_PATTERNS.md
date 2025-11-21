# 🎨 YAML Room Generation - Design Patterns & Troubleshooting

## Table of Contents
1. [Design Patterns](#design-patterns)
2. [Troubleshooting](#troubleshooting)
3. [Performance Considerations](#performance-considerations)
4. [Advanced Techniques](#advanced-techniques)
5. [Level Design Philosophy](#level-design-philosophy)

---

## Design Patterns

### Pattern 1: Difficulty Curve (The Classic Arc)

Create a smooth difficulty progression across the game:

```yaml
level_overrides:
  # Tier 1-5: Learning Phase
  1:
    parameters:
      max_monsters_per_room: 1
      max_rooms: 6
    guaranteed_spawns:
      mode: "additional"
      items:
        - type: "healing_potion"
          count: 3
  
  # Tier 2: Early Game
  5:
    parameters:
      max_monsters_per_room: 2
      max_rooms: 12
    guaranteed_spawns:
      mode: "additional"
      items:
        - type: "healing_potion"
          count: 2
  
  # Tier 3: Mid Game
  10:
    parameters:
      max_monsters_per_room: 3
      max_rooms: 15
    guaranteed_spawns:
      mode: "additional"
      items:
        - type: "healing_potion"
          count: 1
        - type: "fireball_scroll"
          count: "0-1"
  
  # Tier 4: Late Game
  20:
    parameters:
      max_monsters_per_room: 5
      max_rooms: 20
    guaranteed_spawns:
      mode: "additional"
      items:
        - type: "healing_potion"
          count: 1
  
  # Tier 5: Final Boss
  25:
    parameters:
      max_monsters_per_room: 6
      max_rooms: 12
    special_rooms:
      - type: "dragon_lair"
        count: 1
        placement: "largest"
        guaranteed_spawns:
          monsters:
            - type: "dragon"
              count: 1
```

**Why it works:**
- Players learn gradually (level 1 is very safe)
- Challenge increases smoothly (monsters_per_room: 1→6)
- Healing items decrease (players get better)
- Boss level has special room for epicness

---

### Pattern 2: Milestone Levels (Bosses Every 5)

Create distinct boss encounters:

```yaml
level_overrides:
  # Boss 1: Orc Warlord
  5:
    parameters:
      max_monsters_per_room: 3
    special_rooms:
      - type: "orc_warcamp"
        count: 1
        placement: "largest"
        guaranteed_spawns:
          monsters:
            - type: "orc"
              count: "4-6"
          equipment:
            - type: "sword"
              count: "1-2"
  
  # Boss 2: Troll King
  10:
    parameters:
      max_monsters_per_room: 4
    special_rooms:
      - type: "troll_throne_room"
        count: 1
        placement: "largest"
        guaranteed_spawns:
          monsters:
            - type: "troll"
              count: 1
            - type: "orc"
              count: "3-5"
  
  # Boss 3: Slime Queen
  15:
    parameters:
      max_monsters_per_room: 4
    special_rooms:
      - type: "slime_spawning_pool"
        count: 1
        placement: "largest"
        guaranteed_spawns:
          monsters:
            - type: "large_slime"
              count: 2
            - type: "slime"
              count: "8-12"
  
  # Final Boss: Dragon
  25:
    parameters:
      max_monsters_per_room: 6
      min_room_size: 14
    special_rooms:
      - type: "dragon_lair"
        count: 1
        placement: "largest"
        min_room_size: 14
        guaranteed_spawns:
          monsters:
            - type: "dragon"
              count: 1
```

**Why it works:**
- Clear boss checkpoints (5, 10, 15, 20, 25)
- Each boss has unique theme
- Players know what to expect
- Progression feels earned

---

### Pattern 3: Faction Encounter (Mixed Opposition)

Create meaningful encounters with multiple enemy types:

```yaml
level_overrides:
  12:
    parameters:
      max_monsters_per_room: 4
      max_rooms: 16
    
    special_rooms:
      # Main faction room
      - type: "orc_encampment"
        count: 1
        placement: "largest"
        guaranteed_spawns:
          monsters:
            - type: "orc"
              count: "4-6"
            - type: "goblin"
              count: "2-3"
          equipment:
            - type: "sword"
              count: "1-2"
      
      # Allied faction room
      - type: "undead_crypt"
        count: 1
        placement: "smallest"
        guaranteed_spawns:
          monsters:
            - type: "zombie"
              count: "3-5"
            - type: "skeleton"
              count: "2-3"
      
      # Treasure guarded by faction
      - type: "faction_treasury"
        count: 1
        placement: "random"
        guaranteed_spawns:
          monsters:
            - type: "troll"
              count: 1
          items:
            - type: "healing_potion"
              count: 3
            - type: "fireball_scroll"
              count: 2
```

**Why it works:**
- Multiple monster types create variety
- Room placement tells story (main vs ally vs treasure)
- Different strategies needed for each room
- Replayability (different rooms each run)

---

### Pattern 4: Resource Management (Scarce Items)

Make players choose carefully:

```yaml
level_overrides:
  18:  # Late game, resources scarce
    parameters:
      max_monsters_per_room: 5
      max_items_per_room: 1  # Very low
    
    guaranteed_spawns:
      mode: "additional"
      items:
        - type: "healing_potion"
          count: 1  # Only one guarantee
    
    special_rooms:
      # Reward exploration
      - type: "hidden_armory"
        count: 1
        placement: "smallest"  # Hidden in small room
        guaranteed_spawns:
          items:
            - type: "healing_potion"
              count: 2
            - type: "fireball_scroll"
              count: 1
```

**Why it works:**
- Raises stakes (fewer healing items)
- Rewards exploration (hidden room)
- Players must choose battles wisely
- Tension increases naturally

---

### Pattern 5: Testing Showcase (All Content)

Verify all monsters/items work:

```yaml
# In level_templates_testing.yaml
99:
  guaranteed_spawns:
    mode: "replace"  # Only our content
    monsters:
      - type: "orc"
        count: 2
      - type: "troll"
        count: 1
      - type: "slime"
        count: 3
      - type: "large_slime"
        count: 1
      - type: "zombie"
        count: 1
      - type: "goblin"
        count: 2
      - type: "knight"
        count: 1
      - type: "skeleton"
        count: 1
    
    items:
      - type: "healing_potion"
        count: 5
      - type: "invisibility_scroll"
        count: 2
      - type: "fireball_scroll"
        count: 2
      - type: "lightning_scroll"
        count: 2
      - type: "confusion_scroll"
        count: 1
    
    equipment:
      - type: "sword"
        count: 2
      - type: "dagger"
        count: 2
      - type: "shield"
        count: 2
```

**Why it works:**
- Quick verification of all types
- No randomness (predictable)
- Easy combat testing
- Use `--start-level 99` during development

---

### Pattern 6: Asymmetric Difficulty (Easy & Hard Paths)

Create optional harder areas:

```yaml
level_overrides:
  13:
    parameters:
      max_rooms: 18  # More rooms = more choice
    
    special_rooms:
      # Easy path
      - type: "merchant_quarters"
        count: 1
        placement: "random"
        guaranteed_spawns:
          monsters:
            - type: "goblin"
              count: 1
          items:
            - type: "healing_potion"
              count: 2
      
      # Hard path (optional)
      - type: "troll_lair"
        count: 1
        placement: "random"
        guaranteed_spawns:
          monsters:
            - type: "troll"
              count: "1-2"
            - type: "orc"
              count: "3-4"
          equipment:
            - type: "sword"
              count: 1
```

**Why it works:**
- Players choose their challenge level
- Replayability (different paths each run)
- Caters to different skill levels
- Non-linear exploration feel

---

## Troubleshooting

### Issue 1: "Entities not spawning"

**Symptom:** Run game, level has no guaranteed_spawns

**Causes & Fixes:**

1. **YAML Syntax Error**
   ```yaml
   # ❌ Wrong: Inconsistent indentation
   guaranteed_spawns:
     mode: "additional"
       items:  # Extra indent!
         - type: "healing_potion"
   
   # ✅ Right: Consistent 2-space indents
   guaranteed_spawns:
     mode: "additional"
     items:
       - type: "healing_potion"
   ```

2. **Invalid Mode**
   ```yaml
   # ❌ Wrong
   guaranteed_spawns:
     mode: "replace_all"  # Not a valid mode
   
   # ✅ Right
   guaranteed_spawns:
     mode: "replace"  # or "additional"
   ```

3. **Level Number Not Configured**
   ```yaml
   # ❌ Wrong: No level 13 entry
   level_overrides:
     12:
       ...
     14:
       ...
   
   # ✅ Right: Add level 13
   level_overrides:
     13:
       guaranteed_spawns:
         ...
   ```

4. **Entity Type Doesn't Exist**
   - Check `config/entities.yaml` for valid types
   - Common typos: `"healing_potion"` vs `"heal_potion"`

**Fix:** Check `debug.log` for error messages

---

### Issue 2: "Room too small for special room"

**Symptom:** `min_room_size: 15` but no rooms generated

**Solution:**
```yaml
# ❌ Wrong: min_room_size too large
special_rooms:
  - type: "throne"
    min_room_size: 20

# ✅ Right: Reasonable constraint
special_rooms:
  - type: "throne"
    min_room_size: 12  # Room size can be 10-16
```

**Debug:** Increase `max_room_size` in parameters if needed

---

### Issue 3: "Level is too hard/easy"

**Symptom:** Level 5 is harder than level 10

**Solution:** Check parameter progression

```yaml
# ❌ Wrong: Backwards progression
1:
  parameters:
    max_monsters_per_room: 5  # Too high for tutorial!

10:
  parameters:
    max_monsters_per_room: 2  # Too low for mid-game!

# ✅ Right: Consistent increase
1:
  parameters:
    max_monsters_per_room: 1

10:
  parameters:
    max_monsters_per_room: 3
```

---

### Issue 4: "Guaranteed spawns not working"

**Symptom:** Specified items not appearing

**Checklist:**
- [ ] Is mode set to `"additional"` or `"replace"`?
- [ ] Are entity types valid?
- [ ] Is count > 0?
- [ ] Is level number 1-25?
- [ ] Does YAML parse without errors?

**Debug Command:**
```bash
python3 -c "from config.level_template_registry import get_level_template_registry; \
            registry = get_level_template_registry(); \
            registry.load_templates(); \
            print(registry.overrides[13])"
```

---

### Issue 5: "Testing templates not overriding"

**Symptom:** Changed `level_templates_testing.yaml` but no effect

**Solution:** Verify testing mode is enabled

```bash
# Make sure you're using --testing flag
python3 engine.py --testing --start-level 13

# Without flag, only level_templates.yaml loads
python3 engine.py --start-level 13  # ❌ Wrong
```

---

## Performance Considerations

### 1. Spawn Count Impact

```yaml
# ❌ SLOW: Too many entities
guaranteed_spawns:
  mode: "additional"
  monsters:
    - type: "orc"
      count: "20-30"  # Way too many!

# ✅ FAST: Reasonable spawn
guaranteed_spawns:
  mode: "additional"
  monsters:
    - type: "orc"
      count: "3-5"
```

**Impact:** 100+ entities on level = lag, pathfinding delays

### 2. Room Size Impact

```yaml
# ❌ SLOW: Huge rooms
parameters:
  max_room_size: 30  # Massive rooms

# ✅ FAST: Moderate rooms
parameters:
  max_room_size: 14  # Still epic
```

**Impact:** Larger rooms = larger sight lines = more A* pathfinding

### 3. Max Rooms Impact

```yaml
# ❌ SLOW: Too many rooms
parameters:
  max_rooms: 50  # Too many!

# ✅ BALANCED: Reasonable
parameters:
  max_rooms: 15  # Plenty to explore
```

**Impact:** More rooms = more entities = more AI updates

### 4. Optimal Settings

```yaml
# Recommended balance for good performance
parameters:
  max_rooms: 15          # Sweet spot
  min_room_size: 6
  max_room_size: 12      # Large but not huge
  max_monsters_per_room: 3  # Manageable
  max_items_per_room: 2     # Standard
```

---

## Advanced Techniques

### Technique 1: Conditional Content (Manual)

Create content that appears only at certain levels:

```yaml
level_overrides:
  # Early game: Easy
  1:
    guaranteed_spawns:
      mode: "additional"
      items:
        - type: "healing_potion"
          count: 5

  # Late game: Rare items
  20:
    guaranteed_spawns:
      mode: "additional"
      items:
        - type: "healing_potion"
          count: 1
        - type: "fireball_scroll"
          count: "1-2"
```

### Technique 2: Procedural Difficulty

Use ranges for variation:

```yaml
parameters:
  max_monsters_per_room: 3  # Always 3

# vs

guaranteed_spawns:
  monsters:
    - type: "orc"
      count: "2-4"  # Varies: 2, 3, or 4 each run
```

### Technique 3: Multi-Tier Loot

Layer rewards:

```yaml
special_rooms:
  - type: "treasure_vault"
    count: 1
    placement: "smallest"
    guaranteed_spawns:
      items:
        - type: "healing_potion"
          count: 5        # Common tier
        - type: "fireball_scroll"
          count: 2        # Rare tier
        - type: "sword"
          count: 1        # Epic tier
```

### Technique 4: Faction Themes

Use special rooms to establish lore:

```yaml
special_rooms:
  - type: "orc_encampment"
    count: 1
    guaranteed_spawns:
      monsters:
        - type: "orc"
          count: "3-5"
  
  - type: "troll_lair"
    count: 1
    guaranteed_spawns:
      monsters:
        - type: "troll"
          count: 1
  
  - type: "undead_crypt"
    count: 1
    guaranteed_spawns:
      monsters:
        - type: "zombie"
          count: "4-6"
```

**Effect:** Level tells story through room types

---

## Level Design Philosophy

### Principle 1: Progression Over Perfection

```
Level 1: Learning
"How do I move? What's a scroll? How do I fight?"

Level 5: Confidence
"I'm doing okay. This is fun."

Level 10: Challenge
"This is hard but fair."

Level 15: Mastery
"I understand the game now."

Level 20: Epic
"I'm becoming a legend."

Level 25: Victory
"I'm the champion."
```

### Principle 2: Variety Prevents Fatigue

```yaml
# ❌ Boring: Same rooms every level
level_overrides:
  5:
    parameters:
      max_rooms: 15
  6:
    parameters:
      max_rooms: 15  # Identical!

# ✅ Engaging: Each level is unique
level_overrides:
  5:
    parameters:
      max_rooms: 15
      max_monsters_per_room: 2
  6:
    special_rooms:
      - type: "mini_boss"
        count: 1
```

### Principle 3: Reward Exploration

```yaml
special_rooms:
  # Main path
  - type: "troll_throne"
    count: 1
    placement: "largest"
  
  # Hidden treasure (placed randomly)
  - type: "secret_vault"
    count: 1
    placement: "random"
    guaranteed_spawns:
      items:
        - type: "fireball_scroll"
          count: 2
```

**Effect:** Players explore more when rewarded

### Principle 4: Telegraphing Difficulty

```yaml
# Level looks hard → It is hard
13:
  parameters:
    max_monsters_per_room: 5
    max_rooms: 20  # Lots to fight

# Level looks easy → It is easy
2:
  parameters:
    max_monsters_per_room: 1
    max_rooms: 6
```

**Effect:** Players feel smart for recognizing patterns

### Principle 5: Failures Are Lessons

```yaml
# Allow players to die and learn
1:
  guaranteed_spawns:
    mode: "additional"
    items:
      - type: "healing_potion"
        count: 3  # Safety net on level 1

# Fewer lessons needed at end game
24:
  guaranteed_spawns:
    mode: "additional"
    items:
      - type: "healing_potion"
        count: 0  # None, really!
```

---

## Checklist for Good Level Design

- [ ] **Difficulty increases with level** (1 < 5 < 10 < 25)
- [ ] **Boss levels are clearly special** (themed rooms, large spaces)
- [ ] **Early levels teach mechanics** (rewards, healing items)
- [ ] **Late levels challenge mastery** (few healing items, many enemies)
- [ ] **Variety in encounters** (different monsters, themes)
- [ ] **Rewards exploration** (hidden rooms, extra loot)
- [ ] **No "difficulty cliffs"** (smooth progression)
- [ ] **Performance is acceptable** (no lag, reasonable entity counts)
- [ ] **Gameplay tells story** (faction themes, lore)
- [ ] **Player agency** (choices matter, multiple paths)

---

## Summary

**Good level design through YAML:**
1. Start simple (tutorial levels)
2. Increase difficulty gradually
3. Create memorable boss encounters
4. Reward player exploration
5. Vary gameplay with themes
6. Test and iterate quickly

**Happy designing!** 🎮






