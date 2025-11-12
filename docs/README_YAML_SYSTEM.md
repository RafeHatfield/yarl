# YAML Room Generation System - Documentation Index

## 📚 Complete Documentation Set

We've created a **comprehensive documentation suite** for the YAML room generation system. Use these guides to design dungeons without touching Python code.

---

## 📖 Documentation Files

### 1. **Quick Reference** (Start Here!)
**File:** `docs/YAML_ROOM_GENERATION_QUICK_REFERENCE.md`
- **Length:** ~5 minutes to read
- **What:** Syntax cheat sheet, common patterns, entity types
- **Best for:** Quick lookup during design
- **Contains:**
  - 30-second overview
  - Syntax cheat sheet
  - 4 common patterns
  - Entity type list
  - Common mistakes
  - Troubleshooting checklist

**→ Start here if you just want to make changes fast**

---

### 2. **Complete Guide** (Comprehensive Reference)
**File:** `docs/YAML_ROOM_GENERATION_SYSTEM.md`
- **Length:** ~30-40 minutes to read thoroughly
- **What:** Full documentation of every feature
- **Best for:** Understanding the system deeply
- **Contains:**
  - System overview (Tier 1 & 2)
  - YAML file structure
  - Core concepts (level numbers, entity types, count values, modes)
  - Tier 1 details (Guaranteed Spawns)
  - Tier 2 details (Level Parameters & Special Rooms)
  - **Tier 2 details (Door Rules)** - Locked/secret corridors
  - **Tier 2 details (Secret Rooms)** - Hidden chambers with hints
  - **Tier 2 details (Trap Rules)** - Hazardous traps with detection
  - **Tier 2 details (Stairs Configuration)** - Level transitions and floor persistence
  - **Tier 2 details (Connectivity Configuration)** - MST pathfinding and corridor styles
  - Configuration files explanation
  - How to use step-by-step
  - 5 complete examples
  - 10 future growth opportunities
  - Implementation checklist
  - FAQ

**→ Read this to understand how everything works**

---

### 3. **Design Patterns & Troubleshooting** (Advanced)
**File:** `docs/YAML_ROOM_GENERATION_DESIGN_PATTERNS.md`
- **Length:** ~15-20 minutes to read
- **What:** Design patterns, troubleshooting, level design philosophy
- **Best for:** Creating better-designed levels, fixing problems
- **Contains:**
  - 6 design patterns with full examples:
    1. Difficulty Curve (classic progression)
    2. Milestone Levels (bosses every 5 levels)
    3. Faction Encounters (mixed opposition)
    4. Resource Management (scarce items)
    5. Testing Showcase (verification level)
    6. Asymmetric Difficulty (easy & hard paths)
  - Troubleshooting guide (5 common issues with fixes)
  - Performance considerations
  - Advanced techniques
  - Level design philosophy
  - Checklist for good design

**→ Read this when you want to design better levels**

---

## 🎯 Quick Start

### For First-Time Users

1. Read: `YAML_ROOM_GENERATION_QUICK_REFERENCE.md` (5 mins)
2. Copy: A pattern from `config/level_templates_examples.yaml`
3. Modify: For your level
4. Test: `python3 engine.py --testing --start-level <N>`
5. Iterate: Adjust based on gameplay feel

### For Understanding Deeply

1. Read: `YAML_ROOM_GENERATION_SYSTEM.md` (full guide)
2. Study: Examples section (5 examples provided)
3. Explore: `config/level_templates_examples.yaml` (reference configs)
4. Practice: Design 3 levels using patterns
5. Reference: Consult `YAML_ROOM_GENERATION_DESIGN_PATTERNS.md` as needed

### For Problem Solving

1. Check: `YAML_ROOM_GENERATION_QUICK_REFERENCE.md` Common Mistakes section
2. Search: `YAML_ROOM_GENERATION_DESIGN_PATTERNS.md` Troubleshooting section
3. Debug: Run test level with debug logging
4. Refer: Full guide for detailed explanations

---

## 🗂️ Configuration Files

These YAML files are where you actually make changes:

```
config/
├── level_templates.yaml           # ← Normal gameplay configs (EDIT THIS)
├── level_templates_testing.yaml   # ← Testing configs (override normal)
└── level_templates_examples.yaml  # ← Copy-paste examples (reference only)
```

### File Purposes

| File | Purpose | When to Use |
|------|---------|------------|
| `level_templates.yaml` | Main configuration | Production levels |
| `level_templates_testing.yaml` | Testing overrides | Testing mode |
| `level_templates_examples.yaml` | Reference only | Copy patterns from here |

---

## 🎮 Example Workflow

### Scenario: Design Level 13

```
1. Read Quick Reference
   └─ Understand syntax (5 mins)

2. Look at Examples
   └─ Find similar level pattern (2 mins)

3. Copy Template
   └─ Copy level 12 example to level 13 (1 min)

4. Modify Parameters
   └─ Change max_monsters_per_room to 4 (1 min)

5. Add Special Room
   └─ Add boss room if needed (2 mins)

6. Test
   └─ python3 engine.py --testing --start-level 13 (30 secs)

7. Play & Adjust
   └─ Iterate based on gameplay (5-10 mins)

8. Done!
   └─ Move to level_templates.yaml when happy (1 min)

TOTAL TIME: ~20 minutes for a complete level design
```

---

## 📚 Structure of the System

The system has **two tiers of customization**:

### Tier 1: Guaranteed Spawns
**What:** What monsters, items, and equipment appear

```yaml
guaranteed_spawns:
  mode: "additional"  # or "replace"
  monsters:
    - type: "orc"
      count: "2-4"
  items:
    - type: "healing_potion"
      count: 2
  equipment:
    - type: "sword"
      count: 1
```

