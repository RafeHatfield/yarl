# Balance System Overview

This document describes how Catacombs of YARL balances combat and rewards using:

- **ETP (Effective Threat Points)** for monsters and encounters
- **Banded loot distribution** with item tags
- **Pity systems** to prevent RNG soft-locks
- **Sanity harnesses** to measure what the generator actually does

The goal is to keep the dungeon dangerous but fair, with a consistent difficulty curve and enough tools for clever players to survive.

---

## 1. Effective Threat Points (ETP)

ETP = **Effective Threat Points**. It is a single number representing how dangerous a monster is *at a given depth*, after scaling and modifiers.

### 1.1 Base ETP

- Each monster has a `etp_base` in `config/entities.yaml`.
- This is a rough measure of its combat power in a neutral context.

Example (values are illustrative):

- `slime`: 10
- `orc`: 27
- `orc_veteran`: 41
- `troll`: 50
- `troll_ancient`: 95
- `dragon_lord`: 700

### 1.2 Band scaling

The dungeon is divided into **bands** (B1–B5) based on depth:

- B1: shallow floors (early game)
- B2: early-mid
- B3: mid
- B4: mid-late
- B5: late

`balance/etp.py` applies multipliers per band to account for:

- HP scaling
- Damage scaling
- Optional behavior modifiers (e.g., aggressive AI might be more "expensive")

The function `get_monster_etp(monster_type, depth)` returns the final ETP for that monster at a specific depth.

### 1.3 Elite variants

Vault/treasure rooms can spawn **(Elite)** variants of monsters.

- `orc (Elite)` uses the `orc` base ETP.
- An **elite multiplier** is applied (e.g. 1.5x).

This keeps the configuration simple: the base monster defines the core threat, and elite status is layered on top.

### 1.4 Room & floor budgets

`config/etp_config.yaml` defines:

- **Room ETP budgets** per band (min / max)
- **Floor ETP budgets** per band (total over all rooms)

During generation:

- `map_objects/game_map.py` tracks the total ETP of monsters spawned in each room.
- When the room’s ETP reaches the budget, further spawns are prevented (for normal rooms).
- Special rooms (boss, miniboss, treasure/spike) have specific rules and may exceed budgets.

This enforces a consistent difficulty curve floor-by-floor.

### 1.5 Room metadata and ETP

Each room has a `RoomMetadata` record (built in `config/level_template_registry.py`) with fields such as:

- `role`: `"normal"`, `"miniboss"`, `"boss"`, `"end_boss"`, `"treasure"`, `"optional"`
- `allow_spike: bool` – room is allowed to exceed typical budgets
- `etp_exempt: bool` – room is completely exempt from ETP checks

`etp_sanity.py` uses this to classify rooms as:

- `OK`, `UNDER`, `OVER`
- `SPIKE` (treasure/allow_spike rooms)
- `BOSS`, `MINIBOSS`, `ENDBOSS`
- `EMPTY`

Normal rooms should stay within budget; special rooms are allowed to be spiky.

---

## 2. Loot System

Loot is driven by **tags**, **bands**, and **weights**, all defined in `balance/loot_tags.py`.

### 2.1 Item categories

Items are tagged into categories like:

- `healing` – healing potions, regeneration, etc.
- `panic` – escape/oh-shit tools (teleport, haste, invisibility, etc.)
- `offensive` – fireball/lightning scrolls, damaging wands
- `defensive` – shield/protection effects
- `utility` – glue, slow, confusion, raise dead, tricks, etc.
- `upgrade_weapon` – (better) weapons, enchant weapon scrolls
- `upgrade_armor` – armor upgrades, armor enchantment
- `rare` – rings and other rare items
- `key` – bronze/silver/gold keys

Each item knows:

- Which bands it can appear in (`band_min`/`band_max`).
- Its weight in each band.

### 2.2 Band density multipliers

To avoid manually tuning every single number endlessly, we use band-level multipliers:

- `BAND_ITEM_DENSITY_MULTIPLIER[band]` – scales **max items per room**.
- `HEALING_BAND_MULTIPLIER[band]` – scales healing weights per band.
- `RARE_BAND_MULTIPLIER[band]` – strongly suppresses rings/rares in B1–B2.

