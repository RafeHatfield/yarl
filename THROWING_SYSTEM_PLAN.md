# Throwing System + Projectile Animation - Implementation Plan

## 🎯 **Goals**
1. **Projectile Animation** - Animated path for arrows, thrown items, etc.
2. **Throw Action** - Press 't' to throw an item from inventory
3. **Item Shattering** - Potions break on impact with effects
4. **Weapon Throwing** - Throw daggers/weapons for damage
5. **Bow Animation** - Apply projectile animation to existing bow weapons

---

## 📊 **What We Already Have**

### ✅ **Visual Effect System**
- `VisualEffectQueue` with `PATH_EFFECT` support
- Camera translation working
- Effects play during render phase
- Perfect for projectile trails!

### ✅ **Targeting System**
- Works for spells (fireball, lightning, etc.)
- Handles FOV/LOS checking
- Mouse targeting with crosshair
- Easy to reuse for throwing!

### ✅ **Bow Weapons Defined**
- Shortbow (1d6, reach 8)
- Longbow (1d8, reach 10)
- Crossbow (1d8, reach 8)
- **BUT:** No animation or projectile visuals yet!

### ✅ **Item System**
- Potions have effects (healing, poison, paralysis, etc.)
- Items have display names, colors, chars
- Easy to extract for projectile rendering

---

## 🎬 **Phase 1: Projectile Animation System (Foundation)**
**Time: 1 hour**

### **1.1 Add PROJECTILE Effect Type**
**File:** `visual_effect_queue.py`

```python
class EffectType(Enum):
    HIT = auto()
    CRITICAL_HIT = auto()
    MISS = auto()
    FIREBALL = auto()
    LIGHTNING = auto()
    DRAGON_FART = auto()
    AREA_EFFECT = auto()
    PATH_EFFECT = auto()
    WAND_RECHARGE = auto()
    PROJECTILE = auto()  # NEW: Animated flying projectile
```

### **1.2 Implement Projectile Animation**
**File:** `visual_effect_queue.py`

Add `_play_projectile()` method to `QueuedEffect`:

```python
def _play_projectile(self, con=0, camera=None) -> None:
    """Play animated projectile flying from source to target.
    
    Shows item/arrow traveling tile-by-tile with smooth animation.
    Used for: arrows, thrown potions, thrown weapons.
    
    Params (from self.params):
        - path: List[(x, y)] of tiles projectile travels through
        - char: Character to display (arrow, potion char, etc.)
        - color: RGB tuple for projectile color
        - frame_duration: Time per tile (default 0.04s)
    """
    path = self.params.get('path', [])
    char = self.params.get('char', ord('*'))
    color = self.params.get('color', (255, 255, 255))
    frame_duration = self.params.get('frame_duration', 0.04)  # 40ms per tile
    
    # Get viewport offset
    from config.ui_layout import get_ui_layout
    ui_layout = get_ui_layout()
    viewport_offset = ui_layout.viewport_position
    
    # Animate projectile along path
    for world_x, world_y in path:
        # Translate world → viewport → screen
        if camera:
            if not camera.is_in_viewport(world_x, world_y):
                continue
            viewport_x, viewport_y = camera.world_to_viewport(world_x, world_y)
        else:
            viewport_x, viewport_y = world_x, world_y
        
        screen_x = viewport_x + viewport_offset[0]
        screen_y = viewport_y + viewport_offset[1]
        
        # Draw projectile at this position
        libtcodpy.console_set_default_foreground(con, color)
        libtcodpy.console_put_char(con, screen_x, screen_y, char, libtcodpy.BKGND_NONE)
        libtcodpy.console_flush()
        
        time.sleep(frame_duration)
```

### **1.3 Add Queue Helper**
**File:** `visual_effect_queue.py`

```python
def queue_projectile(
    self, 
    path: List[Tuple[int, int]], 
    char: int, 
    color: Tuple[int, int, int],
    **kwargs
) -> None:
    """Queue an animated projectile effect.
    
    Args:
        path: List of (x, y) coordinates projectile travels
        char: Character to display (arrow, item char, etc.)
        color: RGB color tuple
        **kwargs: Additional params (frame_duration, etc.)
    """
    x, y = path[-1] if path else (0, 0)
    self.effects.append(QueuedEffect(
        EffectType.PROJECTILE, x, y, None, 
        path=path, char=char, color=color, **kwargs
    ))
```

