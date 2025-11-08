# 🌀 Portal System - Complete Specification

**Status:** Ready for Implementation  
**Complexity:** Medium (new component types, wand integration, teleportation)  
**Timeline:** Phase A (3-4 days) + Phase B (2-3 days)  
**Tests:** 25+ integration tests  

---

## 🎯 **Core Design**

### **Wand of Portals (Legendary Item)**

**Mechanic:**
- Single legendary item (2-3 per full run, guaranteed at least 1 early)
- **Infinite uses** - never runs out of charges
- **One cycle at a time:** Click entrance → click exit → portals appear → use wand again = old portals vanish, wand recharged
- Portals are **physical map objects** that can be carried in inventory

**Visual:**
- Entrance portal: Blue swirl `Θ` (color: light_blue or 100, 200, 255)
- Exit portal: Orange swirl `Θ` (color: light_orange or 255, 180, 80)
- Clearly distinguishable, visually distinct

---

## 🎮 **Interactions**

### **Deploying Portals**

**Step 1: Activate Portal Targeting**
```
Player presses 'P' (or item activation key for wand)
Game enters TARGETING_PORTAL mode
Cursor becomes targeting reticle
Display: "Click to place ENTRANCE portal (ESC to cancel)"
```

**Step 2: Place Entrance**
```
Player clicks location
- Validate location (not wall, not lava, within map bounds)
- If invalid: "Cannot place portal there"
- If valid: Blue Θ appears, entrance portal created
- Display: "Click to place EXIT portal"
```

**Step 3: Place Exit**
```
Player clicks location
- Validate location (not wall, not lava, within map bounds)
- If invalid: "Cannot place portal there"
- If valid: Orange Θ appears, exit portal created
- Portals linked as pair (entrance.linked_portal = exit, vice versa)
- Display: "Portals active. Use wand again to recycle."
- Game exits TARGETING_PORTAL mode
```

---

### **Using Portals**

**Walking Through Portal (Teleportation)**
```
Player walks onto portal tile (entrance or exit)
- If entrance AND carrying exit portal: BLOCKED (prevent self-entry)
- If entrance AND NOT carrying exit: Teleport to exit portal location
  - Player position updated to exit location
  - FOV recalculated
  - Message: "You step through the portal..."
- Exit portal works identically (bidirectional)
```

**Picking Up Portal**
```
Player right-clicks on deployed portal
- Player pathfinding moves to portal location
- Portal becomes inventory item (named "Portal Entrance" or "Portal Exit")
- Portal removed from map
- If carrying paired portal already: 
  "Portal added to inventory"
- Message: "[Portal] added to inventory"
```

**Deploying Portal from Inventory**
```
Player has portal in inventory
Player right-clicks portal in inventory
- Open location cursor (targeting mode)
- Player clicks target location
- Validate location (same checks as above)
- Portal appears at location on map
- Portal removed from inventory
- Message: "[Portal] deployed"
```

**Recycling Portals (Wand Again)**
```
Player has wand + portals already active
Player uses wand again
- Old entrance + exit vanish from map
- Wand recharged and ready
- If player carrying either portal: 
  "Those portals were destroyed. Wand recharged."
- New cycle begins
```

---

## 🏗️ **Architecture**

### **New Component: Portal**

**File:** `components/portal.py`

