# 🎮 YAML Systems - Complete Coverage Guide

**Date:** November 2025  
**Status:** ✅ Fully Documented  
**Version:** v4.0 (Complete)

---

## 📋 Overview

Yarl uses **YAML configuration** extensively for game balance, level design, entity definitions, and story content. This guide covers **ALL YAML systems** in the game.

### YAML Systems in Yarl

| System | File | Purpose | Documentation |
|--------|------|---------|-----------------|
| **Game Constants** | `config/game_constants.yaml` | Balance tuning | This guide |
| **Level Templates** | `config/level_templates.yaml` | Dungeon generation | `YAML_ROOM_GENERATION_*` |
| **Entity Definitions** | `config/entities.yaml` | Monster/item stats | This guide |
| **Signpost Messages** | `config/signpost_messages.yaml` | Environmental lore | This guide |
| **Murals & Inscriptions** | `config/murals_inscriptions.yaml` | Story elements | This guide |
| **Entity Dialogue** | `config/entity_dialogue.yaml` | NPC dialogue | This guide |
| **Endings** | `config/endings.yaml` | Victory messages | This guide |
| **Vault Themes** | `config/vault_themes.yaml` | Treasure room themes | This guide |

### Benefits of YAML Configuration

- **🎯 Easy Balance Tuning:** Adjust values without code changes
- **🔧 Modding Support:** Players can customize game content
- **📊 Version Control:** Track changes in git history
- **🚀 Hot Reload:** Restart game to apply new values
- **💾 Human Readable:** Easy to read and edit
- **🎨 Creative Control:** Non-programmers can design content

---

## 📁 All YAML Files & Purposes

### Configuration Files (Primary - Edit These)

- **`config/game_constants.yaml`** - Game balance values
- **`config/level_templates.yaml`** - Level generation overrides
- **`config/entities.yaml`** - Monster/item/equipment definitions
- **`config/signpost_messages.yaml`** - Signpost lore
- **`config/murals_inscriptions.yaml`** - Mural descriptions
- **`config/entity_dialogue.yaml`** - NPC and entity dialogue
- **`config/endings.yaml`** - Victory/defeat messages
- **`config/vault_themes.yaml`** - Treasure room configurations

### Testing Files (Testing Mode - Override Production)

- **`config/level_templates_testing.yaml`** - Testing level overrides
- **`config/level_templates_testing_full.yaml`** - Full test suite
- **`config/level_templates_testing_bosses.yaml`** - Boss testing
- **`config/level_templates_testing_lootdrops.yaml`** - Loot testing
- **`config/level_templates_testing_slimes.yaml`** - Slime testing

### Reference Files (Read-Only - Copy Templates From Here)

- **`config/level_templates_examples.yaml`** - Example level configs
- **`config/examples/performance_config.yaml`** - Performance tuning reference

### How YAML Loading Works

1. **Startup:** System scans for YAML files in `config/`
2. **Priority:** Testing files override production files if present
3. **Fallback:** Missing values use hardcoded defaults
4. **Logging:** System logs which files were loaded
5. **Validation:** Some systems validate YAML before accepting

---

## 🎯 Configuration Sections

The YAML file contains 6 main sections:

### 1. Combat Configuration
```yaml
combat:
  DEFAULT_DEFENSE: 0        # Starting defense
  DEFAULT_HP: 1             # Starting HP
  DEFAULT_POWER: 1          # Starting power
  DEFAULT_XP: 0             # Starting XP
  MIN_DAMAGE: 0             # Minimum damage dealt
  DEFAULT_LEVEL_UP_BASE: 200    # XP for level 2
  DEFAULT_LEVEL_UP_FACTOR: 150  # Additional XP per level
```

### 2. Gameplay Configuration
```yaml
gameplay:
  DEFAULT_MAP_WIDTH: 120        # Map width in tiles
  DEFAULT_MAP_HEIGHT: 80        # Map height in tiles
  MAX_ROOMS_PER_FLOOR: 30       # Maximum rooms
  MAX_ROOM_SIZE: 10             # Maximum room dimension
  MIN_ROOM_SIZE: 6              # Minimum room dimension
  MAX_MONSTERS_PER_ROOM: 3      # Monster cap per room
  MAX_ITEMS_PER_ROOM: 2         # Item cap per room
```

### 3. Inventory Configuration
```yaml
inventory:
  DEFAULT_INVENTORY_CAPACITY: 20  # Max items in inventory
  MAX_ITEM_NAME_LENGTH: 50        # Max item name chars
```

