"""Item use functions and spell effects.

This module contains functions that are called when items are used,
including healing potions, spell scrolls, and other consumable items.
Each function implements the specific effect of using that item type.
"""

import tcod as libtcod
import tcod.libtcodpy as libtcodpy

from components.ai import ConfusedMonster
from game_messages import Message
from fov_functions import map_is_in_fov


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

    Args:
        *args: First argument should be the caster entity
        **kwargs: Should contain 'entities', 'fov_map', 'damage', 'radius',
                 'target_x', and 'target_y'

    Returns:
        list: List of result dictionaries with consumption and damage results
    """
    entities = kwargs.get("entities")
    fov_map = kwargs.get("fov_map")
    damage = kwargs.get("damage")
    radius = kwargs.get("radius")
    target_x = kwargs.get("target_x")
    target_y = kwargs.get("target_y")

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

    for entity in entities:
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
    if (hasattr(entity, 'equipment') and entity.equipment and 
        entity.equipment.main_hand and entity.equipment.main_hand.equippable):
        
        weapon = entity.equipment.main_hand
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
    """Enhance the equipped armor's defense range.
    
    Args:
        *args: First argument should be the entity using the scroll
        **kwargs: Should contain 'min_bonus' and 'max_bonus' for defense enhancement
        
    Returns:
        list: List of result dictionaries with consumption and message info
    """
    entity = args[0]
    min_bonus = kwargs.get("min_bonus", 1)
    max_bonus = kwargs.get("max_bonus", 1)
    
    results = []
    
    # Check if player has equipment and armor equipped
    if (hasattr(entity, 'equipment') and entity.equipment and 
        entity.equipment.off_hand and entity.equipment.off_hand.equippable):
        
        armor = entity.equipment.off_hand
        old_min = armor.equippable.defense_min
        old_max = armor.equippable.defense_max
        
        # Only enhance armor that has defense ranges
        if old_min > 0 and old_max > 0:
            armor.equippable.modify_defense_range(min_bonus, max_bonus)
            
            results.append({
                "consumed": True,
                "message": Message(
                    f"Your {armor.name} shimmers! Defense enhanced from "
                    f"({old_min}-{old_max}) to ({armor.equippable.defense_min}-{armor.equippable.defense_max}).",
                    (0, 255, 0)
                )
            })
        else:
            results.append({
                "consumed": False,
                "message": Message(
                    f"The {armor.name} cannot be enhanced further.", (255, 255, 0)
                )
            })
    else:
        results.append({
            "consumed": False,
            "message": Message(
                "You must have armor equipped to use this scroll.", (255, 255, 0)
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
        *args: [entity, entities, fov_map, game_map]
        **kwargs: Contains target_x, target_y from targeting
        
    Returns:
        list: List of result dictionaries with consumption and message info
    """
    from random import randint, random
    
    entity = args[0]
    entities = args[1]
    game_map = args[3]
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
