# 🗺️ **Yarl Development Roadmap: Sorted by Complexity & Impact**

*Last Updated: October 2025 - Traditional Roguelike Feature Analysis Complete*

This roadmap organizes all planned features by implementation complexity and gameplay impact, prioritizing the beloved mechanics from legendary roguelikes (NetHack, DCSS, Brogue, Caves of Qud, ADOM).

**📖 See [TRADITIONAL_ROGUELIKE_FEATURES.md](TRADITIONAL_ROGUELIKE_FEATURES.md) for detailed design documentation of each system.**

---

## ✅ **Recently Completed: Exploration & Discovery** (v3.13.0)

**🗺️ Vaults, Secret Doors, Chests & Signposts** (October 18, 2025)

Complete exploration system transforming dungeon-crawling into discovery-filled adventures:

### **What Was Accomplished (v3.13.0 - Exploration & Discovery)**
- **🗝️ Chest System:** 4 chest types (basic, golden, trapped, locked) with quality-based loot tables
- **🪧 Signpost System:** 90+ YAML-based messages with depth filtering (lore, warnings, hints, humor)
- **🚪 Secret Door System:** Passive + active discovery, Ring of Searching integration
- **💰 Simple Vaults (Phase 1):** Elite monsters (2x HP), guaranteed rare/legendary loot, golden walls
- **🔧 YAML Templates:** Full integration for manual placement and testing configurations
- **🐛 15+ Bug Fixes:** Wand targeting, identification leaks, tooltip alignment, monster AI fixes

### **Benefits Realized**
- **🎮 Players:** Discovery rewards, risk/reward decisions, memorable vault encounters
- **🗺️ Exploration:** Finding vaults and secrets feels exciting and meaningful
- **🏗️ Architecture:** YAML-driven signpost messages, extensible vault system
- **✨ Quality:** Comprehensive testing setup, 26 files improved

**Depth Score:** 48 → ~54/64 (75% → 84%)

---

## ✅ **Previously Completed: Boss Fights & Loot Quality** (v3.8.0 - v3.9.0)

**🐉 Epic Boss Encounters & Magic Items** (October 2025)

Complete boss fight system with multi-phase combat, dialogue, and legendary loot:

### **What Was Accomplished (v3.9.0 - Boss Fights)**
- **🐉 Boss Monsters:** Dragon Lord and Demon King with unique abilities
- **💬 Boss Dialogue:** Story-driven combat with spawn, hit, enrage, low HP, and death dialogue
- **😡 Enrage System:** Bosses deal 50% more damage when below 30% HP
- **🛡️ Status Immunities:** Bosses resist confusion, slow, and other debilitating effects
- **🎯 BossAI:** Smarter targeting and enhanced combat behavior
- **💎 Legendary Loot:** Guaranteed legendary item drops from boss kills
- **🧪 Production Quality:** 28 boss-specific tests, 2,091 total tests passing

### **What Was Accomplished (v3.8.0 - Loot Quality)**
- **✨ 4 Rarity Tiers:** Common, Uncommon (+1), Rare (+2-3), Legendary (+4-5)
- **📈 Level-Scaled Drops:** Better loot at deeper dungeon levels
- **💎 Magic Item Names:** Flaming Longsword +2, Reinforced Shield +3, etc.
- **🎲 Rarity Chances:** Level-based probability for magic item drops
- **🧌 Monster Loot:** All monsters can drop magic items based on dungeon level

### **Benefits Realized**
- **🎮 Players:** Epic memorable fights, exciting loot rewards, progression satisfaction
- **🎨 Story:** Dialogue adds narrative depth to combat encounters
- **🏗️ Architecture:** Extensible boss component for future encounters
- **✨ Quality:** Comprehensive test coverage, zero regressions

---

---

## ✅ **Previously Completed: Persistent Ground Effects** (v3.6.0)

**🔥 Hazardous Ground System** (October 2025)

Complete ground hazard system with persistent fire and poison gas effects:

### **What Was Accomplished**
- **🔥 Persistent Fire:** Fireball leaves burning embers (3 turns, 10→6→3 damage decay)
- **💨 Persistent Poison Gas:** Dragon Fart creates toxic gas cones (4 turns, 5→3→1 damage)
- **⏱️ Turn-Based Processing:** Hazards age and damage automatically each turn
- **✨ Visual Fade Effects:** Beautiful color blending into floor (not to black!)
- **💾 Full Save/Load:** Hazards persist across game sessions
- **⚙️ Environment Turn Phase:** Dedicated system for environmental effects

### **Benefits Realized**
- **🎮 Players:** Tactical zone control, area denial, strategic spell usage
- **🎨 Visual Polish:** Natural color transitions, clear hazard feedback
- **🏗️ Architecture:** Extensible for future hazard types (acid, ice, lightning)

---

## ✅ **Previously Completed: Mouse-Driven UI & Equipment Enhancements** (v3.5.0)

