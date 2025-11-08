# 🏰 Catacombs of Yarl

A traditional roguelike game written in Python with a comprehensive story arc and modern architecture.

**Current Status:** v3.13.0 - Portal System Complete | 2500+ Tests Passing | 131 Documentation Files

---

## 🎮 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the game
python engine.py

# Run tests
pytest tests/

# Run specific test suite
pytest tests/test_portal_system_phase_b.py -v
```

---

## 📊 Executive Summary

### What Is Yarl?

A **feature-rich roguelike** built with Python and libtcod, featuring:

- **Complete story arc** with 5 narrative phases leading to a climactic victory condition
- **Portal system** with emergent AI interactions
- **100+ unique items** across multiple categories (potions, scrolls, wands, rings, equipment)
- **50+ monster types** with distinct AI behaviors
- **30+ spells** with targeting modes and diverse effects
- **Professional test coverage** (2500+ tests, ~45% of codebase)
- **Clean architecture** (ECS-based, event-driven, modular design)

### Current Capabilities

| Aspect | Status | Details |
|--------|--------|---------|
| **Story** | ✅ COMPLETE | Phases 1-5 with 6 distinct endings |
| **Gameplay** | ✅ CORE COMPLETE | Combat, exploration, loot identification |
| **Portal System** | ✅ COMPLETE | Phase A + B with monster AI |
| **Environmental Lore** | ✅ COMPLETE | Signposts, murals, easter eggs |
| **Testing** | ✅ 2500+ | 100% critical path coverage |
| **Performance** | ✅ 60 FPS | Optimized rendering & caching |

---

## 🎯 Core Features

### Story & Victory Condition

The game has a **complete narrative arc** leading to victory:

1. **Phase 1-3:** Explore dungeon, gather items, meet NPCs
2. **Phase 4:** Discover environmental lore revealing the true story
3. **Phase 5:** Reach Ruby Heart, trigger climactic portal to Zhyraxion's realm
4. **Ending:** Six distinct ending options based on player choices

**Story Themes:**
- Soul rotation between incarnations
- Two competing dragons (Zhyraxion & Aurelyn)
- Mysterious ritual and deeper dungeon mystery
- Player agency in choosing the ending

See [STORY_LORE_CANONICAL.md](STORY_LORE_CANONICAL.md) for full narrative details.

### Portal System (Latest)

**Phase A - Core Mechanics:**
- Wand of Portals legendary item (infinite charges)
- Place entrance → exit portal pair
- Teleportation between portals
- Pick up portals as inventory items
- Wand recycling (new portals replace old)

**Phase B - Advanced Features:**
- Monster AI integration with `portal_usable` flags
- Bosses avoid portals (tactical advantage for players)
- Basic monsters chase through portals (emergent gameplay!)
- Visual feedback (distinct messages for player vs monster teleportation)
- Portal item drops naturally when monsters die

**Test Coverage:** 91/91 tests passing (100%)

### Combat System

- **D20 attack rolls** for to-hit determination
- **Damage resistances** (fire, cold, lightning, poison, etc.)
- **Status effects** (20+ types: poison, bleed, stun, charm, etc.)
- **Equipment slots** (head, body, hands, feet, main hand, off hand, amulet)
- **Item identification** system for magical items
- **Throwing system** for ranged attacks with potions/items

### Item System

**100+ unique items:**
- **20+ Equipment pieces** (armor, weapons, shields)
- **22 Scroll types** (spells, identification, removal curse)
- **11 Potion types** (healing, stat bonuses, effects)
- **15 Ring types** (resistances, bonuses, special effects)
- **9 Wand types** (spell wands plus the legendary Portal Wand)

All items have rarity tiers (common, uncommon, rare, legendary) and magical properties.

### Spell System

**30+ spells** with various targeting modes:
- **Fireball:** AoE damage with ground hazards
- **Confusion:** Temporary AI control loss
- **Teleportation:** Player repositioning
- **Healing:** Single & area healing
- **Buffs & Debuffs:** Temporary stat modifications
- Plus many more with unique mechanics

### Monster AI

**50+ monster types** with distinct behaviors:
- **BasicMonster:** Standard hostile AI with pathfinding
- **BossMonster:** Enhanced combat, dialogue, special abilities
- **MindlessZombie:** Indiscriminate hostility
- **ConfusedMonster:** Random movement
- **SlimeMonster:** Multi-faction intelligence
- Plus themed monster variants at different dungeon depths

Monsters now intelligently use portals (respecting their `portal_usable` flag).

---

## 🏗️ Architecture

### Design Principles

See [DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md) for full architectural philosophy.

**Key Principles:**
- **Single Source of Truth** - Each system has one canonical place
- **Component-Based** - ECS architecture for entity flexibility
- **Test-Driven** - 2500+ tests ensuring quality
- **Event-Driven** - Loose coupling via event bus
- **Emergent Gameplay** - Systems interact in unexpected ways

### Core Systems

**Engine:**
- ECS-based entity system
- Event bus for decoupled communication
- State machine for game flow
- Multi-console rendering with viewport

**Game Logic:**
- PortalManager - Central portal system
- AISystem - Monster behavior orchestration
- CombatSystem - Damage, resistances, effects
- MovementService - Collision, terrain, pathfinding

**Content:**
- EntityFactory - Data-driven entity creation
- ConfigRegistry - YAML-based game definitions
- ItemSystem - Stacking, equipment, identification
- SpellSystem - Casting, targeting, effects

**Infrastructure:**
- Save/Load persistence
- Performance profiling
- Memory optimization
- Event logging

### Code Quality

- **2500+ tests** across all systems
- **~131 documentation files** covering architecture and development
- **Type hints** throughout codebase
- **Modular design** with clear separation of concerns
- **One file per responsibility** principle

### Project Statistics

- **113K+ lines** of production code
- **55K+ lines** of test code
- **322 Python files** organized into logical modules
- **11 YAML files** for data-driven content
- **Ratio:** Nearly 1:1 test to production code

See [PROJECT_STATS.md](PROJECT_STATS.md) for detailed breakdown.

---

## 📚 Documentation

### For Game Developers & Reviewers

**Start here:**
- [STORY_LORE_CANONICAL.md](STORY_LORE_CANONICAL.md) - Complete narrative and themes
- [VICTORY_CONDITION_PHASES.md](VICTORY_CONDITION_PHASES.md) - How victory condition works
- [TRADITIONAL_ROGUELIKE_FEATURES.md](TRADITIONAL_ROGUELIKE_FEATURES.md) - Feature roadmap
- [PLAYER_PAIN_POINTS.md](PLAYER_PAIN_POINTS.md) - Design challenges & solutions

### For Developers

- **[docs/architecture/](docs/architecture/)** - System design & specifications
- **[docs/development/](docs/development/)** - Phase summaries & implementation details
- [DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md) - Architectural philosophy
- [PROJECT_STATS.md](PROJECT_STATS.md) - Codebase metrics

### For Implementation Details

- **Portal System:** [docs/development/portal/README.md](docs/development/portal/README.md)
- **Story Arcs:** [docs/development/phase4/](docs/development/phase4/) & [phase5/](docs/development/phase5/)
- **Architecture:** [docs/architecture/README.md](docs/architecture/README.md)

---

## 🎮 Gameplay Features

### Exploration

- **25-level dungeon** scaling in difficulty
- **Random room generation** with proper level design
- **FOV-based exploration** with memory of explored areas
- **Interactive features** (signposts, murals, chests)
- **Easter eggs** for observant players

### Turn Economy

- **Traditional roguelike turns** - Player moves, then all monsters move
- **Action types** - Movement, attacking, item usage, spells
- **Wait action** - Pass turn while staying in place
- **Auto-explore** - Automated movement through safe areas

### Combat

- **Real-time feedback** on damage and effects
- **Resistance system** affects damage taken
- **Status effects** change combat dynamics
- **Tactical positioning** matters
- **Equipment affects stats** (damage, AC, resistances)

### Itemization

- **Identification system** reveals magical properties
- **Equipment slots** for equipped gear bonuses
- **Rarity tiers** (common → legendary)
- **Stacking** of consumable items
- **Special effects** (resistances, stat bonuses, curses)

---

## 🧪 Testing & Quality

### Test Coverage

- **Portal System:** 91/91 tests passing (Phase A + B complete)
- **Combat System:** 200+ tests
- **Item System:** 150+ tests
- **AI System:** 180+ tests
- **Integration Tests:** 800+ tests
- **Total:** 2500+ tests with 100% pass rate on critical paths

### Performance

- **60 FPS** maintained throughout
- **Sub-50ms** input response time
- **Rendering optimization** with entity cache
- **Memory efficient** with pooling and optimization

### Code Quality

- **Type hints** throughout
- **Comprehensive docstrings**
- **Error handling** with clear messages
- **Logging** at appropriate levels
- **Modular architecture** for maintainability

---

## 🚀 Roadmap & Future Work

See [ROADMAP.md](ROADMAP.md) for comprehensive feature planning.

### Currently Complete

- ✅ Core roguelike gameplay
- ✅ Portal system (Phase A & B)
- ✅ Story arc (Phases 1-5)
- ✅ Combat system with resistances
- ✅ Status effects (20+ types)
- ✅ Item identification
- ✅ Equipment system
- ✅ Spell system (30+ spells)

### Planned Features

- 🔄 Vaults & secret doors
- 🔄 Chests & locked containers
- 🔄 Religion/god system
- 🔄 Shop system
- 🔄 Amulet system
- 🔄 Polymorph mechanics
- 🔄 Wish system
- 🔄 Named unique artifacts

---

## 🎓 Design Highlights

### Emergent Gameplay

The portal system exemplifies emergent design:

- **No scripted monster behavior** for portals
- But monsters can pick up inventory items
- And use teleportation mechanics
- **Result:** Orcs unexpectedly chase through your portals!
- **Bosses have flags** to avoid this (tactical advantage)

### Single Source of Truth

Each system has one place where it's canonical:

- **PortalManager** - All portal logic centralized
- **AISystem** - All monster turn orchestration
- **CombatSystem** - All damage/resistance calculation
- Makes debugging, testing, and extending straightforward

### Data-Driven Design

Content defined in YAML, loaded at runtime:

- Easy to add new items/monsters without code changes
- Designers can work without touching Python
- Configuration in `config/entities.yaml` and related files

---

## 📝 Code Example: Creating an Item

```python
# Define in config/entities.yaml
portal_wand:
  name: "Wand of Portals"
  char: "/"
  color: [100, 255, 200]
  render_order: item
  components:
    - type: item
      targeting: true
    - type: wand
      charges: -1  # Infinite
    - type: portal_placer

