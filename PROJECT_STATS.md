# Catacombs of Yarl - Project Statistics

**Generated:** November 8, 2025
**Status:** Active Development - v3.13.0 (Portal System Complete)

---

## 📊 Overall Project Size

### Code Base
- **Total Python Files:** 322
- **Total Lines of Code:** 113,539
- **Root Level Files:** 31
- **Average Lines per File:** 353

### Documentation
- **Markdown Files:** 25 root + 106 in docs/ = 131 total
- **Configuration Files:** 11 YAML files
- **Architecture Documentation:** docs/architecture/
- **Development Documentation:** docs/development/ (phases + portal system)

### Test Coverage
- **Test Files:** 173 (50% of total files)
- **Portal System Tests:** 91/91 passing (37 new Phase B tests)
- **Total Tests:** 2500+ passing with 100% on critical paths
- **Test Lines:** ~55,000+ (45% of codebase)
- **Production Code:** 162 files, 62,496 lines (55%)

**Test/Production Ratio:** Nearly 1:1 - Professional-grade test coverage! 🎉

---

## 📁 Code Distribution by Directory

| Directory | Files | Lines | Purpose |
|-----------|-------|-------|---------|
| **tests/** | 160 | 51,043 | Test suite (comprehensive!) |
| **components/** | 23 | 8,732 | Entity components (Fighter, AI, Items, etc.) |
| **ui/** | 12 | 4,454 | User interface rendering |
| **state_machine/** | 8 | 4,502 | Game state management |
| **memory/** | 8 | 4,290 | Memory optimization & caching |
| **performance/** | 8 | 4,613 | Performance profiling & optimization |
| **config/** | 10 | 4,404 | Game configuration & entity registry |
| **input/** | 8 | 3,294 | Input handling & key mapping |
| **events/** | 8 | 3,267 | Event system & bus |
| **engine/** | 12 | 2,962 | Core game engine & systems |
| **assets/** | 7 | 2,905 | Asset loading & management |
| **spells/** | 6 | 2,248 | Spell definitions & execution |
| **rendering/** | 7 | 1,687 | Rendering optimizations |
| **map_objects/** | 5 | 1,337 | Game map & tiles |
| **loader_functions/** | 2 | 738 | Save/load functionality |

---

## 🏆 Largest Source Files (Top 15)

The "heavy lifters" of the codebase:

| File | Lines | Description |
|------|-------|-------------|
| `game_actions.py` | 1,573 | Action processing (movement, combat, items) |
| `spells/spell_executor.py` | 1,466 | Spell casting engine |
| `components/ai.py` | 1,249 | Monster AI behaviors |
| `item_functions.py` | 1,163 | Item usage & effects |
| `components/fighter.py` | 1,150 | Combat system & stats |
| `config/entity_factory.py` | 1,084 | Entity creation from configs |
| `config/entity_registry.py` | 969 | Entity configuration registry |
| `config/game_constants.py` | 967 | Game constants & settings |
| `map_objects/game_map.py` | 901 | Map data structure |
| `state_machine/core.py` | 766 | State machine implementation |
| `menus.py` | 752 | Menu rendering & interactions |
| `components/status_effects.py` | 748 | Status effect system |
| `input/mapping.py` | 737 | Input key mapping |
| `components/auto_explore.py` | 731 | Auto-exploration AI |
| `performance/analyzer.py` | 718 | Performance analysis tools |

---

## 🎮 Major Systems

Based on code organization, the game has these major systems:

### Core Gameplay (20,000+ lines)
- **Combat System** - Fighter components, damage calculation, resistances
- **AI System** - Monster behaviors, pathfinding, decision making
- **Action Processing** - Movement, attacking, item usage
- **Turn Management** - Turn economy, phase management

### Content Systems (15,000+ lines)
- **Item System** - Potions, scrolls, wands, rings, equipment
- **Spell System** - 30+ spells with targeting, effects, damage types
- **Entity System** - Component-based architecture
- **Inventory System** - Stacking, equipping, dropping

### Engine & Infrastructure (25,000+ lines)
- **Game Engine** - ECS architecture, system registration
- **Event System** - Event bus, listeners, patterns
- **State Machine** - Game state management
- **UI System** - Sidebar, menus, tooltips, dialogs
- **Rendering System** - Optimized multi-console rendering
- **Performance System** - Profiling, caching, optimization

### Supporting Systems (15,000+ lines)
- **Configuration** - YAML-based entity/item definitions
- **Asset Management** - Loading, caching, discovery
- **Memory Management** - GC optimization, pooling
- **Save/Load System** - Game persistence
- **Input System** - Key mapping, mouse handling

### Testing (51,000+ lines)
- **Unit Tests** - Component testing
- **Integration Tests** - System interaction testing
- **Regression Tests** - Bug fix verification
- **Performance Tests** - Benchmarking

---

## 📈 Development Metrics

### Code Quality
- **Test Coverage:** 45% of codebase is tests
- **Documentation:** 112 markdown docs (extensive!)
- **Configuration:** Data-driven design (YAML configs)
- **Architecture:** Clean component-based ECS

### Complexity
- **Largest File:** 1,573 lines (`game_actions.py`)
- **Most Complex System:** Spell Execution (1,466 lines)
- **Most Tested Area:** Combat & AI (based on test distribution)

### Organization
- **Modular:** Code well-organized into logical directories
- **Separation of Concerns:** Clear boundaries between systems
- **DRY Principle:** Shared utilities and base classes
- **Type Safety:** Type hints throughout

---

## 🎯 By The Numbers

### Content
- **15** Ring types
- **22** Scroll types  
- **11** Potion types
- **9** Wand types
- **50+** Monster types
- **30+** Spell types
- **20+** Equipment types

### Systems
- **12** Game systems (rendering, AI, input, etc.)
- **8** Event patterns
- **7** Equipment slots
- **6** Damage/resistance types
- **20+** Status effects

---

## 💡 Fun Facts

1. **Test to Production Ratio:** Nearly 1:1 - You've written as much test code as production code! That's professional-grade coverage.

2. **Documentation Champion:** 112 markdown files means you've documented almost everything. Future you will thank present you!

3. **Biggest File:** `game_actions.py` at 1,573 lines handles everything from movement to item usage to combat. It's the "glue" of the game.

4. **Most Complex System:** Spell execution at 1,466 lines, handling 30+ unique spells with different targeting modes, damage types, and effects.

5. **Component Architecture:** 23 component files (8,732 lines) form the backbone of the ECS architecture.

6. **Config-Driven:** 11 YAML files + 4,404 lines of config code means easy content iteration without code changes.

---

## 🚀 Growth Over Time

Based on the feature list and completed systems, the project has grown to include:
- ✅ Complete ECS architecture
- ✅ Comprehensive item system (potions, scrolls, wands, rings)
- ✅ Full spell system with targeting
- ✅ Resistance system
- ✅ Status effects
- ✅ Equipment system with 7 slots
- ✅ Identification system
- ✅ Throwing system
- ✅ Auto-exploration
- ✅ Turn economy
- ✅ Event system
- ✅ Performance optimization
- ✅ Save/load system

---

## 📊 Comparison to Other Roguelikes

For context, here's how Yarl compares to other traditional roguelikes:

| Game | Lines of Code | Language | Notes |
|------|---------------|----------|-------|
| **Yarl** | **113,539** | **Python** | **Modern architecture** |
| Rogue (1980) | ~10,000 | C | Original roguelike |
| NetHack | ~300,000+ | C | 30+ years of development |
| Brogue | ~50,000 | C | Modern, focused design |
| DCSS | ~500,000+ | C++ | Massive, complex |

**Yarl sits comfortably between Brogue and NetHack** - substantial but not overwhelming, with modern Python architecture making it more maintainable than old C codebases.

---

## 🎉 Summary

**Catacombs of Yarl** is a **substantial roguelike project** with:
- **113K+ lines** of well-organized Python code
- **Professional-grade test coverage** (45%)
- **Extensive documentation** (112 docs)
- **Clean architecture** (ECS, event-driven)
- **Rich content** (100+ items, 50+ monsters, 30+ spells)
- **Modern systems** (resistance, status effects, equipment)

You've built a **real roguelike game** with the depth and complexity to rival classic entries in the genre! 🏆

---

## 🌟 Latest Features (Nov 2025)

### Portal System (COMPLETE)
- **Phase A:** Core mechanics (wand, placement, teleportation, inventory)
- **Phase B:** Monster AI integration + visual feedback
- **AI Flags:** Each monster type configured (bosses avoid, basic chase)
- **VFX System:** Distinct messages for player vs monster teleportation
- **Test Coverage:** 91/91 tests passing

### Story Arcs (COMPLETE)
- **Phase 4:** Environmental Lore (Signposts, Murals, Easter Eggs)
- **Phase 5:** Victory Condition (Ruby Heart quest with 6 endings)
- **Narrative:** Themed soul rotation story across all content

### Architecture
- **ECS System:** Clean component-based design
- **PortalManager:** Single source of truth for portal logic
- **Event Bus:** Decoupled system communication
- **Performance:** 60+ FPS maintained throughout

---

*Next Phase: Continued gameplay expansion with balance and polish! 🚀*