**🖱️ Intuitive Right-Click Interactions** (October 2025)

Complete mouse-driven interface with context-aware right-click actions:

### **What Was Accomplished**
- **🎯 Right-Click Item Pickup**: Click ground items → auto-pathfind and pickup
- **🗑️ Right-Click to Drop**: Click sidebar inventory items → instant drop
- **📦 Click Equipment to Unequip**: Click equipped gear → unequip to inventory
- **💡 Ground Item Tooltips**: Hover over items → see full stats/details
- **🛡️ Equipment Tooltips**: Hover over equipped gear → detailed information
- **🐛 Enhanced Armor Fix**: Now works on all armor pieces (not just shields)

### **Technical Achievements**
- **Context-Aware Actions**: Same button, smart behavior based on target
- **Auto-Pickup System**: Pathfinding with automatic item collection
- **Detailed Tooltips**: Weapon damage, armor AC, wand charges, scroll types
- **Clean Coordinate Translation**: Proper screen → world → viewport mapping
- **FOV Integration**: Only show tooltips for visible items

### **Benefits Realized**
- **🎮 Players**: Intuitive one-click actions, rich information, seamless gear management
- **🖱️ Mouse-Driven**: Entire game playable with mouse (keyboard optional)
- **✨ Polish**: Professional-feeling UI that "just works"
- **🧪 Quality**: 98.97% test coverage (1,725/1,743 tests passing)

---

## ✅ **Previously Completed: Camera System & Larger Maps** (v3.4.0)

**📷 Dynamic Camera with Smooth Scrolling** (October 2025)

Complete camera system enabling massive explorable dungeons with smooth viewport scrolling:

### **What Was Accomplished**
- **📹 Camera Infrastructure**: Complete Camera class with CENTER/EDGE_FOLLOW/MANUAL modes
- **🎥 Smooth Scrolling**: Player-centered camera with perfect coordinate translation
- **🗺️ Larger Maps**: Default map size increased from 80x43 to 120x80 (2.8x more area!)
- **✨ All Systems Updated**: Rendering, input, visual effects, targeting all work with camera
- **⚡ Excellent Performance**: 17ms map gen, 5ms pathfinding, 0.7ms FOV computation
- **🧪 Production Quality**: 29 camera tests + 1,662 total tests passing (99.88%)

### **Technical Achievements**
- **Coordinate Translation**: World ↔ Viewport ↔ Screen with camera offset
- **Entity Culling**: Only render entities within viewport (performance!)
- **Mouse Input**: Targeting spells work perfectly with camera scrolling
- **Save/Load**: Map size preserved across sessions
- **Flexible Testing**: Testing mode supports 160x100 maps for validation

### **Benefits Realized**
- **🎮 Players**: Massive explorable dungeons, smooth camera following, immersive exploration
- **🏗️ Architecture**: Clean camera abstraction, easy to extend (edge scrolling ready)
- **📈 Scalability**: Supports maps up to 200x200 with current performance
- **✨ Polish**: Professional-feeling camera system that "just works"

---

## ✅ **Previously Completed: Equipment System Overhaul** (v3.0.0)

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

## ✅ **Recently Completed: Balance & Quality of Life** (October 2025)

**🎯 Early Game Balance Improvements** (v3.1.0 - In Progress)
- **Level 1 Balance**: Reduced first 2 rooms to max 1 monster
- **Increased Potion Spawns**: 60% healing potion rate on level 1 (vs 35% standard)
- **Guaranteed Items**: 2 healing potions + 1 invisibility scroll on level 1
- **Starting Equipment**: Player now starts with 1 healing potion
- **Statistics Tracking**: Comprehensive combat/exploration/consumables tracking
- **Death Screen Overhaul**: Stats display + quick restart (Press R)
- **Config Refactoring**: Clean separation of normal vs testing configuration

**Combined Impact:** Significantly improves new player experience and adds "one more run" appeal.

---

## 🟢 **Phase 1: Essential Roguelike Features** (1-2 weeks each)

**Goal:** Add THE defining roguelike mechanics that create discovery, risk/reward, and depth.

### **🔍 Discovery & Identification (Core Roguelike Experience)**

| Feature | Time | Impact | Why Now | Technical Notes |
|---------|------|--------|---------|-----------------|
| **Item Identification System** | 1-2 weeks | 🔥 CRITICAL | THE defining roguelike mechanic - "What does this blue potion do?" | **DUAL TOGGLE:** Master disable + difficulty integration (Easy=80% pre-ID, Hard=5%) |
| **Item Stacking** | 1 week | 🔥 High | Quality of life standard - "5x healing potion" | Stack similar items, quantity display, merge logic |
| **Scroll/Potion Variety** | 1-2 weeks | 🔥 High | Expand from 8 to 20 scrolls, add 15 potions | More content for identification system, variety |
| **Resistance System** | 1-2 weeks | 🔥 High | Fire/cold/poison/electric - build diversity | Equipment grants resistances, tactical choices |
| **Throwing System** | 1 week | 🔥 High | Throw potions/daggers - emergent gameplay | Target system, potion shattering, tactical depth |

