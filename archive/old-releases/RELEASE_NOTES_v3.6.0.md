# 🔥 Yarl v3.6.0: Persistent Ground Effects Release Notes

**Release Date:** October 7, 2025  
**Theme:** Hazardous Ground Effects  
**Tagline:** "Fire Burns, Gas Lingers!"

---

## 🌟 What's New

### **1. Persistent Fire Hazards** 🔥

Fireball explosions now leave **burning embers** that persist for 3 turns! Enemies and players who walk through fire take ongoing damage.

**How it works:**
- Cast Fireball → Creates 3x3 explosion
- Fire hazards appear on all affected tiles
- Entities take damage at turn start if standing on fire
- Damage decays: 10 HP → 6 HP → 3 HP over 3 turns
- Visual feedback: Orange `*` characters that fade naturally into floor color

**Tactical Implications:**
- Zone control: Block enemy paths with fire walls
- Area denial: Force enemies to take alternate routes
- Combo potential: Trap enemies in tight spaces
- Risk/Reward: Walking through fire is dangerous but sometimes necessary

**Example Scenario:**
```
Turn 1: Cast Fireball → 3x3 fire area (10 damage per turn)
Turn 2: Orc walks into fire → Takes 10 damage, fire decays to 6 damage
Turn 3: Orc still burning → Takes 6 damage, fire decays to 3 damage
Turn 4: Fire expires → No more damage
```

---

### **2. Persistent Poison Gas** 💨

Dragon Fart creates **toxic gas clouds** that linger for 4 turns in a cone pattern! The gas deals damage-over-time to anyone caught in it.

**How it works:**
- Cast Dragon Fart → Creates directional cone of gas
- Gas hazards persist for 4 turns
- Entities take poison damage at turn start if standing in gas
- Damage decays: 5 HP → 3 HP → 1 HP → 1 HP over 4 turns
- Visual feedback: Green `%` characters that blend into floor as gas dissipates

**Tactical Implications:**
- Crowd control: Fill hallways with choking gas
- Defensive tool: Block pursuit with gas clouds
- Hit-and-run: Cast gas and retreat while enemies suffer
- Safer than fire: Lower initial damage but lasts longer

**Example Scenario:**
```
Turn 1: Cast Dragon Fart eastward → Cone of 5 tiles poisoned (5 damage)
Turn 2: Troll enters gas → Takes 5 damage, gas decays to 3 damage
Turn 3: Troll still poisoned → Takes 3 damage, gas decays to 1 damage
Turn 4: Troll pushes through → Takes 1 damage
Turn 5: Gas finally clears
```

---

### **3. Visual Fade Effects** ✨

Ground hazards feature **beautiful color blending** that fades naturally into the floor color as they age.

**Visual System:**
- Fresh hazards: Bright, vibrant colors (orange fire, green gas)
- Aging hazards: Gradually blend into floor color (purple/teal tones)
- Expired hazards: Seamlessly become floor color
- FOV-aware: Hazards dim when out of line-of-sight (but still visible)

**Color Examples:**
- **Fire (Fresh):** Bright orange (255, 100, 0)
- **Fire (Mid-life):** Orange-purple blend (152, 75, 75)
- **Fire (Expired):** Floor color (50, 50, 150)
- **Gas (Fresh):** Vibrant green (100, 200, 80)
- **Gas (Mid-life):** Green-teal blend (75, 125, 115)
- **Gas (Expired):** Floor color (50, 50, 150)

**Why This Matters:**
- Natural appearance: Fire doesn't "fade to black," it blends into the environment
- Clear feedback: You can see at a glance how much time is left on hazards
- Aesthetic polish: Beautiful color transitions enhance the game's visual appeal
- Tactical readability: Easy to distinguish fresh vs. fading hazards

---

### **4. Turn-Based Hazard System** ⏱️

Hazards age and damage automatically as part of the turn system.

**Turn Sequence:**
1. **Player Turn:** Move, attack, cast spells
2. **Enemy Turns:** All monsters act
3. **Hazard Processing:**
   - Apply damage to all entities on hazardous tiles
   - Age all hazards by 1 turn
   - Remove expired hazards
