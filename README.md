# RLike - A Python Roguelike Game

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-135%20passing-brightgreen.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)](tests/)

A classic roguelike game built in Python using the TCOD library. Features turn-based combat, procedural dungeon generation, spell casting, and AI-driven monsters with various behaviors including confusion mechanics.

## 🎮 Features

### Core Gameplay
- **Turn-based combat** with attack/defense mechanics
- **Procedural dungeon generation** with rooms and corridors
- **Field of view (FOV)** and line-of-sight calculations
- **Inventory management** with item usage and dropping
- **Health and damage system** with healing mechanics

### Spells & Combat
- **🔥 Fireball** - Area-of-effect damage with targeting
- **⚡ Lightning** - Single-target high damage to closest enemy
- **😵 Confusion** - Causes enemies to move randomly for several turns
- **💚 Healing Potions** - Restore health when injured

### AI & Monsters
- **BasicMonster AI** - Tracks and attacks the player using A* pathfinding
- **ConfusedMonster AI** - Random movement with automatic recovery
- **Dynamic AI switching** - Spells can temporarily alter monster behavior

### Technical Features
- **Entity-Component-System (ECS)** architecture
- **A* pathfinding** for intelligent monster movement
- **Message logging system** for game events
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
   python engine.py
   ```

## 🎯 How to Play

### Controls
- **Arrow Keys** - Move your character (@)
- **Mouse Click** - Target spells (fireball, confusion)
- **g** - Pick up items
- **i** - Open inventory
- **d** - Drop items
- **Escape** - Exit menus/game

### Gameplay Tips
- **Stay healthy** - Use healing potions when injured
- **Use spells wisely** - Fireball affects multiple enemies, confusion disables threats
- **Manage inventory** - Limited carrying capacity, drop items you don't need
- **Tactical positioning** - Use corridors to fight enemies one-at-a-time

## 🧪 Testing

This project maintains **100% test coverage** with a comprehensive test suite covering all game systems.

### Running Tests

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests (135 tests)
pytest

# Run with coverage reporting
pytest --cov=. --cov-report=term-missing

# Run specific test categories
pytest tests/test_entity.py -v        # Entity and AI systems
pytest tests/test_item_functions.py -v # Spells and items
pytest tests/test_inventory.py -v      # Inventory management
pytest tests/test_fighter.py -v       # Combat system
pytest tests/test_game_messages.py -v # Message logging
```

### Test Coverage
- **135 tests** with **100% pass rate**
- **Entity System** - Movement, pathfinding, A* algorithm
- **Combat System** - Attack, defense, healing, death mechanics
- **Inventory System** - Item management, capacity limits, error handling
- **Spell System** - All spells including new confusion mechanics
- **AI System** - BasicMonster and ConfusedMonster behavior
- **Message System** - Game event logging and display

## 🏗️ Architecture

### Project Structure
```
rlike/
├── components/          # ECS Components
│   ├── ai.py           # AI behaviors (BasicMonster, ConfusedMonster)
│   ├── fighter.py      # Combat stats and methods
│   ├── inventory.py    # Item storage and management
│   └── item.py         # Item component definition
├── map_objects/        # Map generation and tiles
│   ├── game_map.py     # Dungeon generation and entity placement
│   ├── rectangle.py    # Room generation utilities
│   └── tile.py         # Tile properties (walkable, transparent)
├── tests/              # Comprehensive test suite
│   ├── conftest.py     # Test fixtures and mocking
│   ├── test_*.py       # Test modules for each component
│   └── __init__.py
├── engine.py           # Main game loop and entry point
├── entity.py           # Base entity class with movement/pathfinding
├── item_functions.py   # Spell implementations (heal, fireball, etc.)
├── input_handlers.py   # Keyboard and mouse input processing
├── render_functions.py # Display and rendering logic
├── game_messages.py    # Message logging system
├── game_states.py      # Game state management
└── requirements.txt    # Project dependencies
```

### Key Design Patterns
- **Entity-Component-System (ECS)** - Flexible entity composition
- **Command Pattern** - Input handling and game actions
- **State Machine** - Game state management (playing, inventory, targeting)
- **Strategy Pattern** - AI behavior switching (normal → confused → normal)

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

### Contributing
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for your changes
4. Make your changes
5. Ensure all tests pass (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

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

- [ ] **Save/Load System** - Persistent game state
- [ ] **Multiple Dungeon Levels** - Stairs and level progression
- [ ] **More Spells** - Teleport, invisibility, more tactical options
- [ ] **Equipment System** - Weapons and armor with stat bonuses
- [ ] **Experience/Leveling** - Character progression
- [ ] **More Monster Types** - Varied AI behaviors and abilities
- [ ] **Sound Effects** - Audio feedback for actions
- [ ] **Configuration System** - Customizable controls and settings

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