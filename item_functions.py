"""Item use functions and spell effects.

This module contains functions that are called when items are used,
including healing potions, spell scrolls, and other consumable items.
Each function implements the specific effect of using that item type.
"""

import tcod as libtcod
import tcod.libtcodpy as libtcodpy
import math

from components.ai import ConfusedMonster
from components.component_registry import ComponentType
from game_messages import Message
from fov_functions import map_is_in_fov
from render_functions import RenderOrder
from visual_effects import show_fireball, show_lightning, show_dragon_fart


def heal(*args, **kwargs):
    """Heal the target entity by a specified amount.

    Args:
        *args: First argument should be the entity to heal
        **kwargs: Should contain 'amount' key with healing value

    Returns:
        list: List of result dictionaries with consumption and message info
    """
    entity = args[0]
    amount = kwargs.get("amount")

    results = []

    if entity.fighter.hp == entity.fighter.max_hp:
        results.append(
            {
                "consumed": False,
                "message": Message("You are already at full health", (255, 255, 0)),
            }
        )
    else:
        entity.fighter.heal(amount)
        results.append(
            {
                "consumed": True,
                "message": Message("Your wounds start to feel better!", (0, 255, 0)),
            }
        )

    return results


def cast_lightning(*args, **kwargs):
    """Cast a lightning spell that targets the closest enemy.

    Args:
        *args: First argument should be the caster entity
        **kwargs: Should contain 'entities', 'fov_map', 'damage', and 'maximum_range'

    Returns:
        list: List of result dictionaries with consumption, targeting, and message info
    """
    caster = args[0]
    entities = kwargs.get("entities")
    fov_map = kwargs.get("fov_map")
    damage = kwargs.get("damage")
    maximum_range = kwargs.get("maximum_range")

    results = []

    target = None
    closest_distance = maximum_range + 1

    # Handle None entities list
    if entities is None:
        entities = []

    for entity in entities:
        if (
            entity.fighter
            and entity != caster
            and map_is_in_fov(fov_map, entity.x, entity.y)
        ):
            distance = caster.distance_to(entity)

            if distance < closest_distance:
                target = entity
                closest_distance = distance

    if target:
        # VISUAL EFFECT: Show lightning path! ⚡
        lightning_path = []
        # Calculate straight line from caster to target using Bresenham's line algorithm
        x0, y0 = caster.x, caster.y
        x1, y1 = target.x, target.y
        
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        x, y = x0, y0
        while True:
            lightning_path.append((x, y))
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
        
        # Show the lightning zap!
        show_lightning(lightning_path)
        
        results.append(
            {
                "consumed": True,
                "target": target,
                "message": Message(
                    "A lighting bolt strikes the {0} with a loud thunder! The damage is {1}".format(
                        target.name, damage
                    )
                ),
            }
        )
        results.extend(target.fighter.take_damage(damage))
    else:
        results.append(
            {
                "consumed": False,
                "target": None,
                "message": Message("No enemy is close enough to strike.", (255, 0, 0)),
            }
        )

    return results


def cast_fireball(*args, **kwargs):
    """Cast a fireball spell that damages all entities in a radius.
    
    Creates a fiery explosion that deals immediate damage to all entities
    in the blast radius. Additionally leaves burning ground hazards that
    persist for 3 turns and deal damage to entities standing on them.

    Args:
        *args: First argument should be the caster entity
        **kwargs: Should contain 'entities', 'fov_map', 'damage', 'radius',
                 'target_x', 'target_y', and optionally 'game_map'

    Returns:
        list: List of result dictionaries with consumption and damage results
    """
    entities = kwargs.get("entities")
    fov_map = kwargs.get("fov_map")
    damage = kwargs.get("damage")
    radius = kwargs.get("radius")
    target_x = kwargs.get("target_x")
    target_y = kwargs.get("target_y")
    game_map = kwargs.get("game_map")

    results = []

    # Handle None entities list
    if entities is None:
        entities = []

    if not map_is_in_fov(fov_map, target_x, target_y):
        results.append(
            {
                "consumed": False,
                "message": Message(
                    "You cannot target a tile outside your field of view.",
                    (255, 255, 0),
                ),
            }
        )
        return results

    results.append(
        {
            "consumed": True,
            "message": Message(
                "The fireball explodes, burning everything within {0} tiles!".format(
                    radius
                ),
                (255, 127, 0),
            ),
        }
    )
    
    # VISUAL EFFECT: Show explosion area! 🔥
    explosion_tiles = []
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            # Check if tile is within circular radius
            if math.sqrt(dx**2 + dy**2) <= radius:
                tile_x = target_x + dx
                tile_y = target_y + dy
                explosion_tiles.append((tile_x, tile_y))
    
    # Show the fiery explosion!
    show_fireball(explosion_tiles)
    
    # Create persistent fire hazards on all explosion tiles
    if game_map and hasattr(game_map, 'hazard_manager') and game_map.hazard_manager:
        from components.ground_hazard import GroundHazard, HazardType
        
        for tile_x, tile_y in explosion_tiles:
            # Create a fire hazard with damage decay over 5 turns
            fire_hazard = GroundHazard(
                hazard_type=HazardType.FIRE,
                x=tile_x,
                y=tile_y,
                base_damage=12,  # 12 → 8 → 4 damage over 5 turns
                remaining_turns=5,
                max_duration=5,
                source_name="Fireball"
            )
            game_map.hazard_manager.add_hazard(fire_hazard)

    for entity in entities:
        # Damage ALL entities in radius, including the caster!
        # Fireball is dangerous - be careful where you cast it!
        if entity.distance(target_x, target_y) <= radius and entity.fighter:
            results.append(
                {
                    "message": Message(
                        "The {0} gets burned for {1} hit points.".format(
                            entity.name, damage
                        ),
                        (255, 127, 0),
                    )
                }
            )
            results.extend(entity.fighter.take_damage(damage))

    return results


