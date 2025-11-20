# 🏰 Catacombs of Yarl

> A professional-grade roguelike game built with Python, featuring a complete story arc, advanced procedural generation, sophisticated difficulty balancing, and modern ECS architecture.

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-2500%2B-passing-brightgreen.svg)](tests/)
[![Version](https://img.shields.io/badge/Version-4.3.1-blue.svg)](CHANGELOG.md)

**Catacombs of Yarl** is a traditional roguelike that combines classic dungeon-crawling gameplay with modern software engineering practices. Explore a 25-level dungeon, battle 50+ monster types, discover 100+ unique items, and uncover a dark story of soul rotation and ancient dragons.

---

## ✨ Features

### 🎮 Core Gameplay
- **Traditional roguelike mechanics** - Turn-based combat, exploration, and resource management
- **25-level dungeon** - Procedurally generated with increasing difficulty
- **Complete story arc** - 5 narrative phases leading to 6 distinct endings
- **Advanced level generation** - Doors, secret rooms, traps, stairs, and multi-floor persistence
- **Sophisticated difficulty balancing** - ETP (Encounter Threat Points) system for balanced encounters
- **Faction system** - Dynamic hostility and AI behavior modifications
- **Portal system** - Create shortcuts with emergent monster AI interactions

### ⚔️ Combat & Items
- **D20 combat system** - Attack rolls, armor class, damage resistances
- **100+ unique items** - 22 scrolls, 11 potions, 9 wands, 15 rings, 20+ equipment pieces
- **30+ spells** - Fireball, confusion, teleportation, healing, and more
- **50+ monster types** - Distinct AI behaviors, faction systems, contextual hostility
- **Status effects** - 20+ types including poison, bleed, stun, charm
- **Equipment system** - 7 slots (head, body, hands, legs, feet, ring1, ring2)
- **Item identification** - Magical items require identification to reveal properties
- **Throwing system** - Ranged attacks with potions and items

### 🗺️ Exploration & Discovery
- **Procedural dungeon generation** - Multiple connectivity styles (orthogonal, jagged, organic)
- **Secret rooms** - Hidden chambers with ambient hints for discovery
- **Locked doors** - Require keys with customizable key tags
- **Trap system** - Spike traps, web traps, alarm plates with detection mechanics
- **Auto-explore** - Automated movement through safe areas
- **FOV-based exploration** - Field of view with memory of explored areas
- **Interactive features** - Signposts, murals, chests, easter eggs

### 🏗️ Technical Excellence
- **ECS architecture** - Entity Component System for flexible game entities
- **Event-driven design** - Loose coupling via event bus
- **2500+ tests** - Comprehensive test coverage (~47% test-to-production ratio)
- **Data-driven content** - YAML-based configuration for easy content iteration
- **Telemetry system** - Comprehensive gameplay metrics collection
- **Performance optimized** - 60 FPS with sub-50ms input response
- **Type hints** - Full type annotation throughout codebase
- **Modular design** - Clear separation of concerns

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12 or higher
- pip (Python package manager)

### Installation

```bash
# Clone the repository
git clone https://github.com/RafeHatfield/rlike.git
cd rlike

# Install dependencies
pip install -r requirements.txt

# Run the game
python engine.py
```

### Command Line Options

```bash
# Normal gameplay
python engine.py

# Testing mode (more items, debug features)
python engine.py --testing

# Start at a specific level
python engine.py --start-level 10

# Enable telemetry collection
python engine.py --telemetry-json telemetry.json

# Bot mode (automated gameplay for testing)
python engine.py --bot

# Bot soak mode (multiple sequential bot runs)
python engine.py --bot-soak --runs 10

# Combine flags
python engine.py --testing --start-level 5 --telemetry-json output/session.json
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test suite
pytest tests/test_portal_system_phase_b.py -v

# Run critical quality-assurance tests (fast feedback)
pytest tests/test_golden_path_floor1.py \
        tests/test_public_imports_smoke.py \
        tests/test_component_contracts.py \
        tests/test_world_invariants.py -v

# Use convenience runners
python3 run_golden_path_tests.py      # Golden-path tests (~0.4s)
python3 run_critical_tests.py         # Critical tests (~1.78s)
```

---

## 🎮 How to Play

### Basic Controls

| Action | Key |
|--------|-----|
| Move | Arrow keys or `hjkl` (vi keys) |
| Diagonal movement | `yubn` |
| Pick up item | `g` |
| Wait/Rest | `z` |
| Inventory | `i` |
| Drop item | `d` |
| Throw item | `t` |
| Auto-explore | `o` |
| Search | `s` |
| Use stairs | `Enter` |
| Character screen | `c` |

### Gameplay Flow

1. **Start** - Begin in a random room at dungeon level 1
2. **Explore** - Discover rooms, find items, defeat monsters
3. **Progress** - Deeper levels offer better loot but more danger
4. **Identify** - Use scrolls or trial-and-error to identify magical items
5. **Equip** - Gear up to improve combat effectiveness
6. **Quest** - Reach level 25, claim the Ruby Heart, confront the dragons
7. **Ending** - Choose your path (6 distinct endings available)

### Tips for New Players

- **Manage resources** - Potions and scrolls are limited; use them wisely
- **Identify early** - Knowing what items do is crucial for survival
- **Equipment matters** - Different gear provides different bonuses
- **Status effects** - Can turn fights around; learn what each does
- **Search walls** - Secret rooms hide valuable treasures
- **Watch for traps** - Passive detection helps, but be cautious
- **Keys are valuable** - Locked doors guard important areas
- **Portals are tactical** - Create shortcuts, but monsters can follow!

---

## 📊 Project Statistics

- **116,322+ lines of code** across 363 Python files
- **2500+ tests** with 100% pass rate on critical paths
- **100+ unique items** (scrolls, potions, wands, rings, equipment)
- **50+ monster types** with distinct AI behaviors
- **30+ spells** with various targeting modes
- **25 dungeon levels** with procedural generation
- **131+ documentation files** covering architecture and development

See [PROJECT_STATS.md](PROJECT_STATS.md) for detailed metrics.

---

## 🏗️ Architecture

### Design Principles

Yarl follows modern software engineering principles:

- **Single Source of Truth** - Each system has one canonical place
- **Component-Based** - ECS architecture for entity flexibility
- **Event-Driven** - Loose coupling via event bus
- **Test-Driven** - Comprehensive test coverage
- **Data-Driven** - YAML-based content configuration
- **Emergent Gameplay** - Systems interact in unexpected ways

See [DESIGN_PRINCIPLES.md](docs/DESIGN_PRINCIPLES.md) for full architectural philosophy.

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
- TrapSystem - Hazard detection and triggering
- FactionEngine - Hostility and behavior overrides
- FloorStateManager - Multi-floor persistence
- EncounterBudgetEngine - ETP-based difficulty scaling
- LootController - Pity mechanics and item balancing
- TelemetryService - Gameplay metrics collection

**Content:**
- EntityFactory - Data-driven entity creation
- LevelTemplateRegistry - YAML-based level definitions
- ConfigRegistry - Game constants and settings
- ItemSystem - Stacking, equipment, identification
- SpellSystem - Casting, targeting, effects

---

## 📚 Documentation

### For Players

- **[STORY_LORE_CANONICAL.md](STORY_LORE_CANONICAL.md)** - Complete narrative and themes
- **[ROADMAP.md](ROADMAP.md)** - Development roadmap and planned features
- **[TRADITIONAL_ROGUELIKE_FEATURES.md](TRADITIONAL_ROGUELIKE_FEATURES.md)** - Feature roadmap

### For Developers

- **[docs/README.md](docs/README.md)** - Documentation hub and navigation
- **[docs/DESIGN_PRINCIPLES.md](docs/DESIGN_PRINCIPLES.md)** - Architectural philosophy
- **[docs/architecture/](docs/architecture/)** - System design & specifications
- **[docs/development/](docs/development/)** - Phase summaries & implementation details
- **[docs/CONTRIBUTING_AUTOGEN.md](docs/CONTRIBUTING_AUTOGEN.md)** - Guidelines for AI/automated agents

### Key Documentation Files

- **Level Generation:** [docs/YAML_ROOM_GENERATION_SYSTEM.md](docs/YAML_ROOM_GENERATION_SYSTEM.md)
- **Portal System:** [docs/development/portal/README.md](docs/development/portal/README.md)
- **Bot System:** [docs/BOT_DESIGN.md](docs/BOT_DESIGN.md)
- **Combat System:** [docs/COMBAT_SYSTEM.md](docs/COMBAT_SYSTEM.md)
- **Spell System:** [docs/SPELL_SYSTEM.md](docs/SPELL_SYSTEM.md)

---

## 🧪 Testing

### Test Coverage

- **Portal System:** 91/91 tests passing (100%)
- **Combat System:** 200+ tests
- **Item System:** 150+ tests
- **AI System:** 180+ tests
- **Level Generation:** 100+ tests
- **Integration Tests:** 800+ tests
- **Total:** 2500+ tests with 100% pass rate on critical paths

### Test Suites

| Suite | Purpose | Runtime |
|-------|---------|---------|
| **Golden-Path** | Critical gameplay flows | ~0.4s |
| **Import Smoke** | Module availability & imports | ~0.15s |
| **Component Contracts** | ECS consistency | ~0.2s |
| **World Invariants** | Map generation properties | ~1.0s |
| **All Critical Tests** | Pre-merge gate | ~1.78s |
| **Full Suite** | 2500+ comprehensive tests | ~60s |

---

## 🎯 Current Status

### ✅ Completed Features

- ✅ Core roguelike gameplay (combat, exploration, items)
- ✅ Complete story arc (Phases 1-5 with 6 endings)
- ✅ Portal system (Phase A & B with monster AI)
- ✅ Advanced level generation (doors, secrets, traps, stairs)
- ✅ Multi-floor persistence with anti-farming mechanics
- ✅ Difficulty balancing (ETP system)
- ✅ Faction system with dynamic hostility
- ✅ Loot pity mechanics for balanced item distribution
- ✅ Telemetry & validation systems
- ✅ Bot mode for automated testing
- ✅ Comprehensive test coverage (2500+ tests)

### 🔄 In Progress

- Playtesting and balance tuning
- Performance optimization
- Documentation refinement

### 📋 Planned Features

See [ROADMAP.md](ROADMAP.md) for comprehensive feature planning.

- 🔄 Vaults & advanced room types
- 🔄 Religion/god system
- 🔄 Shop system
- 🔄 Amulet system
- 🔄 Polymorph mechanics
- 🔄 Wish system
- 🔄 Named unique artifacts
- 🔄 Advanced companion systems

---

## 🎨 Design Highlights

### Emergent Gameplay

The portal system exemplifies emergent design:
- No scripted monster behavior for portals
- Monsters can pick up inventory items
- They can use teleportation mechanics
- **Result:** Orcs unexpectedly chase through your portals!
- Bosses have flags to avoid this (tactical advantage)

Similarly, the faction system creates emergent conflicts:
- No hardcoded "orcs attack undead" logic
- Orc and undead entities have faction tags
- Necropolis room has hostility override
- **Result:** Orcs automatically fight undead in that room!

### Data-Driven Design

Content defined in YAML, loaded at runtime:
- Easy to add new items/monsters without code changes
- Designers can work without touching Python
- Configuration in `config/entities.yaml` and `config/level_templates.yaml`
- Template validation catches errors immediately

### Single Source of Truth

Each system has one place where it's canonical:
- **PortalManager** - All portal logic centralized
- **AISystem** - All monster turn orchestration
- **CombatSystem** - All damage/resistance calculation
- **EncounterBudgetEngine** - All difficulty scaling

Makes debugging, testing, and extending straightforward.

---

## 🤝 Contributing

### For AI Assistants & Automated Agents

**Important:** See [docs/CONTRIBUTING_AUTOGEN.md](docs/CONTRIBUTING_AUTOGEN.md) before making broad changes.

This document clarifies:
- **Module ownership** (who owns rendering, portals, world generation, etc.)
- **Testing requirements** (what tests to update for each module)
- **Anti-patterns to avoid** (don't reimplement FOV, don't hardcode values, etc.)
- **Code review checklist** for AI-generated changes

**TL;DR:** When changing behavior, add a test that covers it. Check module ownership. Respect contracts.

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
- Validation tests for configuration schemas

---

## 📊 Telemetry & Analytics

### Telemetry Collection

Comprehensive gameplay metrics collection for balance tuning:

```bash
python engine.py --telemetry-json telemetry.json
```

**Metrics Per Floor:**
- Encounter threat points (ETP)
- Time-to-kill / time-to-death values
- Trap detection and triggering
- Secret room discovery
- Door interactions
- Loot balancing events
- Spawn statistics

See [docs/LOGGING.md](docs/LOGGING.md) for details.

---

## 🏆 Achievements

- ✅ Complete story arc with multiple endings
- ✅ Advanced procedural level generation with 5+ interconnected systems
- ✅ Sophisticated difficulty balancing through ETP budgeting
- ✅ Multi-floor persistence with anti-farming mechanics
- ✅ Professional-grade test coverage (2500+ tests)
- ✅ Clean, modular architecture (ECS-based)
- ✅ Rich content (100+ items, 50+ monsters, 30+ spells)
- ✅ Advanced AI with emergent behavior
- ✅ Portal system with monster interaction
- ✅ Faction system with dynamic hostility
- ✅ Comprehensive telemetry & analytics
- ✅ Template validation with actionable errors
- ✅ Comprehensive documentation (131+ files)
- ✅ Optimized performance (60 FPS)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Built with passion for roguelikes and clean architecture.

**Yarl: Where classic roguelike gameplay meets modern design principles.**

---

## 📞 Support & Information

### Questions?

- See [DESIGN_PRINCIPLES.md](docs/DESIGN_PRINCIPLES.md) for architecture philosophy
- See [docs/architecture/](docs/architecture/) for system design
- See [docs/development/](docs/development/) for implementation details
- See [TRADITIONAL_ROGUELIKE_FEATURES.md](TRADITIONAL_ROGUELIKE_FEATURES.md) for feature roadmap

### Bug Reports

If you find issues:
1. Check existing tests (might be known limitation)
2. Write a failing test that reproduces the bug
3. Fix the bug (test should pass)
4. Add regression test
5. Validate templates if YAML-related

---

**Last Updated:** November 2025 | Version 4.3.1  
**Status:** 🟢 Active Development  
**Next:** Playtesting, balance tuning, and gameplay refinement
