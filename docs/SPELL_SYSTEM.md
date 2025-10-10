# ✨ Spell System Documentation

**Date:** January 2025  
**Status:** ✅ Production Ready  
**Version:** v3.6.0+ (Spell Registry Complete)

---

## 📋 Overview

The spell system provides a centralized, data-driven architecture for managing and casting spells. It replaced scattered spell functions with a unified registry pattern, making it easy to add new spells and maintain existing ones.

### Key Features

- **SpellDefinition** - Declarative spell data (damage, range, effects)
- **SpellRegistry** - Central spell storage (single source of truth)
- **SpellExecutor** - Unified spell casting engine
- **SpellCatalog** - All 15 game spells
- **30-Minute Add Time** - Adding new spells takes ~30 minutes (was 2+ hours!)

---

## 🏗️ Architecture

### The Four Pillars

```
┌─────────────────┐
│ SpellDefinition │  ← Declarative spell data
└────────┬────────┘
         │
    ┌────▼────┐
    │ Catalog │  ← All spell definitions
    └────┬────┘
         │
    ┌────▼────────┐
    │   Registry  │  ← Central spell storage
    └────┬────────┘
         │
    ┌────▼────────┐
    │  Executor   │  ← Unified casting engine
    └─────────────┘
```

### Component Roles

**SpellDefinition:**
- Stores spell metadata
- No logic, just data
- Easy to read and modify

**SpellCatalog:**
- Collection of all spell definitions
- Organized by type
- Call `register_all_spells()` at startup

**SpellRegistry:**
- Central manager for spells
- Get spell by ID
- List all spells
- Single source of truth

**SpellExecutor:**
- Handles spell casting
- Routes by category (offensive/healing/utility/buff/summon)
- Generates results (damage, effects, messages)

---

## 🎯 Spell Definition

### Basic Structure

```python
from spells.spell_definition import SpellDefinition
from spells.spell_types import SpellCategory, TargetingType, DamageType

FIREBALL = SpellDefinition(
    spell_id="fireball",
    name="Fireball",
    category=SpellCategory.OFFENSIVE,
    targeting=TargetingType.AOE,
    
    # Targeting
    max_range=10,
    aoe_radius=3,
    requires_los=True,
    requires_target=True,
    
    # Damage
    damage="3d6",
    damage_type=DamageType.FIRE,
    
    # Hazard (persistent fire)
    creates_hazard=True,
    hazard_duration=3,
    hazard_damage_initial=10,
    hazard_damage_decay_rate=0.4,  # 10→6→3 damage
    
    # Messages
    cast_message="You conjure a blazing fireball!",
    success_message="The fireball explodes!",
    fail_message="There is nothing to target there.",
    no_target_message="You must select a target location!",
    
    # Item behavior
    consumable=True
)
```

### All Fields

**Identity:**
- `spell_id` (str) - Unique identifier
- `name` (str) - Display name

**Category:**
- `SpellCategory.OFFENSIVE` - Damage spells
- `SpellCategory.HEALING` - Healing spells  
- `SpellCategory.UTILITY` - Control/movement
- `SpellCategory.BUFF` - Status buffs
- `SpellCategory.SUMMON` - Summon/taunt

**Targeting:**
- `targeting` - How spell targets
- `max_range` - Maximum casting distance
- `aoe_radius` - Area of effect radius (0 = single target)
- `requires_los` - Needs line of sight?
- `requires_target` - Must target something?

**Damage:**
- `damage` (str) - Dice notation (e.g., "3d6")
- `damage_type` - Fire/Lightning/Acid/Physical

**Healing:**
- `healing` (str) - Dice notation (e.g., "2d8+2")

**Effects:**
- `effect_type` - Confusion/Slow/Shield/Invisibility
- `duration` - Effect duration in turns

**Hazards:**
- `creates_hazard` (bool) - Creates ground hazard?
- `hazard_duration` - Turns hazard lasts
- `hazard_damage_initial` - Starting damage
- `hazard_damage_decay_rate` - Damage decay per turn

**Messages:**
- `cast_message` - When spell is cast
- `success_message` - When spell succeeds
- `fail_message` - When spell fails
- `no_target_message` - When no valid target

