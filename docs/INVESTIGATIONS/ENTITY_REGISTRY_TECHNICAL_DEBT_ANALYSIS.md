# Entity Registry Technical Debt Analysis

**Date:** 2026-01-01  
**Trigger:** Difficulty adding Necromancer attributes  
**Status:** ANALYSIS COMPLETE

---

## Problem Statement

Adding a new monster with custom abilities requires touching **3 locations**:

1. `MonsterDefinition` dataclass (~54 fields currently)
2. `_process_monsters_with_inheritance()` constructor call (~60 lines of kwargs)
3. `monster_factory.py` attribute copying (~20 lines per ability group)

**Symptom:** Adding 6 necromancer attributes required:
- 6 lines in MonsterDefinition (fields 49-54)
- 6 lines in _process_monsters_with_inheritance (kwargs)
- 7 lines in monster_factory (attribute copying)

**This is a textbook example of rigid schema drift.**

---

## Root Cause Analysis

### The Rigid Schema Problem

**MonsterDefinition is a @dataclass with 54 explicit fields.**

**Pros:**
- ✅ Type safety (IDE autocomplete)
- ✅ Validation (dataclass __post_init__)
- ✅ Self-documenting (field names explicit)
- ✅ Compile-time checks (typos caught early)

**Cons:**
- ❌ Every new ability requires 3-location edit
- ❌ 54 fields in one class (cognitive overload)
- ❌ Constructor call is 60+ lines (hard to review)
- ❌ Doesn't scale to future abilities (10+ more monsters planned)

### The Organic Growth Pattern

**Phase 19 added 9 monsters, each with unique abilities:**
- Troll: regeneration (1 field)
- Slime: corrosion + split (7 fields)
- Skeleton: shield wall + damage modifiers (3 fields)
- Orc Chieftain: rally + bellow (9 fields)
- Orc Shaman: hex + chant (12 fields)
- Necromancer: raise dead + hang-back (6 fields)
- Wraith: life drain (handled separately)

**Each addition added ~3-12 fields to MonsterDefinition.**

**Projection:** 10 more ability-based monsters = **+80-120 fields** = **~130-170 field dataclass** (unmaintainable)

---

## Current Architecture Strengths

**What's Working Well:**

1. **YAML as source of truth:** Config-driven, no hardcoded stats
2. **Inheritance system:** Efficient for stat variations (orc_veteran extends orc)
3. **Factory pattern:** Clean separation (registry vs factory vs entity)
4. **Centralized registry:** Single load, fast lookups
5. **Validation:** Dataclass catches missing required fields

**Don't break these!**

---

## Proposed Solutions (3 Options)

### Option A: Ability Component System (RECOMMENDED)

**Concept:** Move ability configs to separate dataclasses/components.

**Example:**
```python
@dataclass
class RaiseDeadAbility:
    enabled: bool = True
    range: int = 5
    cooldown_turns: int = 4
    danger_radius: int = 2
    preferred_distance_min: int = 4
    preferred_distance_max: int = 7

@dataclass
class MonsterDefinition:
    # Core fields (18 fields, stable)
    name: str
    stats: EntityStats
    char: str
    color: Tuple[int, int, int]
    ai_type: str = "basic"
    # ... core fields only ...
    
    # Abilities (extensible)
    abilities: Dict[str, Any] = field(default_factory=dict)
    # abilities = {
    #   "raise_dead": RaiseDeadAbility(...),
    #   "hex": HexAbility(...),
    # }
```

**In YAML:**
```yaml
necromancer:
  # ... core stats ...
  abilities:
    raise_dead:
      enabled: true
      range: 5
      cooldown_turns: 4
      danger_radius: 2
```

**Benefits:**
- ✅ MonsterDefinition stays small (~20 core fields)
- ✅ New abilities don't touch MonsterDefinition
- ✅ Type-safe per-ability configs
- ✅ Self-contained ability modules
- ✅ Easy to deprecate old abilities

**Cost:**
- Moderate refactor (~2-3 hours)
- Need ability registry/factory
- Backward compat for existing saves

**Verdict:** ⭐ **BEST for long-term scalability**

---

### Option B: Generic Attributes Dict (PRAGMATIC)

**Concept:** Add `custom_attrs: Dict[str, Any]` to MonsterDefinition.

