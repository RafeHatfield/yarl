"""Spell system for the roguelike game.

This package provides a unified spell system that replaces the scattered
spell functions in item_functions.py. It includes:

- SpellDefinition: Declarative spell data
- SpellRegistry: Central spell storage
- SpellExecutor: Unified spell casting
- SpellCatalog: All game spells

Usage:
    >>> from spells import cast_spell_by_id
    >>> results = cast_spell_by_id("fireball", caster, entities, fov_map, ...)
"""

from spells.spell_types import SpellCategory, TargetingType, DamageType, EffectType
from spells.spell_definition import SpellDefinition
from spells.spell_registry import (
    SpellRegistry,
    get_spell_registry,
    register_spell,
    get_spell,
)
from spells.spell_executor import SpellExecutor, get_spell_executor


def cast_spell_by_id(spell_id: str, caster, *args, **kwargs):
    """Convenience function to cast a spell by its ID.
    
    This is the main entry point for casting spells in the new system.
    It replaces calling individual spell functions.
    
    Args:
        spell_id: Unique spell identifier (e.g., "fireball")
        caster: Entity casting the spell
        *args: Additional positional arguments
        **kwargs: Keyword arguments (entities, fov_map, target_x, target_y, etc.)
        
    Returns:
        List of result dictionaries
        
    Example:
        >>> results = cast_spell_by_id(
        ...     "fireball",
        ...     player,
        ...     entities=entities,
        ...     fov_map=fov_map,
        ...     target_x=10,
        ...     target_y=15,
        ...     game_map=game_map
        ... )
    """
    from message_builder import MessageBuilder as MB
    
    registry = get_spell_registry()
    executor = get_spell_executor()
    
    spell = registry.get(spell_id)
    if not spell:
        return [
            {
                "consumed": False,
                "message": MB.failure(f"Unknown spell: {spell_id}")
            }
        ]
    
    return executor.cast(spell, caster, *args, **kwargs)


__all__ = [
    # Types
    "SpellCategory",
    "TargetingType",
    "DamageType",
    "EffectType",
    
    # Core classes
    "SpellDefinition",
    "SpellRegistry",
    "SpellExecutor",
    
    # Functions
    "get_spell_registry",
    "get_spell_executor",
    "register_spell",
    "get_spell",
    "cast_spell_by_id",
]

