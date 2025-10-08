# Puzzle Quest-Style Game Project Context

## Overview
This document captures the analysis and recommendations for building a hybrid roguelike/match-3 game inspired by Puzzle Quest, using the existing rlike engine as a foundation.

**Date**: October 8, 2025  
**Status**: Planning/Concept Phase

---

## Initial Question

Can the current roguelike engine be adapted to build a Puzzle Quest-style game that combines:
- Traditional roguelike exploration (dungeon crawling, map travel, NPCs)
- Match-3 puzzle combat (gem matching as the battle system)
- RPG progression (stats, equipment, leveling)

**Answer**: Yes, with significant but manageable work. Approximately 65% of the current engine is directly reusable.

---

## Current Engine Strengths

### 1. World/Map System (95% Reusable)
**Current Implementation:**
- BSP dungeon generation with rooms and tunnels
- Room-based structure with entity placement
- Stairs/level transitions
- Multiple dungeon levels with scaling difficulty

**Puzzle Quest Translation:**
- Overworld map with nodes/locations
- Quest locations, cities, dungeons
- Map travel between locations
- Progressive difficulty scaling

**Files**: `map_objects/game_map.py`, `map_objects/rectangle.py`

### 2. RPG Core (100% Reusable - This IS Puzzle Quest!)

**Fighter Component** (`components/fighter.py`):
- ✅ HP system with max HP calculation
- ✅ D&D-style stats: STR, DEX, CON with modifiers
- ✅ Armor Class (AC) system
- ✅ Attack/Defense with d20 rolls
- ✅ Critical hits and fumbles
- ✅ XP and leveling
- ✅ Damage calculation with equipment bonuses

**Equipment System** (`components/equipment.py`, `components/equippable.py`):
- ✅ 5 equipment slots: main_hand, off_hand, head, chest, feet
- ✅ Equipment bonuses (power, defense, AC, HP)
- ✅ Weapon damage ranges and to-hit bonuses
- ✅ Armor types (light, medium, heavy) with DEX caps
- ✅ Equipment enhancement/upgrade system

**Inventory** (`components/inventory.py`):
- ✅ Item pickup, drop, use
- ✅ Capacity management
- ✅ Item stacking and organization

**Level/XP System** (`components/level.py`):
- ✅ Experience tracking
- ✅ Level-up mechanics
- ✅ Stat increases on level up

### 3. Status Effects System (100% Reusable)

**Current Effects** (`components/status_effects.py`):
- Invisibility - Could become "Stealth" in battles
- Disorientation/Confusion - Directly applicable
- Shield - Temporary defense boost
- Taunted - Redirect enemy focus
- Slowed - Skip turns/reduced actions
- Immobilized - Can't move (perfect for tactical play)
- Enraged - Chaotic damage/accuracy effects

**Status Effect Manager**:
- Duration tracking
- Turn-based processing
- Stacking/refresh logic
- Apply/remove callbacks

**Puzzle Quest Application**: These become battle effects triggered by:
- Gem matches (5+ gems = status effect)
- Spell casting (spend mana from matches)
- Equipment abilities
- Enemy special attacks

### 4. Event Architecture (Enterprise-Grade!)

**Event System** (`events/`):
```
EventBus - Central event routing
├─ Event priorities and queuing
├─ Event chains and sequences
├─ Delayed and recurring events
├─ Conditional event patterns
├─ Pre/post dispatch hooks
└─ Performance monitoring
```

**Game Event Types**:
- Combat events (attack, damage, heal, death)
- Movement events
- Inventory events (pickup, drop, equip)
- Level events
- System events (save, load, pause)
- UI events

**Puzzle Quest Integration**: Add new event types:
- `GemMatchedEvent` - When gems are matched
- `ComboChainEvent` - Multi-match cascades
- `ManaGainedEvent` - Mana from gem matches
- `SpellCastEvent` - Spending mana in battle
- `BattleStartEvent` / `BattleEndEvent`
- `GemSwapEvent` - Player/AI swapping gems

