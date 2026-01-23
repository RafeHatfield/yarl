"""Shared factory helpers and utilities.

This module contains common functionality used by all factory types:
- Registry access and lazy loading
- Configuration management
- Item identification logic
- Render order and equipment slot conversions
- Fallback entity creation
"""

import logging
import random
from typing import Optional

from entity import Entity
from components.component_registry import ComponentType
from components.fighter import Fighter, ResistanceType, normalize_resistance_type
from components.ai import BasicMonster
from components.item import Item
from components.equippable import Equippable
from equipment_slots import EquipmentSlots
from render_functions import RenderOrder
from config.entity_registry import get_entity_registry, load_entity_config
from config.game_constants import GameConstants
from config.item_appearances import get_appearance_generator
from utils.resource_paths import get_resource_path

logger = logging.getLogger(__name__)


class FactoryBase:
    """Base class with shared factory utilities.
    
    Handles:
    - Lazy loading of registry and game constants
    - Item identification logic
    - Render order and equipment slot conversions
    - Appearance generation
    """
    
    def __init__(self, entity_registry=None, game_constants=None, difficulty_level="medium"):
        """Initialize factory base.
        
        Args:
            entity_registry: EntityRegistry instance. If None, uses global registry (lazy-loaded).
            game_constants: GameConstants instance. If None, loads from default path (lazy-loaded).
            difficulty_level: Difficulty level for item identification ("easy", "medium", "hard")
        """
        # Store the registry reference but don't load it yet (lazy loading)
        self._registry = entity_registry
        self._registry_loaded = (entity_registry is not None)
        
        # Store the game constants reference but don't load it yet (lazy loading)
        self._game_constants = game_constants
        self._game_constants_loaded = (game_constants is not None)
        
        self.difficulty_level = difficulty_level
        self.appearance_generator = get_appearance_generator()
    
    @property
    def registry(self):
        """Lazily load and return the entity registry.
        
        The registry is loaded on first access, allowing lightweight scripts
        to avoid loading large YAML files if they don't need the registry.
        
        Returns:
            EntityRegistry: The entity registry instance
        """
        if not self._registry_loaded:
            self._registry = get_entity_registry()
            self._registry_loaded = True

        if self._registry and hasattr(self._registry, "is_loaded") and not self._registry.is_loaded():
            load_entity_config()
        return self._registry
    
    @property
    def game_constants(self):
        """Lazily load and return game constants.
        
        Constants are loaded on first access to avoid expensive file I/O
        for lightweight scripts.
        
        Returns:
            GameConstants: The game constants instance
        """
        if not self._game_constants_loaded:
            self._game_constants = GameConstants.load_from_file(get_resource_path("config/game_constants.yaml"))
            self._game_constants_loaded = True
        return self._game_constants

    def _apply_identification_logic(self, item: Item, item_type: str, item_category: str) -> None:
        """Apply identification logic to an item based on game settings.
        
        This method determines if an item should start identified or unidentified
        based on:
        1. Master toggle (identification_system.enabled)
        2. Global identification state (has this TYPE been identified before?)
        3. Difficulty settings (percentage of items pre-identified)
        4. Item category (scroll, potion, ring, wand)
        
        Args:
            item: The Item component to configure
            item_type: Internal item type name (e.g., "healing_potion")
            item_category: Category for identification ("scroll", "potion", "ring", "wand", "other")
        """
        # Set item category for future identification checks
        item.item_category = item_category
        
        # Check master toggle - if disabled, all items are identified
        if not self.game_constants.identification_system.enabled:
            item.identified = True
            item.appearance = None
            return
        
        # CRITICAL: Check if this item TYPE has had a decision made
        # All items of the same type must have the same identification state
        from config.identification_manager import get_identification_manager
        id_manager = get_identification_manager()
        
        # If this type is already identified, make this item identified
        if id_manager.is_identified(item_type):
            item.identified = True
            item.appearance = None
            return
        
        # If this type is already decided to be unidentified, make this item unidentified
        if id_manager.is_unidentified(item_type):
            item.identified = False
            appearance = self.appearance_generator.get_appearance(item_type, item_category)
            if appearance:
                item.appearance = appearance
            else:
                # Fallback if appearance not found
                logger.warning(f"No appearance found for {item_type} ({item_category}), defaulting to identified")
                item.identified = True
                item.appearance = None
                id_manager.identify_type(item_type)  # Register as identified
            return
        
        # Get difficulty settings
        try:
            difficulty_settings = self.game_constants.difficulty.get_difficulty(self.difficulty_level)
        except ValueError:
            logger.warning(f"Unknown difficulty level: {self.difficulty_level}, using medium")
            difficulty_settings = self.game_constants.difficulty.medium
        
        # Determine pre-identification percentage based on category
        pre_id_percent = 0
        if item_category == "scroll":
            pre_id_percent = difficulty_settings.scrolls_pre_identified_percent
        elif item_category == "potion":
            pre_id_percent = difficulty_settings.potions_pre_identified_percent
        elif item_category == "ring":
            pre_id_percent = difficulty_settings.rings_pre_identified_percent
        elif item_category == "wand":
            pre_id_percent = difficulty_settings.wands_pre_identified_percent
        else:
            # "other" items are always identified
            item.identified = True
            item.appearance = None
            return
        
        # Roll for pre-identification (FIRST TIME for this type)
        # This decision will apply to ALL future items of this type
        roll = random.random() * 100
        if roll < pre_id_percent:
            # Item starts identified - register type globally
            item.identified = True
            item.appearance = None
            id_manager.identify_type(item_type)  # Register as identified
            logger.debug(f"Pre-identified {item_type} (rolled {roll:.1f} < {pre_id_percent})")
        else:
            # Item starts unidentified - get appearance and register decision
            item.identified = False
            appearance = self.appearance_generator.get_appearance(item_type, item_category)
            if appearance:
                item.appearance = appearance
                id_manager.mark_unidentified(item_type)  # Register as unidentified
                logger.debug(f"Unidentified {item_type} (rolled {roll:.1f} >= {pre_id_percent})")
            else:
                # Fallback if appearance not found
                logger.warning(f"No appearance found for {item_type} ({item_category}), defaulting to identified")
                item.identified = True
                item.appearance = None
                id_manager.identify_type(item_type)  # Register as identified

    def _get_render_order(self, render_order_str: str):
        """Convert render order string to RenderOrder enum.
        
        Args:
            render_order_str: String representation of render order
            
        Returns:
            RenderOrder enum value
        """
        try:
            return getattr(RenderOrder, render_order_str.upper())
        except AttributeError:
            logger.warning(f"Unknown render order: {render_order_str}, using ACTOR")
            return RenderOrder.ACTOR

    def _get_equipment_slot(self, slot_str: str):
        """Convert equipment slot string to EquipmentSlots enum.
        
        Args:
            slot_str: String representation of equipment slot
            
        Returns:
            EquipmentSlots enum value
        """
        slot_map = {
            "main_hand": EquipmentSlots.MAIN_HAND,
            "off_hand": EquipmentSlots.OFF_HAND,
            "head": EquipmentSlots.HEAD,
            "chest": EquipmentSlots.CHEST,
            "feet": EquipmentSlots.FEET,
            "quiver": EquipmentSlots.QUIVER  # Phase 22.2.2
        }
        
        slot = slot_map.get(slot_str)
        if slot:
            return slot
        else:
            logger.warning(f"Unknown equipment slot: {slot_str}, using MAIN_HAND")
            return EquipmentSlots.MAIN_HAND

    def _create_fallback_monster(self, monster_type: str, x: int, y: int) -> Entity:
        """Create a fallback monster when definition is missing.
        
        Args:
            monster_type: The requested monster type
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Basic monster entity with default stats
        """
        fighter_component = Fighter(hp=10, defense=0, power=2, xp=10)
        ai_component = BasicMonster()
        
        return Entity(
            x=x, y=y, char='?', color=(255, 0, 255), name=f"Unknown {monster_type}",
            blocks=True, render_order=RenderOrder.ACTOR,
            fighter=fighter_component, ai=ai_component
        )

    def _create_fallback_weapon(self, weapon_type: str, x: int, y: int) -> Entity:
        """Create a fallback weapon when definition is missing.
        
        Args:
            weapon_type: The requested weapon type
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Basic weapon entity with default stats
        """
        equippable_component = Equippable(
            slot=EquipmentSlots.MAIN_HAND,
            power_bonus=1
        )
        
        return Entity(
            x=x, y=y, char='?', color=(255, 0, 255), name=f"Unknown {weapon_type}",
            equippable=equippable_component
        )

    def _create_fallback_armor(self, armor_type: str, x: int, y: int) -> Entity:
        """Create a fallback armor when definition is missing.
        
        Args:
            armor_type: The requested armor type
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Basic armor entity with default stats
        """
        equippable_component = Equippable(
            slot=EquipmentSlots.OFF_HAND,
            defense_bonus=1
        )
        
        return Entity(
            x=x, y=y, char='?', color=(255, 0, 255), name=f"Unknown {armor_type}",
            equippable=equippable_component
        )

    def _create_fallback_spell(self, spell_type: str, x: int, y: int) -> Entity:
        """Create a fallback spell when definition is missing.
        
        Args:
            spell_type: The requested spell type
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Basic spell entity
        """
        item_component = Item()
        
        return Entity(
            x=x, y=y, char='?', color=(255, 0, 255), name=f"Unknown {spell_type}",
            item=item_component
        )

