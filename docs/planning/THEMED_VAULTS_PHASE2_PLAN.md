# Themed Vaults - Phase 2 Implementation Plan

**Feature:** Themed vault types with lock/key system  
**Status:** 🚧 IN PROGRESS  
**Started:** October 18, 2025  
**Branch:** `feature/themed-vaults`

---

## 🎯 Overview

Phase 2 expands on Phase 1's simple vaults by adding:
- **Key/Lock System** - Keys required to unlock vault doors
- **5 Themed Vault Types** - Each with unique loot, monsters, and visual themes
- **Vault-Specific Loot Tables** - Thematic rewards matching vault type
- **Signpost Integration** - Hints about nearby vaults
- **Visual Theming** - Unique wall colors per vault type

---

## 📦 Implementation Slices

### **Slice 1: Key System** (2-3 hours)

**Goal:** Basic key items and inventory integration

**Key Types:**
1. **Bronze Key** - Common, unlocks Library vaults
2. **Silver Key** - Uncommon, unlocks Armory vaults  
3. **Gold Key** - Rare, unlocks Treasure and Shrine vaults
4. **Dragon Scale** - Legendary, unlocks Dragon's Hoard

**Technical Requirements:**
- Add keys to `entities.yaml`
- Keys are consumable items
- Check player inventory for matching key when clicking locked door/chest
- Key consumed on successful unlock
- Message feedback ("You unlock the door with the Bronze Key")

**Files to Modify:**
- `config/entities.yaml` - Key definitions
- `config/entity_factory.py` - Key creation methods
- `components/chest.py` - Update `open()` to check for specific key type
- `mouse_movement.py` - Handle clicking locked doors
- Add key spawning to loot tables (rare drops from monsters/chests)

**Success Criteria:**
- [ ] Keys spawn in regular rooms/chests
- [ ] Keys appear in inventory
- [ ] Locked chests check for correct key type
- [ ] Keys consumed when used
- [ ] Clear feedback messages

---

### **Slice 2: Locked Doors** (2-3 hours)

**Goal:** Door entities that require keys to open

**Features:**
- Locked door entity type
- Visual distinction (different color from normal walls)
- Click interaction (check for key, unlock if present)
- Door transforms to floor tile when unlocked
- Vault rooms can have locked entrances

**Technical Requirements:**
- Add locked door entity type
- Door blocking/unblocking logic
- Key type matching (bronze door needs bronze key)
- Visual feedback for locked vs unlocked

**Files to Modify:**
- `config/entities.yaml` - Locked door definitions (by key type)
- `config/entity_factory.py` - Create locked door method
- `map_objects/game_map.py` - Place locked doors at vault entrances
- `mouse_movement.py` - Handle locked door clicks
- `components/map_feature.py` - LockedDoor component

**Success Criteria:**
- [ ] Locked doors block movement
- [ ] Doors show in distinct color
- [ ] Clicking door checks for key
- [ ] Door opens with correct key
- [ ] Auto-explore stops at locked doors

---

### **Slice 3: Vault Themes** (4-5 hours)

**Goal:** 5 distinct vault types with themed content

**Vault Types:**

**1. Treasure Vault (Gold Key)**
- **Theme:** Wealth, riches, hoarded treasure
- **Wall Color:** Bright gold `(255, 215, 0)`
- **Monsters:** Thieves, rogues, bandits, guardians
- **Loot Focus:** Gold chests, rings, jewelry, coins
- **Special:** Mimic chest (10% chance)

**2. Armory (Silver Key)**
- **Theme:** Weapons and armor cache
- **Wall Color:** Steel grey `(192, 192, 192)`
- **Monsters:** Warriors, knights, weapon masters
- **Loot Focus:** Enhanced weapons, magical armor, shields
- **Special:** Legendary weapon (5% chance)

**3. Library/Scriptorium (Bronze Key)**
- **Theme:** Knowledge, scrolls, magic
- **Wall Color:** Parchment beige `(245, 222, 179)`
- **Monsters:** Scholars, wizards, librarians, living books
- **Loot Focus:** Rare scrolls, spell books, wands
- **Special:** Scroll of Wish (1% chance)

**4. Shrine/Temple (Gold Key)**
- **Theme:** Religious, holy, healing
- **Wall Color:** Divine white `(255, 250, 250)` with gold trim
- **Monsters:** Priests, zealots, undead, guardians
- **Loot Focus:** Holy items, healing potions, protection rings
- **Special:** Altar for blessings (Phase 3)

**5. Dragon's Hoard (Dragon Scale)**
- **Theme:** Legendary treasure, highest danger
- **Wall Color:** Dark crimson `(139, 0, 0)` with gold accents
- **Monsters:** Dragon (mini-boss), dragonlings, fire elementals
- **Loot Focus:** Multiple legendary items, massive loot
- **Special:** Guaranteed 2-3 legendary items

**Technical Requirements:**
- Vault type enum/configuration
- Themed monster tables (monsters per vault type)
- Themed loot tables (items per vault type)
- Wall color per vault type
- Signpost hints referencing vault types

