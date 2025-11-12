# 🏰 Catacombs of Yarl

A professional-grade roguelike game written in Python with complete story arc, advanced procedural generation, sophisticated difficulty balancing, and modern ECS architecture.

**Current Status:** v3.15.0 - Advanced Level Generation & Telemetry Complete | 2500+ Tests Passing | 131+ Documentation Files

---

## 🎮 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the game (normal mode)
python engine.py

# Run with testing mode (more items, debug features)
python engine.py --testing

# Run with telemetry collection (gameplay metrics)
python engine.py --telemetry-json telemetry.json

# Combine flags
python engine.py --testing --start-level 10 --telemetry-json output/session.json

# Run tests
pytest tests/

# Run specific test suite
pytest tests/test_portal_system_phase_b.py -v
```

---

## 📊 Executive Summary

### What Is Yarl?

A **professional-grade roguelike** built with Python and libtcod, featuring:

- **Complete story arc** with 5 narrative phases leading to a climactic victory condition
- **Advanced level generation** with procedural room layouts, connectivity algorithms, and intelligent spawn placement
- **Sophisticated difficulty balancing** through ETP (Encounter Threat Points) budgeting
- **Portal system** with emergent AI interactions
- **Dynamic hazards** including traps, secret rooms, locked doors, and multi-floor persistence
- **100+ unique items** across multiple categories (potions, scrolls, wands, rings, equipment)
- **50+ monster types** with distinct AI behaviors, faction systems, and contextual hostility overrides
- **30+ spells** with targeting modes and diverse effects
- **Loot pity mechanics** for balanced item distribution across difficulty bands
- **Comprehensive telemetry** for gameplay analytics and balance tuning
- **Professional test coverage** (2500+ tests, ~45% of codebase)
- **Clean architecture** (ECS-based, event-driven, modular design)

### Current Capabilities

| Aspect | Status | Details |
|--------|--------|---------|
| **Story** | ✅ COMPLETE | Phases 1-5 with 6 distinct endings |
| **Gameplay** | ✅ CORE COMPLETE | Combat, exploration, loot identification |
| **Portal System** | ✅ COMPLETE | Phase A + B with monster AI |
| **Environmental Lore** | ✅ COMPLETE | Signposts, murals, easter eggs |
| **Advanced Level Generation** | ✅ COMPLETE | Doors, secret rooms, traps, stairs, connectivity |
| **Difficulty Balancing** | ✅ COMPLETE | ETP budgets, encounter scaling, loot pity |
| **Multi-Floor Persistence** | ✅ COMPLETE | State preservation, respawn caps, anti-farming |
| **Faction System** | ✅ COMPLETE | Dynamic hostility, AI behavior mods, room context |
| **Telemetry & Validation** | ✅ COMPLETE | Schema validation, gameplay metrics, JSON export |
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

### Advanced Level Generation (Latest)

Yarl features sophisticated procedural dungeon generation with multiple interconnected systems:

#### Door System
- **Corridor doors** placed at room-to-room connections
- **Locked doors** requiring keys (customizable key tags)
- **Secret doors** rendering as walls until discovered
- **Search DC** for detecting secrets via detection roll
- **Spawn ratio** control (0.0-1.0) for door frequency

#### Secret Rooms
- **Hidden chambers** carved from solid walls adjacent to corridors
- **Ambient hints** marking secret locations for perceptive players
- **Discovery mechanics** via search action or map item triggers
- **Target allocation** to guarantee X secret rooms per floor
- **Themed connections** via secret doors with matching styles

#### Trap System
- **Three trap types:**
  - **Spike Traps** - On-step damage + bleed status effect
  - **Web Traps** - Slow/snare debuff lasting N turns
  - **Alarm Plates** - Alert faction-aligned mobs within radius
- **Detectable traps** with passive and active detection
- **Disarming** via search action
- **Customizable density** per room/level

#### Connectivity & Corridor Styles
- **Minimum Spanning Tree (MST)** for guaranteed connectivity
- **MST + Loops** option for maze-like dungeons
- **Three corridor styles:**
  - **Orthogonal** - Straight corridors (traditional)
  - **Jagged** - Zigzag patterns (organic)
  - **Organic** - Curved/meandering (atmospheric)
- **Door sprinkling** at configurable intervals

#### Multi-Floor Persistence
- **Floor state saving** preserves entities across level transitions
- **Despawn mechanics** remove distant mobs to prevent farming
- **Door memory** persists opened/locked state
- **Respawn caps** limit new spawns on re-entry
- **Restrict return levels** enforces dungeon progression rules

**Example Configuration:**
```yaml
level_overrides:
  10:
    door_rules:
      spawn_ratio: 0.8
      styles: [{type: "wooden_door", weight: 70}, {type: "iron_door", weight: 30}]
      locked: {chance: 0.3, key_tag: "iron_key"}
      secret: {chance: 0.1, search_dc: 15}
    
    secret_rooms:
      target_per_floor: 2
      min_room_size: 4
      connection_bias: "dead_end"
      discovery:
        auto_on_map_item: null
        search_action: true
        ambient_hint: "Strange draft of air"
    
    trap_rules:
      density: 0.15
      whitelist_rooms: ["crypt"]
      trap_table:
        - {id: "spike_trap", weight: 60}
        - {id: "web_trap", weight: 30}
        - {id: "alarm_plate", weight: 10}
      detection:
        passive_chance: 0.15
        reveal_on: ["scroll_identify"]
    
    stairs:
      up: true
      down: true
      restrict_return_levels: 3
      spawn_rules:
        near_start_bias: 0.7
    
    connectivity:
      min_connectivity: "mst_plus_loops"
      loop_count: 3
      corridor_style: "organic"
      door_every_n_tiles: 6