def cast_confuse(*args, **kwargs):
    """Cast a confusion spell on a target entity.

    Args:
        *args: First argument should be the caster entity
        **kwargs: Should contain 'entities', 'fov_map', 'target_x', and 'target_y'

    Returns:
        list: List of result dictionaries with consumption and confusion results
    """
    entities = kwargs.get("entities")
    fov_map = kwargs.get("fov_map")
    target_x = kwargs.get("target_x")
    target_y = kwargs.get("target_y")

    results = []

    if not map_is_in_fov(fov_map, target_x, target_y):
        results.append(
            {
                "consumed": False,
                "message": Message(
                    "You cannot target a tile outside your field of view.",
                    (255, 255, 0),
                ),
            }
        )
        return results

    for entity in entities:
        if entity.x == target_x and entity.y == target_y and entity.ai:
            confused_ai = ConfusedMonster(entity.ai, 10)

            confused_ai.owner = entity
            entity.ai = confused_ai

            results.append(
                {
                    "consumed": True,
                    "message": Message(
                        "The eyes of the {0} look vacant, as he starts to stumble around!".format(
                            entity.name
                        ),
                        (63, 255, 63),  # light_green RGB
                    ),
                }
            )

            break
    else:
        results.append(
            {
                "consumed": False,
                "message": Message(
                    "There is no targetable enemy at that location.", (255, 255, 0)
                ),
            }
        )

    return results


def enhance_weapon(*args, **kwargs):
    """Enhance the equipped weapon's damage range.
    
    Args:
        *args: First argument should be the entity using the scroll
        **kwargs: Should contain 'min_bonus' and 'max_bonus' for damage enhancement
        
    Returns:
        list: List of result dictionaries with consumption and message info
    """
    entity = args[0]
    min_bonus = kwargs.get("min_bonus", 1)
    max_bonus = kwargs.get("max_bonus", 2)
    
    results = []
    
    # Check if player has equipment and a weapon equipped
    # For backward compatibility, check direct attribute first (for Mock objects in tests)
    equipment = getattr(entity, 'equipment', None)
    if not equipment:
        equipment = entity.components.get(ComponentType.EQUIPMENT)
    if (equipment and equipment.main_hand and 
        (equipment.main_hand.components.has(ComponentType.EQUIPPABLE) or hasattr(equipment.main_hand, 'equippable'))):
        weapon = equipment.main_hand
        old_min = weapon.equippable.damage_min
        old_max = weapon.equippable.damage_max
        
        # Only enhance weapons that have damage ranges
        if old_min > 0 and old_max > 0:
            weapon.equippable.modify_damage_range(min_bonus, max_bonus)
            
            results.append({
                "consumed": True,
                "message": Message(
                    f"Your {weapon.name} glows briefly! Damage enhanced from "
                    f"({old_min}-{old_max}) to ({weapon.equippable.damage_min}-{weapon.equippable.damage_max}).",
                    (0, 255, 0)
                )
            })
        else:
            results.append({
                "consumed": False,
                "message": Message(
                    f"The {weapon.name} cannot be enhanced further.", (255, 255, 0)
                )
            })
    else:
        results.append({
            "consumed": False,
            "message": Message(
                "You must have a weapon equipped to use this scroll.", (255, 255, 0)
            )
        })
    
    return results


