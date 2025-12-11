# 🤖 AI System Documentation

**Date:** January 2025  
**Status:** ✅ Production Ready  
**Version:** v3.7.0+ (Monster Equipment & Loot)

---

## 📋 Overview

The AI system controls all non-player entity behavior, including combat decisions, movement, item usage, and special abilities. The system supports multiple AI types with different behaviors, faction-based combat, and status effect interactions.

### Key Features

- **Multiple AI Types** - Basic, Slime, Zombie, Confused
- **A* Pathfinding** - Intelligent obstacle avoidance
- **Faction System** - Monster-vs-monster combat
- **Item Seeking** - Monsters pick up equipment
- **Item Usage** - Monsters use scrolls and potions
- **Status Effects** - AI responds to buffs/debuffs
- **Combat Tracking** - In-combat vs passive states

---

## 🎯 AI Types

### BasicMonster AI

**Purpose:** Standard hostile monster behavior  
**Used By:** Orcs, Trolls, most enemies

**Behavior:**
1. **Passive State:** Stand still until player enters FOV
2. **Active State:** Chase and attack player
3. **In-Combat Flag:** Once attacked, remains aggressive even when player leaves FOV
4. **Item Seeking:** Can pick up nearby equipment while moving
5. **Item Usage:** Can use scrolls/potions (with failure rates)

**Decision Tree:**
```
IF taunted_target exists:
    → Target the taunted entity (Yo Mama spell)
ELSE IF in_combat OR player_in_fov:
    IF item_nearby AND not in_combat:
        → Pick up item
    IF distance <= weapon_reach:
        → Attack target
    ELSE:
        → Move towards target using A*
ELSE:
    → Stand still (passive)
```

**Code Location:** `components/ai/basic_monster.py` - `BasicMonster` class

---

### SlimeAI

**Purpose:** Hostile-to-all faction that attacks everything  
**Used By:** Slimes, oozes

**Behavior:**
1. **Target Priority:** Closest hostile entity
2. **Player Preference:** Always prefer player if tied for distance
3. **Monster Combat:** Will attack other monsters
4. **No Faction Loyalty:** Hostile to everyone

**Decision Tree:**
```
Find all hostile entities in FOV
Calculate distances
Sort by:
    1. Distance (closest first)
    2. Type (player first if tied)

IF best_target exists:
    IF distance <= weapon_reach:
        → Attack target
    ELSE:
        → Move towards target using A*
```

**Special Properties:**
- Faction: `HOSTILE_ALL`
- Enables monster-vs-monster combat
- Used for chaotic encounters

**Code Location:** `components/ai/slime_ai.py` - `SlimeAI` class

---

### MindlessZombieAI

**Purpose:** Raised dead that attack everything mindlessly  
**Used By:** Zombies (from Raise Dead scroll)

**Behavior:**
1. **Attack Priority:** ANY adjacent entity (player, monster, other zombies)
2. **Sticky Targeting:** Continues attacking same target
3. **Target Switching:** 50% chance to switch if new entity gets adjacent
4. **Random Wandering:** Moves randomly when no target
5. **FOV-Based:** Only acts when can see targets

**Decision Tree:**
```
IF current_target AND current_target adjacent AND alive:
    → Continue attacking current_target (sticky behavior)
    
Check all adjacent entities:
    IF 50% chance AND new entity found:
        → Switch to new target
        → Attack new target
    ELSE IF has current_target:
        → Attack current_target
    ELSE:
        → Pick random adjacent entity
        → Attack it

IF no adjacent entities:
    → Wander randomly
```

**Special Properties:**
- No faction loyalty
- Attack friends and foes alike
- Not reliable allies
- Sticky targeting makes them focused

**Code Location:** `components/ai/mindless_zombie.py` - `MindlessZombieAI` class

---

### ConfusedMonster AI

**Purpose:** Temporary confusion status (from Confusion scroll)  
**Used By:** Any monster hit by confusion

**Behavior:**
1. **Random Movement:** 80% chance to move randomly
2. **Attack Anything:** 20% chance to attack adjacent entity (ANY faction)
3. **Duration:** Temporary (N turns)
4. **Reverts:** Returns to previous AI when confusion ends

