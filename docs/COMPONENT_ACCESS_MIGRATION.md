# Component Access Migration Guide

**Purpose:** Standardize all component access patterns to use the new Entity helper methods  
**Status:** 🚧 In Progress  
**Branch:** `refactor/component-access-standardization`

---

## 📊 Migration Status

### **Analysis Results**
- **Old ComponentRegistry pattern:** ~84 instances across 18 files
- **Old attribute access pattern:** ~179 instances across codebase
- **Total refactoring needed:** ~263 instances

### **Priority Files (by component access frequency)**
1. ✅ `entity.py` - Helper methods added
2. ⏳ `components/ai.py` - 13 ComponentRegistry calls
3. ⏳ `components/fighter.py` - 9 ComponentRegistry calls  
4. ⏳ `ui/tooltip.py` - 7 ComponentRegistry calls
5. ⏳ `game_actions.py` - 6 ComponentRegistry calls
6. ⏳ `components/status_effects.py` - 6 ComponentRegistry calls
7. ⏳ `components/monster_item_usage.py` - 5 ComponentRegistry calls

---

## 🎯 New Standard Patterns

### **Pattern 1: Required Component**
**Use when:** Component MUST exist (missing component is a bug)

```python
# ❌ OLD - Silent failure
fighter = entity.components.get(ComponentType.FIGHTER)
if fighter:
    fighter.take_damage(10)

# ❌ OLD - Attribute access (inconsistent)
entity.fighter.take_damage(10)

# ✅ NEW - Explicit and safe
fighter = entity.require_component(ComponentType.FIGHTER)
fighter.take_damage(10)  # Raises clear error if missing
```

**Benefits:**
- Clear error messages with entity name
- Fails fast (catches bugs immediately)
- No silent "nothing happens" bugs

---

### **Pattern 2: Optional Component**
**Use when:** Component may or may not exist (absence is expected)

```python
# ❌ OLD - Same as required (unclear intent)
equipment = entity.components.get(ComponentType.EQUIPMENT)
if equipment:
    # Use equipment

# ✅ NEW - Explicit optional semantics
equipment = entity.get_component_optional(ComponentType.EQUIPMENT)
if equipment:
    # Use equipment
```

**Benefits:**
- Clear intent (this is SUPPOSED to be optional)
- Same behavior, better readability
- Easier to identify bugs (required vs optional is obvious)

---

### **Pattern 3: Check Existence**
**Use when:** Just checking if component exists

```python
# ❌ OLD - Verbose
if entity.components.has(ComponentType.AI):
    # Entity is a monster

# ✅ NEW - Cleaner
if entity.has_component(ComponentType.AI):
    # Entity is a monster
```

**Benefits:**
- Slightly cleaner syntax
- Consistent with other helper methods
- Future-proof (can add caching/optimization)

---

## 🔍 Migration Decision Tree

```
Is the component REQUIRED for this operation?
│
├─ YES: Use require_component()
│   └─ Missing component = bug = should crash with clear error
│
└─ NO: Use get_component_optional()
    └─ Missing component = expected = return None gracefully
```

### **Examples of REQUIRED Components:**

```python
# Taking damage - entity MUST have Fighter
fighter = entity.require_component(ComponentType.FIGHTER)
fighter.take_damage(damage)

# AI taking turn - entity MUST have AI
ai = entity.require_component(ComponentType.AI)
ai.take_turn(...)

# Using item - item MUST have Item component
item_comp = item.require_component(ComponentType.ITEM)
item_comp.use(...)
```

### **Examples of OPTIONAL Components:**

```python
# Checking for equipment (not all entities have it)
equipment = entity.get_component_optional(ComponentType.EQUIPMENT)
if equipment and equipment.main_hand:
    damage += equipment.main_hand.power_bonus

# Checking for inventory (only some entities)
inventory = entity.get_component_optional(ComponentType.INVENTORY)
if inventory:
    inventory.add_item(item)

# Checking for AI (players don't have it)
ai = entity.get_component_optional(ComponentType.AI)
if ai:
    ai.take_turn(...)
```

---

## 📝 Migration Checklist