```

### Encounter Difficulty Balancing (Latest)

Sophisticated ETP (Encounter Threat Points) system for balanced difficulty:

#### ETP System
- **Per-entity ETP values** define encounter difficulty
- **Per-room budgets** constrain total difficulty
- **Per-level budgets** enforce floor-wide scaling
- **Spike mechanics** allow controlled difficulty peaks (bosses)

#### Budget Mechanics
```python
encounter_budget:
  etp_min: 20          # Minimum threat per room
  etp_max: 50          # Maximum threat per room
  allow_spike: true    # Can exceed max by one entity
```

#### Spawn Trimming
- Auto-selects spawn candidates that fit budget
- Partial counts when needed (3 orcs → 2 orcs to fit)
- Removes excess candidates in order
- Full telemetry on trimming decisions

#### Anti-Farming & Pity
- **Loot pity mechanics** track item categories across floors
- **Soft bias** increases weight for underrepresented categories
- **Hard pity** injects items if drought exceeds threshold
- **Rolling windows** prevent clustering of item types

**Example:**
```yaml
level_overrides:
  15:
    encounter_budget:
      etp_min: 30
      etp_max: 45
      allow_spike: false
    
    loot_policy:
      bands:
        B3:
          heal_ev: 2.5
          escape_ev: 1.8
          id_ev: 1.2
          upgrade_ev: 0.8
      pity:
        window_floors: 5
        soft_bias_factor: 1.5
        hard_inject_at: 3  # Inject if missing 3+ floors
```

### Faction System (Latest)

Dynamic hostility and AI behavior modification within special rooms:

#### Hostility Overrides
- **Room-specific faction relationships** override global rules
- **Per-faction targeting** determines attack priorities
- **Emergent conflicts** - Orcs vs Undead in necropolis

#### Behavior Modifications
- **AI parameter tweaking** for specific monster types
- **Context-aware behavior** (door priority, aggression radius)
- **Automatic restoration** when leaving room

**Example Configuration:**
```yaml
special_rooms:
  - type: "necropolis"
    min_room_size: 5
    faction:
      room_tag: "necropolis"
      hostility_matrix:
        orc: ["undead", "skeleton"]
        undead: ["orc", "human"]
        human: []
      behavior_mods:
        orc: {door_priority: 0.8, aggression_radius: 12}
        troll: {door_priority: 1.5}
