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
from message_builder import MessageBuilder as MB
from fov_functions import map_is_in_fov
from dice import roll_dice
from components.component_registry import ComponentType


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
        # Phase 20F: Canonical silence gating at spell execution point
        # This is the single gate for all spells going through SpellExecutor
        from components.status_effects import check_and_gate_silenced_cast
        spell_name = spell.name if hasattr(spell, 'name') else 'cast a spell'
        blocked = check_and_gate_silenced_cast(caster, f"cast {spell_name}")
        if blocked:
            return blocked
        
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
            return [{"consumed": False, "message": MB.warning("Invalid spell range!")}]
        
        # Check for invalid damage (negative only, zero is allowed)
        if damage_override is not None and damage_override < 0:
            return [{"consumed": False, "message": MB.warning("Invalid spell parameters!")}]
        
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
                    "message": MB.failure("Unknown spell category!")
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
            entity_fighter = entity.get_component_optional(ComponentType.FIGHTER)
            if (
                entity_fighter
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
                    "message": MB.spell_fail(
                        spell.fail_message or "No enemy is close enough to strike."
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
        
        # Apply damage using centralized damage service
        from services.damage_service import apply_damage
        
        damage_type_str = spell.damage_type.name.lower() if hasattr(spell, 'damage_type') and spell.damage_type else None
        message_text = spell.success_message or f"The {spell.name} strikes the {target.name} for {damage} damage!"
        results.append(
            {
                "consumed": True,
                "target": target,
                "message": MB.spell_effect(message_text.format(target.name, damage)),
            }
        )
        
        # Get state_manager from kwargs (passed from game_actions)
        state_manager = kwargs.get('state_manager')
        
        # Apply damage with centralized service (handles death automatically)
        damage_results = apply_damage(
            state_manager,
            target,
            damage,
            cause=f"spell:{spell.name}",
            attacker_entity=caster,
            damage_type=damage_type_str
        )
        results.extend(damage_results)
        
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
                    "message": MB.warning(
                        "You cannot target a tile outside your field of view."
                    ),
                }
            ]
        
        # Cast message
        cast_msg = spell.cast_message or f"The {spell.name} explodes!"
        results.append(
            {
                "consumed": True,
                "message": MB.spell_cast(cast_msg),
            }
        )
        
        # Phase 20 Scroll Modernization: Track metrics for AoE spells
        try:
            from services.scenario_metrics import get_active_metrics_collector
            collector = get_active_metrics_collector()
            if collector and spell.spell_id == "fireball":
                collector.increment('fireball_casts')
        except ImportError:
            collector = None
        
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
        # Note: We check "in kwargs" not "is not None" to properly handle damage=0
        if "damage" in kwargs:
            damage = kwargs["damage"]
        else:
            damage = self._calculate_damage(spell.damage) if spell.damage else 0
        
        # Get state_manager from kwargs for damage service
        from services.damage_service import apply_damage
        state_manager = kwargs.get('state_manager')
        damage_type_str = spell.damage_type.name.lower() if hasattr(spell, 'damage_type') and spell.damage_type else None
        
        # Phase 20 Scroll Modernization: Track direct damage for metrics
        total_direct_damage = 0
        
        for entity in entities:
            entity_fighter = entity.get_component_optional(ComponentType.FIGHTER)
            if entity_fighter:
                distance = math.sqrt(
                    (entity.x - target_x) ** 2 + (entity.y - target_y) ** 2
                )
                if distance <= spell.radius:
                    results.append(
                        {
                            "message": MB.spell_effect(
                                f"The {entity.name} gets burned for {damage} hit points."
                            )
                        }
                    )
                    # Apply damage using centralized service (handles death automatically)
                    damage_results = apply_damage(
                        state_manager,
                        entity,
                        damage,
                        cause=f"spell:{spell.name}",
                        attacker_entity=caster,
                        damage_type=damage_type_str
                    )
                    results.extend(damage_results)
                    total_direct_damage += damage
        
        # Phase 20 Scroll Modernization: Track direct damage metric
        if total_direct_damage > 0:
            try:
                from services.scenario_metrics import get_active_metrics_collector
                collector = get_active_metrics_collector()
                if collector and spell.spell_id == "fireball":
                    collector.increment('fireball_direct_damage', total_direct_damage)
            except ImportError:
                pass
        
        # Create ground hazards if defined
        tiles_created = 0
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
                            from components.ground_hazard import GroundHazard
                            hazard = GroundHazard(
                                hazard_type=hazard_type,
                                x=hx,
                                y=hy,
                                base_damage=spell.hazard_damage,
                                remaining_turns=spell.hazard_duration,
                                max_duration=spell.hazard_duration,
                                source_name=spell.name
                            )
                            game_map.hazard_manager.add_hazard(hazard)
                            tiles_created += 1
        
        # Phase 20 Scroll Modernization: Track tiles created metric
        if tiles_created > 0:
            try:
                from services.scenario_metrics import get_active_metrics_collector
                collector = get_active_metrics_collector()
                if collector and spell.spell_id == "fireball":
                    collector.increment('fireball_tiles_created', tiles_created)
            except ImportError:
                pass
        
        return results
    
    def _cast_cone_spell(
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
                    "message": MB.warning(
                        "You cannot target a tile outside your field of view."
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
                "message": MB.spell_cast(cast_msg),
            }
        )
        
        # Phase 20 Scroll Modernization: Track metrics for cone spells
        try:
            from services.scenario_metrics import get_active_metrics_collector
            collector = get_active_metrics_collector()
            if collector and spell.spell_id == "dragon_fart":
                collector.increment('dragon_fart_casts')
        except ImportError:
            collector = None
        
        # Show visual effect
        if spell.visual_effect:
            spell.visual_effect(list(cone_tiles))  # Convert set to list for visual effect
        
        # Phase 20 Scroll Modernization: Check for sleep effect type
        from spells.spell_types import EffectType
        
        if spell.effect_type == EffectType.SLEEP:
            # Apply SleepEffect to entities in cone (replaces old ConfusedMonster AI swap)
            from components.status_effects import SleepEffect, StatusEffectManager
            
            affected_count = 0
            for entity in entities:
                if entity == caster:
                    continue  # Don't affect self
                    
                fighter = entity.get_component_optional(ComponentType.FIGHTER)
                if fighter and (entity.x, entity.y) in cone_tiles:
                    # Ensure entity has status_effects component
                    if not entity.components.has(ComponentType.STATUS_EFFECTS):
                        entity.status_effects = StatusEffectManager(entity)
                        entity.components.add(ComponentType.STATUS_EFFECTS, entity.status_effects)
                    
                    # Apply sleep effect
                    sleep_effect = SleepEffect(duration=spell.duration, owner=entity)
                    effect_results = entity.status_effects.add_effect(sleep_effect)
                    results.extend(effect_results)
                    affected_count += 1
            
            if affected_count == 0:
                results.append({
                    "message": MB.spell_fail("The noxious gas dissipates harmlessly...")
                })
        else:
            # Original damage logic for other cone spells
            from services.damage_service import apply_damage
            
            damage = self._calculate_damage(spell.damage) if spell.damage else 0
            state_manager = kwargs.get('state_manager')
            damage_type_str = spell.damage_type.name.lower() if hasattr(spell, 'damage_type') and spell.damage_type else None
            
            for entity in entities:
                if entity.fighter and (entity.x, entity.y) in cone_tiles:
                    results.append(
                        {
                            "message": MB.spell_effect(
                                f"The {entity.name} is caught in the blast for {damage} hit points!"
                            )
                        }
                    )
                    # Apply damage using centralized service (handles death automatically)
                    damage_results = apply_damage(
                        state_manager,
                        entity,
                        damage,
                        cause=f"spell:{spell.name}",
                        attacker_entity=caster,
                        damage_type=damage_type_str
                    )
                    results.extend(damage_results)
        
        # Create ground hazards if defined
        tiles_created = 0
        if spell.creates_hazard and game_map and hasattr(game_map, 'hazard_manager') and game_map.hazard_manager:
            from components.ground_hazard import HazardType
            
            hazard_type_map = {
                "fire": HazardType.FIRE,
                "poison": HazardType.POISON_GAS,
            }
            
            hazard_type = hazard_type_map.get(spell.hazard_type)
            if hazard_type:
                from components.ground_hazard import GroundHazard
                for hx, hy in cone_tiles:
                    hazard = GroundHazard(
                        hazard_type=hazard_type,
                        x=hx,
                        y=hy,
                        base_damage=spell.hazard_damage,
                        remaining_turns=spell.hazard_duration,
                        max_duration=spell.hazard_duration,
                        source_name=spell.name
                    )
                    game_map.hazard_manager.add_hazard(hazard)
                    tiles_created += 1
        
        # Phase 20 Scroll Modernization: Track tiles created metric
        if tiles_created > 0:
            try:
                from services.scenario_metrics import get_active_metrics_collector
                collector = get_active_metrics_collector()
                if collector and spell.spell_id == "dragon_fart":
                    collector.increment('dragon_fart_tiles_created', tiles_created)
            except ImportError:
                pass
        
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
                    "message": MB.warning("You are already at full health"),
                }
            ]
        
        # Allow amount override from kwargs (for backward compatibility with potions)
        heal_amount = kwargs.get("amount", spell.heal_amount)
        
        caster.fighter.heal(heal_amount)
        results.append(
            {
                "consumed": True,
                "message": MB.healing("Your wounds start to feel better!"),
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
                        "message": MB.warning(
                            "You cannot target a tile outside your field of view."
                        ),
                    }
                ]
        
        # Handle different effect types
        if spell.effect_type == EffectType.CONFUSION:
            return self._cast_confusion_spell(spell, caster, entities, target_x, target_y)
        elif spell.effect_type in [EffectType.SLOW, EffectType.GLUE, EffectType.RAGE]:
            return self._cast_status_effect_spell(spell, caster, entities, fov_map, target_x, target_y)
        elif spell.effect_type == EffectType.FEAR:
            return self._cast_fear_spell(spell, caster, entities, fov_map)
        elif spell.spell_id == "teleport":
            return self._cast_teleport_spell(spell, caster, entities, game_map, target_x, target_y)
        elif spell.spell_id == "blink":
            return self._cast_blink_spell(spell, caster, entities, game_map, fov_map, target_x, target_y)
        elif spell.spell_id == "detect_monster":
            return self._cast_detect_monster_spell(spell, caster)
        elif spell.spell_id == "magic_mapping":
            return self._cast_magic_mapping_spell(spell, caster, game_map)
        elif spell.spell_id == "light":
            return self._cast_light_spell(spell, caster, game_map, fov_map)
        
        return [
            {
                "consumed": False,
                "message": MB.failure("Unknown utility spell effect!")
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
                    "message": MB.warning(
                        spell.no_target_message
                    ),
                }
            ]
        
        # Check boss immunity
        boss = target.get_component_optional(ComponentType.BOSS)
        if boss and boss.is_immune_to("confusion"):
            return [
                {
                    "consumed": True,
                    "message": MB.custom(f"{boss.boss_name} resists the confusion!", MB.GRAY)
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
                "message": MB.spell_effect(
                    message_text.format(target.name)
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
        from components.status_effects import SlowedEffect, ImmobilizedEffect, EnragedEffect, StatusEffectManager
        
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
                    "message": MB.warning(spell.no_target_message)
                }
            ]
        
        # Check boss immunity
        boss = target.get_component_optional(ComponentType.BOSS)
        if boss:
            # Map effect types to immunity names
            effect_name_map = {
                EffectType.SLOW: "slow",
                EffectType.GLUE: "glue",
                EffectType.RAGE: "rage"
            }
            effect_name = effect_name_map.get(spell.effect_type, "")
            if effect_name and boss.is_immune_to(effect_name):
                return [
                    {
                        "consumed": True,
                        "message": MB.custom(f"{boss.boss_name} resists the {effect_name}!", MB.GRAY)
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
            effect = ImmobilizedEffect(duration=spell.duration, owner=target)
        elif spell.effect_type == EffectType.RAGE:
            effect = EnragedEffect(duration=spell.duration, owner=target)
        
        if effect:
            effect_results = target.status_effects.add_effect(effect)
            return [{"consumed": True}] + effect_results
        
        return [
            {
                "consumed": False,
                "message": MB.failure("Failed to apply status effect!")
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
                    "message": MB.warning(
                        "You cannot teleport into a wall!"
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
                            "message": MB.warning(
                                "That location is occupied!"
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
                "message": MB.spell_effect(message_text),
                "fov_recompute": True  # Request FOV recomputation
            }
        ]
    
    def _cast_blink_spell(
        self,
        spell: SpellDefinition,
        caster,
        entities: List,
        game_map,
        fov_map,
        target_x: int,
        target_y: int
    ) -> List[Dict[str, Any]]:
        """Cast blink spell - short-range tactical teleport.
        
        Like teleport but requires line of sight and has shorter range (5 tiles).
        Used for tactical repositioning in combat.
        """
        # Check range
        distance = ((target_x - caster.x) ** 2 + (target_y - caster.y) ** 2) ** 0.5
        if distance > spell.max_range:
            return [
                {
                    "consumed": False,
                    "message": MB.warning(
                        f"That location is too far! (max {spell.max_range} tiles)"
                    ),
                }
            ]
        
        # Check line of sight
        if spell.requires_los and not map_is_in_fov(fov_map, target_x, target_y):
            return [
                {
                    "consumed": False,
                    "message": MB.warning(
                        "You cannot blink to a location you cannot see!"
                    ),
                }
            ]
        
        # Check if target is blocked
        if game_map.is_blocked(target_x, target_y):
            return [
                {
                    "consumed": False,
                    "message": MB.warning(spell.fail_message or "You cannot blink there!"),
                }
            ]
        
        # Check if location is occupied
        for entity in entities:
            if entity.x == target_x and entity.y == target_y and entity != caster:
                if entity.blocks:
                    return [
                        {
                            "consumed": False,
                            "message": MB.warning("That location is occupied!"),
                        }
                    ]
        
        # Blink!
        caster.x = target_x
        caster.y = target_y
        
        return [
            {
                "consumed": True,
                "message": MB.spell_effect(spell.success_message),
                "fov_recompute": True  # Request FOV recomputation
            }
        ]
    
    def _cast_magic_mapping_spell(
        self,
        spell: SpellDefinition,
        caster,
        game_map
    ) -> List[Dict[str, Any]]:
        """Cast magic mapping spell - reveals entire dungeon level.
        
        Sets all tiles on the current level to explored, revealing the full map layout.
        Classic roguelike utility spell.
        """
        # Reveal entire map
        for y in range(game_map.height):
            for x in range(game_map.width):
                game_map.tiles[x][y].explored = True
        
        return [
            {
                "consumed": True,
                "message": MB.spell_effect(spell.success_message),
            }
        ]
    
    def _cast_light_spell(
        self,
        spell: SpellDefinition,
        caster,
        game_map,
        fov_map
    ) -> List[Dict[str, Any]]:
        """Cast light spell - permanently reveals all visible tiles.
        
        Makes all tiles currently in the caster's FOV permanently explored.
        Useful for mapping out the current area.
        """
        # Reveal all tiles in current FOV
        revealed_count = 0
        for y in range(game_map.height):
            for x in range(game_map.width):
                if map_is_in_fov(fov_map, x, y) and not game_map.tiles[x][y].explored:
                    game_map.tiles[x][y].explored = True
                    revealed_count += 1
        
        message = spell.success_message
        if revealed_count > 0:
            message += f" ({revealed_count} tiles revealed)"
        
        return [
            {
                "consumed": True,
                "message": MB.spell_effect(message),
            }
        ]
    
    def _cast_fear_spell(
        self,
        spell: SpellDefinition,
        caster,
        entities: List,
        fov_map
    ) -> List[Dict[str, Any]]:
        """Cast fear spell - makes nearby enemies flee in terror.
        
        Applies fear status effect to all enemies within radius that are in FOV.
        Feared enemies will attempt to run away from the caster.
        """
        from components.status_effects import FearEffect, StatusEffectManager
        
        # Get spell radius (default to spell definition)
        radius = spell.radius if hasattr(spell, 'radius') else 10
        
        # Find all enemies within radius and in FOV
        affected_entities = []
        for entity in entities:
            if entity == caster or not entity.components.has(ComponentType.FIGHTER):
                continue
            
            # Check if in range
            distance = math.sqrt((entity.x - caster.x) ** 2 + (entity.y - caster.y) ** 2)
            if distance > radius:
                continue
            
            # Check if in FOV
            if not map_is_in_fov(fov_map, entity.x, entity.y):
                continue
            
            # Check boss immunity
            boss = entity.get_component_optional(ComponentType.BOSS)
            if boss and boss.is_immune_to("fear"):
                continue
            
            # Ensure entity has status_effects component
            if not entity.components.has(ComponentType.STATUS_EFFECTS):
                entity.status_effects = StatusEffectManager(entity)
                entity.components.add(ComponentType.STATUS_EFFECTS, entity.status_effects)
            
            # Apply fear effect
            effect = FearEffect(duration=spell.duration, owner=entity)
            entity.status_effects.add_effect(effect)
            affected_entities.append(entity)
        
        # Generate messages
        results = [{"consumed": True}]
        
        if affected_entities:
            if spell.cast_message:
                results.append({"message": MB.spell_effect(spell.cast_message)})
            results.append({
                "message": MB.spell_effect(f"{len(affected_entities)} enemies flee in terror!")
            })
        else:
            results.append({"message": MB.info("No enemies are close enough to frighten.")})
        
        return results
    
    def _cast_detect_monster_spell(
        self,
        spell: SpellDefinition,
        caster
    ) -> List[Dict[str, Any]]:
        """Cast detect monster spell - grants ability to sense all monsters.
        
        Applies detect monster status effect which allows seeing all monsters
        on the level regardless of FOV for the duration.
        """
        from components.status_effects import DetectMonsterEffect, StatusEffectManager
        
        # Ensure caster has status_effects component
        if not caster.components.has(ComponentType.STATUS_EFFECTS):
            caster.status_effects = StatusEffectManager(caster)
            caster.components.add(ComponentType.STATUS_EFFECTS, caster.status_effects)
        
        # Apply detect monster effect
        effect = DetectMonsterEffect(duration=spell.duration, owner=caster)
        effect_results = caster.status_effects.add_effect(effect)
        
        return [{"consumed": True}] + effect_results
    
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
        
        Handles shield, invisibility, haste, identify mode, and equipment enhancements.
        """
        # Handle shield spell
        if spell.spell_id == "shield":
            return self._cast_shield_spell(spell, caster)
        
        # Handle invisibility
        elif spell.spell_id == "invisibility":
            return self._cast_invisibility_spell(spell, caster)
        
        # Handle haste
        elif spell.spell_id == "haste":
            return self._cast_haste_spell(spell, caster)
        
        # Handle identify mode
        elif spell.spell_id == "identify":
            return self._cast_identify_spell(spell, caster)
        
        # Handle equipment enhancements
        elif spell.spell_id == "enhance_weapon":
            return self._cast_enhance_weapon_spell(spell, caster, **kwargs)
        elif spell.spell_id == "enhance_armor":
            return self._cast_enhance_armor_spell(spell, caster, **kwargs)
        
        return [
            {
                "consumed": False,
                "message": MB.failure("Unknown buff spell!")
            }
        ]
    
    def _cast_shield_spell(
        self,
        spell: SpellDefinition,
        caster
    ) -> List[Dict[str, Any]]:
        """Cast shield spell for defense boost."""
        from components.status_effects import ShieldEffect, StatusEffectManager
        
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
        
        results = []
        
        # Check if already invisible
        if getattr(caster, 'invisible', False):
            results.append({
                "message": MB.spell_fail(
                    f"{caster.name} is already invisible!"
                )
            })
            results.append({"consumed": False})
            return results
        
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
    
    def _cast_identify_spell(
        self,
        spell: SpellDefinition,
        caster
    ) -> List[Dict[str, Any]]:
        """Cast identify spell - grants temporary identification powers.
        
        Grants the player a 10-turn buff that allows identifying 1 item per turn.
        This is the core mechanic for the Identify scroll.
        """
        from components.status_effects import IdentifyModeEffect, StatusEffectManager
        
        results = []
        
        # Ensure caster has status_effects component
        if not caster.components.has(ComponentType.STATUS_EFFECTS):
            caster.status_effects = StatusEffectManager(caster)
            caster.components.add(ComponentType.STATUS_EFFECTS, caster.status_effects)
        
        # Create identify mode effect
        identify_effect = IdentifyModeEffect(
            duration=spell.duration,  # 10 turns
            owner=caster
        )
        
        effect_results = caster.status_effects.add_effect(identify_effect)
        results.extend(effect_results)
        results.append({"consumed": True})
        
        return results
    
    def _cast_haste_spell(
        self,
        spell: SpellDefinition,
        caster
    ) -> List[Dict[str, Any]]:
        """Cast haste spell - grants increased movement speed.
        
        Uses SpeedEffect to double movement speed for the duration.
        """
        from components.status_effects import SpeedEffect, StatusEffectManager
        
        results = []
        
        # Ensure caster has status_effects component
        if not caster.components.has(ComponentType.STATUS_EFFECTS):
            caster.status_effects = StatusEffectManager(caster)
            caster.components.add(ComponentType.STATUS_EFFECTS, caster.status_effects)
        
        # Create speed effect
        speed_effect = SpeedEffect(
            duration=spell.duration,  # 30 turns
            owner=caster
        )
        
        effect_results = caster.status_effects.add_effect(speed_effect)
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
                weapon.equippable.modify_damage_range(min_bonus, max_bonus)
                
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
    
    def _cast_enhance_armor_spell(
        self,
        spell: SpellDefinition,
        caster,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Enhance equipped armor's AC bonus."""
        import random
        
        bonus = kwargs.get("bonus", 1)
        
        results = []
        
        # Check for equipment
        equipment = caster.get_component_optional(ComponentType.EQUIPMENT)
        if not equipment:
            equipment = getattr(caster, 'equipment', None)
        
        if not equipment:
            return [{
                "consumed": False,
                "message": MB.warning("You have no equipment to enhance!")
            }]
        
        # Find equipped armor pieces
        armor_pieces = []
        for slot_name in ['head', 'chest', 'off_hand']:
            armor = getattr(equipment, slot_name, None)
            if armor and (armor.components.has(ComponentType.EQUIPPABLE) or hasattr(armor, 'equippable')):
                # Check if it's armor (not a weapon)
                equippable = armor.get_component_optional(ComponentType.EQUIPPABLE) if hasattr(armor, 'get_component_optional') else getattr(armor, 'equippable', None)
                if equippable and hasattr(equippable, 'armor_class_bonus'):
                    armor_pieces.append((slot_name, armor))
        
        if not armor_pieces:
            return [{
                "consumed": False,
                "message": MB.warning("You have no armor equipped to enhance!")
            }]
        
        # Randomly select an armor piece
        slot_name, armor = random.choice(armor_pieces)
        old_bonus = armor.equippable.armor_class_bonus

        # Directly modify the armor class bonus
        armor.equippable.armor_class_bonus += bonus
        
        results.append({
            "consumed": True,
            "message": MB.item_effect(
                f"Your {armor.name} glows with magical energy! "
                f"AC bonus increased from +{old_bonus} to +{armor.equippable.armor_class_bonus}."
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
                "message": MB.failure(f"Unsupported summon spell: {spell.spell_id}")
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
        """Cast raise dead spell - resurrect a corpse as a zombie.
        
        Phase 19: Now uses CorpseComponent for safe raise tracking.
        Supports raiser_faction parameter for Necromancer AI.
        """
        import math
        from entity import get_blocking_entities_at_location
        from components.fighter import Fighter
        from components.ai import MindlessZombieAI
        from config.entity_registry import get_entity_registry
        from render_functions import RenderOrder
        from components.faction import Faction
        from components.corpse import CorpseComponent
        
        results = []
        max_range = kwargs.get("range", spell.max_range)
        raiser_faction = kwargs.get("raiser_faction", None)  # Phase 19: Faction override for AI
        
        # Validate target
        if target_x is None or target_y is None:
            return [{
                "consumed": False,
                "message": MB.warning(spell.no_target_message or "You must select a corpse!")
            }]
        
        # Check range
        distance = math.sqrt((target_x - caster.x) ** 2 + (target_y - caster.y) ** 2)
        if distance > max_range:
            return [{
                "consumed": False,
                "message": MB.warning("That corpse is too far away!")
            }]
        
        # Phase 19: Find corpse at location using CorpseComponent (primary)
        # Fallback to name check for backward compatibility with pre-Phase19 saves
        corpse = None
        for ent in entities:
            if ent.x == target_x and ent.y == target_y:
                # Prefer CorpseComponent check
                corpse_comp = ent.get_component_optional(ComponentType.CORPSE)
                if corpse_comp:
                    corpse = ent
                    break
                # Fallback: legacy name-based check
                elif ent.name.startswith("remains of "):
                    corpse = ent
                    break
        
        if not corpse:
            return [{
                "consumed": False,
                "message": MB.warning(spell.fail_message or "No corpse there!")
            }]
        
        # Phase 19: Check corpse eligibility via CorpseComponent
        corpse_comp = corpse.get_component_optional(ComponentType.CORPSE)
        if corpse_comp:
            if not corpse_comp.can_be_raised():
                # Corpse already consumed or at max raises
                if corpse_comp.consumed:
                    return [{
                        "consumed": False,
                        "message": MB.warning("That corpse has already been raised!")
                    }]
                else:
                    return [{
                        "consumed": False,
                        "message": MB.warning("That corpse cannot be raised again!")
                    }]
        
        # Check if location is blocked
        blocking_entity = get_blocking_entities_at_location(entities, corpse.x, corpse.y)
        if blocking_entity and blocking_entity != corpse:
            return [{
                "consumed": False,
                "message": MB.warning(f"{blocking_entity.name} is in the way!")
            }]
        
        # Get original monster stats
        registry = get_entity_registry()
        
        # Phase 19: Use CorpseComponent for accurate monster ID (no name parsing)
        if corpse_comp:
            monster_id = corpse_comp.original_monster_id
        else:
            # Fallback: extract from name for legacy corpses
            original_name = corpse.name.replace("remains of ", "")
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
        
        # Resurrect the corpse!
        original_name = corpse.name.replace("remains of ", "")
        corpse.name = f"Zombified {original_name}"
        corpse.color = (40, 40, 40)  # Dark gray/black
        corpse.blocks = True
        corpse.render_order = RenderOrder.ACTOR
        
        # Create zombie: 2x HP, 0.5x damage
        zombie_hp = base_hp * 2
        zombie_power = max(1, int(base_power * 0.5))
        zombie_damage_min = max(1, int(base_damage_min * 0.5))
        zombie_damage_max = max(1, int(base_damage_max * 0.5))
        zombie_strength = max(6, int(base_strength * 0.75))
        zombie_dexterity = max(6, int(base_dexterity * 0.5))
        zombie_constitution = min(18, int(base_constitution * 1.5))
        
        # Create fighter component
        new_fighter = Fighter(
            hp=zombie_hp,
            defense=base_defense,
            power=zombie_power,
            damage_min=zombie_damage_min,
            damage_max=zombie_damage_max,
            strength=zombie_strength,
            dexterity=zombie_dexterity,
            constitution=zombie_constitution
        )
        new_fighter.owner = corpse
        
        # Set fighter (Entity.__setattr__ auto-registers, so don't call .add())
        corpse.fighter = new_fighter
        
        # Create mindless zombie AI (attacks everything)
        new_ai = MindlessZombieAI()
        new_ai.owner = corpse
        
        # Set AI (Entity.__setattr__ auto-registers, so don't call .add())
        corpse.ai = new_ai
        
        # Phase 19: Set faction based on raiser_faction parameter
        # If raiser_faction provided (Necromancer AI), zombies are friendly to raiser
        # Otherwise, default to NEUTRAL (hostile to all) for player-raised zombies
        if raiser_faction is not None:
            corpse.faction = raiser_faction
        else:
            corpse.faction = Faction.NEUTRAL
        
        # Clear any inventory/equipment from the original monster
        if corpse.components.has(ComponentType.INVENTORY):
            corpse.components.remove(ComponentType.INVENTORY)
        if hasattr(corpse, 'inventory'):
            corpse.inventory = None
        if corpse.components.has(ComponentType.EQUIPMENT):
            corpse.components.remove(ComponentType.EQUIPMENT)
        if hasattr(corpse, 'equipment'):
            corpse.equipment = None
        
        # Phase 19/20: Consume corpse via CorpseComponent
        if corpse_comp:
            raiser_name = getattr(caster, 'name', 'Unknown')
            corpse_comp.consume(raiser_name)
            
            # Phase 20: Track lineage so re-death creates SPENT corpse
            if corpse_comp.corpse_id:
                corpse.raised_from_corpse_id = corpse_comp.corpse_id
            
            # Record metric
            try:
                from services.scenario_metrics import get_active_metrics_collector
                metrics_collector = get_active_metrics_collector()
                if metrics_collector:
                    metrics_collector.increment('raises_completed')
            except Exception:
                pass  # Metrics optional
        
        # Invalidate entity cache since we added AI to an existing entity
        from entity_sorting_cache import invalidate_entity_cache
        invalidate_entity_cache("raise_dead_zombie_created")
        
        results.append({
            "consumed": True,
            "message": MB.spell_effect(spell.success_message or f"{corpse.name} rises!")
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
        
        results = []
        
        # Check if target in FOV
        if not map_is_in_fov(fov_map, target_x, target_y):
            return [{
                "consumed": False,
                "message": MB.warning("You cannot target something you cannot see.")
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
                "message": MB.warning(spell.fail_message or "No valid target!")
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
            "message": MB.custom(
                f'{target.name} yells: "{joke}"',
                MB.PURPLE  # Purple
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
            "message": MB.spell_effect(
                spell.success_message or "All hostiles turn their attention!"
            )
        })
        
        if affected_count > 0:
            results.append({
                "message": MB.spell_effect(
                    f"{affected_count} creature{'s' if affected_count != 1 else ''} now target {target.name}!"
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

