# Catacombs of Yarl - A Python Roguelike Game

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-GPL--3.0-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-1462%20passing-brightgreen.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)](tests/)
[![Startup Tests](https://img.shields.io/badge/startup%20tests-automated-blue.svg)](tests/smoke/)

**Catacombs of Yarl** (Yarl for short) is a feature-rich roguelike game built in Python using a professional game engine architecture. Explore the mysterious catacombs beneath the ancient city of Yarl, featuring turn-based combat, procedural dungeon generation, spell casting, character progression, and AI-driven monsters with various behaviors.

## 🎮 Features

### Core Gameplay
- **Turn-based combat** with attack/defense mechanics
- **Procedural dungeon generation** with rooms and corridors
- **Progressive difficulty scaling** - Challenge increases with dungeon depth
- **Multi-level dungeons** with stairs and level progression
- **Character progression** - XP, leveling, and stat increases
- **JSON Save/Load system** - Human-readable persistent game state with legacy compatibility
- **Field of view (FOV)** and line-of-sight calculations
- **Inventory management** with item usage and dropping
- **Health and damage system** with healing mechanics

### Spells & Combat
- **🔥 Fireball** - Area-of-effect damage with targeting (unlocks at level 6)
- **⚡ Lightning** - Single-target high damage to closest enemy (unlocks at level 4)
- **😵 Confusion** - Causes enemies to move randomly for several turns (unlocks at level 2)
- **💚 Healing Potions** - Restore health when injured (available from start)
- **🌀 Teleport** - Instant repositioning (10% chance of disorienting misfire)
- **🛡️ Shield** - Temporary defense boost (+4 defense for 10 turns)
- **🧟 Raise Dead** - Resurrect a corpse as a mindless zombie ally
- **💨 Dragon Fart** - Directional cone of noxious gas (20-turn knockout)
- **🎯 Progressive item availability** - Better items unlock as you go deeper

### Equipment System
- **⚔️ Variable Damage Weapons** - Swords (2-5 dmg) and daggers (1-3 dmg) with exciting damage ranges
- **🛡️ Variable Defense Armor** - Shields (1-3 def) that provide dynamic protection
- **🎲 Dual-Stat System** - Weapons combine base power + variable damage for unpredictable combat
- **📊 Enhancement Scrolls** - Improve weapon damage and armor defense ranges
- **🔄 Equipment Slots** - Main hand and off hand equipment management
- **🎒 Inventory Integration** - Seamless equip/unequip with detailed damage/defense displays
- **📈 Progressive Equipment** - Better gear unlocks on deeper levels
- **✨ Loot Quality System** - Magic items with rarity tiers (Common, Uncommon, Rare, Legendary)
- **🎯 Level-Scaled Drops** - Better loot at deeper dungeon levels
- **💎 Magic Item Naming** - Flaming Swords, Reinforced Shields, and other epic gear

### AI & Monsters
- **🎲 Variable Monster Damage** - Orcs (3 power + 1-3 natural) and Trolls (6 power + 2-6 natural) for dynamic combat
- **BasicMonster AI** - Tracks and attacks the player using A* pathfinding
- **BossAI** - Enhanced AI for boss monsters with smarter targeting and enrage mechanics
- **ConfusedMonster AI** - Random movement with automatic recovery
- **SlimeAI** - Monster-vs-monster combat with faction-based targeting
- **MindlessZombieAI** - Resurrected undead that hunt anything in FOV
- **Invisibility Mechanics** - Monsters can't detect invisible targets
- **Dynamic AI switching** - Spells can temporarily alter monster behavior
- **Progressive monster scaling** - More and stronger monsters on deeper levels
- **🧌 Orcs** - Basic enemies with balanced variable damage (total range: 4-6)
- **👹 Trolls** - Stronger enemies with high variable damage (total range: 8-12)
- **🟢 Slimes** - Corrosive monsters that attack everything (weapons/armor degrade)
- **🟢 Large Slimes** - Powerful slimes that split into smaller slimes on death
- **🐉 Boss Monsters** - Unique powerful encounters with phases, dialogue, enrage mechanics, and legendary loot

### Technical Features
- **Entity-Component-System (ECS)** architecture
- **Data-Driven Entity System** - All entities configured via YAML with validation
- **Manual Level Design System** - Template-based level customization with guaranteed spawns and special rooms
- **Boss Fight System** - Multi-phase bosses with dialogue, enrage mechanics, and status immunities
- **A* pathfinding** for intelligent monster movement
- **Equipment system** with stat bonuses and slot management
- **Loot Quality & Scaling** - Rarity-based magic items with level-scaled drops
- **Status Effect System** - Invisibility, confusion, disorientation, shield buffs
- **Faction System** - Monster-vs-monster combat and affiliations
- **Equipment Corrosion** - Weapons and armor can degrade during combat
- **Entity sorting cache** for optimized rendering performance
- **Dynamic difficulty scaling** with configurable progression curves
- **Weighted random selection** for balanced item/monster distribution
- **JSON Save/Load system** with human-readable saves and legacy shelve compatibility
- **Message logging system** for game events with categorized formatting
- **Character screen** with level, XP, and detailed stat display including variable damage/defense ranges
- **Robust error handling** throughout the codebase
- **Configuration Management** - Centralized game constants with file loading support
- **Turn Phase System** - Structured turn management (PLAYER → ENEMY → ENVIRONMENT)

## 🚀 Quick Start

### Prerequisites
- Python 3.12 or higher
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/YourUsername/rlike.git
   cd rlike
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the game**
   ```bash
   # Normal gameplay
   python engine.py
   
   # Testing mode (increased item spawns for easier testing)
   python engine.py --testing
   # or use the convenience script
   python test_game.py
   ```

## 🎯 How to Play

### Controls

#### Movement
- **Arrow Keys** - Move your character (@) one step at a time
- **Left Mouse Click** - Click-to-move with pathfinding
  - Click on empty space: Player automatically moves to that location
  - Click on adjacent enemy: Attack that enemy
  - Movement stops automatically if enemies are spotted
- **Right Mouse Click** - Cancel pathfinding movement

#### Spells & Targeting
- **Mouse Click** - Target spells (fireball, confusion) when in targeting mode

#### Items & Inventory
- **g** - Pick up items
- **i** - Open inventory
- **d** - Drop items

#### Navigation & Menus
- **Enter** - Take stairs to next level
- **c** - Open character screen (view level, XP, stats with variable damage/defense ranges)
- **s** - Save game
- **l** - Load game
- **Escape** - Exit menus/game

### Gameplay Tips
- **Stay healthy** - Use healing potions when injured
- **Use spells wisely** - Fireball affects multiple enemies, confusion disables threats
- **Manage inventory** - Limited carrying capacity, drop items you don't need
- **Tactical positioning** - Use corridors to fight enemies one-at-a-time
- **Mouse movement** - Click-to-move is faster for exploration, but movement stops when enemies appear
- **Combat awareness** - Use arrow keys for precise positioning in combat situations
- **Progress deeper** - Better items and more XP on lower levels, but more dangerous
- **Level up strategically** - Choose HP, strength, or defense based on your playstyle
- **Save frequently** - Game saves automatically on exit, but manual saves are recommended
- **Explore thoroughly** - Each level has stairs to the next, usually in the last room

## 🧪 Testing & Development

### Testing Mode

For easier testing of game mechanics, Yarl includes a special testing mode that dramatically increases item spawn rates:

```bash
# Enable testing mode via command line
python engine.py --testing

# Or use the convenience script
python test_game.py

# Or set environment variable
export YARL_TESTING_MODE=true
python engine.py
```

**Testing Mode Features:**
- **10-20 items per room** (vs 1-2 in normal mode)
- **All scrolls and equipment available from level 1** (vs progressive unlocking)
- **Higher spawn chances** for rare items (30-50% vs 5-25%)
- **Monster equipment spawning** at 50% rate (vs 10-70% scaling in normal mode)
- **Enhanced logging** for debugging monster behavior and item tracking
- **Perfect for testing** inventory, targeting, equipment, and spell mechanics

### Debug Logging

Testing mode automatically enables comprehensive logging to help debug game mechanics and track monster behavior:

#### Available Log Files

```bash
# Combat debug log - detailed combat calculations
combat_debug.log

# Monster action log - comprehensive monster behavior tracking
monster_actions.log
```

#### Viewing Logs in Real-Time

```bash
# Monitor combat calculations (damage, defense, variable stats)
tail -f combat_debug.log

# Monitor monster actions (item usage, pickup, movement, combat)
tail -f monster_actions.log

# Monitor both logs simultaneously
tail -f combat_debug.log monster_actions.log
```

#### Log Content Examples

**Combat Debug Log:**
```
18:45:23 - COMBAT: Player [power:2+3] (1-3 dmg) attacks for 8 (5 power + 3 rolled), Orc [def:0+0] blocks 0 (0 defense + 0 rolled) = 8 total damage
18:45:24 - COMBAT: Orc [power:4+0] (1-3 dmg) attacks for 6 (4 power + 2 rolled), Player [def:1+2] blocks 2 (1 defense + 1 rolled) = 4 total damage
```

**Monster Action Log:**
```
18:45:25 - MONSTER: Orc at (5, 5) attempts item_pickup: attempting to pick up Enhance Armor Scroll
18:45:25 - MONSTER: Orc at (5, 5) inventory_change SUCCESS: added Enhance Armor Scroll (inventory: 1 items)
18:45:25 - MONSTER: Orc at (5, 5) item_pickup SUCCESS: picked up and stored Enhance Armor Scroll
18:45:26 - MONSTER: Orc at (5, 5) attempts item_usage: attempting to use Lightning Scroll
18:45:26 - MONSTER: Orc at (5, 5) item_usage FAILED: failed to use Lightning Scroll on Player (failure: fizzle)
18:45:26 - MONSTER: Orc at (5, 5) inventory_change SUCCESS: removed (used) Lightning Scroll (inventory: 0 items)
18:45:27 - MONSTER: Orc at (5, 5) loot_drop SUCCESS: dropped Enhance Armor Scroll at (5, 4)
```

#### What Gets Logged

**Combat Debug Log:**
- ✅ **Variable damage calculations** - Base power + rolled damage
- ✅ **Variable defense calculations** - Base defense + rolled defense  
- ✅ **Final damage calculations** - Attack vs defense with absorption details
- ✅ **Equipment bonuses** - Weapon power and armor defense contributions
- ✅ **Natural damage** - Monster base damage ranges (fists, claws, etc.)

**Monster Action Log:**
- ✅ **Item Usage** - Success/failure with specific failure modes (fizzle, wrong target, equipment damage)
- ✅ **Item Pickup** - Success/failure with reasons (no inventory, full inventory, etc.)
- ✅ **Equipment Changes** - When monsters equip/unequip weapons and armor
- ✅ **Inventory Changes** - Items added/removed with current inventory counts
- ✅ **Loot Dropping** - Exact positions where items are dropped upon monster death
- ✅ **Movement & Combat** - Basic AI actions and pathfinding decisions
- ✅ **Turn Summaries** - Complete overview of each monster's actions per turn

#### Troubleshooting with Logs

**Missing Items:** Check `monster_actions.log` for pickup/usage/drop events
```bash
grep "Enhance Armor Scroll" monster_actions.log
```

**Combat Balance:** Check `combat_debug.log` for damage calculations
```bash
grep "attacks for" combat_debug.log | tail -10
```

**Monster Behavior:** Check `monster_actions.log` for AI decision patterns
```bash
grep "turn complete" monster_actions.log | tail -5
```

### Test Suite

This project maintains **100% test coverage** with a comprehensive test suite covering all game systems.

### Running Tests

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests (1,462 tests)
pytest

# Run with coverage reporting
pytest --cov=. --cov-report=term-missing

# Run specific test categories
pytest tests/test_entity.py -v                # Entity and AI systems
pytest tests/test_item_functions.py -v        # Spells and items
pytest tests/test_inventory.py -v             # Inventory management
pytest tests/test_fighter.py -v               # Combat system
pytest tests/test_game_messages.py -v         # Message logging
pytest tests/test_difficulty_scaling.py -v    # Difficulty scaling system
pytest tests/test_random_utils.py -v          # Weighted selection utilities
pytest tests/test_save_load_basic.py -v       # Save/load functionality
pytest tests/test_level.py -v                 # XP and leveling system
pytest tests/test_dungeon_levels.py -v        # Multi-level dungeons
pytest tests/regression/ -v                  # Regression tests for critical bugs
pytest tests/integration/ -v                 # Integration tests for system interactions
pytest tests/comprehensive/ -v               # Comprehensive end-to-end tests
```

### Test Coverage
- **1,462 tests** with **100% pass rate**
- **Entity System** - Movement, pathfinding, A* algorithm
- **Combat System** - Attack, defense, healing, death mechanics, XP rewards
- **Equipment System** - Equipment slots, stat bonuses, equip/unequip mechanics
- **Inventory System** - Item management, capacity limits, equipment integration
- **Spell System** - All spells including confusion, teleport, raise dead, dragon fart, and targeting
- **AI System** - BasicMonster, ConfusedMonster, SlimeAI, MindlessZombieAI behavior
- **Status Effect System** - Invisibility, confusion, disorientation, shield buffs
- **Faction System** - Monster-vs-monster combat and targeting priorities
- **Message System** - Game event logging and display
- **Difficulty Scaling** - Progressive monster/item scaling, weighted selection
- **JSON Save/Load System** - Human-readable saves, legacy compatibility, comprehensive validation
- **Character Progression** - XP system, leveling, stat increases
- **Dungeon Levels** - Multi-floor generation, stairs, level transitions
- **FOV & Rendering System** - Field of view calculations, map rendering, visual regression prevention
- **Manual Level Design** - Template-based level customization with guaranteed spawns and special rooms
- **Equipment Corrosion** - Weapon and armor degradation mechanics
- **Game Engine Integration** - System coordination, state management, performance optimization
- **Regression Testing** - Automated prevention of critical bugs (FOV, combat, death system)
- **Integration Testing** - End-to-end system interaction validation

## 🏗️ Architecture

### Project Structure
```
rlike/
├── components/          # ECS Components
│   ├── ai.py           # AI behaviors (BasicMonster, ConfusedMonster, SlimeAI, MindlessZombieAI)
│   ├── equipment.py    # Equipment slot management and stat bonuses
│   ├── equippable.py   # Equippable item component with bonuses
│   ├── fighter.py      # Combat stats and methods with XP rewards
│   ├── inventory.py    # Item storage and equipment management
│   ├── item.py         # Item component definition
│   ├── level.py        # XP and leveling system
│   └── status_effects.py  # Status effects (invisibility, confusion, shield, disorientation)
├── config/             # Centralized configuration system
│   ├── game_constants.py       # All game constants and configuration
│   ├── testing_config.py       # Testing mode configuration
│   ├── entities.yaml           # Entity definitions (monsters, weapons, armor, spells)
│   ├── entity_registry.py      # Entity loading and validation
│   ├── entity_factory.py       # Entity creation from YAML definitions
│   ├── level_templates.yaml    # Normal level templates and special rooms
│   ├── level_templates_testing.yaml  # Testing mode level overrides
│   └── level_template_registry.py    # Level template loading and parsing
├── loader_functions/   # Game initialization and JSON save/load
│   ├── initialize_new_game.py  # New game setup
│   └── data_loaders.py         # Save/load functionality
├── map_objects/        # Map generation and tiles
│   ├── game_map.py     # Dungeon generation with difficulty scaling
│   ├── rectangle.py    # Room generation utilities
│   └── tile.py         # Tile properties (walkable, transparent)
├── tests/              # Comprehensive test suite (1,462 tests)
│   ├── comprehensive/  # End-to-end integration tests
│   ├── integration/    # System interaction tests
│   ├── regression/     # Critical bug prevention tests
│   ├── smoke/          # Automated startup and core system tests
│   ├── conftest.py     # Test fixtures and mocking
│   ├── test_*.py       # Test modules for each component
│   └── __init__.py
├── engine.py           # Main game loop and entry point
├── test_startup.py     # Quick game startup verification script
├── entity.py           # Base entity class with movement/pathfinding
├── entity_sorting_cache.py  # Performance optimization for entity rendering
├── game_actions.py     # Modular action processing system
├── item_functions.py   # Spell implementations (heal, fireball, etc.)
├── input_handlers.py   # Keyboard and mouse input processing
├── render_functions.py # Display and rendering logic
├── game_messages.py    # Message logging system
├── game_states.py      # Game state management
├── random_utils.py     # Weighted selection and difficulty scaling
├── stairs.py           # Stairs component for level transitions
├── equipment_slots.py  # Equipment slot enumeration (MAIN_HAND, OFF_HAND)
├── menus.py            # UI menus (inventory, character screen, etc.)
└── requirements.txt    # Project dependencies
```

### Key Design Patterns
- **Entity-Component-System (ECS)** - Flexible entity composition
- **Command Pattern** - Input handling and game actions
- **State Machine** - Game state management (playing, inventory, targeting, leveling)
- **Strategy Pattern** - AI behavior switching (normal → confused → normal)
- **Table-Driven Design** - Difficulty scaling with configurable progression tables
- **Serialization Pattern** - Save/load system with validation and error handling
- **Configuration Pattern** - Centralized constants and settings management

### Configuration System

The game uses a centralized configuration system in `config/game_constants.py`:

```python
from config.game_constants import (
    get_constants,          # Legacy format for compatibility
    get_combat_config,      # Combat stats and progression
    get_inventory_config,   # Inventory capacity and limits
    get_rendering_config,   # Screen dimensions and FOV settings
    get_gameplay_config,    # Map generation and entity spawning
    get_pathfinding_config, # A* pathfinding parameters
    get_performance_config  # Optimization and caching settings
)

# Example usage
combat = get_combat_config()
player_hp = combat.DEFAULT_HP
inventory_size = get_inventory_config().DEFAULT_INVENTORY_CAPACITY
```

**Benefits:**
- **Single source of truth** for all game constants
- **Easy tuning** without hunting through code
- **Type safety** with dataclass configurations
- **Backward compatibility** with legacy dictionary format

### Action Processing System

The game uses a modular action processing system in `game_actions.py`:

```python
from game_actions import ActionProcessor

# Create processor with game state manager
processor = ActionProcessor(state_manager)

# Process player actions
action = {"move": (1, 0)}  # Move right
mouse_action = {"left_click": (10, 15)}  # Click at coordinates
processor.process_actions(action, mouse_action)
```

**Key Features:**
- **Modular handlers** for each action type (movement, combat, inventory)
- **Centralized error handling** with logging
- **State-aware processing** that respects current game state
- **Extensible design** for adding new action types

### Entity Sorting Cache System

The game includes an optimized entity sorting cache in `entity_sorting_cache.py`:

```python
from entity_sorting_cache import get_sorted_entities, get_entity_cache_stats

# Get entities sorted by render order (cached when possible)
sorted_entities = get_sorted_entities(entities)

# Check cache performance
stats = get_entity_cache_stats()
print(f"Cache hit rate: {stats['hit_rate_percent']:.1f}%")
```

**Key Features:**
- **Automatic caching** of entity sorting operations
- **Smart invalidation** when entities are added, removed, or moved
- **Performance monitoring** with detailed statistics
- **Transparent integration** with existing rendering code
- **High hit rates** in typical gameplay scenarios (90%+ when entities are stable)

**Cache Invalidation Triggers:**
- Entity addition (monster spawning, item drops)
- Entity removal (monster death, item pickup)
- Entity position changes (movement)
- Entity render order changes (state transitions)

## 🔧 Development

### Adding New Features
1. **Write tests first** - Follow TDD practices with our 100% coverage
2. **Use the ECS pattern** - Add new components for new capabilities
3. **Update documentation** - Keep README and code comments current
4. **Run the full test suite** - Ensure no regressions

### Code Style
- **Type hints** encouraged for new code
- **Descriptive variable names** for clarity
- **Comprehensive docstrings** for public methods
- **Error handling** - Return results rather than raising exceptions

## 🧪 Automated Testing & Quality Assurance

Yarl includes comprehensive automated testing to ensure code quality and prevent regressions:

### Quick Startup Verification
For rapid development feedback, use the quick startup test:
```bash
python test_startup.py
```
This verifies that all core systems can initialize correctly without running the full test suite.

### Comprehensive Test Suite
Run the full test suite with 1,103 tests:
```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/smoke/           # Startup and core system tests
pytest tests/integration/     # System interaction tests  
pytest tests/regression/      # Critical bug prevention tests
pytest tests/comprehensive/   # End-to-end integration tests

# Run with coverage reporting
pytest --cov=. --cov-report=html
```

### Test Categories
- **🚀 Smoke Tests** (`tests/smoke/`) - Automated startup verification and core system validation
- **🔗 Integration Tests** (`tests/integration/`) - Multi-system interaction testing
- **🛡️ Regression Tests** (`tests/regression/`) - Prevention of critical bug reoccurrence  
- **🎯 Comprehensive Tests** (`tests/comprehensive/`) - End-to-end gameplay scenarios
- **⚙️ Unit Tests** (`tests/test_*.py`) - Individual component validation

### Continuous Integration
The automated test suite prevents runtime regressions by validating:
- ✅ Game engine initialization
- ✅ FOV system functionality  
- ✅ Configuration system integrity
- ✅ Action processing pipeline
- ✅ Core gameplay mechanics
- ✅ Save/load functionality

### Contributing
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for your changes
4. Make your changes
5. Verify game still starts (`python test_startup.py`)
6. Ensure all tests pass (`pytest`)
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to the branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

## 📚 Dependencies

### Runtime Dependencies
- **[tcod](https://github.com/libtcod/python-tcod)** (19.5.0) - Console graphics and input handling
- **[numpy](https://numpy.org/)** (2.3.3) - Numerical computations for pathfinding
- **[PyYAML](https://pyyaml.org/)** (6.0.3) - YAML configuration file parsing
- **[cffi](https://cffi.readthedocs.io/)** (2.0.0) - C Foreign Function Interface

### Development Dependencies
- **[pytest](https://pytest.org/)** (8.4.2) - Testing framework
- **[pytest-cov](https://pytest-cov.readthedocs.io/)** (7.0.0) - Coverage reporting
- **[pytest-mock](https://pytest-mock.readthedocs.io/)** (3.15.1) - Mocking utilities

## 🐛 Known Issues

The following behavioral quirks are documented in tests but intentionally left unchanged:

1. **Division by zero** in `move_towards()` when target equals current position
2. **Multiple death results** possible in Fighter component
3. **Negative damage healing** - No input validation on damage amounts
4. **Defense inconsistency** - Only applied in `attack()`, not `take_damage()`

These are tracked for future improvement when confident in test coverage.

## ⚙️ Configuration System

**Catacombs of Yarl** features a comprehensive data-driven entity system that allows game designers to modify all entity properties without touching code.

### 🎯 Entity Configuration

All monsters, weapons, armor, and spells are defined in `config/entities.yaml`:

```yaml
# Monster definitions
monsters:
  orc:
    stats:
      hp: 20
      power: 4
      defense: 0
      xp: 35
    char: "o"
    color: [63, 127, 63]  # Dark green
    ai_type: "basic"

# Weapon definitions  
weapons:
  sword:
    power_bonus: 3
    damage_min: 2
    damage_max: 5
    slot: "main_hand"
    char: "/"
    color: [192, 192, 192]  # Silver

# Armor definitions
armor:
  shield:
    defense_bonus: 1
    defense_min: 1
    defense_max: 3
    slot: "off_hand"
    char: "["
    color: [139, 69, 19]  # Brown
```

### 🔧 Game Constants

Game mechanics and settings are centralized in `config/game_constants.py`:

- **Combat Config**: Default stats, damage calculations, level progression
- **Entity Config**: File paths, validation settings, inheritance options
- **Performance Config**: Spatial indexing, FOV caching, rendering optimization
- **Gameplay Config**: Map generation, entity spawning parameters
- **Rendering Config**: Screen dimensions, FOV settings, display parameters

### 🏭 Architecture Benefits

- **🎨 Designer-Friendly**: Modify stats, add monsters/items via YAML editing
- **🔒 Type Safety**: Comprehensive validation prevents invalid configurations
- **🚀 Performance**: Entities loaded once at startup with fast factory creation
- **🛡️ Robust**: Fallback entities prevent crashes from missing definitions
- **🧪 Testable**: 71+ dedicated tests ensure configuration system reliability
- **🔄 Extensible**: Inheritance support (foundation) for entity variants

### 📁 Configuration Files

```
config/
├── entities.yaml          # All entity definitions
├── game_constants.py      # Centralized game settings
├── entity_registry.py     # YAML loading and validation
└── entity_factory.py      # Clean entity creation
```

## 🚧 Roadmap

### ✅ Completed Features
- [x] **JSON Save/Load System** - Human-readable saves with legacy shelve compatibility
- [x] **Multiple Dungeon Levels** - Stairs and level progression
- [x] **Experience/Leveling** - Character progression with stat choices
- [x] **Progressive Difficulty** - Dynamic scaling with dungeon depth
- [x] **Equipment System** - Weapons and armor with stat bonuses
- [x] **Mouse Movement** - Click-to-move with pathfinding and enemy detection
- [x] **Variable Damage/Defense** - Equipment and monsters with damage/defense ranges
- [x] **Variable Monster Damage** - Dynamic monster combat with natural damage ranges
- [x] **Monster Equipment & Loot** - Monsters spawn with equipment, seek items, use scrolls, and drop loot
- [x] **General Loot Drops** - All monsters drop equipped items and inventory contents
- [x] **Loot Quality & Scaling** - Magic items with rarity tiers and level-scaled drops (v3.8.0)
- [x] **Boss Fights** - Epic encounters with phases, dialogue, enrage, and legendary loot (v3.9.0)
- [x] **Data-Driven Entity System** - YAML configuration for all entities
- [x] **Manual Level Design Tier 1** - Guaranteed spawns via YAML templates
- [x] **Manual Level Design Tier 2** - Level parameters and special themed rooms
- [x] **Slime System** - Monster-vs-monster combat, invisibility, corrosion, splitting
- [x] **Status Effect System** - Invisibility, confusion, disorientation, shield buffs
- [x] **Faction System** - Monster affiliations and targeting priorities
- [x] **Equipment Corrosion** - Weapons and armor can degrade during combat
- [x] **More Scrolls** - Teleport, Shield, Raise Dead, Dragon Fart (4 new scrolls)
- [x] **Configuration Management** - Centralized game constants with file loading
- [x] **Clean Console Output** - TCOD deprecation warnings suppressed
- [x] **Comprehensive Testing** - 1,462 tests with 100% coverage
- [x] **FOV Rendering System** - Robust field-of-view with regression testing
- [x] **Debug Logging System** - Comprehensive monster action and combat logging
- [x] **Turn Phase Management** - Structured turn system with environment phase

### 🔮 Development Roadmap

#### 🟢 **Phase 1: Core Gameplay Enhancements** (Easy - 1-2 weeks each)
- [ ] **Player Naming** - Allow players to enter custom names for personalization
- [ ] **Weapon Speed** - Different attack speeds per weapon type (daggers fast, swords medium, axes slow)
- [ ] **More Spells** - Teleport, invisibility, more tactical options
- [ ] **Extended Equipment** - More weapon types, armor pieces, rings, amulets
- [ ] **Chance to Hit/Dodge** - Enhanced combat mechanics with RNG
- [ ] **Stat Boosting Potions** - Temporary and permanent stat enhancement items
- [x] **JSON Save/Load** - ✅ Complete - Human-readable saves with legacy compatibility
- [ ] **Movement Speed Configuration** - Adjustable mouse movement animation speed

#### 🟡 **Phase 2: Advanced Systems** (Medium - 2-4 weeks each)
- [ ] **Gear Durability** - Equipment degrades with use and can break, requiring repair
- [ ] **Monster Speed Variations** - Different movement speeds for different monster types
- [ ] **Ranged Weapons** - Bows, crossbows with projectile mechanics
- [ ] **More Equipment Slots** - Rings, amulets, boots, helmets
- [ ] **Equipment Sets** - Bonuses for wearing matching equipment pieces
- [ ] **Complex Leveling System** - Feats, skill trees, and character specialization
- [ ] **Player Classes** - Barbarian (high power), Wizard (magical focus), Warrior (balanced) with unique stats and abilities
- [ ] **Entity Inheritance System** - YAML `extends` keyword for creating monster variants and elite versions
- [ ] **Pet System** - Companions that follow and assist the player
- [ ] **Lockable Treasure Chests** - Containers requiring keys or lockpicking
- [ ] **Trap System** - Hidden dangers with detection and disarmament mechanics
- [ ] **Skill System** - Lockpicking, trap detection, stealth, and other abilities
- [ ] **Skill Scrolls** - Consumable items that teach or enhance abilities
- [ ] **Boss Encounters** - Special monsters with unique mechanics
- [ ] **Environmental Hazards** - Poison gas, lava, ice, pressure plates
- [ ] **PC/Mac Distribution** - Packaging and build system setup

#### 🔴 **Phase 3: Major Overhauls** (Hard - 1-3 months each)
- [ ] **Automated Player** - AI that can play the game automatically for testing and demonstration
- [ ] **Better Character UI** - Enhanced inventory and character management
- [ ] **Sound Effects System** - Audio feedback and atmospheric sounds
- [ ] **Modern UI Overhaul** - Complete interface redesign
- [ ] **Sprite-Based Graphics** - Replace ASCII with sprite rendering
- [ ] **Mobile Distribution** - iOS/Android platform adaptation

#### 📊 **Implementation Difficulty Assessment**

| Feature | Difficulty | Time Estimate | Reason |
|---------|------------|---------------|---------|
| More Spells | 🟢 Easy | 1-2 weeks | Framework exists, just add functions |
| Extended Equipment | 🟢 Easy | 1-2 weeks | System designed for expansion |
| Variable Damage | 🟢 Easy | 1 week | Simple RNG modification to combat |
| Variable Defense | 🟢 Easy | 1 week | Similar to variable damage implementation |
| Chance to Hit/Dodge | 🟢 Easy | 1 week | Simple RNG in combat calculations |
| Stat Boosting Potions | 🟢 Easy | 1-2 weeks | Extend existing item system |
| Movement Speed Config | 🟢 Easy | 1 week | Add animation timing to pathfinding |
| Mouse Movement | ✅ Complete | 1 week | Pathfinding exists, add click handling |
| JSON Save/Load | ✅ Complete | 1-2 weeks | Replace existing serialization |
| More Stats | 🟢 Easy | 1 week | Add to existing stat system |
| More Monster Types | 🟢 Easy | 1-2 weeks | AI system supports expansion |
| **Weapon Speed** | 🟢 Easy | 1-2 weeks | Add speed stat to weapons, modify turn order |
| **Gear Durability** | 🟡 Medium | 2-3 weeks | Track usage, implement repair system, UI updates |
| **Monster Speed Variations** | 🟡 Medium | 2-3 weeks | Modify AI turn system, balance gameplay |
| Ranged Weapons | 🟡 Medium | 2-3 weeks | Need targeting system extension |
| More Equipment Slots | 🟡 Medium | 2-3 weeks | UI updates, component changes |
| Equipment Sets | 🟡 Medium | 2-3 weeks | Set detection and bonus logic |
| Complex Leveling | 🟡 Medium | 3-4 weeks | Feats and skill trees system |
| Player Classes | 🟡 Medium | 4-6 weeks | Class-specific abilities and progression |
| **Entity Inheritance System** | 🟡 Medium | 2-3 weeks | YAML extends keyword, monster variants, elite versions |
| Pet System | 🟡 Medium | 3-4 weeks | AI companions with follow behavior |
| Lockable Chests | 🟡 Medium | 2-3 weeks | Key/lockpicking mechanics |
| Trap System | 🟡 Medium | 3-4 weeks | Detection, disarmament, and damage |
| Skill System | 🟡 Medium | 3-5 weeks | Multiple abilities with progression |
| Boss Encounters | 🟡 Medium | 3-4 weeks | Special AI behaviors needed |
| Environmental Hazards | 🟡 Medium | 2-4 weeks | New tile types and mechanics |
| PC/Mac Distribution | 🟡 Medium | 2-3 weeks | Packaging and build setup |
| **Automated Player** | 🔴 Hard | 4-8 weeks | Complex AI system, decision trees, game state analysis |
| Better Character UI | 🔴 Hard | 4-8 weeks | Major UI redesign required |
| Sound Effects | 🔴 Hard | 6-12 weeks | New audio system needed |
| Modern UI Overhaul | 🔴 Very Hard | 2-3 months | Complete interface redesign |
| Sprite Graphics | 🔴 Very Hard | 3-6 months | Major rendering system changes |
| Mobile Distribution | 🔴 Very Hard | 3-6 months | Platform-specific adaptations |

## 📖 Learning Resources

This project is inspired by the classic roguelike tradition and follows patterns from:
- **[Roguelike Tutorial Revised](http://rogueliketutorials.com/)** - TCOD Python tutorial
- **[Game Programming Patterns](https://gameprogrammingpatterns.com/)** - ECS and other patterns
- **[RogueBasin](http://roguebasin.com/)** - Roguelike development community

## 📄 License

**Yarl - Catacombs of Yarl** is licensed under the **GNU General Public License v3.0 (GPL-3.0)**.

This means you're free to:
- ✅ Use, study, and modify the code
- ✅ Distribute copies and modifications
- ✅ Use it for any purpose, including commercial

**BUT** any derivative works must also be open-sourced under GPL-3.0.

**Copyright © 2024-2025 Rafe Hatfield**

For commercial licensing inquiries or questions about alternative licensing, please open an issue on GitHub.

See the [LICENSE](LICENSE) file for complete terms.

## 🙏 Acknowledgments

- **TCOD Library** - Excellent roguelike development framework
- **Roguelike Community** - Inspiration and guidance from RogueBasin and r/roguelikedev
- **Python Community** - Amazing testing and development tools

---

**Happy exploring in the dungeons!** 🗡️🛡️✨