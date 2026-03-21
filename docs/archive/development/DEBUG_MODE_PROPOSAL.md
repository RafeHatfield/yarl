# Debug Mode & Advanced Playtesting System - Proposal

## 🎯 Problem Statement

Current playtesting challenges for victory/story features:
- **Time Investment**: Testing level 20 Guide encounter requires ~30-45 minutes of gameplay
- **Repetitive**: Each test run requires re-descending entire dungeon
- **Risk**: Can die before reaching test target
- **Iteration Speed**: Slow feedback loop kills development momentum
- **Feature Coverage**: Hard to test edge cases and combinations

## 🔍 Research: How Other Roguelikes Handle This

### NetHack - "Wizard Mode"
**Activation**: Compile-time flag or `nethack -D` (wizard mode)

**Key Features**:
- `^W` - Wish for any item ("blessed +3 gray dragon scale mail")
- `^E` - Detect all monsters/items
- `^F` - Map entire level
- `^G` - Genesis (create monster)
- `^I` - Identify all items
- `^T` - Teleport anywhere
- `^V` - Level teleport (go to any dungeon level)
- Can't die (HP never goes below 1)
- No high scores recorded

**Philosophy**: "Break the game to test the game"

### Dungeon Crawl Stone Soup (DCSS) - "&debug" Menu
**Activation**: `&` key opens debug menu (must be compiled with DEBUG flag)

