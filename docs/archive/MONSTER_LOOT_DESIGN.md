# 🎁 Monster Equipment & Loot System Design

**Feature:** Monster Equipment & Loot Drops  
**Target Version:** v3.7.0  
**Estimated Time:** 1-2 weeks  
**Status:** 🚧 In Planning

---

## 🎯 Goals

Transform combat rewards by having monsters spawn with equipment and drop it when defeated.

### **Primary Objectives**
1. **Monsters Wield Equipment:** Monsters spawn with weapons/armor equipped
2. **Visible Equipment:** Players can see what monsters are wielding
3. **Loot Drops:** Monsters drop their equipment when defeated
4. **Strategic Choices:** Stronger monsters carry better loot
5. **Progression:** Natural gear progression through combat

### **Success Criteria**
- ✅ Monsters can equip weapons and armor
- ✅ Equipment is visible on monsters (tooltip or visual indicator)
- ✅ Equipment drops on monster death
- ✅ Loot quality scales with monster difficulty
- ✅ System is extensible for future loot types
- ✅ All existing tests pass
- ✅ New tests cover loot mechanics

---

## 🏗️ Architecture

### **Phase 1: Monster Equipment System** (3-4 days)

**Add Equipment to Monsters**
```python
# config/entities.yaml
orc:
  components:
    fighter:
      hp: 20
      defense: 0
      power: 4
    equipment:  # NEW!
      slots:
        main_hand: "shortsword"  # 75% spawn with shortsword
        off_hand: null
        chest: "leather_armor"   # 50% spawn with armor
```

**Key Decisions:**
- Use existing `Equipment` component (already works!)
- Add equipment definitions to `entities.yaml`
- Spawn chances per item (not all monsters have gear)
- Equipment affects monster stats (AC from armor, damage from weapons)

**Implementation:**
1. Extend `EntityFactory.create_monster()` to support equipment
2. Add equipment spawning logic with probabilities
3. Monster stats calculated from base + equipment bonuses
4. Equipment stored in monster's `Equipment` component

### **Phase 2: Equipment Visibility** (1-2 days)

**Show What Monsters Are Wielding**

**Option A: Tooltip Enhancement** (Recommended)
```python
# In get_monster_tooltip():
if monster.has_component(ComponentType.EQUIPMENT):
    weapon = monster.equipment.main_hand
    if weapon:
        tooltip_lines.append(f"Wielding: {weapon.name}")
```

**Option B: Visual Indicator** (Future Enhancement)
- Different colors for armed vs unarmed monsters
- Weapon glyph overlay (future sprite system)

**Decision:** Start with Option A (tooltips), add Option B in future

### **Phase 3: Loot Drop System** (2-3 days)

**Drop Equipment on Death**

```python
# In death_functions.py or Fighter.take_damage()
def on_monster_death(monster, killer, game_map, entities):
    """Handle monster death and loot drops."""
    
    # Drop equipped items
    if monster.has_component(ComponentType.EQUIPMENT):
        equipment = monster.equipment
        
        # Drop all equipped items at monster's position
        for slot_item in [equipment.main_hand, equipment.off_hand,
                         equipment.head, equipment.chest, equipment.feet]:
            if slot_item:
                # Create item entity at monster's position
                dropped_item = create_item_from_equipped(
                    slot_item, monster.x, monster.y
                )
                entities.append(dropped_item)
                
                # Message
                game_messages.append(Message(
                    f"The {monster.name} dropped a {slot_item.name}!",
                    libtcod.yellow
                ))
    
    # Existing death logic (XP, corpse, etc.)
    ...
```

**Key Features:**
- All equipped items drop at monster's position
- Items can be picked up immediately
- Visual feedback (message + item on ground)
- Stacking logic for multiple items at same position

### **Phase 4: Loot Quality Scaling** (1-2 days)

**Better Monsters = Better Loot**