**Item Behavior:**
- `consumable` (bool) - Item destroyed after use?

---

## 🎲 Spell Categories

### Offensive Spells

**Purpose:** Deal damage to enemies

**Examples:**
- Lightning Bolt (4d6 damage, single target)
- Fireball (3d6 damage, 3-tile radius, creates fire)
- Dragon Fart (5d8 damage, cone, creates poison gas)

**Execution:**
1. Find targets in area
2. Check FOV/LOS
3. Roll damage per target
4. Apply damage
5. Create hazards (if applicable)
6. Generate messages

---

### Healing Spells

**Purpose:** Restore HP

**Examples:**
- Heal (2d8+2 healing)

**Execution:**
1. Check caster can be healed
2. Roll healing amount
3. Apply healing
4. Generate message

---

### Utility Spells

**Purpose:** Control, movement, status effects

**Examples:**
- Confusion (5 turns, random movement)
- Teleport (instant repositioning, 10% misfire)
- Slow (skip every other turn)
- Glue (immobilize, 5 turns)
- Rage (monsters attack each other)

**Execution:**
1. Find target
2. Apply status effect
3. Generate message

---

### Buff Spells

**Purpose:** Enhance caster or allies

**Examples:**
- Shield (+4 AC, temporary)
- Invisibility (10 turns)
- Enhance Weapon (+1 damage range)
- Enhance Armor (+1 defense range)

**Execution:**
1. Target self or ally
2. Apply buff effect
3. Generate message

---

### Summon Spells

**Purpose:** Summon allies or taunt

**Examples:**
- Raise Dead (resurrect corpse as zombie)
- Yo Mama (taunt all monsters to attack target)

**Execution:**
1. Find valid location/target
2. Create entity OR apply taunt
3. Generate message

---

## 🎯 Targeting Types

### SINGLE_ENEMY

**Description:** Target one enemy  
**Range:** `max_range` tiles  
**LOS:** Required  
**Example:** Lightning Bolt

### SINGLE_ANY

**Description:** Target any entity  
**Range:** `max_range` tiles  
**LOS:** Optional  
**Example:** Yo Mama taunt

### AOE (Area of Effect)

**Description:** Target location, affect radius  
**Range:** `max_range` tiles  
**Radius:** `aoe_radius` tiles  
**LOS:** Optional  
**Example:** Fireball (3-tile radius)

### CONE

**Description:** Directional cone from caster  
**Range:** `max_range` tiles  
**Width:** Fixed (45° cone)  
**LOS:** Not required  
**Example:** Dragon Fart

### SELF

**Description:** Caster only  
**Range:** 0  
**LOS:** N/A  
**Example:** Heal, Shield, Invisibility

### LOCATION

**Description:** Target any location  
**Range:** `max_range` tiles  
**LOS:** Optional  
**Example:** Raise Dead (target corpse location)

---

## 🔧 Usage Examples

### Casting a Spell

```python
from spells import cast_spell_by_id

# Simple self-cast spell
results = cast_spell_by_id(
    "heal",
    caster=player
)

# Targeted spell
results = cast_spell_by_id(
    "lightning_bolt",
    caster=player,
    entities=entities,
    fov_map=fov_map,
    target_x=10,
    target_y=15
)

# AOE spell
results = cast_spell_by_id(
    "fireball",
    caster=player,
    entities=entities,
    fov_map=fov_map,
    game_map=game_map,
    target_x=12,
    target_y=18
)
```

### Processing Results

```python
for result in results:
    if 'message' in result:
        game.message_log.add_message(result['message'])
    
    if 'consumed' in result:
        # Spell consumed, remove scroll/wand charge
        if result['consumed']:
            inventory.remove_item(scroll)
    
    if 'dead' in result:
        # Entity died from spell
        handle_death(result['dead'], result.get('xp', 0))
    
    if 'hazard_created' in result:
        # Ground hazard created
        hazard = result['hazard_created']
        game_map.hazards.append(hazard)
```

---

## ➕ Adding a New Spell

### Step-by-Step (30 minutes)

**1. Define Spell in Catalog (5 min)**