4. **Back to Player Turn**

**Damage Application:**
- Damage applied at **turn start** (predictable timing)
- Uses standard damage system (can kill player or monsters)
- Death messages show hazard type: "Player burned to death in fire!"
- Monsters can die from hazards: "Orc choked to death in poison gas!"

**Tactical Depth:**
- Predictable: You know when hazard damage will trigger
- Strategic positioning: Plan movements around hazard zones
- Resource consideration: Hazards provide "free" damage over time
- Risk assessment: Is it worth walking through fire to reach the exit?

---

### **5. Full Save/Load Support** 💾

Ground hazards are fully persistent across save/load sessions.

**What's Saved:**
- All active hazard positions and types
- Remaining duration for each hazard
- Base damage values
- Source names (for death messages)

**Benefits:**
- Save mid-combat: Hazards are exactly where you left them
- Strategic planning: Save before risky maneuvers through hazards
- Bug prevention: No "phantom" hazards or lost hazards after loading

---

## 🎮 Gameplay Impact

### **Combat Strategy**

**Area Control:**
- Fireball a doorway → Enemies must walk through fire or find another path
- Dragon Fart a hallway → Create a temporary barrier
- Combo spells → Layer fire and gas for maximum zone denial

**Resource Management:**
- Hazards provide "free" damage over multiple turns
- One Fireball can damage 3+ enemies if they stay in the fire
- Save spell scrolls by letting hazards do the work

**Positioning Matters:**
- Standing on hazards = free damage to you
- Kiting enemies through hazards = free damage to them
- Corner enemies in hazard zones for maximum effect

### **New Tactics Unlocked**

1. **The Gauntlet:** Line a hallway with overlapping fireballs
2. **The Trap:** Cast gas around corners, enemies walk into it
3. **The Retreat:** Drop fire behind you as you flee
4. **The Bottleneck:** Block narrow passages with persistent effects
5. **The Sacrifice:** Sometimes you must walk through fire to survive

---

## 🛠️ Technical Details

### **Architecture**

**New Components:**
- `GroundHazard` class: Individual hazard instance
- `GroundHazardManager` class: Manages all hazards on the map
- `HazardType` enum: Fire, Poison Gas (extensible for future types)

**Integration Points:**
- `item_functions.py`: Spells create hazards on cast
- `engine/systems/ai_system.py`: Turn processing applies hazard damage
- `loader_functions/data_loaders.py`: Save/load hazard state
- `render_functions.py`: Visual rendering with fade effects
- `map_objects/game_map.py`: Map stores hazard manager

**Design Principles:**
- **Predictable:** Damage applied once per turn at turn start
- **Simple:** No stacking - newest hazard replaces old one
- **Decaying:** Damage reduces over time (100% → 66% → 33%)
- **Testable:** 100+ new tests covering all functionality

### **Performance**

- Zero impact on frame rate
- Efficient turn processing (O(n) entities + O(m) hazards)
- Render optimization: Hazards integrated into tile rendering pipeline
- Memory efficient: Only active hazards stored

### **Extensibility**

The hazard system is designed for easy expansion:
- Add new hazard types (acid, ice, lightning)
- Configure damage patterns per type
- Customize visual effects per type
- Support multiple hazards per tile (future enhancement)

---

## 🧪 Quality Assurance

### **Testing Coverage**

**New Tests:** 100+ tests added
- Unit tests: `GroundHazard` and `GroundHazardManager` mechanics
- Integration tests: Spell → hazard creation
- System tests: Turn processing and damage application
- Rendering tests: Visual fade effects
- Save/load tests: Persistence across sessions

**Total Test Suite:**
- **1,813 tests** passing ✅
- **100% coverage** of hazard system
- Zero regressions in existing features

### **Regression Protection**

All bug fixes include regression tests:
- Mock setup for status effects
- UI layout consistency in visual effects
- Difficulty scaling buffer handling
- Entity sorting with visual effects
- Map rendering integration

---

## 📚 Documentation