**Files to Modify:**
- `config/entities.yaml` - Themed monster/loot definitions
- `map_objects/game_map.py` - Vault type selection and generation
- `components/chest.py` - Themed loot tables
- New file: `config/vault_themes.yaml` - Vault configurations

**Success Criteria:**
- [ ] 5 distinct vault types generate
- [ ] Each has unique wall color
- [ ] Monsters match theme
- [ ] Loot matches theme
- [ ] Visual distinction is clear

---

### **Slice 4: Themed Loot Tables** (2-3 hours)

**Goal:** Vault-specific loot generation

**Loot Table Structure:**
```yaml
treasure_vault:
  common:
    - gold_ring: 40%
    - silver_ring: 30%
    - copper_ring: 30%
  rare:
    - ring_of_protection: 25%
    - ring_of_strength: 25%
    - ring_of_regeneration: 25%
    - ring_of_might: 25%
  legendary:
    - ring_of_invisibility: 50%
    - ring_of_wizardry: 50%

armory_vault:
  common:
    - shortsword: 25%
    - longsword: 25%
    - mace: 25%
    - shield: 25%
  rare:
    - longsword+2: 33%
    - battleaxe+2: 33%
    - plate_armor+2: 34%
  legendary:
    - greatsword+4: 50%
    - excalibur: 50%  # Phase 3
```

**Technical Requirements:**
- YAML-based loot tables per vault type
- Quality tiers per vault type
- Themed item pools
- Integration with chest generation

**Files to Modify:**
- New file: `config/vault_loot_tables.yaml`
- `components/chest.py` - Load themed tables
- `map_objects/game_map.py` - Assign vault type to chests

**Success Criteria:**
- [ ] Vault loot matches theme
- [ ] Treasure vault drops rings/jewelry
- [ ] Armory drops weapons/armor
- [ ] Library drops scrolls/wands
- [ ] Shrine drops holy items/healing
- [ ] Dragon hoard drops legendary items

---

### **Slice 5: Signpost Hints** (1-2 hours)

**Goal:** Signposts reference nearby vaults

**New Sign Messages:**
- "Through the bronze door lies ancient knowledge..."
- "The armory awaits those with the silver key."
- "Beware! A dragon guards legendary treasure beyond."
- "Only the pure may enter the golden shrine."
- "Treasures beyond measure... if you have the key."

**Technical Requirements:**
- Add vault-hint sign category
- Depth filtering (vaults appear depth 4+)
- Directional hints (optional)

**Files to Modify:**
- `config/signpost_messages.yaml` - Add vault hints
- `map_objects/game_map.py` - Place hints near vaults (optional)

**Success Criteria:**
- [ ] Vault hint messages exist
- [ ] Hints appear on appropriate depths
- [ ] Messages reference key types
- [ ] Players get subtle guidance

---

## 🎨 Visual Design

### **Vault Wall Colors**

| Vault Type | Color Name | RGB | Hex |
|------------|------------|-----|-----|
| Treasure | Bright Gold | (255, 215, 0) | #FFD700 |
| Armory | Steel Grey | (192, 192, 192) | #C0C0C0 |
| Library | Parchment | (245, 222, 179) | #F5DEB3 |
| Shrine | Divine White | (255, 250, 250) | #FFFAFA |
| Dragon | Dark Crimson | (139, 0, 0) | #8B0000 |

### **Locked Door Colors**

| Key Type | Door Color | RGB |
|----------|------------|-----|
| Bronze | Bronze | (205, 127, 50) |
| Silver | Silver | (192, 192, 192) |
| Gold | Gold | (255, 215, 0) |
| Dragon Scale | Crimson | (220, 20, 60) |

---

## 🎮 Gameplay Flow

### **Player Experience:**

1. **Exploration:** Player finds a locked door (bronze/silver/gold)
2. **Key Hunt:** Searches dungeon for matching key
3. **Decision:** Do I have the resources to tackle this vault?
4. **Unlock:** Uses key to open vault door (key consumed)
5. **Challenge:** Fights themed elite monsters
6. **Reward:** Loots themed treasure matching vault type
7. **Satisfaction:** Feels rewarded for exploration and preparation

### **Key Distribution:**

**Spawn Rates (per dungeon level):**
- **Bronze Key:** 15% chance (common)
- **Silver Key:** 10% chance (uncommon)
- **Gold Key:** 5% chance (rare)
- **Dragon Scale:** 1% chance (legendary, depth 8+ only)

**Spawn Locations:**
- Regular chests (30% of key spawns)
- Monster drops (50% of key spawns)
- Floor loot (20% of key spawns)

**Key Hints:**
- Signposts reference vault types
- Locked doors visible before you have key (creates goal)
- Auto-explore stops at locked doors

---

## ⚖️ Balance Guidelines

### **Vault Difficulty by Type:**

