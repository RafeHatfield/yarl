# 🌀 Portal System - Phase B: Advanced Mechanics

**Status:** Ready to implement  
**Timeline:** 2-3 days  
**Goals:** Monster integration, terrain blocking, combat bonuses  
**Tests:** 10+ comprehensive tests  

---

## 🎯 Phase B Overview

Phase A gave us a working portal system. Phase B makes it **intelligent** and **interactive**:

### What Phase B Adds
1. **Terrain Blocking** - Portals can't be placed on water, lava, walls
2. **Monster Portal Usage** - Monsters can navigate through portals (emergent gameplay!)
3. **Combat Bonuses** - Teleport behind an enemy for backstab opportunities
4. **Edge Cases** - Portal destruction, monster pathfinding updates
5. **Polish & Testing** - Visual refinements, comprehensive test coverage

---

## 🏗️ Implementation Plan

### **Task 1: Terrain Blocking (2-3 hours)**

**Location:** `components/portal_placer.py` + `services/portal_manager.py`

**Current State:**
- `_is_valid_placement()` checks for walls (`tile.blocked`)
- Doesn't check for terrain types (water, lava)

**What to Add:**
```python
def _is_terrain_passable(self, tile):
    """Check if terrain allows portal placement."""
    # Check for water tiles
    if hasattr(tile, 'terrain_type') and tile.terrain_type == 'water':
        return False
    # Check for lava tiles
    if hasattr(tile, 'terrain_type') and tile.terrain_type == 'lava':
        return False
    # Check for hazard markers
    if hasattr(tile, 'has_hazard') and tile.has_hazard:
        return False
    return True
```

**Integration:**
- Update `PortalManager.create_portal_entity()` to validate terrain
- Add user feedback: "Cannot place portal on water/lava"
- Test with different terrain types

**Tests:**
- ✅ Can place on normal ground
- ✅ Cannot place on water
- ✅ Cannot place on lava
- ✅ Cannot place on walls
- ✅ Error message shows correct reason

---

### **Task 2: Monster Portal Detection & AI Flags (3-4 hours)**

**Location:** `components/ai.py` + `services/portal_manager.py`

**Current State:**
- Only player can use portals
- Monsters don't know portals exist

**New Design: portal_usable Flag**
```python
# In monster AI definition (BasicMonster, etc):
class BasicMonster(AI):
    def __init__(self):
        self.portal_usable = True  # Can this monster use portals?
    
    # For smart monsters that won't use portals:
    def __init__(self):
        self.portal_usable = False  # Bosses, certain types avoid portals
```

**What to Add:**
```python
class MonsterPortalBehavior:
    """Handle monster interaction with portals."""
    
    @staticmethod
    def can_monster_use_portal(monster, portal):
        """Check if monster should use this portal.
        
        Checks:
        1. Monster AI has portal_usable=True
        2. Monster is not carrying the entry portal
        3. Portal is deployed (not in inventory)
        """
        # Check AI flag first
        if hasattr(monster, 'ai') and hasattr(monster.ai, 'portal_usable'):
            if not monster.ai.portal_usable:
                return False  # This monster won't use portals
        
        # Don't use if carrying entry portal
        if monster.inventory and any(
            hasattr(item, 'portal') and 
            item.portal.portal_type == 'entrance'
            for item in monster.inventory.items
        ):
            return False
        
        return True
    
    @staticmethod
    def should_monster_pathfind_through_portal(monster, portal):
        """Decide if monster should navigate through portal."""
        # Check flag first
        if not MonsterPortalBehavior.can_monster_use_portal(monster, portal):
            return False
        
        # Use portals if they help reach player
        # Later: add smarter tactics (boss avoidance, etc)
        return True
```

**Integration:**
- Add `portal_usable` attribute to AI classes (default: True for basic monsters)
- Set `portal_usable = False` for boss/special monsters
- Check flag in `PortalManager.check_portal_collision()` before teleporting
- Modify pathfinding to consider portals only if `portal_usable=True`
- Call `PortalManager.check_portal_collision()` for monsters too

**Tests:**
- ✅ Monster with `portal_usable=True` uses portals
- ✅ Monster with `portal_usable=False` ignores portals
- ✅ Monster can't use portal if carrying entry portal
- ✅ Monster pathfinds toward portal if it leads to player AND `portal_usable=True`
- ✅ Monster teleports correctly through portal
- ✅ Boss monsters avoid using portals

---

### **Task 3: Monster Teleportation (2-3 hours)**

**Location:** `services/portal_manager.py` + `services/movement_service.py`

**Current State:**
- `check_portal_collision()` only handles players
- Monsters don't get teleported

**What to Add:**
```python
# Expand PortalManager.check_portal_collision() to handle monsters:
if isinstance(entity, Monster):
    # Same teleportation logic as player
    # But: update monster's pathfinding cache
    # Clear any cached paths (they're now invalid!)
```

