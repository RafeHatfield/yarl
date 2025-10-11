# 🔧 Tech Debt Analysis & Refactoring Roadmap

**Date:** October 2025  
**Context:** 275 commits in last 3 months, 1,855 passing tests, 19,579 lines of game code  
**Goal:** Identify top 3 refactors to enable future roadmap expansion

---

## 📊 **Codebase Health Metrics**

### **Current State**
- **Test Coverage:** 98.9% (1,855 tests passing)
- **Largest Files:** 
  - `item_functions.py`: 1,242 lines
  - `game_actions.py`: 1,103 lines
  - `entity_registry.py`: 900 lines
- **Code Smell Alert:** 121 `hasattr()` checks across 28 files
- **Development Velocity:** 275 commits in 3 months (high velocity = accumulating debt)

### **Architecture Overview**
```
✅ GOOD: Entity-Component-System (ECS) architecture
✅ GOOD: System-based engine (Render, AI, Input, Performance)
✅ GOOD: Clean separation of concerns in most areas
⚠️  CONCERN: Component lookups are manual (hasattr everywhere)
⚠️  CONCERN: Item/spell system has significant duplication
⚠️  CONCERN: Turn processing logic is scattered
```

---

## 🎯 **Top 3 Tech Debt Items** (Priority Order)

---

## **#1: Component System Refactor** ⭐⭐⭐ CRITICAL

### **The Problem**
The component system is implemented as **manual attribute lookups** rather than a proper registry:

```python
# Current pattern (found 121 times!)
if hasattr(entity, 'fighter') and entity.fighter:
    if entity.fighter.hp > 0:
        # do something...

if hasattr(entity, 'inventory') and entity.inventory:
    entity.inventory.add_item(item)
```

**Issues:**
- ❌ No type safety - typos silently fail
- ❌ Verbose boilerplate everywhere
- ❌ Difficult to query "all entities with Fighter component"
- ❌ No component lifecycle management
- ❌ Hard to add new components (change 20+ files)

### **What It Blocks on Roadmap**
- **Magic Schools** (Phase 3) - Need MagicSchool component
- **Skill Trees** (Phase 3) - Need Skills component  
- **Perks & Traits** (Phase 4) - Need Perks component
- **Multi-classing** (Phase 5) - Need multiple Class components
- **Status Effects** (already painful) - Better component querying
- **Any new component type** - Adds more hasattr checks

### **Recommended Solution: Component Registry Pattern**

```python
# AFTER: Clean component registry
class Entity:
    def __init__(self, x, y, char, color, name):
        self.components = ComponentRegistry()
        # ... setup ...
    
    def add_component(self, component_type, component):
        """Type-safe component addition."""
        self.components.add(component_type, component)
        component.owner = self
    
    def get_component(self, component_type):
        """Type-safe component lookup."""
        return self.components.get(component_type)
    
    def has_component(self, component_type):
        """Fast component check."""
        return component_type in self.components

# Usage becomes clean and type-safe
if entity.has_component(Fighter):
    fighter = entity.get_component(Fighter)
    if fighter.hp > 0:
        # do something...

# System can query for entities with specific components
fighters = world.query_entities(Fighter, AI)  # All monsters
```

**Benefits:**
- ✅ Type-safe (IDE autocomplete, type checking)
- ✅ Single line to add new component types
- ✅ Fast queries: "all entities with Fighter + AI"
- ✅ Lifecycle hooks (on_add, on_remove, on_update)
- ✅ Reduces 121 hasattr() calls to ~30 clean checks

**Implementation Estimate:** 
- **Time:** 2-3 days
- **Risk:** Medium (touches many files, but tests will catch breaks)
- **Files Changed:** ~30 files
- **Lines Changed:** ~400 lines (net reduction after cleanup)

---

## **#2: Item/Spell System Consolidation** ⭐⭐⭐ HIGH

### **The Problem**
Spell and item logic is **duplicated across 5+ locations**:

1. **`item_functions.py`** (1,242 lines!) - Spell implementations
2. **`config/entity_factory.py`** - Spell-to-Item mapping for scrolls
3. **`config/entity_factory.py`** - Spell-to-Item mapping for wands (duplicate!)
4. **`ui/tooltip.py`** - Spell name mapping for tooltips
5. **`components/monster_item_usage.py`** - Item type detection
6. **`components/item.py`** - Generic Item component (no spell knowledge)

**Adding a new spell requires changes in 5+ files!**

