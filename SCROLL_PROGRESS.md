# Scroll Implementation Progress

## ✅ COMPLETE (5/8 scrolls)
1. **Haste** - SpeedEffect for 30 turns ✅
2. **Blink** - Short-range tactical teleport (5 tiles) ✅  
3. **Magic Mapping** - Reveals entire dungeon level ✅
4. **Light** - Reveals all visible tiles in FOV ✅
5. **Earthquake** - AOE damage (3d6, radius 3) - Uses existing AOE handler ✅

## ⏳ IN PROGRESS (2/8 scrolls)
6. **Fear** - AOE terror effect (needs implementation)
7. **Detect Monster** - Temp monster detection (needs implementation)

## ✅ ALREADY DONE
8. **Identify** - 10-turn identification buff (implemented in v3.11.0) ✅

## 📝 TODO
- Register all scrolls in initialize_new_game.py
- Add spawn rates to game_constants.py
- Write tests for new scrolls
- Playtest!

## Next Steps
1. Implement Fear scroll (AOE that makes enemies flee)
2. Skip Detect Monster for now (complex, can be added later)
3. Register scrolls + spawn rates
4. Test!
