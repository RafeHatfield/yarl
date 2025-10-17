# Ring System Implementation Plan 💍

## 🎯 **Goals**
1. **2 Ring Slots** - Left hand and right hand ring slots
2. **12+ Ring Types** - Variety of passive effects
3. **Passive Effects** - Rings provide continuous bonuses
4. **Equipment Integration** - Seamless integration with existing equipment system
5. **Identification** - Rings start unidentified (like potions)

---

## 📊 **Ring Types** (15 Total)

### **Defensive Rings** (3)
1. **Ring of Protection** - +2 AC
2. **Ring of Regeneration** - Heal 1 HP every 5 turns
3. **Ring of Resistance** - +10% to all resistances

### **Offensive Rings** (3)
4. **Ring of Strength** - +2 STR (more damage)
5. **Ring of Dexterity** - +2 DEX (more accuracy, AC)
6. **Ring of Might** - +1d4 damage to all attacks

### **Utility Rings** (4)
7. **Ring of Teleportation** - 20% chance to teleport when hit
8. **Ring of Invisibility** - Start each level invisible for 5 turns
9. **Ring of Searching** - Reveal traps and secret doors within 3 tiles
10. **Ring of Free Action** - Immune to paralysis and slow

### **Magic Rings** (3)
11. **Ring of Wizardry** - All scrolls/wands get +1 duration/damage
12. **Ring of Clarity** - Immune to confusion
13. **Ring of Speed** - Permanent +10% movement speed

### **Special Rings** (2)
14. **Ring of Constitution** - +2 CON (+20 max HP)
15. **Ring of Hunger** - Cursed! Food drains 2x faster (when hunger implemented)

---

## 🏗️ **Implementation Phases**

### **Phase 1: Equipment Slots** (30m)
**Files:** `components/equipment.py`, `entities.yaml`

**Tasks:**
- [ ] Add `left_ring` and `right_ring` slots to Equipment component
- [ ] Update `toggle_equip()` to handle rings
- [ ] Update equipment serialization for save/load

### **Phase 2: Ring Component** (30m)
**Files:** `components/ring.py` (NEW)

**Tasks:**
- [ ] Create `Ring` component class
- [ ] Add ring effect types enum
- [ ] Implement passive effect application
- [ ] Add effect strength/duration fields

### **Phase 3: Ring Definitions** (30m)
**Files:** `config/entities.yaml`, `config/game_constants.py`

**Tasks:**
- [ ] Define all 15 ring types in YAML
- [ ] Set ring appearances for identification
- [ ] Configure spawn rates (rarity tiers)
- [ ] Add ring colors/chars

### **Phase 4: Passive Effects Integration** (1h)
**Files:** `components/fighter.py`, `components/equipment.py`, various

**Tasks:**
- [ ] Ring of Protection → AC bonus
- [ ] Ring of Strength/Dex/Con → Stat bonuses
- [ ] Ring of Regeneration → Turn-based healing
- [ ] Ring of Might → Damage bonus
- [ ] Ring of Teleportation → On-hit trigger
- [ ] Ring of Free Action → Status immunity
- [ ] Ring of Clarity → Confusion immunity
- [ ] Ring of Wizardry → Spell enhancement
- [ ] Ring of Speed → Movement bonus

### **Phase 5: UI Integration** (30m)
**Files:** `ui/sidebar.py`, `ui/tooltip.py`, `menus.py`

**Tasks:**
- [ ] Display ring slots in sidebar
- [ ] Show ring effects in character screen
- [ ] Add ring tooltips
- [ ] Update inventory display

### **Phase 6: Identification System** (30m)
**Files:** `config/item_appearances.py`, `loader_functions/initialize_new_game.py`

**Tasks:**
- [ ] Add ring appearances (metal types, gem colors)
- [ ] Integrate with existing identification system
- [ ] Initialize ring types in appearance generator

---

## 🎨 **Ring Appearances** (Unidentified)

**Metal Types:**
- Gold ring
- Silver ring
- Bronze ring
- Iron ring
- Platinum ring

**Gem Colors:**
- Ruby ring (red)
- Sapphire ring (blue)
- Emerald ring (green)
- Diamond ring (white)
- Obsidian ring (black)

