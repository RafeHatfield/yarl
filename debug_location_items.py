#!/usr/bin/env python3
"""Debug tool to check what items are at a specific location.

This can help identify if items are being dropped but hidden under corpses
or other entities.
"""

def debug_location_items(entities, x, y):
    """Debug what entities are at a specific location.
    
    Args:
        entities: List of all game entities
        x, y: Coordinates to check
    """
    print(f"🔍 Checking location ({x}, {y}):")
    
    items_at_location = []
    monsters_at_location = []
    other_at_location = []
    
    for entity in entities:
        if entity.x == x and entity.y == y:
            if hasattr(entity, 'item') and entity.item:
                items_at_location.append(entity)
            elif hasattr(entity, 'fighter') and entity.fighter:
                monsters_at_location.append(entity)
            else:
                other_at_location.append(entity)
    
    print(f"  📦 Items: {len(items_at_location)}")
    for item in items_at_location:
        print(f"    - {item.name} ('{item.char}')")
    
    print(f"  👹 Monsters/Corpses: {len(monsters_at_location)}")
    for monster in monsters_at_location:
        print(f"    - {monster.name} ('{monster.char}')")
    
    print(f"  🔧 Other: {len(other_at_location)}")
    for other in other_at_location:
        print(f"    - {other.name} ('{other.char}')")
    
    total = len(items_at_location) + len(monsters_at_location) + len(other_at_location)
    if total == 0:
        print("  ❌ Nothing found at this location")
    elif total > 1:
        print(f"  ⚠️  Multiple entities at same location - items might be hidden!")
    
    return items_at_location, monsters_at_location, other_at_location


# Example usage for testing
if __name__ == "__main__":
    print("This is a debug utility.")
    print("In the actual game, you would call:")
    print("debug_location_items(game_state.entities, monster_x, monster_y)")
