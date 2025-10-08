"""Spell execution engine.

This module handles the actual casting of spells based on their definitions.
It replaces the scattered spell logic in item_functions.py with a unified
execution engine.
"""

from typing import List, Dict, Any, Optional
import math
from spells.spell_definition import SpellDefinition
from spells.spell_types import SpellCategory, TargetingType, DamageType, EffectType
from game_messages import Message
from fov_functions import map_is_in_fov
from dice import roll_dice


class SpellExecutor:
    """Executes spells based on their definitions.
    
    The SpellExecutor takes a SpellDefinition and handles all the logic
    for casting it: finding targets, dealing damage, applying effects,
    creating hazards, and generating messages.
    """
    
    def __init__(self):
        """Initialize the spell executor."""
        pass
    
    def cast(
        self,
        spell: SpellDefinition,
        caster,
        entities: List = None,
        fov_map=None,
        game_map=None,
        target_x: Optional[int] = None,
        target_y: Optional[int] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Cast a spell.
        
        Args:
            spell: SpellDefinition to cast
            caster: Entity casting the spell
            entities: List of all entities
            fov_map: Field of view map
            game_map: Game map (for hazards)
            target_x: X coordinate for targeted spells
            target_y: Y coordinate for targeted spells
            **kwargs: Additional parameters (damage, maximum_range, etc.)
            
        Returns:
            List of result dictionaries with consumption, messages, etc.
        """
        results = []
        
        # Handle entities/fov_map from kwargs for backward compatibility
        entities = entities if entities is not None else kwargs.get("entities", [])
        fov_map = fov_map if fov_map is not None else kwargs.get("fov_map")
        game_map = game_map if game_map is not None else kwargs.get("game_map")
        target_x = target_x if target_x is not None else kwargs.get("target_x")
        target_y = target_y if target_y is not None else kwargs.get("target_y")
        
        # Validate edge case parameters from kwargs
        damage_override = kwargs.get("damage")
        range_override = kwargs.get("maximum_range")
        
        # Check for invalid range (negative if specified)
        if range_override is not None and range_override < 0:
            return [{"consumed": False, "message": Message("Invalid spell range!", (255, 255, 0))}]
        
        # Check for invalid damage (negative only, zero is allowed)
        if damage_override is not None and damage_override < 0:
            return [{"consumed": False, "message": Message("Invalid spell parameters!", (255, 255, 0))}]
        
        # Handle different spell categories
        if spell.category == SpellCategory.OFFENSIVE:
            return self._cast_offensive_spell(
                spell, caster, entities, fov_map, game_map, target_x, target_y, **kwargs
            )
        elif spell.category == SpellCategory.HEALING:
            return self._cast_healing_spell(spell, caster, **kwargs)
        elif spell.category == SpellCategory.UTILITY:
            return self._cast_utility_spell(
                spell, caster, entities, fov_map, game_map, target_x, target_y, **kwargs
            )
        elif spell.category == SpellCategory.BUFF:
            return self._cast_buff_spell(spell, caster, entities, target_x, target_y, **kwargs)
        elif spell.category == SpellCategory.SUMMON:
            return self._cast_summon_spell(spell, caster, entities, fov_map, target_x, target_y, **kwargs)
        else:
            return [
                {
                    "consumed": False,
                    "message": Message("Unknown spell category!", (255, 0, 0))
                }
            ]
    
    def _cast_offensive_spell(
        self,
        spell: SpellDefinition,
        caster,
        entities: List,
        fov_map,
        game_map,
        target_x: Optional[int],
        target_y: Optional[int],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Cast an offensive/damage spell.
        
        Handles single-target, AoE, and cone damage spells.
        """
        results = []
        
        # Handle different targeting types
        if spell.targeting == TargetingType.SINGLE_ENEMY:
            # Auto-target closest enemy (like lightning)
            return self._cast_auto_target_spell(spell, caster, entities, fov_map, **kwargs)
        
        elif spell.targeting == TargetingType.AOE:
            # Area of effect (like fireball)
            return self._cast_aoe_spell(
                spell, caster, entities, fov_map, game_map, target_x, target_y, **kwargs
            )
        
        elif spell.targeting == TargetingType.CONE:
            # Cone attack (like dragon fart)
            return self._cast_cone_spell(
                spell, caster, entities, fov_map, game_map, target_x, target_y, **kwargs
            )
        
        return results
    
    def _cast_auto_target_spell(
        self,
        spell: SpellDefinition,
        caster,
        entities: List,
        fov_map,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Cast a spell that auto-targets the closest enemy (e.g., lightning).
        
        This is used for spells like Lightning Bolt that automatically find
        and strike the nearest visible enemy within range.
        """
        results = []
        
        # Get overrides from kwargs (used for item customization)
        damage_override = kwargs.get("damage")
        range_override = kwargs.get("maximum_range")
        
        # Find closest enemy in range
        max_range = range_override if range_override is not None else spell.max_range
        target = None
        closest_distance = max_range + 1
        
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
        
        if not target:
            return [
                {
                    "consumed": False,
                    "target": None,
                    "message": Message(
                        spell.fail_message or "No enemy is close enough to strike.",
                        (255, 0, 0)
                    ),
                }
            ]
        
        # Calculate damage (use override if provided, including 0)
        if "damage" in kwargs:
            damage = kwargs["damage"]
        else:
            damage = self._calculate_damage(spell.damage) if spell.damage else 0
        
        # Show visual effect if defined
        if spell.visual_effect:
            # For lightning, calculate path from caster to target
            path = self._bresenham_line(caster.x, caster.y, target.x, target.y)
            spell.visual_effect(path)
        
        # Apply damage
        message_text = spell.success_message or f"The {spell.name} strikes the {target.name} for {damage} damage!"
        results.append(
            {
                "consumed": True,
                "target": target,
                "message": Message(message_text.format(target.name, damage)),
            }
        )
        results.extend(target.fighter.take_damage(damage))
        
        return results
    
    def _cast_aoe_spell(
        self,
        spell: SpellDefinition,
        caster,
        entities: List,
        fov_map,
        game_map,
        target_x: int,
        target_y: int,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Cast an area-of-effect spell (e.g., fireball).
        
        Damages all entities within radius of the target location.
        Can optionally create ground hazards.
        """
        results = []
        
        # Check line of sight if required
        if spell.requires_los and not map_is_in_fov(fov_map, target_x, target_y):
            return [
                {
                    "consumed": False,
                    "message": Message(
                        "You cannot target a tile outside your field of view.",
                        (255, 255, 0),
                    ),
                }
            ]
        
        # Cast message
        cast_msg = spell.cast_message or f"The {spell.name} explodes!"
        results.append(
            {
                "consumed": True,
                "message": Message(cast_msg, (255, 127, 0)),
            }
        )
        
        # Show visual effect
        if spell.visual_effect:
            explosion_tiles = []
            for dx in range(-spell.radius, spell.radius + 1):
                for dy in range(-spell.radius, spell.radius + 1):
                    distance = math.sqrt(dx**2 + dy**2)
                    if distance <= spell.radius:
                        explosion_tiles.append((target_x + dx, target_y + dy))
            spell.visual_effect(explosion_tiles)
        
        # Deal damage to entities in radius (use override if provided, including 0)
        if "damage" in kwargs:
            damage = kwargs["damage"]
        else:
            damage = self._calculate_damage(spell.damage) if spell.damage else 0
        
        for entity in entities:
            if entity.fighter:
                distance = math.sqrt(
                    (entity.x - target_x) ** 2 + (entity.y - target_y) ** 2
                )
                if distance <= spell.radius:
                    results.append(
                        {
                            "message": Message(
                                f"The {entity.name} gets burned for {damage} hit points."
                            )
                        }
                    )
                    results.extend(entity.fighter.take_damage(damage))
        
        # Create ground hazards if defined
        if spell.creates_hazard and game_map and hasattr(game_map, 'hazard_manager'):
            from components.ground_hazard import HazardType
            
            hazard_type_map = {
                "fire": HazardType.FIRE,
                "poison": HazardType.POISON_GAS,
            }
            
            hazard_type = hazard_type_map.get(spell.hazard_type)
            if hazard_type:
                for dx in range(-spell.radius, spell.radius + 1):
                    for dy in range(-spell.radius, spell.radius + 1):
                        distance = math.sqrt(dx**2 + dy**2)
                        if distance <= spell.radius:
                            hx, hy = target_x + dx, target_y + dy
                            game_map.hazard_manager.add_hazard(
                                x=hx,
                                y=hy,
                                hazard_type=hazard_type,
                                duration=spell.hazard_duration,
                                damage=spell.hazard_damage
                            )
        
        return results
    
    def _cast_cone_spell(
        self,
        spell: SpellDefinition,
        caster,
        entities: List,
        fov_map,
        game_map,
        target_x: int,
        target_y: int
    ) -> List[Dict[str, Any]]:
        """Cast a cone-shaped spell (e.g., dragon fart).
        
        Similar to AoE but uses cone geometry.
        """
        # Import cone helper from item_functions (for now, we'll migrate this later)
        from item_functions import get_cone_tiles
        
        results = []
        
        # Check line of sight if required
        if spell.requires_los and not map_is_in_fov(fov_map, target_x, target_y):
            return [
                {
                    "consumed": False,
                    "message": Message(
                        "You cannot target a tile outside your field of view.",
                        (255, 255, 0),
                    ),
                }
            ]
        
        # Get cone tiles
        cone_tiles = get_cone_tiles(
            caster.x, caster.y,
            target_x, target_y,
            max_range=spell.cone_range,
            cone_width=spell.cone_width
        )
        
        # Cast message
        cast_msg = spell.cast_message or f"The {spell.name} erupts in a cone!"
        results.append(
            {
                "consumed": True,
                "message": Message(cast_msg, (100, 255, 100)),
            }
        )
        
        # Show visual effect
        if spell.visual_effect:
            spell.visual_effect(cone_tiles)
        
        # Deal damage to entities in cone
        damage = self._calculate_damage(spell.damage) if spell.damage else 0
        
        for entity in entities:
            if entity.fighter and (entity.x, entity.y) in cone_tiles:
                results.append(
                    {
                        "message": Message(
                            f"The {entity.name} is caught in the blast for {damage} hit points!"
                        )
                    }
                )
                results.extend(entity.fighter.take_damage(damage))
        
        # Create ground hazards if defined
        if spell.creates_hazard and game_map and hasattr(game_map, 'hazard_manager'):
            from components.ground_hazard import HazardType
            
            hazard_type_map = {
                "fire": HazardType.FIRE,
                "poison": HazardType.POISON_GAS,
            }
            
            hazard_type = hazard_type_map.get(spell.hazard_type)
            if hazard_type:
                for hx, hy in cone_tiles:
                    game_map.hazard_manager.add_hazard(
                        x=hx,
                        y=hy,
                        hazard_type=hazard_type,
                        duration=spell.hazard_duration,
                        damage=spell.hazard_damage
                    )
        
        return results
    
    def _cast_healing_spell(
        self,
        spell: SpellDefinition,
        caster,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Cast a healing spell.
        
        Restores HP to the caster.
        """
        results = []
        
        if caster.fighter.hp == caster.fighter.max_hp:
            return [
                {
                    "consumed": False,
                    "message": Message("You are already at full health", (255, 255, 0)),
                }
            ]
        
        # Allow amount override from kwargs (for backward compatibility with potions)
        heal_amount = kwargs.get("amount", spell.heal_amount)
        
        caster.fighter.heal(heal_amount)
        results.append(
            {
                "consumed": True,
                "message": Message("Your wounds start to feel better!", (0, 255, 0)),
            }
        )
        
        return results
    
    def _cast_utility_spell(
        self,
        spell: SpellDefinition,
        caster,
        entities: List,
        fov_map,
        game_map,
        target_x: Optional[int],
        target_y: Optional[int],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Cast a utility spell (confusion, teleport, etc.).
        
        Handles confusion, status effect application, and teleportation.
        """
        results = []
        
        # Check line of sight if required
        if spell.requires_los and target_x is not None and target_y is not None:
            if not map_is_in_fov(fov_map, target_x, target_y):
                return [
                    {
                        "consumed": False,
                        "message": Message(
                            "You cannot target a tile outside your field of view.",
                            (255, 255, 0),
                        ),
                    }
                ]
        
        # Handle different effect types
        if spell.effect_type == EffectType.CONFUSION:
            return self._cast_confusion_spell(spell, caster, entities, target_x, target_y)
        elif spell.effect_type in [EffectType.SLOW, EffectType.GLUE, EffectType.RAGE]:
            return self._cast_status_effect_spell(spell, caster, entities, fov_map, target_x, target_y)
        elif spell.spell_id == "teleport":
            return self._cast_teleport_spell(spell, caster, entities, game_map, target_x, target_y)
        
        return [
            {
                "consumed": False,
                "message": Message("Unknown utility spell effect!", (255, 0, 0))
            }
        ]
    
    def _cast_confusion_spell(
        self,
        spell: SpellDefinition,
        caster,
        entities: List,
        target_x: int,
        target_y: int
    ) -> List[Dict[str, Any]]:
        """Cast confusion spell that replaces target's AI."""
        from components.ai import ConfusedMonster
        from components.component_registry import ComponentType
        
        # Find target entity at location
        target = None
        for entity in entities:
            if entity.x == target_x and entity.y == target_y and entity.components.has(ComponentType.AI):
                target = entity
                break
        
        if not target:
            return [
                {
                    "consumed": False,
                    "message": Message(
                        spell.no_target_message,
                        (255, 255, 0)
                    ),
                }
            ]
        
        # Replace AI with confused AI
        confused_ai = ConfusedMonster(target.ai, spell.duration)
        confused_ai.owner = target
        target.ai = confused_ai
        
        message_text = spell.success_message or f"The eyes of the {target.name} look vacant!"
        return [
            {
                "consumed": True,
                "message": Message(
                    message_text.format(target.name),
                    (63, 255, 63),
                ),
            }
        ]
    
    def _cast_status_effect_spell(
        self,
        spell: SpellDefinition,
        caster,
        entities: List,
        fov_map,
        target_x: int,
        target_y: int
    ) -> List[Dict[str, Any]]:
        """Cast spell that applies a status effect (slow, glue, rage)."""
        from components.status_effects import SlowedEffect, GluedEffect, EnragedEffect, StatusEffectManager
        from components.component_registry import ComponentType
        
        # Find target entity
        target = None
        for entity in entities:
            if entity.x == target_x and entity.y == target_y and entity.components.has(ComponentType.FIGHTER):
                target = entity
                break
        
        if not target:
            return [
                {
                    "consumed": False,
                    "message": Message(spell.no_target_message, (255, 255, 0))
                }
            ]
        
        # Ensure target has status_effects component
        if not target.components.has(ComponentType.STATUS_EFFECTS):
            target.status_effects = StatusEffectManager(target)
            target.components.add(ComponentType.STATUS_EFFECTS, target.status_effects)
        
        # Create appropriate status effect
        effect = None
        if spell.effect_type == EffectType.SLOW:
            effect = SlowedEffect(duration=spell.duration, owner=target)
        elif spell.effect_type == EffectType.GLUE:
            effect = GluedEffect(duration=spell.duration, owner=target)
        elif spell.effect_type == EffectType.RAGE:
            effect = EnragedEffect(duration=spell.duration, owner=target)
        
        if effect:
            effect_results = target.status_effects.add_effect(effect)
            return [{"consumed": True}] + effect_results
        
        return [
            {
                "consumed": False,
                "message": Message("Failed to apply status effect!", (255, 0, 0))
            }
        ]
    
    def _cast_teleport_spell(
        self,
        spell: SpellDefinition,
        caster,
        entities: List,
        game_map,
        target_x: int,
        target_y: int
    ) -> List[Dict[str, Any]]:
        """Cast teleport spell to move caster to target location."""
        # Check if target location is valid
        if game_map.is_blocked(target_x, target_y):
            return [
                {
                    "consumed": False,
                    "message": Message(
                        "You cannot teleport into a wall!",
                        (255, 255, 0)
                    ),
                }
            ]
        
        # Check if location is occupied
        for entity in entities:
            if entity.x == target_x and entity.y == target_y and entity != caster:
                if entity.blocks:
                    return [
                        {
                            "consumed": False,
                            "message": Message(
                                "That location is occupied!",
                                (255, 255, 0)
                            ),
                        }
                    ]
        
        # Teleport!
        old_x, old_y = caster.x, caster.y
        caster.x = target_x
        caster.y = target_y
        
        message_text = spell.success_message or f"You teleport from ({old_x},{old_y}) to ({target_x},{target_y})!"
        return [
            {
                "consumed": True,
                "message": Message(message_text, (127, 0, 255)),  # Purple
                "fov_recompute": True  # Request FOV recomputation
            }
        ]
    
    def _cast_buff_spell(
        self,
        spell: SpellDefinition,
        caster,
        entities: List,
        target_x: Optional[int],
        target_y: Optional[int],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Cast a buff/enhancement spell.
        
        Handles shield, invisibility, and equipment enhancements.
        """
        # Handle shield spell
        if spell.spell_id == "shield":
            return self._cast_shield_spell(spell, caster)
        
        # Handle invisibility
        elif spell.spell_id == "invisibility":
            return self._cast_invisibility_spell(spell, caster)
        
        # Handle equipment enhancements
        elif spell.spell_id == "enhance_weapon":
            return self._cast_enhance_weapon_spell(spell, caster, **kwargs)
        elif spell.spell_id == "enhance_armor":
            return self._cast_enhance_armor_spell(spell, caster, **kwargs)
        
        return [
            {
                "consumed": False,
                "message": Message("Unknown buff spell!", (255, 0, 0))
            }
        ]
    
    def _cast_shield_spell(
        self,
        spell: SpellDefinition,
        caster
    ) -> List[Dict[str, Any]]:
        """Cast shield spell for defense boost."""
        from components.status_effects import ShieldEffect, StatusEffectManager
        from components.component_registry import ComponentType
        
        results = []
        
        # Ensure caster has status_effects component
        if not caster.components.has(ComponentType.STATUS_EFFECTS):
            caster.status_effects = StatusEffectManager(caster)
            caster.components.add(ComponentType.STATUS_EFFECTS, caster.status_effects)
        
        # Create shield effect
        shield_effect = ShieldEffect(
            duration=spell.duration,
            owner=caster,
            defense_bonus=4  # Default +4 defense
        )
        
        effect_results = caster.status_effects.add_effect(shield_effect)
        results.extend(effect_results)
        results.append({"consumed": True})
        
        return results
    
    def _cast_invisibility_spell(
        self,
        spell: SpellDefinition,
        caster
    ) -> List[Dict[str, Any]]:
        """Cast invisibility spell."""
        from components.status_effects import InvisibilityEffect, StatusEffectManager
        from components.component_registry import ComponentType
        
        results = []
        
        # Ensure caster has status_effects component
        if not caster.components.has(ComponentType.STATUS_EFFECTS):
            caster.status_effects = StatusEffectManager(caster)
            caster.components.add(ComponentType.STATUS_EFFECTS, caster.status_effects)
        
        # Create invisibility effect
        invisibility_effect = InvisibilityEffect(
            duration=spell.duration,
            owner=caster
        )
        
        effect_results = caster.status_effects.add_effect(invisibility_effect)
        results.extend(effect_results)
        results.append({"consumed": True})
        
        return results
    
    def _cast_enhance_weapon_spell(
        self,
        spell: SpellDefinition,
        caster,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Enhance equipped weapon's damage."""
        from components.component_registry import ComponentType
        
        min_bonus = kwargs.get("min_bonus", 1)
        max_bonus = kwargs.get("max_bonus", 2)
        
        results = []
        
        # Check for equipped weapon
        equipment = caster.components.get(ComponentType.EQUIPMENT)
        if not equipment:
            equipment = getattr(caster, 'equipment', None)
        
        if (equipment and equipment.main_hand and 
            (equipment.main_hand.components.has(ComponentType.EQUIPPABLE) or 
             hasattr(equipment.main_hand, 'equippable'))):
            weapon = equipment.main_hand
            old_min = weapon.equippable.damage_min
            old_max = weapon.equippable.damage_max
            
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
    
    def _cast_enhance_armor_spell(
        self,
        spell: SpellDefinition,
        caster,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Enhance equipped armor's AC bonus."""
        from components.component_registry import ComponentType
        import random
        
        bonus = kwargs.get("bonus", 1)
        
        results = []
        
        # Check for equipment
        equipment = caster.components.get(ComponentType.EQUIPMENT)
        if not equipment:
            equipment = getattr(caster, 'equipment', None)
        
        if not equipment:
            return [{
                "consumed": False,
                "message": Message("You have no equipment to enhance!", (255, 255, 0))
            }]
        
        # Find equipped armor pieces
        armor_pieces = []
        for slot_name in ['head', 'chest', 'off_hand']:
            armor = getattr(equipment, slot_name, None)
            if armor and (armor.components.has(ComponentType.EQUIPPABLE) or hasattr(armor, 'equippable')):
                # Check if it's armor (not a weapon)
                equippable = armor.components.get(ComponentType.EQUIPPABLE) or getattr(armor, 'equippable', None)
                if equippable and hasattr(equippable, 'armor_class_bonus'):
                    armor_pieces.append((slot_name, armor))
        
        if not armor_pieces:
            return [{
                "consumed": False,
                "message": Message("You have no armor equipped to enhance!", (255, 255, 0))
            }]
        
        # Randomly select an armor piece
        slot_name, armor = random.choice(armor_pieces)
        old_bonus = armor.equippable.armor_class_bonus
        
        armor.equippable.modify_ac_bonus(bonus)
        
        results.append({
            "consumed": True,
            "message": Message(
                f"Your {armor.name} glows with magical energy! "
                f"AC bonus increased from +{old_bonus} to +{armor.equippable.armor_class_bonus}.",
                (0, 255, 0)
            )
        })
        
        return results
    
    def _cast_summon_spell(
        self,
        spell: SpellDefinition,
        caster,
        entities: List,
        fov_map,
        target_x: Optional[int],
        target_y: Optional[int],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Cast a summoning spell.
        
        Handles spells that create or resurrect entities.
        """
        if spell.spell_id == "raise_dead":
            return self._cast_raise_dead_spell(spell, caster, entities, target_x, target_y, **kwargs)
        elif spell.spell_id == "yo_mama":
            # Yo Mama is actually a utility spell (taunt), but categorized here for organization
            return self._cast_yo_mama_spell(spell, caster, entities, fov_map, target_x, target_y, **kwargs)
        else:
            return [{
                "consumed": False,
                "message": Message(f"Unsupported summon spell: {spell.spell_id}", (255, 0, 0))
            }]
    
    def _cast_raise_dead_spell(
        self,
        spell: SpellDefinition,
        caster,
        entities: List,
        target_x: Optional[int],
        target_y: Optional[int],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Cast raise dead spell - resurrect a corpse as a zombie."""
        import math
        from entity import get_blocking_entities_at_location
        from components.fighter import Fighter
        from components.ai import HostileAI
        from config.entity_registry import get_entity_registry
        from render_order import RenderOrder
        from components.component_registry import ComponentType
        
        results = []
        max_range = kwargs.get("range", spell.max_range)
        
        # Validate target
        if target_x is None or target_y is None:
            return [{
                "consumed": False,
                "message": Message(spell.no_target_message or "You must select a corpse!", (255, 255, 0))
            }]
        
        # Check range
        distance = math.sqrt((target_x - caster.x) ** 2 + (target_y - caster.y) ** 2)
        if distance > max_range:
            return [{
                "consumed": False,
                "message": Message("That corpse is too far away!", (255, 255, 0))
            }]
        
        # Find corpse at location
        corpse = None
        for ent in entities:
            if (ent.x == target_x and ent.y == target_y and 
                ent.name.startswith("remains of ")):
                corpse = ent
                break
        
        if not corpse:
            return [{
                "consumed": False,
                "message": Message(spell.fail_message or "No corpse there!", (255, 255, 0))
            }]
        
        # Check if location is blocked
        blocking_entity = get_blocking_entities_at_location(entities, corpse.x, corpse.y)
        if blocking_entity and blocking_entity != corpse:
            return [{
                "consumed": False,
                "message": Message(f"{blocking_entity.name} is in the way!", (255, 255, 0))
            }]
        
        # Resurrect the corpse!
        original_name = corpse.name.replace("remains of ", "")
        corpse.name = f"Zombified {original_name}"
        corpse.color = (40, 40, 40)  # Dark gray/black
        corpse.blocks = True
        corpse.render_order = RenderOrder.ACTOR
        
        # Get original stats
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
            # Fallback defaults
            base_hp = 10
            base_defense = 0
            base_power = 3
            base_damage_min = 1
            base_damage_max = 3
            base_strength = 10
            base_dexterity = 10
            base_constitution = 10
        
        # Create zombie: 2x HP, 0.5x damage
        zombie_hp = base_hp * 2
        zombie_power = max(1, int(base_power * 0.5))
        zombie_damage_min = max(1, int(base_damage_min * 0.5))
        zombie_damage_max = max(1, int(base_damage_max * 0.5))
        zombie_strength = max(6, int(base_strength * 0.75))
        zombie_dexterity = max(6, int(base_dexterity * 0.5))
        zombie_constitution = min(18, int(base_constitution * 1.5))
        
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
        corpse.components.add(ComponentType.FIGHTER, corpse.fighter)
        
        # Add hostile AI (attacks everything)
        corpse.ai = HostileAI()
        corpse.ai.owner = corpse
        corpse.components.add(ComponentType.AI, corpse.ai)
        
        results.append({
            "consumed": True,
            "message": Message(spell.success_message or f"{corpse.name} rises!", (0, 255, 0))
        })
        
        return results
    
    def _cast_yo_mama_spell(
        self,
        spell: SpellDefinition,
        caster,
        entities: List,
        fov_map,
        target_x: Optional[int],
        target_y: Optional[int],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Cast Yo Mama spell - target yells a joke and becomes taunted."""
        import yaml
        import random
        import os
        from components.status_effects import TauntedTargetEffect, StatusEffectManager
        from components.component_registry import ComponentType
        
        results = []
        
        # Check if target in FOV
        if not map_is_in_fov(fov_map, target_x, target_y):
            return [{
                "consumed": False,
                "message": Message("You cannot target something you cannot see.", (255, 255, 0))
            }]
        
        # Find target
        target = None
        for entity in entities:
            if entity.x == target_x and entity.y == target_y and entity.fighter:
                target = entity
                break
        
        if not target:
            return [{
                "consumed": False,
                "message": Message(spell.fail_message or "No valid target!", (255, 255, 0))
            }]
        
        # Load jokes from YAML
        jokes_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "yo_mama_jokes.yaml")
        try:
            with open(jokes_path, 'r') as f:
                jokes_data = yaml.safe_load(f)
                jokes = jokes_data.get('jokes', [])
        except Exception as e:
            jokes = ["Yo mama so ugly, even the game couldn't load her jokes!"]
            print(f"Warning: Could not load yo_mama_jokes.yaml: {e}")
        
        if not jokes:
            jokes = ["Yo mama so forgettable, even the joke list forgot about her!"]
        
        # Select random joke
        joke = random.choice(jokes)
        
        # Target yells the joke
        results.append({
            "message": Message(
                f'{target.name} yells: "{joke}"',
                (200, 150, 255)  # Purple
            )
        })
        
        # Apply taunt effect
        if not target.components.has(ComponentType.STATUS_EFFECTS):
            target.status_effects = StatusEffectManager(target)
            target.components.add(ComponentType.STATUS_EFFECTS, target.status_effects)
        
        taunt_effect = TauntedTargetEffect(duration=spell.duration, owner=target)
        effect_results = target.status_effects.add_effect(taunt_effect)
        results.extend(effect_results)
        
        # Count affected monsters
        affected_count = 0
        for entity in entities:
            if (entity.components.has(ComponentType.AI) and 
                entity.components.has(ComponentType.FIGHTER) and 
                entity != target):
                affected_count += 1
        
        results.append({
            "consumed": True,
            "message": Message(
                spell.success_message or "All hostiles turn their attention!",
                (255, 100, 100)
            )
        })
        
        if affected_count > 0:
            results.append({
                "message": Message(
                    f"{affected_count} creature{'s' if affected_count != 1 else ''} now target {target.name}!",
                    (255, 200, 100)
                )
            })
        
        return results
    
    def _calculate_damage(self, damage_dice: str) -> int:
        """Calculate damage from dice notation.
        
        Args:
            damage_dice: Dice notation string (e.g., "3d6", "2d8+4")
            
        Returns:
            Damage amount
        """
        return roll_dice(damage_dice)
    
    def _bresenham_line(self, x0: int, y0: int, x1: int, y1: int) -> List[tuple]:
        """Calculate a line from (x0, y0) to (x1, y1) using Bresenham's algorithm.
        
        Args:
            x0, y0: Starting coordinates
            x1, y1: Ending coordinates
            
        Returns:
            List of (x, y) tuples forming the line
        """
        path = []
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        x, y = x0, y0
        while True:
            path.append((x, y))
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
        
        return path


# Global spell executor instance
_global_executor: Optional[SpellExecutor] = None


def get_spell_executor() -> SpellExecutor:
    """Get the global spell executor instance.
    
    Returns:
        The singleton SpellExecutor instance
    """
    global _global_executor
    if _global_executor is None:
        _global_executor = SpellExecutor()
    return _global_executor