The event system can elegantly handle the match-3 → combat translation:
```python
# Example flow:
GemMatchedEvent(type="skull", count=4)
  → Triggers: DamageEvent(target=enemy, amount=4)
    → Triggers: CombatDamageEvent
      → Updates HP, checks death
```

### 5. Entity/Component System

**Component Registry** (`components/component_registry.py`):
- Clean component-based architecture (ECS-style)
- Modular, extensible design
- Type-safe component access
- Easy to add new components

**Entity System** (`entity.py`):
- Flexible entity creation
- Component composition
- Position and rendering
- Pathfinding (A* algorithm)

### 6. AI System (80% Reusable)

**Current AI Types** (`components/ai.py`):
- `BasicMonster` - Chase and attack player
- `SlimeAI` - Multi-faction hostility
- `MindlessZombieAI` - Attack everything nearby
- `ConfusedMonster` - Random movement

**Puzzle Quest Adaptation**:
Enemy AI during match-3 battles could:
- Prioritize gem colors based on their spell needs
- Block player's potential matches
- Set up cascades for big damage
- Target specific gem types strategically

Exploration AI remains the same for overworld encounters.

### 7. Game State Machine

**Current States** (`game_states.py`):
- `PLAYERS_TURN` - Player movement/action
- `ENEMY_TURN` - AI processing
- `PLAYER_DEAD` - Death screen
- `SHOW_INVENTORY` - Inventory UI
- `DROP_INVENTORY` - Drop items
- `TARGETING` - Spell/item targeting
- `LEVEL_UP` - Level up choices
- `CHARACTER_SCREEN` - Stats display

**Add for Puzzle Quest**:
- `MATCH3_BATTLE` - Match-3 combat screen
- `MAP_TRAVEL` - Overworld navigation
- `QUEST_DIALOG` - NPC conversations
- `SHOP` - Buy/sell equipment
- `QUEST_LOG` - Track quests

---

## What Needs to Be Built (35% New Work)

### 1. Match-3 Engine (Core New System)

**Match3Board Class**:
```python
class Match3Board:
    def __init__(self, width=8, height=8):
        self.width = width
        self.height = height
        self.grid = []  # 2D array of gems
        self.gem_types = ["skull", "red", "blue", "green", "yellow", "purple"]
    
    def swap_gems(self, x1, y1, x2, y2) -> bool:
        """Swap two adjacent gems if valid"""
        
    def find_matches(self) -> List[Match]:
        """Detect all 3+ matches on board"""
        
    def remove_matches(self, matches):
        """Remove matched gems from board"""
        
    def apply_gravity(self):
        """Make gems fall to fill empty spaces"""
        
    def spawn_new_gems(self):
        """Fill empty spaces with new gems"""
        
    def calculate_cascade(self) -> int:
        """Process chain reactions, return combo count"""
```

**MatchDetector**:
- Horizontal and vertical match detection
- L-shaped and T-shaped match detection (for combos)
- Special gem detection (4+ matches create power gems)
- Cascade/chain counting

**GemPhysics**:
- Falling animation
- Gem spawning from top
- Smooth transitions
- Particle effects on matches

**Complexity**: 3-6 weeks of focused work

### 2. Match-3 Rendering

**Options**:

**Option A: Pygame (Recommended)**
- Richer graphics for gems (sprites, gradients, shine effects)
- Easier animation (smooth movement, rotations, particles)
- Good performance for gem grid
- Can composite with tcod for exploration mode

**Option B: Enhanced tcod**
- Use colored tiles/characters for gems
- More retro aesthetic
- Consistent with exploration mode
- Limited animation capabilities

**Hybrid Approach** (Best of both):
- Exploration mode: tcod (current system)
- Battle screen: Switch to pygame surface
- Share game state between both renderers

**Estimated Effort**: 1-2 weeks

### 3. Battle Integration Layer