**Example:**
```python
@dataclass
class MonsterDefinition:
    # Core fields (18 stable fields)
    name: str
    stats: EntityStats
    # ...
    
    # Generic catch-all for ability configs
    custom_attrs: Dict[str, Any] = field(default_factory=dict)

# In _process_monsters_with_inheritance:
monster_def = MonsterDefinition(
    name=...,
    stats=...,
    # ... core fields ...
    custom_attrs={k: v for k, v in monster_data.items() 
                  if k not in CORE_FIELDS}
)

# In monster_factory:
for key, value in monster_def.custom_attrs.items():
    setattr(monster, key, value)
```

**In YAML:** (unchanged)
```yaml
necromancer:
  raise_dead_enabled: true
  raise_dead_range: 5
  # ... etc ...
```

**Benefits:**
- ✅ Small refactor (~1 hour)
- ✅ No MonsterDefinition edits for new abilities
- ✅ Backward compatible (existing monsters unaffected)
- ✅ Minimal risk

**Costs:**
- ❌ Loses type safety (typos not caught until runtime)
- ❌ No IDE autocomplete for custom attrs
- ❌ Validation harder (need custom checks)

**Verdict:** ⭐ **BEST for immediate unblocking**

---

### Option C: Config Schema Generator (OVER-ENGINEERED)

**Concept:** Auto-generate MonsterDefinition from YAML schema.

**Approach:**
- Parse YAML, introspect fields
- Dynamically create dataclass at runtime
- Use `type()` or `make_dataclass()`

**Benefits:**
- ✅ Zero manual schema updates
- ✅ YAML drives schema (DRY principle)

**Costs:**
- ❌ Loses static type checking entirely
- ❌ IDE support broken
- ❌ Debugging nightmare
- ❌ Over-engineered for this scale

**Verdict:** ❌ **NOT RECOMMENDED**

---

## Recommendation

### Short-Term (Now): **Do Nothing**

**Why:**
- Current system **works** (3286 tests passing)
- Adding necromancer took ~20 lines across 3 files (acceptable)
- **Refactor is premature** until we hit **10+ more ability-based monsters**
- Risk of introducing bugs > value of slight convenience improvement

**Trigger for refactor:** When MonsterDefinition hits **80+ fields** (~5-7 more Phase 19-style monsters)

### Medium-Term (Next Phase): **Option B (Generic Attributes)**

**When:**
- If Phase 20/21 adds 5+ monsters with unique abilities
- If MonsterDefinition hits 80 fields
- If adding attributes becomes painful (>30 min per monster)

**Effort:** ~1-2 hours
**Risk:** Low (backward compatible)
**Value:** High (unblocks future growth)

### Long-Term (Phase 22+): **Option A (Ability Component System)**

**When:**
- If we plan 20+ ability-based monsters
- If abilities need composition (monster with hex + rally + raise)
- If ability reuse across monsters becomes common

**Effort:** ~4-6 hours
**Risk:** Moderate (requires careful migration)
**Value:** Very high (proper architecture)

---

## Current System Metrics

**MonsterDefinition:**
- 54 fields (18 core + 36 ability-specific)
- Growth rate: +6 fields per ability-based monster (avg)
- Projected at 10 more monsters: **~110 fields** (too many)

**_process_monsters_with_inheritance:**
- 60 lines of kwargs in constructor call
- Each new ability: +6 lines
- Projected at 10 more monsters: **~120 lines** (too many)

**monster_factory attribute copying:**
- ~180 lines total
- ~7 lines per ability group
- Manageable but repetitive

---

## Comparison: Current vs Options

| Aspect | Current | Option B (Dict) | Option A (Components) |
|--------|---------|-----------------|----------------------|
| Fields in MonsterDefinition | 54 | 18 | 18 |
| Type safety | Full | Partial | Full |
| IDE autocomplete | Full | None | Full |
| Lines per new ability | 19 (3 locations) | 0 (just YAML) | 5 (ability class) |
| Refactor effort | - | 1-2 hours | 4-6 hours |
| Risk | - | Low | Moderate |
| Scalability | Poor (54→110) | Good | Excellent |

---

## Specific Pain Points Observed

**During Necromancer Implementation:**

1. **Step 1:** Add 6 fields to MonsterDefinition
   - Easy but verbose
   - Had to scroll through 54 existing fields
   - Risk of typos in field names

2. **Step 2:** Add 6 kwargs to constructor call
   - Error-prone (easy to miss one)
   - Constructor call is 60+ lines (hard to review diffs)
   - Must match field order/names exactly

3. **Step 3:** Add 7 lines to monster_factory
   - Pattern is clear (copy from monster_def to monster)
   - But repetitive and easy to forget

**Time cost:** ~15 minutes (acceptable)
**Frustration:** Moderate (3 locations, careful matching required)

**If we had 10 more monsters:** ~2.5 hours of mechanical schema updates (unacceptable)