**Decision Tree:**
```
IF random() < 0.8:
    → Move randomly (8 directions)
    → Log: "The Orc stumbles around"
ELSE:
    → Check adjacent entities
    → Attack random adjacent entity (ANY faction!)
    → Log: "The Orc lashes out wildly"
```

**Special Properties:**
- Temporary AI replacement
- Can damage allies
- Chaotic behavior

**Code Location:** `components/ai/confused_monster.py` - `ConfusedMonster` class

---

## 🎯 Combat Decision Making

### Target Selection

**BasicMonster:**
```python
1. Check for taunted target (Yo Mama spell)
2. Default to player
```

**SlimeAI:**
```python
1. Check for taunted target
2. Find all hostile entities in FOV
3. Sort by distance (closest first)
4. Prefer player if tied
5. Attack closest hostile
```

**MindlessZombieAI:**
```python
1. Check current_target (sticky)
2. Check all adjacent entities
3. 50% chance to switch targets
4. Attack ANY adjacent entity
```

### Attack vs Move

All AI types follow this pattern:
```python
distance = monster.distance_to(target)
weapon_reach = get_weapon_reach(monster)  # Usually 1, spears = 2

if distance <= weapon_reach:
    # Within range - attack!
    attack_results = monster.fighter.attack_d20(target)
else:
    # Too far - move closer
    if not immobilized:  # Check for Glue spell
        monster.move_astar(target, entities, game_map)
```

---

## 🚶 Movement & Pathfinding

### A* Pathfinding

All AI types use A* algorithm for intelligent pathfinding:

**Features:**
- Obstacle avoidance
- Shortest path calculation
- Hazard awareness (fire, poison gas)
- Entity collision avoidance

**Hazard Costs:**
```python
# Normal tile: cost = 1
# Diagonal: cost = 1.41 (√2)
# Hazard tile: cost = 1 + (damage * 10)
```

**Example:**
- Fire tile (10 damage): cost = 101
- Poison gas (3 damage): cost = 31
- Monsters prefer safe routes unless desperate

**Code Location:** `entity.py` - `move_astar()` method

### Movement Patterns

**BasicMonster:**
- Move towards player when in FOV
- Stop moving when player leaves FOV (unless in_combat)
- Can detour to pick up items

**SlimeAI:**
- Always move towards closest hostile
- Aggressive pursuit
- No passive state

**MindlessZombieAI:**
- Random wandering when no target
- Direct movement towards current target
- Chaotic, unpredictable

**ConfusedMonster:**
- 80% random movement
- 20% attack adjacent
- No intelligent pathfinding

---

## 🎒 Item Seeking & Usage

### Item Seeking (BasicMonster Only)

**Configuration:**
```python
ENABLE_ITEM_SEEKING = True        # Feature toggle
ITEM_SEEK_DISTANCE = 5           # Max distance to seek
ITEM_PRIORITY_OVER_PLAYER = True # Pick up items even when player nearby
```

**Behavior:**
```python
IF not in_combat:
    nearby_items = find_items_within(ITEM_SEEK_DISTANCE)
    
    IF nearby_items:
        closest_item = min(nearby_items, key=distance)
        
        IF adjacent_to(closest_item):
            → Pick up item
            → Equip if weapon/armor
        ELSE:
            → Move towards item (ignore player temporarily)
```

**Item Priority:**
- Weapons > Armor > Scrolls > Potions
- Better equipment preferred
- Won't pick up if inventory full (no inventory system for monsters currently)

### Item Usage (BasicMonster Only)

**Configuration:**
```python
SCROLL_FAILURE_RATE = 0.75  # 75% failure (monsters aren't smart!)
POTION_FAILURE_RATE = 0.20  # 20% failure (easier to use)
```

**Behavior:**
```python
IF has_scroll AND random() > SCROLL_FAILURE_RATE:
    → Attempt to use scroll
    → May fizzle (75% of the time)
    → Log: "The Orc tries to read a scroll... fizzles!"
    
IF hp < max_hp * 0.5 AND has_potion:
    → Use healing potion (80% success)
```

**Supported Items:**
- Lightning Scrolls
- Fireball Scrolls
- Healing Potions
- Other consumables

**Code Location:** 
- `components/monster_item_usage.py` - Item usage logic
- `components/item_seeking_ai.py` - Item seeking behavior