### 4. Pathfinding Configuration
```yaml
pathfinding:
  DIAGONAL_MOVE_COST: 1.41           # Diagonal movement cost
  MAX_PATH_LENGTH_IN_FOV: 40         # Max path when visible
  MAX_PATH_LENGTH_OUT_FOV: 25        # Max path when not visible
  MAX_PATH_LENGTH_EXPLORED: 150      # Max path for explored areas
  MAX_COORDINATE: 9999               # Max valid coordinate
```

### 5. Performance Configuration
```yaml
performance:
  SPATIAL_GRID_SIZE: 8          # Grid cell size for indexing
  FOV_CACHE_SIZE: 100           # Max cached FOV results
  TARGET_FPS: 60                # Target frame rate
  MAX_DIRTY_RECTANGLES: 50      # Before full redraw
```

### 6. Rendering Configuration
```yaml
rendering:
  DEFAULT_SCREEN_WIDTH: 80          # Console width
  DEFAULT_SCREEN_HEIGHT: 50         # Console height
  DEFAULT_PANEL_HEIGHT: 7           # Message panel height
  DEFAULT_BAR_WIDTH: 20             # HP/XP bar width
  DEFAULT_FOV_RADIUS: 10            # Field of view radius
  DEFAULT_FOV_LIGHT_WALLS: true     # Light walls in FOV
  DEFAULT_FOV_ALGORITHM: 0          # FOV algorithm (0 = basic)
  DEFAULT_MESSAGE_LOG_HEIGHT: 5     # Message log lines
  DEFAULT_MESSAGE_LOG_WIDTH: 40     # Message log width
```

---

## ✏️ Editing Constants

### Step 1: Locate the File
```bash
cd /path/to/rlike
open config/game_constants.yaml  # macOS
# or
nano config/game_constants.yaml  # Linux/Terminal
```

### Step 2: Edit Values
```yaml
# Example: Make the game easier
combat:
  DEFAULT_HP: 50  # Start with more HP (was 1)
  MIN_DAMAGE: 1   # Always deal some damage (was 0)

gameplay:
  MAX_MONSTERS_PER_ROOM: 2  # Fewer monsters (was 3)
  MAX_ITEMS_PER_ROOM: 3     # More items (was 2)
```

### Step 3: Test Changes
1. Save the file
2. Restart the game
3. Check the logs to confirm loading
4. Play and verify balance

---

## 🔧 Advanced Usage

### Exporting Current Values

```python
from config.game_constants import GAME_CONSTANTS

# Export to YAML
GAME_CONSTANTS.save_to_file('my_config.yaml', format='yaml')

# Export to JSON
GAME_CONSTANTS.save_to_file('my_config.json', format='json')
```

### Loading Custom Config

```python
from config.game_constants import GameConstants

# Load custom config
custom_constants = GameConstants.load_from_file('my_config.yaml')
```

### Accessing Values in Code

```python
from config.game_constants import (
    get_combat_config,
    get_gameplay_config,
    get_pathfinding_config
)

# Get config sections
combat = get_combat_config()
print(f"Default HP: {combat.DEFAULT_HP}")

gameplay = get_gameplay_config()
print(f"Map size: {gameplay.DEFAULT_MAP_WIDTH}x{gameplay.DEFAULT_MAP_HEIGHT}")
```

---

## 🐛 Troubleshooting

### Problem: Changes Not Applied
**Solution:** Restart the game completely. Constants are loaded at startup.

### Problem: "Failed to load game constants"
**Solution:** Check YAML syntax. Common issues:
- Incorrect indentation (use spaces, not tabs)
- Missing colons after keys
- Wrong data types (numbers as strings)

**Example - Bad YAML:**
```yaml
combat:
DEFAULT_HP: 1  # Missing indentation!
  DEFAULT_POWER: "1"  # Should be number, not string
```

**Example - Good YAML:**
```yaml
combat:
  DEFAULT_HP: 1  # Proper indentation (2 spaces)
  DEFAULT_POWER: 1  # Number, not string
```

### Problem: Game Uses Defaults
**Solution:** Check the logs:
```
INFO: Loaded game constants from config/game_constants.yaml  # ✅ Working
WARNING: Failed to load game constants ... Using defaults.   # ❌ Error
```

---

## 2️⃣ ENTITY DEFINITIONS SYSTEM (`config/entities.yaml`)