**Key Features**:
- Gain experience instantly
- Gain piety with gods
- Teleport to any branch/level
- Wizard mode protection (can't die)
- Create any monster/item
- Reveal the entire map
- Blink anywhere
- Edit character stats
- Gain all spells

**Philosophy**: Interactive menu system for precision testing

### Brogue - "Recording" Mode
**Activation**: `-s` flag to record, playback with filename

**Key Features**:
- Records all RNG seeds
- Deterministic playback
- Can fast-forward to specific turn
- Automated regression testing
- "This game is a recording" UI indicator

**Philosophy**: Reproducibility for bug hunting

### Caves of Qud - "Wish" System + Debug Commands
**Activation**: Modded game or dev build

**Key Features**:
- Wish system (type item/creature name to spawn)
- God mode toggle
- Reveal all
- Teleport to zone
- Modify stats/skills
- Grant experience/levels

## 💡 Recommended Solution: Multi-Tiered Approach

### Tier 1: **Enhanced Testing Mode** (ALREADY EXISTS, EXTEND IT) ⚡
**Target**: Quick feature testing, no cheating feel
**Activation**: `YARL_TESTING_MODE=1` or `--testing` flag
**Status**: ✅ Already implemented, needs extension

**Current Features**:
- Level templates with guaranteed spawns
- More items per room
- Combat debug logging

**Proposed Extensions**:
```bash
# New command-line arguments
python engine.py --testing --start-level 15  # Start on level 15
python engine.py --testing --god-mode         # Can't die
python engine.py --testing --reveal-map       # Full FOV always
python engine.py --testing --fast-explore     # Auto-explore at 10x speed
```

**Implementation**:
- Add `--start-level N` flag to skip to specific level
- Add `--god-mode` flag (HP never goes below 1)
- Add `--reveal-map` flag (FOV covers entire level)
- Add `--no-monsters` flag (peaceful mode for story testing)
- Store these in `TestingConfig` class
- **Estimated Time**: 4-6 hours

### Tier 2: **Wizard Mode** (NEW, INTERACTIVE) 🧙
**Target**: Deep debugging, testing edge cases
**Activation**: `python engine.py --wizard` or `W` key in testing mode
**Status**: 🔲 Not implemented, HIGH VALUE

**Proposed Features**:
1. **In-Game Debug Menu** (Press `&` or `F12`)
   ```
   === WIZARD MODE ===
   L - Teleport to Level
   I - Spawn Item
   M - Spawn Monster
   H - Heal to Full
   X - Gain XP
   K - Learn Knowledge (for Guide testing!)
   T - Toggle God Mode
   R - Reveal Map
   ESC - Close Menu
   ```

2. **Quick Commands** (No menu needed)
   - `Ctrl+L` - Level up instantly
   - `Ctrl+H` - Heal to full
   - `Ctrl+T` - Teleport to cursor
   - `Ctrl+K` - Kill all monsters on level
   - `Ctrl+R` - Reveal entire map
   - `Ctrl+G` - God mode toggle

3. **Knowledge Command** (FOR PHASE 3 TESTING!)
   ```python
   # Press 'K' in wizard mode
   player.victory.unlock_knowledge("entity_true_name_zhyraxion")
   player.victory.knows_entity_true_name = True
   message_log.add_message("DEBUG: Learned Zhyraxion's true name")
   ```

4. **NPC Spawning**
   ```python
   # Press 'N' in wizard mode, type "guide"
   factory.create_unique_npc('ghost_guide', player.x + 1, player.y, dungeon_level)
   ```

**Implementation**:
- Create `wizard_mode.py` module
- Add `WizardMenu` screen (like inventory menu)
- Add wizard commands to `input_handlers.py`
- Add `--wizard` flag parsing
- Prevent save/score recording in wizard mode
- **Estimated Time**: 8-12 hours

### Tier 3: **Save State System** (NEW, ADVANCED) 💾
**Target**: Test specific scenarios repeatedly
**Activation**: `--save-state NAME` / `--load-state NAME`
**Status**: 🔲 Not implemented, MEDIUM VALUE

**Proposed Features**:
```bash
# Save current game state
python engine.py --testing --save-state "level15_before_guide"

# Load saved state
python engine.py --testing --load-state "level15_before_guide"

# List all saved states
python engine.py --list-states
```

**Use Cases**:
- Save at level 15 before talking to Guide
- Load state, test dialogue paths
- Reset and try different options
- No need to replay 15 levels each time

**Implementation**:
- Extend existing save/load system
- Store in `debug_saves/` directory
- Include full game state (map, entities, RNG seed)
- Quick load from command line
- **Estimated Time**: 6-8 hours

### Tier 4: **Automated Playthrough** (NEW, ADVANCED) 🤖
**Target**: Regression testing, overnight runs
**Activation**: `--autoplay SCRIPT`
**Status**: 🔲 Not implemented, FUTURE

**Proposed Features**:
```python
# scripts/test_guide_all_encounters.py
autoplay = AutoPlayScript()
autoplay.start_level(1)
autoplay.descend_to_level(5)
autoplay.find_npc("ghost_guide")
autoplay.talk_to_npc()
autoplay.choose_option("who_are_you")
autoplay.verify_knowledge_not_unlocked("entity_true_name")
autoplay.descend_to_level(15)
# ... etc
```

**Implementation**:
- Create `autoplay.py` system
- Record/playback input sequences
- Assert game state conditions
- Generate detailed logs
- **Estimated Time**: 12-16 hours

## 🎯 Recommended Implementation Order

### Phase A: **Quick Wins** (1-2 days) ⚡⚡⚡
**Priority**: IMMEDIATE - Solves 80% of your problem NOW

1. **Command-Line Level Skip** (2 hours)
   ```bash
   python engine.py --testing --start-level 20
   ```
   - Modify `engine.py` argument parsing
   - Call `game_map.next_floor()` N times before game starts
   - Give player appropriate gear for level
   - **Impact**: Test level 20 Guide in 30 seconds instead of 30 minutes

2. **God Mode Flag** (1 hour)
   ```bash
   python engine.py --testing --god-mode
   ```
   - Check in `Fighter.take_damage()`
   - If god mode: `self.hp = max(1, self.hp)`
   - **Impact**: Can't die during testing

3. **No Monsters Flag** (1 hour)
   ```bash
   python engine.py --testing --no-monsters
   ```
   - Check in `GameMap.place_entities()`
   - Skip monster spawning entirely
   - **Impact**: Focus on story without combat

4. **Reveal Map Flag** (1 hour)
   ```bash
   python engine.py --testing --reveal-map
   ```
   - Set FOV radius to 999 in testing mode
   - **Impact**: Find Guide instantly, no exploration needed

**Total Time**: ~5 hours
**Value**: Massive - Solves immediate Phase 3+ testing needs

### Phase B: **Wizard Mode** (3-4 days) 🧙
**Priority**: HIGH - For deep feature testing

1. **Basic Debug Menu** (4 hours)
   - Create `wizard_menu.py`
   - Add `&` key handler
   - Implement menu rendering

2. **Core Commands** (4 hours)
   - Level teleport
   - Spawn item
   - Spawn monster/NPC
   - Heal to full

3. **Knowledge System Integration** (2 hours)
   - Add knowledge unlock command
   - Add knowledge display
   - **Critical for testing Phases 4-6!**

**Total Time**: ~10 hours
**Value**: High - Enables edge case testing

### Phase C: **Save States** (2-3 days) 💾
**Priority**: MEDIUM - Nice to have

1. **Save State Command** (4 hours)
2. **Load State Command** (2 hours)
3. **State Management UI** (2 hours)

**Total Time**: ~8 hours
**Value**: Medium - Quality of life improvement

### Phase D: **Automated Testing** (1 week) 🤖
**Priority**: LOW - Future optimization

**Total Time**: ~16 hours
**Value**: Low initially, high for regression prevention

## 📋 Detailed Implementation Plan - Phase A (START HERE!)

### 1. Command-Line Argument System

**File**: `engine.py`

```python
import argparse

def parse_arguments():
    """Parse command-line arguments for debug/testing features."""
    parser = argparse.ArgumentParser(description='Catacombs of YARL')
    
    # Testing mode
    parser.add_argument('--testing', action='store_true',
                       help='Enable testing mode with extra items')
    
    # Debug features (require --testing)
    parser.add_argument('--start-level', type=int, metavar='N',
                       help='Start game on dungeon level N (requires --testing)')
    parser.add_argument('--god-mode', action='store_true',
                       help='Enable god mode (cannot die) (requires --testing)')
    parser.add_argument('--no-monsters', action='store_true',
                       help='Disable monster spawning (requires --testing)')
    parser.add_argument('--reveal-map', action='store_true',
                       help='Reveal entire map (requires --testing)')
    
    # Wizard mode (most powerful)
    parser.add_argument('--wizard', action='store_true',
                       help='Enable wizard mode (all debug features + interactive menu)')
    
    return parser.parse_args()

# In main():
args = parse_arguments()
if args.testing or args.wizard:
    set_testing_mode(True)
    print("🧪 TESTING MODE ENABLED")

if args.wizard:
    config.wizard_mode = True
    print("🧙 WIZARD MODE ENABLED - Press & for debug menu")

if args.god_mode or args.wizard:
    config.god_mode = True
    print("🛡️ GOD MODE ENABLED - You cannot die")

if args.no_monsters or args.wizard:
    config.no_monsters = True
    print("☮️ PEACEFUL MODE - No monsters will spawn")
```

### 2. Level Skip Implementation

**File**: `engine.py` (in new_game function)

```python
def new_game(constants, args=None):
    # ... existing setup ...
    
    # DEBUG: Skip to specific level
    if args and args.start_level and args.start_level > 1:
        target_level = args.start_level
        print(f"⏭️ Skipping to level {target_level}...")
        
        # Descend to target level
        for i in range(target_level - 1):
            game_map.next_floor(player, constants)
        
        # Give player appropriate gear for this level
        _grant_level_appropriate_gear(player, target_level, entities)
        
        # Update player stats for survivability
        player.level.current_level = min(target_level // 2, 10)  # Half level depth
        player.fighter.max_hp = 30 + (player.level.current_level * 10)
        player.fighter.hp = player.fighter.max_hp
        
        print(f"✅ Started at dungeon level {game_map.dungeon_level}")
        print(f"   Player level: {player.level.current_level}")
        print(f"   HP: {player.fighter.hp}/{player.fighter.max_hp}")
    
    return player, entities, game_map, message_log, game_state

def _grant_level_appropriate_gear(player, dungeon_level, entities):
    """Give player gear suitable for testing at this depth."""
    from config.entity_factory import get_entity_factory
    factory = get_entity_factory()
    
    # Always give healing potions
    for i in range(5):
        potion = factory.create_item('healing_potion', 0, 0, 1)
        if potion and player.inventory:
            player.inventory.add_item(potion, silent=True)
    
    # Give basic combat gear
    if dungeon_level >= 5:
        sword = factory.create_weapon('sword', 0, 0)
        if sword and player.equipment:
            player.equipment.toggle_equip(sword)
    
    # Give armor for deeper levels
    if dungeon_level >= 10:
        chain_mail = factory.create_armor('chain_mail', 0, 0)
        if chain_mail and player.equipment:
            player.equipment.toggle_equip(chain_mail)
    
    # Give scrolls for escape
    if dungeon_level >= 15:
        for i in range(3):
            scroll = factory.create_item('teleport_scroll', 0, 0, dungeon_level)
            if scroll and player.inventory:
                player.inventory.add_item(scroll, silent=True)
```

### 3. God Mode Implementation

**File**: `components/fighter.py`

```python
def take_damage(self, amount):
    """Apply damage to this entity.
    
    Args:
        amount: Amount of damage to apply
        
    Returns:
        List of result dictionaries
    """
    results = []
    
    # DEBUG: God mode protection
    from config.testing_config import get_testing_config
    config = get_testing_config()
    if hasattr(config, 'god_mode') and config.god_mode and self.owner.name == "Player":
        if self.hp - amount < 1:
            self.hp = 1  # Never go below 1 HP
            from message_builder import MessageBuilder as MB
            results.append({
                'message': MB.warning("🛡️ GOD MODE: Damage prevented!")
            })
            return results
    
    # Normal damage application
    self.hp -= amount
    
    if self.hp <= 0:
        results.append({'dead': self.owner})
    
    return results
```

### 4. Testing Config Extensions

**File**: `config/testing_config.py`

```python
class TestingConfig:
    def __init__(self, testing_mode: bool = False):
        self.testing_mode = testing_mode
        
        # New debug flags (set by command-line args)
        self.god_mode = False
        self.no_monsters = False
        self.reveal_map = False
        self.wizard_mode = False
        self.start_level = 1
```

### 5. No Monsters Implementation

**File**: `map_objects/game_map.py`

```python
def place_entities(self, room, entities):
    """Place monsters and items in a room."""
    from config.testing_config import get_testing_config
    config = get_testing_config()
    
    # DEBUG: Skip monster spawning in peaceful mode
    if not hasattr(config, 'no_monsters') or not config.no_monsters:
        # Normal monster spawning
        number_of_monsters = get_random_monster_count(self.dungeon_level)
        for i in range(number_of_monsters):
            # ... spawn monsters ...
    
    # Always spawn items (even in peaceful mode)
    number_of_items = get_random_item_count(self.dungeon_level)
    # ... spawn items ...
```

## 🎮 Example Usage Scenarios

### Scenario 1: Test Level 20 Guide Encounter
```bash
# Before (30+ minutes):
python engine.py
# Play through 20 levels, find Guide, hope you don't die

# After (30 seconds):
python engine.py --testing --start-level 20 --god-mode --no-monsters
# Immediately on level 20, can't die, no combat distractions
# Press 'o' to auto-explore, find Guide, press 'T' to talk
```

### Scenario 2: Test Multiple Endings
```bash
# Test bad ending
python engine.py --testing --start-level 25 --god-mode
# Get amulet, enter portal, give amulet

# Test good ending
python engine.py --testing --start-level 25 --god-mode --wizard
# Get amulet, press 'K' in wizard mode to learn true name
# Enter portal, test redemption path
```

### Scenario 3: Test All Guide Encounters Quickly
```bash
# Level 5
python engine.py --testing --start-level 5 --no-monsters --reveal-map

# Level 10
python engine.py --testing --start-level 10 --no-monsters --reveal-map

# Level 15 (critical - true name!)
python engine.py --testing --start-level 15 --no-monsters --reveal-map

# Level 20
python engine.py --testing --start-level 20 --no-monsters --reveal-map
```

## 📊 Estimated Impact

### Time Savings (Per Test Cycle)
| Feature | Before | After | Savings |
|---------|--------|-------|---------|
| Level 5 Guide | ~5 min | ~30 sec | 90% |
| Level 10 Guide | ~10 min | ~30 sec | 95% |
| Level 15 Guide | ~20 min | ~30 sec | 97.5% |
| Level 20 Guide | ~30 min | ~30 sec | 98.3% |
| Level 25 Amulet | ~45 min | ~30 sec | 98.9% |

### Development Velocity Impact
- **Current**: 3-5 test cycles per day (if lucky)
- **With Phase A**: 50-100+ test cycles per day
- **Iteration Speed**: ~20x faster
- **Bug Finding**: Find edge cases you'd never discover manually

## 🚀 Recommendation

**START WITH PHASE A IMMEDIATELY** - It's a 5-hour investment that will save you 100+ hours over Phases 4-6 development.

The command-line flags are:
1. **Non-invasive** - No impact on normal gameplay
2. **Fast to implement** - Mostly argument parsing and conditionals
3. **Huge ROI** - 20x faster iteration immediately
4. **Foundation** - Sets up architecture for wizard mode later

Then add Wizard Mode (Phase B) when you need more advanced testing (spawning specific items, unlocking knowledge, etc.).

**Do you want me to implement Phase A now?** I can have `--start-level`, `--god-mode`, `--no-monsters`, and `--reveal-map` working in about 5 hours of work.