def enhance_armor(*args, **kwargs):
    """Enhance a random equipped armor piece's AC bonus.
    
    Args:
        *args: First argument should be the entity using the scroll
        **kwargs: Should contain 'bonus' key for AC enhancement (default +1)
        
    Returns:
        list: List of result dictionaries with consumption and message info
    """
    entity = args[0]
    bonus = kwargs.get("bonus", 1)  # Default +1 AC
    
    results = []
    
    # Check if player has equipment
    # For backward compatibility, check direct attribute first (for Mock objects in tests)
    equipment = getattr(entity, 'equipment', None)
    if not equipment:
        equipment = entity.components.get(ComponentType.EQUIPMENT)
    if not equipment:
        results.append({
            "consumed": False,
            "message": Message(
                "You must have armor equipped to use this scroll.", (255, 255, 0)
            )
        })
        return results
    
    # Collect all equipped armor pieces (any equipment slot with armor_class_bonus)
    armor_pieces = []
    equipment_slots = [
        ('head', entity.equipment.head),
        ('chest', entity.equipment.chest),
        ('feet', entity.equipment.feet),
        ('off_hand', entity.equipment.off_hand),
    ]
    
    for slot_name, item in equipment_slots:
        if item and item.components.has(ComponentType.EQUIPPABLE):
            # Check if this item has armor_class_bonus (is an armor piece)
            if hasattr(item.equippable, 'armor_class_bonus') and item.equippable.armor_class_bonus > 0:
                armor_pieces.append((slot_name, item))
    
    if not armor_pieces:
        results.append({
            "consumed": False,
            "message": Message(
                "You must have armor equipped to use this scroll.", (255, 255, 0)
            )
        })
        return results
    
    # Randomly select one armor piece to enhance
    import random
    slot_name, armor = random.choice(armor_pieces)
    
    old_ac = armor.equippable.armor_class_bonus
    
    # Enhance the armor's AC bonus
    armor.equippable.armor_class_bonus += bonus
    
    results.append({
        "consumed": True,
        "message": Message(
            f"Your {armor.name} shimmers with magical energy! AC bonus increased from "
            f"+{old_ac} to +{armor.equippable.armor_class_bonus}.",
            (0, 255, 0)
        )
    })
    
    return results


def cast_invisibility(*args, **kwargs):
    """Cast invisibility on the caster, making them invisible to most monsters.
    
    The invisibility effect lasts for a limited number of turns and breaks
    when the player attacks. This enables tactical gameplay where monsters
    can be made to fight each other.
    
    Args:
        *args: First argument should be the entity casting invisibility
        **kwargs: Should contain 'duration' key with number of turns (default 10)
        
    Returns:
        list: List of result dictionaries with consumption and message info
    """
    entity = args[0]
    duration = kwargs.get("duration", 10)
    
    results = []
    
    # Check if already invisible
    if hasattr(entity, 'invisible') and entity.invisible:
        results.append({
            "consumed": False,
            "message": Message("You are already invisible!", (255, 255, 0))
        })
        return results
    
    # Apply invisibility effect
    from components.status_effects import InvisibilityEffect
    invisibility_effect = InvisibilityEffect(duration=duration, owner=entity)
    
    # Add the status effect to the entity
    effect_results = entity.add_status_effect(invisibility_effect)
    results.extend(effect_results)
    
    # Add success message
    results.append({
        "consumed": True,
        "message": Message(
            f"{entity.name} becomes invisible for {duration} turns!",
            (200, 200, 255)  # Light blue
        )
    })
    
    return results


