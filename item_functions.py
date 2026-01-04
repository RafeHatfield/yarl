"""Item use functions and spell effects.

This module contains functions that are called when items are used,
including healing potions, spell scrolls, and other consumable items.
Each function implements the specific effect of using that item type.

NOTE: This module is being migrated to the new spell registry system.
Some functions now delegate to the SpellExecutor for consistency.
"""

# Rendering stays in the IO layer. These placeholders remain so tests can
# patch `libtcod`/`libtcodpy` without reintroducing direct console usage.
libtcod = None
libtcodpy = None

import math
from random import randint, random

from components.ai import ConfusedMonster
from components.component_registry import ComponentType
from components.ground_hazard import GroundHazard, HazardType
from components.status_effects import (
    BlindnessEffect,
    DisorientationEffect,
    EnragedEffect,
    HeroismEffect,
    IdentifyModeEffect,
    ImmobilizedEffect,
    InvisibilityEffect,
    LevitationEffect,
    ParalysisEffect,
    ProtectionEffect,
    RegenerationEffect,
    SlowedEffect,
    SluggishEffect,  # Phase 7: Speed debuff effect
    SpeedEffect,
    StatusEffectManager,
    WeaknessEffect
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
            # Apply bonus to minimum damage and max damage (min gets min_bonus, max gets max_bonus)
            weapon.equippable.damage_min += min_bonus
            weapon.equippable.damage_max += max_bonus

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
        confused_ai = ConfusedMonster(target_entity.get_component_optional(ComponentType.AI), sleep_duration)
        confused_ai.owner = target_entity
        target_entity.components.add(ComponentType.AI, confused_ai)
        
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
        entity_fighter = entity.get_component_optional(ComponentType.FIGHTER)
        if entity.x == target_x and entity.y == target_y and entity_fighter:
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
        entity_fighter = entity.get_component_optional(ComponentType.FIGHTER)
        if entity.x == target_x and entity.y == target_y and entity_fighter:
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
        entity_fighter = entity.get_component_optional(ComponentType.FIGHTER)
        if entity.x == target_x and entity.y == target_y and entity_fighter:
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


def drink_lightning_reflexes_potion(*args, **kwargs):
    """Drink a potion of lightning reflexes - grants +50% combat speed bonus for 15 turns.
    
    Phase 5: This potion temporarily overrides equipment-based speed bonuses,
    granting a flat +50% bonus attack chance for the duration.
    
    Args:
        *args: First argument should be the entity drinking the potion
        **kwargs: Optional parameters
    
    Returns:
        list: List of result dictionaries with consumption and status effect info
    """
    entity = args[0] if args else None
    if not entity:
        return [{"consumed": False, "message": MB.failure("No entity to apply lightning reflexes to!")}]
    
    results = []
    
    # Get or create status effect manager
    if not hasattr(entity, 'status_effects'):
        from components.status_effects import StatusEffectManager
        entity.status_effects = StatusEffectManager(entity)
    
    # Add lightning reflexes effect for 15 turns (short but powerful)
    from components.status_effects import LightningReflexesEffect
    reflexes_effect = LightningReflexesEffect(duration=15, owner=entity, speed_bonus=0.50)
    effect_results = entity.status_effects.add_effect(reflexes_effect)
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
# Phase 7: Tar Potion (Speed Debuff)
# ============================================================================

def drink_tar_potion(*args, **kwargs):
    """Drink a potion of tar - applies SluggishEffect (speed debuff) for 10 turns.
    
    Phase 7: Unlike SlowedEffect which skips turns, this reduces the
    speed_bonus_ratio through the SpeedBonusTracker's debuff system.
    Categorized as a panic-style item (for emergencies/tactical use).
    
    Args:
        *args: First argument should be the entity drinking the potion
        **kwargs: Optional parameters (duration, speed_penalty from yaml)
    
    Returns:
        list: List of result dictionaries with consumption and status effect info
    """
    entity = args[0] if args else None
    if not entity:
        return [{"consumed": False, "message": MB.failure("No entity to apply tar effect to!")}]
    
    # Get parameters from kwargs (from yaml config) or use defaults
    duration = kwargs.get("duration", 10)
    speed_penalty = kwargs.get("speed_penalty", 0.25)
    
    results = []
    
    # Get or create status effect manager (handle both missing attr and None)
    if not hasattr(entity, 'status_effects') or entity.status_effects is None:
        from components.status_effects import StatusEffectManager
        entity.status_effects = StatusEffectManager(entity)
    
    # Add sluggish effect
    sluggish_effect = SluggishEffect(duration=duration, owner=entity, speed_penalty=speed_penalty)
    effect_results = entity.status_effects.add_effect(sluggish_effect)
    results.extend(effect_results)
    
    results.append({"consumed": True})
    return results


# ============================================================================
# Phase 20B: Fire Potion (Burning DOT)
# ============================================================================

def apply_burning_potion(*args, **kwargs):
    """Apply a burning effect to the target (from a thrown fire potion).
    
    Args:
        *args: First argument should be the target entity
        **kwargs: Optional parameters (duration, damage_per_turn)
    
    Returns:
        list: List of result dictionaries with consumption and status effect info
    """
    entity = args[0] if args else None
    if not entity:
        return [{"consumed": False, "message": MB.failure("No entity to ignite!")}]
    
    duration = kwargs.get("duration", 4)
    damage_per_turn = kwargs.get("damage_per_turn", 1)
    results = []
    
    from components.status_effects import StatusEffectManager, BurningEffect
    
    if not hasattr(entity, 'status_effects') or entity.status_effects is None:
        entity.status_effects = StatusEffectManager(entity)
    
    if hasattr(entity, 'components') and not entity.components.has(ComponentType.STATUS_EFFECTS):
        entity.components.add(ComponentType.STATUS_EFFECTS, entity.status_effects)
    
    burning_effect = BurningEffect(duration=duration, owner=entity, damage_per_turn=damage_per_turn)
    effect_results = entity.status_effects.add_effect(burning_effect)
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
        print(f">>> CRIMSON CODEX: Unlocking knowledge for entity {entity.name}")
        knowledge_unlocked = entity.victory.unlock_knowledge('crimson_ritual_knowledge')
        print(f">>> CRIMSON CODEX: knowledge_unlocked = {knowledge_unlocked}")
        print(f">>> CRIMSON CODEX: knows_crimson_ritual = {entity.victory.knows_crimson_ritual}")

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
            print(f">>> CRIMSON CODEX: Already have knowledge")
        else:
            results.append({
                "message": MB.info("The knowledge of the Crimson Ritual remains locked until you face the Entity.")
            })
            print(f">>> CRIMSON CODEX: No victory component or knowledge not unlocked yet")
    
    # This item is not consumed - it stays in inventory as a quest item
    results.append({"consumed": False})
    
    return results


def use_wand_of_portals(*args, **kwargs):
    """Use the Wand of Portals to create a portal pair or cancel active portals.
    
    The wand always has 1 charge (never more, never less).
    It operates as a binary state machine:
    - State A: No portals → enters targeting to place portal pair
    - State B: Portals active → cancels them and returns to State A
    
    This function is called when the player selects the wand from inventory.
    
    Args:
        *args: First argument should be the entity using the wand (player)
        **kwargs: Optional parameters from the game engine, including:
            - wand_entity: The wand item entity
            - entities: Game entities list (required for cancellation)
    
    Returns:
        list: List of result dictionaries with status messages
    """
    entity = args[0] if args else None
    if not entity:
        return [{"consumed": False, "message": MB.failure("No one to use the wand!")}]
    
    results = []
    
    # Get the wand from kwargs (passed by the engine)
    wand = kwargs.get("wand_entity")
    if not wand or not hasattr(wand, 'portal_placer'):
        return [{"consumed": False, "message": MB.failure("This wand is corrupted!")}]
    
    portal_placer = wand.portal_placer
    
    # Ensure charge is always 1 (invariant enforcement)
    portal_placer.charges = 1
    
    # Check if portals are already active - if so, cancel them (don't place new ones)
    if portal_placer.has_active_portals():
        entities = kwargs.get("entities")
        if not entities:
            return [{"consumed": False, "message": MB.failure("Cannot cancel portals (no entities list)!")}]
        
        # Cancel active portals and reset wand
        cancel_result = portal_placer.cancel_active_portals(entities)
        
        if cancel_result.get('success'):
            # Portals canceled, wand reset to ready state
            results.append({
                "consumed": False,
                "message": MB.success(cancel_result.get('message', 'Portals canceled. Wand ready.'))
            })
            results.append({"portal_canceled": True})
        else:
            results.append({
                "consumed": False,
                "message": MB.warning(cancel_result.get('message', 'Failed to cancel portals'))
            })
        
        return results
    
    # No active portals - enter targeting mode to place new pair
    results.append({
        "message": MB.success("Portal wand ready. Click to place entrance portal.")
    })
    
    # Signal to game engine that targeting mode should start
    results.append({"targeting_mode": True})
    results.append({"consumed": False})  # Don't consume from inventory
    
    return results


# ============================================================================
# PHASE 10: FACTION MANIPULATION SCROLLS & ANTIDOTE
# ============================================================================


def use_aggravation_scroll(*args, **kwargs):
    """Use Scroll of Unreasonable Aggravation on a target monster.
    
    Phase 10: Incites a monster to become irrationally enraged against a faction.
    
    The enraged monster will prioritize attacking that faction over all others
    (including the player), until death. Effect is permanent (until death).
    
    Susceptibility:
    - Works best on: ORC_FACTION, INDEPENDENT, UNDEAD (zombies)
    - Reduced/no effect on: CULTIST, high undead (wraiths)
    
    Args:
        *args: First argument should be the caster (player)
        **kwargs: Should contain:
            - target_x, target_y: Coordinates of target monster
            - entities: List of all entities
            - fov_map: Field of view map
            - target_faction: The faction to enrage against (if pre-selected)
    
    Returns:
        list: List of result dictionaries with consumption and message info
    """
    caster = args[0] if args else None
    entities = kwargs.get("entities", [])
    fov_map = kwargs.get("fov_map")
    target_x = kwargs.get("target_x")
    target_y = kwargs.get("target_y")
    target_faction_str = kwargs.get("target_faction")  # Optional: pre-selected faction
    
    results = []
    
    # Validate targeting
    if target_x is None or target_y is None:
        return [{"consumed": False, "message": MB.warning("You must select a target monster.")}]
    
    # Check FOV
    if fov_map and not map_is_in_fov(fov_map, target_x, target_y):
        return [{"consumed": False, "message": MB.warning("You cannot target something you cannot see.")}]
    
    # Find target entity at coordinates
    target = None
    for entity in entities:
        if entity.x == target_x and entity.y == target_y:
            # Must have AI (be a monster) and be alive
            ai = entity.get_component_optional(ComponentType.AI)
            fighter = entity.get_component_optional(ComponentType.FIGHTER)
            if ai and fighter and fighter.hp > 0:
                target = entity
                break
    
    if not target:
        return [{"consumed": False, "message": MB.warning("There is no valid monster target there.")}]
    
    # Import faction module
    from components.faction import (
        Faction, get_faction_display_name, are_factions_hostile,
        get_faction_from_string
    )
    
    # Check resistance based on target's faction
    target_faction = getattr(target, 'faction', Faction.NEUTRAL)
    
    # Resistance check: Cultists and high undead (wraiths) resist
    resist_chance = 0.0
    if target_faction == Faction.CULTIST:
        resist_chance = 0.70  # 70% resist
    elif target_faction == Faction.UNDEAD:
        # Check if it's a "high" undead (wraith-like) by name/char
        target_name_lower = target.name.lower() if hasattr(target, 'name') else ""
        if any(x in target_name_lower for x in ['wraith', 'lich', 'vampire', 'specter', 'ghost']):
            resist_chance = 0.80  # 80% resist for high undead
        else:
            resist_chance = 0.20  # 20% resist for low undead (zombies, skeletons)
    
    # Roll for resistance
    if resist_chance > 0 and random() < resist_chance:
        results.append({
            "consumed": True,  # Scroll is used even on resist
            "message": MB.spell_fail(
                f"The magic fizzles; {target.name} is unmoved by the scroll's influence."
            )
        })
        return results
    
    # Gather available factions from nearby entities (in FOV or nearby)
    available_factions = set()
    for entity in entities:
        if entity == target or entity == caster:
            continue
        
        entity_faction = getattr(entity, 'faction', None)
        if entity_faction and entity_faction != Faction.PLAYER:
            # Check if this entity is alive and could be a target
            e_fighter = entity.get_component_optional(ComponentType.FIGHTER)
            if e_fighter and e_fighter.hp > 0:
                # Don't include same faction as target
                if entity_faction != target_faction:
                    available_factions.add(entity_faction)
    
    # Always allow enraging against the player
    available_factions.add(Faction.PLAYER)
    
    # Determine which faction to enrage against
    chosen_faction = None
    
    if target_faction_str:
        # Pre-selected faction (from menu selection)
        chosen_faction = get_faction_from_string(target_faction_str)
    elif len(available_factions) == 1:
        # Only one faction available - auto-select
        chosen_faction = list(available_factions)[0]
    else:
        # Multiple factions - need player to choose
        # Return a special result to trigger faction selection menu
        faction_options = [
            (f.value, get_faction_display_name(f)) 
            for f in available_factions
        ]
        results.append({
            "consumed": False,
            "requires_faction_selection": True,
            "faction_options": faction_options,
            "target_entity": target,
            "message": MB.info("Choose which faction to enrage against:")
        })
        return results
    
    if not chosen_faction:
        return [{"consumed": False, "message": MB.warning("No valid faction to enrage against.")}]
    
    # Apply the EnragedAgainstFactionEffect
    from components.status_effects import (
        StatusEffectManager, EnragedAgainstFactionEffect
    )
    
    # Ensure target has status_effects component
    if not target.components.has(ComponentType.STATUS_EFFECTS):
        target.status_effects = StatusEffectManager(target)
        target.components.add(ComponentType.STATUS_EFFECTS, target.status_effects)
    
    # Create and apply the effect
    aggravation_effect = EnragedAgainstFactionEffect(
        owner=target,
        target_faction=chosen_faction
    )
    effect_results = target.status_effects.add_effect(aggravation_effect)
    results.extend(effect_results)
    
    # Queue VFX
    try:
        from visual_effects import show_anger_effect
        show_anger_effect(target.x, target.y, target)
    except ImportError:
        pass  # VFX optional
    
    results.append({"consumed": True})
    
    return results


def drink_antidote_potion(*args, **kwargs):
    """Drink an antidote potion to cure the Plague of Restless Death.
    
    Phase 10: Removes PlagueOfRestlessDeathEffect from the player.
    
    Args:
        *args: First argument should be the entity drinking the potion
        **kwargs: Optional parameters
    
    Returns:
        list: List of result dictionaries with consumption and message info
    """
    entity = args[0] if args else None
    if not entity:
        return [{"consumed": False, "message": MB.failure("No entity to cure!")}]
    
    results = []
    
    # Check if entity has the plague
    status_effects = entity.get_component_optional(ComponentType.STATUS_EFFECTS)
    if not status_effects:
        results.append({
            "consumed": True,  # Potion is consumed even if no effect
            "message": MB.info(
                "You drink the antidote. It tastes bitter but has no effect."
            )
        })
        return results
    
    if status_effects.has_effect("plague_of_restless_death"):
        # Remove the plague
        removal_results = status_effects.remove_effect("plague_of_restless_death")
        results.extend(removal_results)
        
        results.append({
            "consumed": True,
            "message": MB.healing(
                "You feel the foul corruption leave your body. The plague is cured!"
            )
        })
    else:
        results.append({
            "consumed": True,  # Potion is consumed even if no plague
            "message": MB.info(
                "You drink the antidote. It tastes bitter but you weren't infected."
            )
        })
    
    return results


def apply_plague_effect(*args, **kwargs):
    """Apply Plague of Restless Death to a target (from scroll or monster attack).
    
    Phase 10: Can only affect "corporeal_flesh" creatures.
    
    Args:
        *args: First argument should be the caster/source
        **kwargs: Should contain:
            - target_x, target_y: Coordinates of target (for scroll)
            - target: Direct target entity (for monster attack)
            - entities: List of all entities
            - fov_map: Field of view map
            - duration: Plague duration (default 20)
    
    Returns:
        list: List of result dictionaries with consumption and message info
    """
    caster = args[0] if args else None
    entities = kwargs.get("entities", [])
    fov_map = kwargs.get("fov_map")
    target_x = kwargs.get("target_x")
    target_y = kwargs.get("target_y")
    direct_target = kwargs.get("target")  # For monster attack
    duration = kwargs.get("duration", 20)
    
    results = []
    
    # Determine target
    target = direct_target
    if not target and target_x is not None and target_y is not None:
        # Find target at coordinates
        for entity in entities:
            if entity.x == target_x and entity.y == target_y:
                fighter = entity.get_component_optional(ComponentType.FIGHTER)
                if fighter and fighter.hp > 0:
                    target = entity
                    break
    
    if not target:
        return [{"consumed": False, "message": MB.warning("There is no valid target there.")}]
    
    # Check if target is "corporeal_flesh"
    is_corporeal_flesh = _is_corporeal_flesh(target)
    if not is_corporeal_flesh:
        results.append({
            "consumed": True,  # Scroll consumed even on invalid target
            "message": MB.spell_fail(
                f"The plague has no effect on {target.name} - they have no flesh to corrupt."
            )
        })
        return results
    
    # Check FOV for scroll usage (not needed for monster attacks)
    if direct_target is None and fov_map:
        if not map_is_in_fov(fov_map, target_x, target_y):
            return [{"consumed": False, "message": MB.warning("You cannot target something you cannot see.")}]
    
    # Apply the PlagueOfRestlessDeathEffect
    from components.status_effects import (
        StatusEffectManager, PlagueOfRestlessDeathEffect
    )
    
    # Ensure target has status_effects component
    if not target.components.has(ComponentType.STATUS_EFFECTS):
        target.status_effects = StatusEffectManager(target)
        target.components.add(ComponentType.STATUS_EFFECTS, target.status_effects)
    
    # Create and apply the effect
    plague_effect = PlagueOfRestlessDeathEffect(
        duration=duration,
        owner=target,
        damage_per_turn=1
    )
    effect_results = target.status_effects.add_effect(plague_effect)
    results.extend(effect_results)
    
    results.append({"consumed": True})
    
    return results


def _is_corporeal_flesh(entity) -> bool:
    """Check if an entity is corporeal flesh (can be infected by plague).
    
    Phase 10: Determines plague eligibility.
    
    Corporeal flesh includes:
    - Orcs, goblins, trolls
    - Cultists
    - Player
    - Beasts/animals (some independents)
    
    NOT corporeal flesh:
    - Slimes (no flesh)
    - Incorporeal undead (wraiths, ghosts)
    - Golems/elementals
    
    Args:
        entity: The entity to check
        
    Returns:
        True if entity has corporeal flesh
    """
    from components.faction import Faction
    
    # Check for explicit tag first
    if hasattr(entity, 'tags') and entity.tags:
        if 'corporeal_flesh' in entity.tags:
            return True
        if 'incorporeal' in entity.tags or 'no_flesh' in entity.tags:
            return False
    
    # Fallback: determine by faction and name
    faction = getattr(entity, 'faction', None)
    name_lower = entity.name.lower() if hasattr(entity, 'name') else ""
    
    # Player is always corporeal flesh
    if faction == Faction.PLAYER:
        return True
    
    # Orcs, cultists are corporeal flesh
    if faction in [Faction.ORC_FACTION, Faction.CULTIST, Faction.NEUTRAL]:
        return True
    
    # Slimes (HOSTILE_ALL) are not flesh
    if faction == Faction.HOSTILE_ALL:
        return False
    
    # Undead: check if incorporeal
    if faction == Faction.UNDEAD:
        # Incorporeal undead
        incorporeal_names = ['wraith', 'ghost', 'specter', 'shade', 'spirit', 'phantom']
        if any(x in name_lower for x in incorporeal_names):
            return False
        # Corporeal undead (zombies, skeletons) - already undead, can't be reinfected
        # But for gameplay, we might allow it. For now, treat as corporeal.
        # Actually, skeletons have no flesh. Zombies do.
        if 'skeleton' in name_lower or 'bone' in name_lower:
            return False
        # Zombies have rotting flesh
        if 'zombie' in name_lower:
            return True
        # Default undead: no
        return False
    
    # Independents: check by name
    if faction == Faction.INDEPENDENT:
        # Animals/beasts have flesh
        beast_names = ['wolf', 'bear', 'spider', 'snake', 'rat', 'bat', 'hound']
        if any(x in name_lower for x in beast_names):
            return True
        # Non-flesh independents
        non_flesh = ['slime', 'ooze', 'elemental', 'golem', 'construct']
        if any(x in name_lower for x in non_flesh):
            return False
        # Default independent: yes (assume beast)
        return True
    
    # Default: assume corporeal
    return True


def use_ward_scroll(*args, **kwargs):
    """Use a Ward Against Drain scroll to gain temporary immunity to life drain.
    
    Phase 19: Applies WardAgainstDrainEffect to the caster, which blocks
    wraith life drain for the specified duration (default 10 turns).
    
    Args:
        *args: First argument should be the caster (player)
        **kwargs: duration (optional, defaults to 10)
    
    Returns:
        list: List of result dictionaries with status effect application
    """
    caster = args[0] if args else None
    if not caster:
        return [{"consumed": False, "message": MB.failure("No caster!")}]
    
    results = []
    duration = kwargs.get('duration', 10)
    
    # Apply WardAgainstDrainEffect to the caster
    from components.status_effects import WardAgainstDrainEffect
    from components.component_registry import ComponentType
    
    # Ensure caster has status effect manager
    if not caster.status_effects:
        caster.status_effects = caster.get_status_effect_manager()
    
    # Create and apply the ward effect
    ward_effect = WardAgainstDrainEffect(duration=duration, owner=caster)
    effect_results = caster.add_status_effect(ward_effect)
    results.extend(effect_results)
    
    # Scroll is consumed
    results.append({"consumed": True})
    
    return results


def use_soul_ward_scroll(*args, **kwargs):
    """Use a Soul Ward scroll to gain protection against Soul Bolt damage.
    
    Phase 19: Applies SoulWardEffect to the caster, which:
    - Reduces Soul Bolt upfront damage by 70%
    - Converts prevented damage to Soul Burn DOT over 3 turns
    - Lasts for the specified duration (default 10 turns)
    
    Args:
        *args: First argument should be the caster (player)
        **kwargs: duration (optional, defaults to 10)
    
    Returns:
        list: List of result dictionaries with status effect application
    """
    caster = args[0] if args else None
    if not caster:
        return [{"consumed": False, "message": MB.failure("No caster!")}]
    
    results = []
    duration = kwargs.get('duration', 10)
    
    # Apply SoulWardEffect to the caster
    from components.status_effects import SoulWardEffect
    from components.component_registry import ComponentType
    
    # Ensure caster has status effect manager
    if not caster.status_effects:
        caster.status_effects = caster.get_status_effect_manager()
    
    # Create and apply the soul ward effect
    soul_ward_effect = SoulWardEffect(duration=duration, owner=caster)
    effect_results = caster.add_status_effect(soul_ward_effect)
    results.extend(effect_results)
    
    # Scroll is consumed
    results.append({"consumed": True})
    
    return results
