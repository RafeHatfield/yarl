# Manual Level Design System

## Overview

The Manual Level Design system allows developers to create hand-crafted, story-driven levels that can be mixed with procedurally generated content. This enables special encounters like orc villages, boss lairs, puzzle rooms, and narrative set pieces.

## Core Concept

- **Most levels remain procedural** - maintains replayability and exploration
- **Special levels at key points** - adds memorable encounters and story beats
- **Template-based system** - reusable patterns with customization
- **Conditional spawning** - levels appear based on game state, player level, or story progression

## Feature Specification

### **Level Templates**

#### **Template Definition Format (YAML)**
```yaml
# Example: Orc Village Template
level_templates:
  orc_village:
    name: "Orc Village"
    description: "A fortified orc settlement with multiple chambers"
    
    # When this level can appear
    conditions:
      dungeon_levels: [3, 4, 5]  # Can appear on these levels
      probability: 0.3           # 30% chance when conditions met
      max_occurrences: 1         # Only once per game
      
    # Level layout definition
    layout:
      width: 25
      height: 20
      rooms:
        - id: "entrance"
          position: [2, 2]
          size: [6, 4]
          connections: ["main_hall"]
          
        - id: "main_hall" 
          position: [10, 5]
          size: [8, 6]
          connections: ["entrance", "chieftain_chamber"]
          
        - id: "chieftain_chamber"
          position: [15, 12]
          size: [7, 6]
          connections: ["main_hall"]
          
    # Entity spawning rules
    spawns:
      entrance:
        entities:
          - type: "orc"
            count: 2
            positions: "random"  # or specific coordinates
            
      main_hall:
        entities:
          - type: "orc"
            count: 3
            equipment: ["sword", "shield"]
            
      chieftain_chamber:
        entities:
          - type: "orc_chieftain"  # Uses entity inheritance system
            count: 1
            position: [4, 3]  # Specific position in room
            equipment: ["chieftain_sword", "chieftain_armor"]
            
        items:
          - type: "treasure_chest"
            contents: ["gold", "enhancement_scroll", "rare_weapon"]
            
    # Environmental features
    features:
      - type: "campfire"
        room: "main_hall"
        position: [4, 3]
        
      - type: "throne"
        room: "chieftain_chamber" 
        position: [4, 5]
```

### **Level Generation Integration**

#### **Modified Map Generation Flow**
```python
def generate_level(dungeon_level, player_state):
    # Check for special level conditions
    special_level = check_special_level_conditions(dungeon_level, player_state)
    
    if special_level:
        return generate_template_level(special_level)
    else:
        return generate_procedural_level(dungeon_level)  # Existing system
```

#### **Template Level Generator**
```python
class TemplateLevelGenerator:
    def generate_from_template(self, template_id):
        template = load_level_template(template_id)
        
        # Create base map structure
        game_map = create_template_map(template.layout)
        
        # Generate rooms and connections
        for room in template.layout.rooms:
            create_room(game_map, room)
            connect_rooms(game_map, room.connections)
            
        # Spawn entities according to template
        entities = spawn_template_entities(template.spawns)
        
        # Add environmental features
        add_template_features(game_map, template.features)
        
        return game_map, entities
```

### **Advanced Features**

#### **Conditional Spawning**
- **Story progression**: "Orc village only after defeating first boss"
- **Player level**: "Dragon lair only at level 10+"
- **Previous choices**: "Peaceful village if player spared orc chief"
- **Random events**: "Merchant caravan has 5% chance to appear"

#### **Dynamic Templates**
- **Variable room sizes**: Rooms can have min/max size ranges
- **Optional rooms**: Some rooms only appear under certain conditions
- **Scalable encounters**: Entity counts scale with player level
- **Randomized layouts**: Multiple layout variants per template

#### **Entity Inheritance Integration**
```yaml
# Uses the entity inheritance system for variants
entities:
  orc_chieftain:
    extends: "orc"
    name: "Orc Chieftain"
    stats:
      hp: 40      # Override base orc HP
      power: 8    # Stronger than regular orcs
    equipment_slots:
      main_hand: "chieftain_sword"
      off_hand: "chieftain_shield"
```

## Implementation Plan

### **Phase 1: Core Infrastructure (2-3 weeks)**
1. **Template Loading System**
   - YAML template parser
   - Template validation and error handling
   - Template registry and caching

2. **Basic Level Generation**
   - Room-based template generation
   - Simple entity spawning
   - Integration with existing map generation

### **Phase 2: Advanced Features (2-3 weeks)**
1. **Conditional System**
   - Condition evaluation engine
   - Game state tracking for conditions
   - Probability and occurrence limiting

2. **Enhanced Spawning**
   - Equipment assignment system
   - Position-based spawning
   - Environmental feature placement

### **Phase 3: Polish & Tools (1-2 weeks)**
1. **Template Editor** (Optional)
   - Visual template creation tool
   - Template testing and validation
   - Export to YAML format

2. **Documentation & Examples**
   - Template creation guide
   - Example templates for common scenarios
   - Integration documentation

## Example Use Cases

### **Story Encounters**
- **Orc Village**: Multi-room settlement with chief and treasure
- **Dragon Lair**: Boss encounter with environmental hazards
- **Abandoned Temple**: Puzzle rooms with hidden passages
- **Merchant Camp**: Safe zone with trading opportunities

### **Gameplay Variety**
- **Arena Rooms**: Combat challenges with waves of enemies
- **Treasure Vaults**: High-security areas with valuable loot
- **Trap Galleries**: Skill-based navigation challenges
- **Portal Chambers**: Transportation between distant areas

### **Narrative Elements**
- **Throne Rooms**: Important story encounters
- **Libraries**: Lore and spell learning locations
- **Workshops**: Equipment crafting and enhancement
- **Sanctuaries**: Healing and rest areas

## Technical Benefits

### **For Developers**
- **Rapid prototyping**: Quick creation of special encounters
- **Story integration**: Seamless narrative moment creation
- **Reusable content**: Templates can be adapted and reused
- **Easy balancing**: Centralized encounter tuning

### **For Players**
- **Memorable encounters**: Hand-crafted moments break up procedural exploration
- **Story progression**: Clear narrative beats and objectives
- **Variety**: Mix of procedural and designed content
- **Replayability**: Templates can have variations and conditions

## Future Extensions

### **Advanced Template Features**
- **Multi-level templates**: Templates spanning multiple floors
- **Branching paths**: Player choices affect template progression
- **Dynamic events**: Templates that change based on player actions
- **Procedural elements**: Templates with procedural sub-components

### **Community Content**
- **Template sharing**: Community-created templates
- **Mod support**: External template loading
- **Template marketplace**: Curated community content
- **Creation tools**: User-friendly template editors

This system provides a powerful foundation for creating memorable, hand-crafted experiences while maintaining the core procedural nature that makes roguelikes endlessly replayable.