def cast_teleport(*args, **kwargs):
    """Teleport the caster to a target location.
    
    Has a 10% chance to misfire and teleport to a random location instead.
    
    Args:
        *args: First argument should be the caster entity
        **kwargs: Contains 'entities', 'game_map', 'target_x', 'target_y'
        
    Returns:
        list: List of result dictionaries with consumption and message info
    """
    from random import randint, random
    
    entity = args[0]
    entities = kwargs.get("entities", [])
    game_map = kwargs.get("game_map")
    target_x = kwargs.get("target_x")
    target_y = kwargs.get("target_y")
    
    results = []
    
    # 10% chance of misfire!
    if random() < 0.10:
        # Misfire - teleport to random location
        max_attempts = 100
        for _ in range(max_attempts):
            random_x = randint(1, game_map.width - 2)
            random_y = randint(1, game_map.height - 2)
            
            # Check if location is valid (walkable and unoccupied)
            if not game_map.tiles[random_x][random_y].blocked:
                # Check if any entity is blocking this position
                blocking_entity = None
                for other_entity in entities:
                    if other_entity.blocks and other_entity.x == random_x and other_entity.y == random_y:
                        blocking_entity = other_entity
                        break
                
                if not blocking_entity:
                    # Valid random location found!
                    entity.x = random_x
                    entity.y = random_y
                    
                    # Apply disorientation effect (3-5 turns of random movement)
                    disorientation_duration = randint(3, 5)
                    from components.status_effects import DisorientationEffect
                    disorientation_effect = DisorientationEffect(
                        duration=disorientation_duration,
                        owner=entity
                    )
                    
                    # Add the status effect
                    if hasattr(entity, 'add_status_effect'):
                        effect_results = entity.add_status_effect(disorientation_effect)
                        results.extend(effect_results)
                    
                    results.append({
                        "consumed": True,
                        "message": Message(
                            "The teleport spell misfires!",
                            (255, 165, 0)  # Orange - warning color
                        )
                    })
                    return results
        
        # Couldn't find valid random location - fail safely
        results.append({
            "consumed": False,
            "message": Message(
                "The teleport spell fizzles and fails!",
                (255, 255, 0)  # Yellow
            )
        })
        return results
    
    # Normal teleport to target location
    if not target_x or not target_y:
        results.append({
            "consumed": False,
            "message": Message("You must select a target location.", (255, 255, 0))
        })
        return results
    
    # Check if target location is valid
    if game_map.tiles[target_x][target_y].blocked:
        results.append({
            "consumed": False,
            "message": Message("You cannot teleport to a blocked location.", (255, 255, 0))
        })
        return results
    
    # Check if any entity is blocking the target
    for other_entity in entities:
        if other_entity.blocks and other_entity.x == target_x and other_entity.y == target_y:
            results.append({
                "consumed": False,
                "message": Message(
                    f"You cannot teleport to a location occupied by {other_entity.name}.",
                    (255, 255, 0)
                )
            })
            return results
    
    # Successful teleport!
    entity.x = target_x
    entity.y = target_y
    
    results.append({
        "consumed": True,
        "message": Message(
            "You teleport across space!",
            (128, 200, 255)  # Light cyan
        )
    })
    
    return results


def cast_shield(*args, **kwargs):
    """Cast a protective shield that boosts defense.
    
    Players get a safe +4 defense boost.
    Monsters have a 10% chance for the spell to backfire and halve their defense.
    
    Args:
        *args: First argument should be the entity casting
        **kwargs: Contains duration (default 10)
        
    Returns:
        list: List of result dictionaries with consumption and message info
    """
    entity = args[0]
    duration = kwargs.get("duration", 10)
    defense_bonus = kwargs.get("defense_bonus", 4)
    
    results = []
    
    # Create and apply the shield effect
    from components.status_effects import ShieldEffect
    shield_effect = ShieldEffect(
        duration=duration,
        owner=entity,
        defense_bonus=defense_bonus
    )
    
    # Add the status effect to the entity
    if hasattr(entity, 'add_status_effect'):
        effect_results = entity.add_status_effect(shield_effect)
        results.extend(effect_results)
    
    results.append({
        "consumed": True
    })
    
    return results


def get_cone_tiles(origin_x, origin_y, target_x, target_y, max_range=8, cone_width=45):
    """Calculate tiles in a cone spreading from origin toward target.
    
    Args:
        origin_x, origin_y: Starting point (player position)
        target_x, target_y: Direction point (where player clicked)
        max_range: Maximum distance of cone
        cone_width: Width of cone in degrees (default 45)
        
    Returns:
        set: Set of (x, y) tuples within the cone
    """
    cone_tiles = set()
    
    # Calculate direction angle from origin to target
    dx = target_x - origin_x
    dy = target_y - origin_y
    
    if dx == 0 and dy == 0:
        return cone_tiles
    
    target_angle = math.atan2(dy, dx)
    half_width = math.radians(cone_width / 2)
    
    # Check each tile within max_range
    for distance in range(1, max_range + 1):
        # Width increases with distance
        width_at_distance = int(distance * math.tan(half_width))
        
        for offset in range(-width_at_distance, width_at_distance + 1):
            # Calculate position at this distance and offset
            angle = target_angle + math.atan2(offset, distance)
            
            x = origin_x + int(distance * math.cos(angle))
            y = origin_y + int(distance * math.sin(angle))
            
            # Check if within cone angle
            tile_dx = x - origin_x
            tile_dy = y - origin_y
            tile_angle = math.atan2(tile_dy, tile_dx)
            angle_diff = abs(tile_angle - target_angle)
            
            # Normalize angle difference to [-pi, pi]
            while angle_diff > math.pi:
                angle_diff -= 2 * math.pi
            while angle_diff < -math.pi:
                angle_diff += 2 * math.pi
            
            if abs(angle_diff) <= half_width:
                cone_tiles.add((x, y))
    
    return cone_tiles