```python
class Portal(MapFeature):
    """A dimensional gateway that teleports entities between two points."""
    
    def __init__(self, 
                 portal_type: str,  # 'entrance' or 'exit'
                 linked_portal: Optional['Portal'] = None):
        """
        Args:
            portal_type: 'entrance' (blue) or 'exit' (orange)
            linked_portal: The paired portal this connects to
        """
        super().__init__(
            feature_type=MapFeatureType.PORTAL,
            discovered=True,  # Portals always visible
            interactable=True
        )
        
        self.portal_type = portal_type  # 'entrance' or 'exit'
        self.linked_portal = linked_portal
        self.is_deployed = True  # False when in inventory
        self.owner = None  # Entity carrying this portal (if in inventory)
    
    def get_portal_pair(self) -> Tuple[Optional['Portal'], Optional['Portal']]:
        """Get both entrance and exit portals as tuple (entrance, exit)."""
        if self.portal_type == 'entrance':
            return (self, self.linked_portal)
        else:
            return (self.linked_portal, self)
    
    def is_valid_to_enter(self, actor: 'Entity') -> bool:
        """Check if entity can enter this portal."""
        if self.portal_type == 'exit':
            return True  # Exits always usable
        
        # Entrance blocked if carrying exit portal
        if actor.inventory:
            for item in actor.inventory.items:
                if hasattr(item, 'portal') and item.portal.portal_type == 'exit':
                    if item.portal.linked_portal == self.linked_portal:
                        return False  # Carrying paired exit portal
        
        return True
    
    def teleport_through(self, actor: 'Entity', dungeon) -> List[Dict[str, Any]]:
        """Teleport actor through this portal to the exit."""
        results = []
        
        if not self.is_valid_to_enter(actor):
            results.append({
                'message': "You can't enter that portal right now."
            })
            return results
        
        if not self.linked_portal or not self.linked_portal.is_deployed:
            results.append({
                'message': "The portal flickers and dies before you reach it."
            })
            return results
        
        # Teleport
        old_x, old_y = actor.x, actor.y
        actor.x = self.linked_portal.x
        actor.y = self.linked_portal.y
        
        results.append({
            'teleported': True,
            'actor': actor,
            'from_pos': (old_x, old_y),
            'to_pos': (actor.x, actor.y),
            'message': "You step through the portal..."
        })
        
        return results
    
    def __repr__(self):
        return f"Portal({self.portal_type}, deployed={self.is_deployed})"
```

---

### **New Component: PortalPlacer (Wand Logic)**

**File:** `components/portal_placer.py`

```python
class PortalPlacer(Wand):
    """Manages portal creation and lifecycle for Wand of Portals."""
    
    def __init__(self):
        """Initialize portal wand (infinite uses)."""
        super().__init__(
            name="Wand of Portals",
            description="Creates dimensional gateways",
            charges=0  # Infinite (always "charged")
        )
        
        self.active_entrance: Optional[Portal] = None
        self.active_exit: Optional[Portal] = None
        self.targeting_stage = 0  # 0=idle, 1=placing_entrance, 2=placing_exit
    
    def start_targeting(self) -> None:
        """Begin portal placement sequence."""
        if self.active_entrance or self.active_exit:
            self.targeting_stage = 1  # Start fresh cycle
            return
        self.targeting_stage = 1
    
    def place_entrance(self, x: int, y: int, dungeon) -> Dict[str, Any]:
        """Place entrance portal."""
        if not self._is_valid_placement(x, y, dungeon):
            return {'success': False, 'message': 'Cannot place portal there'}
        
        # Remove old portals if recycling
        if self.active_entrance:
            self.active_entrance.is_deployed = False
            self.active_entrance.owner = None
        if self.active_exit:
            self.active_exit.is_deployed = False
            self.active_exit.owner = None
        
        # Create entrance portal
        from components.portal import Portal
        entrance = Portal('entrance')
        entrance.x, entrance.y = x, y
        entrance.is_deployed = True
        
        self.active_entrance = entrance
        self.targeting_stage = 2
        
        return {
            'success': True,
            'portal': entrance,
            'message': 'Entrance portal placed. Click to place exit portal.'
        }
    
    def place_exit(self, x: int, y: int, dungeon) -> Dict[str, Any]:
        """Place exit portal and complete cycle."""
        if not self._is_valid_placement(x, y, dungeon):
            return {'success': False, 'message': 'Cannot place portal there'}
        
        if not self.active_entrance:
            return {'success': False, 'message': 'No entrance portal active'}
        
        # Create exit portal
        from components.portal import Portal
        exit_portal = Portal('exit', linked_portal=self.active_entrance)
        exit_portal.x, exit_portal.y = x, y
        exit_portal.is_deployed = True
        
        # Link both portals
        self.active_entrance.linked_portal = exit_portal
        
        self.active_exit = exit_portal
        self.targeting_stage = 0
        
        return {
            'success': True,
            'entrance': self.active_entrance,
            'exit': exit_portal,
            'message': 'Portals active!'
        }
    
    def recycle_portals(self) -> Dict[str, Any]:
        """Remove current portals and reset for new cycle."""
        if self.active_entrance:
            self.active_entrance.is_deployed = False
            self.active_entrance = None
        if self.active_exit:
            self.active_exit.is_deployed = False
            self.active_exit = None
        
        self.targeting_stage = 0
        
        return {
            'recycled': True,
            'message': 'Portals recycled. Wand ready for new placement.'
        }
    
    def _is_valid_placement(self, x: int, y: int, dungeon) -> bool:
        """Validate portal placement location."""
        # Check bounds
        if x < 0 or x >= dungeon.width or y < 0 or y >= dungeon.height:
            return False
        
        tile = dungeon.tiles[x][y]
        
        # Can't place on walls
        if tile.block_movement:
            return False
        
        # Can't place on water, lava (specific tile types)
        if tile.tile_type in ['water', 'lava']:
            return False
        
        # Valid placement
        return True
```