**Special:**
- Twisted ring
- Engraved ring
- Ancient ring
- Glowing ring
- Plain ring

---

## 💻 **Technical Details**

### **Ring Component Structure:**
```python
class Ring:
    """Component for ring items with passive effects."""
    
    def __init__(self, ring_type: str, effect_strength: int = 0):
        self.ring_type = ring_type  # "protection", "strength", etc.
        self.effect_strength = effect_strength
        self.owner = None
    
    def apply_passive_effects(self, wearer):
        """Apply continuous passive effects to wearer."""
        # Called each turn or when relevant
        pass
```

### **Equipment Slot Changes:**
```python
class Equipment:
    def __init__(self):
        # ... existing slots ...
        self.left_ring = None   # NEW
        self.right_ring = None  # NEW
```

### **Ring Integration Points:**
- **AC Calculation** → Ring of Protection adds to armor_class property
- **Stat Bonuses** → Ring of Str/Dex/Con modify get_stat() methods
- **Damage Calculation** → Ring of Might adds to attack damage
- **Turn Processing** → Ring of Regeneration heals each turn
- **On-Hit Triggers** → Ring of Teleportation activates when damaged
- **Status Immunity** → Ring of Free Action/Clarity prevents effects

---

## 📋 **Implementation Checklist**

### Phase 1: Equipment Slots (30m)
- [ ] Add left_ring and right_ring to Equipment.__init__()
- [ ] Update Equipment.toggle_equip() for ring slot selection
- [ ] Add ring slot checks to unequip logic
- [ ] Update save/load serialization
- [ ] Test equipping/unequipping rings

### Phase 2: Ring Component (30m)
- [ ] Create components/ring.py
- [ ] Define Ring class with ring_type and effect_strength
- [ ] Add RingType enum for different ring effects
- [ ] Implement apply_passive_effects() method
- [ ] Register Ring component type

### Phase 3: Ring Definitions (30m)
- [ ] Add rings section to entities.yaml
- [ ] Define all 15 ring types with stats
- [ ] Add ring spawn rates to game_constants.py
- [ ] Configure rarity tiers (common/uncommon/rare/legendary)
- [ ] Set ring characters and colors

### Phase 4: Passive Effects (1h)
- [ ] Integrate Ring of Protection with armor_class
- [ ] Add stat bonuses for Str/Dex/Con rings
- [ ] Implement turn-based regeneration
- [ ] Add damage bonus for Ring of Might
- [ ] Implement teleportation trigger
- [ ] Add status immunities
- [ ] Implement spell enhancement
- [ ] Test all passive effects

### Phase 5: UI Integration (30m)
- [ ] Update sidebar to show ring slots
- [ ] Add ring display to character screen
- [ ] Update tooltips to show ring effects
- [ ] Show equipped rings in inventory
- [ ] Test UI display

### Phase 6: Identification (30m)
- [ ] Add RING_APPEARANCES list
- [ ] Update appearance_gen.initialize() with ring types
- [ ] Test identification system
- [ ] Verify all rings start unidentified

---

## 🎯 **Total Time Estimate: 3-4 hours**

## 🎁 **Depth Score Impact**

**Build Diversity: 5 → 7** (+2 points)
**Overall: 40/64 → 42/64** (+2 points, 63% → 66%)

---

## 🧪 **Testing Scenarios**

1. **Basic Equipping:**
   - Find ring → Equip to left hand → See effects apply
   - Find second ring → Equip to right hand → Both effects stack
   - Unequip ring → Effects disappear

2. **Stat Bonuses:**
   - Ring of Strength → Damage increases
   - Ring of Dexterity → AC and to-hit increase
   - Ring of Constitution → Max HP increases

3. **Special Effects:**
   - Ring of Regeneration → Heal each turn
   - Ring of Teleportation → Teleport when hit
   - Ring of Free Action → Can't be paralyzed

4. **Identification:**
   - Find "gold ring" → Use identify scroll → Revealed as "Ring of Protection"
   - Multiple "silver rings" → Identify one → All silver rings identified

5. **Save/Load:**
   - Equip rings → Save game → Load game → Rings still equipped with effects

---

**Ready to implement!** 💍✨