**🎚️ Difficulty Integration:** Item ID percentages scale with difficulty (Easy/Medium/Hard), PLUS master toggle to disable entirely for accessibility.

**Combined Impact:** Creates the core roguelike experience with maximum player agency. Can opt-out completely or scale challenge.

### **🎯 Combat & Mechanics (Already Strong)**

| Feature | Time | Impact | Status | Technical Notes |
|---------|------|--------|--------|-----------------|
| **Variable Damage** | ✅ Complete (v3.0) | 🔥 High | Done | D&D dice notation (1d4, 2d6) |
| **Variable Defense** | ✅ Complete (v3.0) | 🔥 High | Done | Armor provides variable protection |
| **Variable Monster Damage** | ✅ Complete (v3.0) | 🔥 High | Done | Monsters use dice-based damage |
| **Chance to Hit/Dodge** | ✅ Complete (v3.0) | 🔥 High | Done | d20 attack rolls vs AC |
| **More Spells** | ✅ Complete (v2.7) | 🔥 High | Done | 8 tactical scrolls |
| **Monster Equipment & Loot** | ✅ Complete (v3.8) | 🔥 High | Done | Monsters wield and drop gear |
| **Loot Quality & Scaling** | ✅ Complete (v3.8) | 🔥 High | Done | 4 rarity tiers (Common→Legendary) |
| **Boss Encounters** | ✅ Complete (v3.9) | 🔥 High | Done | Multi-phase bosses with dialogue |
| **Critical Failure Consequences** | 1-2 weeks | 🔥 High | Pending | Fumbles cause weapon drops, prone |

**Combined Impact:** Strong combat foundation - focus now on adding roguelike depth systems.

### **💍 Equipment & Magic Items (Build Diversity)**

| Feature | Time | Impact | Why Now | Technical Notes |
|---------|------|--------|---------|-----------------|
| **Wand System** | 2 weeks | 🔥 CRITICAL | Rechargeable magic - component ALREADY EXISTS in codebase! | 15 wand types, limited charges, recharge mechanic |
| **Ring System** | 2-3 weeks | 🔥 CRITICAL | 15 ring types, 2 slots - build customization | Passive effects, some with drawbacks, rings alter playstyle |
| **Amulet System** | 2 weeks | 🔥 High | 10 amulet types, 1 slot - power spikes | Life saving, reflection, ESP - build-defining |
| **Stat Boosting Potions** | 1-2 weeks | 🔥 High | Tactical consumables add resource management | Extend existing item system |

**Combined Impact:** Massive build diversity through passive effects and reusable magic. Wands especially critical as component already exists!

### **🗺️ World Depth (Discovery & Exploration)**

| Feature | Time | Impact | Why Now | Technical Notes |
|---------|------|--------|---------|-----------------|
| **Vaults** | 1-2 weeks | 🔥 High | Special treasure rooms with challenges - memorable moments | 10-15 vault templates, pre-designed, tough guards |
| **Secret Doors** | 1 week | 🔥 High | Hidden passages revealed by searching - exploration rewards | Search action, passive discovery, bonus areas |
| **Corpse System** | 1-2 weeks | 🔥 High | Dead monsters leave corpses - eat for effects | Nutrition, gain abilities, get sick, decay |
| **Trap System** | 2-3 weeks | 🔥 CRITICAL | 10 trap types - danger rewards caution | Hidden until triggered, search/disarm, intentional use |
| **Fountain Effects** | 1-2 weeks | 🔥 High | Random effects from drinking - risk/reward | Restore HP, detect treasure, water demons, 1% wish! |

**Combined Impact:** Transforms exploration from walking to discovery-filled adventure with memorable moments.

### **🎮 Meta-Progression & Replayability**

| Feature | Time | Impact | Why Now | Technical Notes |
|---------|------|--------|---------|-----------------|
| **Difficulty Selection** | 1-2 weeks | 🔥 High | Player choice for game challenge level (Easy/Normal/Hard/Ironman) | Startup menu, scaling config for monsters/loot |
| **Player Profiles/Achievements** | 2-3 weeks | 🔥 High | Persistent player stats across runs, multiple profiles | Profile management, aggregate statistics tracking |
| **Multi-Save Games** | 2-3 weeks | 🔥 High | Multiple save slots with metadata display | Save slot UI, file management, save previews |
| **Morgue Files** | 1-2 weeks | 🔥 High | Post-death character dumps - community, learning | Text file with complete run statistics |
| **Victory Condition/Ascension** | 2-3 weeks | 🔥 CRITICAL | Clear goal - retrieve amulet, escape | Win screen, hall of fame, score system |
| **Player Naming** | 1 week | 🔥 High | Allow players to enter custom names for personalization | Add name input dialog at game start |