**BattleManager Class**:
```python
class BattleManager:
    def __init__(self, player, enemy, match3_board):
        self.player = player
        self.enemy = enemy
        self.board = match3_board
        self.player_mana = {gem_type: 0 for gem_type in gem_types}
        self.turn = "player"
    
    def process_match(self, matches):
        """Convert gem matches to combat effects"""
        for match in matches:
            if match.gem_type == "skull":
                damage = len(match.gems)
                self.deal_damage(self.enemy, damage)
            else:
                # Add mana for spell casting
                self.player_mana[match.gem_type] += len(match.gems)
    
    def cast_spell(self, spell, target):
        """Spend mana to cast spell using Fighter/StatusEffect system"""
        
    def check_battle_end(self) -> bool:
        """Check if player or enemy is dead"""
```

**Gem Type → Combat Translation**:
- **Skulls** (💀): Direct damage to enemy (uses STR modifier)
- **Red Gems** (🔴): Red mana → Fire spells (damage over time)
- **Blue Gems** (🔵): Blue mana → Water/Ice spells (freeze, slow)
- **Green Gems** (🟢): Green mana → Earth spells (defense, healing)
- **Yellow Gems** (🟡): Yellow mana → Light spells (buff, cleanse)
- **Purple Gems** (🟣): Purple mana → Dark spells (curse, drain)

**Equipment Impact on Battles**:
- Weapon damage bonus → +% skull damage
- Armor → Reduce enemy skull damage
- Jewelry → +% mana gain from gem matches
- Special equipment → Unique battle abilities

**Estimated Effort**: 2-3 weeks

### 4. Battle AI

**Enemy Match-3 AI**:
```python
class BattleAI:
    def choose_move(self, board, enemy_state, player_state):
        """AI decides which gems to swap"""
        # Strategy priorities:
        # 1. Look for 4+ matches (power gems)
        # 2. Match gems for needed mana
        # 3. Match skulls if can deal lethal damage
        # 4. Block player's obvious matches
        # 5. Set up future cascades
        
        moves = self.find_all_valid_moves(board)
        scored_moves = [(move, self.score_move(move)) for move in moves]
        return max(scored_moves, key=lambda x: x[1])[0]
```

**AI Difficulty Levels**:
- Easy: Random valid moves
- Medium: Prioritize own matches
- Hard: Block player + set up combos

**Estimated Effort**: 1-2 weeks

---

## Architecture Recommendation

### Project Structure

```
puzzle-quest-project/
├── exploration/           # Current rlike systems
│   ├── map_generation/    # World map, dungeons
│   ├── entities/          # NPCs, enemies, items
│   ├── ai/                # Overworld AI
│   └── rendering/         # tcod exploration view
│
├── battle/                # NEW: Match-3 battle system
│   ├── match3_board.py    # Core match-3 logic
│   ├── match_detector.py  # Find gem matches
│   ├── gem_physics.py     # Falling, cascades
│   ├── battle_manager.py  # Combat integration
│   ├── battle_ai.py       # Enemy match-3 AI
│   └── battle_renderer.py # Pygame gem rendering
│
├── core/                  # SHARED: Core RPG systems
│   ├── components/        # Fighter, Equipment, Inventory (REUSE)
│   ├── events/            # Event bus system (REUSE)
│   ├── entity.py          # Entity system (REUSE)
│   └── game_states.py     # State machine (EXTEND)
│
├── ui/                    # UI systems
│   ├── exploration_ui.py  # tcod UI (REUSE)
│   ├── battle_ui.py       # NEW: Match-3 UI
│   ├── character_screen.py # REUSE
│   └── inventory_screen.py # REUSE
│
└── main.py                # Game loop coordinator
```

### Game Flow