| Vault | Key Rarity | Monster Difficulty | Loot Quality | Depth |
|-------|------------|-------------------|--------------|-------|
| Library | Common (Bronze) | Medium (Wizards) | Scrolls/Wands | 4-6 |
| Armory | Uncommon (Silver) | High (Warriors) | Weapons/Armor | 6-8 |
| Treasure | Rare (Gold) | High (Rogues) | Rings/Jewels | 7-9 |
| Shrine | Rare (Gold) | Medium (Undead) | Holy/Healing | 6-8 |
| Dragon | Legendary (Scale) | EXTREME (Dragon) | Legendary x3 | 9+ |

### **Monster Scaling:**

**Library (Wizards):**
- 1.5x HP, +1 power, +1 defense
- Can cast spells (scroll usage AI)
- Drop scrolls/wands

**Armory (Warriors):**
- 2.0x HP, +2 power, +2 defense  
- Always equipped with weapons/armor
- Drop their equipment

**Treasure (Rogues/Thieves):**
- 1.5x HP, +2 power, +1 defense
- High dodge chance (Phase 3)
- Can steal items (Phase 3)

**Shrine (Priests/Undead):**
- 1.5x HP, +1 power, +2 defense
- Healing abilities (Phase 3)
- Holy resistance

**Dragon's Hoard (Dragon Boss):**
- 3.0x HP, +4 power, +3 defense
- Multi-phase fight (existing boss system)
- Fire breath attack
- Enrage at 50% HP

---

## 🔧 Technical Architecture

### **New Components:**

**VaultTheme Enum:**
```python
class VaultTheme(Enum):
    TREASURE = "treasure"
    ARMORY = "armory"
    LIBRARY = "library"
    SHRINE = "shrine"
    DRAGON_HOARD = "dragon_hoard"
```

**Key Component:**
```python
class Key:
    def __init__(self, key_type: str):
        self.key_type = key_type  # "bronze", "silver", "gold", "dragon_scale"
```

**LockedDoor Component:**
```python
class LockedDoor(MapFeature):
    def __init__(self, required_key: str):
        self.required_key = required_key
        self.locked = True
```

### **Vault Configuration (YAML):**

```yaml
vault_themes:
  treasure:
    name: "Treasure Vault"
    key_required: "gold_key"
    wall_color: [255, 215, 0]
    monsters:
      - thief: 40
      - rogue: 30
      - bandit: 20
      - guardian: 10
    loot_table: "treasure_vault"
    chest_count: [3, 5]
    
  armory:
    name: "Armory"
    key_required: "silver_key"
    wall_color: [192, 192, 192]
    monsters:
      - warrior: 40
      - knight: 30
      - weapon_master: 30
    loot_table: "armory_vault"
    chest_count: [2, 4]
```

---

## 📝 Implementation Order

### **Phase 2A: Foundation (4-5 hours)**
1. ✅ Create plan document (this file)
2. 🔲 Implement key items in `entities.yaml`
3. 🔲 Add key spawning logic
4. 🔲 Create LockedDoor component
5. 🔲 Implement door unlock logic

### **Phase 2B: Vault Themes (6-8 hours)**
6. 🔲 Create `vault_themes.yaml` configuration
7. 🔲 Create `vault_loot_tables.yaml`
8. 🔲 Implement vault theme selection
9. 🔲 Add themed monster tables
10. 🔲 Add themed loot generation
11. 🔲 Apply themed wall colors

### **Phase 2C: Integration (2-3 hours)**
12. 🔲 Add vault hint signpost messages
13. 🔲 Lock doors on vault generation
14. 🔲 Update auto-explore for locked doors
15. 🔲 Add testing configuration

### **Phase 2D: Testing & Balance (2-3 hours)**
16. 🔲 Test all 5 vault types
17. 🔲 Balance key spawn rates
18. 🔲 Balance vault difficulty
19. 🔲 Verify loot quality matches risk

**Total Estimated Time:** 14-19 hours

---

## ✅ Success Criteria

**Phase 2 Complete When:**
- [ ] All 5 vault types generate with unique themes
- [ ] Keys spawn and work correctly
- [ ] Locked doors require correct keys
- [ ] Vault loot matches theme (armory has weapons, etc.)
- [ ] Visual distinction clear (different wall colors)
- [ ] Balance feels fair (risk = reward)
- [ ] Signposts hint at vaults
- [ ] Auto-explore stops at locked doors
- [ ] No locked chests without key system
- [ ] Dragon's Hoard feels LEGENDARY

---

## 🔮 Phase 3 Preview

**Future Enhancements (not in Phase 2):**
- Unique artifacts (Excalibur, Mjolnir)
- Altar system in shrines (blessings, prayers)
- Trap system for vault doors
- Guardian mini-bosses (not just elite monsters)
- Vault achievements tracking
- Multi-room vault layouts
- Puzzle-locked vaults
- Cursed vaults (risk/reward)

---

## 📚 References

- Phase 1 Plan: `docs/planning/VAULT_SYSTEM_PLAN.md`
- Exploration Plan: `docs/planning/EXPLORATION_DISCOVERY_PLAN.md`
- Player Pain Points: `PLAYER_PAIN_POINTS.md`
- Traditional Roguelike Features: `TRADITIONAL_ROGUELIKE_FEATURES.md`

---

**Last Updated:** October 18, 2025  
**Next Review:** After Phase 2A completion


