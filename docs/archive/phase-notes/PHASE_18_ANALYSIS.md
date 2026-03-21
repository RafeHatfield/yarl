# Phase 18: Item Identity & Damage Type Semantics

**Date**: 2025-12-13  
**Branch**: `feature/phase18-item-identity`  
**Status**: Analysis Complete

## Step 0: Critical Hit System Verification

### ✅ CONFIRMED: Critical Hits EXIST

**Evidence:**

**File**: `components/fighter.py`, method `attack_d20()` (lines 815-945)

**Mechanics:**
```python
# Line 858: Roll d20
d20_roll = random.randint(1, 20)

# Line 875: Check for critical
is_critical = (d20_roll == 20) or is_surprise

# Lines 926-929: Double damage on crit
if is_critical:
    damage = damage * 2
    damage = max(1, damage)
```

**Critical Hit System:**
- **Trigger**: Natural 20 on d20 attack roll (5% base chance)
- **Effect**: Double ALL damage (weapon dice + STR modifier)
- **Always Hits**: Natural 20 bypasses AC check
- **Visual**: Yellow/gold flash on target
- **Message**: "CRITICAL HIT! X strikes Y for Z damage!"
- **Surprise Bonus**: Surprise attacks are forced crits (Phase 9 mechanic)

**Statistics Tracking:**
- `components/statistics.py` tracks `critical_hits` count (line 49)
- `record_attack(hit=True, critical=True)` increments counter (line 96)
- Death screen displays critical hit count (line 106 in death_screen_renderer.py)

**Documentation:**
- `docs/COMBAT_SYSTEM.md` (lines 252-257) describes crit system
- Natural 20 = auto-hit + double damage
- Minimum 1 damage even on crit

### Conclusion

**Critical hits are a CORE combat mechanic** with:
- Established probability (5% base)
- Damage multiplier (2×)
- Visual/audio feedback
- Statistics tracking
- Full documentation

**Implication for Phase 18**: Weapon affixes CAN use crit mechanics:
- "Keen" weapons → +crit chance (e.g., crit on 19-20 instead of just 20)
- "Vicious" weapons → +crit multiplier (e.g., 2.5× instead of 2×)
- Both approaches are valid and testable

---

## Phase 18 Design Goals

### 1. Weapon Affix Identity

**Current Problem:**
- Weapons have generic names ("Iron Sword", "Fine Dagger")
- Affixes don't convey mechanical differences
- Players can't distinguish gear quality at a glance

**Solution:**
Explicit affix-to-stat mapping with clear naming:

| Affix | Mechanical Effect | Example |
|-------|------------------|---------|
| **Fine** | +1 to-hit OR +1 AC (armor) | "Fine Longsword" (+1 hit) |
| **Keen** | Expanded crit range (19-20) | "Keen Rapier" (10% crit) |
| **Vicious** | +1 damage OR crit multiplier 2.5× | "Vicious Battleaxe" (+1 dmg) |
| **Masterwork** | +1 to-hit AND +1 damage | "Masterwork Greatsword" |
| **Heavy** | +2 damage, -1 to-hit | "Heavy Warhammer" (already exists?) |

### 2. Damage Type Semantics

**Current State:**
- Weapons likely have damage types (slashing/piercing/bludgeoning)
- But damage type doesn't affect mechanics

**Solution:**
Armor type vulnerability/resistance system:

| Armor Type | Vulnerable To | Resistant To |
|------------|---------------|--------------|
| **Cloth/Leather** | Slashing (+1 dmg) | Bludgeoning (-1 dmg) |
| **Chainmail** | Piercing (+1 dmg) | Slashing (-1 dmg) |
| **Plate** | Bludgeoning (+1 dmg) | Piercing (-1 dmg) |

**OR** simpler approach:
- Undead: Vulnerable to bludgeoning (+2 dmg)
- Armored enemies: Vulnerable to piercing (+1 dmg)
- Beasts: Vulnerable to slashing (+1 dmg)

---

## Implementation Plan

### Phase 18.1: Critical Hit Expansion (Keen Weapons)

**Files to modify:**
- `components/equippable.py` - Add `crit_range` field
- `components/fighter.py` - Check `crit_range` in attack_d20()
- `config/equipment.yaml` - Define "Keen" weapons

**Mechanics:**
```python
# In attack_d20():
crit_threshold = 20  # Default
if weapon and weapon.equippable:
    crit_threshold = weapon.equippable.crit_threshold or 20

is_critical = (d20_roll >= crit_threshold) or is_surprise
```

**Example:**
- Normal weapon: Crit on 20 (5% chance)
- Keen weapon: Crit on 19-20 (10% chance)
- Superior Keen: Crit on 18-20 (15% chance) - rare

### Phase 18.2: Damage Type Resistance/Vulnerability

**Files to modify:**
- `components/fighter.py` - Add damage type parameter
- `components/equippable.py` - Add `damage_type` field
- Damage calculation - Apply resist/vuln modifiers

**Mechanics:**
```python
# Simple approach (monster-based):
def apply_damage_type_modifier(base_damage, damage_type, target):
    if target.name == "Skeleton" and damage_type == "bludgeoning":
        return base_damage + 2  # Skeletons vulnerable to crushing
    if target.name == "Zombie" and damage_type == "slashing":
        return base_damage - 1  # Zombies resistant to cuts
    return base_damage
```

### Phase 18.3: Explicit Affix System

**Create affix configuration:**
```yaml
# config/weapon_affixes.yaml
affixes:
  fine:
    to_hit_bonus: +1
    tier: "common"
  
  keen:
    crit_threshold: 19  # Crit on 19-20
    tier: "uncommon"
  
  vicious:
    damage_bonus: +1
    tier: "uncommon"
  
  masterwork:
    to_hit_bonus: +1
    damage_bonus: +1
    tier: "rare"
```

