# 🗺️ **Yarl Development Roadmap: Sorted by Complexity & Impact**

*Last Updated: October 2025 - Equipment System Overhaul Complete*

This roadmap organizes all planned features by implementation complexity and gameplay impact, helping prioritize development efforts for maximum player enjoyment.

---

## ✅ **Recently Completed: Equipment System Overhaul** (v3.0.0)

**🎉 Major Equipment & Combat System Transformation** (October 2025)

Complete D&D-style equipment system with dice notation, 12 new weapons, and full stat integration:

### **What Was Accomplished**
- **🎲 D&D Dice Notation**: Full dice rolling system (1d4, 2d6+3, 1d20, etc.)
- **⚔️ 12 New Weapons**: Dagger (1d4) → Greatsword (2d6), covering all power levels
- **🎯 Weapon Properties**: Finesse weapons (+1 to-hit), Unwieldy weapons (-1 to-hit)
- **🛡️ Armor System**: Light/Medium/Heavy armor with DEX caps
- **📊 Equipment Slots**: Weapon, Shield, Head, Chest, Feet
- **💪 Full Stat System**: STR/DEX/CON with proper modifiers
- **🎯 d20 Combat**: Attack rolls, AC calculation, critical hits, fumbles
- **📱 Character Screen**: Beautiful slot-based UI showing all equipment
- **🧪 Production Quality**: All 1,575 tests passing, 100% coverage

### **Weapons Added**
- **Light (1d4)**: Dagger (+1 to-hit, finesse)
- **One-Handed (1d6)**: Club, Shortsword (+1 to-hit), Mace
- **One-Handed (1d8)**: Longsword, Rapier (+1 to-hit), Spear
- **Heavy (1d10)**: Battleaxe, Warhammer
- **Two-Handed**: Greataxe (1d12, -1 to-hit), Greatsword (2d6)

### **Benefits Realized**
- **🎮 Players**: 12 weapon choices, strategic builds (finesse vs strength)
- **⚔️ Combat**: D&D-familiar mechanics, tactical depth, clear feedback
- **🎨 Display**: Clean dice notation ("1d4+2" instead of "1-4+2")
- **📈 Scalability**: Easy to add more weapons, armor types, and properties

---

## ✅ **Previously Completed: Spell & AI System Expansion** (v2.7.0)

**🎉 Major Spell & AI System Expansion** (October 2025)

Complete overhaul of spell system, AI behaviors, and monster-vs-monster combat:

### **What Was Accomplished**
- **🌀 Teleport Scroll**: Instant repositioning with 10% misfire chance (disorientation)
- **🛡️ Shield Scroll**: Temporary +4 defense buff (10% monster backfire)
- **🧟 Raise Dead Scroll**: Resurrect corpses as mindless zombie allies
- **💨 Dragon Fart Scroll**: Directional cone of noxious gas (20-turn knockout)
- **🤖 MindlessZombieAI**: Sticky targeting, FOV-based hunting, attacks anything
- **🎯 Status Effect System**: Disorientation and shield effects
- **🐌 Slime Loot Fix**: Slimes no longer drop equipment
- **🧪 Production Quality**: All 1,462 tests passing, 100% coverage

### **Benefits Realized**
- **🎮 Players**: 4 new tactical scrolls, zombie summoning, enhanced combat variety
- **🤖 AI Systems**: Sophisticated zombie AI with FOV and sticky targeting
- **🐛 Bug Fixes**: Slime splitting on valid tiles, proper loot drops
- **📈 Scalability**: Foundation for more complex spells and AI behaviors

---

## ✅ **Previously Completed: Entity Configuration System** (v2.0.0)

**🎉 Major Architecture Achievement** (December 2024)

The entire entity creation system has been transformed from hardcoded values to a clean, data-driven architecture:

### **What Was Accomplished**
- **🏗️ Complete Code Transformation**: 55+ lines of hardcoded entity creation → 6 clean factory calls
- **📊 Data-Driven Design**: All monsters, weapons, armor configured via `config/entities.yaml`
- **🔧 Configuration Management**: Centralized game constants with GameConstants integration
- **🧪 Production Quality**: 71 comprehensive tests ensuring 100% backward compatibility
- **⚡ Zero Regressions**: All 1,200+ tests pass, perfect migration execution

