# Balance System Overview

This document describes the combat and loot balancing systems in Catacombs of YARL. It covers the Effective Threat Points (ETP) encounter budgeting, banded loot distribution, and the pity system that prevents bad-luck streaks.

## Overview

The balance system has three main components:

1. **ETP (Effective Threat Points)** - Controls encounter difficulty via per-room monster budgets
2. **Banded Loot System** - Controls item availability and density per dungeon band (B1-B5)
3. **Pity System** - Safety net that guarantees critical items after unlucky streaks

All three systems work together to create a consistent difficulty curve while allowing for exciting variance.

---

## Effective Threat Points (ETP)

### What is ETP?

ETP measures monster threat level relative to player power at a given depth. Higher ETP = harder fight.

### Where ETP is Defined

- **Base ETP per monster:** `config/entities.yaml` → each monster has a `base_etp` value
- **Band budgets:** `config/etp_config.yaml` → defines per-band room budgets
- **Logic:** `balance/etp.py` → applies multipliers and computes final ETP

### ETP Modifiers

| Modifier | Description | Example |
|----------|-------------|---------|
| **Band Multiplier** | Scales ETP by depth band | B1=1.0x, B3=1.2x, B5=1.5x |
| **Elite Multiplier** | (Elite) variants get bonus ETP | +50% for elite monsters |
| **Behavior Modifiers** | Optional AI trait bonuses | +10% for "aggressive" |

### Room Budgets

Each band defines a min/max ETP budget for rooms:

| Band | Depths | Room ETP Budget |
|------|--------|-----------------|
| B1 | 1-5 | 0-60 |
| B2 | 6-10 | 20-100 |
| B3 | 11-15 | 30-150 |
| B4 | 16-20 | 40-200 |
| B5 | 21-25 | 50-300 |

### ETP Status Codes

When running `etp_sanity.py`, rooms get one of these status codes:

| Status | Meaning |
|--------|---------|
| **OK** | Within budget |
| **UNDER** | Below minimum (easy room) |
| **OVER** | Exceeds maximum (violation in normal rooms) |
| **SPIKE** | Special room that's allowed to exceed budget |
| **BOSS** | Boss/miniboss room (budget exempt) |
| **EMPTY** | No monsters |
| **EXEMPT** | Explicitly exempt from budget |

### Running ETP Sanity

```bash
# Basic run
python3 etp_sanity.py

# Strict mode (fails on violations)
python3 etp_sanity.py --strict

# Verbose output
python3 etp_sanity.py --verbose
```

---

## Room Metadata & Roles

### RoomMetadata Class

Located in `config/level_template_registry.py`:

```python
@dataclass
class RoomMetadata:
    role: str = "normal"      # Room type
    allow_spike: bool = False  # Can exceed ETP budget
    etp_exempt: bool = False   # Skip ETP checks entirely
```

### Room Roles

| Role | Description | ETP Handling | Pity |
|------|-------------|--------------|------|
| `normal` | Standard room | Must stay within budget | ✓ Active |
| `miniboss` | Contains miniboss | Can exceed budget | ✗ Skipped |
| `boss` | Contains boss | Can exceed budget | ✗ Skipped |
| `end_boss` | Final boss room | Can exceed budget | ✗ Skipped |
| `treasure` | Vault/treasure room | Can spike (allow_spike=True) | ✗ Skipped |
| `optional` | Side content | Normal budget | ✓ Active |

### Effects on Systems

Room metadata affects:

1. **ETP Budgeting:** Boss/treasure rooms can exceed budgets
2. **Monster Spawning:** Minibosses/bosses only spawn in appropriate rooms
3. **Pity System:** Special rooms skip pity entirely (they're meant to be swingy)

---

## Loot System

### Loot Tags

Located in `balance/loot_tags.py`, each item has:

```python
@dataclass
class LootTags:
    categories: List[str]  # e.g., ["healing"], ["panic", "utility"]
    band_min: int          # Minimum band (1-5) where item appears
    band_max: int          # Maximum band (1-5) where item appears
    weight: float          # Base spawn weight
```

### Item Categories

| Category | Description | Examples |
|----------|-------------|----------|
| `healing` | HP restoration | healing_potion, regeneration_potion |
| `panic` | Emergency escape | teleport_scroll, haste_scroll, blink_scroll |
| `offensive` | Direct damage | fireball_scroll, lightning_scroll, wands |
| `defensive` | Protection/buffs | shield_scroll, protection_potion |
| `utility` | Tactical/situational | confusion_scroll, identify_scroll |
| `upgrade_weapon` | Weapon improvements | enhance_weapon_scroll, swords |
| `upgrade_armor` | Armor improvements | enhance_armor_scroll, armor pieces |
| `rare` | Valuable items | All rings |
| `key` | Progression keys | bronze_key, silver_key, gold_key |

### Band Multipliers

Three multipliers control loot distribution by band:

```python
# Item density (items per room)
BAND_ITEM_DENSITY_MULTIPLIER = {
    1: 0.35,  # B1: ~35% of normal
    2: 0.45,  # B2: ~45% of normal
    3: 1.0,   # B3-B5: baseline
    4: 1.0,
    5: 1.0,
}

# Healing spawn weight
HEALING_BAND_MULTIPLIER = {
    1: 0.25,  # B1: 25% of normal
    2: 0.35,  # B2: 35% of normal
    3: 1.0,
    4: 1.1,   # Slightly more healing for harder content
    5: 1.1,
}

# Rare item (rings) spawn weight
RARE_BAND_MULTIPLIER = {
    1: 0.05,  # B1: almost no rings
    2: 0.15,  # B2: very few rings
    3: 0.5,   # B3: some rings
    4: 0.8,
    5: 1.0,   # B5: full ring rates
}
```

### How Spawning Works

In `map_objects/game_map.py`'s `place_entities()`:

1. Calculate `max_items_per_room` from config
2. Apply `BAND_ITEM_DENSITY_MULTIPLIER` to scale down early bands
3. Build `item_chances` dict with weights from loot tags
4. Apply `HEALING_BAND_MULTIPLIER` and `RARE_BAND_MULTIPLIER` to category weights
5. Spawn items using weighted random selection
6. Run pity check after spawning

---

## Pity System

### Purpose

The pity system ensures players don't go too long without receiving critical items. It acts as a safety net—it should rarely trigger if base spawn rates are healthy.

### PityState Tracking

Located in `balance/pity.py`:

```python
@dataclass
class PityState:
    rooms_since_healing_drop: int = 0
    rooms_since_panic_item: int = 0
    rooms_since_weapon_upgrade: int = 0
    rooms_since_armor_upgrade: int = 0
```

### Band-Based Thresholds

| Band | Healing | Panic | Weapon | Armor |
|------|---------|-------|--------|-------|
| B1 | 6 rooms | 7 rooms | 8 rooms | 8 rooms |
| B2 | 5 rooms | 6 rooms | 7 rooms | 7 rooms |
| B3+ | 4 rooms | 5 rooms | 6 rooms | 6 rooms |

When a counter exceeds the threshold, pity triggers and guarantees that item type.

### The `check_and_apply_pity()` Function

Called once per room after normal item spawning:

```python
def check_and_apply_pity(
    depth: int,
    band: int,
    room_role: str,
    room_etp_exempt: bool,
    spawned_item_ids: List[str],
    spawn_healing_item_fn: Callable,
    spawn_panic_item_fn: Callable,
    spawn_upgrade_weapon_fn: Callable,
    spawn_upgrade_armor_fn: Callable,
    room_id: str,
) -> PityResult
```

### Pity Rules

1. **Skip special rooms:** Boss, miniboss, treasure rooms don't increment counters or trigger pity
2. **At most one pity item per room:** Priority order is healing → panic → weapon → armor
3. **Counter reset:** When an item of a category spawns (naturally or via pity), that counter resets
4. **Counter increment:** When a normal room lacks a category, that counter increments

### Why One Pity Per Room?

To prevent "pity spam" where a room gets flooded with 3+ pity items. The priority order ensures survival (healing) is addressed first.

---

## Sanity Harnesses

### etp_sanity.py

Tests encounter difficulty across bands.

```bash
# Basic run
python3 etp_sanity.py

# Strict mode (fails on violations)
python3 etp_sanity.py --strict

# Specific depth
python3 etp_sanity.py --depth 15
```

**What to look for:**
- OVER violations in normal rooms = budget too low or monster too strong
- All UNDER = monsters too weak for band
- Boss/treasure rooms can exceed budgets (expected)

### loot_sanity.py

Tests item distribution and pity behavior.

```bash
# Test all bands (testing mode)
python3 loot_sanity.py --bands --runs 5

# Test actual game balance (normal mode)
python3 loot_sanity.py --bands --runs 5 --normal

# Filter to category
python3 loot_sanity.py --bands --runs 5 --category healing
```

**Output sections:**
1. **Per-Band Statistics** - Items/room, category breakdown
2. **Pity System Summary** - Trigger rates per band
3. **Potential Issues** - Automated warnings

**Interpreting pity trigger rates:**
- **5-15%** = Healthy (pity is a rare safety net)
- **0%** = Base rates generous enough pity never triggers
- **30%+** = Base rates too low; pity is doing heavy lifting
- **50%+** = Problem—pity shouldn't be main progression driver

---

## Tuning Workflow

### Step 1: Encounter Difficulty (ETP)

1. Edit `config/etp_config.yaml` to adjust band budgets
2. Edit monster `base_etp` in `config/entities.yaml`
3. Run `python3 etp_sanity.py --strict` and verify no violations

### Step 2: Item Availability (Loot Tags)

1. Edit `balance/loot_tags.py`:
   - Adjust `band_min`/`band_max` for when items appear
   - Adjust `weight` for spawn frequency
   - Tune band multipliers for density/healing/rares
2. Run `python3 loot_sanity.py --bands --normal --runs 5`
3. Check items/room targets: B1=5-8, B2=6-9, B3-B5=8-10

### Step 3: Pity Thresholds

1. Edit thresholds in `balance/pity.py`:
   - `HEALING_PITY_THRESHOLDS`
   - `PANIC_PITY_THRESHOLDS`
   - `WEAPON_PITY_THRESHOLDS`
   - `ARMOR_PITY_THRESHOLDS`
2. Run `python3 loot_sanity.py --bands --normal --runs 5`
3. Check pity trigger rates (target: 5-15%)

### Step 4: Iterate

- If pity triggers too often → increase base spawn rates
- If pity triggers too rarely → thresholds may be too generous
- Testing mode templates (depths 1-8) have heavy guaranteed spawns; test normal mode for balance

---

## Quick Reference

### Key Files

| File | Purpose |
|------|---------|
| `config/etp_config.yaml` | ETP band budgets |
| `config/entities.yaml` | Monster base_etp values |
| `balance/etp.py` | ETP calculation logic |
| `balance/loot_tags.py` | Item categories, bands, weights, multipliers |
| `balance/pity.py` | Pity thresholds and logic |
| `map_objects/game_map.py` | Spawning integration |
| `etp_sanity.py` | Encounter sanity harness |
| `loot_sanity.py` | Loot sanity harness |

### Design Intent

- **ETP** ensures encounters are appropriately challenging per band
- **Loot tags** ensure items appear when they're useful
- **Pity** ensures bad luck never softlocks progression
- **Room metadata** allows special rooms to break the rules intentionally

The systems are designed to be tweaked via config, not code. When in doubt, run the harnesses and let the numbers guide you.
