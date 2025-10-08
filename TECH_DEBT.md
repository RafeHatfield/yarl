# 🔧 Tech Debt Tracker

**Purpose:** Ongoing tracking of technical debt, code smells, and optimization opportunities  
**Last Updated:** October 2025  
**Status:** 🔴 3 Critical Items | 🟡 3 High-Priority Items | 🟢 8 Nice-to-Have Items

---

## 🔴 **CRITICAL** (Blocking Roadmap Features)

### **#1: Component System Refactor** 
**Status:** 🔴 TODO | **Priority:** P0 | **Effort:** 3 days | **Blocks:** Magic Schools, Skill Trees, Perks

**Problem:**
- 121 `hasattr()` checks across 28 files
- No type safety, verbose boilerplate
- Hard to query "all entities with X component"
- No component lifecycle management

**Solution:** Component Registry Pattern with type-safe lookups

**Progress:**
- [ ] Design ComponentRegistry class
- [ ] Implement component type enum
- [ ] Refactor Entity class to use registry
- [ ] Update all hasattr() calls (~30 files)
- [ ] Add component query methods
- [ ] Update tests
- [ ] Verify all 1,855 tests pass

**Branch:** `refactor/component-registry`  
**Tracking Issue:** #1

---

### **#2: Item/Spell System Consolidation**
**Status:** 🔴 TODO | **Priority:** P0 | **Effort:** 4 days | **Blocks:** New Spells, Magic Schools, Crafting

**Problem:**
- `item_functions.py` is 1,242 lines
- Adding spell = 5+ file changes
- Duplication: scrolls, wands, tooltips, monster AI

**Solution:** Spell Registry - define once, use everywhere

**Progress:**
- [ ] Design SpellRegistry and Spell dataclass
- [ ] Create spell definitions (20+ spells)
- [ ] Refactor item_functions.py to use registry
- [ ] Update entity_factory to reference spells
- [ ] Update tooltips to use spell metadata
- [ ] Consolidate wand/scroll creation
- [ ] Update tests

**Branch:** `refactor/spell-registry`  
**Tracking Issue:** #2

---

### **#3: Turn Processing Unification**
**Status:** 🔴 TODO | **Priority:** P0 | **Effort:** 5 days | **Blocks:** Reactions, Initiative, Time Magic

**Problem:**
- Turn logic scattered across 4 systems
- Hard to add turn-based effects
- No concept of simultaneous actions
- No initiative/speed system

**Solution:** TurnManager with event listeners

**Progress:**
- [ ] Design TurnManager class
- [ ] Design TurnListener interface
- [ ] Refactor AISystem to use TurnManager
- [ ] Move hazard processing to TurnListener
- [ ] Update pathfinding turn logic
- [ ] Add turn event hooks
- [ ] Update tests

**Branch:** `refactor/turn-manager`  
**Tracking Issue:** #3

---

## 🟡 **HIGH PRIORITY** (Maintainability & Quality)

### **#4: Extract Game Constants to YAML**
**Status:** 🟡 TODO | **Priority:** P1 | **Effort:** 1 day

**Problem:**
- `game_constants.py` is 671 lines of hardcoded values
- Balance changes require code changes
- No modding support

**Solution:** YAML files for numeric constants, keep code for configs

**Files to Extract:**
- Combat values (damage, AC, HP scaling)
- Item spawn rates
- Monster stats
- Spell parameters
- Map generation values

**Progress:**
- [ ] Design YAML schema
- [ ] Create constants/ directory
- [ ] Extract combat.yaml
- [ ] Extract items.yaml
- [ ] Extract monsters.yaml
- [ ] Update loader to read YAML
- [ ] Add validation
- [ ] Update tests

---

### **#5: Split item_functions.py**
**Status:** 🟡 TODO | **Priority:** P1 | **Effort:** 1 day

**Problem:**
- 1,242 lines in a single file
- Hard to navigate
- Spells mixed with consumables mixed with equipment

**Solution:** Split into organized modules

**New Structure:**
```
item_functions/
├── __init__.py
├── spells/
│   ├── __init__.py
│   ├── evocation.py    # Fireball, Lightning
│   ├── conjuration.py  # Dragon Fart
│   ├── enchantment.py  # Confusion
│   └── transmutation.py # Enhance, Teleport
├── consumables/
│   ├── __init__.py
│   ├── healing.py
│   └── buffs.py
└── equipment/
    ├── __init__.py
    └── enhancements.py
```

**Progress:**
- [ ] Create directory structure
- [ ] Split spells by school
- [ ] Split consumables by type
- [ ] Update imports
- [ ] Update tests
- [ ] Delete old item_functions.py

---

### **#6: Add Component Type Hints**
**Status:** 🟡 TODO | **Priority:** P1 | **Effort:** 2 days

**Problem:**
- Components are plain classes
- No IDE autocomplete
- Type errors only at runtime

**Solution:** Add `@dataclass` decorators and full type hints

**Components to Update:**
- [x] Fighter ✅
- [x] AI (partially) ✅
- [ ] Inventory
- [ ] Equipment
- [ ] Equippable
- [ ] Level
- [ ] Item
- [ ] StatusEffectManager
- [ ] PlayerPathfinding
- [ ] Wand