---

### **Updated MapFeatureType**

**File:** `components/map_feature.py`

```python
class MapFeatureType(Enum):
    """Types of map features that can be interacted with."""
    CHEST = auto()
    SIGNPOST = auto()
    MURAL = auto()
    PORTAL = auto()  # NEW
    SECRET_DOOR = auto()
    VAULT_DOOR = auto()
    DOOR = auto()
```

---

### **Updated ComponentType**

**File:** `components/component_registry.py`

```python
class ComponentType(Enum):
    # ... existing ...
    PORTAL = auto()  # NEW
    PORTAL_PLACER = auto()  # NEW (for wand)
```

---

### **Updated Entity Factory**

**File:** `config/entity_factory.py`

```python
def create_wand_of_portals(self, x: int, y: int) -> Optional[Entity]:
    """Create Wand of Portals legendary item."""
    try:
        from components.portal_placer import PortalPlacer
        
        wand = Entity(
            x=x, y=y,
            char='/', color=(100, 255, 200),
            name='Wand of Portals',
            blocks=False,
            render_order=RenderOrder.ITEM
        )
        
        portal_placer = PortalPlacer()
        wand.portal_placer = portal_placer
        wand.components.add(ComponentType.PORTAL_PLACER, portal_placer)
        
        logger.debug(f"Created Wand of Portals at ({x}, {y})")
        return wand
    except Exception as e:
        logger.error(f"Error creating Wand of Portals: {e}")
        return None

def create_portal(self, x: int, y: int, 
                 portal_type: str = 'entrance',
                 linked: Optional['Portal'] = None) -> Optional[Entity]:
    """Create a portal entity."""
    try:
        from components.portal import Portal
        
        color = (100, 200, 255) if portal_type == 'entrance' else (255, 180, 80)
        
        entity = Entity(
            x=x, y=y,
            char='Θ', color=color,
            name=f'{portal_type.title()} Portal',
            blocks=False,
            render_order=RenderOrder.ITEM
        )
        
        portal = Portal(portal_type, linked_portal=linked)
        entity.portal = portal
        entity.components.add(ComponentType.PORTAL, portal)
        
        logger.debug(f"Created {portal_type} portal at ({x}, {y})")
        return entity
    except Exception as e:
        logger.error(f"Error creating portal: {e}")
        return None
```

---

### **Input Handling**

**File:** `input/state.py` (or similar)

```python
# Add new input state
class GameInputState(Enum):
    # ... existing ...
    TARGETING_PORTAL = auto()  # NEW
```

**File:** `input_handlers.py`