---

## 🏳️ Faction System

### Faction Types

**Faction.HOSTILE (Default):**
- Hostile to player
- Friendly to other HOSTILE monsters
- Will not attack each other

**Faction.HOSTILE_ALL (Slimes):**
- Hostile to player
- Hostile to ALL other entities
- Enables monster-vs-monster combat

**Faction.FRIENDLY (Unused):**
- Friendly to player
- Reserved for future allies/pets

### Faction Checking

```python
from components.faction import are_factions_hostile

if are_factions_hostile(entity1_faction, entity2_faction):
    # These entities will attack each other
    can_attack = True
```

**Faction Matrix:**
```
              | HOSTILE | HOSTILE_ALL | FRIENDLY
--------------|---------|-------------|----------
HOSTILE       | No      | Yes         | Yes
HOSTILE_ALL   | Yes     | Yes         | Yes
FRIENDLY      | Yes     | Yes         | No
```

**Code Location:** `components/faction.py`

---

## ⚡ Status Effect Integration

### Status Effect Processing

All AI types check status effects at turn start:

```python
# At the start of every turn
status_effects = self.owner.get_component_optional(ComponentType.STATUS_EFFECTS)
if status_effects:
    effect_results = status_effects.process_turn_start()
    
    for result in effect_results:
        if result.get('skip_turn'):
            # Effect wants to skip this turn (e.g., Slow effect)
            return results  # Early exit, skip entire turn
```

### Common Status Effects

**Slowed:**
- Skip every other turn
- Movement reduced by 50%

**Immobilized (Glue):**
- Cannot move
- Can still attack if target in range
- Message: "The Orc struggles against the glue!"

**Taunted (Yo Mama):**
- All monsters target the taunted entity
- Overrides normal target selection
- Creates monster-vs-monster fights

**Confused:**
- Replaces AI entirely
- Random movement + wild attacks
- Temporary duration

**Shielded:**
- Doesn't affect AI behavior
- Just a defensive buff

---

## 🎮 Special AI Mechanics

### Yo Mama Spell (Taunt)

**How It Works:**
1. Player casts Yo Mama on target monster
2. Target gains `taunted` status effect
3. ALL other monsters change target to taunted entity
4. Monsters pursue and attack taunted monster
5. When taunted monster dies OR effect expires:
   - Monsters return to normal behavior
   - Stop pursuing if player not in FOV

**Code:**
```python
taunted_target = find_taunted_target(entities)

if taunted_target:
    if taunted_target == self.owner:
        # THIS monster is taunted - fight back!
        is_taunted_target = True
    else:
        # Another monster is taunted - pursue it!
        target = taunted_target
        is_pursuing_taunt = True
```

### In-Combat Flag

**Purpose:** Monsters remember if they've been attacked

**Behavior:**
```python
# Set when monster takes damage
def take_damage(self, amount):
    self.hp -= amount
    ai = self.owner.get_component_optional(ComponentType.AI)
    if ai:
        ai.in_combat = True  # Remember we were attacked!
```

**Effect:**
- Monster continues chasing player even when out of FOV
- Prevents "peek-a-boo" exploit
- Only cleared on death or game reload

---

## 🐛 Common Issues & Solutions

### "Monster stands still when player visible"

**Problem:** FOV check failing  
**Solution:** Check `map_is_in_fov(fov_map, monster.x, monster.y)`

### "Monster ignores items on ground"

**Problem:** Item seeking disabled or item too far  
**Solution:** Check `ENABLE_ITEM_SEEKING = True` and `ITEM_SEEK_DISTANCE >= distance`

### "Monster uses scroll every turn"

**Problem:** No usage tracking  
**Solution:** Scrolls are consumed after use - check if still in inventory

### "Slimes don't attack other monsters"

**Problem:** Faction not set to HOSTILE_ALL  
**Solution:** Set `Faction.HOSTILE_ALL` in entity config

### "Zombies attack player only"

**Problem:** Not checking all adjacent entities  
**Solution:** Verify `_find_adjacent_targets()` logic

---

## 🔧 Code Examples

### Creating Custom AI