### **Benefits Realized**
- **🎨 Game Designers**: Edit monster stats, weapon damage, armor defense via YAML
- **🚀 Developers**: Clean EntityFactory pattern, robust error handling, type safety
- **🔄 Extensibility**: Foundation ready for entity inheritance, modding, variants
- **📈 Maintainability**: Centralized configuration, consistent patterns, easy testing

### **Architecture Excellence**
```yaml
# Before: 30+ lines of hardcoded Fighter/Entity creation per monster
if monster_choice == "orc":
    fighter_component = Fighter(hp=20, defense=0, power=4, xp=35)
    # ... more hardcoded properties ...

# After: 1 line using EntityFactory
monster = entity_factory.create_monster("orc", x, y)
```

This establishes the **gold standard** for data-driven game development in Python roguelikes.

---

## 🟢 **Phase 1: Quick Wins & High Impact** (1-2 weeks each)

These features build on existing systems and provide immediate gameplay improvements with minimal risk.

### **🎯 Combat & Mechanics (Immediate Fun)**

| Feature | Time | Impact | Why Now | Technical Notes |
|---------|------|--------|---------|-----------------|
| **Variable Damage** | ✅ Complete (v3.0) | 🔥 High | D&D dice notation (1d4, 2d6) for dynamic combat | Dice rolling system with full notation support |
| **Variable Defense** | ✅ Complete (v3.0) | 🔥 High | Armor provides variable protection | Defense ranges integrated with dice system |
| **Variable Monster Damage** | ✅ Complete (v3.0) | 🔥 High | Monsters use dice-based damage like players | All entities use unified dice combat system |
| **Chance to Hit/Dodge** | ✅ Complete (v3.0) | 🔥 High | d20 attack rolls vs AC for tactical depth | Full d20 combat with critical hits/fumbles |
| **More Spells** | ✅ Complete (v2.7) | 🔥 High | 8 tactical scrolls (teleport, invisibility, etc.) | Comprehensive spell system with status effects |
| **Monster Equipment & Loot** | 1-2 weeks | 🔥 High | Monsters can wield weapons/armor and drop them | Equipment system for monsters, loot drops |
| **General Loot Drops** | 1 week | 🔥 High | All monsters drop items when defeated | Death event handling, loot table system |

**Combined Impact:** Transforms combat from predictable to dynamic and tactical.

### **🎒 Equipment & Progression (Player Retention)**

| Feature | Time | Impact | Why Now | Technical Notes |
|---------|------|--------|---------|-----------------|
| **Rings & Amulets** | 1 week | 🔥 High | 2 new equipment slots for magical effects | Slots exist, just add items with special effects |
| **Extended Equipment** | 1-2 weeks | 🔥 High | More loot variety = more exploration motivation | System designed for easy expansion |
| **More Stats on Equipment** | 1 week | 🔥 High | Makes loot more interesting and build diversity | Add to existing stat system |
| **Stat Boosting Potions** | 1-2 weeks | 🔥 High | Tactical consumables add resource management | Extend existing item system |

**Combined Impact:** Creates meaningful loot progression and tactical resource decisions.

**Note on Rings & Amulets:** Equipment system is ready for 2 more slots. These would provide magical bonuses (HP regen, resistance, special abilities). Low complexity since infrastructure exists - just need item definitions and slot UI updates.

### **🎮 Quality of Life (Polish)**

| Feature | Time | Impact | Why Now | Technical Notes |
|---------|------|--------|---------|-----------------|
| **Movement Speed Config** | 1 week | 🔥 High | Makes mouse movement feel perfect for each player | Add animation timing to pathfinding |
| **Player Naming** | 1 week | 🔥 High | Allow players to enter custom names for personalization | Add name input dialog at game start |
| **More Monster Types** | 1-2 weeks | 🔥 High | Keeps exploration fresh and challenging | AI system supports easy expansion |
| **Multi-Save Games** | 2-3 weeks | 🔥 High | Multiple save slots with metadata display | Save slot UI, file management, save previews |
| **JSON Save/Load** | ✅ Complete | 🔶 Medium | Human-readable saves, easier debugging | Replace existing shelve serialization |

**Combined Impact:** Polishes the core experience and improves development workflow.

---

