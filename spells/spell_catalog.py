"""Catalog of all game spells.

This module defines all the spells in the game using SpellDefinition objects.
It replaces the scattered spell functions in item_functions.py with a 
centralized, declarative catalog.
"""

from spells.spell_definition import SpellDefinition
from spells.spell_types import SpellCategory, TargetingType, DamageType, EffectType
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


# === UTILITY SPELLS ===

CONFUSION = SpellDefinition(
    spell_id="confusion",
    name="Confusion",
    category=SpellCategory.UTILITY,
    targeting=TargetingType.SINGLE_ANY,
    effect_type=EffectType.CONFUSION,
    duration=10,
    requires_los=True,
    requires_target=True,
    max_range=10,
    success_message="The eyes of the {0} look vacant, as he starts to stumble around!",
    no_target_message="There is no targetable enemy at that location.",
    consumable=True
)

TELEPORT = SpellDefinition(
    spell_id="teleport",
    name="Teleport",
    category=SpellCategory.UTILITY,
    targeting=TargetingType.LOCATION,
    requires_los=True,
    requires_target=False,
    max_range=20,
    success_message="✨ You teleport in a flash of light!",
    consumable=True
)

SLOW = SpellDefinition(
    spell_id="slow",
    name="Slow",
    category=SpellCategory.UTILITY,
    targeting=TargetingType.SINGLE_ENEMY,
    effect_type=EffectType.SLOW,
    duration=10,
    requires_los=True,
    requires_target=True,
    max_range=10,
    success_message="{0} has been slowed!",
    no_target_message="There is no valid target there.",
    consumable=True
)

GLUE = SpellDefinition(
    spell_id="glue",
    name="Glue",
    category=SpellCategory.UTILITY,
    targeting=TargetingType.SINGLE_ENEMY,
    effect_type=EffectType.GLUE,
    duration=5,
    requires_los=True,
    requires_target=True,
    max_range=10,
    success_message="{0} is stuck in magical glue!",
    no_target_message="There is no valid target there.",
    consumable=True
)

RAGE = SpellDefinition(
    spell_id="rage",
    name="Rage",
    category=SpellCategory.UTILITY,
    targeting=TargetingType.SINGLE_ANY,
    effect_type=EffectType.RAGE,
    duration=8,
    requires_los=True,
    requires_target=True,
    max_range=10,
    success_message="{0} goes into a berserker rage!",
    no_target_message="There is no valid target there.",
    consumable=True
)


# === BUFF SPELLS ===

SHIELD = SpellDefinition(
    spell_id="shield",
    name="Shield",
    category=SpellCategory.BUFF,
    targeting=TargetingType.SELF,
    duration=10,
    requires_los=False,
    requires_target=False,
    success_message="A magical shield surrounds you!",
    consumable=True
)

INVISIBILITY = SpellDefinition(
    spell_id="invisibility",
    name="Invisibility",
    category=SpellCategory.BUFF,
    targeting=TargetingType.SELF,
    duration=10,
    requires_los=False,
    requires_target=False,
    success_message="You fade from view!",
    consumable=True
)

ENHANCE_WEAPON = SpellDefinition(
    spell_id="enhance_weapon",
    name="Enhance Weapon",
    category=SpellCategory.BUFF,
    targeting=TargetingType.SELF,
    requires_los=False,
    requires_target=False,
    success_message="Your weapon glows with power!",
    consumable=True
)

ENHANCE_ARMOR = SpellDefinition(
    spell_id="enhance_armor",
    name="Enhance Armor",
    category=SpellCategory.BUFF,
    targeting=TargetingType.SELF,
    requires_los=False,
    requires_target=False,
    success_message="Your armor shimmers with magic!",
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
    
    # Utility spells
    register_spell(CONFUSION)
    register_spell(TELEPORT)
    register_spell(SLOW)
    register_spell(GLUE)
    register_spell(RAGE)
    
    # Buff spells
    register_spell(SHIELD)
    register_spell(ENHANCE_WEAPON)
    register_spell(ENHANCE_ARMOR)
    register_spell(INVISIBILITY)

