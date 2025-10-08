"""Catalog of all game spells.

This module defines all the spells in the game using SpellDefinition objects.
It replaces the scattered spell functions in item_functions.py with a 
centralized, declarative catalog.
"""

from spells.spell_definition import SpellDefinition
from spells.spell_types import SpellCategory, TargetingType, DamageType
from spells.spell_registry import register_spell
from visual_effects import show_fireball, show_lightning, show_dragon_fart


# === OFFENSIVE SPELLS ===

LIGHTNING_BOLT = SpellDefinition(
    spell_id="lightning",
    name="Lightning Bolt",
    category=SpellCategory.OFFENSIVE,
    targeting=TargetingType.SINGLE_ENEMY,
    damage="3d8",  # ~13.5 average
    damage_type=DamageType.LIGHTNING,
    max_range=10,
    requires_los=True,
    requires_target=True,
    cast_message="",  # No cast message, goes straight to hit
    success_message="A lighting bolt strikes the {0} with a loud thunder! The damage is {1}",
    fail_message="No enemy is close enough to strike.",
    visual_effect=show_lightning,
    consumable=True
)

FIREBALL = SpellDefinition(
    spell_id="fireball",
    name="Fireball",
    category=SpellCategory.OFFENSIVE,
    targeting=TargetingType.AOE,
    damage="3d6",  # ~10.5 average
    damage_type=DamageType.FIRE,
    radius=3,
    max_range=10,
    requires_los=True,
    requires_target=False,  # Targets location, not entity
    cast_message="The fireball explodes, burning everything within {0} tiles!",
    creates_hazard=True,
    hazard_type="fire",
    hazard_duration=3,
    hazard_damage=3,
    visual_effect=show_fireball,
    consumable=True
)

DRAGON_FART = SpellDefinition(
    spell_id="dragon_fart",
    name="Dragon Fart",
    category=SpellCategory.OFFENSIVE,
    targeting=TargetingType.CONE,
    damage="2d8",  # ~9 average
    damage_type=DamageType.POISON,
    cone_range=8,
    cone_width=45,
    max_range=8,
    requires_los=True,
    requires_target=False,
    cast_message="💨 The dragon farts a noxious cloud of poison gas!",
    creates_hazard=True,
    hazard_type="poison",
    hazard_duration=5,
    hazard_damage=3,
    visual_effect=show_dragon_fart,
    consumable=True
)


# === HEALING SPELLS ===

HEAL = SpellDefinition(
    spell_id="heal",
    name="Healing Potion",
    category=SpellCategory.HEALING,
    targeting=TargetingType.SELF,
    heal_amount=20,
    requires_los=False,
    requires_target=False,
    consumable=True
)


def register_all_spells():
    """Register all spells in the catalog with the global registry.
    
    This function should be called once at game startup to populate
    the spell registry with all available spells.
    """
    # Offensive spells
    register_spell(LIGHTNING_BOLT)
    register_spell(FIREBALL)
    register_spell(DRAGON_FART)
    
    # Healing spells
    register_spell(HEAL)
    
    # TODO: Add utility spells (confusion, teleport, slow, glue, rage)
    # TODO: Add buff spells (shield, enhance_weapon, enhance_armor)
    # TODO: Add summon spells (raise_dead)

