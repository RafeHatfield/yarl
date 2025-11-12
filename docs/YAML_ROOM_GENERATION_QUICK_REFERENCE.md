# 🚀 YAML Room Generation - Quick Reference

## 30-Second Overview

Edit `config/level_templates.yaml` to customize any level (1-25):

```yaml
level_overrides:
  13:  # Your level number
    parameters:
      max_monsters_per_room: 5  # Harder!
    guaranteed_spawns:
      mode: "additional"
      items:
        - type: "healing_potion"
          count: 3
    special_rooms:
      - type: "boss_chamber"
        count: 1
        placement: "largest"
        guaranteed_spawns:
          monsters:
            - type: "troll"
              count: 1
```

**Test it:** `python3 engine.py --testing --start-level 13`

---

## Syntax Cheat Sheet

### Basic Template

```yaml
level_overrides:
  <LEVEL>:
    parameters:           # Tier 2: How to generate
      max_rooms: 15
      min_room_size: 6
      max_room_size: 12
      max_monsters_per_room: 3
      max_items_per_room: 2
    
    guaranteed_spawns:    # Tier 1: What to spawn
      mode: "additional"  # or "replace"
      monsters:
        - type: "orc"
          count: 2
      items:
        - type: "healing_potion"
          count: "2-4"
      equipment:
        - type: "sword"
          count: 1
    
    special_rooms:        # Tier 2: Themed rooms
      - type: "throne"
        count: 1
        placement: "largest"  # or "random" or "smallest"
        min_room_size: 10
        guaranteed_spawns:
          monsters:
            - type: "troll"
              count: 1
```

---

## Common Patterns

### Pattern 1: Easy Level (Tutorial)

```yaml
1:
  parameters:
    max_rooms: 6
    max_monsters_per_room: 1
  guaranteed_spawns:
    mode: "additional"
    items:
      - type: "healing_potion"
        count: 3
```

### Pattern 2: Boss Level

```yaml
10:
  parameters:
    max_monsters_per_room: 5
  special_rooms:
    - type: "boss_throne"
      count: 1
      placement: "largest"
      min_room_size: 12
      guaranteed_spawns:
        monsters:
          - type: "troll"
            count: 1
          - type: "orc"
            count: "3-5"
        items:
          - type: "healing_potion"
            count: 2
```

### Pattern 3: Themed Room

```yaml
3:
  special_rooms:
    - type: "slime_nest"
      count: 1
      placement: "random"
      guaranteed_spawns:
        monsters:
          - type: "slime"
            count: "5-8"
```

### Pattern 4: Testing Level

```yaml
# In level_templates_testing.yaml
99:
  guaranteed_spawns:
    mode: "replace"  # Only test content
    monsters:
      - type: "orc"
        count: 5
      - type: "troll"
        count: 2
    items:
      - type: "healing_potion"
        count: 10
```

---

## Entity Types

### Common Monsters
`orc`, `troll`, `slime`, `large_slime`, `zombie`, `goblin`, `knight`, `skeleton`

### Common Items
`healing_potion`, `invisibility_scroll`, `fireball_scroll`, `lightning_scroll`, `confusion_scroll`, `identify_scroll`, `raise_dead_scroll`, `teleport_scroll`

### Common Equipment
`sword`, `dagger`, `shield`, `chain_mail`, `chain_coif`, `chain_boots`, `ring_of_might`, `ring_of_protection`

### Map Features
`chest`, `signpost`, `mural`

---

## Count Syntax

| Format | Meaning | Example |
|--------|---------|---------|
| `count: 5` | Always 5 | Always spawn 5 |
| `count: "3-8"` | Random 3-8 | Random each time |
| `count: "5"` | Always 5 | Same as integer |

---

## Mode Comparison

| Mode | Use Case | Example |
|------|----------|---------|
| `"additional"` | Normal levels (randomness + guaranteed) | Level 5: Add 2 potions to normal spawns |
| `"replace"` | Testing or controlled levels (only guaranteed) | Testing level: Only orcs and trolls |

---

## Placement Strategies for Special Rooms

| Strategy | Meaning | Use For |
|----------|---------|---------|
| `"random"` | Any room can be this room type | Treasure chambers (hidden anywhere) |
| `"largest"` | Biggest room becomes this type | Boss arenas |
| `"smallest"` | Smallest room becomes this type | Hidden treasures |

---

## Parameters (Difficulty Scaling)

```yaml
parameters:
  max_rooms: 15                # Rooms 8-20 (more = harder)
  min_room_size: 6             # Small 4-8 (tight spaces)
  max_room_size: 12            # Large 10-16 (epic fights)
  max_monsters_per_room: 3     # Dangerous 1-6 monsters/room
  max_items_per_room: 2        # Loot density
  vault_count: 2               # 0-3 treasure vaults
```

### Difficulty Curve

```
Early (1-5):     max_rooms=6,   max_monsters=1,   lax
Mid (10-15):     max_rooms=15,  max_monsters=3,   balanced
Late (20-25):    max_rooms=20+, max_monsters=6+,  hard
```

---

## Door Rules (Corridor Configuration)