def cast_dragon_fart(*args, **kwargs):
    """Unleash a cone of noxious gas that puts enemies to sleep!
    
    Creates a directional cone of gas that spreads from the caster.
    All entities in the cone fall asleep for 20 turns (or become confused
    since we're reusing that AI). Additionally leaves toxic gas hazards that
    persist for 4 turns and deal damage to entities standing in them.
    
    Args:
        *args: First argument is the caster entity (self.owner from inventory)
        **kwargs: Contains entities, fov_map, game_map, target_x, target_y, duration
        
    Returns:
        list: List of result dictionaries with consumption and message info
    """
    entity = args[0]
    entities = kwargs.get("entities", [])
    game_map = kwargs.get("game_map")
    target_x = kwargs.get("target_x")
    target_y = kwargs.get("target_y")
    sleep_duration = kwargs.get("duration", 20)
    
    results = []
    
    if not target_x or not target_y:
        results.append({
            "consumed": False,
            "message": Message(
                "You must select a direction for the dragon fart!",
                (255, 255, 0)
            )
        })
        return results
    
    # Get all tiles in the cone
    cone_tiles = get_cone_tiles(
        entity.x, entity.y,
        target_x, target_y,
        max_range=8,
        cone_width=45
    )
    
    # VISUAL EFFECT: Show the noxious cone! 💨
    show_dragon_fart(list(cone_tiles))
    
    # Create persistent poison gas hazards on all cone tiles
    if game_map and hasattr(game_map, 'hazard_manager') and game_map.hazard_manager:
        from components.ground_hazard import GroundHazard, HazardType
        
        for tile_x, tile_y in cone_tiles:
            # Create a poison gas hazard with damage decay over 5 turns
            gas_hazard = GroundHazard(
                hazard_type=HazardType.POISON_GAS,
                x=tile_x,
                y=tile_y,
                base_damage=6,  # 6 → 4 → 2 damage over 5 turns (lower than fire)
                remaining_turns=5,
                max_duration=5,
                source_name="Dragon Fart"
            )
            game_map.hazard_manager.add_hazard(gas_hazard)
    
    # Track affected entities
    affected_entities = []
    
    # Find all entities in the cone
    for other_entity in entities:
        if other_entity == entity:
            continue  # Don't affect self
            
        if (other_entity.x, other_entity.y) in cone_tiles:
            # Check if entity has AI (is a monster)
            if other_entity.components.has(ComponentType.AI):
                affected_entities.append(other_entity)
    
    if not affected_entities:
        results.append({
            "consumed": False,
            "message": Message(
                "The noxious gas dissipates harmlessly...",
                (150, 150, 150)  # Gray
            )
        })
        return results
    
    # Epic dragon fart message FIRST! 💨
    results.append({
        "consumed": True,
        "message": Message(
            f"💨 {entity.name} unleashes a MIGHTY DRAGON FART! A cone of noxious gas spreads outward!",
            (150, 255, 100)  # Bright green
        )
    })
    
    # Apply confusion/sleep to all affected entities
    for target_entity in affected_entities:
        # Apply confusion AI (acts like sleep - random wandering)
        confused_ai = ConfusedMonster(target_entity.ai, sleep_duration)
        confused_ai.owner = target_entity
        target_entity.ai = confused_ai
        
        results.append({
            "message": Message(
                f"{target_entity.name} is overwhelmed by the noxious fumes and passes out!",
                (100, 255, 100)  # Green
            )
        })
    
    return results