### Purpose
Defines all monsters, items, equipment, and unique entities in the game.

### Structure
```yaml
entities:
  monsters:
    orc:
      char: 'o'
      color: [63, 127, 63]
      hp: 10
      power: 3
      defense: 0
      xp: 35
  
  items:
    healing_potion:
      char: '!'
      color: [127, 0, 255]
      use_function: "heal"
      amount: 40
  
  equipment:
    sword:
      char: '/'
      power_bonus: 2
      damage_min: 1
      damage_max: 4
```

### Sections
- **monsters** - All NPC/enemy definitions
- **items** - Consumable and usable items
- **equipment** - Weapons, armor, rings
- **unique_items** - Special quest items (ruby heart, portal, etc.)

### When to Edit
- Adding new monster types
- Tweaking monster stats
- Creating new items or equipment
- Balancing item effects

---

## 3️⃣ SIGNPOST MESSAGES SYSTEM (`config/signpost_messages.yaml`)

### Purpose
Environmental lore text discovered on signposts throughout the dungeon.

### Structure
```yaml
signposts:
  tier_1:
    - "A weathered sign reads: 'Here lies the Valley of Sorrow.'"
    - "The inscription fades with age..."
  
  tier_2:
    - "You decipher: 'Two souls bound as one...'"
  
  crosscutting_lore:
    - "An ominous warning about the dragons..."
```

### Tiers
- **tier_1** - Early game discoveries
- **tier_2** - Mid-game lore
- **tier_3** - Late game revelations
- **crosscutting_lore** - Soul rotation, dragon themes

### When to Edit
- Adding environmental story clues
- Revealing backstory gradually
- Thematic reinforcement
- Player education

---

## 4️⃣ MURALS & INSCRIPTIONS SYSTEM (`config/murals_inscriptions.yaml`)

### Purpose
Detailed mural descriptions revealing deep story elements.

### Structure
```yaml
murals:
  - id: "mural_1"
    name: "The Golden Pair"
    depth: 5
    description: "Two figures stand in radiant light..."
    meaning: "The original dragon souls before the split"
  
  - id: "mural_2"
    name: "The Ritual"
    depth: 10
    description: "A dark ceremony takes place..."
    meaning: "How souls became trapped in mortal forms"
```

### Attributes
- **id** - Unique identifier
- **name** - Display title
- **depth** - When discovered (level range)
- **description** - Detailed visual description
- **meaning** - Lore significance

### When to Edit
- Adding story progression markers
- Revealing major plot points
- Creating visual narrative

---

## 5️⃣ ENTITY DIALOGUE SYSTEM (`config/entity_dialogue.yaml`)

### Purpose
NPC dialogue and responses for interactive entities.

### Structure
```yaml
entity_dialogue:
  guide:
    initial: "Welcome, traveler. I am your guide."
    curious: "You seem to understand the truth..."
    enraged: "You dare defy the dragons?!"
  
  interactions:
    attack: "The entity attacks you!"
    help: "The entity offers assistance."
```

### Progression States
- **initial** - First meeting
- **curious** - After learning lore
- **enraged** - Upon conflict

### When to Edit
- Adding NPC interactions
- Character development dialogue
- Quest-related conversations
- Dynamic responses

---

## 6️⃣ ENDINGS SYSTEM (`config/endings.yaml`)

### Purpose
Victory and defeat messages for each ending.

### Structure
```yaml
endings:
  victory_ending:
    title: "Victory"
    messages:
      - "You have reclaimed the amulet!"
      - "The dragons have been vanquished!"
  
  defeat_ending:
    title: "Defeat"
    messages:
      - "Your adventure ends here..."
```

### When to Edit
- Adding new endings
- Customizing victory messages
- Dramatic conclusion text
- Defeat scenarios

---

## 7️⃣ VAULT THEMES SYSTEM (`config/vault_themes.yaml`)

### Purpose
Themed treasure room configurations for special encounters.

### Structure
```yaml
vault_themes:
  dragon_hoard:
    description: "A hoard of dragon treasure"
    equipment_count: "3-5"
    items:
      - type: "gold_coins"
        count: "50-100"
  
  ancient_armory:
    description: "Ancient weapons and armor"
    equipment:
      - "sword"
      - "shield"
```

### When to Edit
- Creating special treasure rooms
- Thematic loot distributions
- Boss encounter rewards
- Level-specific treasures

---

## 🎯 YAML SYSTEM HIERARCHY

