#!/usr/bin/env python3
"""Debug tool to check monster information and identify character/name mismatches.

This script can be used to diagnose issues where monsters display the wrong
character or have mismatched names in combat logs.
"""

from config.entity_registry import load_entity_config
from config.entity_factory import get_entity_factory
from config.testing_config import set_testing_mode


def check_monster_definitions():
    """Check all monster definitions for consistency."""
    print("🔍 Checking monster definitions...")
    
    load_entity_config()
    from config.entity_registry import get_entity_registry
    
    registry = get_entity_registry()
    
    print("\n📋 Monster Definitions:")
    for monster_id in registry.get_all_monster_ids():
        monster_def = registry.get_monster(monster_id)
        print(f"  {monster_id}: name=\"{monster_def.name}\", char=\"{monster_def.char}\", color={monster_def.color}")


def test_monster_creation():
    """Test monster creation for consistency."""
    print("\n🧪 Testing monster creation...")
    
    factory = get_entity_factory()
    
    for monster_type in ['orc', 'troll']:
        monster = factory.create_monster(monster_type, 0, 0)
        if monster:
            print(f"  {monster_type} -> name=\"{monster.name}\", char=\"{monster.char}\", color={monster.color}")
            
            # Check for mismatches
            expected_name = monster_type.title()
            if monster.name != expected_name:
                print(f"    ⚠️  NAME MISMATCH: expected \"{expected_name}\", got \"{monster.name}\"")
        else:
            print(f"  {monster_type} -> FAILED TO CREATE")


def test_in_game_scenario():
    """Test a realistic in-game scenario."""
    print("\n🎮 Testing in-game scenario...")
    
    set_testing_mode(True)
    
    from map_objects.game_map import GameMap
    from map_objects.rectangle import Rect
    
    # Test at different dungeon levels
    for level in [1, 3, 5]:
        print(f"\n  Dungeon Level {level}:")
        game_map = GameMap(20, 20, dungeon_level=level)
        entities = []
        room = Rect(5, 5, 10, 10)
        
        # Spawn a few monsters
        for i in range(3):
            initial_count = len(entities)
            game_map.place_entities(room, entities)
            new_entities = entities[initial_count:]
            
            for entity in new_entities:
                if hasattr(entity, 'fighter') and entity.fighter:
                    print(f"    Monster: \"{entity.name}\" ('{entity.char}') at ({entity.x},{entity.y})")
                    
                    # Check for known mismatches
                    if entity.char == 'o' and entity.name != 'Orc':
                        print(f"      🚨 MISMATCH: 'o' character but name is \"{entity.name}\"")
                    elif entity.char == 'T' and entity.name != 'Troll':
                        print(f"      🚨 MISMATCH: 'T' character but name is \"{entity.name}\"")


if __name__ == "__main__":
    print("🐛 Monster Debug Tool")
    print("=" * 50)
    
    try:
        check_monster_definitions()
        test_monster_creation()
        test_in_game_scenario()
        
        print("\n✅ Debug complete!")
        print("\nIf you see a mismatch in the actual game:")
        print("1. Note the exact dungeon level")
        print("2. Note what you see vs what the combat log says")
        print("3. Check if the monster was recently killed/replaced")
        print("4. Try saving and reloading to see if it persists")
        
    except Exception as e:
        print(f"\n❌ Error during debug: {e}")
        import traceback
        traceback.print_exc()
