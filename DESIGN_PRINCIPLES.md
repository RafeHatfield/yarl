# Yarl: Design Principles

These principles guide all architectural and gameplay decisions in Yarl.

---

## 🎮 **Gameplay Design**

### 1. Meaningful Choices, Real Consequences
Every decision should matter. Whether it's:
- Equipment choices (what to equip)
- Portal placement (where to create shortcuts)
- Combat tactics (positioning, abilities)
- Dialogue options (different endings)

The game should reward clever thinking and punish carelessness.

### 2. Emergent Gameplay Over Scripted Moments
- Systems interact in unexpected ways (e.g., monsters using player-placed portals)
- AI behavior creates dynamic encounters
- Multiple valid solutions to problems
- Player agency and experimentation rewarded

### 3. Risk vs Reward
- Deeper dungeons have better loot but more danger
- Unique items are rare and valuable
- Resources are limited (potions, charges)
- Meaningful trade-offs: power vs survivability

### 4. Discovery & Surprise
- Hidden areas reward exploration
- NPCs have meaningful dialogue
- Easter eggs for attentive players
- Story unfolds through lore clues

---

## 🏗️ **Architecture Principles**

### 1. Single Source of Truth
Each system should have ONE place where it's defined:
- PortalManager handles all portal logic (not scattered across files)
- AISystem is the decision point for all monster actions
- EntityFactory is the creation point for all entities

**Benefit:** Easy to maintain, understand, and extend.

### 2. Component-Based Design
- Entities are collections of components
- Each component has one responsibility
- Systems operate on components, not entities directly
- Easy to mix-and-match behaviors

**Example:** Any entity with a `Fighter` component can combat. Any entity with `Portal` component can teleport.

### 3. Clear Integration Points
- Define where systems interact (collision detection, item usage)
- Minimize coupling between systems
- Use message passing where possible
- Document dependencies

### 4. Test-Driven Architecture
- Systems must be testable in isolation
- Mock objects for external dependencies
- Comprehensive test coverage (90%+)
- Integration tests for complex flows

**Current Status:** 2500+ tests passing, 100% critical path coverage

---

## 🎨 **Code Quality**

### 1. Readable Over Clever
- Clear variable names over abbreviated code
- Explicit logic over implicit behavior
- Comments for "why", not "what"
- Consistent style throughout

### 2. Fail-Fast & Explicit Errors
- Validate inputs early
- Clear error messages
- Crash on bad data (don't silently ignore)
- Logging at appropriate levels

### 3. DRY Principle (Don't Repeat Yourself)
- Extract common logic into utilities
- Reuse components across different entities
- Avoid duplicate code paths

### 4. Backward Compatibility
- Don't break existing features
- Deprecate carefully with warnings
- All existing tests must pass
- Refactoring shouldn't change behavior

---

## 🎯 **Gameplay Experience**

### 1. Clarity Over Complexity
- Visual feedback for all important actions
- Messages explain what happened and why
- UI is intuitive and responsive
- Player always knows the game state

### 2. Accessibility
- Roguelike difficulty is the game challenge (not controls)
- Clear color differentiation for important elements
- Consistent input handling (keyboard/mouse)
- Readable fonts and UI elements

### 3. Satisfying Feedback
- Combat shows damage clearly
- Items have visual feedback when used
- Monster deaths are visible
- Spell effects are obvious

### 4. Balanced Difficulty
- Early game teaches mechanics
- Mid-game is challenging but fair
- Late game rewards mastery
- Multiple viable build strategies

---

## 🔄 **Development Process**

### 1. Phases Over Continuous Development
- Complete phases with clear objectives
- Each phase is fully tested and playable
- Clean handoff between sessions
- Documentation updated per phase

### 2. Playtesting Drives Decisions
- Features tested before expansion
- Player feedback incorporated
- Balance issues addressed quickly
- Emergent gameplay celebrated

### 3. Technical Debt is Tracked
- Refactoring is explicit work (not ignored)
- Architecture reviews for large features
- Old code is progressively improved
- Legacy systems eventually replaced

### 4. Documentation is Living
- Updated with each major change
- Strategic docs in root for easy access
- Development notes in docs/ folder
- Code comments for complex logic

---

## 🚀 **Release Quality**

### 1. No Known Critical Bugs
- All reported bugs are addressed
- Regression tests prevent reoccurrence
- Edge cases are covered
- Crash-free gameplay required

### 2. Performance Acceptable
- 60 FPS target (achieved)
- Sub-50ms input response (achieved)
- Rendering optimized with caching
- Memory usage reasonable

### 3. All Features Working
- No half-implemented features in release
- All promised functionality present
- Test coverage 90%+
- Documentation complete

### 4. Extensible Foundation
- New features should be easy to add
- Systems should be modular
- Architecture should scale
- Code should be maintainable

---

## 🎓 **Examples in Action**

### Single Source of Truth
**Good:**
```
PortalManager.check_portal_collision(entity, entities)
// All portal teleportation happens here
```

**Bad:**
```
// Portal checks scattered in:
// - MovementService.py
// - AISystem.py
// - CombatSystem.py
// (Inconsistent behavior)
```

### Emergent Gameplay
**Example:** Monster picks up player-placed portal
- Game doesn't explicitly handle this
- But monster inventory system works
- Item drop system works
- Portal mechanics work
- Result: Unexpected, exciting, logical interaction

### Clear Feedback
**Good:**
```
Message: "✨ Evil Orc shimmers and vanishes!"
Effect: Monster teleports
Result: Player understands what happened
```

**Bad:**
```
// Silent teleportation
// Player confused where monster went
```

---

## 📊 **Current Status**

These principles are actively applied to:
- ✅ Portal System (Phase A & B complete)
- ✅ Victory Condition (Phase 5 complete)
- ✅ Environmental Lore (Phase 4 complete)
- ✅ Core Combat & Movement
- ⏳ Future phases will follow same principles

---

## 🔮 **Future Enhancements**

As new features are added, these principles will ensure:
- Consistent quality and complexity
- Emergent interactions between systems
- Clean, maintainable code
- Great player experience

---

**Last Updated:** Portal System Phase B Complete (91 tests passing)

**Philosophy:** Build systems that are simple, clear, and powerful. Let emergent gameplay create complexity, not the code.

