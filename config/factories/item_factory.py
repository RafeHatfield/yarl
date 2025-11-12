"""Item creation factory.

Handles creation of consumable items:
- Spells/scrolls/potions
- Wands (multi-charge items)
"""

import logging
from typing import Optional

from entity import Entity
from components.component_registry import ComponentType
from components.item import Item
from components.wand import Wand
from render_functions import RenderOrder
from config.factories._factory_base import FactoryBase

logger = logging.getLogger(__name__)


class ItemFactory(FactoryBase):
    """Factory for creating consumable and spell items."""
    
    def create_spell_item(self, spell_type: str, x: int, y: int) -> Optional[Entity]:
        """Create a spell/consumable item entity from configuration.
        
        Args:
            spell_type: The type of spell to create (e.g., "healing_potion")
            x: X coordinate for the spell item
            y: Y coordinate for the spell item
            
        Returns:
            Entity instance if spell type exists, None otherwise
        """
        spell_def = self.registry.get_spell(spell_type)
        if not spell_def:
            # Don't log - this is called as part of smart fallback chain
            return None  # Return None so caller can try other methods

        try:
            # Create item component with appropriate function
            item_component = self._create_item_component(spell_def)
            
            # Determine item category for identification
            item_category = "other"  # default
            if "scroll" in spell_type.lower():
                item_category = "scroll"
            elif "potion" in spell_type.lower():
                item_category = "potion"
            
            # Apply identification logic
            self._apply_identification_logic(item_component, spell_type, item_category)

            # Create entity
            spell_item = Entity(
                x=x,
                y=y,
                char=spell_def.char,
                color=spell_def.color,
                name=spell_def.name,
                item=item_component
            )

            logger.debug(f"Created spell item: {spell_def.name} at ({x}, {y}) [identified: {item_component.identified}]")
            return spell_item

        except Exception as e:
            logger.error(f"Error creating spell {spell_type}: {e}")
            return self._create_fallback_spell(spell_type, x, y)

    def create_wand(self, wand_type: str, x: int, y: int, dungeon_level: int = 1) -> Optional[Entity]:
        """Create a wand item entity with random charges.
        
        Wands are multi-charge spell casters that can be recharged by picking up
        matching scrolls. They spawn with random charges based on dungeon level:
        - Base charges: 2-4 (random)
        - Additional charges: +(dungeon_level - 1)
        - Max starting charges: 10
        
        Args:
            wand_type: The type of wand to create (e.g., "wand_of_fireball")
            x: X coordinate for the wand
            y: Y coordinate for the wand
            dungeon_level: Current dungeon level (affects starting charges)
            
        Returns:
            Entity instance if wand type exists, None otherwise
        """
        wand_def = self.registry.get_wand(wand_type)
        if not wand_def:
            logger.warning(f"Unknown wand type: {wand_type}")
            return None

        try:
            import random
            
            # Calculate random starting charges
            # Base: 2-4, + (level-1), max 10
            base_charges = random.randint(2, 4)
            level_bonus = dungeon_level - 1
            starting_charges = min(base_charges + level_bonus, 10)
            
            # Create wand component
            wand_component = Wand(
                spell_type=wand_def.spell_name,
                charges=starting_charges
            )
            
            # Create item component (same as the spell it casts)
            item_component = self._create_item_component_from_wand(wand_def)
            
            # Create entity
            wand_entity = Entity(
                x=x,
                y=y,
                char=wand_def.char,
                color=wand_def.color,
                name=wand_def.name,
                item=item_component
            )
            
            # Attach wand component
            wand_entity.wand = wand_component
            wand_component.owner = wand_entity
            
            logger.debug(f"Created wand: {wand_def.name} ({starting_charges} charges) at ({x}, {y})")
            return wand_entity

        except Exception as e:
            logger.error(f"Error creating wand {wand_type}: {e}")
            return None

    def _create_item_component(self, spell_def):
        """Create an item component with appropriate use function.
        
        Args:
            spell_def: Spell definition
            
        Returns:
            Item component with appropriate use function
        """
        # Import item functions dynamically to avoid circular imports
        from item_functions import (
            heal, cast_lightning, cast_fireball, cast_confuse,
            enhance_weapon, enhance_armor
        )

        # NEW: If effect_function is specified, dynamically import and use it
        if hasattr(spell_def, 'effect_function') and spell_def.effect_function:
            try:
                import item_functions
                use_function = getattr(item_functions, spell_def.effect_function)
                logger.debug(f"Using effect_function: {spell_def.effect_function} for {spell_def.name}")
                return Item(use_function=use_function)
            except AttributeError:
                logger.error(f"Effect function '{spell_def.effect_function}' not found in item_functions")
                # Fall through to legacy mapping below
        
        # Handle keys (they're items without use functions)
        if hasattr(spell_def, 'spell_type') and spell_def.spell_type == 'key':
            logger.debug(f"Creating key item: {spell_def.name}")
            return Item()  # Keys are just inventory items, no use function

        # Map spell types to functions and parameters
        if spell_def.name.lower().replace(' ', '_') == "healing_potion":
            return Item(use_function=heal, amount=spell_def.heal_amount)
        elif spell_def.name.lower().replace(' ', '_') == "lightning_scroll":
            return Item(
                use_function=cast_lightning,
                damage=spell_def.damage,
                maximum_range=spell_def.maximum_range
            )
        elif spell_def.name.lower().replace(' ', '_') == "fireball_scroll":
            return Item(
                use_function=cast_fireball,
                targeting=True,
                damage=spell_def.damage,
                radius=spell_def.radius
            )
        elif spell_def.name.lower().replace(' ', '_') == "confusion_scroll":
            return Item(use_function=cast_confuse, targeting=True)
        elif spell_def.name.lower().replace(' ', '_') == "enhance_weapon_scroll":
            return Item(use_function=enhance_weapon)
        elif spell_def.name.lower().replace(' ', '_') == "enhance_armor_scroll":
            return Item(use_function=enhance_armor)
        elif spell_def.name.lower().replace(' ', '_') == "invisibility_scroll":
            from item_functions import cast_invisibility
            duration = getattr(spell_def, 'duration', 10)  # Default 10 turns
            return Item(use_function=cast_invisibility, duration=duration)
        elif spell_def.name.lower().replace(' ', '_') == "teleport_scroll":
            from item_functions import cast_teleport
            return Item(use_function=cast_teleport, targeting=True)
        elif spell_def.name.lower().replace(' ', '_') == "shield_scroll":
            from item_functions import cast_shield
            duration = getattr(spell_def, 'duration', 10)
            defense_bonus = getattr(spell_def, 'defense_bonus', 4)
            return Item(use_function=cast_shield, duration=duration, defense_bonus=defense_bonus)
        elif spell_def.name.lower().replace(' ', '_') == "dragon_fart_scroll":
            from item_functions import cast_dragon_fart
            duration = getattr(spell_def, 'duration', 20)
            spell_range = getattr(spell_def, 'range', 8)
            cone_width = getattr(spell_def, 'cone_width', 45)
            return Item(
                use_function=cast_dragon_fart,
                targeting=True,
                duration=duration,
                range=spell_range,
                cone_width=cone_width
            )
        elif spell_def.name.lower().replace(' ', '_') == "raise_dead_scroll":
            from item_functions import cast_raise_dead
            spell_range = getattr(spell_def, 'range', 5)
            return Item(
                use_function=cast_raise_dead,
                targeting=True,
                range=spell_range
            )
        elif spell_def.name.lower().replace(' ', '_') == "yo_mama_scroll":
            from item_functions import cast_yo_mama
            spell_range = getattr(spell_def, 'range', 10)
            return Item(
                use_function=cast_yo_mama,
                targeting=True,
                range=spell_range
            )
        elif spell_def.name.lower().replace(' ', '_') == "slow_scroll":
            from item_functions import cast_slow
            duration = getattr(spell_def, 'duration', 10)
            spell_range = getattr(spell_def, 'range', 8)
            return Item(
                use_function=cast_slow,
                targeting=True,
                duration=duration,
                range=spell_range
            )
        elif spell_def.name.lower().replace(' ', '_') == "glue_scroll":
            from item_functions import cast_glue
            duration = getattr(spell_def, 'duration', 5)
            spell_range = getattr(spell_def, 'range', 8)
            return Item(
                use_function=cast_glue,
                targeting=True,
                duration=duration,
                range=spell_range
            )
        elif spell_def.name.lower().replace(' ', '_') == "rage_scroll":
            from item_functions import cast_rage
            duration = getattr(spell_def, 'duration', 8)
            spell_range = getattr(spell_def, 'range', 8)
            return Item(
                use_function=cast_rage,
                targeting=True,
                duration=duration,
                range=spell_range
            )
        elif spell_def.name.lower().replace(' ', '_') == "identify_scroll":
            from item_functions import cast_identify
            duration = getattr(spell_def, 'duration', 5)  # Default 5 turns of identify mode
            return Item(
                use_function=cast_identify,
                duration=duration
            )
        else:
            # Smart fallback: Check if spell exists in spell registry
            # If yes, create a delegate function using cast_spell_by_id
            from spells.spell_registry import get_spell_registry
            spell_registry = get_spell_registry()
            
            # Try to find the spell in the registry by spell_id (which matches the item name)
            spell_id = spell_def.name.lower().replace(' ', '_').replace('_scroll', '').replace('_potion', '')
            spell_in_registry = spell_registry.get(spell_id)
            
            if spell_in_registry:
                # Create a delegate function that calls cast_spell_by_id
                from item_functions import cast_spell_by_id
                
                def delegate_function(*args, **kwargs):
                    """Delegate to spell registry."""
                    caster = args[0] if args else None
                    return cast_spell_by_id(spell_id, caster, **kwargs)
                
                # Determine if targeting is needed
                targeting = spell_in_registry.requires_target
                
                logger.debug(f"Created delegate for {spell_def.name} → spell_id '{spell_id}'")
                return Item(
                    use_function=delegate_function,
                    targeting=targeting
                )
            else:
                # Truly unknown spell
                logger.warning(f"Unknown spell function for {spell_def.name} (tried spell_id '{spell_id}'), creating basic item")
                return Item()

    def _create_item_component_from_wand(self, wand_def):
        """Create an item component from a wand definition.
        
        This creates an Item component that matches the spell the wand casts.
        The wand's spell_name field determines which spell function to use.
        
        Args:
            wand_def: WandDefinition
            
        Returns:
            Item component with appropriate use function
        """
        # Import item functions dynamically to avoid circular imports
        from item_functions import (
            cast_lightning, cast_fireball, cast_confuse, cast_teleport,
            cast_dragon_fart
        )
        
        # Map spell names to functions and parameters
        spell_name = wand_def.spell_name.lower()
        
        if spell_name == "fireball_scroll":
            return Item(
                use_function=cast_fireball,
                targeting=True,
                damage=wand_def.damage,
                radius=wand_def.radius
            )
        elif spell_name == "lightning_scroll":
            return Item(
                use_function=cast_lightning,
                damage=wand_def.damage,
                maximum_range=wand_def.maximum_range
            )
        elif spell_name == "confusion_scroll":
            return Item(use_function=cast_confuse, targeting=True)
        elif spell_name == "teleport_scroll":
            return Item(use_function=cast_teleport, targeting=True)
        elif spell_name == "dragon_fart_scroll":
            return Item(
                use_function=cast_dragon_fart,
                targeting=True,
                duration=wand_def.duration,
                range=wand_def.range,
                cone_width=wand_def.cone_width
            )
        elif spell_name == "yo_mama_scroll":
            from item_functions import cast_yo_mama
            return Item(
                use_function=cast_yo_mama,
                targeting=True,
                range=wand_def.range
            )
        elif spell_name == "slow_scroll":
            from item_functions import cast_slow
            return Item(
                use_function=cast_slow,
                targeting=True,
                duration=wand_def.duration,
                range=wand_def.range
            )
        elif spell_name == "glue_scroll":
            from item_functions import cast_glue
            return Item(
                use_function=cast_glue,
                targeting=True,
                duration=wand_def.duration,
                range=wand_def.range
            )
        elif spell_name == "rage_scroll":
            from item_functions import cast_rage
            return Item(
                use_function=cast_rage,
                targeting=True,
                duration=wand_def.duration,
                range=wand_def.range
            )
        else:
            logger.warning(f"Unknown wand spell '{spell_name}', creating basic item")
            return Item()