**Combined Impact:** Gives players reasons to play "one more run" and sense of progression/completion.

### **🎮 Quality of Life (Polish)**

| Feature | Time | Impact | Status | Technical Notes |
|---------|------|--------|--------|-----------------|
| **Movement Speed Config** | 1 week | 🔥 High | Pending | Makes mouse movement feel perfect for each player |
| **Tooltip System** | ✅ Complete (v3.5) | 🔥 High | Done | Ground & equipment item tooltips on hover |
| **Explored Area Pathfinding** | 1 week | 🔥 High | Pending | Click any previously explored tile to pathfind back to it |
| **JSON Save/Load** | ✅ Complete | 🔶 Medium | Done | Human-readable saves |

**Combined Impact:** Polishes the core experience.

### **📷 Camera System (Optional Polish)**

| Feature | Time | Impact | Why Now | Technical Notes |
|---------|------|--------|---------|-----------------|
| **Camera & Viewport Scrolling** | ✅ Complete (Phases 1-3) | 🔥 High | Smooth scrolling, 120x80 maps, excellent performance | Camera class, coordinate translation, all systems integrated |
| **Edge Scrolling Mode** | 1-2 hours | 🔶 Medium | Alternative to CENTER mode - camera moves when player near edge | Infrastructure exists (EDGE_FOLLOW mode), just needs UI toggle |
| **Camera Smooth Interpolation** | 2-3 hours | 🔷 Low | Gradual camera movement instead of instant snap | Interpolation between camera positions |
| **Camera Shake Effects** | 2-3 hours | 🔷 Low | Screen shake for combat/explosions | Shake amplitude/duration system |
| **Performance Optimization** | 2-3 hours | 🔷 Low | Optimize for 200x200+ maps | Tile caching, dirty rectangle tracking, profiling |

**Combined Impact:** Camera system is production-ready! Optional polish items add nice-to-have effects but aren't critical. Current performance is excellent (17ms map gen, 5ms pathfinding, 0.7ms FOV).

---

## 🟡 **Phase 2: Core Roguelike Systems** (2-4 weeks each)

**Goal:** Add the major systems that define traditional roguelikes - resource management, equipment depth, and economic systems.

### **🍖 Resource Management (Strategic Depth Without Tedium)**

| Feature | Time | Impact | Why Critical | Technical Requirements |
|---------|------|--------|--------------|----------------------|
| **Wand System with Charges** | 2 weeks | 🔥 CRITICAL | Primary resource management - reusable magic | Charge tracking, recharge scroll (risky), 15 wand types |
| **Item Identification Economy** | (with ID System) | 🔥 HIGH | Identify scrolls valuable, shop services | Scroll of identify, shop identification fees |
| **Anti-Grinding Design** | 1 week | 🔥 HIGH | Prevents safe grinding without hunger tedium | Finite monsters per floor, no respawns |
| ~~**Hunger/Food System**~~ | ~~2-3 weeks~~ | ⚠️ SKIP/OPTIONAL | DCSS removed this in v0.26 - "tedium without depth" | Make optional difficulty setting if added |

**⚠️ DESIGN DECISION:** Skipping mandatory hunger system based on player research. DCSS removed it after finding it added busywork without meaningful decisions. Resource management comes from wands, ID economy, and anti-grinding design instead.

**Combined Impact:** Strategic resource management without tedious busywork. Respects player time.

### **⚔️ Equipment Depth (The Equipment Puzzle)**

| Feature | Time | Impact | Why Critical | Technical Requirements |
|---------|------|--------|--------------|----------------------|
| **Blessed/Cursed Items** | 2-3 weeks | 🔥 CRITICAL | Equipment risk/reward - can't remove cursed! **WITH clear visual indicators** | BUC states, visual cues (red glow), cursed items have UPSIDES, remove curse scrolls |
| **More Status Effects** | 2-3 weeks | 🔥 High | Poison, paralysis, blindness, levitation **- NO instant death** | Extend status system, survivable effects only, clear cures |

**⚠️ SAFETY NETS:** Cursed items have upsides (cursed sword: -1 AC, +3 damage). No instant death effects. Clear visual indicators.

**Combined Impact:** Makes equipment decisions meaningful WITHOUT unfair punishment. Drama without rage quits.

### **🙏 Divine & Economic Systems (Meta-Progression)**

| Feature | Time | Impact | Why Critical | Technical Requirements |
|---------|------|--------|--------------|----------------------|
| **Religion/God System** | 3-4 weeks | 🔥 CRITICAL | Multiple gods, favor, prayers, divine gifts - massive replay value | God definitions, altars, favor tracking, divine powers |
| **Shop System** | 2-3 weeks | 🔥 High | Buy/sell economy, identification services, tough shopkeepers | Shopkeeper NPCs, inventory, pricing, theft detection |

