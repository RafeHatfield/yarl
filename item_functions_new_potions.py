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
        return [{"consumed": False, "message": MB.error("No entity to apply speed effect to!")}]
    
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
        return [{"consumed": False, "message": MB.error("No entity to apply regeneration effect to!")}]
    
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
    
    Note: Duration is longer than invisibility scroll (30 vs 10 turns).
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
        return [{"consumed": False, "message": MB.error("No entity to apply invisibility effect to!")}]
    
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
        return [{"consumed": False, "message": MB.error("No entity to apply levitation effect to!")}]
    
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
        return [{"consumed": False, "message": MB.error("No entity to apply protection effect to!")}]
    
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
        return [{"consumed": False, "message": MB.error("No entity to apply heroism effect to!")}]
    
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
        return [{"consumed": False, "message": MB.error("No entity to apply weakness effect to!")}]
    
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
        return [{"consumed": False, "message": MB.error("No entity to apply slowness effect to!")}]
    
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
        return [{"consumed": False, "message": MB.error("No entity to apply blindness effect to!")}]
    
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
        return [{"consumed": False, "message": MB.error("No entity to apply paralysis effect to!")}]
    
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
        return [{"consumed": False, "message": MB.error("No entity to gain experience!")}]
    
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