def cast_raise_dead(*args, **kwargs):
    """Resurrect a corpse as a mindless zombie that attacks everything.
    
    The zombie will have doubled HP, half damage, black coloring, and will
    attack ANY adjacent entity - player, monsters, or other zombies.
    Perfect for creating chaos!
    
    Args:
        *args: First argument is the caster entity (self.owner from inventory)
        **kwargs: Contains entities, target_x, target_y, range
        
    Returns:
        list: List of result dictionaries with consumption and message info
    """
    entity = args[0]
    entities = kwargs.get("entities", [])
    target_x = kwargs.get("target_x")
    target_y = kwargs.get("target_y")
    max_range = kwargs.get("range", 5)
    
    results = []
    
    if not target_x or not target_y:
        results.append({
            "consumed": False,
            "message": Message(
                "You must select a corpse to resurrect!",
                (255, 255, 0)
            )
        })
        return results
    
    # Check range
    distance = math.sqrt((target_x - entity.x) ** 2 + (target_y - entity.y) ** 2)
    if distance > max_range:
        results.append({
            "consumed": False,
            "message": Message(
                "That corpse is too far away to resurrect!",
                (255, 255, 0)
            )
        })
        return results
    
    # Find a corpse at the target location
    corpse = None
    for ent in entities:
        if (ent.x == target_x and ent.y == target_y and
            ent.name.startswith("remains of ")):
            corpse = ent
            break
    
    if not corpse:
        results.append({
            "consumed": False,
            "message": Message(
                "There is no corpse at that location!",
                (255, 255, 0)
            )
        })
        return results
    
    # Check if there's already a blocking entity at the corpse's location
    from entity import get_blocking_entities_at_location
    blocking_entity = get_blocking_entities_at_location(entities, corpse.x, corpse.y)
    if blocking_entity and blocking_entity != corpse:
        results.append({
            "consumed": False,
            "message": Message(
                f"Cannot resurrect corpse - {blocking_entity.name} is in the way!",
                (255, 255, 0)
            )
        })
        return results
    
    # Resurrect the corpse!
    # Extract original name
    original_name = corpse.name.replace("remains of ", "")
    
    # Restore as zombified version
    corpse.name = f"Zombified {original_name}"
    corpse.char = corpse.char  # Keep original char (but we'll change color)
    corpse.color = (40, 40, 40)  # Dark gray/black for undead
    corpse.blocks = True
    corpse.render_order = RenderOrder.ACTOR
    
    # Restore fighter component with modified stats
    from components.fighter import Fighter
    from config.entity_registry import get_entity_registry
    
    # Try to get original stats from registry
    registry = get_entity_registry()
    monster_id = original_name.lower()
    original_def = registry.monsters.get(monster_id)
    
    if original_def and hasattr(original_def, 'stats'):
        base_hp = original_def.stats.hp
        base_defense = original_def.stats.defense
        base_power = original_def.stats.power
        base_damage_min = getattr(original_def.stats, 'damage_min', 0)
        base_damage_max = getattr(original_def.stats, 'damage_max', 0)
        base_strength = getattr(original_def.stats, 'strength', 10)
        base_dexterity = getattr(original_def.stats, 'dexterity', 10)
        base_constitution = getattr(original_def.stats, 'constitution', 10)
    else:
        # Fallback defaults if we can't find original
        base_hp = 10
        base_defense = 0
        base_power = 3
        base_damage_min = 1
        base_damage_max = 3
        base_strength = 10
        base_dexterity = 10
        base_constitution = 10
    
    # Create zombie fighter: 2x HP, 0.5x damage, reduced stats
    zombie_hp = base_hp * 2
    zombie_power = max(1, int(base_power * 0.5))  # At least 1 damage
    zombie_damage_min = max(1, int(base_damage_min * 0.5))  # Half natural damage, min 1
    zombie_damage_max = max(1, int(base_damage_max * 0.5))  # Half natural damage, min 1
    
    # Zombies are slow and clumsy but tough
    zombie_strength = max(6, int(base_strength * 0.75))  # Reduced strength
    zombie_dexterity = max(6, int(base_dexterity * 0.5))  # Very slow/clumsy
    zombie_constitution = min(18, int(base_constitution * 1.5))  # Undead are tough
    
    corpse.fighter = Fighter(
        hp=zombie_hp,
        defense=base_defense,
        power=zombie_power,
        damage_min=zombie_damage_min,
        damage_max=zombie_damage_max,
        strength=zombie_strength,
        dexterity=zombie_dexterity,
        constitution=zombie_constitution
    )
    corpse.fighter.owner = corpse
    
    # Give it mindless zombie AI
    from components.ai import MindlessZombieAI
    corpse.ai = MindlessZombieAI()
    corpse.ai.owner = corpse
    
    # Set faction to NEUTRAL or a zombie faction (attacks everything)
    from components.faction import Faction
    corpse.faction = Faction.NEUTRAL  # Zombies are hostile to all
    
    # Clear any inventory/equipment from the original monster
    # Check both ComponentRegistry and direct attributes for backward compatibility
    if corpse.components.has(ComponentType.INVENTORY) or hasattr(corpse, 'inventory'):
        corpse.inventory = None
    if corpse.components.has(ComponentType.EQUIPMENT) or hasattr(corpse, 'equipment'):
        corpse.equipment = None
    
    results.append({
        "consumed": True,
        "message": Message(
            f"Dark energy flows into the corpse! {corpse.name} rises, mindless and hungry!",
            (100, 255, 100)  # Green necromancy
        )
    })
    
    return results