**Combined Impact:** Adds strategic meta-progression and economic resource conversion.

### **🏹 Advanced Combat & World**

| Feature | Time | Impact | Status | Technical Requirements |
|---------|------|--------|--------|----------------------|
| **Ranged Weapons** | 2-3 weeks | 🔥 High | Pending | Bows, crossbows, ammo - projectile mechanics |
| **Boss Encounters** | ✅ Complete (v3.9) | 🔥 High | Done | Multi-phase bosses with dialogue, NO instant death |
| **Persistent Spell Effects** | ✅ Complete (v3.6) | 🔥 High | Done | Ground effects (fire, poison gas), survivable damage |
| **Manual Level Design - Tier 3** | 3-4 weeks | 🔥 High | Pending | ASCII map crafting, boss arenas |
| **Trap System** | 2-3 weeks | 🔥 High | Pending | **NO instant death** - warnings, passive discovery, all survivable |
| **Vaults & Secret Doors** | 1-2 weeks | 🔥 High | Pending | Special treasure rooms, **passive 75% discovery** for secret doors |

**⚠️ NO INSTANT DEATH:** All features designed with warnings, safety nets, and survivability. Fair challenge, not "gotcha" moments.

**Combined Impact:** Adds combat variety and memorable encounters WITHOUT frustrating deaths.

### **🎭 Character Depth (3-6 weeks)**

| Feature | Time | Impact | Complexity | Technical Requirements |
|---------|------|--------|------------|----------------------|
| **Difficulty Selection** | 1-2 weeks | 🔥 High | Choose challenge level at game start | Startup menu, monster/loot scaling configs |
| **Player Profiles** | 2-3 weeks | 🔥 High | Persistent stats across runs, multiple profiles | Profile management, aggregate statistics |
| **Player Classes** | 4-6 weeks | 🔥 High | Warrior/Mage/Rogue with unique abilities | Class-specific progression, ability systems |
| **Complex Leveling** | 3-4 weeks | 🔥 High | Feats, skill trees, specialization | Feat system, prerequisite checking |
| **Skill System** | 3-5 weeks | 🔥 High | Lockpicking, stealth, trap detection | Multiple skill mechanics with progression |

**Combined Impact:** Massive replayability boost through character customization and difficulty options.

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
| **Hidden Doors & Secrets** | 1-2 weeks | 🔥 High | Secret passages, search mechanics, exploration rewards | Door revealing system, search/detection mechanics, visual cues |
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

## 🔴 **Phase 3: Legendary Features** (3-6 weeks each)

**Goal:** Add the most memorable and talked-about roguelike mechanics - the features that create player stories.

### **✨ Emergent Gameplay (The "Did you know you can..." moments)**

| Feature | Time | Impact | Why Legendary | Technical Requirements |
|---------|------|--------|---------------|----------------------|
| **Polymorph System** | 3-4 weeks | 🔥 LEGENDARY | Transform into monsters, gain abilities - creates unforgettable moments | Polymorph effects, monster form system, ability transfer |
| **Item Interaction System** | 3-4 weeks | 🔥 LEGENDARY | Dip weapons in potions, mix potions, alchemy - emergent depth | Dipping mechanics, combination system, effect tables |
| **Wish/Genie System** | 1-2 weeks | 🔥 LEGENDARY | Rare wishes players remember forever - "I wished for Excalibur!" | Text input, item parser, wish granting logic |
| **Unique Artifacts** | 2-3 weeks | 🔥 High | 10 legendary items (Excalibur, Mjolnir, Stormbringer) - chase items | Unique item definitions, special abilities, special spawning |
| **Digging/Tunneling** | 2-3 weeks | 🔥 High | Create paths through walls - player agency, creative solutions | Dig action, wall replacement, pickaxe/wand |
| **Monster Special Abilities** | 2-4 weeks | 🔥 High | Stealing, stat draining, summoning, rust attacks - threat variety | New monster behaviors, special attack effects |
| **Swarm Mechanics** | 1-2 weeks | 🔥 High | Groups of 5-15 weak monsters (rats, bats) - tactical variety | Swarm spawning, flee AI, balance |

**Combined Impact:** Creates the legendary roguelike moments that players talk about for years. "Remember when I polymorphed into a dragon and got a wish?"

### **🏆 Character Development (Long-term Systems)**

| Feature | Time | Impact | Priority | Technical Requirements |
|---------|------|--------|----------|----------------------|
| **Player Classes** | 4-6 weeks | 🔥 CRITICAL | High | Warrior/Mage/Rogue - different starting equipment/stats/abilities |
| **Complex Leveling System** | 3-4 weeks | 🔥 High | Medium | Feats, skill trees, specialization |
| **Skill System** | 3-5 weeks | 🔥 High | Medium | Lockpicking, stealth, trap detection with progression |