```

### Portal System (Existing)

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

Monsters now intelligently use portals (respecting their `portal_usable` flag) and respond to faction overrides within special rooms.

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
- TrapSystem - Hazard detection and triggering
- FactionEngine - Hostility and behavior overrides
- FloorStateManager - Multi-floor persistence
- EncounterBudgetEngine - ETP-based difficulty scaling
- LootController - Pity mechanics and item balancing
- TelemetryService - Gameplay metrics collection

**Content:**
- EntityFactory - Data-driven entity creation
- LevelTemplateRegistry - YAML-based level definitions with validation
- ConfigRegistry - Game constants and settings
- ItemSystem - Stacking, equipment, identification
- SpellSystem - Casting, targeting, effects

**Infrastructure:**
- Save/Load persistence
- Performance profiling
- Memory optimization
- Event logging
- Telemetry export

### Code Quality

- **2500+ tests** across all systems
- **~131+ documentation files** covering architecture and development
- **Type hints** throughout codebase
- **Modular design** with clear separation of concerns
- **One file per responsibility** principle
- **Template validation** with actionable error messages

### Project Statistics

- **113K+ lines** of production code
- **55K+ lines** of test code
- **330+ Python files** organized into logical modules
- **11+ YAML files** for data-driven content
- **Ratio:** Nearly 1:1 test to production code

See [PROJECT_STATS.md](PROJECT_STATS.md) for detailed breakdown.

---

## 📊 Telemetry & Diagnostics

### Telemetry Collection

Comprehensive gameplay metrics collection for balance tuning and analytics:

```bash
# Run with telemetry enabled
python engine.py --telemetry-json telemetry.json
```

**Metrics Per Floor:**
- `depth` - Floor number
- `etp_sum` - Total encounter threat points
- `etp_budget_min/max` - Budget constraints if configured
- `ttk_hist` - Time-to-kill damage values (mob deaths)
- `ttd_hist` - Time-to-death values (player damage taken)
- `traps_triggered` - Count of traps sprung
- `traps_detected` - Count of traps found
- `secrets_found` - Secret rooms discovered
- `doors_opened/unlocked` - Door interactions
- `keys_used` - Key consumption
- `pity_events` - Loot balancing triggers
- `room_count/monster_count/item_count` - Spawn statistics

**Output Format:**
```json
{
  "generated_at": "2025-11-12T14:32:45.123456",
  "floor_count": 15,
  "floors": [
    {
      "depth": 1,
      "timestamp": "2025-11-12T14:32:10.000000",
      "etp_sum": 42,
      "ttk_hist": [15, 20, 18, 12],
      "traps_triggered": 2,
      "secrets_found": 1,
      "doors_opened": 3,
      "keys_used": 2,
      "pity_events": [{"event_type": "soft_bias", "category": "heal"}]
    }
  ]
}
```

### Template Validation

Comprehensive validation of YAML configurations:

**Validation Checks:**
- Entity IDs exist in entity factory
- Count ranges are valid (min <= max)
- Modes and placements are valid enums
- Special room sizes fit within level constraints
- Encounter budgets are internally consistent
- Level parameters align with spawn configs

**Error Reporting:**
```
Invalid monster entity type 'invalid_orc' does not exist
File: config/level_templates.yaml
Key: level_overrides.15.guaranteed_spawns.monsters[0].type
```

---

## 🎮 Gameplay Features

### Exploration

- **25-level dungeon** scaling in difficulty
- **Random room generation** with multiple connectivity styles
- **FOV-based exploration** with memory of explored areas
- **Interactive features** (signposts, murals, chests)
- **Dynamic hazards** (traps, secret rooms, locked doors)
- **Easter eggs** for observant players

### Turn Economy

- **Traditional roguelike turns** - Player moves, then all monsters move
- **Action types** - Movement, attacking, item usage, spells
- **Wait action** - Pass turn while staying in place
- **Auto-explore** - Automated movement through safe areas (respects doors)

### Combat

- **Real-time feedback** on damage and effects
- **Resistance system** affects damage taken
- **Status effects** change combat dynamics
- **Tactical positioning** matters
- **Equipment affects stats** (damage, AC, resistances)
- **Faction-aware combat** in special rooms

### Itemization

- **Identification system** reveals magical properties
- **Equipment slots** for equipped gear bonuses
- **Rarity tiers** (common → legendary)
- **Stacking** of consumable items
- **Special effects** (resistances, stat bonuses, curses)
- **Loot pity** ensures balanced category distribution

---

## 🧪 Testing & Quality

### Test Coverage

- **Portal System:** 91/91 tests passing (Phase A + B complete)
- **Combat System:** 200+ tests
- **Item System:** 150+ tests
- **AI System:** 180+ tests
- **Level Generation:** 100+ tests
- **Integration Tests:** 800+ tests
- **Total:** 2500+ tests with 100% pass rate on critical paths

### Performance

- **60 FPS** maintained throughout
- **Sub-50ms** input response time
- **Rendering optimization** with entity cache
- **Memory efficient** with pooling and optimization
- **Pathfinding** optimized with caching

### Code Quality

- **Type hints** throughout
- **Comprehensive docstrings**
- **Error handling** with clear messages
- **Logging** at appropriate levels
- **Modular architecture** for maintainability
- **Schema validation** with actionable errors

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

- **Level Generation:** [docs/YAML_ROOM_GENERATION_SYSTEM.md](docs/YAML_ROOM_GENERATION_SYSTEM.md)
- **Portal System:** [docs/development/portal/README.md](docs/development/portal/README.md)
- **Story Arcs:** [docs/development/phase4/](docs/development/phase4/) & [phase5/](docs/development/phase5/)
- **Architecture:** [docs/architecture/README.md](docs/architecture/README.md)

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
- ✅ Advanced level generation (doors, secrets, traps, stairs)
- ✅ Multi-floor persistence
- ✅ Difficulty balancing (ETP system)
- ✅ Faction system
- ✅ Loot pity mechanics
- ✅ Telemetry & validation

### Planned Features

- 🔄 Vaults & advanced room types
- 🔄 Religion/god system
- 🔄 Shop system
- 🔄 Amulet system
- 🔄 Polymorph mechanics
- 🔄 Wish system
- 🔄 Named unique artifacts
- 🔄 Advanced companion systems

---

## 🎓 Design Highlights

### Emergent Gameplay

The portal system exemplifies emergent design:

- **No scripted monster behavior** for portals
- But monsters can pick up inventory items
- And use teleportation mechanics
- **Result:** Orcs unexpectedly chase through your portals!
- **Bosses have flags** to avoid this (tactical advantage)

Similarly, the faction system creates emergent conflicts:
- No hardcoded "orcs attack undead" logic
- But orc and undead entities have faction tags
- And necropolis room has hostility override
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
- Makes debugging, testing, and extending straightforward

---

## 📝 Code Example: Configuring a Level

```yaml
# config/level_templates.yaml
level_overrides:
  12:
    mode: "replace"
    parameters:
      room_count: 10
      max_room_size: 15
      max_monsters_per_room: 5
    
    # Doors at corridor connections
    door_rules:
      spawn_ratio: 0.9
      styles:
        - {type: "wooden_door", weight: 70}
        - {type: "iron_door", weight: 30}
      locked:
        chance: 0.2
        key_tag: "iron_key"
      secret:
        chance: 0.05
        search_dc: 13
    
    # Secret rooms in solid walls
    secret_rooms:
      target_per_floor: 2
      min_room_size: 4
      connection_bias: "dead_end"
      discovery:
        search_action: true
        ambient_hint: "Strange musty smell"
    
    # Hazardous traps
    trap_rules:
      density: 0.12
      trap_table:
        - {id: "spike_trap", weight: 60}
        - {id: "web_trap", weight: 30}
        - {id: "alarm_plate", weight: 10}
      detection:
        passive_chance: 0.15
    
    # Difficulty scaling
    encounter_budget:
      etp_min: 25
      etp_max: 40
      allow_spike: false
    
    # Guaranteed spawns
    guaranteed_monsters:
      - {type: "orc", count: "2-4"}
      - {type: "goblin", count: "3-6"}