```python
class CustomAI:
    """Custom AI with unique behavior."""
    
    def __init__(self):
        self.owner = None
        self.in_combat = False
    
    def take_turn(self, target, fov_map, game_map, entities):
        """Execute one turn of AI behavior."""
        results = []
        monster = self.owner
        
        # 1. Process status effects
        status_effects = monster.get_component_optional(ComponentType.STATUS_EFFECTS)
        if status_effects:
            effect_results = status_effects.process_turn_start()
            for result in effect_results:
                if result.get('skip_turn'):
                    return [result]  # Skip turn
                results.append(result)
        
        # 2. Choose target
        custom_target = self._select_target(target, entities, fov_map)
        
        # 3. Act on target
        if custom_target:
            distance = monster.distance_to(custom_target)
            weapon_reach = get_weapon_reach(monster)
            
            if distance <= weapon_reach:
                # Attack!
                attack_results = monster.fighter.attack_d20(custom_target)
                results.extend(attack_results)
            else:
                # Move closer
                monster.move_astar(custom_target, entities, game_map)
        
        return results
    
    def _select_target(self, default_target, entities, fov_map):
        """Custom target selection logic."""
        # Your custom targeting here
        return default_target
```

### Adding AI to Entity

```python
from components.ai import BasicMonster

# In entity_factory.py
monster = Entity(
    x, y, char='o', color=(63, 127, 63),
    name='Orc', blocks=True, render_order=RenderOrder.ACTOR
)

# Add AI component
ai_component = BasicMonster()
monster.components.register(ComponentType.AI, ai_component)

# Add Fighter for combat
fighter_component = Fighter(hp=20, defense=0, power=4)
monster.components.register(ComponentType.FIGHTER, fighter_component)
```

---

## 📊 AI Complexity Comparison

| AI Type | Complexity | Target Selection | Movement | Special Features |
|---------|------------|------------------|----------|------------------|
| **BasicMonster** | Medium | Player only | A* pathfinding | Item seeking, item usage |
| **SlimeAI** | Medium | Closest hostile | A* pathfinding | Monster-vs-monster |
| **MindlessZombieAI** | High | Any adjacent | Random wander | Sticky targeting, chaotic |
| **ConfusedMonster** | Low | Random adjacent | Random | Temporary status |

---

## 🔮 Future Enhancements

### Planned Features

- **Pack Tactics:** Monsters coordinate attacks (+2 to-hit when ally adjacent)
- **Retreat Behavior:** Low HP monsters flee
- **Ranged AI:** Special behavior for archers
- **Spellcaster AI:** Monsters cast spells intelligently
- **Boss AI:** Multi-phase boss battles
- **Pet AI:** Controllable companion behavior

### Possible Improvements

- **Better Item Prioritization:** Evaluate item value before picking up
- **Scroll Success Rates:** Smart monsters (mages) have better success
- **Coordinated Movement:** Monsters flank player
- **Memory System:** Remember player's last known position
- **Aggro System:** Track which entity dealt most damage
- **Formation AI:** Monsters maintain battle formations

---

## 📚 Related Files

### Core AI Files
- `components/ai.py` - Main AI implementations
- `components/monster_action_logger.py` - AI debugging
- `components/item_seeking_ai.py` - Item seeking logic
- `components/monster_item_usage.py` - Item usage logic
- `components/faction.py` - Faction system

### Integration Files
- `entity.py` - `move_astar()` pathfinding
- `engine/systems/ai_system.py` - AI turn processing
- `fov_functions.py` - Visibility checks
- `game_actions.py` - Action processing

### Configuration
- `config/entities.yaml` - Monster AI type assignment
- `config/game_constants.py` - AI behavior constants

---

## 🎓 Quick Reference

### AI Decision Priority

```
1. Status effects (skip turn if needed)
2. Taunt target check (Yo Mama spell)
3. In-combat flag OR FOV check
4. Item seeking (if not in combat)
5. Distance check → Attack or Move
```

### Common Checks

```python
# Check if monster in player FOV
in_fov = map_is_in_fov(fov_map, monster.x, monster.y)

# Check weapon reach
reach = get_weapon_reach(monster)

# Check if taunted target exists
taunted = find_taunted_target(entities)

# Check faction hostility
hostile = are_factions_hostile(faction1, faction2)
```

---

**Last Updated:** January 2025  
**Maintainer:** Development Team  
**Status:** Production Ready ✅