## 🟡 **Phase 2: Game-Changing Systems** (2-6 weeks each)

These features add new gameplay dimensions and significantly expand the game's depth.

### **🏹 Advanced Combat (2-4 weeks)**

| Feature | Time | Impact | Complexity | Technical Requirements |
|---------|------|--------|------------|----------------------|
| **Ranged Weapons** | 2-3 weeks | 🔥 High | Need targeting system extension | Projectile mechanics, line-of-sight calculations |
| **Boss Encounters** | 3-4 weeks | 🔥 High | Special AI behaviors and mechanics | Custom AI states, unique abilities |
| **Environmental Hazards** | 2-4 weeks | 🔥 High | Traps, poison, lava - tactical positioning | New tile types, damage-over-time systems |
| **Manual Level Design - Tier 1** | ✅ Complete | 🔥 High | Guaranteed spawns for testing (YAML-based) | Template system with mode control (additional/replace) |
| **Manual Level Design - Tier 2** | 2-3 weeks | 🔥 High | Level parameters & special rooms | Room count/size control, themed room types |
| **Manual Level Design - Tier 3** | 3-4 weeks | 🔥 High | Full level crafting with ASCII maps | Custom maps, precise entity placement, boss arenas |

**Combined Impact:** Adds strategic depth and memorable encounters.

### **🎭 Character Depth (3-6 weeks)**

| Feature | Time | Impact | Complexity | Technical Requirements |
|---------|------|--------|------------|----------------------|
| **Player Classes** | 4-6 weeks | 🔥 High | Warrior/Mage/Rogue with unique abilities | Class-specific progression, ability systems |
| **Complex Leveling** | 3-4 weeks | 🔥 High | Feats, skill trees, specialization | Feat system, prerequisite checking |
| **Skill System** | 3-5 weeks | 🔥 High | Lockpicking, stealth, trap detection | Multiple skill mechanics with progression |

**Combined Impact:** Massive replayability boost through character customization.

### **🏆 Equipment Evolution (2-3 weeks)**

| Feature | Time | Impact | Complexity | Technical Requirements |
|---------|------|--------|------------|----------------------|
| **More Equipment Slots** | 2-3 weeks | 🔥 High | Rings, amulets, boots, helmets | UI updates, equipment component changes |
| **Equipment Sets** | 2-3 weeks | 🔥 High | Matching gear bonuses | Set detection logic, bonus calculations |
| **Lockable Chests** | 2-3 weeks | 🔶 Medium | Keys and lockpicking mechanics | Container system, key/skill requirements |

**Combined Impact:** Deeper equipment strategy and treasure hunting excitement.

### **🐕 Companions & World (3-4 weeks)**

| Feature | Time | Impact | Complexity | Technical Requirements |
|---------|------|--------|------------|----------------------|
| **Pet System** | 3-4 weeks | 🔥 High | AI companions that follow and assist | Companion AI, follow behavior, combat assistance |
| **Trap System** | 3-4 weeks | 🔥 High | Detection, disarmament, damage | Hidden objects, skill checks, trigger mechanics |
| **Skill Scrolls** | 2-3 weeks | 🔶 Medium | Consumable ability learning | Skill teaching items, progression integration |

**Combined Impact:** Living world feel with meaningful exploration rewards.

### **📦 Distribution (2-3 weeks)**

| Feature | Time | Impact | Complexity | Technical Requirements |
|---------|------|--------|------------|----------------------|
| **PC/Mac Distribution** | 2-3 weeks | 🔶 Medium | Packaging and build system | Build scripts, installers, distribution setup |

**Combined Impact:** Easier sharing and installation for players.

### **🔧 Code Quality & Performance (2-4 weeks)**

| Feature | Time | Impact | Complexity | Technical Requirements |
|---------|------|--------|------------|----------------------|
| **Rendering System Unification** | 2-3 weeks | 🔶 Medium | Consolidate multiple render paths | Merge render systems, optimize pipeline |
| **State Management Simplification** | 3-4 weeks | 🔶 Medium | Reduce state machine complexity | Evaluate and simplify state patterns |
| **Entity System Optimization** | 2-3 weeks | 🔶 Medium | Improve entity performance | Spatial indexing, entity pooling |

**Combined Impact:** Cleaner codebase, better performance, easier maintenance.

---