```
Game Startup
  ├─ Load game_constants.yaml
  │  └─ Balance values, performance, rendering
  │
  ├─ Load entities.yaml
  │  └─ Monster/item/equipment definitions
  │
  ├─ Load level_templates.yaml (or testing)
  │  └─ Dungeon generation parameters
  │
  ├─ Load signpost_messages.yaml
  │  └─ Environmental lore
  │
  ├─ Load murals_inscriptions.yaml
  │  └─ Story murals
  │
  ├─ Load entity_dialogue.yaml
  │  └─ NPC dialogue
  │
  ├─ Load endings.yaml
  │  └─ Victory/defeat messages
  │
  └─ Load vault_themes.yaml
     └─ Treasure room themes

Game Running
  ├─ Constants used throughout
  ├─ Entities spawned based on definitions
  ├─ Levels generated from templates
  └─ Content displayed from remaining systems
```

---

## 📚 Complete YAML System Map

| System | Config File | Python Loader | When Loaded | Can Hot-Reload |
|--------|-------------|----------------|------------|---|
| **Constants** | `game_constants.yaml` | `game_constants.py` | Startup | No (restart) |
| **Entities** | `entities.yaml` | `entity_registry.py` | Startup | No (restart) |
| **Levels** | `level_templates.yaml` | `level_template_registry.py` | Startup | No (restart) |
| **Signposts** | `signpost_messages.yaml` | `signpost_registry.py` | Startup | No (restart) |
| **Murals** | `murals_inscriptions.yaml` | `mural_registry.py` | Startup | No (restart) |
| **Dialogue** | `entity_dialogue.yaml` | `entity_dialogue.py` | Startup | No (restart) |
| **Endings** | `endings.yaml` | `endings.py` | Startup | No (restart) |
| **Vault Themes** | `vault_themes.yaml` | `vault_themes.py` | Startup | No (restart) |

---

## 📊 What's NOT in YAML?

Some configuration is intentionally kept in code:

- **Visual Colors:** Theme colors (in rendering code)
- **Complex Formulas:** Level-based spawn rate calculations
- **UI Layout:** Screen positioning and sizing logic
- **Algorithm Parameters:** Pathfinding tweaks, FOV calculations
- **Hardcoded Logic:** Turn economy, combat resolution

These may be moved to YAML in future versions if needed.

---

## 🎯 Common Use Cases

### Make Early Game Easier
```yaml
combat:
  DEFAULT_HP: 30            # More starting HP
gameplay:
  MAX_MONSTERS_PER_ROOM: 2  # Fewer monsters
  MAX_ITEMS_PER_ROOM: 3     # More items
```

### Larger Maps
```yaml
gameplay:
  DEFAULT_MAP_WIDTH: 150
  DEFAULT_MAP_HEIGHT: 100
  MAX_ROOMS_PER_FLOOR: 40
```

### Faster Leveling
```yaml
combat:
  DEFAULT_LEVEL_UP_BASE: 100    # Less XP needed (was 200)
  DEFAULT_LEVEL_UP_FACTOR: 75   # Less scaling (was 150)
```

### Better Performance
```yaml
performance:
  SPATIAL_GRID_SIZE: 16  # Larger grid cells
  FOV_CACHE_SIZE: 200    # More caching
  TARGET_FPS: 30         # Lower target FPS
```

---

## 🔄 Version Control

When committing balance changes:

```bash
git add config/game_constants.yaml
git commit -m "balance: Reduce early game difficulty"
git push
```

This makes balance changes:
- ✅ Trackable in git history
- ✅ Revertible if needed
- ✅ Reviewable in PRs
- ✅ Documentable in commits

---

## 📚 Related Documentation

- **`config/game_constants.py`** - Full code documentation
- **`TECH_DEBT.md`** - Implementation history
- **`config/entities.yaml`** - Monster/item definitions
- **`BALANCE_NOTES.md`** - Game balance philosophy

---

## 🎉 Summary

The YAML constants system provides:
- Easy balance tuning without code changes
- Modding support for players
- Better version control for balance
- Graceful fallback to defaults

Just edit `config/game_constants.yaml` and restart the game!

---

## 🗺️ Navigation: All YAML Documentation

This guide covers ALL YAML systems. For specific deep-dives:

