"""Item use functions and spell effects.

This module contains functions that are called when items are used,
including healing potions, spell scrolls, and other consumable items.
Each function implements the specific effect of using that item type.

NOTE: This module is being migrated to the new spell registry system.
Some functions now delegate to the SpellExecutor for consistency.
"""

import tcod as libtcod
import tcod.libtcodpy as libtcodpy
import math

from components.ai import ConfusedMonster
from components.component_registry import ComponentType
from components.ground_hazard import GroundHazard, HazardType
from components.status_effects import (
    DisorientationEffect,
    SlowedEffect,
    ImmobilizedEffect,
    EnragedEffect,
    StatusEffectManager
)
from game_messages import Message
from message_builder import MessageBuilder as MB
from fov_functions import map_is_in_fov
from render_functions import RenderOrder
from visual_effects import show_fireball, show_lightning, show_dragon_fart

# New spell system imports
from spells import cast_spell_by_id

# For identify spell
from components.item import Item


def heal(*args, **kwargs):
    """Heal the target entity by a specified amount.

    This function now delegates to the spell registry system.

    Args:
        *args: First argument should be the entity to heal
        **kwargs: Should contain 'amount' key with healing value

    Returns:
        list: List of result dictionaries with consumption and message info
    """
    # Delegate to new spell system (pass amount for backward compatibility)
    caster = args[0]
    amount = kwargs.get("amount")
    return cast_spell_by_id("heal", caster, entities=[], fov_map=None, amount=amount)


def cast_lightning(*args, **kwargs):
    """Cast a lightning spell that targets the closest enemy.

    This function now delegates to the spell registry system.

    Args:
        *args: First argument should be the caster entity
        **kwargs: Should contain 'entities', 'fov_map', 'damage', and 'maximum_range'

    Returns:
        list: List of result dictionaries with consumption, targeting, and message info
    """
    # Delegate to new spell system
    caster = args[0]
    return cast_spell_by_id("lightning", caster, **kwargs)


def cast_fireball(*args, **kwargs):
    """Cast a fireball spell that damages all entities in a radius.
    
    This function now delegates to the spell registry system.

    Args:
        *args: First argument should be the caster entity
        **kwargs: Should contain 'entities', 'fov_map', 'damage', 'radius',
                 'target_x', 'target_y', and optionally 'game_map'

    Returns:
        list: List of result dictionaries with consumption and damage results
    """
    # Delegate to new spell system
    caster = args[0] if args else None
    return cast_spell_by_id("fireball", caster, **kwargs)


def cast_confuse(*args, **kwargs):
    """Cast a confusion spell on a target entity.

    This function now delegates to the spell registry system.

    Args:
        *args: First argument should be the caster entity (optional for backward compat)
        **kwargs: Should contain 'entities', 'fov_map', 'target_x', and 'target_y'

    Returns:
        list: List of result dictionaries with consumption and confusion results
    """
    # Delegate to new spell system
    # Handle both old and new calling patterns
    caster = args[0] if args else None
    entities = kwargs.get("entities", [])
    fov_map = kwargs.get("fov_map")
    target_x = kwargs.get("target_x")
    target_y = kwargs.get("target_y")
    
    return cast_spell_by_id(
        "confusion",
        caster,
        entities=entities,
        fov_map=fov_map,
        target_x=target_x,
        target_y=target_y
    )