```

---

## 🤝 Contributing

### Adding Features

1. **Plan** - Document what you're adding
2. **Architect** - Design how it fits existing systems
3. **Implement** - Code the feature
4. **Test** - Write comprehensive tests
5. **Document** - Update relevant docs
6. **Validate** - Ensure YAML templates validate

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
- Search suspicious walls for secrets
- Be cautious with traps (passive detection helps!)
- Respect locked doors (find keys first)

---

## 🏆 Achievements

- ✅ Complete story arc with multiple endings
- ✅ Advanced procedural level generation with 5+ interconnected systems
- ✅ Sophisticated difficulty balancing through ETP budgeting
- ✅ Multi-floor persistence with anti-farming mechanics
- ✅ Professional-grade test coverage (2500+ tests)
- ✅ Clean, modular architecture (ECS-based)
- ✅ Rich content (100+ items, 50+ monsters)
- ✅ Advanced AI with emergent behavior
- ✅ Portal system with monster interaction
- ✅ Faction system with dynamic hostility
- ✅ Comprehensive telemetry & analytics
- ✅ Template validation with actionable errors
- ✅ Comprehensive documentation (131+ files)
- ✅ Optimized performance (60 FPS)

---

## 📞 Support & Information

### Questions?

- See [DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md) for architecture philosophy
- See [docs/architecture/](docs/architecture/) for system design
- See [docs/development/](docs/development/) for implementation details
- See [TRADITIONAL_ROGUELIKE_FEATURES.md](TRADITIONAL_ROGUELIKE_FEATURES.md) for feature roadmap
- See [docs/YAML_ROOM_GENERATION_SYSTEM.md](docs/YAML_ROOM_GENERATION_SYSTEM.md) for level generation

### Bug Reports

If you find issues:
1. Check existing tests (might be known limitation)
2. Write a failing test that reproduces the bug
3. Fix the bug (test should pass)
4. Add regression test
5. Validate templates if YAML-related

---

## 📄 License

[See LICENSE file](LICENSE)

---

## 🎉 Thanks

Built with passion for roguelikes and clean architecture.

**Yarl: Where classic roguelike gameplay meets modern design principles.**

---

**Last Updated:** November 2025 | Advanced Level Generation, Difficulty Balancing, and Telemetry Complete

**Next Session:** Playtesting, balance tuning, and gameplay refinement