---

## Testing Strategy

### Unit Tests (Required)

1. **Crit Range Tests:**
   ```python
   def test_keen_weapon_crits_on_19():
       weapon = create_weapon("keen_dagger")
       assert weapon.equippable.crit_threshold == 19
       # ... attack test with mocked d20 roll = 19
       assert result["is_critical"] == True
   ```

2. **Damage Type Tests:**
   ```python
   def test_bludgeoning_vs_skeleton():
       weapon = create_weapon("club")  # Bludgeoning
       target = create_monster("skeleton")
       damage = calculate_damage(weapon, target)
       # Verify bonus damage applied
   ```

3. **Affix Identity Tests:**
   ```python
   def test_fine_longsword_has_to_hit_bonus():
       weapon = create_weapon("fine_longsword")
       assert weapon.equippable.to_hit_bonus >= base_longsword.to_hit_bonus
   ```

### Integration Tests (Scenario Harness)

- Run deterministic combat scenarios
- Verify crit frequency for keen weapons (should be ~10% with sufficient samples)
- Verify damage type bonuses apply consistently

---

## Guardrails

### ✅ DO NOT:
- Rewrite combat core
- Change d20 roll mechanics
- Modify TurnStateAdapter
- Break ECS architecture
- Change rendering boundary

### ✅ ONLY MODIFY:
- `components/equippable.py` (add fields)
- `components/fighter.py` (read new fields in attack)
- `config/equipment.yaml` (define affixes)
- Tests for new mechanics

---

## Expected Outcomes

### Player Experience

**Before Phase 18:**
```
"You find an Iron Longsword"
"You find a Fine Dagger"
→ What's the difference?
```

**After Phase 18:**
```
"You find a Keen Rapier" (10% crit chance)
"You find a Vicious Battleaxe" (+1 damage)
"You find a Masterwork Greatsword" (+1 hit, +1 damage)
→ Clear mechanical identity!
```

### Combat Feedback

**Before:**
```
You hit the Skeleton for 6 damage. (generic)
```

**After:**
```
You hit the Skeleton for 8 damage! (bludgeoning bonus vs undead)
CRITICAL HIT! Your Keen Rapier strikes the Orc for 14 damage!
```

---

## Implementation Status

1. ✅ **Step 0 Complete**: Confirmed crits exist
2. ✅ **Keen weapon crit ranges**: Implemented (crit_threshold field)
3. ✅ **Damage types added**: Base weapons have damage_type field
4. ✅ **Affix weapons created**: 8 new affixed weapons in entities.yaml
5. ✅ **Keen tests added**: 5 tests for keen crit mechanics
6. ✅ **Phase 18.1 tests pass**: All passing
7. ✅ **Damage type resistance/vulnerability**: Implemented (+1/-1 modifiers)
8. ✅ **Damage type tests added**: 5 tests for resist/vuln mechanics
9. ✅ **All tests pass**: 3097+ tests passing
10. [ ] Player-facing documentation (optional)

---

## Phase 18.1 + 18.2 Implementation Complete

### Files Modified

**`components/equippable.py`:**
- Added `crit_threshold` field (default 20)
- Added `damage_type` field (slashing/piercing/bludgeoning)

**`components/fighter.py`:**
- Modified `attack_d20()` to check weapon `crit_threshold`
- Crits now trigger on `d20_roll >= crit_threshold` (not just == 20)
- Defensive checks for mock compatibility

**`config/entities.yaml`:**
- Added `damage_type` to base weapons (dagger, club, shortsword, mace)
- Added 8 affixed weapons:
  - `keen_dagger`, `keen_rapier` (crit 19-20, 10% chance)
  - `vicious_battleaxe`, `vicious_warhammer` (1d10+1 damage)
  - `fine_longsword`, `fine_mace` (+1 to-hit)
  - `masterwork_greatsword` (+1 hit, +1 damage)

**`tests/test_phase18_keen_weapons.py`** (NEW):
- 5 tests validating keen crit mechanics
- All tests passing

---

## Phase 18.2: Damage Type System Implemented

### Resistance/Vulnerability Mechanics

**Implementation** (`components/fighter.py`):
```python
# After base damage calculation, before crit multiplier:
if weapon_damage_type:
    if target.damage_resistance == weapon_damage_type:
        damage -= 1  # Resistant: -1 damage
    elif target.damage_vulnerability == weapon_damage_type:
        damage += 1  # Vulnerable: +1 damage
```

**Monster Configuration** (`config/entities.yaml`):
```yaml
zombie:
  damage_resistance: "piercing"     # Rotting flesh resists stabs
  damage_vulnerability: "bludgeoning"  # Crushing destroys undead
```

### Test Coverage

**`tests/test_phase18_damage_types.py`** (NEW - 5 tests):
- ✅ Vulnerable targets take +1 damage
- ✅ Resistant targets take -1 damage (floor at 1)
- ✅ Neutral targets unaffected
- ✅ Modifier applies before crit multiplier
- ✅ Damage never goes below 1

### Design Rationale

**Why +1/-1 flat modifiers?**
- Simple to understand ("clubs hurt zombies more")
- Easy to test (deterministic)
- Small balance impact (~15-20% damage swing)
- No percentage calculations or complex formulas

**Why zombie only?**
- Proof of concept (can expand later)
- Clear thematic fit (undead flesh)
- Easy to validate in testing

**Application Order:**
```
Base damage (weapon dice) → +STR → +damage_type → ×crit → floor(1)
```

---

**Status**: ✅ **Phase 18.1 + 18.2 Complete** - Keen weapons, affixes, and damage type system fully implemented and tested!
