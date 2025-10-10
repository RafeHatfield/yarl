# 🎮 YAML Constants System Guide

**Date:** January 2025  
**Status:** ✅ Implemented  
**Version:** v3.8.1

---

## 📋 Overview

The game constants system now supports loading configuration values from a YAML file, making it easy to adjust game balance without modifying code.

### Benefits

- **🎯 Easy Balance Tuning:** Adjust values without code changes
- **🔧 Modding Support:** Players can customize game constants
- **📊 Version Control:** Track balance changes in git
- **🚀 Hot Reload:** Restart game to apply new values
- **💾 Human Readable:** YAML format is easy to read and edit

---

## 📁 Files

### Configuration Files

- **`config/game_constants.yaml`** - Main configuration file (auto-loaded)
- **`config/game_constants.py`** - Code with defaults and loading logic

### How It Works

1. On startup, the system checks for `config/game_constants.yaml`
2. If found, loads values from YAML
3. If not found or error, uses hardcoded defaults
4. Logs which approach was used

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

## 📊 What's NOT in YAML?

Some configuration is intentionally kept in code:

- **Monster/Item Spawn Rates:** Complex level-based formulas (in `ItemSpawnConfig`)
- **Entity Definitions:** Monster/item stats (in `config/entities.yaml`)
- **Monster Equipment:** Equipment spawn logic (in `MonsterEquipmentConfig`)
- **Colors:** Visual theme colors (in code)

These may be added to YAML in future versions.

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

**Last Updated:** January 2025  
**Maintainer:** Development Team  
**Status:** Production Ready ✅