Add doors to corridors that connect rooms. Doors can be locked, secret, or open.

```yaml
door_rules:
  spawn_ratio: 0.5            # 0.0-1.0: probability door appears in corridor
  styles:                     # Door types with weighted selection
    - type: "wooden_door"
      weight: 70              # 70% wooden (higher = more common)
    - type: "iron_door"
      weight: 20              # 20% iron doors
    - type: "stone_door"
      weight: 10              # 10% stone doors
  locked:                     # Optional: make doors locked
    chance: 0.5               # 50% of placed doors are locked
    key_tag: "iron_key"       # Key type required to unlock
  secret:                     # Optional: make doors hidden
    chance: 0.3               # 30% of doors appear as walls
    search_dc: 12             # DC 12 to discover via search
```

### Quick Patterns

**All doors locked (fortress):**
```yaml
door_rules:
  spawn_ratio: 1.0
  styles: [{ type: "iron_door", weight: 1 }]
  locked: { chance: 1.0, key_tag: "iron_key" }
```

**Secret passages:**
```yaml
door_rules:
  spawn_ratio: 0.6
  styles: [{ type: "wooden_door", weight: 1 }]
  secret: { chance: 1.0, search_dc: 14 }
```

**Mixed secure corridors:**
```yaml
door_rules:
  spawn_ratio: 0.8
  styles:
    - type: "iron_door"
      weight: 1
  locked: { chance: 0.5, key_tag: "iron_key" }
  secret: { chance: 0.2, search_dc: 12 }
```

---

## Secret Rooms (Hidden Chambers)

Carve hidden rooms adjacent to corridors, connected by secret doors with hint markers.

```yaml
secret_rooms:
  target_per_floor: 2               # Try to create 2 secret rooms
  min_room_size: 5                  # Minimum secret room dimension
  connection_bias: "any"            # "any" or "dead_end" - where to place doors
  discovery:
    search_action: true             # Can be found via search
    auto_on_map_item: null          # Item type that reveals (optional)
    ambient_hint: "?"               # Marker shown outside wall
```

### Quick Patterns

**Simple hidden treasure:**
```yaml
secret_rooms:
  target_per_floor: 1
  min_room_size: 6
  discovery: { search_action: true, ambient_hint: "?" }
```

**Multiple secret areas:**
```yaml
secret_rooms:
  target_per_floor: 3
  min_room_size: 5
  connection_bias: "dead_end"
  discovery: { search_action: true, ambient_hint: "*" }
```

---

## Trap Rules (Hazardous Map Features)

Place hazardous traps that damage, slow, or alert enemies when triggered.

```yaml
trap_rules:
  density: 0.1                      # 0.0-1.0: probability per room tile
  whitelist_rooms: []               # Empty = all rooms; or ["boss_arena"]
  trap_table:                       # Available traps with weights
    - id: "spike_trap"
      weight: 3                     # Damage + bleed
    - id: "web_trap"
      weight: 2                     # Slow + snare
    - id: "alarm_plate"
      weight: 1                     # Alert nearby mobs
  detection:
    passive_chance: 0.1             # Base 10% to detect when stepping on
    detectable: true                # If false, trap always stays hidden
    reveal_on: ["detect_magic"]     # Items that auto-reveal
```

### Quick Patterns

**Sparse hazards (5% of tiles):**
```yaml
trap_rules:
  density: 0.05
  trap_table:
    - id: "spike_trap"
      weight: 2
    - id: "web_trap"
      weight: 1
  detection: { passive_chance: 0.2, detectable: true }
```

**Death trap gauntlet (30% of tiles in specific rooms):**
```yaml
trap_rules:
  density: 0.3
  whitelist_rooms: ["boss_arena", "cursed_chamber"]
  trap_table:
    - id: "spike_trap"
      weight: 5
    - id: "alarm_plate"
      weight: 3
  detection: { passive_chance: 0.05, detectable: true }
```

**Always-hidden curses:**
```yaml
trap_rules:
  density: 0.02
  trap_table:
    - id: "curse_trap"
      weight: 1
  detection: { passive_chance: 0.0, detectable: false }
```

---

## Stairs Configuration (Level Transitions)

Control stairs behavior, return restrictions, and spawn bias near stairs.

```yaml
stairs:
  up: true                          # Can go up to previous floors
  down: true                        # Can go down to next floors
  restrict_return_levels: 0         # Levels back player CANNOT return to (0 = no restriction)
  spawn_rules:
    near_start_bias: 0.5            # 0.0-1.0: bias for spawning near stairs (higher = more)
```

### Quick Patterns

**Normal open dungeon:**
```yaml
stairs:
  up: true
  down: true
  restrict_return_levels: 0
  spawn_rules: { near_start_bias: 0.5 }
```

**One-way descent (trap/mine):**
```yaml
stairs:
  up: false                         # No return!
  down: true
  restrict_return_levels: 0
```

**Linear progression (no backtracking past 2 levels):**
```yaml
stairs:
  up: true
  down: true
  restrict_return_levels: 2        # Can only go back 2 levels max
```