Example: Adding "Ice Bolt" spell:
```python
# ❌ CURRENT: Must update 5 files
# 1. item_functions.py - add cast_ice_bolt()
# 2. entity_factory.py - add Ice Bolt scroll mapping
# 3. entity_factory.py - add Ice Bolt wand mapping  
# 4. tooltip.py - add ice_bolt detection
# 5. entity_registry.py - add Ice Bolt scroll definition
# 6. entity_registry.py - add Ice Bolt wand definition
```

### **What It Blocks on Roadmap**
- **New Spells** (Phase 2/3) - Currently painful to add
- **Spell Modifications** (Phase 3) - Empowered, Extended, etc.
- **Magic Schools** (Phase 3) - Need spell categorization
- **Wand Variations** (Phase 3) - Different wand types
- **Consumable Items** (Phase 3) - Potions, food, oils
- **Crafting System** (Phase 4) - Combine items to create new ones
- **Spell Combos** (Phase 5) - Cast multiple spells together

### **Recommended Solution: Spell Registry + Item Types**

```python
# AFTER: Unified spell system
class SpellRegistry:
    """Central registry for all spells."""
    _spells = {}
    
    @classmethod
    def register(cls, spell_id: str, spell: Spell):
        cls._spells[spell_id] = spell
    
    @classmethod
    def get(cls, spell_id: str) -> Spell:
        return cls._spells.get(spell_id)

@dataclass
class Spell:
    """Define a spell once, use everywhere."""
    id: str
    name: str
    description: str
    school: MagicSchool
    cast_function: Callable
    targeting: TargetingType
    damage: Optional[int] = None
    radius: Optional[int] = None
    duration: Optional[int] = None
    # ... other properties

# Register spells once in a central location
SpellRegistry.register("fireball", Spell(
    id="fireball",
    name="Fireball",
    description="Explosive fire magic",
    school=MagicSchool.EVOCATION,
    cast_function=cast_fireball_impl,
    targeting=TargetingType.AREA,
    damage=20,
    radius=3
))

# Items reference spells by ID
scroll = entity_factory.create_scroll("fireball")  # That's it!
wand = entity_factory.create_wand("fireball", charges=5)  # That's it!

# Tooltips are automatic
tooltip = spell.get_tooltip()  # "Evocation: Fireball (20 damage, 3 radius)"
```

**Benefits:**
- ✅ Add new spell = 1 registry entry (not 5+ file changes)
- ✅ Single source of truth for spell properties
- ✅ Easy to query spells by school/type
- ✅ Automatic tooltip generation
- ✅ Enables spell modification system
- ✅ Reduces item_functions.py from 1,242 → ~600 lines

**Implementation Estimate:**
- **Time:** 3-4 days
- **Risk:** Medium-High (changes core item system)
- **Files Changed:** ~15 files
- **Lines Changed:** ~800 lines (net reduction after consolidation)

---

## **#3: Turn Processing Unification** ⭐⭐ MEDIUM

### **The Problem**
Turn processing logic is **scattered across 4 systems**:

1. **`engine/systems/ai_system.py`** - Enemy turns, hazard processing
2. **`game_actions.py`** - Player actions, state transitions
3. **`mouse_movement.py`** - Pathfinding turns, interrupts
4. **`engine_integration.py`** - Turn coordination

**Current flow is complex:**
```
Player Action → ActionProcessor → State Change → AISystem Update →
  → AI Turn → Hazard Turn → Pathfinding Check → Back to Player
```

**Issues:**
- ❌ Difficult to add turn-based effects (regeneration, poison ticks)
- ❌ No concept of "simultaneous actions"
- ❌ Hard to implement reactions/interrupts
- ❌ Initiative system would be very complex
- ❌ Time-based effects are bolted on (hazards in AISystem?)

### **What It Blocks on Roadmap**
- **Reactions** (Phase 3) - "Attack of Opportunity" when enemy moves
- **Initiative System** (Phase 3) - Faster monsters get more turns
- **Simultaneous Actions** (Phase 4) - Roguelike simultaneous turn mode
- **Time-Based Magic** (Phase 4) - Haste/Slow affecting turn order
- **Status Effect Ticks** (current) - Poison damage per turn
- **Environmental Effects** (current) - Hazard ticks per turn
- **Complex Turn Actions** (Phase 5) - Multiple actions per turn

### **Recommended Solution: Turn Manager System**