**Progress:**
- [ ] Add dataclass to remaining components
- [ ] Add proper type hints
- [ ] Run mypy for type checking
- [ ] Fix type errors
- [ ] Update tests

---

## 🟢 **NICE TO HAVE** (Code Quality)

### **#7: Reduce entity.py Complexity**
**Status:** 🟢 TODO | **Priority:** P2 | **Effort:** 2 days

**Problem:**
- `entity.py` has complex pathfinding logic (100+ lines)
- `move_astar()` is 80 lines with hazard costs
- Hard to test pathfinding separately

**Solution:** Extract PathfindingSystem or PathfindingHelper

---

### **#8: Consolidate Message Logging**
**Status:** 🟢 TODO | **Priority:** P2 | **Effort:** 1 day

**Problem:**
- `Message()` calls scattered everywhere
- Inconsistent formatting
- No message categories

**Solution:** MessageBuilder pattern with categories

```python
MessageBuilder.combat("You hit the Orc for 10 damage!")
MessageBuilder.item("You pick up the Sword!")
MessageBuilder.system("Game saved successfully.")
```

---

### **#9: Extract UI Layout Constants**
**Status:** 🟢 TODO | **Priority:** P2 | **Effort:** 1 day

**Problem:**
- UI layout calculations in multiple files
- Tooltip positioning has magic numbers
- Sidebar coordinates hardcoded

**Solution:** UILayoutConfig with named regions

---

### **#10: Add Performance Profiling**
**Status:** 🟢 TODO | **Priority:** P2 | **Effort:** 2 days

**Problem:**
- No visibility into performance bottlenecks
- Can't measure optimization impact

**Solution:** Add profiling decorators and performance dashboard

---

### **#11: Standardize Error Handling**
**Status:** 🟢 TODO | **Priority:** P2 | **Effort:** 1 day

**Problem:**
- Mix of try/except, hasattr, and silent failures
- Errors logged inconsistently

**Solution:** Define error handling strategy per system

---

### **#12: Extract Map Generation Logic**
**Status:** 🟢 TODO | **Priority:** P2 | **Effort:** 3 days

**Problem:**
- Map generation is monolithic
- Hard to add new room types
- Difficult to test

**Solution:** Room generator pattern with pluggable generators

---

### **#13: Add Integration Test Suite**
**Status:** 🟢 TODO | **Priority:** P2 | **Effort:** 2 days

**Problem:**
- 1,855 unit tests, but few integration tests
- Can't test multi-system interactions

**Solution:** Add scenario-based integration tests

---

### **#14: Document Core Systems**
**Status:** 🟢 TODO | **Priority:** P2 | **Effort:** 2 days

**Problem:**
- No architecture docs
- New contributors struggle to understand systems

**Solution:** Add docs/ folder with system documentation

---

## 📊 **Metrics to Track**

### **Code Quality Metrics**
- [ ] Lines of code per file (target: <500)
- [ ] Cyclomatic complexity (target: <10 per function)
- [ ] Test coverage (current: 98.9%, maintain >95%)
- [ ] Number of hasattr() calls (current: 121, target: <50 after #1)
- [ ] Longest file (current: 1,242 lines, target: <800)

### **Development Velocity Metrics**
- [ ] Time to add new spell (current: ~2 hours, target: <30 min after #2)
- [ ] Time to add new component (current: ~3 hours, target: <30 min after #1)
- [ ] Time to add new turn effect (current: ~4 hours, target: <1 hour after #3)

### **Test Metrics**
- [ ] Test suite runtime (current: ~20 seconds, maintain <30s)
- [ ] Test failures per PR (target: 0)
- [ ] New tests per feature (target: >5 per feature)

---

## 🔄 **Review Cadence**

### **Weekly Review** (Every Monday)
- Review P0/P1 items
- Update progress
- Adjust priorities based on roadmap

### **Monthly Review** (First Monday of Month)
- Assess metrics
- Add new tech debt items
- Archive completed items
- Celebrate wins! 🎉

### **Quarterly Review** (January, April, July, October)
- Major architecture decisions
- Long-term refactoring plans
- Tech debt vs feature balance

---

## 📋 **Quick Reference**

### **How to Add New Tech Debt Item**
1. Add to appropriate section (🔴 🟡 🟢)
2. Fill in: Status, Priority, Effort, Problem, Solution
3. Add progress checklist
4. Assign tracking issue number
5. Commit with: `docs: Add tech debt item #N`

### **How to Complete Tech Debt Item**
1. Create feature branch
2. Work through progress checklist
3. Ensure all tests pass
4. Create PR referencing tracking issue
5. After merge: Move to COMPLETED section
6. Update metrics

### **Priority Levels**
- **P0 (Critical):** Blocking roadmap features - do ASAP
- **P1 (High):** Impacts maintainability - do within 1-2 sprints
- **P2 (Medium):** Code quality - do when capacity allows
- **P3 (Low):** Nice to have - backlog

---

## ✅ **COMPLETED** (Archive)

### **Component System Refactor** 
**Completed:** TBD | **Branch:** `refactor/component-registry`  
*Details moved to archive after completion*

---

**Last Review:** October 2025  
**Next Review:** [Schedule weekly review]  
**Owner:** Development Team