```
┌─────────────────────────────────────────────────────────┐
│ EXPLORATION MODE (tcod rendering)                       │
│ ─────────────────────────────────────────────────────── │
│ • Navigate overworld map                                │
│ • Enter dungeons, cities, quest locations               │
│ • Talk to NPCs, pick up quests                         │
│ • Manage inventory, equipment                          │
│ • Level up, allocate stats                             │
│                                                         │
│ [Enemy Encountered] → Trigger BATTLE MODE              │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ BATTLE MODE (pygame rendering)                          │
│ ─────────────────────────────────────────────────────── │
│ • Match-3 gem board (8x8 grid)                         │
│ • Player swaps gems → matches → damage/mana            │
│ • Cast spells using accumulated mana                   │
│ • Equipment bonuses apply (STR/DEX/CON)                │
│ • Status effects active (Slow, Shield, etc.)           │
│ • Enemy AI makes tactical gem matches                  │
│                                                         │
│ [Victory] → Return to EXPLORATION + Loot/XP            │
│ [Defeat] → Game Over or Retreat                        │
└─────────────────────────────────────────────────────────┘

SHARED SYSTEMS (Always Active):
├─ Fighter Component (HP, stats, equipment)
├─ Equipment System (bonuses apply everywhere)
├─ Inventory (items usable in or out of battle)
├─ Status Effects (persist across modes)
├─ Event Bus (coordinates everything)
└─ Save/Load System
```

### State Transitions

```python
class GameStateManager:
    def update(self):
        if self.state == GameStates.EXPLORATION:
            # Normal roguelike exploration
            if enemy_encountered:
                self.transition_to_battle(enemy)
                
        elif self.state == GameStates.MATCH3_BATTLE:
            # Match-3 combat
            if battle_ended:
                if victory:
                    self.grant_loot_and_xp()
                self.transition_to_exploration()
                
        elif self.state == GameStates.INVENTORY:
            # Show inventory (works in both modes)
            
        elif self.state == GameStates.CHARACTER_SCREEN:
            # Show stats, equipment
```

---

## Effort Breakdown

| Component | Reuse | Build New | Time Estimate | Complexity |
|-----------|-------|-----------|---------------|------------|
| Exploration/Map | 95% | 5% | 1 week | Add quest system, dialogue |
| Combat Stats/Equipment | 100% | 0% | 0 days | Already complete |
| Status Effects | 100% | 0% | 0 days | Already complete |
| AI Framework | 80% | 20% | 1 week | Add match-3 strategy AI |
| **Match-3 Engine** | **0%** | **100%** | **3-6 weeks** | **Core new system** |
| **Battle Integration** | 10% | 90% | 2-3 weeks | Gem → combat translation |
| Rendering (Hybrid) | 70% | 30% | 1-2 weeks | Add pygame gem renderer |
| UI/Menus | 80% | 20% | 1 week | Battle UI, quest log |
| **TOTAL** | **~65%** | **~35%** | **8-14 weeks** | **2-3 months full-time** |

---

## Key Technical Challenges

### 1. Match-3 Algorithm Complexity
- **Challenge**: Efficient match detection + cascade processing
- **Solution**: Flood-fill or BFS for matches, recursive cascade handling
- **Complexity**: Medium

### 2. Rendering Dual Systems
- **Challenge**: Switching between tcod (exploration) and pygame (battle)
- **Solution**: Renderer abstraction layer, share same game state
- **Complexity**: Medium

### 3. AI for Match-3
- **Challenge**: Making AI tactical without being too hard/frustrating
- **Solution**: Move scoring system, difficulty-based lookahead depth
- **Complexity**: Medium-High

### 4. Balancing Gem → Combat Translation
- **Challenge**: Making match-3 feel impactful and strategic
- **Solution**: Extensive playtesting, equipment scaling, combo bonuses
- **Complexity**: High (iterative design)

### 5. Animation Performance
- **Challenge**: Smooth gem animations without lag
- **Solution**: Sprite batching, efficient redraw, animation queuing
- **Complexity**: Medium

---

## Development Phases

### Phase 1: Foundation (2-3 weeks)
1. Set up new project structure
2. Copy/adapt core systems from rlike:
   - Component system
   - Entity system
   - Event bus
   - Fighter/Equipment/Inventory
   - Status effects
3. Create basic Match3Board class (no rendering yet)
4. Implement match detection algorithms
5. Unit tests for match detection

**Milestone**: Match-3 logic works in console/tests

### Phase 2: Battle Rendering (2-3 weeks)
1. Set up pygame rendering system
2. Create gem sprites or graphics
3. Implement board rendering
4. Add swap animations
5. Add match/cascade animations
6. Particle effects

**Milestone**: Can play match-3 game with mouse