### **For Each File:**
- [ ] Identify all component access patterns
- [ ] Determine required vs optional for each
- [ ] Replace with appropriate helper method
- [ ] Run file-specific tests
- [ ] Commit with descriptive message

### **Testing Strategy:**
1. Run tests after each file migration
2. If tests fail, fix or revert
3. Don't move to next file until current one passes
4. Run full test suite after every 3-5 files

---

## 🚀 Migration Order

### **Phase 1: Core Systems (Week 1)**
1. ✅ `entity.py` - Add helpers (DONE)
2. 🟡 `components/ai.py` - High traffic, many bugs
3. 🟡 `components/fighter.py` - Combat critical
4. 🟡 `game_actions.py` - Core game loop
5. 🟡 `components/status_effects.py` - Effects system

### **Phase 2: UI & Interaction (Week 1)**
6. ⚪ `ui/tooltip.py` - Player-facing
7. ⚪ `ui/sidebar.py` - Player-facing
8. ⚪ `mouse_movement.py` - Input handling
9. ⚪ `menus.py` - UI system

### **Phase 3: Supporting Systems (Week 2)**
10. ⚪ `engine/systems/ai_system.py` - System layer
11. ⚪ `components/monster_item_usage.py` - Monster AI
12. ⚪ `components/item_seeking_ai.py` - Monster AI
13. ⚪ `spells/spell_executor.py` - Spell system
14. ⚪ `components/monster_equipment.py` - Loot system

### **Phase 4: Remaining Files (Week 2)**
15. ⚪ All remaining files with <5 instances each

---

## ⚠️ Common Pitfalls

### **Pitfall 1: Over-using require_component()**
```python
# ❌ BAD - Not all entities have equipment
equipment = entity.require_component(ComponentType.EQUIPMENT)  # Crashes for items!

# ✅ GOOD - Equipment is optional
equipment = entity.get_component_optional(ComponentType.EQUIPMENT)
```

### **Pitfall 2: Under-using require_component()**
```python
# ❌ BAD - Fighter should be required for combat
fighter = entity.get_component_optional(ComponentType.FIGHTER)
if fighter:  # Silent bug if missing!
    fighter.take_damage(damage)

# ✅ GOOD - Crash if Fighter missing (it's a bug!)
fighter = entity.require_component(ComponentType.FIGHTER)
fighter.take_damage(damage)
```

### **Pitfall 3: Not removing old imports**
```python
# ❌ BAD - Still importing old registry
from components.component_registry import ComponentRegistry, ComponentType

# ✅ GOOD - Only need ComponentType for helper methods
from components.component_registry import ComponentType
```

---

## 📈 Expected Outcomes

### **After Phase 1 (Core Systems):**
- ✅ 50+ instances migrated
- ✅ Critical bugs surface immediately (fail fast)
- ✅ ~30% of total migration complete
- ✅ Core game loop uses new patterns

### **After Phase 2 (UI & Interaction):**
- ✅ 80+ instances migrated
- ✅ User-facing code standardized
- ✅ ~60% of total migration complete
- ✅ Easier to onboard new developers

### **After Phase 3-4 (Complete):**
- ✅ All 263 instances migrated
- ✅ 100% consistent pattern
- ✅ Entire class of bugs eliminated
- ✅ Clear, maintainable codebase

---

## 🎓 Learning Resources

- **Entity Helper Docs:** See `entity.py` docstrings
- **Test Examples:** See `tests/test_component_access_helpers.py`
- **Best Practices:** See `docs/COMPONENT_TYPE_BEST_PRACTICES.md`

---

## 📞 Questions?

**Q: Do I always need to use the helpers?**  
A: Yes! Consistency is key. Old patterns should be considered deprecated.

**Q: What if I'm not sure if a component is required or optional?**  
A: Ask yourself: "If this component is missing, is that a bug?" If yes → `require_component()`. If no → `get_component_optional()`.

**Q: Can I still use `.components.get()` directly?**  
A: Discouraged. The helpers provide better error messages and clearer intent.

**Q: What about attribute access (`.fighter`, `.inventory`)?**  
A: Being phased out. Use ComponentType-based access for consistency.

---

**Last Updated:** October 10, 2025  
**Next Review:** After Phase 1 completion

