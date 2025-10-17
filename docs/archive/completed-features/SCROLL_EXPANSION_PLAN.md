# Scroll Identification + Variety - Implementation Plan

## Executive Summary

**Goal:** Expand scroll system from 8 → 15+ types and add identification system (like potions)

**Expected Impact:**
- Discovery: 3/10 → 5/10 (+2)
- Resource Management: 4/10 → 5/10 (+1)
- Build Diversity: 5/10 → 6/10 (+1)
- Overall: 38/64 (59%) → 44/64 (69%) ✅ **Past Milestone 1 target!**

**Estimated Time:** 1-2 weeks
**Complexity:** Medium (leverage existing potion ID system)

---

## Current State Analysis

### Existing Scrolls (8 types)
1. **Lightning** - Area damage spell
2. **Fireball** - Area damage spell
3. **Confusion** - Status effect on target
4. **Teleportation** - Move player randomly
5. **Invisibility** - Status effect (30 turns)
6. **Raise Dead** - Summon zombie ally
7. **Magic Mapping** - Reveal entire floor
8. **Shield** - +5 AC for 20 turns

**Current Issues:**
- All scrolls always identified (no mystery)
- Limited tactical variety (mostly damage + 2 utility)
- No "Identify" scroll (can't identify other items)
- No scroll rarity tiers

---

## New Scrolls to Add (7+ new types)

### Tier 1: Essential Scrolls (3 new)

#### 1. Identify Scroll ⭐⭐⭐⭐⭐
**Priority:** #1 - This is THE meta-scroll
**Function:** Identifies one unidentified item
**Usage:** Select from inventory → item becomes identified
**Spawn Rate:** Uncommon (important but not too common)
**Why Critical:** Creates economy around identification

#### 2. Enchant Weapon Scroll
**Function:** +1 to weapon's to-hit bonus (max +3)
**Usage:** Select weapon from inventory
**Spawn Rate:** Rare
**Why Important:** Build customization, meaningful choice

#### 3. Enchant Armor Scroll
**Function:** +1 to armor's AC bonus (max +3)
**Usage:** Select armor piece from inventory
**Spawn Rate:** Rare
**Why Important:** Build customization, pairs with enchant weapon

### Tier 2: Tactical Scrolls (4 new)

#### 4. Haste Scroll
**Function:** Double movement speed for 30 turns (like Speed potion but longer)
**Usage:** Drink and move twice as fast
**Spawn Rate:** Uncommon
**Why Important:** Escape mechanism, kiting strategy

#### 5. Blink Scroll
**Function:** Short-range teleport (3-5 tiles) with targeting
**Usage:** Choose destination within range
**Spawn Rate:** Common
**Why Important:** Tactical positioning without full randomness

#### 6. Fear Scroll
**Function:** Make all visible enemies flee for 15 turns
**Usage:** Read scroll, affects all in FOV
**Spawn Rate:** Uncommon
**Why Important:** Escape option, crowd control

#### 7. Remove Curse Scroll
**Function:** Uncurse one cursed item (for when we add cursed items)
**Usage:** Select cursed item from inventory
**Spawn Rate:** Uncommon
**Why Important:** Essential for cursed item system (future)
**Note:** Implement now for future-proofing

### Tier 3: High-Power Scrolls (3 new)

#### 8. Earthquake Scroll
**Function:** Destroys walls in 3-tile radius, damages all creatures
**Usage:** Read scroll, creates rubble and damages everyone nearby
**Spawn Rate:** Rare
**Damage:** 3d6 to all creatures in range
**Why Important:** Environmental destruction, desperate escape

#### 9. Recharging Scroll
**Function:** Restore charges to wands (for when we add wands)
**Usage:** Select wand from inventory
**Spawn Rate:** Very Rare
**Why Important:** Essential for wand economy (future)
**Note:** Implement now for future-proofing

#### 10. Summon Ally Scroll
**Function:** Summon random friendly creature for 50 turns
**Usage:** Read scroll, ally appears adjacent
**Spawn Rate:** Rare
**Options:** Orc ally, Troll ally, Goblin pack (3x)
**Why Important:** Different from Raise Dead, more varied

### Bonus: Utility Scrolls (2 new)

#### 11. Light Scroll
**Function:** Permanently light up a room or large area
**Usage:** Read scroll, reveals dark areas
**Spawn Rate:** Common
**Why Important:** Exploration utility, pairs with dark levels

#### 12. Detect Monster Scroll
**Function:** Reveal all monsters on the floor for 20 turns
**Usage:** Read scroll, monsters show through walls temporarily
**Spawn Rate:** Uncommon
**Why Important:** Scouting, avoiding ambushes

**Total: 8 existing + 12 new = 20 scroll types** ✅ Exceeds 15+ goal

---

## Scroll Identification System

### Design (Mirrors Potion System)

**Unidentified Appearance:**
- Scrolls appear as "scroll labeled XYZZY" or "scroll labeled PRATYAVAYAH"
- Random labels per game (generated from word list)
- Once used/identified, all scrolls of that type are known
- Use existing `IdentificationManager` (already built!)

**Label Examples (30+ possible):**
- XYZZY (NetHack classic)
- PRATYAVAYAH (DCSS)
- ELBIB YLOH
- VE FORBRYDERNE
- ZELGO MER
- JUYED AWK YACC
- NR 9
- ANDOVA BEGARIN
- HACKEM MUCHE
- VELOX NEB
- READ ME
- FOOBIE BLETCH
- TEMOV
- GARVEN DEH
- LOREM IPSUM
- ETAOIN SHRDLU
- DUAM XNAHT
- KERNOD WEL
- ELAM EBOW
- VERR YED HORRE
- ASHPD SODALG
- YUM YUM
- DAIYEN FOOELS
- LEP GEX VEN ZEA
- PRIRUTSENIE
- ELBIB
- ZLORFIK
- GNIK SISI VLE
- GHOTI
- ABRA KA DABRA
- HOCUS POCUS

**Integration with Existing System:**
```python
# Already exists from potion system!
from config.identification_manager import get_identification_manager
from config.item_appearances import get_appearance_generator

# Just need to expand to scrolls
appearance_gen.initialize({
    'potion': [...],  # Already done
    'scroll': [...]   # Add this!
})
```

### Configuration (Use Existing System)

**Already Implemented from Potion System:**
```yaml
identification_system:
  enabled: true  # Master toggle

difficulty:
  easy:
    item_identification:
      scrolls_pre_identified: 80%  # Most scrolls known
  medium:
    item_identification:
      scrolls_pre_identified: 40%  # Common ones known
  hard:
    item_identification:
      scrolls_pre_identified: 5%   # Almost nothing known
```

**No new config needed!** Just use what we built for potions ✅

---

## Implementation Plan

### Phase 1: Add Scroll Labels (1-2 hours)
**Files to Modify:**
- `config/item_appearances.py` - Add scroll label list
- `loader_functions/initialize_new_game.py` - Register scroll types

**Tasks:**
1. Add 30+ scroll labels to appearance generator
2. Register all scroll types in `appearance_gen.initialize()`
3. Test label generation

**Validation:**
- Start new game
- Verify scroll labels are random
- Verify consistency within game
- Verify different labels on restart

### Phase 2: Implement New Scroll Functions (4-6 hours)
**Files to Modify:**
- `item_functions.py` - Add 12 new scroll functions
- `config/entities.yaml` - Define 12 new scrolls

**Priority Order:**
1. **Identify Scroll** - Most critical
2. Enchant Weapon/Armor - Core upgrades
3. Blink, Fear, Haste - Tactical options
4. Earthquake - Environmental
5. Light, Detect Monster - Utility
6. Summon Ally - Advanced
7. Remove Curse, Recharging - Future-proofing

**For Each Scroll:**
```python
def scroll_<name>(*args, **kwargs):
    """<Description>"""
    entity = args[0] if args else None
    
    # Implementation
    
    results = []
    results.append({"consumed": True})
    return results
```

### Phase 3: Spawn Rates & Balance (2-3 hours)
**Files to Modify:**
- `config/game_constants.py` - Add spawn rates

**Rarity Tiers:**
- **Common (30%):** Light, Blink, Teleport
- **Uncommon (50%):** Identify, Haste, Fear, Detect Monster, Remove Curse
- **Rare (15%):** Enchant Weapon, Enchant Armor, Earthquake, Summon Ally
- **Very Rare (5%):** Recharging

**Balance Considerations:**
- Identify shouldn't be too common (devalues system)
- Enchant scrolls are powerful (limit to rare)
- Tactical scrolls should be common enough to use

### Phase 4: Identify Scroll Implementation (2-3 hours)
**Special Handling:**
- Needs inventory selection UI
- Needs to mark item as identified
- Needs to update global registry

**Implementation:**
```python
def scroll_identify(*args, **kwargs):
    """Identify one unidentified item."""
    # 1. Check for unidentified items
    # 2. Show selection menu
    # 3. Mark selected item as identified
    # 4. Update IdentificationManager
    # 5. Show success message
```

**UI Flow:**
1. Read identify scroll
2. Show "Select item to identify:" menu
3. List unidentified items only
4. Player selects
5. Item becomes identified
6. Scroll consumed

### Phase 5: Testing (3-4 hours)
**Test Files to Create:**
1. `tests/test_scroll_identification.py` - ID system
2. `tests/test_new_scrolls.py` - New scroll functions
3. `tests/test_scroll_variety.py` - Spawn rates, balance

**Test Coverage:**
- Label generation
- Scroll identification
- Each new scroll function
- Identify scroll selection UI
- Integration with difficulty settings
- Global registry consistency

### Phase 6: Integration & Polish (2-3 hours)
**Tasks:**
1. Update spawn rates in level generation
2. Update item descriptions
3. Add to help menu
4. Update tutorial (if exists)
5. Playtest 10+ runs
6. Balance adjustments

---

## Technical Details

### Enchant Weapon/Armor Implementation

```python
def scroll_enchant_weapon(*args, **kwargs):
    """Enchant a weapon, adding +1 to-hit (max +3)."""
    entity = args[0] if args else None
    results = []
    
    # Get weapons from inventory
    weapons = [item for item in entity.inventory.items 
               if item.components.has(ComponentType.EQUIPPABLE) 
               and item.equippable.slot == EquipmentSlots.MAIN_HAND]
    
    if not weapons:
        results.append({"consumed": False, 
                       "message": MB.failure("No weapons to enchant!")})
        return results
    
    # Show selection menu (if multiple)
    selected_weapon = weapons[0]  # Simplified for now
    
    # Get current enchantment level
    equippable = selected_weapon.equippable
    current_bonus = getattr(equippable, 'enchantment_bonus', 0)
    
    if current_bonus >= 3:
        results.append({"consumed": True,  # Still consumed!
                       "message": MB.warning(f"{selected_weapon.name} cannot be enchanted further!")})
        return results
    
    # Apply enchantment
    equippable.enchantment_bonus = current_bonus + 1
    equippable.to_hit_bonus += 1
    
    results.append({"consumed": True,
                   "message": MB.success(f"{selected_weapon.name} glows brightly! (+{equippable.enchantment_bonus} enchantment)")})
    return results
```

### Earthquake Implementation

```python
def scroll_earthquake(*args, **kwargs):
    """Cause earthquake in 3-tile radius, destroying walls and damaging creatures."""
    entity = args[0] if args else None
    game_map = kwargs.get('game_map')
    entities = kwargs.get('entities', [])
    
    results = []
    
    # Get all tiles in radius
    radius = 3
    cx, cy = entity.x, entity.y
    
    # Destroy walls
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            x, y = cx + dx, cy + dy
            
            if 0 <= x < game_map.width and 0 <= y < game_map.height:
                distance = ((dx**2 + dy**2) ** 0.5)
                if distance <= radius:
                    tile = game_map.tiles[x][y]
                    
                    # Destroy walls (turn into floor)
                    if tile.blocked:
                        tile.blocked = False
                        tile.block_sight = False
                        # Create rubble visual effect
    
    # Damage all creatures in radius
    for target in entities:
        if target == entity:
            continue  # Don't damage caster
        
        dx = target.x - cx
        dy = target.y - cy
        distance = ((dx**2 + dy**2) ** 0.5)
        
        if distance <= radius and target.components.has(ComponentType.FIGHTER):
            damage = dice.roll_dice(3, 6)  # 3d6 damage
            
            target_results = target.fighter.take_damage(damage)
            results.extend(target_results)
            
            results.append({"message": MB.combat(f"{target.name} takes {damage} damage from earthquake!")})
    
    results.append({"consumed": True,
                   "message": MB.spell(f"The ground shakes violently!")})
    return results
```

---

## Testing Strategy

### Unit Tests
- Each scroll function tested in isolation
- Mock all dependencies (game_map, entities, etc.)
- Test edge cases (empty inventory, max enchantment, etc.)

### Integration Tests
- Scroll identification with global registry
- Spawn rates match configuration
- Difficulty scaling works
- Label consistency across game

### Regression Tests
- All existing scrolls still work
- Identification doesn't break existing systems
- Save/load preserves scroll state

### Playtesting Checklist
- [ ] Find identify scroll, use it successfully
- [ ] Find enchant scroll, upgrade weapon to +3
- [ ] Test each new scroll in combat
- [ ] Verify scroll labels randomize on new game
- [ ] Check spawn rates feel balanced
- [ ] Confirm difficulty settings work (Easy vs Hard)
- [ ] Test with identification system disabled
- [ ] Verify no crashes or errors

---

## Risks & Mitigations

### Risk 1: UI for Identify Scroll
**Issue:** Need inventory selection interface
**Mitigation:** Use existing inventory UI patterns, keep simple

### Risk 2: Enchantment System
**Issue:** No existing enchantment tracking on items
**Mitigation:** Add `enchantment_bonus` attribute to Equippable component

### Risk 3: Balance
**Issue:** Too many/few scrolls spawning
**Mitigation:** Easy to adjust spawn rates in constants

### Risk 4: Identify Scroll Economy
**Issue:** If too common, identification becomes meaningless
**Mitigation:** Mark as Uncommon, playtest extensively

---

## Definition of Done

- [ ] 12+ new scrolls implemented and tested
- [ ] Scroll identification system working
- [ ] Identify scroll selects from inventory
- [ ] Enchant scrolls upgrade equipment
- [ ] All scrolls have proper spawn rates
- [ ] 30+ scroll labels implemented
- [ ] Integration with difficulty settings
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] Playtesting complete (10+ runs)
- [ ] Documentation updated
- [ ] Depth scores updated

