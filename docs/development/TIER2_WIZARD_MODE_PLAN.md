# 🧙 Tier 2: Wizard Mode Implementation Plan

## Overview

**Goal**: Add in-game debug menu for interactive testing during gameplay

**Why**: Tier 1 flags require restarting game. Wizard mode allows on-the-fly debugging.

**Estimated Time**: 6-8 hours

---

## Features to Implement

### Phase 1: Core Infrastructure (2 hours)
1. **Wizard Mode Toggle**
   - Add `--wizard` command-line flag
   - Store in `TestingConfig.wizard_mode`
   - Display indicator in sidebar when active

2. **Wizard Menu Screen**
   - Create `screens/wizard_menu.py`
   - Similar to inventory menu
   - Press `&` (Shift+7) or F12 to open

3. **Input Handling**
   - Add wizard commands to `input_handlers.py`
   - Only active when `wizard_mode = True`
   - Visual indicator that wizard mode is active

### Phase 2: Essential Commands (2 hours)
**Most Useful for Testing**:

1. **`H` - Heal to Full**
   ```python
   player.fighter.hp = player.fighter.max_hp
   message_log.add_message(MB.custom("🧙 WIZARD: Healed to full HP", (138, 43, 226)))
   ```

2. **`L` - Teleport to Level**
   ```python
   # Prompt for level number
   target_level = get_number_input("Teleport to level:", 1, 25)
   # Call game_map.next_floor() repeatedly
   ```

3. **`R` - Reveal Map**
   ```python
   for x in range(game_map.width):
       for y in range(game_map.height):
           game_map.tiles[x][y].explored = True
   ```

4. **`G` - Toggle God Mode**
   ```python
   config.god_mode = not config.god_mode
   status = "ENABLED" if config.god_mode else "DISABLED"
   message_log.add_message(MB.custom(f"🧙 WIZARD: God Mode {status}", (138, 43, 226)))
   ```

5. **`X` - Gain XP**
   ```python
   xp_amount = 100  # Or prompt for amount
   player.level.add_xp(xp_amount)
   message_log.add_message(MB.custom(f"🧙 WIZARD: Gained {xp_amount} XP", (138, 43, 226)))
   ```

### Phase 3: Entity Spawning (2 hours)
**For Testing Ghost Guide & Monsters**:

1. **`N` - Spawn NPC**
   ```python
   # Prompt for NPC type: "guide", etc.
   npc_type = get_text_input("NPC type:")
   x, y = find_empty_spot_near_player()
   npc = entity_factory.create_unique_npc(npc_type, x, y, game_map.dungeon_level)
   entities.append(npc)
   ```

2. **`M` - Spawn Monster**
   ```python
   # Prompt for monster type: "orc", "troll", etc.
   monster_type = get_text_input("Monster type:")
   x, y = find_empty_spot_near_player()
   monster = entity_factory.create_monster(monster_type, x, y)
   entities.append(monster)
   ```

3. **`I` - Spawn Item**
   ```python
   # Prompt for item type: "healing_potion", "sword", etc.
   item_type = get_text_input("Item type:")
   x, y = player.x, player.y
   item = entity_factory.create_spell_item(item_type, x, y)
   entities.append(item)
   ```

### Phase 4: Knowledge System (1 hour)
**For Testing Phase 3 Victory Conditions**:

1. **`K` - Unlock Knowledge**
   ```python
   # Show list of available knowledge:
   # 1. entity_true_name_zhyraxion
   # 2. [future knowledge items]
   choice = get_menu_choice(knowledge_list)
   player.victory.unlock_knowledge(choice)
   message_log.add_message(MB.custom(f"🧙 WIZARD: Unlocked {choice}", (138, 43, 226)))
   ```

### Phase 5: Quick Commands (1 hour)
**Keyboard Shortcuts (No Menu)**:

- `Ctrl+H` - Heal to full (instant)
- `Ctrl+G` - Toggle god mode (instant)
- `Ctrl+R` - Reveal map (instant)
- `Ctrl+K` - Kill all monsters (instant)
- `Ctrl+L` - Level up (instant)
- `Ctrl+T` - Teleport to cursor (if in FOV)

---

## Implementation Details

### File Structure

```
screens/
  wizard_menu.py          # Main wizard menu screen
  wizard_spawner.py       # Entity spawning submenu

config/
  testing_config.py       # Add wizard_mode flag

engine.py                 # Add --wizard flag parsing

input_handlers.py         # Add wizard command keys

wizard/
  __init__.py
  commands.py            # Wizard command implementations
  helpers.py             # Helper functions (find_empty_spot, etc.)
```

### Color Scheme

All wizard messages use **purple** color to distinguish from game messages:
```python
WIZARD_COLOR = (138, 43, 226)  # Purple
MB.custom("🧙 WIZARD: ...", WIZARD_COLOR)
```

### Safety Features

1. **Prevent Save in Wizard Mode**
   ```python
   if get_testing_config().wizard_mode:
       message_log.add_message(MB.warning("Cannot save in Wizard Mode!"))
       return
   ```

2. **Prevent High Scores**
   ```python
   if get_testing_config().wizard_mode:
       # Don't record score
       return
   ```

3. **Visual Indicator**
   ```python
   # In sidebar, show:
   if wizard_mode:
       console.print(x, y, "🧙 WIZARD MODE", fg=WIZARD_COLOR)
   ```

---

## Testing Strategy

