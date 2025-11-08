# Portal System Playtest Checklist

## Overview
The player now starts with a **Wand of Portals** for testing Phase A implementation.

## Setup Status
✅ **READY FOR PLAYTEST**
- Player starts with Wand of Portals in inventory (slot `b`)
- Healing Potion also in starting inventory (slot `a`)
- Portal Placer component properly attached to wand
- All 33 Phase A tests passing

## Playtest Objectives

### 1. Wand Acquisition & UI
- [ ] Wand appears in inventory list
- [ ] Can see wand name "Wand of Portals" with proper color (cyan/teal)
- [ ] Wand can be selected/highlighted in inventory

### 2. Portal Targeting Mode
- [ ] Press `b` to select wand from inventory (or use configured binding)
- [ ] Game enters targeting mode (cursor changes, message shown)
- [ ] Can move cursor with mouse/keyboard
- [ ] ESC cancels targeting mode

### 3. Portal Placement - Entrance
- [ ] Click to place entrance portal (blue Θ)
- [ ] Portal appears at cursor location
- [ ] Game prompts for exit portal placement
- [ ] Message confirms "Entrance portal placed at..."

### 4. Portal Placement - Exit
- [ ] Click to place exit portal (orange Θ)
- [ ] Exit portal appears at new location
- [ ] Game returns to normal play
- [ ] Both portals visible on map

### 5. Portal Teleportation
- [ ] Walk onto entrance portal → player teleports to exit
- [ ] Walk onto exit portal → player teleports to entrance
- [ ] Teleportation is instant
- [ ] No turn cost for teleportation (or verify intended behavior)

### 6. Inventory Interaction
- [ ] Right-click on deployed portal → "Pick up [Portal]"
- [ ] Portal enters inventory
- [ ] Picking up entrance blocks exit teleportation
- [ ] Picking up exit blocks entrance teleportation

### 7. Portal Redeployment
- [ ] Use wand again (press `b`) while carrying a portal
- [ ] Old portals disappear
- [ ] New portal pair can be placed
- [ ] Wand never runs out of charges

### 8. Combat & Movement
- [ ] Monsters path around portals naturally
- [ ] No AI errors when portals on map
- [ ] Player can use portals tactically in combat
- [ ] Portals don't break existing movement systems

### 9. Edge Cases
- [ ] Deploy portals in narrow corridors → no pathfinding issues
- [ ] Deploy portals across level transitions → verify cleanup
- [ ] Carry max inventory + portal → inventory slots work correctly
- [ ] Multiple portals on same tile → no overlap issues

## Known Limitations (Phase A)
- Monsters may not intelligently use portals (Phase B feature)
- Portal rendering may need fine-tuning (Phase B feature)
- No visual effect on teleportation yet (Phase B feature)
- Input routing depends on full integration (verify works in main game flow)

## Bug Reporting
If you encounter issues:
1. Note the specific action that failed
2. Check console for error messages
3. Verify the Phase A tests still pass
4. Report in session notes

## Next Steps After Playtest
- Phase B: Advanced mechanics (terrain interactions, monster AI)
- Polish: Visual effects, sound, UI refinements
- Integration: Full input/render pipeline testing