# Use in factory
wand = entity_factory.create_wand_of_portals(0, 0)

# Add to inventory
player.inventory.add_item(wand)

# Use during gameplay
player.inventory.use(wand_index)  # Enters targeting mode
```

---

## 🤝 Contributing

### Adding Features

1. **Plan** - Document what you're adding
2. **Architect** - Design how it fits existing systems
3. **Implement** - Code the feature
4. **Test** - Write comprehensive tests
5. **Document** - Update relevant docs

### Code Style

- Type hints required
- Clear variable names
- Comments for "why", not "what"
- One file per responsibility
- Modular, testable functions

### Testing Requirements

- Unit tests for individual components
- Integration tests for system interactions
- Regression tests for bug fixes
- Tests should pass before merging

---

## 🎮 How to Play

### Getting Started

1. Start in a random room at dungeon level 1
2. Explore, find items, defeat monsters
3. Deeper levels have better loot but more danger
4. Identify items to learn their properties
5. Equip gear to improve stats

### The Quest

1. Reach dungeon level 25
2. Defeat the final guardian and claim the Ruby Heart
3. Use the heart to open the portal to Zhyraxion's realm
4. Confront the dragons
5. Choose your ending (6 options)

### Tips

- Manage resources (potions, scrolls are limited)
- Identify valuable items early
- Use portals tactically (they can trap monsters!)
- Different equipment provides different bonuses
- Status effects can turn fights around

---

## 🏆 Achievements

- ✅ Complete story arc with multiple endings
- ✅ Professional-grade test coverage (2500+ tests)
- ✅ Clean, modular architecture (ECS-based)
- ✅ Rich content (100+ items, 50+ monsters)
- ✅ Advanced AI with emergent behavior
- ✅ Portal system with monster interaction
- ✅ Comprehensive documentation
- ✅ Optimized performance (60 FPS)

---

## 📞 Support & Information

### Questions?

- See [DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md) for architecture philosophy
- See [docs/architecture/](docs/architecture/) for system design
- See [docs/development/](docs/development/) for implementation details
- See [TRADITIONAL_ROGUELIKE_FEATURES.md](TRADITIONAL_ROGUELIKE_FEATURES.md) for feature roadmap

### Bug Reports

If you find issues:
1. Check existing tests (might be known limitation)
2. Write a failing test that reproduces the bug
3. Fix the bug (test should pass)
4. Add regression test

---

## 📄 License

[See LICENSE file](LICENSE)

---

## 🎉 Thanks

Built with passion for roguelikes and clean architecture.

**Yarl: Where classic roguelike gameplay meets modern design principles.**

---

**Last Updated:** November 2025 | Portal System Phase B Complete

**Next Session:** Continue with gameplay expansion and balance refinement