**Why This Works:**
- Reuses existing path/camera translation code
- Tile-by-tile animation (like lightning bolt)
- Configurable speed (fast arrows, slow boulders)
- Works with camera system

---

## 🎯 **Phase 2: Throw Action Handler**
**Time: 30 minutes**

### **2.1 Add 't' Key Handler**
**File:** `input_handlers.py`

In `handle_player_turn_keys()`, add:

```python
elif key_char == "t":
    return {"throw": True}
```

### **2.2 Add Throw Action to Game Actions**
**File:** `game_actions.py`

```python
def _handle_throw_action(self, _) -> None:
    """Handle throw action - select item then target."""
    current_state = self.state_manager.state.current_state
    if current_state != GameStates.PLAYERS_TURN:
        return
    
    player = self.state_manager.state.player
    message_log = self.state_manager.state.message_log
    
    if not player.inventory or not player.inventory.items:
        message = MB.warning("You have nothing to throw.")
        message_log.add_message(message)
        return
    
    # Show inventory selection screen for throwing
    from game_states import GameStates
    self.state_manager.set_game_state(GameStates.THROW_SELECT_ITEM)
```

### **2.3 Add Game State**
**File:** `game_states.py`

```python
class GameStates(Enum):
    # ... existing states ...
    THROW_SELECT_ITEM = auto()  # Selecting item to throw
    THROW_TARGETING = auto()    # Targeting throw location
```

**Flow:**
1. Press 't' → Enter THROW_SELECT_ITEM state (show inventory)
2. Select item → Enter THROW_TARGETING state (show crosshair)
3. Click target → Execute throw, animate projectile, apply effect

---

## 🧪 **Phase 3: Throw Execution Logic**
**Time: 1 hour**

### **3.1 Create Throwing Module**
**File:** `throwing.py` (NEW)