```python
# In spells/spell_catalog.py

ICE_STORM = SpellDefinition(
    spell_id="ice_storm",
    name="Ice Storm",
    category=SpellCategory.OFFENSIVE,
    targeting=TargetingType.AOE,
    max_range=10,
    aoe_radius=4,
    requires_los=True,
    requires_target=True,
    damage="4d8",
    damage_type=DamageType.COLD,
    effect_type=EffectType.SLOW,  # Slow enemies hit
    duration=3,
    cast_message="You summon a freezing blizzard!",
    success_message="Ice shards rain down!",
    fail_message="There is nothing to target there.",
    no_target_message="You must select a target location!",
    consumable=True
)
```

**2. Register Spell (1 min)**

```python
# In spells/spell_catalog.py → register_all_spells()

def register_all_spells():
    # ... existing spells ...
    register_spell(ICE_STORM)
```

**3. Add Item Definition (10 min)**

```python
# In config/entities.yaml

ice_storm_scroll:
  char: '~'
  color: [128, 200, 255]
  name: 'Ice Storm Scroll'
  components:
    item:
      targeting: true
      targeting_message:
        text: 'Left-click target tile, or right-click to cancel.'
        color: [0, 255, 255]
      spell_id: 'ice_storm'  # Links to SpellCatalog
```

**4. Add Spawn Rates (5 min)**

```python
# In config/game_constants.py → ItemSpawnConfig

ICE_STORM_SCROLL_SPAWN = [[20, 8]]  # 20% from level 8
```

**5. Test Spell (5 min)**

```bash
# Start game
python app.py

# Spawn scroll with debug
# Cast spell
# Verify behavior
```

**Done!** New spell in ~30 minutes.

---

## 📚 All 15 Spells

### Offensive (3)

| Spell | Damage | Range | AOE | Special |
|-------|--------|-------|-----|---------|
| **Lightning Bolt** | 4d6 | 10 | Single | Instant |
| **Fireball** | 3d6 | 10 | 3 tiles | Creates fire (3 turns) |
| **Dragon Fart** | 5d8 | 6 | Cone | Creates poison gas (4 turns) |

### Healing (1)

| Spell | Healing | Range | Target |
|-------|---------|-------|--------|
| **Heal** | 2d8+2 | Self | Caster |

### Utility (4)

| Spell | Effect | Duration | Target |
|-------|--------|----------|--------|
| **Confusion** | Random movement | 10 turns | Single enemy |
| **Teleport** | Instant move | Instant | Caster (10% misfire) |
| **Slow** | Skip turns | 10 turns | Single enemy |
| **Glue** | Immobilize | 5 turns | Location AOE |
| **Rage** | Monster attacks | Instant | Cone |

### Buff (4)

| Spell | Effect | Duration | Target |
|-------|--------|----------|--------|
| **Shield** | +4 AC | 5 turns | Caster |
| **Invisibility** | Invisible | 10 turns | Caster |
| **Enhance Weapon** | +1 damage | Permanent | Equipped weapon |
| **Enhance Armor** | +1 defense | Permanent | Equipped armor |

### Summon (2)

| Spell | Effect | Target |
|-------|--------|--------|
| **Raise Dead** | Resurrect as zombie | Corpse location |
| **Yo Mama** | Taunt all monsters | Single entity |

---

## 🔥 Ground Hazards

### Persistent Fire (Fireball)

**Duration:** 3 turns  
**Damage:** 10 → 6 → 3 (linear decay)  
**Visual:** Orange → Purple → Blue (fades to floor)

**Mechanics:**
```python
initial_damage = 10
decay_rate = 0.4  # 40% reduction per turn

turn_1 = 10
turn_2 = 10 * (1 - 0.4) = 6
turn_3 = 6 * (1 - 0.4) = 3.6 ≈ 3
```

### Poison Gas (Dragon Fart)

**Duration:** 4 turns  
**Damage:** 5 → 3 → 1 → 0 (linear decay)  
**Visual:** Green → Yellow → White (fades to floor)

**Mechanics:**
- Cone shape from caster
- Affects all entities in area
- Damages each turn
- Blocks movement (optional)

---

## 🎨 Visual Effects

### Spell Animations

**Fireball:**
- Orange flash at impact
- Fire spreading animation
- Persistent fire tiles

**Lightning Bolt:**
- Blue/white flash
- Lightning bolt line
- Target impact flash