## 🔴 **Phase 3: Major Transformations** (1-6 months each)

These features require significant architectural changes but provide transformative improvements.

### **🎨 Visual & Audio Overhauls**

| Feature | Time | Impact | Complexity | Technical Requirements |
|---------|------|--------|------------|----------------------|
| **Sound Effects** | 6-12 weeks | 🔥 High | New audio system from scratch | Audio engine integration, sound management |
| **Better Character UI** | 4-8 weeks | 🔥 High | Enhanced inventory and character screens | Major UI redesign, improved UX patterns |
| **Modern UI Overhaul** | 2-3 months | 🔥 High | Complete interface redesign | Full UI system replacement |
| **Sprite Graphics** | 3-6 months | 🔥 High | Replace ASCII with sprite rendering | New rendering pipeline, sprite management |

**Combined Impact:** Modern, polished presentation that attracts new players.

### **🌍 Platform Expansion**

| Feature | Time | Impact | Complexity | Technical Requirements |
|---------|------|--------|------------|----------------------|
| **Mobile Distribution** | 3-6 months | 🔥 High | iOS/Android platform adaptation | Touch controls, platform-specific optimizations |

**Combined Impact:** Massive audience expansion.

---

## 🎯 **Recommended Development Path**

### **🚀 Immediate High-Impact Wins (Next 4-6 weeks)**

**Priority Order:**
1. ✅ **Variable Damage** (Complete) - Instant combat excitement
2. ✅ **Variable Defense** (Complete) - Completes the dynamic combat system  
3. ✅ **Variable Monster Damage** (Complete) - Monsters get exciting damage ranges too
4. **Monster Equipment & Loot** (1-2 weeks) - Monsters drop their weapons/armor
5. **General Loot Drops** (1 week) - All monsters drop items when defeated
6. **Chance to Hit/Dodge** (1 week) - Adds tactical tension
7. **More Spells** (1-2 weeks) - Teleport and invisibility for tactical depth

**Why This Order:** Building on the variable damage foundation, adding monster equipment and loot drops creates a complete dynamic combat and reward system.

### **🎮 Medium-Term Game Changers (Next 2-3 months)**

**Priority Order:**
8. **Player Classes** (4-6 weeks) - Massive replayability boost
9. **Ranged Weapons** (2-3 weeks) - New combat dimension
10. **Pet System** (3-4 weeks) - Companions add emotional attachment
11. **More Equipment Slots** (2-3 weeks) - Deeper equipment strategy

**Why This Order:** Player classes provide the biggest replayability impact, while ranged weapons and pets add new gameplay dimensions.

### **🏗️ Long-Term Vision (6+ months)**

**Focus Areas:**
- **Audio/Visual Polish** - Sound effects and improved UI
- **Platform Expansion** - Mobile and broader PC distribution
- **Advanced Systems** - Complex skill trees and environmental systems

---

## 📊 **Impact vs Effort Matrix**

### **High Impact, Low Effort (Do First)**
- ✅ Variable Damage/Defense (Complete)
- ✅ Variable Monster Damage
- Monster Equipment & Loot Drops
- General Loot Drops
- Chance to Hit/Dodge
- More Spells
- Extended Equipment
- Multi-Save Games

### **High Impact, Medium Effort (Do Second)**
- Player Classes
- Ranged Weapons
- Pet System
- Equipment Sets

### **High Impact, High Effort (Long-term Goals)**
- Sound Effects System
- Sprite Graphics
- Mobile Distribution

### **Medium Impact, Low Effort (Fill-in Work)**
- Movement Speed Config
- ✅ JSON Save/Load (Complete)
- More Monster Types

---

## 🔄 **Maintenance & Updates**

This roadmap should be updated:
- **After each feature completion** - Mark as complete, reassess priorities
- **Monthly** - Review impact assessments based on player feedback
- **When new ideas emerge** - Add to appropriate phase based on complexity
- **Before major releases** - Ensure roadmap aligns with release goals

---

## 📈 **Success Metrics**

### **Phase 1 Success:**
- Combat feels more dynamic and unpredictable
- Players spend more time exploring for better loot
- Mouse movement feels perfectly responsive

### **Phase 2 Success:**
- Players create multiple characters with different builds
- Combat encounters feel varied and strategic
- Exploration rewards feel meaningful