**Integration:**
- Update `MovementService` to call portal collision for all entities
- Monsters step on portal → they teleport
- Update monster's memory/targeting after teleport
- Clear pathfinding cache (destination changed!)

**Tests:**
- ✅ Monster teleports when stepping on portal
- ✅ Monster position updated correctly
- ✅ Monster's FOV recalculated
- ✅ Monster pathfinding resets after teleport
- ✅ Monster can't teleport if carrying exit portal

---

### **Task 4: Combat Positioning - Backstab Bonus (2-3 hours)**

**Location:** `combat/combat_system.py` + `services/portal_manager.py`

**Current State:**
- Combat resolved based on position
- No special bonuses for tactical positioning

**What to Add:**
```python
class PortalCombatBonus:
    """Handle combat bonuses from portal teleportation."""
    
    @staticmethod
    def get_backstab_bonus(attacker, defender, was_teleported):
        """Calculate damage bonus if attacking from behind via portal."""
        if not was_teleported:
            return 0
        
        # Check if attacker is now behind defender
        dx = attacker.x - defender.x
        dy = attacker.y - defender.y
        
        # Simple check: behind means different x or y
        # (More sophisticated: calculate actual facing direction)
        if dx != 0 or dy != 0:
            # Backstab bonus: 1.5x damage
            return 0.5  # 50% bonus multiplier
        
        return 0
```

**Integration:**
- Track if entity just teleported this turn
- When combat happens, check for backstab bonus
- Apply 1.5x damage multiplier if player backstabs
- Enemies can't backstab player (optional: they can in hard mode!)

**Tests:**
- ✅ Player teleports behind enemy, gets backstab bonus
- ✅ Backstab bonus only works first turn after teleport
- ✅ No bonus if teleporting to same spot
- ✅ Bonus damage calculated correctly
- ✅ Message shows "backstab" flavor text

---

### **Task 5: Portal Destruction & Cleanup (1-2 hours)**

**Location:** `services/portal_manager.py` + `services/ai_system.py`

**Current State:**
- Portals persist until wand recharges
- Monsters with portals in inventory → portals destroyed

**What to Add:**
```python
class PortalCleanup:
    """Handle portal cleanup when conditions change."""
    
    @staticmethod
    def cleanup_on_death(entity):
        """Remove/destroy portals if carrying them."""
        if entity.inventory:
            portals = [item for item in entity.inventory.items 
                      if hasattr(item, 'portal')]
            for portal in portals:
                # Drop portal on death location
                # Or: destroy it
                pass
    
    @staticmethod
    def cleanup_on_level_change(entities):
        """Destroy all portals when leaving level."""
        # Find all portal entities
        # Remove them from entities list
        pass
```

**Integration:**
- When monster dies while carrying portal → portal drops
- When player leaves level → portals destroyed
- When wand recharges → old portals destroyed (already done)

**Tests:**
- ✅ Portal drops when monster dies
- ✅ Portal destroyed when player changes level
- ✅ Player can pick up dropped portal
- ✅ Old portals destroyed on wand recharge

---

## 📊 Phase B Success Metrics

### Completion Checklist
- [ ] All terrain types block portal placement
- [ ] Monsters pathfind through portals
- [ ] Monsters teleport correctly
- [ ] Combat backstab bonus works
- [ ] Portal cleanup on death/level change
- [ ] 10+ comprehensive tests passing
- [ ] No regressions in Phase A tests
- [ ] Playtesting confirms fun emergent behavior

### Quality Gates
- ✅ All existing tests still pass (54/55)
- ✅ New tests all pass (10+)
- ✅ No linter errors
- ✅ Playable and balanced

---

## 🎮 Playtesting Focus for Phase B

**Key Scenarios to Test:**
1. Try placing portals on different terrain types
2. Watch monsters pathfind toward you through portals
3. Teleport behind an enemy and backstab
4. Leave a portal, come back later - what happens?
5. Drop a portal in lava and pick it up - still works?
6. Monster picks up exit portal - how does game handle it?
7. Die while carrying a portal - does it drop?
8. Go down stairs while portal is active - does it persist?

**Balance Tuning:**
- Is backstab bonus too strong? (1.5x damage)
- Should monsters be smarter about portal usage?
- Should some monsters avoid portals?
- Portal placement restrictions too harsh?

---

## 🏁 Phase B Implementation Order

**Day 5 (Today):**
1. ✅ Terrain blocking validation
2. ⏱️ Monster portal detection setup

**Day 6 (Tomorrow):**
3. Monster teleportation
4. Combat backstab bonus
5. Comprehensive tests

**Day 7 (Day After):**
6. Integration testing
7. Balance tuning
8. Documentation

---

## 🚀 Ready to Begin

All groundwork complete. Phase A foundation solid. Ready to make portals **truly interactive** with monsters and terrain.

**First step:** Implement terrain blocking (task 1). It's the quickest win and everything else builds on it.