def enhance_weapon(*args, **kwargs):
    """Enhance the equipped weapon's damage range.

    Automatically targets the equipped weapon, or fails if no weapon equipped.

    Args:
        *args: First argument should be the entity using the scroll
        **kwargs: Should contain 'min_bonus' and 'max_bonus' for damage enhancement

    Returns:
        list: List of result dictionaries with consumption and message info
    """
    from components.component_registry import ComponentType
    from message_builder import MessageBuilder as MB
    import random

    caster = args[0]
    min_bonus = kwargs.get("min_bonus", 1)
    max_bonus = kwargs.get("max_bonus", 2)

    results = []

    # Check for equipped weapon
    equipment = caster.get_component_optional(ComponentType.EQUIPMENT)
    if not equipment:
        equipment = getattr(caster, 'equipment', None)

    if (equipment and equipment.main_hand and
        (equipment.main_hand.components.has(ComponentType.EQUIPPABLE) or
         hasattr(equipment.main_hand, 'equippable'))):
        weapon = equipment.main_hand
        old_min = weapon.equippable.damage_min
        old_max = weapon.equippable.damage_max

        if old_min > 0 and old_max > 0:
            # Apply random bonus within range
            bonus = random.randint(min_bonus, max_bonus)
            weapon.equippable.damage_min += bonus
            weapon.equippable.damage_max += bonus

            results.append({
                "consumed": True,
                "message": MB.item_effect(
                    f"Your {weapon.name} glows briefly! Damage enhanced from "
                    f"({old_min}-{old_max}) to ({weapon.equippable.damage_min}-{weapon.equippable.damage_max})."
                )
            })
        else:
            results.append({
                "consumed": False,
                "message": MB.warning(
                    f"The {weapon.name} cannot be enhanced further."
                )
            })
    else:
        results.append({
            "consumed": False,
            "message": MB.warning(
                "You must have a weapon equipped to use this scroll."
            )
        })

    return results