```python
"""Throwing system - handles thrown items and projectiles."""

from typing import List, Dict, Any, Tuple
import tcod.line
from message_builder import MessageBuilder as MB


def calculate_throw_path(
    start_x: int, start_y: int,
    target_x: int, target_y: int,
    game_map,
    max_range: int = 10
) -> List[Tuple[int, int]]:
    """Calculate path projectile takes when thrown.
    
    Uses Bresenham line algorithm. Stops at first blocking tile.
    
    Args:
        start_x, start_y: Thrower's position
        target_x, target_y: Target position
        game_map: Game map for collision
        max_range: Maximum throw distance
        
    Returns:
        List of (x, y) tuples for projectile path
    """
    # Get line from start to target
    line = list(tcod.line.bresenham(start_x, start_y, target_x, target_y))
    
    # Limit to max range
    if len(line) > max_range:
        line = line[:max_range]
    
    # Stop at first blocking tile (wall)
    path = []
    for x, y in line:
        path.append((x, y))
        if game_map.tiles[x][y].blocked:
            break  # Hit a wall, stop here
    
    return path


def throw_item(
    thrower,
    item,
    target_x: int,
    target_y: int,
    entities: List,
    game_map,
    fov_map
) -> List[Dict[str, Any]]:
    """Execute a throw action.
    
    Calculates path, animates projectile, applies effects.
    
    Args:
        thrower: Entity throwing the item
        item: Item entity being thrown
        target_x, target_y: Target coordinates
        entities: All entities in game
        game_map: Game map
        fov_map: Field of view map
        
    Returns:
        List of result dictionaries
    """
    results = []
    
    # Calculate throw path
    path = calculate_throw_path(
        thrower.x, thrower.y,
        target_x, target_y,
        game_map,
        max_range=10  # Base throw range
    )
    
    if not path:
        return [{
            "consumed": False,
            "message": MB.warning("Invalid throw target!")
        }]
    
    # Get final landing position (last tile in path)
    final_x, final_y = path[-1]
    
    # Queue projectile animation
    from visual_effect_queue import get_effect_queue
    effect_queue = get_effect_queue()
    
    item_char = ord(item.char) if hasattr(item, 'char') else ord('*')
    item_color = item.color if hasattr(item, 'color') else (255, 255, 255)
    
    effect_queue.queue_projectile(
        path=path,
        char=item_char,
        color=item_color,
        frame_duration=0.05  # 50ms per tile
    )
    
    # Check what we hit
    target_entity = None
    for entity in entities:
        if entity.x == final_x and entity.y == final_y and entity != thrower:
            if hasattr(entity, 'fighter') and entity.fighter:
                target_entity = entity
                break
    
    # Apply effects based on item type
    if item.item and item.item.use_function:
        # It's a potion/consumable - apply effect at target location
        results.extend(_throw_potion(
            item, thrower, target_entity, final_x, final_y, 
            entities, game_map, fov_map
        ))
    elif hasattr(item, 'item') and hasattr(item.item, 'equipment'):
        # It's a weapon - deal damage
        results.extend(_throw_weapon(
            item, thrower, target_entity, final_x, final_y
        ))
    else:
        # Generic throwable
        results.append({
            "message": MB.info(f"You throw the {item.name}. It lands at ({final_x}, {final_y}).")
        })
    
    results.append({"consumed": True})  # Item is thrown (removed from inventory)
    return results


def _throw_potion(
    potion, thrower, target, final_x, final_y,
    entities, game_map, fov_map
) -> List[Dict[str, Any]]:
    """Handle throwing a potion - it shatters on impact."""
    results = []
    
    if target:
        # Hit an entity directly - apply full effect
        results.append({
            "message": MB.spell_effect(
                f"The {potion.name} shatters on {target.name}!"
            )
        })
        
        # Apply potion effect to target
        use_results = potion.item.use_function(target, entities=entities)
        results.extend(use_results)
        
    else:
        # Missed - potion breaks on ground (splash effect?)
        results.append({
            "message": MB.info(
                f"The {potion.name} shatters on the ground!"
            )
        })
        
        # Could add splash damage to adjacent tiles here
        # For now, just wasted
    
    return results


def _throw_weapon(
    weapon, thrower, target, final_x, final_y
) -> List[Dict[str, Any]]:
    """Handle throwing a weapon - deals damage based on weapon."""
    results = []
    
    if target:
        # Hit! Roll damage
        import random
        from components.fighter import roll_dice
        
        # Get weapon damage (reduced for throwing vs melee)
        equipment = weapon.item.equipment
        damage_dice = equipment.damage_dice if equipment else "1d4"
        
        # Throwing penalty: -2 to damage (min 1)
        base_damage = roll_dice(damage_dice)
        throw_damage = max(1, base_damage - 2)
        
        # Apply damage
        if target.fighter:
            target.fighter.take_damage(throw_damage)
            
            results.append({
                "message": MB.damage(
                    f"The {weapon.name} hits {target.name} for {throw_damage} damage!"
                )
            })
            
            # Check if target died
            if target.fighter.hp <= 0:
                results.append({
                    "message": MB.kill(f"{target.name} is killed!")
                })
    else:
        # Missed - weapon lands on ground
        results.append({
            "message": MB.info(f"The {weapon.name} clatters to the ground.")
        })
    
    # Drop weapon at final position (whether hit or miss)
    weapon.x = final_x
    weapon.y = final_y
    
    return results
```

---

## 🏹 **Phase 4: Apply to Bow Attacks**
**Time: 30 minutes**

### **4.1 Detect Ranged Weapons**
**File:** `components/fighter.py`

In `attack()` method, check for ranged weapons:

```python
def attack(self, target, entities, game_map, fov_map):
    """Attack a target, with projectile animation for ranged weapons."""
    # ... existing attack logic ...
    
    # Check if using ranged weapon
    if self.owner.equipment:
        main_hand = self.owner.equipment.main_hand
        if main_hand and hasattr(main_hand.item.equipment, 'reach'):
            reach = main_hand.item.equipment.reach
            if reach and reach > 1:
                # It's a ranged weapon! Animate projectile
                self._animate_ranged_attack(target, main_hand)
    
    # ... rest of attack logic ...

def _animate_ranged_attack(self, target, weapon):
    """Animate arrow/bolt flying to target."""
    import tcod.line
    from visual_effect_queue import get_effect_queue
    
    # Calculate arrow path
    path = list(tcod.line.bresenham(
        self.owner.x, self.owner.y,
        target.x, target.y
    ))
    
    # Queue arrow animation
    effect_queue = get_effect_queue()
    
    # Arrow character based on direction
    dx = target.x - self.owner.x
    dy = target.y - self.owner.y
    
    if abs(dx) > abs(dy):
        arrow_char = ord('-')  # Horizontal
    else:
        arrow_char = ord('|')  # Vertical
    
    effect_queue.queue_projectile(
        path=path,
        char=arrow_char,
        color=(139, 69, 19),  # Brown arrow
        frame_duration=0.03  # Fast!
    )
```