**Dragon Fart:**
- Green cone emanating from caster
- Gas cloud spreading
- Persistent gas tiles

**Teleport:**
- Flash at old location
- Flash at new location
- Particle trail

---

## 🐛 Common Issues & Solutions

### "Spell does nothing when cast"

**Problem:** Spell not registered  
**Solution:** Call `register_all_spells()` at startup

### "Spell ID not found"

**Problem:** Item uses wrong spell_id  
**Solution:** Check `spell_id` matches SpellDefinition.spell_id

### "Spell hits caster/allies"

**Problem:** Wrong targeting type  
**Solution:** Use `SINGLE_ENEMY` not `SINGLE_ANY`

### "AOE damage too low"

**Problem:** Damage divided by targets (was intended?)  
**Solution:** Check `_cast_offensive_spell()` damage calculation

### "Hazard never disappears"

**Problem:** Duration not decrementing  
**Solution:** Check `process_hazards()` in turn manager

---

## 🔮 Future Enhancements

### Planned Features

- **Spell Levels:** Multiple power levels per spell
- **Spell Combos:** Combine spells for bonus effects
- **Counterspells:** Negate enemy spells
- **Spell Schools:** Fire/Ice/Lightning specialization
- **Metamagic:** Modify spell properties (extend duration, increase range)

### Possible Additions

- **Spell Failure:** Chance to fizzle based on stats
- **Spell Slots:** Limited casts per rest
- **Concentration:** Maintain spell with focus
- **Ritual Spells:** Long cast time, powerful effects
- **Channeled Spells:** Multi-turn casting

---

## 📊 Spell Balance

### Design Philosophy

**Offensive Spells:**
- Single target: High damage (4d6 = 14 avg)
- AOE: Medium damage (3d6 = 10.5 avg)
- Hazards: Low initial damage but persistent

**Healing Spells:**
- Heal ~50% of early-game HP (2d8+2 = 11 avg)
- Later outpaced by damage scaling

**Utility Spells:**
- Short duration (5-10 turns)
- Single target or small AOE
- Disruptive but not overpowered

**Buff Spells:**
- Moderate bonuses (+4 AC, not +10)
- Temporary (5-10 turns)
- Permanent buffs are small (+1)

---

## 📚 Related Files

### Core Spell Files
- `spells/__init__.py` - Public API
- `spells/spell_definition.py` - SpellDefinition class
- `spells/spell_registry.py` - SpellRegistry class
- `spells/spell_executor.py` - SpellExecutor class
- `spells/spell_catalog.py` - All spell definitions
- `spells/spell_types.py` - Enums (Category, Targeting, etc.)

### Integration Files
- `item_functions.py` - Legacy spell functions (deprecated)
- `config/entities.yaml` - Item definitions
- `components/ground_hazard.py` - Ground hazard system
- `components/status_effects.py` - Status effect integration

### Documentation
- `docs/SPELL_REGISTRY_DESIGN.md` - Original design doc
- `docs/SPELL_MIGRATION_COMPLETE.md` - Migration summary
- `docs/SPELL_REGISTRY_PROGRESS.md` - Implementation progress

---

## 🎓 Quick Reference

### Casting Flow

```
1. Get spell from registry
2. Validate parameters
3. Route by category (offensive/healing/etc.)
4. Execute spell logic
5. Return results (damage, messages, effects)
```

### Registry Functions

```python
from spells import (
    cast_spell_by_id,    # Main casting function
    get_spell_registry,  # Get registry instance
    get_spell_executor,  # Get executor instance
    register_spell,      # Register new spell
    get_spell,           # Get spell by ID
)
```

### Common Patterns

```python
# Self-cast heal
results = cast_spell_by_id("heal", caster)

# Targeted damage
results = cast_spell_by_id(
    "lightning_bolt", caster,
    entities=entities, fov_map=fov_map,
    target_x=x, target_y=y
)

# AOE spell
results = cast_spell_by_id(
    "fireball", caster,
    entities=entities, fov_map=fov_map, game_map=game_map,
    target_x=x, target_y=y
)
```

---

**Last Updated:** January 2025  
**Maintainer:** Development Team  
**Status:** Production Ready ✅  
**Spells:** 15/15 Migrated to Registry