### Phase 3: Battle Integration (2-3 weeks)
1. Build BattleManager class
2. Connect gem matches → damage/mana
3. Integrate spell casting (mana costs)
4. Apply equipment bonuses in battle
5. Status effects during battle
6. Battle UI (HP bars, mana display, turn indicator)

**Milestone**: Full combat loop with stats/equipment

### Phase 4: Exploration Mode (2-3 weeks)
1. Adapt map generation for overworld
2. Add quest system
3. NPC dialogue
4. Shop system
5. Battle trigger system
6. Victory/defeat flow

**Milestone**: Complete exploration → battle → exploration loop

### Phase 5: Enemy AI (1-2 weeks)
1. Implement move scoring
2. Test different AI strategies
3. Add difficulty levels
4. Balance AI behavior

**Milestone**: Challenging but fair AI opponents

### Phase 6: Polish & Balance (2-4 weeks)
1. Add more enemy types
2. More spells and items
3. Quest line development
4. Balance tuning
5. Sound effects and music
6. Save/load testing
7. Bug fixing

**Milestone**: Playable alpha

---

## Recommended Approach

### Option A: New Project with Copied Systems (Recommended)
**Pros**:
- Clean separation of concerns
- No risk of breaking current game
- Can iterate on PQ-specific features freely
- Current rlike remains stable

**Cons**:
- Initial setup overhead
- Code duplication (mitigated by good abstraction)

### Option B: Fork Current Project
**Pros**:
- Start with everything in place
- Easier initial setup

**Cons**:
- Will end up deleting/rewriting 40% anyway
- Git history becomes confusing
- Risk of breaking existing systems

### Option C: Modular Extension
**Pros**:
- Could support both game modes in one project
- Maximum code reuse

**Cons**:
- Complex architecture
- Maintenance overhead
- Unclear why you'd want both in one binary

**Recommendation**: **Option A** - New project, copy proven systems

---

## Technology Stack

### Keep from Current Project
- Python 3.x
- Core game logic in pure Python
- tcod for ASCII/tile rendering (exploration mode)
- JSON for data files (entities, levels, configs)
- pytest for testing

### Add for Puzzle Quest
- **Pygame** - Match-3 rendering, animations, gem graphics
- **Pillow** (PIL) - Gem sprite generation if needed
- **Numpy** (optional) - Fast grid operations for match detection
- **PyTween** (optional) - Animation easing

### Rendering Strategy
```python
class Renderer:
    def __init__(self):
        self.tcod_console = init_tcod()  # Exploration
        self.pygame_surface = init_pygame()  # Battle
        
    def render_exploration(self, game_map, entities):
        # Use tcod (current system)
        
    def render_battle(self, match3_board, battle_state):
        # Use pygame for gem board
```

---

## Files to Copy/Adapt from Current Project

### Copy Directly (Minimal Changes)
```
components/
  ├─ fighter.py          # HP, stats, combat - PERFECT
  ├─ equipment.py        # Equipment management
  ├─ equippable.py       # Equipment bonuses
  ├─ inventory.py        # Item management
  ├─ level.py            # XP/leveling
  ├─ status_effects.py   # Buffs/debuffs
  └─ component_registry.py  # ECS framework

events/                  # Entire event system - GOLD
  ├─ bus.py
  ├─ core.py
  ├─ dispatcher.py
  ├─ listener.py
  ├─ game_events.py      # Extend with Match3Event types
  └─ patterns.py

entity.py               # Core entity system
equipment_slots.py      # Slot enumeration
game_messages.py        # Message log
dice.py                 # Random utilities
```

### Adapt Heavily
```
map_objects/game_map.py  # Convert to overworld map
components/ai.py         # Add battle AI
game_states.py          # Add MATCH3_BATTLE state
engine.py               # Main game loop - split exploration/battle
```

### Don't Copy (Build New)
```
battle/
  ├─ match3_board.py     # NEW
  ├─ match_detector.py   # NEW
  ├─ gem_physics.py      # NEW
  ├─ battle_manager.py   # NEW
  ├─ battle_ai.py        # NEW
  └─ battle_renderer.py  # NEW (pygame)

ui/
  └─ battle_ui.py        # NEW

quest_system.py          # NEW
dialogue_system.py       # NEW
overworld_map.py         # NEW
```