def enhance_armor(*args, **kwargs):
    """Enhance a random equipped armor piece's AC bonus.

    Automatically targets a random equipped armor piece, or fails if no armor equipped.

    Args:
        *args: First argument should be the entity using the scroll
        **kwargs: Should contain 'bonus' key for AC enhancement (default +1)

    Returns:
        list: List of result dictionaries with consumption and message info
    """
    from components.component_registry import ComponentType
    from message_builder import MessageBuilder as MB
    import random

    caster = args[0]
    bonus = kwargs.get("bonus", 1)  # Default +1 AC

    results = []

    # Check for equipment
    equipment = caster.get_component_optional(ComponentType.EQUIPMENT)
    if not equipment:
        equipment = getattr(caster, 'equipment', None)

    if not equipment:
        results.append({
            "consumed": False,
            "message": MB.warning("You have no equipment to enhance!")
        })
        return results

    # Find equipped armor pieces
    armor_pieces = []
    for slot_name in ['head', 'chest', 'off_hand']:
        armor = getattr(equipment, slot_name, None)
        if armor and (armor.components.has(ComponentType.EQUIPPABLE) or hasattr(armor, 'equippable')):
            # Check if it's armor (not a weapon) - has armor_class_bonus > 0
            equippable = None
            if hasattr(armor, 'get_component_optional'):
                equippable = armor.get_component_optional(ComponentType.EQUIPPABLE)
            if equippable is None and hasattr(armor, 'equippable'):
                equippable = armor.equippable

            if equippable and hasattr(equippable, 'armor_class_bonus') and equippable.armor_class_bonus > 0:
                armor_pieces.append((slot_name, armor))

    if not armor_pieces:
        results.append({
            "consumed": False,
            "message": MB.warning("You have no armor equipped to enhance!")
        })
        return results

    # Randomly select an armor piece
    slot_name, armor = random.choice(armor_pieces)
    old_bonus = armor.equippable.armor_class_bonus

    # Apply enhancement
    armor.equippable.armor_class_bonus += bonus

    results.append({
        "consumed": True,
        "message": MB.item_effect(
            f"Your {armor.name} glows briefly! AC bonus enhanced from "
            f"+{old_bonus} to +{armor.equippable.armor_class_bonus}."
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
    
    # Delegate to new spell system
    return cast_spell_by_id(
        "invisibility",
        entity,
        duration=duration
    )


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
                        "message": MB.custom(
                            "The teleport spell misfires!",
                            MB.ORANGE  # Orange - warning color
                        )
                    })
                    return results
        
        # Couldn't find valid random location - fail safely
        results.append({
            "consumed": False,
            "message": MB.spell_fail(
                "The teleport spell fizzles and fails!"
            )
        })
        return results
    
    # Normal teleport to target location
    if not target_x or not target_y:
        results.append({
            "consumed": False,
            "message": MB.warning("You must select a target location.")
        })
        return results
    
    # Check if target location is valid
    if game_map.tiles[target_x][target_y].blocked:
        results.append({
            "consumed": False,
            "message": MB.warning("You cannot teleport to a blocked location.")
        })
        return results
    
    # Check if any entity is blocking the target
    for other_entity in entities:
        if other_entity.blocks and other_entity.x == target_x and other_entity.y == target_y:
            results.append({
                "consumed": False,
                "message": MB.warning(
                    f"You cannot teleport to a location occupied by {other_entity.name}."
                )
            })
            return results
    
    # Successful teleport!
    entity.x = target_x
    entity.y = target_y
    
    results.append({
        "consumed": True,
        "message": MB.spell_effect(
            "You teleport across space!"
        )
    })
    
    return results


def cast_shield(*args, **kwargs):
    """Cast a protective shield that boosts defense.
    
    This function now delegates to the spell registry system.
    
    Args:
        *args: First argument should be the entity casting
        **kwargs: Contains duration (default 10)
        
    Returns:
        list: List of result dictionaries with consumption and message info
    """
    # Delegate to new spell system
    caster = args[0]
    
    return cast_spell_by_id(
        "shield",
        caster,
        entities=[],
        fov_map=None
    )


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
            "message": MB.warning(
                "You must select a direction for the dragon fart!"
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
            "message": MB.spell_fail(
                "The noxious gas dissipates harmlessly..."
            )
        })
        return results
    
    # Epic dragon fart message FIRST! 💨
    results.append({
        "consumed": True,
        "message": MB.custom(
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
            "message": MB.spell_effect(
                f"{target_entity.name} is overwhelmed by the noxious fumes and passes out!"
            )
        })
    
    return results


def cast_raise_dead(*args, **kwargs):
    """Resurrect a corpse as a mindless zombie that attacks everything.
    
    This function now delegates to the spell registry system.
    
    The zombie will have doubled HP, half damage, black coloring, and will
    attack ANY adjacent entity - player, monsters, or other zombies.
    Perfect for creating chaos!
    
    Args:
        *args: First argument is the caster entity (self.owner from inventory)
        **kwargs: Contains entities, target_x, target_y, range
        
    Returns:
        list: List of result dictionaries with consumption and message info
    """
    caster = args[0]
    return cast_spell_by_id("raise_dead", caster, **kwargs)


def cast_yo_mama(*args, **kwargs):
    """Cast Yo Mama spell - target yells a joke and becomes the focus of all hostiles.
    
    This function now delegates to the spell registry system.
    
    Args:
        *args: Standard targeting args (caster entity)
        **kwargs: Should contain target_x, target_y, entities, fov_map
    
    Returns:
        list: List of result dictionaries with consumption and message info
    """
    caster = args[0] if args else None
    return cast_spell_by_id("yo_mama", caster, **kwargs)


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
        return [{"consumed": False, "message": MB.warning("You cannot target something you cannot see.")}]
    
    # Find target entity at coordinates
    target = None
    for entity in entities:
        if entity.x == target_x and entity.y == target_y and entity.fighter:
            target = entity
            break
    
    if not target:
        return [{"consumed": False, "message": MB.warning("There is no valid target there.")}]
    
    # Apply SlowedEffect
    # Ensure target has status_effects component
    if not target.components.has(ComponentType.STATUS_EFFECTS):
        target.status_effects = StatusEffectManager(target)
        target.components.add(ComponentType.STATUS_EFFECTS, target.status_effects)
    
    # Delegate to new spell system
    return cast_spell_by_id(
        "slow",
        caster,
        entities=entities,
        fov_map=fov_map,
        target_x=target_x,
        target_y=target_y
    )


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
        return [{"consumed": False, "message": MB.warning("You cannot target something you cannot see.")}]
    
    # Find target entity at coordinates
    target = None
    for entity in entities:
        if entity.x == target_x and entity.y == target_y and entity.fighter:
            target = entity
            break
    
    if not target:
        return [{"consumed": False, "message": MB.warning("There is no valid target there.")}]
    
    # Apply ImmobilizedEffect
    # Ensure target has status_effects component
    if not target.components.has(ComponentType.STATUS_EFFECTS):
        target.status_effects = StatusEffectManager(target)
        target.components.add(ComponentType.STATUS_EFFECTS, target.status_effects)
    
    # Delegate to new spell system
    return cast_spell_by_id(
        "glue",
        caster,
        entities=entities,
        fov_map=fov_map,
        target_x=target_x,
        target_y=target_y
    )


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
        return [{"consumed": False, "message": MB.warning("You cannot target something you cannot see.")}]
    
    # Find target entity at coordinates
    target = None
    for entity in entities:
        if entity.x == target_x and entity.y == target_y and entity.fighter:
            target = entity
            break
    
    if not target:
        return [{"consumed": False, "message": MB.warning("There is no valid target there.")}]
    
    # Apply EnragedEffect
    # Ensure target has status_effects component
    if not target.components.has(ComponentType.STATUS_EFFECTS):
        target.status_effects = StatusEffectManager(target)
        target.components.add(ComponentType.STATUS_EFFECTS, target.status_effects)
    
    # Delegate to new spell system
    return cast_spell_by_id(
        "rage",
        caster,
        entities=entities,
        fov_map=fov_map,
        target_x=target_x,
        target_y=target_y
    )


def cast_identify(*args, **kwargs):
    """Grant temporary identification powers for 5 turns.
    
    Applies IdentifyModeEffect which automatically identifies 1 random
    unidentified item per turn for 5 turns.
    
    Args:
        *args: First argument should be the caster (player)
        **kwargs: duration (optional, defaults to 5)
    
    Returns:
        list: List of result dictionaries with status effect application
    """
    from components.status_effects import IdentifyModeEffect
    
    caster = args[0]
    results = []
    duration = kwargs.get('duration', 5)
    
    # Check if player has any unidentified items
    if not hasattr(caster, 'inventory') or not caster.inventory:
        results.append({
            "consumed": False,
            "message": MB.warning("You have no inventory!")
        })
        return results
    
    # Count unidentified items
    unidentified_count = 0
    for item in caster.inventory.items:
        item_comp = getattr(item, 'item', None)
        if item_comp and hasattr(item_comp, 'identified') and not item_comp.identified:
            unidentified_count += 1
    
    if unidentified_count == 0:
        results.append({
            "consumed": False,
            "message": MB.info("You have no unidentified items!")
        })
        return results
    
    # Apply identify mode effect
    identify_effect = IdentifyModeEffect(duration=duration, owner=caster)
    effect_results = caster.status_effects.add_effect(identify_effect)
    results.extend(effect_results)
    
    # Scroll is consumed
    results.append({"consumed": True})
    
    return results
# This will be appended to item_functions.py


# ============================================================================
# NEW POTION EFFECTS - Slice 1: Buff Potions
# ============================================================================

def drink_speed_potion(*args, **kwargs):
    """Drink a potion of speed - doubles movement speed for 20 turns.
    
    Args:
        *args: First argument should be the entity drinking the potion
        **kwargs: Optional parameters
    
    Returns:
        list: List of result dictionaries with consumption and status effect info
    """
    from components.status_effects import SpeedEffect
    from message_builder import MessageBuilder as MB
    
    entity = args[0] if args else None
    if not entity:
        return [{"consumed": False, "message": MB.failure("No entity to apply speed effect to!")}]
    
    results = []
    
    # Get or create status effect manager
    if not hasattr(entity, 'status_effects'):
        from components.status_effects import StatusEffectManager
        entity.status_effects = StatusEffectManager(entity)
    
    # Add speed effect for 20 turns
    speed_effect = SpeedEffect(duration=20, owner=entity)
    effect_results = entity.status_effects.add_effect(speed_effect)
    results.extend(effect_results)
    
    results.append({"consumed": True})
    return results


def drink_regeneration_potion(*args, **kwargs):
    """Drink a potion of regeneration - heals 1 HP per turn for 50 turns (50 HP total).
    
    Args:
        *args: First argument should be the entity drinking the potion
        **kwargs: Optional parameters
    
    Returns:
        list: List of result dictionaries with consumption and status effect info
    """
    from components.status_effects import RegenerationEffect
    from message_builder import MessageBuilder as MB
    
    entity = args[0] if args else None
    if not entity:
        return [{"consumed": False, "message": MB.failure("No entity to apply regeneration effect to!")}]
    
    results = []
    
    # Get or create status effect manager
    if not hasattr(entity, 'status_effects'):
        from components.status_effects import StatusEffectManager
        entity.status_effects = StatusEffectManager(entity)
    
    # Add regeneration effect for 50 turns, 1 HP per turn
    regen_effect = RegenerationEffect(duration=50, owner=entity, heal_per_turn=1)
    effect_results = entity.status_effects.add_effect(regen_effect)
    results.extend(effect_results)
    
    results.append({"consumed": True})
    return results


def drink_invisibility_potion(*args, **kwargs):
    """Drink a potion of invisibility - become invisible for 30 turns.
    
    Note: Same duration as invisibility scroll (both 30 turns).
    Future: Can be thrown at enemies to make them invisible too.
    
    Args:
        *args: First argument should be the entity drinking the potion
        **kwargs: Optional parameters
    
    Returns:
        list: List of result dictionaries with consumption and status effect info
    """
    from components.status_effects import InvisibilityEffect
    from message_builder import MessageBuilder as MB
    
    entity = args[0] if args else None
    if not entity:
        return [{"consumed": False, "message": MB.failure("No entity to apply invisibility effect to!")}]
    
    results = []
    
    # Get or create status effect manager
    if not hasattr(entity, 'status_effects'):
        from components.status_effects import StatusEffectManager
        entity.status_effects = StatusEffectManager(entity)
    
    # Add invisibility effect for 30 turns (longer than scroll's 10 turns)
    invis_effect = InvisibilityEffect(duration=30, owner=entity)
    effect_results = entity.status_effects.add_effect(invis_effect)
    results.extend(effect_results)
    
    results.append({"consumed": True})
    return results


def drink_levitation_potion(*args, **kwargs):
    """Drink a potion of levitation - float over ground hazards for 40 turns.
    
    Allows safe passage over fire, poison gas, and other ground hazards.
    
    Args:
        *args: First argument should be the entity drinking the potion
        **kwargs: Optional parameters
    
    Returns:
        list: List of result dictionaries with consumption and status effect info
    """
    from components.status_effects import LevitationEffect
    from message_builder import MessageBuilder as MB
    
    entity = args[0] if args else None
    if not entity:
        return [{"consumed": False, "message": MB.failure("No entity to apply levitation effect to!")}]
    
    results = []
    
    # Get or create status effect manager
    if not hasattr(entity, 'status_effects'):
        from components.status_effects import StatusEffectManager
        entity.status_effects = StatusEffectManager(entity)
    
    # Add levitation effect for 40 turns
    levitation_effect = LevitationEffect(duration=40, owner=entity)
    effect_results = entity.status_effects.add_effect(levitation_effect)
    results.extend(effect_results)
    
    results.append({"consumed": True})
    return results


def drink_protection_potion(*args, **kwargs):
    """Drink a potion of protection - gain +4 AC for 50 turns.
    
    Provides a protective aura that significantly boosts defense.
    
    Args:
        *args: First argument should be the entity drinking the potion
        **kwargs: Optional parameters
    
    Returns:
        list: List of result dictionaries with consumption and status effect info
    """
    from components.status_effects import ProtectionEffect
    from message_builder import MessageBuilder as MB
    
    entity = args[0] if args else None
    if not entity:
        return [{"consumed": False, "message": MB.failure("No entity to apply protection effect to!")}]
    
    results = []
    
    # Get or create status effect manager
    if not hasattr(entity, 'status_effects'):
        from components.status_effects import StatusEffectManager
        entity.status_effects = StatusEffectManager(entity)
    
    # Add protection effect for 50 turns, +4 AC
    protection_effect = ProtectionEffect(duration=50, owner=entity, ac_bonus=4)
    effect_results = entity.status_effects.add_effect(protection_effect)
    results.extend(effect_results)
    
    results.append({"consumed": True})
    return results


def drink_heroism_potion(*args, **kwargs):
    """Drink a potion of heroism - gain +3 to hit and +3 damage for 30 turns.
    
    Perfect for boss fights and difficult encounters.
    
    Args:
        *args: First argument should be the entity drinking the potion
        **kwargs: Optional parameters
    
    Returns:
        list: List of result dictionaries with consumption and status effect info
    """
    from components.status_effects import HeroismEffect
    from message_builder import MessageBuilder as MB
    
    entity = args[0] if args else None
    if not entity:
        return [{"consumed": False, "message": MB.failure("No entity to apply heroism effect to!")}]
    
    results = []
    
    # Get or create status effect manager
    if not hasattr(entity, 'status_effects'):
        from components.status_effects import StatusEffectManager
        entity.status_effects = StatusEffectManager(entity)
    
    # Add heroism effect for 30 turns, +3 to hit and damage
    heroism_effect = HeroismEffect(duration=30, owner=entity, attack_bonus=3, damage_bonus=3)
    effect_results = entity.status_effects.add_effect(heroism_effect)
    results.extend(effect_results)
    
    results.append({"consumed": True})
    return results


# ============================================================================
# NEW POTION EFFECTS - Slice 2: Debuff Potions
# ============================================================================

def drink_weakness_potion(*args, **kwargs):
    """Drink a potion of weakness - suffer -2 damage for 30 turns.
    
    A debuff potion that reduces combat effectiveness. Survivable but annoying.
    Part of the identification risk/reward system.
    
    Args:
        *args: First argument should be the entity drinking the potion
        **kwargs: Optional parameters
    
    Returns:
        list: List of result dictionaries with consumption and status effect info
    """
    from components.status_effects import WeaknessEffect
    from message_builder import MessageBuilder as MB
    
    entity = args[0] if args else None
    if not entity:
        return [{"consumed": False, "message": MB.failure("No entity to apply weakness effect to!")}]
    
    results = []
    
    # Get or create status effect manager
    if not hasattr(entity, 'status_effects'):
        from components.status_effects import StatusEffectManager
        entity.status_effects = StatusEffectManager(entity)
    
    # Add weakness effect for 30 turns, -2 damage
    weakness_effect = WeaknessEffect(duration=30, owner=entity, damage_penalty=2)
    effect_results = entity.status_effects.add_effect(weakness_effect)
    results.extend(effect_results)
    
    results.append({"consumed": True})
    return results


def drink_slowness_potion(*args, **kwargs):
    """Drink a potion of slowness - move at half speed for 20 turns.
    
    A debuff potion that reduces movement speed. Dangerous but not deadly.
    
    Args:
        *args: First argument should be the entity drinking the potion
        **kwargs: Optional parameters
    
    Returns:
        list: List of result dictionaries with consumption and status effect info
    """
    from components.status_effects import SlowedEffect
    from message_builder import MessageBuilder as MB
    
    entity = args[0] if args else None
    if not entity:
        return [{"consumed": False, "message": MB.failure("No entity to apply slowness effect to!")}]
    
    results = []
    
    # Get or create status effect manager
    if not hasattr(entity, 'status_effects'):
        from components.status_effects import StatusEffectManager
        entity.status_effects = StatusEffectManager(entity)
    
    # Add slowed effect for 20 turns
    slowed_effect = SlowedEffect(duration=20, owner=entity)
    effect_results = entity.status_effects.add_effect(slowed_effect)
    results.extend(effect_results)
    
    results.append({"consumed": True})
    return results


def drink_blindness_potion(*args, **kwargs):
    """Drink a potion of blindness - FOV reduced to 1 tile for 15 turns.
    
    A high-risk debuff potion. Temporary setback but survivable.
    
    Args:
        *args: First argument should be the entity drinking the potion
        **kwargs: Optional parameters
    
    Returns:
        list: List of result dictionaries with consumption and status effect info
    """
    from components.status_effects import BlindnessEffect
    from message_builder import MessageBuilder as MB
    
    entity = args[0] if args else None
    if not entity:
        return [{"consumed": False, "message": MB.failure("No entity to apply blindness effect to!")}]
    
    results = []
    
    # Get or create status effect manager
    if not hasattr(entity, 'status_effects'):
        from components.status_effects import StatusEffectManager
        entity.status_effects = StatusEffectManager(entity)
    
    # Add blindness effect for 15 turns, FOV radius = 1
    blindness_effect = BlindnessEffect(duration=15, owner=entity, fov_radius=1)
    effect_results = entity.status_effects.add_effect(blindness_effect)
    results.extend(effect_results)
    
    results.append({"consumed": True})
    return results


def drink_paralysis_potion(*args, **kwargs):
    """Drink a potion of paralysis - cannot move for 3-5 turns.
    
    A very dangerous debuff potion but short duration and survivable.
    High risk for identification but won't instantly kill you.
    
    Args:
        *args: First argument should be the entity drinking the potion
        **kwargs: Optional parameters
    
    Returns:
        list: List of result dictionaries with consumption and status effect info
    """
    from components.status_effects import ParalysisEffect
    from message_builder import MessageBuilder as MB
    import random
    
    entity = args[0] if args else None
    if not entity:
        return [{"consumed": False, "message": MB.failure("No entity to apply paralysis effect to!")}]
    
    results = []
    
    # Get or create status effect manager
    if not hasattr(entity, 'status_effects'):
        from components.status_effects import StatusEffectManager
        entity.status_effects = StatusEffectManager(entity)
    
    # Add paralysis effect for 3-5 turns (random)
    duration = random.randint(3, 5)
    paralysis_effect = ParalysisEffect(duration=duration, owner=entity)
    effect_results = entity.status_effects.add_effect(paralysis_effect)
    results.extend(effect_results)
    
    results.append({"consumed": True})
    return results


# ============================================================================
# NEW POTION EFFECTS - Slice 3: Special Potion
# ============================================================================

def drink_experience_potion(*args, **kwargs):
    """Drink a potion of experience - gain 1 level instantly.
    
    A rare and powerful potion that provides an immediate level-up.
    High value identification target.
    
    Args:
        *args: First argument should be the entity drinking the potion
        **kwargs: Optional parameters
    
    Returns:
        list: List of result dictionaries with consumption and level-up info
    """
    from components.component_registry import ComponentType
    from message_builder import MessageBuilder as MB
    
    entity = args[0] if args else None
    if not entity:
        return [{"consumed": False, "message": MB.failure("No entity to gain experience!")}]
    
    results = []
    
    # Get level component
    level_comp = entity.get_component_optional(ComponentType.LEVEL)
    if not level_comp:
        results.append({
            "consumed": False,
            "message": MB.warning(f"{entity.name} cannot gain experience!")
        })
        return results
    
    # Calculate XP needed for next level and grant it
    xp_to_next_level = level_comp.experience_to_next_level - level_comp.current_xp
    level_comp.add_xp(xp_to_next_level)
    
    results.append({
        "consumed": True,
        "message": MB.level_up(f"{entity.name} feels a surge of power and gains a level!")
    })
    
    # Check if level-up occurred (add_xp should trigger it)
    if level_comp.current_level > level_comp.current_level - 1:
        results.append({"leveled_up": True})
    
    return results


# ============================================================================
# PHASE 5: QUEST ITEM FUNCTIONS
# ============================================================================

def unlock_crimson_ritual(*args, **kwargs):
    """Read the Crimson Ritual Codex and unlock knowledge of the ritual.
    
    This ancient journal reveals the secret of the dragon-binding ritual,
    unlocking the alternate "Give (Ritual)" option in Ending 1b.
    
    The journal describes how the Crimson Order extracted Aurelyn's heart
    and bound Zhyraxion, suggesting the ritual could be reversed.
    
    Args:
        *args: First argument should be the entity reading the codex
        **kwargs: Optional parameters
    
    Returns:
        list: List of result dictionaries with messages
    """
    from message_builder import MessageBuilder as MB
    
    entity = args[0] if args else None
    if not entity:
        return [{"consumed": False, "message": MB.failure("No one to read the codex!")}]
    
    results = []
    
    # The codex can always be read, but knowledge is stored for when victory component exists
    results.append({
        "message": MB.item_effect(
            "You read the ancient journal. The ritual is clear: "
            "extract a dragon's heart to bind them, or return a heart to free them. "
            "If Zhyraxion had two hearts... one could be given back."
        )
    })

    # Try to unlock knowledge if victory component exists
    knowledge_unlocked = False
    if hasattr(entity, 'victory') and entity.victory:
        knowledge_unlocked = entity.victory.unlock_knowledge('crimson_ritual_knowledge')

    if knowledge_unlocked:
        results.append({
            "message": MB.success(
                "New knowledge unlocked: The Crimson Ritual! "
                "A new choice will be available at the final confrontation."
            )
        })
    else:
        # Either already unlocked or no victory component yet
        if hasattr(entity, 'victory') and entity.victory and entity.victory.has_knowledge('crimson_ritual_knowledge'):
            results.append({
                "message": MB.info("You already understand the Crimson Ritual.")
            })
        else:
            results.append({
                "message": MB.info("The knowledge of the Crimson Ritual remains locked until you face the Entity.")
            })
    
    # This item is not consumed - it stays in inventory as a quest item
    results.append({"consumed": False})
    
    return results