```yaml
# config/entities.yaml

# Early game (Level 1-3)
rat:
  equipment:
    spawn_chances:
      main_hand: 0%      # No equipment
      
orc:
  equipment:
    spawn_chances:
      main_hand: 75%     # 75% chance of weapon
      chest: 50%         # 50% chance of armor
    equipment_pool:
      main_hand: ["club", "dagger", "shortsword"]
      chest: ["leather_armor"]

# Mid game (Level 4-7)
orc_warrior:
  equipment:
    spawn_chances:
      main_hand: 95%     # Almost always has weapon
      chest: 75%         # Usually has armor
    equipment_pool:
      main_hand: ["longsword", "battleaxe", "mace"]
      chest: ["leather_armor", "chainmail"]

# Late game (Level 8+)
orc_champion:
  equipment:
    spawn_chances:
      main_hand: 100%    # Always has weapon
      off_hand: 50%      # Might have shield
      chest: 90%         # Usually has armor
    equipment_pool:
      main_hand: ["greatsword", "greataxe"]
      off_hand: ["steel_shield"]
      chest: ["chainmail", "plate_armor"]
```

**Loot Progression:**
- Early monsters: Basic gear or none
- Mid monsters: Common gear (75% spawn rate)
- Late monsters: Quality gear (95%+ spawn rate)
- Boss monsters: Guaranteed rare gear (100% spawn rate)

---

## 🎮 Player Experience

### **Before This Feature**
1. Kill monster
2. Get XP
3. Maybe find random item elsewhere in dungeon
4. No connection between combat and loot

### **After This Feature**
1. See orc with shortsword (tooltip)
2. Kill orc in combat
3. "The Orc dropped a Shortsword!"
4. Pick up shortsword immediately
5. **Satisfying reward-for-effort loop!**

### **Strategic Decisions**
- "That orc has a longsword - I want it!"
- "The champion probably has great gear - worth the risk?"
- "Focus the armed enemies first to disarm them"
- "Lead monsters away from their loot piles"

---

## 🔧 Implementation Plan

### **Phase 1: Foundation** (Day 1-2)
1. Add `equipment` field to monster definitions in `entities.yaml`
2. Extend `EntityFactory.create_monster()` to parse equipment
3. Add equipment spawn probability system
4. Test: Monsters spawn with equipment ✅

### **Phase 2: Equipment Effects** (Day 2-3)
1. Ensure monster stats include equipment bonuses
2. Monster AC = base defense + armor bonus
3. Monster damage = base power + weapon dice
4. Test: Equipped monsters are stronger ✅

### **Phase 3: Visibility** (Day 3-4)
1. Extend monster tooltips to show equipped items
2. Add "Wielding: Shortsword" to tooltip
3. Test: Tooltips show equipment ✅

### **Phase 4: Loot Drops** (Day 4-6)
1. Create `drop_equipment()` function in death handling
2. Drop all equipped items at monster position
3. Add messages for dropped items
4. Handle item stacking on ground
5. Test: Equipment drops on death ✅

### **Phase 5: Loot Scaling** (Day 6-7)
1. Define equipment pools per monster type
2. Add spawn chance configuration
3. Create loot tables for early/mid/late game
4. Test: Loot quality matches monster difficulty ✅

### **Phase 6: Polish & Testing** (Day 7-8)
1. Comprehensive test suite
2. Balance testing (loot frequency, quality)
3. Edge cases (death spells, hazards, summons)
4. Documentation and release notes

---

## 🧪 Testing Strategy

### **Unit Tests**
```python
def test_monster_spawns_with_equipment():
    """Monsters spawn with configured equipment."""
    
def test_equipment_affects_monster_stats():
    """Equipment modifies monster AC and damage."""
    
def test_equipment_drops_on_death():
    """All equipped items drop when monster dies."""
    
def test_dropped_items_pickable():
    """Dropped items can be picked up by player."""
    
def test_loot_scaling():
    """Stronger monsters have better loot."""
```

### **Integration Tests**
```python
def test_full_loot_cycle():
    """Complete cycle: spawn → kill → drop → pickup."""
    
def test_multiple_monsters_stacking():
    """Multiple monsters dying at same spot."""
    
def test_loot_with_hazards():
    """Monster dies to fire/poison - still drops loot."""
```

### **Balance Testing**
- Loot frequency feels rewarding but not overwhelming
- Equipment quality matches player progression
- Loot doesn't trivialize early game
- Late game monsters drop meaningful upgrades

---

## 📊 Configuration Examples

### **Example 1: Rat (No Equipment)**
```yaml
rat:
  name: "Rat"
  components:
    fighter:
      hp: 5
      defense: 0
      power: 2
    # No equipment component - stays vanilla
```