| System | Main Guide | Purpose |
|--------|-----------|---------|
| **Room Generation** | `YAML_ROOM_GENERATION_SYSTEM.md` | Level design without code |
| **Room Patterns** | `YAML_ROOM_GENERATION_DESIGN_PATTERNS.md` | Advanced level design |
| **Room Quick Ref** | `YAML_ROOM_GENERATION_QUICK_REFERENCE.md` | Syntax reference |
| **All Systems** | `YAML_CONSTANTS_GUIDE.md` (this file) | Complete YAML overview |

---

## 🎓 Learning Paths

### For Game Designers
1. Read: `YAML_ROOM_GENERATION_QUICK_REFERENCE.md`
2. Design: 5+ levels in `config/level_templates.yaml`
3. Add: Lore to `config/signpost_messages.yaml`
4. Create: Murals in `config/murals_inscriptions.yaml`

### For Balance Tuners
1. Read: This guide (Game Constants section)
2. Adjust: `config/game_constants.yaml`
3. Test: `python3 engine.py` and playtest
4. Iterate: Use `--testing --start-level` flag

### For Content Creators
1. Read: Entity Definitions & Dialogue sections
2. Add: New monsters/items to `config/entities.yaml`
3. Write: Dialogue in `config/entity_dialogue.yaml`
4. Test: Restart and verify

### For Story Writers
1. Read: Signpost, Mural, Dialogue, Endings sections
2. Write: Environmental lore
3. Create: Mural descriptions and meanings
4. Polish: Ending narratives

---

## 📋 Complete YAML Configuration Checklist

- [ ] **Game Constants**
  - [ ] Balance values adjusted?
  - [ ] Performance settings optimized?
  - [ ] Rendering config correct?

- [ ] **Entities**
  - [ ] All monsters defined?
  - [ ] Items have stats?
  - [ ] Equipment balanced?

- [ ] **Levels**
  - [ ] Level progression tuned?
  - [ ] Boss levels special?
  - [ ] Difficulty curve smooth?

- [ ] **Story Content**
  - [ ] Signposts placed strategically?
  - [ ] Murals reveal lore progressively?
  - [ ] Dialogue feels natural?
  - [ ] Endings are satisfying?

- [ ] **Testing**
  - [ ] Testing files set up?
  - [ ] Quick test level available?
  - [ ] Balance tested with `--testing`?

---

## 🚀 Quick Start Template

To add a new game feature via YAML:

1. **Define the structure** in appropriate YAML file
2. **Create a registry/loader** in Python (if new system)
3. **Load at startup** in game initialization
4. **Test with** `--testing` mode
5. **Document in** this guide
6. **Commit** with descriptive message

Example commit message:
```
feat(yaml): Add enchantment system to equipment

- Add enchantments section to entities.yaml
- Create enchantment_registry.py for loading
- Integrate with equipment component
- Document in YAML_CONSTANTS_GUIDE.md
```

---

## 🔄 YAML System Workflow

```
Design in YAML
    ↓
Load at Startup
    ↓
Use in Game
    ↓
Test with --testing
    ↓
Iterate Based on Feedback
    ↓
Commit Changes
    ↓
Update Documentation
```

---

## 💾 Backup & Version Control

All YAML files should be in version control:

```bash
# View changes to configuration
git diff config/game_constants.yaml

# See history of a file
git log -p config/level_templates.yaml

# Revert a balance change
git checkout HEAD^ -- config/game_constants.yaml
```

---

## 🎯 Summary: Complete YAML Ecosystem

**Yarl's YAML configuration system provides:**

✅ **Balance Tuning** - Without code changes  
✅ **Level Design** - Structured dungeon generation  
✅ **Entity Definitions** - Monster/item stats  
✅ **Environmental Story** - Lore through signposts & murals  
✅ **Character Dialogue** - NPC interactions  
✅ **Narrative Endings** - Victory/defeat messages  
✅ **Treasure Themes** - Special room customization  

**All systems are:**
- 📖 Fully documented
- 🧪 Tested and working
- 📊 Version controlled
- 🔄 Easily modifiable
- 🎮 Ready for production

---

**Last Updated:** November 2025  
**Documentation Version:** v4.0 (Complete Coverage)  
**Status:** ✅ Production Ready  
**Maintainer:** Development Team  

---

## 📞 Need Help?

- **Level Design:** See `YAML_ROOM_GENERATION_*` guides
- **Balance Questions:** See Game Constants section above
- **Story/Content:** See Entity Dialogue, Signposts, Murals sections
- **System Integration:** See YAML System Hierarchy section

