# Slime System Design Specification

## Overview

The Slime System introduces tactical depth through monster-vs-monster combat, equipment corrosion mechanics, invisibility scrolls, and dynamic entity splitting. This system implements a general faction-based combat framework while focusing on slimes as the first hostile-to-all faction.

## Core Features

### **1. Faction-Based Combat System**

#### **Faction Framework**
```python
class Faction(Enum):
    PLAYER = "player"
    NEUTRAL = "neutral"      # Most monsters (orcs, trolls) - only attack player
    HOSTILE_ALL = "hostile_all"  # Slimes - attack everyone including other monsters
    # Future: UNDEAD, HUMANOID, BEAST, etc.
```

#### **Combat Targeting Priority**
```python
# Slime AI targeting priority:
1. Player (if visible and closer than other targets)
2. Other monsters (if visible and different faction)
3. Move toward closest valid target
4. Wander if no targets visible
```

#### **Entity Configuration**
```yaml
# entities.yaml additions
monsters:
  slime:
    name: "Slime"
    stats:
      hp: 15
      power: 2
      defense: 0
      xp: 25
      damage_min: 1
      damage_max: 3
    char: "s"
    color: [0, 255, 0]  # Green
    ai_type: "slime"
    faction: "hostile_all"
    special_abilities: ["corrosion"]
    can_seek_items: false  # Slimes don't pick up items
    inventory_size: 0
    
  large_slime:
    extends: "slime"
    name: "Large Slime"
    stats:
      hp: 40
      power: 4
      defense: 1
      xp: 75
      damage_min: 2
      damage_max: 5
    char: "S"
    color: [0, 200, 0]  # Darker green
    special_abilities: ["corrosion", "splitting"]
```

### **2. Equipment Corrosion Mechanics**

#### **Corrosion Application**
```python
# Applied after successful slime attacks
def apply_corrosion_effect(attacker, target, damage_dealt):
    if damage_dealt > 0 and attacker.faction == Faction.HOSTILE_ALL:
        # 5% chance per successful hit
        if random.random() < 0.05:
            corrode_equipment(attacker, target)

def corrode_equipment(attacker, target):
    """Apply corrosion to target's equipment."""
    results = []
    
    # Corrode weapon (when slime hits player/monster)
    if target.equipment and target.equipment.main_hand:
        weapon = target.equipment.main_hand
        if weapon.equippable and weapon.equippable.damage_max > weapon.equippable.damage_min:
            weapon.equippable.damage_max -= 1
            results.append({
                'message': Message(f'The {attacker.name} corrodes your {weapon.name}!', 
                                 color=(255, 165, 0))  # Orange warning
            })
    
    # Corrode armor (when player/monster hits slime)
    if attacker != target and target.equipment and target.equipment.off_hand:
        armor = target.equipment.off_hand
        if armor.equippable and armor.equippable.defense_max > armor.equippable.defense_min:
            armor.equippable.defense_max -= 1
            results.append({
                'message': Message(f'The {target.name}\'s {armor.name} is corroded by acid!', 
                                 color=(255, 165, 0))
            })
    
    return results
```

#### **Equipment Protection**
- **Minimum Values**: Corrosion cannot reduce stats below minimum values
- **Permanent Effect**: No repair system initially (future enhancement)
- **Strategic Gameplay**: Players may want to use backup equipment vs slimes

### **3. Large Slime Splitting Mechanics**

#### **Splitting Trigger**
```python
def handle_large_slime_death(large_slime, entities, game_map):
    """Handle Large Slime splitting into normal slimes on death."""
    results = []
    
    # Find adjacent empty tiles for spawning
    spawn_positions = []
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue  # Skip center position
            
            x, y = large_slime.x + dx, large_slime.y + dy
            if (0 <= x < game_map.width and 0 <= y < game_map.height and
                not game_map.tiles[x][y].blocked and
                not any(entity.x == x and entity.y == y and entity.blocks for entity in entities)):
                spawn_positions.append((x, y))
    
    # Spawn 2-3 normal slimes (or fewer if no space)
    spawn_count = min(3, len(spawn_positions))
    if spawn_count > 0:
        from config.entity_factory import EntityFactory
        entity_factory = EntityFactory()
        
        for i in range(spawn_count):
            x, y = spawn_positions[i]
            new_slime = entity_factory.create_monster("slime", x, y)
            entities.append(new_slime)
            
        results.append({
            'message': Message(f'The {large_slime.name} splits into {spawn_count} smaller slimes!', 
                             color=(0, 255, 0))
        })
    
    return results
```

### **4. Invisibility Scroll System**

#### **Status Effect Framework**
```python
class StatusEffect:
    """Base class for temporary status effects."""
    def __init__(self, name, duration, description):
        self.name = name
        self.duration = duration
        self.description = description
        self.owner = None
    
    def apply(self, entity):
        """Apply the status effect to an entity."""
        pass
    
    def tick(self):
        """Process one turn of the status effect."""
        self.duration -= 1
        return self.duration <= 0  # Return True if effect should be removed

class InvisibilityEffect(StatusEffect):
    """Invisibility status effect."""
    def __init__(self, duration=10):
        super().__init__("Invisible", duration, "Cannot be seen by most enemies")
        self.broken_by_attack = True
    
    def apply(self, entity):
        """Make entity invisible."""
        entity.invisible = True
    
    def remove(self, entity):
        """Remove invisibility."""
        entity.invisible = False
```

