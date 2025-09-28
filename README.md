# Catacombs of Yarl - A Python Roguelike Game

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-729%20passing-brightgreen.svg)](tests/)
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
- **Save/Load system** - Persistent game state across sessions
- **Field of view (FOV)** and line-of-sight calculations
- **Inventory management** with item usage and dropping
- **Health and damage system** with healing mechanics

### Spells & Combat
- **🔥 Fireball** - Area-of-effect damage with targeting (unlocks at level 6)
- **⚡ Lightning** - Single-target high damage to closest enemy (unlocks at level 4)
- **😵 Confusion** - Causes enemies to move randomly for several turns (unlocks at level 2)
- **💚 Healing Potions** - Restore health when injured (available from start)
- **🎯 Progressive item availability** - Better items unlock as you go deeper

### Equipment System
- **⚔️ Weapons** - Swords and daggers that increase attack power
- **🛡️ Armor** - Shields that provide defense bonuses
- **📊 Stat Bonuses** - Equipment modifies power, defense, and max HP
- **🔄 Equipment Slots** - Main hand and off hand equipment management
- **🎒 Inventory Integration** - Seamless equip/unequip from inventory
- **📈 Progressive Equipment** - Better gear unlocks on deeper levels

### AI & Monsters
- **BasicMonster AI** - Tracks and attacks the player using A* pathfinding
- **ConfusedMonster AI** - Random movement with automatic recovery
- **Dynamic AI switching** - Spells can temporarily alter monster behavior
- **Progressive monster scaling** - More and stronger monsters on deeper levels
- **🧌 Orcs** - Basic enemies available from level 1
- **👹 Trolls** - Stronger enemies that become more common on deeper levels (15% → 30% → 60%)

### Technical Features
- **Entity-Component-System (ECS)** architecture
- **A* pathfinding** for intelligent monster movement
- **Equipment system** with stat bonuses and slot management
- **Entity sorting cache** for optimized rendering performance
- **Dynamic difficulty scaling** with configurable progression curves
- **Weighted random selection** for balanced item/monster distribution
- **Save/Load system** using Python's shelve with comprehensive validation
- **Message logging system** for game events
- **Character screen** with level and stat display
- **Robust error handling** throughout the codebase

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
- **Arrow Keys** - Move your character (@)
- **Mouse Click** - Target spells (fireball, confusion)
- **g** - Pick up items
- **i** - Open inventory
- **d** - Drop items
- **Enter** - Take stairs to next level
- **c** - Open character screen (view level, XP, stats)
- **s** - Save game
- **l** - Load game
- **Escape** - Exit menus/game

### Gameplay Tips
- **Stay healthy** - Use healing potions when injured
- **Use spells wisely** - Fireball affects multiple enemies, confusion disables threats
- **Manage inventory** - Limited carrying capacity, drop items you don't need
- **Tactical positioning** - Use corridors to fight enemies one-at-a-time
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
- **Perfect for testing** inventory, targeting, equipment, and spell mechanics

### Test Suite

This project maintains **100% test coverage** with a comprehensive test suite covering all game systems.

### Running Tests

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests (659 tests)
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
- **659 tests** with **100% pass rate**
- **Entity System** - Movement, pathfinding, A* algorithm
- **Combat System** - Attack, defense, healing, death mechanics, XP rewards
- **Equipment System** - Equipment slots, stat bonuses, equip/unequip mechanics
- **Inventory System** - Item management, capacity limits, equipment integration
- **Spell System** - All spells including confusion mechanics and targeting
- **AI System** - BasicMonster and ConfusedMonster behavior
- **Message System** - Game event logging and display
- **Difficulty Scaling** - Progressive monster/item scaling, weighted selection
- **Save/Load System** - Game state persistence, validation, error handling
- **Character Progression** - XP system, leveling, stat increases
- **Dungeon Levels** - Multi-floor generation, stairs, level transitions
- **FOV & Rendering System** - Field of view calculations, map rendering, visual regression prevention
- **Game Engine Integration** - System coordination, state management, performance optimization
- **Regression Testing** - Automated prevention of critical bugs (FOV, combat, death system)
- **Integration Testing** - End-to-end system interaction validation

## 🏗️ Architecture

### Project Structure
```
rlike/
├── components/          # ECS Components
│   ├── ai.py           # AI behaviors (BasicMonster, ConfusedMonster)
│   ├── equipment.py    # Equipment slot management and stat bonuses
│   ├── equippable.py   # Equippable item component with bonuses
│   ├── fighter.py      # Combat stats and methods with XP rewards
│   ├── inventory.py    # Item storage and equipment management
│   ├── item.py         # Item component definition
│   └── level.py        # XP and leveling system
├── config/             # Centralized configuration system
│   ├── game_constants.py    # All game constants and configuration
│   └── testing_config.py    # Testing mode configuration
├── loader_functions/   # Game initialization and save/load
│   ├── initialize_new_game.py  # New game setup
│   └── data_loaders.py         # Save/load functionality
├── map_objects/        # Map generation and tiles
│   ├── game_map.py     # Dungeon generation with difficulty scaling
│   ├── rectangle.py    # Room generation utilities
│   └── tile.py         # Tile properties (walkable, transparent)
├── tests/              # Comprehensive test suite (729 tests)
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
Run the full test suite with 690+ tests:
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

## 🚧 Roadmap

### ✅ Completed Features
- [x] **Save/Load System** - Persistent game state with validation
- [x] **Multiple Dungeon Levels** - Stairs and level progression
- [x] **Experience/Leveling** - Character progression with stat choices
- [x] **Progressive Difficulty** - Dynamic scaling with dungeon depth
- [x] **Equipment System** - Weapons and armor with stat bonuses
- [x] **Comprehensive Testing** - 659 tests with 100% coverage
- [x] **FOV Rendering System** - Robust field-of-view with regression testing

### 🔮 Future Enhancements
- [ ] **More Spells** - Teleport, invisibility, more tactical options
- [ ] **Extended Equipment** - More weapon types, armor pieces, rings, amulets
- [ ] **Equipment Sets** - Bonuses for wearing matching equipment pieces
- [ ] **More Monster Types** - Varied AI behaviors and abilities
- [ ] **Boss Encounters** - Special monsters on certain levels
- [ ] **Environmental Hazards** - Traps and obstacles
- [ ] **Equipment Crafting** - Player-created equipment and upgrades
- [ ] **Sound Effects** - Audio feedback for actions
- [ ] **Configuration System** - Customizable controls and settings
- [ ] **Mobile Distribution** - iOS/Android compatibility exploration

## 📖 Learning Resources

This project is inspired by the classic roguelike tradition and follows patterns from:
- **[Roguelike Tutorial Revised](http://rogueliketutorials.com/)** - TCOD Python tutorial
- **[Game Programming Patterns](https://gameprogrammingpatterns.com/)** - ECS and other patterns
- **[RogueBasin](http://roguebasin.com/)** - Roguelike development community

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **TCOD Library** - Excellent roguelike development framework
- **Roguelike Community** - Inspiration and guidance from RogueBasin and r/roguelikedev
- **Python Community** - Amazing testing and development tools

---

**Happy exploring in the dungeons!** 🗡️🛡️✨