**Combined Impact:** Massive replayability through build variety.

---

## 🔴 **Phase 4: Polish & Long-term** (1-6 months each)

### **🎨 Visual & Audio Overhauls**

| Feature | Time | Impact | Priority | Technical Requirements |
|---------|------|--------|----------|----------------------|
| **Sound Effects System** | 6-12 weeks | 🔥 High | Low | Audio integration, sound library, volume controls |
| **Better Character UI** | 4-8 weeks | 🔥 High | Low | Enhanced inventory and character screens |
| **Modern UI Overhaul** | 2-3 months | 🔥 High | Low | Complete interface redesign |
| **Sprite Graphics** | 3-6 months | 🔥 High | Low | Replace ASCII with sprite rendering |

**Combined Impact:** Modern presentation. Note: ASCII is fine for traditional roguelike - low priority.

### **🌍 Platform Expansion**

| Feature | Time | Impact | Priority | Technical Requirements |
|---------|------|--------|----------|----------------------|
| **PC/Mac Distribution** | 2-3 weeks | 🔶 Medium | Medium | Packaging, installers, build system |
| **Mobile Distribution** | 3-6 months | 🔥 High | Low | iOS/Android adaptation, touch controls |

**Combined Impact:** Easier sharing and broader audience.

---

## 🎯 **Recommended Development Path**

**Based on research of NetHack, DCSS, Brogue, Caves of Qud, and ADOM**

### **🚀 Phase 1: Core Roguelike Identity (Weeks 1-8)**

**Goal:** Transform into a true roguelike with THE defining mechanics

**Priority Order:**
1. **Item Identification System** (2 weeks) - THE roguelike mechanic. Everything else waits for this.
2. **Item Stacking** (1 week) - Quality of life to support identification
3. **Scroll/Potion Variety** (2 weeks) - Expand to 20 scrolls, 15 potions for identification content
4. **Resistance System** (2 weeks) - Build diversity foundation
5. **Throwing System** (1 week) - Tactical depth, emergent gameplay

**Why These First:**
- Item identification is THE defining roguelike feature - without it, we're just an action RPG
- These create the core "I wonder what this does?" experience
- Foundation for all other systems
- Quick wins (1-2 weeks each)

**Expected Player Impact:** "Now THIS feels like a real roguelike!"

### **📈 Phase 2: Resource Management & Build Depth (Weeks 9-18)**

**Goal:** Add tension and strategic equipment decisions

**Priority Order:**
1. **Wand System** (2 weeks) - Component ALREADY EXISTS! Rechargeable magic.
2. **Ring System** (2-3 weeks) - 2 slots, 15 types, build customization
3. **Hunger/Food System** (2-3 weeks) - Time pressure, prevents grinding
4. **Corpse System** (1 week) - Integration with hunger, risk/reward
5. **Vaults & Secret Doors** (2 weeks) - Discovery rewards

**Why Next:**
- Wands are already coded - just need implementation
- Hunger creates tension (core roguelike mechanic)
- Rings enable build diversity
- Vaults create memorable moments

**Expected Player Impact:** "I have to manage resources and every decision matters!"

### **🏆 Phase 3: Meta-Progression & Depth (Weeks 19-32)**

**Goal:** Add the systems that create replay value and strategic depth

**Priority Order:**
1. **Trap System** (2-3 weeks) - Danger, caution rewarded
2. **Blessed/Cursed Items** (2-3 weeks) - Equipment puzzle layer
3. **Religion/God System** (3-4 weeks) - Meta-progression, massive replay value
4. **Shop System** (2-3 weeks) - Economy, identification services
5. **Amulet System** (2 weeks) - Power spikes
6. **More Status Effects** (2-3 weeks) - Poison, paralysis, blindness

**Expected Player Impact:** "Every run feels different based on my god choice and equipment luck!"

### **🌟 Phase 4: Legendary Features (Weeks 33-48)**

**Goal:** Add the features players talk about for years

**Priority Order:**
1. **Victory Condition/Ascension** (2-3 weeks) - Clear goal, hall of fame
2. **Item Interaction System** (3-4 weeks) - Dipping, alchemy, emergent gameplay
3. **Polymorph System** (3-4 weeks) - Legendary moments
4. **Unique Artifacts** (2-3 weeks) - Chase items (Excalibur, Mjolnir)
5. **Wish/Genie System** (1-2 weeks) - "I got a wish!" moments
6. **Monster Special Abilities** (2-4 weeks) - Stealing, stat drain, summoning

**Expected Player Impact:** "Remember that run when I polymorphed into a dragon, got a wish, and found Excalibur?!"

### **🏗️ Long-Term: Polish & Distribution (6+ months)**

**Focus Areas:**
- **Player Classes** (4-6 weeks) - After core roguelike systems
- **Ranged Weapons** (2-3 weeks) - After throwing system
- **Audio/Visual Polish** - Sound effects and improved UI
- **Platform Expansion** - PC/Mac distribution, then mobile
- **Advanced Systems** - Skill trees, complex leveling