#### **Invisibility Scroll Implementation**
```python
# item_functions.py addition
def cast_invisibility(caster, **kwargs):
    """Cast invisibility spell on the caster."""
    results = []
    
    # Add invisibility status effect
    invisibility = InvisibilityEffect(duration=10)
    if not hasattr(caster, 'status_effects'):
        caster.status_effects = []
    
    caster.status_effects.append(invisibility)
    invisibility.apply(caster)
    
    results.append({
        'consumed': True,
        'message': Message(f'{caster.name} becomes invisible!', color=(200, 200, 255))
    })
    
    return results

# entities.yaml addition
spells:
  invisibility_scroll:
    name: "Invisibility Scroll"
    char: "?"
    color: [200, 200, 255]  # Light blue
    use_function: "cast_invisibility"
    targeting: false
    targeting_message: null
```

#### **AI Targeting Modifications**
```python
# Modified AI targeting in components/ai.py
def can_see_target(self, target, fov_map):
    """Check if this AI can see the target."""
    # Check basic FOV
    if not map_is_in_fov(fov_map, target.x, target.y):
        return False
    
    # Check invisibility
    if hasattr(target, 'invisible') and target.invisible:
        # Future: Some monsters might see through invisibility
        return False
    
    return True

def find_best_target(self, entities, fov_map):
    """Find the best target based on faction and proximity."""
    visible_targets = []
    
    for entity in entities:
        if (entity != self.owner and 
            entity.fighter and 
            self.can_see_target(entity, fov_map) and
            self.is_hostile_to(entity)):
            
            distance = self.owner.distance_to(entity)
            priority = self.get_target_priority(entity)
            visible_targets.append((entity, distance, priority))
    
    if not visible_targets:
        return None
    
    # Sort by priority (higher first), then by distance (closer first)
    visible_targets.sort(key=lambda x: (-x[2], x[1]))
    return visible_targets[0][0]

def is_hostile_to(self, target):
    """Check if this entity should attack the target based on factions."""
    if self.owner.faction == Faction.HOSTILE_ALL:
        # Slimes attack everyone except other slimes
        return target.faction != Faction.HOSTILE_ALL
    elif self.owner.faction == Faction.NEUTRAL:
        # Most monsters only attack player
        return target.faction == Faction.PLAYER
    
    return False

def get_target_priority(self, target):
    """Get targeting priority for different entity types."""
    if target.faction == Faction.PLAYER:
        return 10  # Highest priority
    else:
        return 5   # Lower priority for other monsters
```

### **5. Visual Effects**

#### **Invisibility Rendering**
```python
# render_functions.py modification
def draw_entity(con, entity, fov_map, game_map):
    """Draw an entity if it's in the player's FOV."""
    if map_is_in_fov(fov_map, entity.x, entity.y):
        # Check if entity is invisible (and is the player)
        if hasattr(entity, 'invisible') and entity.invisible and entity.name == "Player":
            # Render player as translucent when invisible
            translucent_color = tuple(c // 3 for c in entity.color)  # Much lighter
            libtcod.console_set_default_foreground(con, translucent_color)
        else:
            libtcod.console_set_default_foreground(con, entity.color)
        
        libtcod.console_put_char(con, entity.x, entity.y, entity.char, libtcod.BKGND_NONE)
```

## Implementation Plan

### **Phase 1: Core Framework (3-4 days)**
1. **Faction System**
   - Add faction enum and entity property
   - Update entity definitions in YAML
   - Modify AI targeting logic

2. **Status Effect System**
   - Create base StatusEffect class
   - Add status effect management to entities
   - Implement turn-based effect processing

### **Phase 2: Slime Mechanics (2-3 days)**
3. **Slime AI**
   - Create SlimeAI class with multi-target logic
   - Implement faction-based targeting
   - Add corrosion attack effects

4. **Equipment Corrosion**
   - Add corrosion methods to Equippable
   - Integrate with combat system
   - Add visual feedback messages

### **Phase 3: Advanced Features (2-3 days)**
5. **Large Slime Splitting**
   - Add splitting mechanics to death system
   - Implement spawn positioning logic
   - Add visual/audio feedback

6. **Invisibility System**
   - Create invisibility scroll and effect
   - Modify rendering for invisible entities
   - Add effect breaking on attack

### **Phase 4: Polish & Testing (1-2 days)**
7. **Integration Testing**
   - Test all interactions between systems
   - Balance tuning (corrosion rates, durations)
   - Performance optimization

## Technical Benefits

### **Extensibility**
- **Faction system** ready for future monster types
- **Status effect framework** supports buffs/debuffs
- **Equipment modification** system for future durability
- **Multi-target AI** enables complex encounters

### **Gameplay Impact**
- **Tactical depth**: Invisibility + monster positioning
- **Resource management**: Equipment preservation vs slimes  
- **Dynamic encounters**: Splitting creates escalating fights
- **Strategic choices**: When to use invisibility, which equipment to risk

## Future Extensions

### **Additional Factions**
```yaml
# Future faction possibilities
factions:
  undead: ["skeleton", "zombie", "lich"]
  humanoid: ["orc", "goblin", "bandit"]
  beast: ["wolf", "bear", "spider"]
  elemental: ["fire_elemental", "ice_elemental"]
```

### **Advanced Status Effects**
- **Poison**: Damage over time
- **Paralysis**: Skip turns
- **Haste**: Extra actions
- **Regeneration**: Heal over time

### **Equipment Durability System**
- **Repair mechanics**: Blacksmith NPCs, repair kits
- **Durability display**: Visual wear indicators
- **Quality tiers**: Different durability for item quality

This system provides a solid foundation for complex tactical gameplay while maintaining clean, extensible architecture for future enhancements.