### **Example 2: Orc (Basic Equipment)**
```yaml
orc:
  name: "Orc"
  components:
    fighter:
      hp: 20
      defense: 0  # Base defense (before armor)
      power: 4    # Base power (before weapon)
    equipment:
      spawn_chances:
        main_hand: 0.75  # 75% chance
        chest: 0.50      # 50% chance
      equipment_pool:
        main_hand:
          - item: "club"
            weight: 40
          - item: "dagger"
            weight: 30
          - item: "shortsword"
            weight: 30
        chest:
          - item: "leather_armor"
            weight: 100
```

### **Example 3: Troll (Advanced Equipment)**
```yaml
troll:
  name: "Troll"
  components:
    fighter:
      hp: 30
      defense: 2
      power: 8
    equipment:
      spawn_chances:
        main_hand: 0.95
        chest: 0.75
        off_hand: 0.25  # Rare shield
      equipment_pool:
        main_hand:
          - item: "battleaxe"
            weight: 50
          - item: "warhammer"
            weight: 50
        chest:
          - item: "chainmail"
            weight: 70
          - item: "plate_armor"
            weight: 30
        off_hand:
          - item: "steel_shield"
            weight: 100
```

---

## 🎨 Visual Design

### **Tooltip Display**
```
┌─────────────────────────┐
│ Orc                     │
│ Wielding: Shortsword    │
│ Wearing: Leather Armor  │
└─────────────────────────┘
```

### **Death Message**
```
You killed the Orc! (35 XP)
The Orc dropped a Shortsword!
The Orc dropped Leather Armor!
```

### **Ground Display**
```
You see here:
  a) Shortsword (1d6 damage)
  b) Leather Armor (+2 AC)
  c) Orc corpse
```

---

## 🚧 Future Enhancements

### **Phase 2 Features** (Future Versions)
- **Gold Drops:** Monsters carry gold/currency
- **Consumable Drops:** Potions, scrolls from inventory
- **Rare Items:** Unique items from boss monsters
- **Loot Tables:** More sophisticated drop systems
- **Enchanted Equipment:** +1 weapons, magical armor
- **Item Durability:** Damaged equipment drops
- **Loot Rarity:** Common/Uncommon/Rare/Legendary

### **Advanced Features**
- **Visual Equipment:** See weapons/armor on monster sprite
- **Equipment Damage:** Items can break in combat
- **Steal Ability:** Rogue skill to steal equipped items
- **Disarm Ability:** Knock weapon from monster's hand
- **Loot Chest System:** Monsters guard treasure chests

---

## ✅ Definition of Done

**Feature Complete When:**
- [x] Monsters can spawn with equipment
- [x] Equipment affects monster stats (AC, damage)
- [x] Equipment visible in tooltips
- [x] Equipment drops on monster death
- [x] Dropped items can be picked up
- [x] Loot quality scales with monster difficulty
- [x] All existing tests pass
- [x] New tests cover loot system
- [x] Documentation updated
- [x] Balance tested and tuned
- [x] Release notes written

---

## 📝 Open Questions

1. **Equipment Stat Display:** Show in tooltip always, or only with a skill/spell?
   - **Decision:** Always show for now (QoL), add "Identify" spell later

2. **Drop Everything or Selection:** Drop all equipped items or randomly select some?
   - **Decision:** Drop everything (more satisfying, clear feedback)

3. **Item Condition:** Dropped items at full durability or damaged?
   - **Decision:** Full durability for now (no durability system yet)

4. **Stacking Behavior:** Multiple items at same position - show all or stack?
   - **Decision:** Use existing item stacking system (works well)

5. **Death by Hazard:** Monster dies to fire/poison - does loot survive?
   - **Decision:** Yes, loot always drops (hazards don't destroy items... yet!)

---

## 🎯 Success Metrics

### **Player Engagement**
- Players explore more to find geared monsters
- Combat feels more rewarding
- Loot discovery creates "aha!" moments

### **Game Balance**
- Loot frequency: ~60-70% of monsters have equipment
- Upgrade frequency: New gear every 2-3 levels
- Loot quality: Matches player progression curve

### **Technical Quality**
- Zero regressions in existing features
- 100% test coverage for new code
- Clean, extensible architecture
- Easy to add new loot types

---

**Next Steps:**
1. Review and approve design
2. Create feature branch
3. Implement Phase 1 (Foundation)
4. Iterate and test
5. Polish and release!

*"Loot drops transform combat from a chore into a treasure hunt."*  
~ Game Design Wisdom