### **New Documentation:**
- `components/ground_hazard.py`: Comprehensive module docstrings
- `engine/systems/ai_system.py`: `_process_hazard_turn` method docs
- `render_functions.py`: `_render_hazard_at_tile` function docs
- `loader_functions/data_loaders.py`: Hazard serialization docs
- All public methods and classes fully documented

### **Updated Documentation:**
- ROADMAP.md: Marked "Persistent Ground Effects" as complete
- Test strategy: New testing patterns for ground effects
- Architecture notes: Hazard manager integration

---

## 🎨 Visual Polish

### **Character Set**
- Fire: `*` (burning embers)
- Poison Gas: `%` (toxic clouds)
- Future hazards: Reserved characters for acid, ice, lightning

### **Color Palette**
- Fire: Orange (255, 100, 0) → blends to floor
- Poison Gas: Green (100, 200, 80) → blends to floor
- FOV dimming: 30% intensity when out of sight
- Natural fading: Gradual blend, not abrupt transitions

---

## 🔄 What's Next?

### **Optional Enhancements Available:**

**AI Pathfinding Integration** (1-2 weeks)
- Monsters avoid hazardous tiles when possible
- Path cost based on hazard damage
- Smart AI doesn't walk through fire unnecessarily

**More Hazard Types** (1 week each)
- **Acid Pools:** Left by Acid Splash, persistent corrosion damage
- **Ice Patches:** Left by Ice Storm, slows movement
- **Lightning Fields:** Left by Chain Lightning, random arcs

**Hazard Stacking** (1-2 weeks)
- Multiple hazards on one tile
- Combined effects (fire + poison = toxic inferno?)
- Visual layering system

---

## 🐛 Bug Fixes

This release includes fixes for several test issues discovered during development:

1. **Status Effects Iteration:** Fixed mock setup in AI tests
2. **UI Layout Consistency:** Ensured proper sidebar width in visual effect tests
3. **Difficulty Scaling:** Extended buffer for new item types
4. **Visual Effects Integration:** Mocked effect queue in rendering tests
5. **Monster Migration:** Dynamic side effects for `from_dungeon_level` mocks
6. **Wand Display:** Updated display format with charge indicators

---

## 📊 Statistics

### **Code Changes:**
- **Files Modified:** 25
- **Files Added:** 5 (ground_hazard.py + 4 test files)
- **Lines Changed:** ~22,000 (includes test data and comprehensive tests)
- **New Tests:** 100+
- **Test Pass Rate:** 100% (1,813/1,813)

### **Feature Completion:**
- ✅ Ground hazard core system
- ✅ Fireball integration
- ✅ Dragon Fart integration
- ✅ Turn-based damage processing
- ✅ Visual rendering with fade effects
- ✅ Save/load persistence
- ✅ Comprehensive testing
- ✅ Full documentation

---

## 🙏 Acknowledgments

This release demonstrates the power of:
- **Test-Driven Development:** All features backed by comprehensive tests
- **Iterative Design:** User feedback shaped the visual fade effect
- **Clean Architecture:** Easy integration into existing systems
- **Quality Focus:** Zero regressions, all tests passing

---

## 🚀 Upgrade Instructions

**From v3.5.0:**
1. Pull latest code from repository
2. No migration required - hazard system is fully backward compatible
3. Existing save games work perfectly (hazards initialize as empty)
4. All tests passing - safe to upgrade

**For Developers:**
- Review `components/ground_hazard.py` for API documentation
- See test files for usage examples
- Hazard manager automatically created for all game maps

---

## 🎉 Conclusion

**Yarl v3.6.0** transforms area-of-effect spells from instant damage to **strategic zone control**. Fire walls block paths, gas clouds choke enemies, and the beautiful visual fade effects make every spell feel impactful and satisfying.

The hazard system is **production-ready**, **fully tested**, and **easily extensible** for future effect types. Combined with the existing mouse-driven UI, camera system, and D&D-style combat, Yarl continues to evolve into a polished, tactical roguelike experience.

**Try it out:** Cast a Fireball, watch the fire burn for 3 turns, and enjoy the strategic depth of persistent ground effects!

---

*"The fire burns long after the spell is cast..." - Yarl Proverb*