---

## Decision Framework

**Ask yourself:**

1. **How many more ability-based monsters are planned?**
   - 0-5: Do nothing
   - 5-10: Option B (generic dict)
   - 10+: Option A (component system)

2. **Is schema update time becoming painful?**
   - No (< 30 min): Do nothing
   - Yes (> 30 min): Refactor

3. **Do abilities need composition/reuse?**
   - No: Option B sufficient
   - Yes: Option A required

4. **Is technical debt blocking development?**
   - No: Defer refactor
   - Yes: Refactor immediately

---

## Recommendation for RLIKE

**Current Assessment:**

- ✅ System works (3286 tests pass)
- ✅ Adding necromancer took 15-20 minutes (acceptable)
- ✅ No immediate blocking pain
- ⚠️ Growth trajectory concerning (54→110+ fields)
- ⚠️ MonsterDefinition becoming unwieldy

**Recommendation:**

### **DEFER REFACTOR** until:
1. MonsterDefinition hits 80 fields (6-7 more Phase 19-style monsters), OR
2. Next phase plans 5+ ability-based monsters, OR
3. Schema updates take >30 minutes per monster

**Then: Implement Option B (Generic Attributes Dict)**
- Low risk
- 1-2 hour effort
- Unblocks future growth
- Backward compatible

**For now:**
- Document this technical debt (this file)
- Monitor field count growth
- Revisit decision after Phase 20 planning

---

## If Refactoring, Do This:

### Option B Implementation Plan

**Step 1:** Add `custom_attrs` to MonsterDefinition
```python
@dataclass
class MonsterDefinition:
    # ... existing core fields (18) ...
    
    # Generic catch-all (replaces 36 ability-specific fields)
    custom_attrs: Dict[str, Any] = field(default_factory=dict)
```

**Step 2:** Update `_process_monsters_with_inheritance`
```python
# Define core field set
CORE_MONSTER_FIELDS = {
    'name', 'stats', 'char', 'color', 'ai_type', 'render_order',
    'blocks', 'extends', 'faction', 'can_seek_items', 'inventory_size',
    'seek_distance', 'special_abilities', 'tags', 'equipment',
    'is_boss', 'boss_name', 'speed_bonus'
}

# Build custom_attrs from non-core fields
custom_attrs = {k: v for k, v in monster_data.items() 
                if k not in CORE_MONSTER_FIELDS and k != 'stats'}

monster_def = MonsterDefinition(
    # ... core fields only ...
    custom_attrs=custom_attrs
)
```

**Step 3:** Update `monster_factory.py`
```python
# Copy all custom attributes to entity
for attr_name, attr_value in monster_def.custom_attrs.items():
    setattr(monster, attr_name, attr_value)
    logger.debug(f"Set custom attr {attr_name}={attr_value} on {monster.name}")
```

**Step 4:** Migrate existing ability fields
- Move 36 ability fields from MonsterDefinition to custom_attrs
- Keep defaults in YAML (not in Python)
- Remove explicit kwargs from constructor

**Step 5:** Add validation helper
```python
def validate_ability_config(monster_def: MonsterDefinition, required_fields: List[str]):
    """Validate that required ability fields are present."""
    for field in required_fields:
        if field not in monster_def.custom_attrs:
            raise ValueError(f"Monster {monster_def.name} missing required field: {field}")
```

**Effort:** 1-2 hours
**Risk:** Low (tests catch regressions)
**Value:** High (unblocks future monsters)

---

## Comparison to Industry Patterns

### **Good Example: Unity GameObject**
```csharp
// Components are separate, composable
GameObject monster = new GameObject();
monster.AddComponent<Fighter>();
monster.AddComponent<RaiseDeadAbility>();
```

### **Bad Example: God Object**
```python
class Monster:
    # 200 fields
    hex_enabled, hex_radius, hex_duration, ...
    rally_radius, rally_min_allies, ...
    raise_range, raise_cooldown, ...
    # (This is where we're headed)
```