### **Phase 3 Success:**
- Game attracts new audiences through modern presentation
- Mobile version expands player base significantly
- Audio/visual polish creates memorable experiences

---

## 🎮 **Current Status & Active Development**

### **✅ Recently Completed (v2.7.0)**
- **More Scrolls Phase** - Teleport, Shield, Raise Dead, Dragon Fart (4 new scrolls)
- **MindlessZombieAI** - Sophisticated FOV-based hunting and sticky targeting
- **Status Effect System** - Disorientation and shield effects
- **Slime Loot Fix** - Slimes no longer drop equipment inappropriately
- **Manual Level Design - Tier 2** - Level parameters & special themed rooms
- **Manual Level Design - Tier 1** - Guaranteed spawns for testing
- **Slime System Complete** - Affiliations, invisibility, corrosion, splitting
- **Variable Damage/Defense** - Dynamic combat with ranges
- **JSON Save/Load System** - Human-readable saves with legacy compatibility
- **Comprehensive Testing** - 1,462 tests with 100% coverage
- **Modern Architecture** - ECS, state machines, performance optimization

### **🎯 Current Sprint: Equipment Expansion**

**✅ Phase 1: More Scrolls** (COMPLETE)
- ✅ **Teleport Scroll**: Escape or reposition instantly (10% misfire → disorientation)
- ✅ **Shield Scroll**: Temporary +4 defense boost (10% monster backfire)
- ✅ **Raise Dead Scroll**: Resurrect defeated monster as zombie ally (2x HP, 0.5x damage)
- ✅ **Dragon Fart Scroll**: Cone of noxious gas, enemies pass out for 20 turns
- ✅ Extended spell system with new targeting modes (directional cone)

**Future Scrolls** (deferred until speed/item systems ready):
- **Haste Scroll**: Increased movement/attack speed (needs weapon speed system)
- **Slow Scroll**: Reduce enemy speed (needs speed system)
- **Identify Scroll**: Reveal item properties (needs item property system)

**Phase 2: Equipment Slots & Items** (2-3 weeks) 🔜 **NEXT**
- **New Slots**: chest (armor), head (helmets), boots, rings, amulets
- **New Weapons**: varied damage types, different weapon classes
- **New Armor**: light/medium/heavy with tradeoffs
- **Weapon Properties**:
  - Speed (attack frequency)
  - Reach (melee range)
  - Durability (item degradation)
- **Set Bonuses**: Matching gear provides extra bonuses

**Phase 3: Ranged Weapons** (2-3 weeks)
- Bows, crossbows, throwing weapons
- Line-of-sight targeting system
- Ammo management
- Projectile animations

**Phase 4: Monster Equipment & Loot** (1-2 weeks)
- Monsters spawn with equipped weapons/armor
- Drop their equipment when defeated
- Visible equipment on monsters
- Stronger monsters = better loot

### **📋 Upcoming Features**

**Manual Level Design - Tier 3** (3-4 weeks)
- Full ASCII map crafting
- Hand-designed levels with precise entity placement
- Boss arenas, puzzle rooms, narrative areas

**Dynamic Terrain & Diggable Walls** (2-4 weeks)
- Different terrain types (stone, dirt, water, etc.)
- Destructible dirt walls that player can dig through
- Strategic path creation and exploration options
- Resource management for digging tools/abilities

**Scrolling Maps & Camera System** (3-5 weeks)
- Maps larger than viewport (currently 80x45)
- Camera follows player movement
- Smooth scrolling as player approaches edges
- Zoom levels and viewport management

**Mini-Map System** (1-2 weeks)
- Small overview map display
- Shows explored areas and current position
- Auto-updates as player explores
- Toggle on/off with hotkey
- **Dependency**: Requires scrolling maps first

**Storytelling & Narrative** (4-6 weeks)
- Story framework integration
- Quest/objective system
- NPC dialogue system
- Narrative progression tracking

**Player Classes** (4-6 weeks)
- Warrior, Mage, Rogue archetypes
- Class-specific abilities and progression
- Unique playstyles and builds

---

*This roadmap represents the current vision for Yarl's development. Priorities may shift based on player feedback, technical discoveries, or new creative insights. The goal is always to maximize player enjoyment while maintaining code quality and system stability.*