def cast_yo_mama(*args, **kwargs):
    """Cast Yo Mama spell - target yells a joke and becomes the focus of all hostiles.
    
    This spell marks a target entity (monster, player, or even a corpse) as "taunted".
    All hostile creatures in the dungeon will immediately switch their aggro to attack
    the taunted target. The target yells a random Yo Mama joke when taunted.
    
    Duration is 1000 turns (effectively permanent, but easy to adjust).
    
    Args:
        *args: Standard targeting args (caster entity)
        **kwargs: Should contain:
            - target_x, target_y: Coordinates to target
            - entities: List of all entities in the game
            - fov_map: Field of view map
    
    Returns:
        list: List of result dictionaries with consumption and message info
    """
    import yaml
    import random
    import os
    
    caster = args[0] if args else None
    entities = kwargs.get("entities", [])
    fov_map = kwargs.get("fov_map")
    target_x = kwargs.get("target_x")
    target_y = kwargs.get("target_y")
    
    results = []
    
    # Check if target location is in FOV
    if not map_is_in_fov(fov_map, target_x, target_y):
        return [{"consumed": False, "message": Message("You cannot target something you cannot see.", (255, 255, 0))}]
    
    # Find target entity at coordinates
    target = None
    for entity in entities:
        if entity.x == target_x and entity.y == target_y and entity.fighter:
            target = entity
            break
    
    if not target:
        return [{"consumed": False, "message": Message("There is no valid target there.", (255, 255, 0))}]
    
    # Load jokes from YAML
    jokes_path = os.path.join(os.path.dirname(__file__), "config", "yo_mama_jokes.yaml")
    try:
        with open(jokes_path, 'r') as f:
            jokes_data = yaml.safe_load(f)
            jokes = jokes_data.get('jokes', [])
    except Exception as e:
        # Fallback joke if loading fails
        jokes = ["Yo mama so ugly, even the game couldn't load her jokes!"]
        print(f"Warning: Could not load yo_mama_jokes.yaml: {e}")
    
    if not jokes:
        jokes = ["Yo mama so forgettable, even the joke list forgot about her!"]
    
    # Select random joke
    joke = random.choice(jokes)
    
    # Target yells the joke (in Entity's purple color for consistency)
    results.append({
        "message": Message(
            f'{target.name} yells: "{joke}"',
            (200, 150, 255)  # Entity purple
        )
    })
    
    # Apply TauntedTargetEffect to the target
    from components.status_effects import TauntedTargetEffect, StatusEffectManager
    
    # Ensure target has status_effects component
    if not target.components.has(ComponentType.STATUS_EFFECTS):
        target.status_effects = StatusEffectManager(target)
        # Also register with ComponentRegistry
        target.components.add(ComponentType.STATUS_EFFECTS, target.status_effects)
    
    # Apply the taunt effect (1000 turns = effectively permanent)
    taunt_effect = TauntedTargetEffect(duration=1000, owner=target)
    effect_results = target.status_effects.add_effect(taunt_effect)
    results.extend(effect_results)
    
    # Add message about all monsters turning attention
    results.append({
        "message": Message(
            "All hostile creatures in the dungeon turn their attention to the insult!",
            (255, 100, 100)  # Red warning
        )
    })
    
    # Count how many monsters are affected
    affected_count = 0
    for entity in entities:
        if (entity.components.has(ComponentType.AI) and 
            entity.components.has(ComponentType.FIGHTER) and 
            entity != target):
            affected_count += 1
    
    if affected_count > 0:
        results.append({
            "message": Message(
                f"{affected_count} hostile creature{'s' if affected_count != 1 else ''} now target {target.name}!",
                (255, 200, 100)  # Orange
            )
        })
    
    return results


def cast_slow(*args, **kwargs):
    """Cast Slow spell - target moves every 2nd turn.
    
    Applies SlowedEffect to the target, making them only act on even-numbered turns.
    This gives tactical advantage by reducing enemy action economy.
    
    Args:
        *args: Standard targeting args (caster entity)
        **kwargs: Should contain:
            - target_x, target_y: Coordinates to target
            - entities: List of all entities
            - fov_map: Field of view map
            - duration: How many turns the slow lasts (default 10)
    
    Returns:
        list: List of result dictionaries with consumption and message info
    """
    caster = args[0] if args else None
    entities = kwargs.get("entities", [])
    fov_map = kwargs.get("fov_map")
    target_x = kwargs.get("target_x")
    target_y = kwargs.get("target_y")
    duration = kwargs.get("duration", 10)
    
    results = []
    
    # Check if target location is in FOV
    if not map_is_in_fov(fov_map, target_x, target_y):
        return [{"consumed": False, "message": Message("You cannot target something you cannot see.", (255, 255, 0))}]
    
    # Find target entity at coordinates
    target = None
    for entity in entities:
        if entity.x == target_x and entity.y == target_y and entity.fighter:
            target = entity
            break
    
    if not target:
        return [{"consumed": False, "message": Message("There is no valid target there.", (255, 255, 0))}]
    
    # Apply SlowedEffect
    from components.status_effects import SlowedEffect, StatusEffectManager
    
    # Ensure target has status_effects component
    if not target.components.has(ComponentType.STATUS_EFFECTS):
        target.status_effects = StatusEffectManager(target)
        target.components.add(ComponentType.STATUS_EFFECTS, target.status_effects)
    
    # Apply the slow effect
    slow_effect = SlowedEffect(duration=duration, owner=target)
    effect_results = target.status_effects.add_effect(slow_effect)
    results.extend(effect_results)
    
    results.append({"consumed": True})
    return results


