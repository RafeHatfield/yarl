"""Entity factory for creating game entities from configuration.

This module provides factory methods for creating entities based on
definitions loaded from the EntityRegistry. It bridges the gap between
configuration data and actual game entities.
"""

import logging
import random
from typing import Optional

from entity import Entity
from components.component_registry import ComponentType
from components.fighter import Fighter
from components.ai import BasicMonster, SlimeAI, BossAI
from components.item import Item
from components.equippable import Equippable
from components.faction import Faction, get_faction_from_string
from equipment_slots import EquipmentSlots
from render_functions import RenderOrder
from config.entity_registry import (
    get_entity_registry,
    MonsterDefinition,
    WeaponDefinition,
    ArmorDefinition,
    SpellDefinition,
    EntityStats
)
from config.game_constants import GameConstants
from config.item_appearances import get_appearance_generator

logger = logging.getLogger(__name__)


class EntityFactory:
    """Factory for creating entities from configuration definitions.
    
    This factory provides clean methods for creating all types of entities
    based on their configuration definitions. It handles the conversion
    from configuration data to actual game entity instances.
    
    The factory supports:
    - Monster creation with AI and fighter components
    - Weapon creation with equippable components
    - Armor creation with equippable components
    - Spell/item creation with appropriate functions
    - Player stat retrieval for character creation
    - Fallback behavior for missing definitions
    - Item identification system integration
    """

    def __init__(self, entity_registry=None, game_constants=None, difficulty_level="medium"):
        """Initialize the entity factory.
        
        Args:
            entity_registry: EntityRegistry instance. If None, uses global registry.
            game_constants: GameConstants instance. If None, loads from default path.
            difficulty_level: Difficulty level for item identification ("easy", "medium", "hard")
        """
        self.registry = entity_registry or get_entity_registry()
        self.game_constants = game_constants or GameConstants.load_from_file("config/game_constants.yaml")
        self.difficulty_level = difficulty_level
        self.appearance_generator = get_appearance_generator()
    
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

    def create_monster(self, monster_type: str, x: int, y: int) -> Optional[Entity]:
        """Create a monster entity from configuration.
        
        Args:
            monster_type: The type of monster to create (e.g., "orc", "troll")
            x: X coordinate for the monster
            y: Y coordinate for the monster
            
        Returns:
            Entity instance if monster type exists, None otherwise
        """
        monster_def = self.registry.get_monster(monster_type)
        if not monster_def:
            logger.warning(f"Unknown monster type: {monster_type}")
            return self._create_fallback_monster(monster_type, x, y)

        try:
            # Create fighter component from stats
            fighter_component = Fighter(
                hp=monster_def.stats.hp,
                defense=monster_def.stats.defense,
                power=monster_def.stats.power,
                xp=monster_def.stats.xp,
                damage_min=monster_def.stats.damage_min or 0,
                damage_max=monster_def.stats.damage_max or 0,
                strength=getattr(monster_def.stats, 'strength', 10),
                dexterity=getattr(monster_def.stats, 'dexterity', 10),
                constitution=getattr(monster_def.stats, 'constitution', 10),
                resistances=getattr(monster_def.stats, 'resistances', None)
            )

            # Create AI component based on ai_type
            ai_component = self._create_ai_component(monster_def.ai_type)
            
            # Create equipment component for monsters (needed for equipment system)
            from components.equipment import Equipment
            equipment_component = Equipment()
            
            # Create inventory component for monsters that can seek items OR have equipment
            inventory_component = None
            has_equipment_config = hasattr(monster_def, 'equipment') and monster_def.equipment
            if (monster_def.can_seek_items and monster_def.inventory_size > 0) or has_equipment_config:
                from components.inventory import Inventory
                # Use configured inventory size, or default to 5 for monsters with equipment
                inventory_size = monster_def.inventory_size if monster_def.inventory_size > 0 else 5
                inventory_component = Inventory(capacity=inventory_size)
                logger.debug(f"Created inventory for {monster_def.name} with {inventory_size} slots")

            # Get faction from monster definition
            faction = get_faction_from_string(getattr(monster_def, 'faction', 'neutral'))
            
            # Create entity
            monster = Entity(
                x=x,
                y=y,
                char=monster_def.char,
                color=monster_def.color,
                name=monster_def.name,
                blocks=monster_def.blocks,
                render_order=self._get_render_order(monster_def.render_order),
                faction=faction,
                fighter=fighter_component,
                ai=ai_component,
                equipment=equipment_component,
                inventory=inventory_component
            )
            
            # Set special abilities if defined
            if hasattr(monster_def, 'special_abilities') and monster_def.special_abilities:
                monster.special_abilities = monster_def.special_abilities
            
            # Create item-seeking AI if monster can seek items
            if monster_def.can_seek_items:
                from components.item_seeking_ai import create_item_seeking_ai
                from components.component_registry import ComponentType
                item_seeking_ai = create_item_seeking_ai(monster, monster_def)
                if item_seeking_ai:
                    monster.item_seeking_ai = item_seeking_ai  # Legacy attribute for backward compatibility
                    monster.components.add(ComponentType.ITEM_SEEKING_AI, item_seeking_ai)  # Register with ComponentRegistry
                    logger.debug(f"Added item-seeking AI to {monster_def.name}")
                else:
                    logger.warning(f"Failed to create item-seeking AI for {monster_def.name}")
            
            # Create item usage component if monster has inventory
            if inventory_component:
                from components.monster_item_usage import create_monster_item_usage
                item_usage = create_monster_item_usage(monster)
                if item_usage:
                    monster.item_usage = item_usage  # Legacy attribute for backward compatibility
                    monster.components.add(ComponentType.ITEM_USAGE, item_usage)  # Register with ComponentRegistry
                    logger.debug(f"Added item usage capability to {monster_def.name}")
                else:
                    logger.warning(f"Failed to create item usage for {monster_def.name}")

            # Spawn equipment on monster if configured
            if hasattr(monster_def, 'equipment') and monster_def.equipment:
                self._spawn_monster_equipment(monster, monster_def.equipment)
                logger.debug(f"Spawned equipment on {monster_def.name}")
            
            # Create boss component if this is a boss
            if hasattr(monster_def, 'is_boss') and monster_def.is_boss:
                boss_component = self._create_boss_component(monster_type, monster_def.boss_name)
                if boss_component:
                    monster.boss = boss_component
                    monster.components.add(ComponentType.BOSS, boss_component)
                    logger.info(f"Created BOSS: {boss_component.boss_name}")

            logger.debug(f"Created monster: {monster_def.name} at ({x}, {y})")
            return monster

        except Exception as e:
            logger.error(f"Error creating monster {monster_type}: {e}")
            return self._create_fallback_monster(monster_type, x, y)

    def create_weapon(self, weapon_type: str, x: int, y: int) -> Optional[Entity]:
        """Create a weapon entity from configuration.
        
        Args:
            weapon_type: The type of weapon to create (e.g., "sword", "dagger")
            x: X coordinate for the weapon
            y: Y coordinate for the weapon
            
        Returns:
            Entity instance if weapon type exists, None otherwise
        """
        weapon_def = self.registry.get_weapon(weapon_type)
        if not weapon_def:
            # Don't log - this is called as part of smart fallback chain
            return None  # Return None so caller can try armor

        try:
            # Convert string resistance types to ResistanceType enums if resistances are defined
            resistances_dict = None
            if weapon_def.resistances:
                from components.fighter import ResistanceType, normalize_resistance_type
                resistances_dict = {}
                for resist_type_str, value in weapon_def.resistances.items():
                    resist_enum = normalize_resistance_type(resist_type_str)
                    if resist_enum:
                        resistances_dict[resist_enum] = value
            
            # Create equippable component
            equippable_component = Equippable(
                slot=self._get_equipment_slot(weapon_def.slot),
                power_bonus=weapon_def.power_bonus,
                damage_min=weapon_def.damage_min,
                damage_max=weapon_def.damage_max,
                damage_dice=weapon_def.damage_dice,
                to_hit_bonus=weapon_def.to_hit_bonus,
                two_handed=weapon_def.two_handed,
                reach=weapon_def.reach,
                resistances=resistances_dict
            )

            # Create entity
            weapon = Entity(
                x=x,
                y=y,
                char=weapon_def.char,
                color=weapon_def.color,
                name=weapon_def.name,
                equippable=equippable_component
            )

            logger.debug(f"Created weapon: {weapon_def.name} at ({x}, {y})")
            return weapon

        except Exception as e:
            logger.error(f"Error creating weapon {weapon_type}: {e}", exc_info=True)
            logger.error(f"Weapon definition: {weapon_def}")
            return self._create_fallback_weapon(weapon_type, x, y)

    def create_armor(self, armor_type: str, x: int, y: int) -> Optional[Entity]:
        """Create an armor entity from configuration.
        
        Args:
            armor_type: The type of armor to create (e.g., "shield")
            x: X coordinate for the armor
            y: Y coordinate for the armor
            
        Returns:
            Entity instance if armor type exists, None otherwise
        """
        armor_def = self.registry.get_armor(armor_type)
        if not armor_def:
            # Don't log - this is called as part of smart fallback chain
            return None  # Return None so caller can try weapon

        try:
            # Convert string resistance types to ResistanceType enums if resistances are defined
            resistances_dict = None
            if armor_def.resistances:
                from components.fighter import ResistanceType, normalize_resistance_type
                resistances_dict = {}
                for resist_type_str, value in armor_def.resistances.items():
                    resist_enum = normalize_resistance_type(resist_type_str)
                    if resist_enum:
                        resistances_dict[resist_enum] = value
            
            # Create equippable component
            equippable_component = Equippable(
                slot=self._get_equipment_slot(armor_def.slot),
                defense_bonus=armor_def.defense_bonus,
                defense_min=armor_def.defense_min,
                defense_max=armor_def.defense_max,
                armor_class_bonus=armor_def.armor_class_bonus,
                armor_type=armor_def.armor_type,
                dex_cap=armor_def.dex_cap,
                resistances=resistances_dict
            )

            # Create entity
            armor = Entity(
                x=x,
                y=y,
                char=armor_def.char,
                color=armor_def.color,
                name=armor_def.name,
                equippable=equippable_component
            )

            logger.debug(f"Created armor: {armor_def.name} at ({x}, {y})")
            return armor

        except Exception as e:
            logger.error(f"Error creating armor {armor_type}: {e}")
            return self._create_fallback_armor(armor_type, x, y)

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
            from components.wand import Wand
            
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

    def create_ring(self, ring_type: str, x: int, y: int) -> Optional[Entity]:
        """Create a ring item entity from configuration.
        
        Rings provide passive effects when equipped in left or right ring slots.
        All rings start unidentified and must be identified to reveal their effects.
        
        Args:
            ring_type: The type of ring to create (e.g., "ring_of_protection")
            x: X coordinate for the ring
            y: Y coordinate for the ring
            
        Returns:
            Entity instance if ring type exists, None otherwise
        """
        ring_def = self.registry.get_ring(ring_type)
        if not ring_def:
            # Don't log - this is called as part of smart fallback chain
            return None

        try:
            from components.ring import Ring, RingEffect
            from components.item import Item
            
            # Convert ring_effect string to RingEffect enum
            ring_effect_map = {
                "protection": RingEffect.PROTECTION,
                "regeneration": RingEffect.REGENERATION,
                "resistance": RingEffect.RESISTANCE,
                "strength": RingEffect.STRENGTH,
                "dexterity": RingEffect.DEXTERITY,
                "might": RingEffect.MIGHT,
                "teleportation": RingEffect.TELEPORTATION,
                "invisibility": RingEffect.INVISIBILITY,
                "searching": RingEffect.SEARCHING,
                "free_action": RingEffect.FREE_ACTION,
                "wizardry": RingEffect.WIZARDRY,
                "clarity": RingEffect.CLARITY,
                "speed": RingEffect.SPEED,
                "constitution": RingEffect.CONSTITUTION,
                "luck": RingEffect.LUCK,
            }
            
            ring_effect_enum = ring_effect_map.get(ring_def.ring_effect.lower())
            if not ring_effect_enum:
                logger.error(f"Unknown ring effect: {ring_def.ring_effect}")
                return None
            
            # Create ring component with its passive effect
            ring_component = Ring(
                ring_effect=ring_effect_enum,
                effect_strength=ring_def.effect_strength
            )
            
            # Convert string resistance types to ResistanceType enums if resistances are defined
            resistances_dict = None
            if hasattr(ring_def, 'resistances') and ring_def.resistances:
                from components.fighter import ResistanceType, normalize_resistance_type
                resistances_dict = {}
                for resist_type_str, value in ring_def.resistances.items():
                    resist_enum = normalize_resistance_type(resist_type_str)
                    if resist_enum:
                        resistances_dict[resist_enum] = value
            
            # Create equippable component for ring slot
            from components.equippable import Equippable
            equippable_component = Equippable(
                slot=EquipmentSlots.RING,  # Uses generic RING slot, will be assigned to left or right
                resistances=resistances_dict
            )
            
            # Create item component
            item_component = Item()
            
            # Apply identification logic for rings
            self._apply_identification_logic(item_component, ring_type, "ring")
            
            # Create entity
            ring_entity = Entity(
                x=x,
                y=y,
                char=ring_def.char,
                color=ring_def.color,
                name=ring_def.name,
                item=item_component,
                equippable=equippable_component
            )
            
            # Attach ring component
            ring_entity.ring = ring_component
            ring_component.owner = ring_entity
            ring_entity.components.add(ComponentType.RING, ring_component)
            
            logger.debug(f"Created ring: {ring_def.name} at ({x}, {y}) [identified: {item_component.identified}]")
            return ring_entity

        except Exception as e:
            logger.error(f"Error creating ring {ring_type}: {e}")
            return None
    
    def create_chest(self, chest_type: str, x: int, y: int, loot_quality: Optional[str] = None) -> Optional[Entity]:
        """Create a chest map feature entity from configuration.
        
        Chests are interactive loot containers that can be closed, trapped, locked, or mimics.
        
        Args:
            chest_type: The type of chest to create (e.g., "chest", "trapped_chest", "locked_chest")
            x: X coordinate for the chest
            y: Y coordinate for the chest
            loot_quality: Override loot quality ("common", "uncommon", "rare", "legendary")
            
        Returns:
            Entity instance if chest type exists, None otherwise
        """
        chest_def = self.registry.get_map_feature(chest_type)
        if not chest_def or chest_def.feature_type != "chest":
            logger.warning(f"Unknown chest type: {chest_type}")
            return None
        
        try:
            from components.chest import Chest, ChestState
            
            # Convert chest_state string to ChestState enum
            state_map = {
                "closed": ChestState.CLOSED,
                "open": ChestState.OPEN,
                "trapped": ChestState.TRAPPED,
                "locked": ChestState.LOCKED
            }
            
            chest_state = state_map.get(chest_def.chest_state, ChestState.CLOSED)
            quality = loot_quality or chest_def.loot_quality or "common"
            
            # Create chest component
            chest_component = Chest(
                state=chest_state,
                loot=[],  # Will be populated later
                trap_type=chest_def.trap_type,
                key_id=chest_def.key_id,
                loot_quality=quality
            )
            
            # Create entity
            chest_entity = Entity(
                x=x,
                y=y,
                char=chest_def.char,
                color=chest_def.color,
                name=chest_def.name,
                blocks=chest_def.blocks
            )
            
            # Attach chest component
            chest_entity.chest = chest_component
            chest_component.owner = chest_entity
            chest_entity.components.add(ComponentType.CHEST, chest_component)
            
            # Set render order
            from render_functions import RenderOrder
            chest_entity.render_order = getattr(RenderOrder, chest_def.render_order.upper(), RenderOrder.ITEM)
            
            logger.debug(f"Created chest: {chest_def.name} at ({x}, {y}) [state: {chest_state.name}, quality: {quality}]")
            return chest_entity
        
        except Exception as e:
            logger.error(f"Error creating chest {chest_type}: {e}")
            return None
    
    def create_signpost(self, sign_type: str, x: int, y: int, message: Optional[str] = None, depth: int = 1) -> Optional[Entity]:
        """Create a signpost map feature entity from configuration.
        
        Signposts display readable messages and provide environmental storytelling.
        Messages are depth-aware and will be filtered based on the dungeon level.
        
        Args:
            sign_type: The type of sign to create (e.g., "signpost", "warning_sign", "humor_sign")
            x: X coordinate for the signpost
            y: Y coordinate for the signpost
            message: Override message text (None = random from pool)
            depth: Dungeon level for depth-specific messages
            
        Returns:
            Entity instance if signpost type exists, None otherwise
        """
        sign_def = self.registry.get_map_feature(sign_type)
        if not sign_def or sign_def.feature_type != "signpost":
            logger.warning(f"Unknown signpost type: {sign_type}")
            return None
        
        try:
            from components.signpost import Signpost
            
            # Use provided message or get random one for the type and depth
            actual_message = message or sign_def.message
            if not actual_message:
                actual_message = Signpost.get_random_message(sign_def.sign_type, depth)
            
            # Create signpost component
            signpost_component = Signpost(
                message=actual_message,
                sign_type=sign_def.sign_type
            )
            
            # Create entity
            sign_entity = Entity(
                x=x,
                y=y,
                char=sign_def.char,
                color=sign_def.color,
                name=sign_def.name,
                blocks=sign_def.blocks
            )
            
            # Attach signpost component
            sign_entity.signpost = signpost_component
            signpost_component.owner = sign_entity
            sign_entity.components.add(ComponentType.SIGNPOST, signpost_component)
            
            # Set render order
            from render_functions import RenderOrder
            sign_entity.render_order = getattr(RenderOrder, sign_def.render_order.upper(), RenderOrder.ITEM)
            
            logger.debug(f"Created signpost: {sign_def.name} at ({x}, {y}) [type: {sign_def.sign_type}]")
            return sign_entity
        
        except Exception as e:
            logger.error(f"Error creating signpost {sign_type}: {e}")
            return None

    def get_player_stats(self) -> Optional[EntityStats]:
        """Get player starting stats from configuration.
        
        Returns:
            EntityStats for player if configured, None otherwise
        """
        stats = self.registry.get_player_stats()
        if not stats:
            logger.warning("No player stats configured, using fallback values")
            return EntityStats(hp=100, power=0, defense=1, xp=0, damage_min=3, damage_max=4)  # Updated to new system
        
        return stats

    def _create_ai_component(self, ai_type: str):
        """Create an AI component based on type.
        
        Args:
            ai_type: The type of AI to create
            
        Returns:
            AI component instance
        """
        if ai_type == "basic":
            return BasicMonster()
        elif ai_type == "boss":
            return BossAI()
        elif ai_type == "slime":
            return SlimeAI()
        else:
            logger.warning(f"Unknown AI type: {ai_type}, using basic AI")
            return BasicMonster()
    
    def _create_boss_component(self, monster_type: str, boss_name: str):
        """Create a Boss component for a boss monster.
        
        Args:
            monster_type: Type of monster (e.g., "dragon_lord", "demon_king")
            boss_name: Display name for the boss
            
        Returns:
            Boss component instance
        """
        from components.boss import create_dragon_lord_boss, create_demon_king_boss
        
        # Use prefab boss configurations
        if monster_type == "dragon_lord":
            return create_dragon_lord_boss()
        elif monster_type == "demon_king":
            return create_demon_king_boss()
        else:
            # Generic boss for unknown types
            from components.boss import Boss
            logger.warning(f"Unknown boss type: {monster_type}, using generic boss")
            return Boss(boss_name=boss_name or monster_type.title())

    def _spawn_monster_equipment(self, monster: Entity, equipment_config: dict):
        """Spawn equipment on a monster based on configuration.
        
        Args:
            monster: The monster entity to equip
            equipment_config: Equipment configuration from YAML
                Format: {
                    'spawn_chances': {'main_hand': 0.75, 'chest': 0.50},
                    'equipment_pool': {
                        'main_hand': [{'item': 'club', 'weight': 40}, ...],
                        'chest': [{'item': 'leather_armor', 'weight': 100}]
                    }
                }
        """
        import random
        
        spawn_chances = equipment_config.get('spawn_chances', {})
        equipment_pool = equipment_config.get('equipment_pool', {})
        
        # Process each equipment slot
        for slot_name, spawn_chance in spawn_chances.items():
            # Roll for this slot
            if random.random() > spawn_chance:
                continue  # Didn't spawn equipment in this slot
            
            # Get items available for this slot
            slot_items = equipment_pool.get(slot_name, [])
            if not slot_items:
                logger.warning(f"No equipment pool defined for slot '{slot_name}'")
                continue
            
            # Select item using weighted random
            total_weight = sum(item_def.get('weight', 1) for item_def in slot_items)
            roll = random.random() * total_weight
            
            cumulative_weight = 0
            selected_item = None
            for item_def in slot_items:
                cumulative_weight += item_def.get('weight', 1)
                if roll <= cumulative_weight:
                    selected_item = item_def.get('item')
                    break
            
            if not selected_item:
                logger.warning(f"Failed to select item for slot '{slot_name}'")
                continue
            
            # Create the item (weapon or armor)
            # Items spawn at monster's position but will be immediately equipped
            item_entity = None
            if slot_name == 'main_hand' or slot_name == 'off_hand':
                item_entity = self.create_weapon(selected_item, monster.x, monster.y)
            elif slot_name in ['head', 'chest', 'feet']:
                item_entity = self.create_armor(selected_item, monster.x, monster.y)
            else:
                logger.warning(f"Unknown slot type '{slot_name}'")
                continue
            
            if not item_entity:
                logger.warning(f"Failed to create item '{selected_item}' for slot '{slot_name}'")
                continue
            
            # Equip the item on the monster
            equipment = monster.get_component_optional(ComponentType.EQUIPMENT)
            if not equipment:
                equipment = getattr(monster, 'equipment', None)
            
            if equipment and hasattr(item_entity, 'equippable'):
                # Add to monster's inventory first (required for equipping)
                inventory = monster.get_component_optional(ComponentType.INVENTORY)
                if not inventory:
                    inventory = getattr(monster, 'inventory', None)
                
                if inventory:
                    # Add to inventory
                    inventory.add_item(item_entity)
                    # Equip the item
                    results = equipment.toggle_equip(item_entity)
                    logger.debug(f"Equipped {selected_item} on {monster.name} in slot {slot_name}")
                else:
                    logger.warning(f"Monster {monster.name} has no inventory, cannot equip items")
            else:
                logger.warning(f"Cannot equip {selected_item} on {monster.name}")

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
            "feet": EquipmentSlots.FEET
        }
        
        slot = slot_map.get(slot_str)
        if slot:
            return slot
        else:
            logger.warning(f"Unknown equipment slot: {slot_str}, using MAIN_HAND")
            return EquipmentSlots.MAIN_HAND

    def _create_item_component(self, spell_def: SpellDefinition):
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
    
    def create_unique_item(self, item_type: str, x: int, y: int) -> Optional[Entity]:
        """Create a unique quest item entity.
        
        Unique items are special entities that trigger victory conditions,
        story events, or other unique gameplay mechanics.
        
        Args:
            item_type: Type of unique item (e.g., 'amulet_of_yendor', 'entity_portal')
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Entity instance or None if creation fails
        """
        # Get unique item definition from registry
        if not hasattr(self.registry, 'data') or 'unique_items' not in self.registry.data:
            logger.warning(f"No unique_items section in registry")
            return None
        
        unique_items = self.registry.data['unique_items']
        if item_type not in unique_items:
            logger.warning(f"Unique item type '{item_type}' not found in registry")
            return None
        
        item_def = unique_items[item_type]
        
        # Extract basic properties
        char = item_def.get('char', '?')
        color = tuple(item_def.get('color', [255, 255, 255]))
        description = item_def.get('description', 'A unique item.')
        name = item_type.replace('_', ' ').title()
        
        # Create item component
        item_component = Item()
        
        # Create entity
        entity = Entity(
            x=x, y=y,
            char=char,
            color=color,
            name=name,
            blocks=item_def.get('blocks', False),
            render_order=RenderOrder.ITEM,
            item=item_component
        )
        
        # Add special properties for quest items
        if item_def.get('is_quest_item'):
            entity.is_quest_item = True
        if item_def.get('triggers_victory'):
            entity.triggers_victory = True
        if item_def.get('is_portal'):
            entity.is_portal = True
        
        # Store description on entity for examine text
        entity.description = description
        
        return entity


# Global factory instance
_entity_factory = None


def get_entity_factory() -> EntityFactory:
    """Get the global entity factory instance.
    
    Returns:
        The global EntityFactory instance
    """
    global _entity_factory
    if _entity_factory is None:
        _entity_factory = EntityFactory()
    return _entity_factory


def set_entity_factory(factory: EntityFactory) -> None:
    """Set the global entity factory instance.
    
    Args:
        factory: EntityFactory instance to use globally
    """
    global _entity_factory
    _entity_factory = factory