This gives us:

- Early floors: more forgiving in some ways (or more cluttered), depending on templates.
- Mid/late floors: more controlled densities, better progression of upgrades and rare items.

### 2.3 How rooms get items

In `map_objects/game_map.py`:

1. For each room, we determine:
   - The depth and band.
   - The base `max_items_per_room` for that band.
   - The adjusted `max_items` using `BAND_ITEM_DENSITY_MULTIPLIER`.

2. We build an item chance table by:
   - Asking `loot_tags` which items are valid for this band.
   - Applying band multipliers for healing/rare items.
   - Applying each item’s local weight.

3. We roll a number of items (up to `max_items`) and place them in that room.

4. After natural item spawning is done, we call the **pity system** to see if we should add a guaranteed item.

---

## 3. Pity System

The pity system is a **safety net** that gently corrects for bad RNG streaks.

It does **not** guarantee fairness in every room, but it prevents runs where the player has:

- No healing for a long time.
- No panic tools when difficulty spikes.
- No upgrades as monster ETP ramps up.

All pity logic lives in `balance/pity.py`.

### 3.1 PityState and counters

`PityState` tracks:

- `rooms_since_healing_drop`
- `rooms_since_panic_item`
- `rooms_since_weapon_upgrade`
- `rooms_since_armor_upgrade`

These are counts of **normal rooms** since the last time the relevant category dropped naturally or via pity.

`reset_pity_state()` is called when a new game starts.

### 3.2 Band-based thresholds

Each category has band-specific thresholds defining how many normal rooms can pass with no item of that type before pity triggers.

Typical defaults (subject to tuning):

- **Healing:**
  - B1: 6 rooms
  - B2: 5 rooms
  - B3+: 4 rooms

- **Panic (teleport/haste/invis/etc.):**
  - B1: 7 rooms
  - B2: 6 rooms
  - B3+: 5 rooms

- **Weapon upgrades:**
  - B1: 8 rooms
  - B2: 7 rooms
  - B3+: 6 rooms

- **Armor upgrades:**
  - (Initially the same as weapon; can diverge later.)

These are exposed via helper functions like:

- `get_healing_pity_threshold(band)`
- `get_panic_pity_threshold(band)`
- `get_weapon_pity_threshold(band)`
- `get_armor_pity_threshold(band)`


### 3.3 `check_and_apply_pity(...)`

Once per room, after normal item placement, `map_objects/game_map.py` calls:

    pity_result = check_and_apply_pity(
        depth,
        band,
        room_metadata,
        spawned_item_ids,
        spawn_healing_item_fn,
        spawn_panic_item_fn,
        spawn_upgrade_weapon_fn,
        spawn_upgrade_armor_fn,
    )

**Where:**

- `room_metadata` is the `RoomMetadata` for that room.  
- `spawned_item_ids` is the list of item IDs already placed in that room.  
- The `spawn_*` functions know how to place an item of the requested category into this room.

---

## Rules

### Room roles

If `room_metadata.role` is one of:

- `"boss"`
- `"miniboss"`
- `"end_boss"`
- `"treasure"`

or if:

- `room_metadata.etp_exempt == True`

Then:

- Pity counters are **not incremented**  
- Pity does **not trigger**

These rooms are intentionally allowed to be swingy/spiky.

---

### Counters and detection

For **normal rooms** we inspect `spawned_item_ids` and use `loot_tags` to classify items.

Categories tracked:

- `healing`
- `panic`
- `upgrade_weapon`
- `upgrade_armor`

For each category:

- If the room contains at least one item of that category → **reset** counter  
- Else → **increment** counter  

---

### Triggering pity

Pity checks occur in the following **priority order**:

1. Healing  
2. Panic  
3. Weapon upgrade  
4. Armor upgrade  

For each category, if:

- The counter exceeds its threshold, **and**  
- The room does not contain an item in that category,  

then:

- The appropriate spawn function is called  
- The counter is reset  
- Only **one** pity event fires per room

---

### Result & logging

`check_and_apply_pity` returns a small dict describing which pity event (if any) was triggered.

Debug example:

    [PITY] depth=10 band=B2 room=room_12_7 -> triggered panic pity (rooms_since_panic_item=6)

---