```python
class TurnManager:
    """Unified turn processing system."""
    
    def __init__(self):
        self.turn_queue = []  # Priority queue for initiative
        self.turn_listeners = []  # Subscribe to turn events
        self.current_turn = None
    
    def process_turn(self, entity):
        """Process a single entity's turn."""
        self.current_turn = entity
        
        # 1. Notify turn start listeners
        self._notify_turn_start(entity)
        
        # 2. Process pre-turn effects (regeneration, poison ticks)
        self._process_start_of_turn_effects(entity)
        
        # 3. Execute entity action (AI or player input)
        action_result = self._execute_entity_action(entity)
        
        # 4. Process reactions/interrupts
        self._process_reactions(entity, action_result)
        
        # 5. Process end-of-turn effects
        self._process_end_of_turn_effects(entity)
        
        # 6. Notify turn end listeners
        self._notify_turn_end(entity)
        
        self.current_turn = None
    
    def add_turn_listener(self, listener: TurnListener):
        """Subscribe to turn events (for hazards, effects, etc.)."""
        self.turn_listeners.append(listener)

# Usage is clean
turn_manager = TurnManager()

# Hazards listen to turns
turn_manager.add_turn_listener(HazardSystem())

# Status effects listen to turns
turn_manager.add_turn_listener(StatusEffectSystem())

# Initiative determines order
turn_manager.set_initiative_order(entities)
```

**Benefits:**
- ✅ Single source of truth for turn processing
- ✅ Easy to add turn-based effects (just add listener)
- ✅ Enables initiative/speed system
- ✅ Supports reactions and interrupts
- ✅ Clean separation: TurnManager orchestrates, Systems execute
- ✅ Easier to test turn-based behavior

**Implementation Estimate:**
- **Time:** 4-5 days
- **Risk:** High (core game loop changes)
- **Files Changed:** ~20 files
- **Lines Changed:** ~600 lines (refactor existing)

---

## 📈 **Impact Analysis**

### **If We Fix These 3 Items:**

| Roadmap Feature | Without Fixes | With Fixes |
|----------------|---------------|------------|
| **Magic Schools** | Very Hard (hasattr + spell duplication) | Easy (component + spell registry) |
| **New Spells** | Hard (5+ file changes) | Trivial (1 registry entry) |
| **Skill Trees** | Hard (manual component checks) | Easy (component queries) |
| **Status Effects** | Medium (scattered logic) | Easy (turn listeners) |
| **Initiative System** | Very Hard (refactor turns first) | Medium (turn manager ready) |
| **Reactions** | Very Hard (no interrupt system) | Easy (turn manager hooks) |
| **Multi-classing** | Very Hard (component chaos) | Easy (component system) |

---

## 🎯 **Recommended Implementation Order**

### **Phase 1: Foundation (Week 1-2)**
1. ✅ **Component System Refactor** (3 days)
   - Enables all future component additions
   - Lowest risk, highest ROI
   - Do this FIRST

### **Phase 2: Content System (Week 3)**
2. ✅ **Spell System Consolidation** (4 days)
   - Unlocks rapid spell/item development
   - Medium risk, high reward
   - Do BEFORE adding new spells

### **Phase 3: Turn System (Week 4-5)**
3. ✅ **Turn Processing Unification** (5 days)
   - Enables advanced turn-based features
   - Highest risk, but necessary for roadmap
   - Do BEFORE initiative/reactions

---

## 💡 **Quick Wins** (Bonus Items)

These didn't make top 3 but are worth mentioning:

### **#4: Extract Game Constants to YAML** (1 day, low risk)
- `config/game_constants.py` is 671 lines
- Move numeric constants to YAML for easier balancing
- Enables modding support

### **#5: Split item_functions.py** (1 day, low risk)
- Currently 1,242 lines in one file
- Split into: `spells/`, `consumables/`, `equipment_effects/`
- Easier navigation and maintenance

### **#6: Add Component Type Hints** (2 days, low risk)
- Add `@dataclass` to all components
- Enables better IDE support
- Catches bugs at type-check time

---

## 🎯 **Conclusion**

All 3 tech debt items are **architectural blockers** for your roadmap. The good news:

✅ Your test suite (1,855 tests) will catch breaks during refactoring  
✅ Your ECS foundation is solid - we're just formalizing patterns  
✅ Total time investment: ~2 weeks  
✅ **ROI: Enables 2+ years of feature development**  

### **My Recommendation:**

**Do all 3 refactors in sequence BEFORE Phase 3 of the roadmap.**

You've been building at high velocity (275 commits / 3 months), and the codebase is accumulating complexity. Taking 2 weeks now to solidify the architecture will:

1. **Speed up future development** (new features take hours instead of days)
2. **Reduce bugs** (type safety, single source of truth)
3. **Enable ambitious features** (magic schools, initiative, reactions)
4. **Make the codebase more maintainable** (onboarding, debugging)

The alternative is continuing to accumulate debt until it becomes **impossible to implement advanced features** without a full rewrite.

---

**Questions? Let's discuss which one to tackle first!** 🚀