---

## Success Metrics

**Quantitative:**
- 20 total scroll types (vs 8 before)
- Depth score: 38/64 → 44/64 (69%)
- 30+ tests passing
- 0 crashes or errors

**Qualitative:**
- Players ask "What does this scroll do?"
- Players get excited finding identify scrolls
- Enchant scrolls feel rewarding
- Tactical scrolls create interesting decisions

---

## Next Steps After Completion

With scrolls complete, we'll have:
- **Complete identification system** (potions + scrolls)
- **20 scrolls + 19 potions** = 39 consumables
- **Strong foundation** for wands/rings later

**Then Move to:**
1. **Resistance System** - Fire/Cold/Poison resist
2. **Throwing System** - Throw potions at enemies
3. **Item Stacking** - Clean up inventory

**Milestone 1 "Real Roguelike" will be COMPLETE at 69%!** 🎯

---

## Appendix: Scroll Label Full List

```python
SCROLL_LABELS = [
    "XYZZY", "PRATYAVAYAH", "ELBIB YLOH", "VE FORBRYDERNE",
    "ZELGO MER", "JUYED AWK YACC", "NR 9", "ANDOVA BEGARIN",
    "HACKEM MUCHE", "VELOX NEB", "READ ME", "FOOBIE BLETCH",
    "TEMOV", "GARVEN DEH", "LOREM IPSUM", "ETAOIN SHRDLU",
    "DUAM XNAHT", "KERNOD WEL", "ELAM EBOW", "VERR YED HORRE",
    "ASHPD SODALG", "YUM YUM", "DAIYEN FOOELS", "LEP GEX VEN ZEA",
    "PRIRUTSENIE", "ELBIB", "ZLORFIK", "GNIK SISI VLE",
    "GHOTI", "ABRA KA DABRA", "HOCUS POCUS", "SHAZAM"
]
```

Classic roguelike references included! 🎮

