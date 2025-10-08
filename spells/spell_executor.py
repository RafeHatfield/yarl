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
        entities: List,
        fov_map,
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
            **kwargs: Additional parameters
            
        Returns:
            List of result dictionaries with consumption, messages, etc.
        """
        results = []
        
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
            return self._cast_auto_target_spell(spell, caster, entities, fov_map)
        
        elif spell.targeting == TargetingType.AOE:
            # Area of effect (like fireball)
            return self._cast_aoe_spell(
                spell, caster, entities, fov_map, game_map, target_x, target_y
            )
        
        elif spell.targeting == TargetingType.CONE:
            # Cone attack (like dragon fart)
            return self._cast_cone_spell(
                spell, caster, entities, fov_map, game_map, target_x, target_y
            )
        
        return results
    
    def _cast_auto_target_spell(
        self,
        spell: SpellDefinition,
        caster,
        entities: List,
        fov_map
    ) -> List[Dict[str, Any]]:
        """Cast a spell that auto-targets the closest enemy (e.g., lightning).
        
        This is used for spells like Lightning Bolt that automatically find
        and strike the nearest visible enemy within range.
        """
        results = []
        
        # Find closest enemy in range
        target = None
        closest_distance = spell.max_range + 1
        
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
        
        # Calculate damage
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
        target_y: int
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
        
        # Deal damage to entities in radius
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
        
        For now, delegate to old functions. We'll migrate these next.
        """
        # TODO: Implement buff spell execution
        return [
            {
                "consumed": False,
                "message": Message("Buff spells not yet implemented in registry!", (255, 0, 0))
            }
        ]
    
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