---

## Example Code Snippets

### Match Detection Algorithm
```python
def find_horizontal_matches(self) -> List[Match]:
    """Find all horizontal 3+ matches"""
    matches = []
    for y in range(self.height):
        x = 0
        while x < self.width:
            gem = self.grid[x][y]
            if gem is None:
                x += 1
                continue
                
            # Count consecutive matching gems
            count = 1
            match_gems = [(x, y)]
            while x + count < self.width and self.grid[x + count][y] == gem:
                match_gems.append((x + count, y))
                count += 1
            
            if count >= 3:
                matches.append(Match(gem, match_gems))
                x += count
            else:
                x += 1
    return matches
```

### Battle Integration
```python
def process_gem_matches(self, matches: List[Match]) -> List[BattleResult]:
    """Convert gem matches to combat effects"""
    results = []
    
    for match in matches:
        gem_count = len(match.gems)
        
        if match.gem_type == "skull":
            # Direct damage using Fighter system
            damage = gem_count
            # Apply STR modifier
            damage += self.player.fighter.strength_mod
            # Apply weapon bonus
            damage += self.player.equipment.power_bonus
            
            damage_results = self.enemy.fighter.take_damage(damage)
            results.extend(damage_results)
            
        else:
            # Add mana for spell casting
            self.player_mana[match.gem_type] += gem_count
            results.append({
                'message': f"Gained {gem_count} {match.gem_type} mana"
            })
        
        # Combo bonuses for 4+ matches
        if gem_count >= 4:
            results.append(self.grant_extra_turn())
        
        if gem_count >= 5:
            results.append(self.apply_status_effect(self.enemy, "stunned"))
    
    return results
```

---

## Questions to Consider

1. **Art Style**: Pixel art gems? Shiny 3D-rendered gems? ASCII gems?
2. **Scope**: Single-player campaign or multiplayer battles?
3. **Quest Structure**: Linear story or open-world exploration?
4. **Equipment Progression**: How deep? Crafting? Enhancement?
5. **Spell Variety**: How many spells? Elemental system depth?
6. **Enemy Variety**: How many unique enemies? Special abilities?
7. **Battle Mechanics**: Power gems? Wildcard gems? Special board tiles?

---

## Conclusion

Building a Puzzle Quest-style game with your current engine is **absolutely viable** and would be a **fantastic project**. You've already built 65% of the foundation:

### What You Have ✅
- Complete RPG stat system (STR/DEX/CON, HP, AC)
- Full equipment system (5 slots, bonuses, upgrades)
- Status effects (buffs, debuffs, duration tracking)
- Sophisticated event system (enterprise-grade!)
- Entity/component architecture (clean, extensible)
- AI framework (adaptable to match-3 strategy)
- Map generation (converts to overworld)
- Game state management (extend for battle mode)

### What You Need to Build 🔨
- Match-3 engine (board, detection, cascades) - **3-6 weeks**
- Battle integration (gems → combat) - **2-3 weeks**
- Gem rendering (pygame or enhanced tcod) - **1-2 weeks**
- Battle AI (strategic gem matching) - **1-2 weeks**

### Total Estimate: 2-3 months full-time

The match-3 layer would integrate **cleanly** with your existing systems rather than requiring a rewrite. Your event bus, component system, and RPG mechanics are exactly what Puzzle Quest needs under the hood.

**Recommendation**: Start a new project, copy the proven systems (components, events, entity), and build the match-3 engine as a new layer that leverages these existing foundations.

---

## Next Steps When Ready

1. Review this document and refine scope
2. Create new project repository
3. Set up project structure (exploration/ battle/ core/)
4. Copy core systems from rlike
5. Start Phase 1: Match-3 foundation
6. Build iteratively, test frequently
7. Playtest and balance continuously

Good luck! This is a challenging but very achievable project with your current foundation. 🎮✨
