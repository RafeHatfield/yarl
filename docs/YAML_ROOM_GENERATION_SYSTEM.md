# 🏗️ YAML Room Generation System - Complete Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [YAML File Structure](#yaml-file-structure)
3. [Core Concepts](#core-concepts)
4. [Tier 1: Guaranteed Spawns](#tier-1-guaranteed-spawns)
5. [Tier 2: Level Parameters](#tier-2-level-parameters)
6. [Tier 2: Special Rooms](#tier-2-special-rooms)
7. [Tier 2: Door Rules](#tier-2-door-rules)
8. [Tier 2: Secret Rooms](#tier-2-secret-rooms)
9. [Tier 2: Trap Rules](#tier-2-trap-rules)
10. [Tier 2: Stairs Configuration](#tier-2-stairs-configuration)
11. [Tier 2: Connectivity Configuration](#tier-2-connectivity-configuration)
12. [Configuration Files](#configuration-files)
13. [How to Use This System](#how-to-use-this-system)
14. [Examples](#examples)
15. [Growth Opportunities](#growth-opportunities)

---

## System Overview

The YAML room generation system is a **declarative configuration framework** that allows designers to customize dungeon generation without writing code. It works at **two tiers**:

### Tier 1: Guaranteed Spawns
**What it does:** Ensures specific monsters, items, and equipment appear on a level.
- Replaces or supplements normal random spawning
- Global to the entire level
- Use case: "Level 1 should always have 2 healing potions"

### Tier 2: Generation Parameters & Special Rooms
**What it does:** Customize the level generation algorithm and create themed room types.
- **Parameters:** Control room size, count, and difficulty
- **Special Rooms:** Create thematic rooms with guaranteed contents
- Use case: "Level 10 should have a boss throne room"

---

## YAML File Structure

```yaml
# config/level_templates.yaml (for normal gameplay)
# config/level_templates_testing.yaml (for testing - overrides normal)

version: "1.0"

level_overrides:
  <level_number>:
    parameters:
      # Tier 2: Level generation parameters
      max_rooms: <int>
      min_room_size: <int>
      max_room_size: <int>
      max_monsters_per_room: <int>
      max_items_per_room: <int>
      vault_count: <int>
    
    guaranteed_spawns:
      # Tier 1: Global level spawns
      mode: "additional" | "replace"
      monsters:
        - type: "<monster_id>"
          count: <int> | "<min>-<max>"
      items:
        - type: "<item_id>"
          count: <int> | "<min>-<max>"
      equipment:
        - type: "<equipment_id>"
          count: <int> | "<min>-<max>"
      map_features:
        - type: "<feature_id>"
          count: <int> | "<min>-<max>"
    
    special_rooms:
      # Tier 2: Thematic rooms
      - type: "<room_type_name>"
        count: <int>
        placement: "random" | "largest" | "smallest"
        min_room_size: <int>
        guaranteed_spawns:
          monsters: [...]
          items: [...]
          equipment: [...]
```

---

## Core Concepts

### 1. Level Number
- Valid range: **1-25** (standard roguelike depth)
- Special values:
  - **1:** Tutorial/intro level
  - **10, 15, 20, 25:** Boss/milestone levels
  - **Others:** Regular progression

### 2. Entity Types
Entity types come from the master `config/entities.yaml` file. Common types:

**Monsters:**
- `orc`, `troll`, `slime`, `large_slime`, `zombie`, `goblin`, `knight`, etc.

**Items:**
- `healing_potion`, `invisibility_scroll`, `fireball_scroll`, `lightning_scroll`, `confusion_scroll`, `identify_scroll`, `raise_dead_scroll`, `teleport_scroll`, etc.

**Equipment:**
- `sword`, `dagger`, `shield`, `chain_mail`, `chain_coif`, `chain_boots`, `ring_of_might`, `ring_of_protection`, etc.

**Map Features:**
- `chest`, `signpost`, `mural`, `portal`, etc.

### 3. Count Values
Count can be specified as:
- **Fixed integer:** `count: 5` (always 5)
- **Range string:** `count: "3-8"` (random 3-8)
- **Single string:** `count: "5"` (same as 5)

The system uses `random.randint(min, max)` to select within ranges.

### 4. Modes: "additional" vs "replace"
- **"additional":** Guaranteed spawns ADD to normal random spawning
  - Use when you want more content for a level
  - Example: "Always have 2 healing potions PLUS normal loot"
  
- **"replace":** Guaranteed spawns REPLACE all random spawning
  - Use for testing or themed levels where you control everything
  - Example: "Testing level with only orcs and trolls"

### 5. Placement Strategies
For special rooms, `placement` controls where the room type is assigned:

- **"random":** Any randomly selected room can become this room type
- **"largest":** Use the largest room(s) generated
- **"smallest":** Use the smallest room(s) generated

Example: Boss rooms use `placement: "largest"` to give them space.

---

## Tier 1: Guaranteed Spawns

Tier 1 controls what monsters, items, and equipment ALWAYS appear on a level.

### Structure

```yaml
level_overrides:
  <level>:
    guaranteed_spawns:
      mode: "additional" | "replace"  # Required
      monsters:
        - type: "orc"
          count: 2
        - type: "troll"
          count: "1-2"
      items:
        - type: "healing_potion"
          count: 3
        - type: "fireball_scroll"
          count: "1-2"
      equipment:
        - type: "sword"
          count: 1
      map_features:
        - type: "chest"
          count: 1
```

### Processing Order

1. **Normal spawning occurs first** (random monsters/items based on level)
2. **Mode is checked:**
   - `"additional"`: Guaranteed spawns are ADDED to entities list
   - `"replace"`: Entities list is cleared, ONLY guaranteed spawns are used
3. **For each spawn type, a random count is selected** (within the configured range)
4. **Entities are placed in random valid locations** on the level

### Best Practices

✅ **DO:**
- Use `"additional"` for normal levels (players still get surprises)
- Use `"replace"` for testing or tutorial levels
- Specify ranges for variety: `"2-4"` instead of always `4`
- Include healing items on dangerous levels

❌ **DON'T:**
- Over-guarantee items (players need challenge)
- Use `"replace"` in normal gameplay (removes randomness)
- Create impossible spawn counts for the level size

---

## Tier 2: Level Parameters

Tier 2 controls the ALGORITHM that generates the level.

### Available Parameters

```yaml
parameters:
  max_rooms: 15              # Total rooms to attempt (default: 15)
  min_room_size: 6           # Smallest room dimension (default: 6)
  max_room_size: 12          # Largest room dimension (default: 12)
  max_monsters_per_room: 3   # Monster spawn cap per room (default: 3)
  max_items_per_room: 2      # Item spawn cap per room (default: 2)
  vault_count: 2             # Treasure vault rooms (default: random 0-2)
  map_width: 80              # Override map width (default: 80)
  map_height: 45             # Override map height (default: 45)
```

### Parameter Effects

| Parameter | Default | Effect |
|-----------|---------|--------|
| `max_rooms` | 15 | More rooms = more exploration, more enemies |
| `min_room_size` | 6 | Smaller = tighter spaces, harder combat |
| `max_room_size` | 12 | Larger = epic boss arenas |
| `max_monsters_per_room` | 3 | Difficulty scaling |
| `max_items_per_room` | 2 | Loot density |
| `vault_count` | Random 0-2 | Extra treasure rooms |
| `map_width` | 80 | Horizontal scrolling test |
| `map_height` | 45 | Vertical scrolling test |

### Difficulty Progression Pattern

```yaml
# Early levels: Small, safe
level_overrides:
  1:
    parameters:
      max_rooms: 8
      min_room_size: 4
      max_room_size: 8
      max_monsters_per_room: 1

# Mid levels: Standard
  13:
    parameters:
      max_rooms: 15
      min_room_size: 6
      max_room_size: 12
      max_monsters_per_room: 3

# Late levels: Massive, deadly
  23:
    parameters:
      max_rooms: 20
      min_room_size: 10
      max_room_size: 16
      max_monsters_per_room: 6
```

---

## Tier 2: Special Rooms

Special rooms are **thematic, pre-configured room types** placed in generated dungeons.

### Structure

```yaml
special_rooms:
  - type: "throne_room"            # Room type identifier
    count: 1                         # How many of this room to create
    placement: "largest"             # Where to place it
    min_room_size: 12                # Minimum size required (optional)
    guaranteed_spawns:
      monsters:
        - type: "troll"
          count: 1
        - type: "orc"
          count: "2-4"
      items:
        - type: "healing_potion"
          count: 2
      equipment:
        - type: "sword"
          count: 1
```

### Key Features

**Type Field:**
- Can be any string identifier (`"throne_room"`, `"slime_nest"`, `"armory"`, etc.)
- NOT validated against a registry (designers can create custom names)
- Used for semantics/documentation

**Count Field:**
- How many instances of this room type to create
- `count: 1` = One throne room
- `count: 2` = Two identical throne rooms (useful for symmetry)

**Placement Field:**
- `"random"`: Any room can be selected
- `"largest"`: Only the largest room(s) qualify
- `"smallest"`: Only the smallest room(s) qualify

**Min Room Size:**
- Optional filter: skip rooms smaller than this
- Example: Boss throne room needs `min_room_size: 12`

**Guaranteed Spawns:**
- Same structure as Tier 1 spawns
- Limited to this specific room only
- Overrides any random spawns in that room

### Example: Complete Special Room

```yaml
special_rooms:
  - type: "dragon_lair"
    count: 1
    placement: "largest"
    min_room_size: 14
    guaranteed_spawns:
      monsters:
        - type: "dragon"
          count: 1
        - type: "goblin"
          count: "4-6"
      items:
        - type: "healing_potion"
          count: 3
        - type: "fireball_scroll"
          count: 2
      equipment:
        - type: "sword"
          count: 2
        - type: "shield"
          count: 1
```

### Multiple Special Rooms

```yaml
special_rooms:
  - type: "boss_throne"
    count: 1
    placement: "largest"
    min_room_size: 14
    guaranteed_spawns:
      monsters:
        - type: "boss_troll"
          count: 1
  
  - type: "treasure_vault"
    count: 1
    placement: "smallest"  # Hidden in small rooms!
    guaranteed_spawns:
      items:
        - type: "healing_potion"
          count: 5
        - type: "fireball_scroll"
          count: 3
```

---

## Tier 2: Door Rules

### What Are Door Rules?

Door rules configure how doors are placed in corridors that connect rooms. This allows you to create:
- **Locked corridors** that require keys
- **Secret passages** hidden as walls
- **Security barriers** for vault-style rooms
- **Open passages** for exploration

### When Does It Apply?

Door rules are **Tier 2 configuration** - they apply to how corridors are generated and populated with doors. They can be specified at:

1. **Level scope:** Applies to ALL corridor connections on that level
2. **Special room scope:** Applies ONLY to connections from that special room (overrides level rules)

### Full Syntax

```yaml
door_rules:
  spawn_ratio: float            # 0.0-1.0: probability each corridor gets a door
  styles:                       # List of door types (required if spawn_ratio > 0)
    - type: string             # Door entity type: "wooden_door", "iron_door", "stone_door"
      weight: int              # Weight for weighted random selection (higher = more common)
  locked:                       # Optional: make some doors locked
    chance: float              # 0.0-1.0: probability placed door starts locked
    key_tag: string            # Key tag needed to unlock (default: "iron_key")
  secret:                       # Optional: make some doors hidden
    chance: float              # 0.0-1.0: probability door is secret (appears as wall)
    search_dc: int             # Difficulty to discover via search (default: 12, higher = harder)
```

### Example: Level with Locked Doors

```yaml
5:
  parameters:
    max_monsters_per_room: 3
  
  door_rules:
    spawn_ratio: 0.75          # 75% of corridors have doors
    styles:
      - type: "wooden_door"
        weight: 70
      - type: "iron_door"
        weight: 30
    locked:
      chance: 0.5              # 50% of doors are locked
      key_tag: "iron_key"      # Requires iron_key to unlock
```

### Example: Level with Secret Passages

```yaml
10:
  door_rules:
    spawn_ratio: 0.6           # 60% of corridors have hidden doors
    styles:
      - type: "wooden_door"
        weight: 1
    secret:
      chance: 1.0              # 100% of doors are secret
      search_dc: 12            # Standard difficulty to discover
```

### Example: Special Room with Vault Security

```yaml
15:
  special_rooms:
    - type: "treasure_vault"
      count: 1
      placement: "largest"
      guaranteed_spawns:
        items:
          - type: "healing_potion"
            count: 5
      
      # Override level door rules for this room only
      door_rules:
        spawn_ratio: 1.0       # ALL connections to vault are guarded
        styles:
          - type: "iron_door"
            weight: 1          # Always iron doors
        locked:
          chance: 1.0          # ALL doors locked (fortress!)
          key_tag: "iron_key"  # Player must find key
        secret:
          chance: 0.0          # No hidden passages (security through locks)
```

### Design Patterns

**Pattern 1: Open Exploration (No Barriers)**
```yaml
door_rules:
  spawn_ratio: 0.0             # No doors, explore freely
```

**Pattern 2: Light Security (Some Doors)**
```yaml
door_rules:
  spawn_ratio: 0.5
  styles: [{ type: "wooden_door", weight: 1 }]
  # No locked or secret configuration = doors are just barriers
```

**Pattern 3: Fortress Dungeon (Locked Corridors)**
```yaml
door_rules:
  spawn_ratio: 1.0             # All corridors locked
  styles: [{ type: "iron_door", weight: 1 }]
  locked:
    chance: 1.0
    key_tag: "iron_key"
```

**Pattern 4: Mysterious Dungeon (Secret Doors)**
```yaml
door_rules:
  spawn_ratio: 0.6             # Some corridors hide secrets
  styles: [{ type: "wooden_door", weight: 1 }]
  secret:
    chance: 1.0                # All doors are secret
    search_dc: 14              # Challenging to discover
```

**Pattern 5: Mixed Security (Locked + Secret)**
```yaml
door_rules:
  spawn_ratio: 0.8             # Most corridors have doors
  styles:
    - type: "iron_door"
      weight: 1
  locked:
    chance: 0.4                # 40% locked
    key_tag: "iron_key"
  secret:
    chance: 0.3                # 30% hidden
    search_dc: 12
```

### Available Door Types

| Type | Color | Use Case |
|------|-------|----------|
| `wooden_door` | Brown | Common, standard doors |
| `iron_door` | Gray (metallic) | Secure, fortress-style |
| `stone_door` | Light gray | Ancient, dungeon aesthetic |

### Behavior Summary

| State | Appearance | Can Pass | Notes |
|-------|------------|----------|-------|
| Open unlocked door | '+' in door color | Yes | Normal passage |
| Closed unlocked door | '+' in door color | No | Can be opened |
| Locked door | '+' in door color | No | Requires matching key to unlock |
| Secret undiscovered | '#' (wall gray) | No | Appears as wall until discovered |
| Secret discovered | '+' in door color | Yes/No | Visible but may still be locked |

---

## Tier 2: Secret Rooms

### What Are Secret Rooms?

Secret rooms are hidden chambers carved into solid walls adjacent to existing corridors. They provide:
- **Exploration Rewards**: Hidden treasures and loot
- **Discovery Moments**: Finding secret passages creates memorable experiences
- **Challenge Variation**: Optional harder encounters in hidden areas
- **Map Knowledge**: Encourages exploration and experimentation

### Full Syntax

```yaml
secret_rooms:
  target_per_floor: int           # Number of secret rooms to attempt per level (0-5 typical)
  min_room_size: int              # Minimum room dimension (3+ required, 5-7 typical)
  connection_bias: string         # "any" or "dead_end" - where to place connections
  discovery:
    search_action: bool           # Can player find via search action? (default: true)
    auto_on_map_item: string|null # Item type that auto-reveals (optional, e.g., "map_scroll")
    ambient_hint: string          # Character/marker shown outside wall (default: "?")
```

### Example: Basic Secret Rooms

```yaml
10:
  secret_rooms:
    target_per_floor: 1           # One hidden chamber per level
    min_room_size: 6              # Decent-sized hidden rooms
    connection_bias: "any"
    discovery:
      search_action: true         # Player can find by searching
      ambient_hint: "?"           # Standard question mark hint
```

### Design Patterns

**Minimal Secrets (Exploration):**
```yaml
secret_rooms:
  target_per_floor: 1
  min_room_size: 5
  discovery: { search_action: true, ambient_hint: "?" }
```

**Discovery-Focused (Rewards Thorough Exploration):**
```yaml
secret_rooms:
  target_per_floor: 2
  min_room_size: 6
  connection_bias: "dead_end"
  discovery: { search_action: true, ambient_hint: "?" }
```

**Treasure Hunter's Paradise (Multiple Secrets):**
```yaml
secret_rooms:
  target_per_floor: 4
  min_room_size: 5
  discovery:
    search_action: true
    auto_on_map_item: "map_scroll"
    ambient_hint: "*"
```

### Acceptance Criteria

✅ **Secret rooms exist but not visible until discovered** - Rendered as walls (#) until revealed
✅ **Hints render properly** - Ambient marker shown outside wall  
✅ **Entering via secret door works** - Door opens to reveal hidden chamber

---

## Tier 2: Trap Rules

### What Are Traps?

Traps are hazardous map features that:
- Spawn at configurable density within rooms
- Deal damage or apply debuffs when triggered
- Can be detected (passively or via search action)
- Can be disarmed to prevent triggering
- Support multiple trap types with weighted selection

### Detection Model (Extensible)

Trap detection is **intentionally extensible** for future systems:

```
Base Detection (in trap_rules):
├─ passive_chance: Random detection when stepping on trap
├─ detectable: If false, trap is always hidden (impossible to detect)
└─ reveal_on: Items/conditions that auto-reveal (e.g., "detect_magic")

Future Extensions:
├─ Player skills/perks (e.g., "rogue_trap_sense": +0.3)
├─ Scrolls/potions (e.g., "detect_traps_scroll": sets to 1.0 for duration)
├─ Equipment (e.g., boots with trap detection bonus)
├─ Environmental (e.g., dark rooms harder to detect)
└─ Difficulty modifiers (e.g., higher difficulties = harder to detect)
```

This architecture allows future code to modify detection chances at runtime based on player state, items, and game conditions.

### Full Syntax

```yaml
trap_rules:
  density: float                    # 0.0-1.0: probability of trap per room tile
  whitelist_rooms: [str]           # Room types that CAN have traps (empty = all types)
  trap_table:                       # Available traps with weighted selection
    - id: "spike_trap"
      weight: 3                     # Traps with higher weight appear more often
    - id: "web_trap"
      weight: 2
    - id: "alarm_plate"
      weight: 1
  detection:
    passive_chance: 0.1             # Base 10% chance to detect when stepping on trap
    detectable: true                # If false, trap cannot be detected by any means
    reveal_on: ["detect_magic"]     # Items/conditions that auto-reveal traps
```

### Trap Types

| Trap | Effect | Notes |
|------|--------|-------|
| `spike_trap` | Damage + bleed status | Hazardous, high damage |
| `web_trap` | Slow/snare for N turns | Movement penalty, stackable |
| `alarm_plate` | Alert nearby mobs in faction | Tactical, draws reinforcements |

### Design Patterns

**Pattern 1: Sparse Hazards (Dungeon Dressing)**
```yaml
trap_rules:
  density: 0.05                     # 5% of room tiles
  trap_table:
    - id: "spike_trap"
      weight: 2
    - id: "web_trap"
      weight: 1
  detection:
    passive_chance: 0.2
    detectable: true
```

**Pattern 2: Death Trap Gauntlet**
```yaml
trap_rules:
  density: 0.3                      # 30% of room tiles - dangerous!
  whitelist_rooms: ["boss_arena", "cursed_chamber"]  # Only in specific rooms
  trap_table:
    - id: "spike_trap"
      weight: 5
    - id: "alarm_plate"
      weight: 3
  detection:
    passive_chance: 0.05            # Hard to detect
    detectable: true
```

**Pattern 3: Hidden Passage Traps**
```yaml
trap_rules:
  density: 0.15
  trap_table:
    - id: "alarm_plate"
      weight: 1                     # Mostly alarms to protect secrets
    - id: "spike_trap"
      weight: 1
  detection:
    passive_chance: 0.1
    detectable: true
    reveal_on: ["search_action"]    # Only found by active searching
```

**Pattern 4: Undetectable Curses**
```yaml
trap_rules:
  density: 0.02
  trap_table:
    - id: "curse_trap"              # Magical trap
      weight: 1
  detection:
    passive_chance: 0.0             # Cannot be passively detected
    detectable: false               # Impossible to detect - always hidden
    reveal_on: []                   # No items can reveal it
```

### Scope: Level vs. Room

Traps can be configured at **two scopes**:

**Level Scope** (Global)
```yaml
level_overrides:
  5:
    trap_rules:                     # Applied to entire level
      density: 0.1
      trap_table: [...]
```

**Room Scope** (Per Special Room)
```yaml
level_overrides:
  5:
    special_rooms:
      - type: "armory"
        count: 1
        trap_rules:                 # Overrides level trap_rules for this room
          density: 0.25
          trap_table: [...]
```

### Acceptance Criteria

✅ **Traps spawn respecting density** - Each room tile has independent density check  
✅ **Triggers invoke effects** - Spike damages+bleeds, web slows, alarm alerts mobs  
✅ **Detection respects passive_chance** - Configurable base detection probability  
✅ **Search reveals traps** - Active search action can find hidden traps  
✅ **Disarm removes trap** - Disarming via interaction prevents triggering  
✅ **Detectable flag works** - Setting `detectable: false` makes trap always hidden  
✅ **Extensible detection model** - Future code can modify chances based on player state  

---

## Tier 2: Stairs Configuration

### What Is Stairs Configuration?

Stairs configuration controls:
- **Direction constraints**: Whether players can go up/down from a level
- **Return restrictions**: Prevent backtracking past certain depth (anti-sequence-breaking)
- **Spawn behavior**: Where mobs spawn relative to stairs entry point
- **Floor state persistence**: Automatic save/restore when returning to previous levels

### Floor State Persistence (Automatic)

When a player moves between levels using stairs:

1. **Save Current Floor**: Entity positions, health, door open/close states, trap detection states
2. **Despawn Far Mobs**: Entities >20 tiles from stairs entry are removed (prevents pre-staging)
3. **Load Saved State**: When returning to a visited floor, the saved state is restored
4. **Cap Respawns**: Track visits to prevent infinite farming

This happens **automatically** - no configuration needed!

### Full Syntax

```yaml
stairs:
  up: bool                          # Can go to previous floor (default: true)
  down: bool                        # Can go to next floor (default: true)
  restrict_return_levels: int       # Max levels can go back (0 = no restriction)
  spawn_rules:
    near_start_bias: float          # 0.0-1.0: bias for spawning near stairs
```

### Design Patterns

**Pattern 1: Open Dungeon (No Restrictions)**
```yaml
stairs:
  up: true
  down: true
  restrict_return_levels: 0
  spawn_rules: { near_start_bias: 0.5 }
```
- Players can freely move up/down
- Mobs spawn balanced (50% near stairs, 50% elsewhere)
- Classic roguelike experience

**Pattern 2: One-Way Descent (Trap/Mine)**
```yaml
stairs:
  up: false
  down: true
  restrict_return_levels: 0
```
- No return once descended
- Creates tension and consequence
- Good for "point of no return" moments

**Pattern 3: Linear Progression (Act System)**
```yaml
stairs:
  up: true
  down: true
  restrict_return_levels: 2
  spawn_rules: { near_start_bias: 0.7 }
```
- Can only backtrack up to 2 levels
- Mobs spawn mostly near stairs (70%)
- Prevents sequence-breaking, encourages forward momentum

**Pattern 4: Tight Spawn (Mini-Gauntlet)**
```yaml
stairs:
  up: true
  down: true
  restrict_return_levels: 0
  spawn_rules: { near_start_bias: 0.9 }
```
- Almost all mobs spawn near stairs
- Intense combats right at entry
- Feels dangerous and claustrophobic

### Scope: Level-wide

Stairs config applies to the **entire level**:

```yaml
level_overrides:
  13:
    stairs:                         # Applied to level 13
      up: true
      down: true
      restrict_return_levels: 1
```

### How It Works

**First Time Visiting**: Standard level generation

**Returning to Old Floor**: 
1. Floor state loaded from memory
2. Far entities despawned (anti-staging)
3. Entities restored with saved health/status
4. Doors remember if opened/closed
5. Traps remember if detected/disarmed
6. Respawn capped to prevent farming

**Return Restriction**:
- `restrict_return_levels: 2` on level 10 = can go back to level 8+ only
- Prevents skipping zones, encourages forward progression
- Can still go down to future levels freely

### Acceptance Criteria

✅ **Moving up returns to prior map** - Saved state loaded  
✅ **State preserved** - Entities, doors, traps, health restored  
✅ **Far mobs despawned** - Prevents creature pre-staging  
✅ **Re-entry caps respawns** - Prevents infinite farming  
✅ **restrict_return_levels enforced** - Cannot backtrack past limit  
✅ **Up/down constraints work** - Blocks disallowed directions  

---

## Tier 2: Connectivity Configuration

### What Is Connectivity Configuration?

Connectivity configuration controls:
- **Baseline connectivity**: MST ensures all rooms reachable with minimal connections
- **Loop creation**: Optional additional connections creating cycles/loops for alternate paths
- **Corridor styles**: How corridors are dug (straight, zigzag, curved)
- **Door placement**: Automatic door sprinkler at regular intervals

### Full Syntax

```yaml
connectivity:
  min_connectivity: str              # "mst" or "mst_plus_loops"
  loop_count: int                    # Extra loops (only with mst_plus_loops)
  corridor_style: str                # "orthogonal", "jagged", or "organic"
  door_every_n_tiles: int            # Place doors every N tiles (0 = no placement)
```

### Minimum Spanning Tree (MST)

**What It Does:**
- Computes shortest total path to connect all rooms
- Ensures every room is reachable from every other room
- Uses Kruskal's algorithm with Union-Find data structure
- Creates tree topology (no cycles initially)

**Why It Matters:**
- Efficient baseline: N-1 connections for N rooms
- Guarantees connectivity without over-connecting
- Prevents isolated room zones

### Loop Creation

**When `mst_plus_loops`**:
- Starts with MST connections
- Adds N random additional connections NOT already present
- Creates alternative paths and cycles
- Increases maze complexity and replayability

**Example**:
- 20 rooms = 19 MST edges
- `loop_count: 3` = adds 3 more edges = 22 total connections
- Creates 3 loops for alternate routing

### Corridor Styles

**Orthogonal**:
```yaml
corridor_style: "orthogonal"
```
- Straight horizontal + vertical segments
- Creates L-shaped corridors (H-then-V or V-then-H, random)
- Classic dungeon appearance
- Best for structured layouts

**Jagged**:
```yaml
corridor_style: "jagged"
```
- Random zigzag pattern
- Randomly alternates between X and Y movement
- Chaotic, unpredictable appearance
- Good for dangerous/wild dungeons

**Organic**:
```yaml
corridor_style: "organic"
```
- Smooth curves using modified Bresenham with randomness
- Winding natural appearance
- Most aesthetically pleasing
- Best for atmospheric levels

### Door Placement

**Door Sprinkler**:
```yaml
door_every_n_tiles: 8
```
- Places doors every N tiles along corridors
- 0 = no automatic placement (default)
- Useful for secured/militarized dungeons
- Works with existing door_rules configuration

**Example**:
- 40-tile corridor with `door_every_n_tiles: 8`
- Doors placed at positions 7, 15, 23, 31, 39
- Approximately 5 doors per corridor

### Design Patterns

**Pattern 1: Simple Tree (Exploration Focus)**
```yaml
connectivity:
  min_connectivity: "mst"
  corridor_style: "orthogonal"
```
- Single path between any two rooms
- Good for linear storytelling
- Clear exploration progress
- Minimal backtracking

**Pattern 2: Complex Maze (Challenge Focus)**
```yaml
connectivity:
  min_connectivity: "mst_plus_loops"
  loop_count: 5
  corridor_style: "jagged"
```
- Multiple valid paths
- High replay value
- Challenging navigation
- Chaotic atmosphere

**Pattern 3: Natural Dungeon (Immersion Focus)**
```yaml
connectivity:
  min_connectivity: "mst_plus_loops"
  loop_count: 2
  corridor_style: "organic"
```
- Balanced complexity
- Winding natural passages
- Multiple routes feel organic
- Good for atmospheric play

**Pattern 4: Fortress (Tactical Focus)**
```yaml
connectivity:
  min_connectivity: "mst"
  corridor_style: "orthogonal"
  door_every_n_tiles: 6
```
- Orderly grid-like layout
- Frequent doors = multiple choke points
- Defendable positions
- Military feel

### Algorithm Details

**MST Computation**:
1. Calculate distances between all room center pairs
2. Sort by distance (Kruskal's algorithm)
3. Use Union-Find to select non-cyclic edges
4. Result: N-1 edges connecting N rooms with minimum total distance

**Loop Addition**:
1. Identify all pairs not yet connected
2. Randomly select loop_count pairs
3. Add those as additional connections
4. Result: MST + random cycles

**Corridor Digging**:
- **Orthogonal**: 50% H-first, 50% V-first L-shaped paths
- **Jagged**: Weighted random X/Y stepping based on remaining distance
- **Organic**: Bresenham-like with 15% chance per tile to deviate

### Acceptance Criteria

✅ **Maps show loops when configured** - mst_plus_loops creates alternate paths  
✅ **MST ensures connectivity** - All rooms reachable  
✅ **Corridor styles differ** - Orthogonal/jagged/organic visibly different  
✅ **Door sprinkler respects interval** - Doors placed every N tiles  

---

## Configuration Files

### Files in the System

| File | Purpose | Mode |
|------|---------|------|
| `level_templates.yaml` | Normal gameplay overrides | Production |
| `level_templates_testing.yaml` | Testing overrides (takes precedence) | Development |
| `level_templates_examples.yaml` | Copy-paste examples | Reference |
| `level_templates_testing_*.yaml` | Variant testing configs | Development |

### Load Order

1. **Normal templates load first** (`level_templates.yaml`)
2. **If in testing mode**, testing templates load and **override** normal templates
3. **Testing mode checked** via `config.testing_config.is_testing_mode()`

### Testing Mode Override Example

```yaml
# level_templates.yaml (normal)
level_overrides:
  5:
    parameters:
      max_monsters_per_room: 3

# level_templates_testing.yaml (in testing mode)
level_overrides:
  5:
    parameters:
      max_monsters_per_room: 1  # Override: easier for testing
```

When in testing mode, level 5 will use `max_monsters_per_room: 1`.

---

## How to Use This System

### Step 1: Choose Your Level

```yaml
level_overrides:
  13:  # Pick your level (1-25)
    # Add overrides here
```

### Step 2: Decide What You Want to Control

**Option A: Just add loot**
```yaml
guaranteed_spawns:
  mode: "additional"
  items:
    - type: "healing_potion"
      count: 2
```

**Option B: Make it harder**
```yaml
parameters:
  max_monsters_per_room: 5
  max_rooms: 20
```

**Option C: Create a themed room**
```yaml
special_rooms:
  - type: "orc_warcamp"
    count: 1
    placement: "largest"
    guaranteed_spawns:
      monsters:
        - type: "orc"
          count: "4-6"
```

**Option D: All of the above**
```yaml
parameters:
  max_rooms: 18
guaranteed_spawns:
  mode: "additional"
  items:
    - type: "fireball_scroll"
      count: 1
special_rooms:
  - type: "boss_arena"
    count: 1
    placement: "largest"
    guaranteed_spawns:
      monsters:
        - type: "troll"
          count: 1
```

### Step 3: Test It

```bash
# In testing mode with --start-level flag
python3 engine.py --testing --start-level 13

# Or modify level_templates_testing.yaml and reload
```

---

## Examples

### Example 1: Tutorial Level (Safe & Generous)

```yaml
1:
  parameters:
    max_rooms: 6
    min_room_size: 5
    max_monsters_per_room: 1
  
  guaranteed_spawns:
    mode: "additional"
    items:
      - type: "healing_potion"
        count: 3
      - type: "invisibility_scroll"
        count: 1
```

**Narrative:** New players get lots of healing items and an escape option.

### Example 2: Boss Level (Epic & Challenging)

```yaml
10:
  parameters:
    max_rooms: 10
    min_room_size: 10
    max_room_size: 14
    max_monsters_per_room: 5
  
  special_rooms:
    - type: "troll_throne_room"
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
        equipment:
          - type: "sword"
            count: 1
```

**Narrative:** Boss room is big, has the troll boss, guards, and loot.

### Example 3: Slime Nest (Thematic Horror)

```yaml
3:
  parameters:
    max_rooms: 8
  
  guaranteed_spawns:
    mode: "additional"
    items:
      - type: "healing_potion"
        count: "2-3"
  
  special_rooms:
    - type: "slime_spawning_pool"
      count: 1
      placement: "largest"
      guaranteed_spawns:
        monsters:
          - type: "large_slime"
            count: 2
          - type: "slime"
            count: "5-8"
```

**Narrative:** One room is overrun with slimes; players need healing to survive.

### Example 4: Treasure Level (Reward)

```yaml
12:
  parameters:
    max_rooms: 12
    vault_count: 3  # Force 3 treasure vaults
  
  guaranteed_spawns:
    mode: "additional"
    equipment:
      - type: "sword"
        count: 2
      - type: "shield"
        count: 1
  
  special_rooms:
    - type: "armory"
      count: 1
      placement: "largest"
      guaranteed_spawns:
        equipment:
          - type: "chain_mail"
            count: 1
          - type: "sword"
            count: "1-2"
```

**Narrative:** Mid-game reward level with lots of equipment.

### Example 5: Testing All Monsters

```yaml
# In level_templates_testing.yaml
99:  # Use a test level
  guaranteed_spawns:
    mode: "replace"  # ONLY show test content
    monsters:
      - type: "orc"
        count: 3
      - type: "troll"
        count: 2
      - type: "slime"
        count: 5
      - type: "large_slime"
        count: 2
      - type: "zombie"
        count: 2
    items:
      - type: "healing_potion"
        count: 5
      - type: "fireball_scroll"
        count: 2
```

**Narrative:** Easy testing level to see all monster types.

---

## Growth Opportunities

### 1. Faction Support (FUTURE)

```yaml
# Potential future syntax
special_rooms:
  - type: "orc_encampment"
    faction: "orc_clan"
    count: 1
    guaranteed_spawns:
      monsters:
        - type: "orc"
          count: "4-6"
```

**Value:** Groups related monsters for faction interactions.

### 2. Monster Behaviors (FUTURE)

```yaml
guaranteed_spawns:
  monsters:
    - type: "orc_warrior"
      count: 2
      behavior: "aggressive"  # Could trigger different AI
    - type: "orc_shaman"
      count: 1
      behavior: "support"     # Heals allies
```

**Value:** Create tactical encounters.

### 3. Room Connections (FUTURE)

```yaml
special_rooms:
  - type: "throne_room"
    connections:
      - next_room: "guard_chamber"
        distance: 2  # Rooms nearby
```

**Value:** Design interconnected level layouts.

### 4. Loot Tables (FUTURE)

```yaml
special_rooms:
  - type: "treasure_vault"
    loot_table: "legendary_tier"  # Reference a predefined loot distribution
    guaranteed_spawns:
      items:
        - type: "*"  # Wildcard: pick from loot table
          count: "3-5"
```

**Value:** Reusable loot distributions without hardcoding.

### 5. Environmental Effects (FUTURE)

```yaml
special_rooms:
  - type: "dragon_lair"
    environment: "lava_floor"    # Damage on standing
    lighting: "dark"              # Reduced visibility
    hazards:
      - type: "fire_trap"
        count: "2-3"
```

**Value:** Create atmospheric, dangerous environments.

### 6. Boss Variants (FUTURE)

```yaml
special_rooms:
  - type: "boss_arena"
    boss_variant: "enraged"  # Different difficulty tier
    difficulty_multiplier: 1.5
```

**Value:** Adjust boss difficulty by tier/level without adding new monster types.

### 7. Quest Integration (FUTURE)

```yaml
special_rooms:
  - type: "objective_room"
    quest_objective: "retrieve_artifact"
    guaranteed_spawns:
      map_features:
        - type: "artifact_pedestal"
          count: 1
```

**Value:** Tie room generation to quest objectives.

### 8. Procedural Naming (FUTURE)

```yaml
special_rooms:
  - type: "throne_room"
    naming_template: "{faction}_throne"  # "Orc Throne", "Troll Throne", etc.
```

**Value:** Dynamically name rooms based on content.

### 9. Configuration Validation (NEAR FUTURE)

Add schema validation to catch errors at load time:
- Verify all entity types exist in `entities.yaml`
- Check for impossible spawn counts
- Validate placement strategies
- Warn about unconfigured levels

### 10. Hot Reload (FUTURE)

```bash
# Reload templates without restarting
python3 -c "from config.level_template_registry import get_level_template_registry; \
            get_level_template_registry().load_templates()"
```

**Value:** Iterate on level design faster.

---

## Implementation Checklist

### For Designers

- [ ] Read the examples above
- [ ] Copy `level_templates_examples.yaml` entry for your level
- [ ] Modify entity types to match your monsters/items
- [ ] Adjust parameters for difficulty
- [ ] Test with `--testing --start-level <N>`
- [ ] Iterate based on gameplay feel

### For Developers

- [ ] Verify entity types exist in `entities.yaml`
- [ ] Test count range parsing (`"1-5"` → 1-5)
- [ ] Verify `LevelTemplateRegistry` loads files correctly
- [ ] Test `"additional"` vs `"replace"` modes
- [ ] Validate placement strategies (`random`, `largest`, `smallest`)
- [ ] Check that special rooms spawn correctly
- [ ] Test testing mode overrides normal mode

---

## FAQ

**Q: Can I use a count less than 1?**
A: No. `count: 0` would skip the spawn. Use conditions in code if needed.

**Q: What happens if I specify an invalid entity type?**
A: The factory will log a warning and skip that spawn. No crash.

**Q: Can special rooms have different monsters than the level default?**
A: Yes! Special room guaranteed_spawns override normal room spawning entirely.

**Q: How many special rooms can one level have?**
A: Unlimited, but only rooms that fit the criteria (size, placement) are used.

**Q: Can I have a special room with NO monsters?**
A: Yes! Just don't specify monsters in its guaranteed_spawns. It becomes a themed empty room.

**Q: Does the `count` in special rooms mean room instances or entity count?**
A: Room instances. `count: 2` = 2 separate throne rooms. Entities inside each room are specified separately.

**Q: How do I reload templates without restarting?**
A: Currently, restart the game. Hot reload is a future feature.

**Q: What's the max count I can specify?**
A: Technically unlimited, but practically limited by room size and spawn algorithm.

---

## Summary

The YAML room generation system gives you **two powerful levers**:

1. **Tier 1:** Control WHAT appears on a level (monsters, items, loot)
2. **Tier 2:** Control HOW the level is generated (room sizes, themed rooms)

Together, they let you design rich, varied dungeons **without touching Python code**.

Start with Tier 1 (guarantee some loot), then graduate to Tier 2 (special rooms) as you get comfortable.

**Happy level designing!** 🎮