### Unit Tests
```python
# tests/test_wizard_mode.py

def test_wizard_mode_flag():
    config = TestingConfig()
    assert config.wizard_mode == False
    
    config.wizard_mode = True
    assert config.wizard_mode == True

def test_heal_command():
    player = create_test_player()
    player.fighter.hp = 10
    
    wizard_heal(player)
    
    assert player.fighter.hp == player.fighter.max_hp

def test_toggle_god_mode():
    config = TestingConfig()
    initial = config.god_mode
    
    wizard_toggle_god_mode(config)
    
    assert config.god_mode != initial
```

### Integration Tests
```python
# tests/test_wizard_integration.py

def test_wizard_spawning_npc():
    """Test spawning Ghost Guide via wizard mode."""
    player, entities, game_map = create_test_game()
    
    # Spawn guide
    wizard_spawn_npc('ghost_guide', player.x + 1, player.y, entities, game_map)
    
    # Verify guide exists
    guide = next(e for e in entities if hasattr(e, 'is_guide') and e.is_guide)
    assert guide is not None
    assert guide.name == "Ghostly Guide"

def test_wizard_unlock_knowledge():
    """Test unlocking knowledge via wizard mode."""
    player = create_test_player()
    
    wizard_unlock_knowledge(player, 'entity_true_name_zhyraxion')
    
    assert player.victory.knows_entity_true_name == True
```

---

## User Experience

### Opening Wizard Menu

```
Press & (Shift+7) to open

╔════════════════════════════════════╗
║         🧙 WIZARD MODE             ║
╠════════════════════════════════════╣
║ H - Heal to Full HP                ║
║ L - Teleport to Level...           ║
║ R - Reveal Entire Map              ║
║ G - Toggle God Mode [OFF]          ║
║ X - Gain XP...                     ║
║ -----------------------------------║
║ N - Spawn NPC...                   ║
║ M - Spawn Monster...               ║
║ I - Spawn Item...                  ║
║ -----------------------------------║
║ K - Unlock Knowledge...            ║
║ -----------------------------------║
║ ESC - Close Menu                   ║
╚════════════════════════════════════╝
```

### Spawning NPC (Example Flow)

```
1. Press & to open wizard menu
2. Press N for "Spawn NPC"
3. Submenu appears:

   ╔══════════════════════════════╗
   ║    Spawn NPC                 ║
   ╠══════════════════════════════╣
   ║ 1. Ghost Guide               ║
   ║ 2. [Future NPC]              ║
   ║                              ║
   ║ ESC - Cancel                 ║
   ╚══════════════════════════════╝

4. Press 1
5. Message: "🧙 WIZARD: Spawned Ghostly Guide"
6. NPC appears next to player
```

---

## Advantages Over Tier 1

| Feature | Tier 1 (Flags) | Tier 2 (Wizard) |
|---------|----------------|-----------------|
| **Change settings** | Restart game | Instant |
| **Test Guide** | --start-level 5 | Press N, spawn |
| **Heal** | Die & reload | Press H |
| **Level testing** | Restart at level | Press L, go there |
| **Knowledge unlock** | Edit save file | Press K |
| **Multiple tests** | Restart each time | All in one session |

**Wizard Mode = 10x faster testing!**

---

## Implementation Order

### Session 1: Foundation (2 hours)
1. ✅ Add `--wizard` flag to `engine.py`
2. ✅ Add `wizard_mode` to `TestingConfig`
3. ✅ Create `screens/wizard_menu.py`
4. ✅ Add `&` key to `input_handlers.py`
5. ✅ Show "🧙 WIZARD MODE" indicator in sidebar

### Session 2: Core Commands (2 hours)
1. ✅ Implement Heal (H)
2. ✅ Implement Toggle God Mode (G)
3. ✅ Implement Reveal Map (R)
4. ✅ Implement Gain XP (X)
5. ✅ Test each command manually

### Session 3: Entity Spawning (2 hours)
1. ✅ Implement Spawn NPC (N)
2. ✅ Create NPC submenu
3. ✅ Add Ghost Guide to spawn list
4. ✅ Test spawning Ghost Guide at level 1

### Session 4: Advanced Features (2 hours)
1. ✅ Implement Unlock Knowledge (K)
2. ✅ Implement Teleport to Level (L)
3. ✅ Add quick commands (Ctrl+H, etc.)
4. ✅ Write comprehensive tests

---

## Success Criteria

### Must Have ✅
- [ ] `--wizard` flag enables wizard mode
- [ ] `&` key opens wizard menu
- [ ] Can heal to full HP
- [ ] Can toggle god mode
- [ ] Can spawn Ghost Guide
- [ ] Can unlock knowledge
- [ ] Can reveal map
- [ ] Visual indicator shows wizard mode active
- [ ] Cannot save in wizard mode

### Nice to Have 🎯
- [ ] Quick commands (Ctrl+H, etc.)
- [ ] Spawn any monster/item
- [ ] Teleport to cursor
- [ ] Kill all monsters command
- [ ] Comprehensive unit tests

---

## Future Enhancements (Tier 3+)

After Tier 2 is complete, we can add:
- Save states (quick save/load for testing)
- Automated playthroughs (record & replay)
- Performance profiling
- Map editor
- Dialogue editor

---

## Commit Strategy

Each phase gets its own commit:
1. `🧙 Tier 2: Add wizard mode flag and menu infrastructure`
2. `🧙 Tier 2: Implement core wizard commands (heal, god mode, reveal)`
3. `🧙 Tier 2: Add entity spawning (NPC, monsters, items)`
4. `🧙 Tier 2: Add knowledge system and advanced commands`
5. `🧪 Tier 2: Add comprehensive wizard mode tests`
6. `📝 Tier 2: Document wizard mode completion`

---

## Ready to Start!

**First Step**: Add `--wizard` flag and create basic menu infrastructure.

Let's do this! 🧙✨