### **Current RLIKE:**
- MonsterDefinition = **data-driven god object** (54 fields)
- Not as bad as code god object (it's data, not logic)
- But trending toward unmaintainable

---

## Alternative: Ability-Specific AI (Current Pattern)

**What we're actually doing:**
- MonsterDefinition stores ability config
- AI class reads config from monster entity
- AI implements behavior

**Example:**
```python
# NecromancerAI reads config from self.owner
raise_range = getattr(self.owner, 'raise_dead_range', 5)
```

**This is actually fine!** The problem is just the **schema declaration**, not the runtime pattern.

**Insight:** We don't need to change the runtime pattern. We just need to make schema updates easier.

---

## Concrete Recommendation

### **Do This Now:**

**NOTHING.** Document the debt (this file) and move on.

**Reasons:**
1. Current system works fine
2. 15-20 minutes per monster is acceptable
3. No blocking pain yet
4. Premature refactor = risk for little gain

### **Do This When MonsterDefinition Hits 80 Fields:**

**Implement Option B (Generic Attributes):**

1. Add `custom_attrs: Dict[str, Any]` to MonsterDefinition
2. Move ability fields (36→0) to custom_attrs
3. Update constructor to auto-populate custom_attrs
4. Update monster_factory to auto-copy custom_attrs
5. Keep core fields (18) as explicit dataclass fields

**Estimated effort:** 2 hours
**Estimated risk:** Low (extensive test coverage)
**Estimated value:** High (unblocks 50+ future monsters)

---

## Metrics to Monitor

**Field Count Growth:**
- Current: 54 fields
- Trigger for refactor: **80 fields**
- Emergency threshold: **100 fields**

**Time per Monster:**
- Current: 15-20 minutes
- Trigger for refactor: **30+ minutes**
- Emergency threshold: **60+ minutes**

**Lines per Ability:**
- Current: ~19 lines (3 locations)
- Trigger for refactor: **30+ lines**

---

## Historical Context

**Why did this happen?**

Phase 19 was **exploratory** - we didn't know upfront how many ability-based monsters we'd add or what their configs would look like.

**Typical progression:**
1. First monster (Troll): "Just add 1 field, NBD"
2. Second monster (Slime): "7 more fields, getting big..."
3. Third monster (Skeleton): "3 more, starting to notice pattern"
4. Fourth monster (Chieftain): "9 more, this is getting repetitive"
5. Fifth monster (Shaman): "12 more, okay this is a pattern now"
6. Sixth monster (Necromancer): "Wait, this is taking too long"

**This is normal!** Organic growth often requires later refactoring once patterns emerge.

---

## Philosophical Question: Is This Actually Tech Debt?

**Argument FOR "Yes, it's debt":**
- Adding fields in 3 places is mechanical toil
- Doesn't scale to 10+ more monsters
- High cognitive load (54 fields to scan)

**Argument AGAINST "No, it's fine":**
- Only costs 15-20 minutes per monster
- Type safety is valuable
- Explicit is better than implicit (Python zen)
- Refactor has risk (tests might miss edge cases)

**My take:**
- It's **mild technical debt**
- Not urgent (system works)
- Worth addressing **when it hurts** (80+ fields or 30+ min per monster)
- Current approach is **defensible** given test coverage

---

## What Other Projects Do

**Roguelike Examples:**

**Dungeon Crawl Stone Soup (C++):**
- Monster data in .txt files (key-value pairs)
- Generic attribute loading (similar to Option B)
- ~500 monsters, works well

**NetHack (C):**
- Hardcoded monster structs (~200 fields!)
- Every monster has all fields (most unused)
- Works but unmaintainable

**Cogmind (C++):**
- Component-based (similar to Option A)
- Each ability is a component class
- Highly extensible (~1000 entity types)

**Brogue (C):**
- Hardcoded flags + special-case logic
- Fast to code, painful to extend
- ~30 monsters max (our scale)

**RLIKE's current approach is typical for ~20-30 monster types.**
**At 50+ monsters, most projects migrate to generic attrs or components.**

---

## Action Items

**Immediate:**
- [x] Document this analysis (this file)
- [x] Add field count to MonsterDefinition docstring
- [x] Add comment: "Refactor to generic attrs at 80 fields"

**Before Next Phase:**
- [ ] Review Phase 20 monster plans
- [ ] Estimate total new fields
- [ ] Decide: proceed with current pattern or refactor first

**When MonsterDefinition hits 80 fields:**
- [ ] Implement Option B (generic attributes)
- [ ] Migrate existing abilities to custom_attrs
- [ ] Update this doc with "REFACTOR COMPLETE" status

---

## Conclusion

**Yes, this is technical debt.**  
**No, it doesn't need immediate fixing.**

**The current system is:**
- ✅ Functional
- ✅ Well-tested
- ✅ Understood by the team
- ⚠️ Showing early signs of scaling issues
- ⚠️ Will become painful at 80+ fields

**The right move is:**
- Continue with current pattern for now
- Monitor field count growth
- Refactor when pain > risk (80 fields or 30+ min per monster)

**This is good engineering judgment:** Don't refactor preemptively, but document the debt and set clear triggers for when to act.

---

**END OF ANALYSIS**

