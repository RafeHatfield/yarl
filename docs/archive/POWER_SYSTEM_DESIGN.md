# Power System Design Documentation

## 🎯 **Power Model Philosophy**

### **Power = "Inherent Combat Ability"**
Power represents an entity's inherent combat prowess that can come from various sources, providing a flexible foundation for character differentiation and progression.

## 📊 **Current Implementation**

### **Baseline Model (v2.3.0)**
```yaml
# All entities start with power: 0 (baseline)
player:
  power: 0        # No inherent bonus
  damage_min: 3   # Fist damage: 3-4
  damage_max: 4   # Total unarmed: 0 + 3-4 = 3-4

orc:
  power: 0        # No inherent bonus  
  damage_min: 4   # Natural attack: 4-6
  damage_max: 6   # Total attack: 0 + 4-6 = 4-6
```

### **Enhancement Sources**
- **🧙‍♂️ Magical Enhancement** - Enchanted items, spell effects, magical scrolls
- **🏋️‍♂️ Natural Strength** - Barbarian's raw strength, orc chieftain's leadership/training
- **⚔️ Combat Training** - Veteran warrior's skill, elite monster variants
- **👑 Leadership/Status** - Boss monsters, elite units, experienced fighters
- **🧬 Racial/Species Traits** - Some creature types naturally stronger than others

## 🚀 **Future Implementation Patterns**

### **Player Classes**
```yaml
# Baseline human
player:
  power: 0
  damage_min: 3
  damage_max: 4
  # Total unarmed: 3-4

# Physical powerhouse
barbarian:
  power: 3        # Naturally stronger (+3 to all attacks)
  damage_min: 4   # Stronger fists
  damage_max: 5   # Total unarmed: 7-8 (3 power + 4-5 fists)
  hp: 120         # More health
  class_abilities:
    - "rage"      # Future: special abilities

# Magically weak but gets power from spells/items
wizard:
  power: 0        # Physically weak
  damage_min: 2   # Weak fists
  damage_max: 3   # Total unarmed: 2-3
  hp: 80          # Less health
  class_abilities:
    - "spell_mastery"  # Future: better with magical items

# Balanced fighter
warrior:
  power: 1        # Some training
  damage_min: 3   # Standard fists
  damage_max: 4   # Total unarmed: 4-5
  hp: 110         # Balanced health
  class_abilities:
    - "weapon_expertise"  # Future: better with weapons
```

### **Monster Variants with Inheritance**
```yaml
# Base monster template
orc:
  stats:
    hp: 20
    power: 0
    damage_min: 4
    damage_max: 6
  char: "o"
  color: [63, 127, 63]
  ai_type: "basic"

# Elite variant using inheritance
orc_chieftain:
  extends: orc              # Inherit all orc properties
  stats:
    hp: 35                  # Override: more health
    power: 2                # Override: leadership/training bonus
    xp: 75                  # Override: more XP reward
  char: "O"                 # Override: capital letter
  color: [127, 63, 63]      # Override: different color (red)
  name_suffix: "Chieftain"  # Display as "Orc Chieftain"
  # Inherits: damage_min: 4, damage_max: 6
  # Total damage: 2 power + 4-6 natural = 6-8

# Veteran variant
orc_veteran:
  extends: orc
  stats:
    hp: 25
    power: 1                # Some combat experience
    xp: 50
  name_suffix: "Veteran"
  # Total damage: 1 power + 4-6 natural = 5-7

# Magical variant
orc_shaman:
  extends: orc
  stats:
    hp: 18                  # Physically weaker
    power: 0                # No physical bonus
    defense: 1              # Magical protection
    xp: 60
  char: "s"
  color: [63, 63, 127]      # Blue (magical)
  ai_type: "spellcaster"    # Future: different AI
  equipment:
    - "magic_staff"         # Spawns with magical weapon
  spells:                   # Future: monster spells
    - "heal_self"
    - "magic_missile"
```

### **Weapon Progression with Power**
```yaml
# Physical weapons (replace natural damage)
iron_sword:
  damage_min: 5
  damage_max: 8
  power_bonus: 0            # Pure physical

# Magical weapons (add power bonus)
flame_sword:
  damage_min: 5             # Same physical damage
  damage_max: 8
  power_bonus: 2            # +2 magical fire damage
  # Total for barbarian: 5-8 weapon + 3 natural + 2 magical = 10-13

# Masterwork weapons (both better physical + magical)
legendary_blade:
  damage_min: 7             # Better craftsmanship
  damage_max: 12
  power_bonus: 3            # Legendary enchantment
  special_abilities:
    - "critical_strike"     # Future: special effects
```

### **Boss Monsters**
```yaml
# Dungeon boss using inheritance
troll_king:
  extends: troll
  stats:
    hp: 80                  # Much more health
    power: 4                # Royal strength/magic
    defense: 3              # Better armor
    xp: 500                 # Huge XP reward
  char: "K"
  color: [255, 215, 0]      # Gold
  ai_type: "boss"           # Future: special boss AI
  equipment:
    - "crown_of_power"      # Spawns with special items
    - "royal_armor"
  abilities:
    - "summon_minions"      # Future: boss abilities
    - "area_attack"
```

## 🎮 **Design Benefits**

### **1. Flexible Character Differentiation**
- **Barbarian**: High power, low magic affinity
- **Wizard**: Low power, high magic potential  
- **Warrior**: Balanced, weapon-focused

### **2. Easy Monster Variants**
- **Base Template**: Define core monster
- **Inheritance**: Create variants without duplication
- **Elite Versions**: Simple power/health increases

### **3. Clear Progression Paths**
- **Physical**: Better weapons (damage ranges)
- **Magical**: Power bonuses from items/spells
- **Hybrid**: Both weapon upgrades AND power increases

### **4. Intuitive Mental Model**
```
Total Damage = Weapon/Natural Damage + Power Bonus
             = Physical Component    + Enhancement
```

## 🔧 **Implementation Notes**

### **Inheritance System**
The `extends` keyword would:
1. **Copy all properties** from the base entity
2. **Override specified properties** in the variant
3. **Support nested inheritance** (orc_chieftain -> orc -> base_monster)
4. **Maintain clear hierarchy** for easy understanding

### **Power Sources Priority**
1. **Base Power** (racial/class)
2. **Equipment Power Bonus** (weapons, armor)
3. **Temporary Effects** (spells, potions)
4. **Special Abilities** (rage, berserk)

### **Future Extensions**
- **Conditional Power**: Barbarian rage (+5 power for 3 turns)
- **Situational Bonuses**: +1 power when below 25% health
- **Equipment Sets**: Matching armor provides power bonus
- **Environmental**: +2 power in home terrain

This system provides a solid foundation for rich character progression and monster variety while maintaining conceptual clarity and implementation simplicity.