---

## 🎮 **Phase 5: UI Integration**
**Time: 30 minutes**

### **5.1 Throw Item Selection**
**File:** `ui/menus.py`

Add inventory selection for throwing (reuse existing inventory menu):

```python
def throw_item_menu(con, header, player, inventory_width, screen_width, screen_height):
    """Show inventory for selecting item to throw."""
    # Reuse inventory_menu but with different header
    return inventory_menu(
        con, 
        "Select item to throw:", 
        player, 
        inventory_width, 
        screen_width, 
        screen_height
    )
```

### **5.2 Targeting for Throws**
- Reuse existing targeting system (same as spells)
- Show crosshair
- Click to throw

---

## 🧪 **Phase 6: Testing & Polish**
**Time: 30 minutes**

### **Test Cases:**
1. ✅ Throw healing potion at ally → heals them
2. ✅ Throw paralysis potion at enemy → paralyzes
3. ✅ Throw dagger at enemy → deals damage
4. ✅ Throw at wall → projectile stops, item drops
5. ✅ Throw beyond range → stops at max range
6. ✅ Bow attack → arrow animation plays
7. ✅ Crossbow attack → bolt animation plays
8. ✅ Projectile respects camera (works when scrolled)

### **Polish:**
- Sound effects (if we add audio later)
- Splash damage for AOE potions?
- Different projectile chars for different items
- Throwing takes 1 turn (turn economy)

---

## 📋 **Implementation Checklist**

### Phase 1: Projectile Animation (1h)
- [ ] Add PROJECTILE effect type to EffectType enum
- [ ] Implement `_play_projectile()` method
- [ ] Add `queue_projectile()` helper to VisualEffectQueue
- [ ] Test projectile animation in isolation

### Phase 2: Throw Action (30m)
- [ ] Add 't' key handler to input_handlers.py
- [ ] Add THROW_SELECT_ITEM and THROW_TARGETING game states
- [ ] Add `_handle_throw_action()` to game_actions.py
- [ ] Wire up state transitions

### Phase 3: Throw Logic (1h)
- [ ] Create throwing.py module
- [ ] Implement `calculate_throw_path()`
- [ ] Implement `throw_item()` main function
- [ ] Implement `_throw_potion()` for consumables
- [ ] Implement `_throw_weapon()` for equipment
- [ ] Test potion throwing
- [ ] Test weapon throwing

### Phase 4: Bow Animation (30m)
- [ ] Add ranged weapon detection to fighter.py
- [ ] Implement `_animate_ranged_attack()`
- [ ] Test bow animations
- [ ] Test crossbow animations

### Phase 5: UI Integration (30m)
- [ ] Add throw item selection menu
- [ ] Integrate targeting system
- [ ] Test full throw flow (select → target → throw)

### Phase 6: Testing (30m)
- [ ] Write unit tests for throw calculations
- [ ] Write integration tests for throw actions
- [ ] Playtest all scenarios
- [ ] Polish and bug fixes

---

## 🎯 **Total Time Estimate: 4 hours**

## 🎁 **Benefits**

1. **Projectile Animation** - Visual feedback for ranged combat
2. **Emergent Gameplay** - Throw healing at allies, poison at enemies
3. **Tactical Depth** - Positioning matters, range matters
4. **Bow Enhancement** - Existing bows become visually satisfying
5. **Foundation** - Easy to add more throwables (rocks, bombs, etc.)

---

## 🔥 **Bonus Ideas** (Future)

- **Splash Damage** - AOE potions affect 3x3 area
- **Bouncing** - Some items bounce off walls
- **Critical Throws** - Nat 20 = double damage/effect
- **Throwing Skill** - STR affects throw range/damage
- **Ammo System** - Arrows consumed on bow attacks
- **Quiver Slot** - Dedicated arrow storage

---

**Ready to implement!** 🚀