**Use:** Add specific content to levels

### Tier 2: Generation & Rooms
**What:** How rooms are generated and themed

```yaml
parameters:
  max_monsters_per_room: 4  # Difficulty
  max_rooms: 15             # Complexity

special_rooms:
  - type: "boss_chamber"
    count: 1
    placement: "largest"
    guaranteed_spawns: {...}
```

**Use:** Control level architecture and theme

---

## 🔑 Key Concepts

### Count Syntax
- `count: 5` = Always 5
- `count: "3-8"` = Random 3-8

### Modes
- `"additional"` = Add to random content (normal gameplay)
- `"replace"` = Only this content (testing)

### Placement
- `"random"` = Any room
- `"largest"` = Biggest room(s)
- `"smallest"` = Smallest room(s)

### Parameters
- `max_rooms` = Level complexity (8-20)
- `min/max_room_size` = Room dimensions (6-14)
- `max_monsters_per_room` = Difficulty (1-6)
- `max_items_per_room` = Loot density (1-3)

---

## 🐛 Troubleshooting Quick Links

| Problem | Where to Look |
|---------|---------------|
| "Entities not spawning" | Quick Ref: Common Mistakes |
| "Room too small" | Design Patterns: Troubleshooting |
| "Level too hard/easy" | Design Patterns: Issue 3 |
| "Yaml syntax error" | Quick Ref: Syntax Cheat Sheet |
| "Entity type invalid" | Quick Ref: Entity Types |
| "Special room not working" | Design Patterns: Troubleshooting |

---

## 🚀 Getting Started

### Minimum Viable Level

```yaml
# Bare minimum config
level_overrides:
  13:
    guaranteed_spawns:
      mode: "additional"
      items:
        - type: "healing_potion"
          count: 1
```

**Result:** Level 13 now always has 1 healing potion

### Full Featured Level

```yaml
# Complete level config
13:
  parameters:
    max_monsters_per_room: 4
    max_rooms: 15
  
  guaranteed_spawns:
    mode: "additional"
    items:
      - type: "healing_potion"
        count: 2
  
  special_rooms:
    - type: "boss_chamber"
      count: 1
      placement: "largest"
      guaranteed_spawns:
        monsters:
          - type: "troll"
            count: 1
```

**Result:** Complex level with boss room and extra healing

---

## 📊 System Statistics

```
Configuration Options:
  - Levels supported: 25 (1-25)
  - Tier 1 features: 4 (monsters, items, equipment, map features)
  - Tier 2 features: 2 (parameters, special rooms)
  - Parameters: 8 customizable
  - Placement strategies: 3
  - Count formats: 2 (fixed, range)
  - Modes: 2 ("additional", "replace")
  
Supported Entities: 50+
  - Monsters: 15+
  - Items: 20+
  - Equipment: 10+
  - Map Features: 5+

Documentation:
  - Total pages: 3 guides + examples
  - Total content: ~20,000 words
  - Examples: 10+ complete configs
  - Patterns: 6 design patterns
  - FAQ: 10 common questions
```

---

## 🎓 Learning Path

### Day 1: Basics
- [ ] Read Quick Reference (5 mins)
- [ ] Copy one example (5 mins)
- [ ] Test it (2 mins)
- [ ] Modify parameters slightly (5 mins)
- [ ] Test again (2 mins)
- **Total: 20 minutes → You can now modify levels!**

### Day 2: Competence
- [ ] Read design patterns (15 mins)
- [ ] Design 2-3 levels from scratch (30 mins)
- [ ] Test and iterate (20 mins)
- **Total: 65 minutes → You're proficient**

### Day 3+: Mastery
- [ ] Study full guide (30 mins)
- [ ] Design 5+ levels (ongoing)
- [ ] Create custom patterns (ongoing)
- **Total: Continuous improvement**

---

## 🎯 Next Steps

1. **Pick a level (1-25)**
   - Good choices: 1 (tutorial), 10 (boss), 25 (final)

2. **Read Quick Reference**
   - Just the Syntax Cheat Sheet section

3. **Find similar level in examples**
   - Use `level_templates_examples.yaml`

4. **Copy and modify**
   - Change entity types and counts

5. **Test in game**
   - `python3 engine.py --testing --start-level <N>`

6. **Iterate**
   - Adjust difficulty until it feels right

7. **Share!**
   - Commit to git when happy

---

## 📞 FAQ

**Q: How long does it take to design a level?**
A: 15-30 minutes once you're comfortable. First level takes ~45 minutes.

**Q: Can I break something?**
A: No. Worst case, the level doesn't load and you'll see an error. Just fix the YAML.

**Q: Do I need to know Python?**
A: No! This is pure YAML configuration.

**Q: How do I test changes?**
A: Use `python3 engine.py --testing --start-level 13`

**Q: Where are all the entity types?**
A: Check `config/entities.yaml` for the full list.

---

## 🏆 You're Ready!

You now have everything you need to:
- ✅ Understand room generation
- ✅ Modify existing levels
- ✅ Design new levels
- ✅ Create themed encounters
- ✅ Scale difficulty
- ✅ Test configurations

**Go make awesome dungeons!** 🎮

---

## 📎 Quick Links

| What | Where |
|------|-------|
| Syntax | `YAML_ROOM_GENERATION_QUICK_REFERENCE.md` |
| Full Guide | `YAML_ROOM_GENERATION_SYSTEM.md` |
| Patterns | `YAML_ROOM_GENERATION_DESIGN_PATTERNS.md` |
| Examples | `config/level_templates_examples.yaml` |
| Main Config | `config/level_templates.yaml` |
| Testing Config | `config/level_templates_testing.yaml` |

---

**Made with 💚 for roguelike designers everywhere**