**Tight spawn near stairs:**
```yaml
stairs:
  up: true
  down: true
  restrict_return_levels: 0
  spawn_rules: { near_start_bias: 0.8 }  # Mobs spawn close to stairs
```

---

## Floor State Persistence

When player moves between levels:
1. **Current floor saved**: Entities, door states, trap states recorded
2. **Far mobs despawned**: Entities >20 tiles from stairs entry are removed
3. **State restored**: When returning to old floor, saved state is loaded
4. **Respawn capped**: Prevents infinite farming on re-entry

This happens automatically - no YAML needed!

---

## Connectivity Configuration (Dungeon Layout)

Control how rooms connect, corridor styles, and door placement patterns.

```yaml
connectivity:
  min_connectivity: "mst"                 # "mst" or "mst_plus_loops"
  loop_count: 0                           # Additional loops (only for mst_plus_loops)
  corridor_style: "orthogonal"            # "orthogonal", "jagged", or "organic"
  door_every_n_tiles: 0                   # Place doors every N tiles (0 = no placement)
```

### Quick Patterns

**Simple tree (no loops - fastest):**
```yaml
connectivity:
  min_connectivity: "mst"
  corridor_style: "orthogonal"
```

**Tree with 2 loops (complex maze):**
```yaml
connectivity:
  min_connectivity: "mst_plus_loops"
  loop_count: 2
  corridor_style: "orthogonal"
```

**Natural winding corridors:**
```yaml
connectivity:
  min_connectivity: "mst"
  corridor_style: "organic"
```

**With automatic door placement every 8 tiles:**
```yaml
connectivity:
  min_connectivity: "mst_plus_loops"
  loop_count: 1
  corridor_style: "orthogonal"
  door_every_n_tiles: 8
```

### Corridor Styles

| Style | Appearance | Effect |
|-------|-----------|--------|
| `orthogonal` | Straight L-shaped | Clean, dungeon-like |
| `jagged` | Random zigzag | Chaotic, unpredictable |
| `organic` | Smooth curves | Natural, winding |

---

## File Locations

| File | Purpose | When to Use |
|------|---------|------------|
| `config/level_templates.yaml` | Main config | Normal gameplay |
| `config/level_templates_testing.yaml` | Testing | Testing mode overrides |
| `config/level_templates_examples.yaml` | Reference | Copy templates from here |

---

## Workflow

### 1. Design on Paper
```
"Level 13 should be hard, with a boss room"
```

### 2. Write YAML
```yaml
13:
  parameters:
    max_monsters_per_room: 5
  special_rooms:
    - type: "boss"
      count: 1
      placement: "largest"
```

### 3. Test
```bash
python3 engine.py --testing --start-level 13
```

### 4. Play & Adjust
- Too easy? Increase `max_monsters_per_room`
- Too hard? Add more `guaranteed_spawns: items: healing_potion`
- Room too small? Add `min_room_size: 12`

### 5. Copy to Normal
When happy, move from `level_templates_testing.yaml` to `level_templates.yaml`

---

## Common Mistakes

❌ **Wrong:** Invalid entity type
```yaml
items:
  - type: "super_potion"  # Doesn't exist!
    count: 1
```
✅ **Right:** Use valid type
```yaml
items:
  - type: "healing_potion"
    count: 1
```

❌ **Wrong:** Inconsistent count syntax
```yaml
count: 3-5  # Missing quotes!
```
✅ **Right:** Quote ranges
```yaml
count: "3-5"  # Correct
```

❌ **Wrong:** mode on normal level
```yaml
guaranteed_spawns:
  mode: "replace"  # Removes all randomness!
```
✅ **Right:** Use additional for normal
```yaml
guaranteed_spawns:
  mode: "additional"  # Keeps game fresh
```

❌ **Wrong:** Special room in non-existent room
```yaml
special_rooms:
  - type: "huge_throne"
    count: 5  # Too many!
```
✅ **Right:** Limited special rooms
```yaml
special_rooms:
  - type: "throne"
    count: 1  # One throne
```

---

## Testing Checklist

- [ ] Syntax is valid YAML (no mixing tabs/spaces)
- [ ] Entity types exist in `entities.yaml`
- [ ] Level number is 1-25
- [ ] Count values are integers or `"min-max"` strings
- [ ] mode is `"additional"` or `"replace"`
- [ ] Placement is `"random"`, `"largest"`, or `"smallest"`
- [ ] Level is easy → hard as numbers increase
- [ ] Boss levels have special rooms
- [ ] Tutorial level (1) has healing items

---

## Next Steps

1. **Read:** Full guide at `docs/YAML_ROOM_GENERATION_SYSTEM.md`
2. **Copy:** A template from `level_templates_examples.yaml`
3. **Modify:** For your level
4. **Test:** `python3 engine.py --testing --start-level <N>`
5. **Share:** Commit to git when happy

---

## Quick Stats

```
Levels:               1-25
Monsters:             15+ types
Items:                20+ types
Equipment:            10+ types
Parameters:           8 customizable
Placement strategies: 3 options
Count syntax:         Fixed or Range
Modes:                "additional" or "replace"
```

---

**That's it! You're ready to design dungeons. Go make something awesome.** 🎮