```python
def handle_portal_targeting(self, event) -> Dict[str, Any]:
    """Handle player input during portal placement."""
    
    if event.key == 'ESCAPE':
        return {'input_state': GameInputState.NORMAL}
    
    if event.mouse_button == 'LEFT':
        x, y = event.mouse_pos
        
        if self.portal_targeting_stage == 1:
            # Placing entrance
            result = player.wand.place_entrance(x, y, dungeon)
            if result['success']:
                # Add portal to map
                dungeon.entities.append(result['portal'])
            return result
        
        elif self.portal_targeting_stage == 2:
            # Placing exit
            result = player.wand.place_exit(x, y, dungeon)
            if result['success']:
                # Add portals to map
                dungeon.entities.append(result['entrance'])
                dungeon.entities.append(result['exit'])
            return {**result, 'input_state': GameInputState.NORMAL}
```

---

## 🎯 **Inventory Integration**

### **Portal as Item**

Portals become **item entities** when carried:

```python
# In inventory
portal_item = Entity(
    x=0, y=0,  # Inventory, no position
    char='Θ', color=(100, 200, 255),
    name='Portal (Entrance)',
    blocks=False
)
portal_item.item = Item()  # Standard item component
portal_item.portal = Portal('entrance')  # Portal component

# In inventory display
"Portal (Entrance)"  # Player sees this
# Right-click to deploy
```

**Carrying Rules:**
- Portal items occupy standard inventory slots
- Carrying entrance + exit = can't use entrance (blocked by game logic)
- No special UI needed - standard item interaction

---

## 🧭 **Monster Pathfinding**

### **Monster AI with Portals**

**File:** `components/ai.py` (update existing)

```python
class BaseMonsterAI:
    def _find_path_to_target(self, target, dungeon):
        """Find path to target, considering portals."""
        
        # Normal pathfinding
        path = self._compute_path(target, dungeon)
        
        # Check if using portal as shortcut is better
        # (Portal usage logic optional - can add later)
        
        return path
    
    def _is_blocked_by_portal(self, x, y):
        """Check if portal blocks movement (portals don't block, they transport)."""
        # Portals are NOT blocking, entities walk through them
        return False
```

**Monster + Portal Behavior:**
- Monsters can walk through deployed portals (teleports them)
- Monsters don't actively seek portals (no special AI)
- If monster steps on entrance, teleports to exit
- Creates risk/reward: Portal can be used against you

---

## 🎨 **Rendering**

### **Portal Visuals**

```python
# In render_functions.py or rendering system

def render_portal(entity, console):
    """Render portal with visual distinction."""
    
    if entity.portal.portal_type == 'entrance':
        color = (100, 200, 255)  # Blue
        char = 'Θ'
    else:
        color = (255, 180, 80)   # Orange
        char = 'Θ'
    
    console.print(entity.x, entity.y, char, fg=color)
    
    # Optional: Add animation (flicker portal every other turn)
    if entity.portal.is_deployed:
        if game_turn % 2 == 0:
            # Full brightness
            pass
        else:
            # Dimmed (semi-transparent effect)
            pass
```

---

## 🧪 **Phase A: Testing (Core System)**

**Test Suite:** `tests/test_portal_system_phase_a.py`

```python
class TestPortalPlacement:
    def test_wand_creates_entrance_portal(self)
    def test_wand_creates_exit_portal(self)
    def test_portals_linked_correctly(self)
    def test_invalid_placement_blocked(self)
    def test_portal_in_wall_rejected(self)
    def test_portal_out_of_bounds_rejected(self)

class TestTeleportation:
    def test_walk_through_entrance_teleports_to_exit(self)
    def test_walk_through_exit_teleports_to_entrance(self)
    def test_cannot_enter_if_carrying_exit(self)
    def test_invalid_teleport_blocks_movement(self)

class TestInventory:
    def test_right_click_portal_picks_it_up(self)
    def test_portal_item_in_inventory(self)
    def test_right_click_from_inventory_deploys_portal(self)
    def test_cannot_deploy_to_invalid_location(self)

class TestRecycling:
    def test_wand_recycles_portals(self)
    def test_recycled_portals_removed_from_map(self)
    def test_wand_ready_after_recycle(self)
    def test_carrying_portal_destroyed_on_recycle(self)

class TestMonsterInteraction:
    def test_monster_walks_through_portal(self)
    def test_monster_teleports_correctly(self)
```