---

## 📊 **Impact vs Effort Matrix** (Traditional Roguelike Focus)

### **🔥 CRITICAL Impact, Low-Medium Effort (Do First)**
- **Item Identification System** (2 weeks) - THE defining roguelike feature
- **Item Stacking** (1 week) - Quality of life standard
- **Throwing System** (1 week) - Emergent gameplay
- **Scroll/Potion Variety** (2 weeks) - Content for identification
- **Resistance System** (2 weeks) - Build diversity

### **🔥 CRITICAL Impact, Medium Effort (Do Second)**
- **Hunger/Food System** (2-3 weeks) - Time pressure core to roguelikes
- **Wand System** (2 weeks) - Component exists, rechargeable magic
- **Ring System** (2-3 weeks) - Massive build customization
- **Blessed/Cursed Items** (2-3 weeks) - Equipment puzzle layer
- **Religion/God System** (3-4 weeks) - Meta-progression, replay value
- **Trap System** (2-3 weeks) - Danger and caution rewarded

### **🔥 High Impact, Medium Effort (Do Third)**
- **Shop System** (2-3 weeks) - Economy and resource conversion
- **Vaults & Secret Doors** (2 weeks) - Discovery and exploration
- **More Status Effects** (2-3 weeks) - Tactical depth
- **Amulet System** (2 weeks) - Power spikes
- **Victory Condition/Ascension** (2-3 weeks) - Clear goal

### **🌟 LEGENDARY Impact, Higher Effort (Do Fourth)**
- **Wish/Genie System** (1-2 weeks) - Unforgettable moments
- **Polymorph System** (3-4 weeks) - Power fantasy
- **Item Interaction System** (3-4 weeks) - Emergent depth
- **Unique Artifacts** (2-3 weeks) - Chase items

### **✅ Already Complete**
- Variable Damage/Defense (v3.0)
- D20 Combat System (v3.0)
- Boss Fights (v3.9)
- Loot Quality System (v3.8)
- 8 Tactical Scrolls (v2.7)
- Ground Hazards (v3.6)

---

## 🔄 **Maintenance & Updates**

This roadmap should be updated:
- **After each feature completion** - Mark as complete, reassess priorities
- **Monthly** - Review impact assessments based on player feedback
- **When new ideas emerge** - Add to appropriate phase based on complexity
- **Before major releases** - Ensure roadmap aligns with release goals

---

## 📈 **Success Metrics**

### **Phase 1 Success: Core Roguelike Identity**
Target: Players say "Now this feels like a REAL roguelike!"
- Players excitedly identify unknown potions/scrolls
- "I wonder what this does?" moments every run
- Item discovery creates risk/reward tension
- Players throw potions tactically in combat

### **Phase 2 Success: Resource Management**
Target: "I have to manage everything carefully!"
- Hunger creates urgency to keep exploring
- Wand charges are precious resources
- Ring choices define character builds
- Vault discoveries create memorable moments

### **Phase 3 Success: Meta-Progression**
Target: "Every run feels unique!"
- God choice significantly impacts playstyle
- Cursed items create "oh no!" moments
- Shop economics add resource conversion
- Trap encounters add danger and caution

### **Phase 4 Success: Legendary Status**
Target: "Remember that amazing run when..."
- Players share wish stories
- Polymorph creates power fantasy moments
- Artifact discoveries are celebrated
- Players create emergent solutions with item interactions

### **Overall Success: Best Traditional Roguelike**
- Depth Score: 9/10+ across all categories (Discovery, Resource Management, Build Diversity, Emergent Gameplay)
- Players compare favorably to NetHack/DCSS/Brogue
- "One more run" factor is extremely high
- Community shares legendary moments

---

## 🎮 **Current Status & Active Development**

### **✅ Recently Completed (v3.1.0 - In Progress)**
- **Early Game Balance** - Level 1 difficulty reduction for new players
- **Statistics System** - Comprehensive tracking (kills, damage, accuracy, exploration)
- **Death Screen Overhaul** - Stats display with quick restart functionality (Press R)
- **Config Architecture** - Clean separation of normal vs testing configuration
- **Option 6 Balance Changes** - Multi-layered safety nets for early game survival

### **✅ Recently Completed (v3.0.0)**
- **D&D Dice Notation** - Complete dice rolling system (1d4, 2d6+3, etc.)
- **12 New Weapons** - Dagger to Greatsword with finesse/unwieldy properties
- **Full Stat System** - STR/DEX/CON with proper modifiers
- **d20 Combat** - Attack rolls, AC, critical hits, fumbles
- **Armor System** - Light/Medium/Heavy armor with DEX caps
- **Equipment Overhaul** - Slot-based system with 6 equipment slots