def cast_glue(*args, **kwargs):
    """Cast Glue spell - target cannot move for X turns.
    
    Applies ImmobilizedEffect to the target, preventing all movement.
    Target can still attack if enemies are adjacent. Great for zoning!
    
    Args:
        *args: Standard targeting args (caster entity)
        **kwargs: Should contain:
            - target_x, target_y: Coordinates to target
            - entities: List of all entities
            - fov_map: Field of view map
            - duration: How many turns they're stuck (default 5)
    
    Returns:
        list: List of result dictionaries with consumption and message info
    """
    caster = args[0] if args else None
    entities = kwargs.get("entities", [])
    fov_map = kwargs.get("fov_map")
    target_x = kwargs.get("target_x")
    target_y = kwargs.get("target_y")
    duration = kwargs.get("duration", 5)
    
    results = []
    
    # Check if target location is in FOV
    if not map_is_in_fov(fov_map, target_x, target_y):
        return [{"consumed": False, "message": Message("You cannot target something you cannot see.", (255, 255, 0))}]
    
    # Find target entity at coordinates
    target = None
    for entity in entities:
        if entity.x == target_x and entity.y == target_y and entity.fighter:
            target = entity
            break
    
    if not target:
        return [{"consumed": False, "message": Message("There is no valid target there.", (255, 255, 0))}]
    
    # Apply ImmobilizedEffect
    from components.status_effects import ImmobilizedEffect, StatusEffectManager
    
    # Ensure target has status_effects component
    if not target.components.has(ComponentType.STATUS_EFFECTS):
        target.status_effects = StatusEffectManager(target)
        target.components.add(ComponentType.STATUS_EFFECTS, target.status_effects)
    
    # Apply the immobilize effect
    immobilize_effect = ImmobilizedEffect(duration=duration, owner=target)
    effect_results = target.status_effects.add_effect(immobilize_effect)
    results.extend(effect_results)
    
    results.append({"consumed": True})
    return results


def cast_rage(*args, **kwargs):
    """Cast Rage spell - target attacks ANYONE nearby with 2x damage, 0.5x accuracy!
    
    Applies EnragedEffect to the target:
    - Attacks any adjacent entity (friend or foe!)
    - Deals 2x damage
    - Has 0.5x to-hit chance (wild, inaccurate swings)
    - Absolute chaos!
    
    Args:
        *args: Standard targeting args (caster entity)
        **kwargs: Should contain:
            - target_x, target_y: Coordinates to target
            - entities: List of all entities
            - fov_map: Field of view map
            - duration: How many turns they're enraged (default 8)
    
    Returns:
        list: List of result dictionaries with consumption and message info
    """
    caster = args[0] if args else None
    entities = kwargs.get("entities", [])
    fov_map = kwargs.get("fov_map")
    target_x = kwargs.get("target_x")
    target_y = kwargs.get("target_y")
    duration = kwargs.get("duration", 8)
    
    results = []
    
    # Check if target location is in FOV
    if not map_is_in_fov(fov_map, target_x, target_y):
        return [{"consumed": False, "message": Message("You cannot target something you cannot see.", (255, 255, 0))}]
    
    # Find target entity at coordinates
    target = None
    for entity in entities:
        if entity.x == target_x and entity.y == target_y and entity.fighter:
            target = entity
            break
    
    if not target:
        return [{"consumed": False, "message": Message("There is no valid target there.", (255, 255, 0))}]
    
    # Apply EnragedEffect
    from components.status_effects import EnragedEffect, StatusEffectManager
    
    # Ensure target has status_effects component
    if not target.components.has(ComponentType.STATUS_EFFECTS):
        target.status_effects = StatusEffectManager(target)
        target.components.add(ComponentType.STATUS_EFFECTS, target.status_effects)
    
    # Apply the enrage effect
    enrage_effect = EnragedEffect(duration=duration, owner=target)
    effect_results = target.status_effects.add_effect(enrage_effect)
    results.extend(effect_results)
    
    results.append({"consumed": True})
    return results