**Total Phase A Tests:** 15+

---

## 🧪 **Phase B: Testing (Advanced)**

```python
class TestTerrainInteraction:
    def test_cannot_place_on_water(self)
    def test_cannot_place_on_lava(self)
    def test_cannot_place_on_wall(self)

class TestCombatIntegration:
    def test_portal_behind_enemy(self)
    def test_backstab_bonus_with_portal(self)
    def test_monster_avoids_dangerous_portal(self)

class TestVisualization:
    def test_entrance_blue_exit_orange(self)
    def test_portal_animations(self)
    def test_inventory_portal_display(self)
```

**Total Phase B Tests:** 10+

**Total Combined:** 25+ tests

---

## 📋 **Implementation Order**

### **Phase A: Core System (3-4 days)**

**Day 1:**
- [ ] Create `components/portal.py` (Portal class)
- [ ] Create `components/portal_placer.py` (PortalPlacer/wand logic)
- [ ] Update map feature types + component types
- [ ] Update entity factory (create_wand_of_portals, create_portal)

**Day 2:**
- [ ] Input handling (TARGETING_PORTAL state)
- [ ] Portal targeting UI (reticle, messages)
- [ ] Entrance/exit placement validation
- [ ] Portal linkage logic

**Day 3:**
- [ ] Teleportation through portals
- [ ] Portal inventory pickup/drop
- [ ] Inventory deployment
- [ ] Portal recycling (wand reuse)

**Day 4:**
- [ ] Rendering (portal visuals)
- [ ] Phase A tests (15+ tests)
- [ ] Debug & refine
- [ ] Integration testing

---

### **Phase B: Advanced Mechanics (2-3 days)**

**Day 5:**
- [ ] Terrain blocking (water, lava, walls)
- [ ] Monster pathfinding with portals
- [ ] Monster teleportation logic

**Day 6:**
- [ ] Combat positioning (backstab bonus)
- [ ] Visual animations (optional)
- [ ] Phase B tests (10+ tests)

**Day 7:**
- [ ] Final integration tests
- [ ] Balance tuning
- [ ] Documentation

---

## 🎯 **Success Criteria**

**Phase A Complete When:**
- ✅ Wand creates entrance + exit portals
- ✅ Player can teleport through portals
- ✅ Portals can be picked up/dropped
- ✅ Wand recycling works
- ✅ 15+ tests passing
- ✅ No regressions in existing tests

**Phase B Complete When:**
- ✅ Terrain interactions working
- ✅ Monster pathfinding through portals
- ✅ Combat bonuses applied
- ✅ 25+ total tests passing
- ✅ Playable, balanced, fun

---

## 🔗 **Integration Points**

**Files that need updates:**
- `config/entities.yaml` - Add wand_of_portals definition
- `config/entity_factory.py` - create_wand + create_portal
- `components/map_feature.py` - Add PORTAL type
- `components/component_registry.py` - Add PORTAL + PORTAL_PLACER types
- `input/state.py` - Add TARGETING_PORTAL state
- `input_handlers.py` - Portal targeting handler
- `render_functions.py` - Portal rendering
- `map_objects/game_map.py` - Optional: portal spawn rules

**New files:**
- `components/portal.py`
- `components/portal_placer.py`
- `tests/test_portal_system_phase_a.py`
- `tests/test_portal_system_phase_b.py` (Phase B)

---

## 🚀 **Ready to Execute**

All spec complete. Architecture clear. Tests defined. Ready to build.

**Next Step:** Approve this spec and I'll start Phase A implementation.