### **✅ Recently Completed (v2.7.0)**
- **More Scrolls Phase** - Teleport, Shield, Raise Dead, Dragon Fart (4 new scrolls)
- **MindlessZombieAI** - Sophisticated FOV-based hunting and sticky targeting
- **Status Effect System** - Disorientation and shield effects
- **Slime System Complete** - Affiliations, invisibility, corrosion, splitting
- **Manual Level Design** - Tier 1 (guaranteed spawns) and Tier 2 (level parameters)
- **JSON Save/Load System** - Human-readable saves with legacy compatibility
- **Comprehensive Testing** - 1,575+ tests with 100% coverage
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
- **New Slots**: rings, amulets
- **New Weapons**: varied damage types, different weapon classes
- **New Armor**: light/medium/heavy with tradeoffs
- **Weapon Properties**:
  - Speed (attack frequency)
  - Durability (item degradation)
- **Set Bonuses**: Matching gear provides extra bonuses
- **Wands System**: Rechargeable spell items
  - Multi-charge items (like scrolls but reusable!)
  - Can be recharged by "feeding" matching scrolls
  - Different wand types for each spell
  - Wand durability/max charges
  - More reliable than scroll RNG

**Phase 3: Ranged Weapons** (2-3 weeks) 🟢 **IN PROGRESS**
- ✅ **Basic Ranged Weapons**: Shortbow, Longbow, Crossbow (reach system!)
- ✅ **Targeting System**: Uses existing reach/pathfinding system
- ✅ **Auto-attack on Approach**: Stops at max range and fires!
- 📋 **Ammo Management**: Track arrows/bolts, limited ammo (1-2 weeks)
- 📋 **Projectile Animations**: Visual arrow/bolt flight path (1-2 weeks)
- 📋 **Throwing Weapons**: Daggers, javelins, axes (1 week)

**Phase 4: Monster Equipment & Loot** (1-2 weeks)
- Monsters spawn with equipped weapons/armor
- Drop their equipment when defeated
- Visible equipment on monsters
- Stronger monsters = better loot

### **📋 Upcoming Features**

**Difficulty Selection System** (1-2 weeks) 🔜 **NEXT**
- **Easy Mode**: 50% more HP, +2 to-hit, 50% more healing potions
- **Normal Mode**: Current balance (newly improved for v3.1)
- **Hard Mode**: Monsters deal 25% more damage, fewer consumables
- **Ironman Mode**: Permadeath (no save/load), achievements unlocked
- Startup menu integration
- Profile-based difficulty tracking

**Player Profile System** (2-3 weeks)
- Multiple named profiles per player
- Aggregate statistics across all runs
- Best run tracking (deepest level, most kills, fastest time)
- Achievement system (first kill, 100 kills, reach level 10, etc.)
- Profile selection/creation UI
- Leaderboard display (local only)

**Wands System** (1-2 weeks)
- **Rechargeable spell items**: Like scrolls but with multiple charges!
- **Wand Types**: Wand of Fireball, Wand of Lightning, Wand of Healing, etc.
- **Charge System**: 
  - Each wand starts with 3-10 charges
  - Using a wand consumes 1 charge
  - Empty wands remain in inventory
- **Recharging Mechanic**:
  - "Feed" matching scrolls to wands to recharge them
  - E.g., use Fireball Scroll on empty Wand of Fireball → +1 charge
  - Intuitive: drag scroll onto wand or use scroll while targeting wand
  - Makes scrolls valuable even when you have wands
- **Benefits over Scrolls**:
  - More reliable (no RNG on finding them)
  - Encourages long-term planning
  - Trade-off: rarer to find, but reusable
- **Wand Durability**: 
  - Max charges decrease over time (e.g., 10 → 9 → 8...)
  - Eventually wands "wear out" and break
  - Creates item sink and progression

**Manual Level Design - Tier 3** (3-4 weeks)
- Full ASCII map crafting
- Hand-designed levels with precise entity placement
- Boss arenas, puzzle rooms, narrative areas

**Dynamic Terrain & Diggable Walls** (2-4 weeks)
- Different terrain types (stone, dirt, water, etc.)
- Destructible dirt walls that player can dig through
- Strategic path creation and exploration options

**Distribution & Packaging** (4-6 hours first time, 30 min subsequent)
- **PyInstaller Setup**: Bundle Python + dependencies into standalone executables
- **Windows Build**: Create .exe with no Python installation required
- **macOS Build**: Create .app bundle (Intel + Apple Silicon)
- **Testing**: Validate on clean machines (Windows 10/11, macOS)
- **Documentation**: Installation instructions for playtesters
- **GitHub Releases**: Automated release packaging
- **Future**: Code signing ($100-400/year), installers (DMG/NSIS), CI/CD automation
- **See:** `docs/DISTRIBUTION_PLAN.md` for complete guide

**Scrolling Maps & Camera System** (3-5 weeks) ✅ **COMPLETE!**
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
