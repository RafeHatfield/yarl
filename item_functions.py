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
from game_messages import Message
from fov_functions import map_is_in_fov
from render_functions import RenderOrder
from visual_effects import show_fireball, show_lightning, show_dragon_fart

# New spell system imports
from spells import cast_spell_by_id


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
    entities = kwargs.get("entities", [])
    fov_map = kwargs.get("fov_map")
    
    return cast_spell_by_id(
        "lightning",
        caster,
        entities=entities,
        fov_map=fov_map
    )


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
    caster = args[0]
    entities = kwargs.get("entities", [])
    fov_map = kwargs.get("fov_map")
    target_x = kwargs.get("target_x")
    target_y = kwargs.get("target_y")
    game_map = kwargs.get("game_map")
    
    return cast_spell_by_id(
        "fireball",
        caster,
        entities=entities,
        fov_map=fov_map,
        game_map=game_map,
        target_x=target_x,
        target_y=target_y
    )


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
    
    This function now delegates to the spell registry system.
    
    Args:
        *args: First argument should be the entity using the scroll
        **kwargs: Should contain 'min_bonus' and 'max_bonus' for damage enhancement
        
    Returns:
        list: List of result dictionaries with consumption and message info
    """
    # Delegate to new spell system
    caster = args[0]
    min_bonus = kwargs.get("min_bonus", 1)
    max_bonus = kwargs.get("max_bonus", 2)
    
    return cast_spell_by_id(
        "enhance_weapon",
        caster,
        min_bonus=min_bonus,
        max_bonus=max_bonus
    )


def enhance_armor(*args, **kwargs):
    """Enhance a random equipped armor piece's AC bonus.
    
    This function now delegates to the spell registry system.
    
    Args:
        *args: First argument should be the entity using the scroll
        **kwargs: Should contain 'bonus' key for AC enhancement (default +1)
        
    Returns:
        list: List of result dictionaries with consumption and message info
    """
    entity = args[0]
    bonus = kwargs.get("bonus", 1)  # Default +1 AC
    
    # Delegate to new spell system
    return cast_spell_by_id(
        "enhance_armor",
        entity,
        bonus=bonus
    )


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
    
    # Delegate to new spell system
    return cast_spell_by_id(
        "invisibility",
        entity,
        entities=[],
        fov_map=None
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
    
    # Delegate to new spell system
    return cast_spell_by_id(
        "rage",
        caster,
        entities=entities,
        fov_map=fov_map,
        target_x=target_x,
        target_y=target_y
    )
