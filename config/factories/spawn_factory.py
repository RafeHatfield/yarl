"""Spawn/feature creation factory.

Handles creation of map features and utility items:
- Chests (containers with loot)
- Signposts (readable messages)
- Murals (environmental storytelling)
- Portals (teleportation gateways)
- Wand of Portals (legendary item)
- Unique items and NPCs
"""

import logging
from typing import Optional

from entity import Entity
from components.component_registry import ComponentType
from components.item import Item
from components.chest import Chest, ChestState
from components.signpost import Signpost
from components.mural import Mural
from components.portal import Portal
from components.portal_placer import PortalPlacer
from components.wand import Wand
from render_functions import RenderOrder
from config.factories._factory_base import FactoryBase

logger = logging.getLogger(__name__)


class SpawnFactory(FactoryBase):
    """Factory for creating map features and special items."""
    
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
            
            # Create entity - chests block movement
            chest_entity = Entity(
                x=x,
                y=y,
                char=chest_def.char,
                color=chest_def.color,
                name=chest_def.name,
                blocks=True  # Chests block movement; interact via right-click adjacently
            )
            
            # Attach chest component
            # Note: Setting chest_entity.chest triggers __setattr__ which auto-registers in components
            chest_entity.chest = chest_component
            chest_component.owner = chest_entity
            
            # Mark chest as openable (for right-click interaction)
            chest_entity.tags.add("openable")
            
            # Set render order
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
            # Use provided message or get random one for the type and depth
            actual_message = message or sign_def.message
            if not actual_message:
                actual_message = Signpost.get_random_message(sign_def.sign_type, depth)
            
            # Create signpost component
            signpost_component = Signpost(
                message=actual_message,
                sign_type=sign_def.sign_type
            )
            
            # Create entity - signposts block movement
            sign_entity = Entity(
                x=x,
                y=y,
                char=sign_def.char,
                color=sign_def.color,
                name=sign_def.name,
                blocks=True  # Signposts block movement; interact via right-click adjacently
            )
            # Mark as interactable
            sign_entity.tags.add('interactable')
            
            # Attach signpost component
            # Note: Setting sign_entity.signpost triggers __setattr__ which auto-registers in components
            sign_entity.signpost = signpost_component
            signpost_component.owner = sign_entity
            
            # Set render order
            sign_entity.render_order = getattr(RenderOrder, sign_def.render_order.upper(), RenderOrder.ITEM)
            
            logger.debug(f"Created signpost: {sign_def.name} at ({x}, {y}) [type: {sign_def.sign_type}]")
            return sign_entity
        
        except Exception as e:
            logger.error(f"Error creating signpost {sign_type}: {e}")
            return None
    
    def create_mural(self, x: int, y: int, depth: int = 1) -> Optional[Entity]:
        """Create a mural or inscription map feature entity.
        
        Murals display environmental lore about the dungeon's history and
        the tragedy of Zhyraxion and Aurelyn. Text is depth-aware and unique per floor.
        
        Args:
            x: X coordinate for the mural
            y: Y coordinate for the mural
            depth: Dungeon level for depth-specific murals
            
        Returns:
            Entity instance if mural creation succeeds, None otherwise
        """
        try:
            # Get a unique mural for this depth (no repeats on same floor)
            from services.mural_manager import get_mural_manager
            mural_manager = get_mural_manager()
            mural_text, mural_id = mural_manager.get_unique_mural(depth)
            
            if not mural_text:
                # No murals available for this depth
                return None
            
            # Create mural component
            mural_component = Mural(text=mural_text, mural_id=mural_id)
            
            # Create entity - murals block movement
            mural_entity = Entity(
                x=x,
                y=y,
                char="M",  # Mural character
                color=(220, 20, 60),  # Crimson red
                name="Mural",
                blocks=True  # Murals block movement; interact via right-click adjacently
            )
            # Mark as interactable
            mural_entity.tags.add('interactable')
            
            # Attach mural component
            # Note: Setting mural_entity.mural triggers __setattr__ which auto-registers in components
            mural_entity.mural = mural_component
            mural_component.owner = mural_entity
            
            # Set render order
            mural_entity.render_order = RenderOrder.ITEM
            
            logger.debug(f"Created mural at ({x}, {y}) [id: {mural_id}, depth: {depth}]")
            return mural_entity
        
        except Exception as e:
            logger.error(f"Error creating mural: {e}")
            return None
    
    def create_wand_of_portals(self, x: int, y: int) -> Optional[Entity]:
        """Create Wand of Portals legendary item.
        
        The wand allows creation of two-portal pairs for tactical teleportation.
        Starts with finite charges. Using wand while portals are active cancels
        them and refunds the charge.
        
        Flow:
        - Use wand: place entrance portal (costs 1 charge)
        - Use wand: place exit portal (pair now active)
        - Use wand while active: cancel portals, refund 1 charge
        
        Args:
            x: X coordinate for wand
            y: Y coordinate for wand
            
        Returns:
            Entity instance if creation succeeds, None otherwise
        """
        try:
            from item_functions import use_wand_of_portals
            
            # Create wand entity
            wand_entity = Entity(
                x=x,
                y=y,
                char='/',
                color=(100, 255, 200),
                name='Wand of Portals',
                blocks=False
            )
            
            # Attach Item component with targeting enabled
            # The use function will be called when selected from inventory
            item_component = Item(
                use_function=use_wand_of_portals,
                targeting=True,  # Enters targeting mode when used
                identified=True,
                item_category="wand",
                stackable=False
            )
            item_component.owner = wand_entity
            wand_entity.item = item_component
            
            # Attach PortalPlacer component (which extends Wand)
            # This handles both charge tracking AND portal lifecycle management
            # PortalPlacer.__init__ sets charges=3 by default
            # Note: Setting attributes triggers __setattr__ which auto-registers in components
            portal_placer = PortalPlacer()
            portal_placer.owner = wand_entity
            wand_entity.portal_placer = portal_placer
            
            # Also set as 'wand' attribute for compatibility with code that checks entity.wand
            # PortalPlacer extends Wand so this works
            wand_entity.wand = portal_placer
            
            # Set render order
            wand_entity.render_order = RenderOrder.ITEM
            
            logger.debug(f"Created Wand of Portals at ({x}, {y}) with {portal_placer.charges} charges")
            return wand_entity
        
        except Exception as e:
            logger.error(f"Error creating Wand of Portals: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def create_portal(
        self,
        x: int,
        y: int,
        portal_type: str = 'entrance',
        linked: Optional[Portal] = None
    ) -> Optional[Entity]:
        """Create a portal entity using YAML definitions.
        
        Portals are dimensional gateways that teleport entities.
        - Entrance (cyan): Entry point
        - Exit (orange): Destination point
        
        Args:
            x: X coordinate for portal
            y: Y coordinate for portal
            portal_type: 'entrance' or 'exit'
            linked: Linked portal (if creating pair)
            
        Returns:
            Entity instance if creation succeeds, None otherwise
        """
        try:
            # Determine which YAML entity to use based on portal type
            yaml_entity_type = 'portal_entrance' if portal_type == 'entrance' else 'portal_exit'
            
            # Create base entity from YAML (will have char, color, name, is_portal flag, and Item component)
            entity = self.create_unique_item(yaml_entity_type, x, y)
            
            if not entity:
                logger.error(f"Failed to create portal entity from YAML: {yaml_entity_type}")
                return None
            
            # Attach portal component (Item component is already added by create_unique_item)
            # Note: Setting entity.portal triggers __setattr__ which auto-registers in components
            portal = Portal(portal_type, linked_portal=linked)
            entity.portal = portal
            portal.owner = entity  # Set owner so we can get position
            
            logger.debug(f"Created {portal_type} portal at ({x}, {y}) using YAML definition")
            return entity
        
        except Exception as e:
            import traceback
            logger.error(f"Error creating portal: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def create_unique_item(self, item_type: str, x: int, y: int) -> Optional[Entity]:
        """Create a unique quest item entity.
        
        Unique items are special entities that trigger victory conditions,
        story events, or other unique gameplay mechanics.
        
        Args:
            item_type: Type of unique item (e.g., 'ruby_heart', 'entity_portal')
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
        
        # Create item component (portals ARE pickupable for future Portal system!)
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

        # Handle use_function for unique items (like Crimson Ritual Codex)
        if item_def.get('use_function'):
            use_function_name = item_def['use_function']
            # Import item_functions module and get the function by name
            import item_functions
            try:
                use_function = getattr(item_functions, use_function_name)
                item_component.use_function = use_function
            except AttributeError:
                logger.warning(f"Unknown use_function '{use_function_name}' for unique item '{item_type}'")
        
        # Store description on entity for examine text
        entity.description = description
        
        return entity
    
    def create_unique_npc(self, npc_type: str, x: int, y: int, dungeon_level: int = 1) -> Optional[Entity]:
        """Create a unique NPC entity (e.g., Ghost Guide).
        
        Unique NPCs are special entities that provide dialogue, quests, or story.
        
        Args:
            npc_type: Type of unique NPC (e.g., 'ghost_guide')
            x: X coordinate
            y: Y coordinate
            dungeon_level: Current dungeon level (for dialogue loading)
            
        Returns:
            Entity instance or None if creation fails
        """
        # Get unique NPC definition from registry
        if not hasattr(self.registry, 'data') or 'unique_npcs' not in self.registry.data:
            logger.warning(f"No unique_npcs section in registry")
            return None
        
        unique_npcs = self.registry.data['unique_npcs']
        if npc_type not in unique_npcs:
            logger.warning(f"Unique NPC type '{npc_type}' not found in registry")
            return None
        
        npc_def = unique_npcs[npc_type]
        
        # Extract basic properties
        char = npc_def.get('char', '@')
        color = tuple(npc_def.get('color', [255, 255, 255]))
        description = npc_def.get('description', 'A mysterious figure.')
        name = npc_def.get('name', npc_type.replace('_', ' ').title())
        blocks = npc_def.get('blocks', False)  # Ghosts don't block
        
        # Create entity
        entity = Entity(
            x=x, y=y,
            char=char,
            color=color,
            name=name,
            blocks=blocks,
            render_order=RenderOrder.ACTOR
        )
        
        # Add dialogue component if specified
        if npc_def.get('has_dialogue', False):
            dialogue_source = npc_def.get('dialogue_source', 'guide_dialogue')
            
            # Load dialogue from YAML
            import yaml
            import os
            from components.npc_dialogue import create_dialogue_from_yaml
            from utils.resource_paths import get_resource_path
            
            dialogue_file = get_resource_path(f"config/{dialogue_source}.yaml")
            if os.path.exists(dialogue_file):
                with open(dialogue_file, 'r') as f:
                    dialogue_data = yaml.safe_load(f)
                
                npc_dialogue = create_dialogue_from_yaml(dialogue_data)
                entity.npc_dialogue = npc_dialogue
                logger.info(f"Loaded dialogue for {name} from {dialogue_file}")
            else:
                logger.warning(f"Dialogue file not found: {dialogue_file}")
        
        # Add special flags
        entity.is_npc = npc_def.get('is_npc', True)
        entity.is_guide = npc_def.get('is_guide', False)
        entity.is_intangible = npc_def.get('is_intangible', False)
        entity.flavor_text = npc_def.get('flavor_text', '')
        
        logger.info(f"Created unique NPC: {name} at ({x}, {y})")
        return entity

    def create_door(self, door_type: str, x: int, y: int) -> Optional[Entity]:
        """Create a door entity from configuration.
        
        Doors are placed in corridors to create passage barriers.
        
        Args:
            door_type: The type of door (e.g., "wooden_door", "iron_door", "stone_door")
            x: X coordinate for the door
            y: Y coordinate for the door
            
        Returns:
            Entity instance if door type exists, None otherwise
        """
        door_def = self.registry.get_map_feature(door_type)
        if not door_def:
            logger.warning(f"Unknown door type: {door_type}")
            return None
        
        try:
            # Create entity
            door_entity = Entity(
                x=x,
                y=y,
                char=door_def.char,
                color=door_def.color,
                name=door_def.name,
                blocks=door_def.blocks
            )
            
            # Set render order
            door_entity.render_order = getattr(RenderOrder, door_def.render_order.upper(), RenderOrder.ITEM)
            
            logger.debug(f"Created door: {door_def.name} at ({x}, {y})")
            return door_entity
        
        except Exception as e:
            logger.error(f"Error creating door {door_type}: {e}")
            return None
    
    def create_trap(self, trap_type: str, x: int, y: int) -> Optional[Entity]:
        """Create a trap entity from configuration.
        
        Traps are hazardous map features that trigger when stepped on.
        They can be detected, disarmed, and have configurable effects.
        
        Args:
            trap_type: The type of trap (e.g., "spike_trap", "web_trap", "alarm_plate")
            x: X coordinate for the trap
            y: Y coordinate for the trap
            
        Returns:
            Entity instance if trap type exists, None otherwise
        """
        from components.trap import Trap
        
        try:
            # Get trap definition from registry
            if not hasattr(self.registry, 'data') or 'map_traps' not in self.registry.data:
                logger.warning(f"No map_traps section in registry")
                return None
            
            traps = self.registry.data['map_traps']
            if trap_type not in traps:
                logger.warning(f"Unknown trap type: {trap_type}")
                return None
            
            trap_def = traps[trap_type]
            
            # Extract trap configuration
            char = trap_def.get('char', 'X')
            color = tuple(trap_def.get('color', [192, 32, 32]))
            name = trap_def.get('name', trap_type.replace('_', ' ').title())
            blocks = trap_def.get('blocks', False)
            description = trap_def.get('description', f'A {trap_type}')
            
            # Extract detection settings
            is_detectable = trap_def.get('is_detectable', True)
            passive_detect_chance = trap_def.get('passive_detect_chance', 0.1)
            
            # Extract trap-specific effects (defaults based on type)
            if trap_type == "spike_trap":
                spike_damage = trap_def.get('spike_damage', 7)
                spike_bleed_severity = trap_def.get('spike_bleed_severity', 1)
                spike_bleed_duration = trap_def.get('spike_bleed_duration', 3)
                
                trap_component = Trap(
                    trap_type=trap_type,
                    detectable=is_detectable,
                    passive_detect_chance=passive_detect_chance,
                    spike_damage=spike_damage,
                    spike_bleed_severity=spike_bleed_severity,
                    spike_bleed_duration=spike_bleed_duration
                )
            
            elif trap_type == "web_trap":
                web_slow_severity = trap_def.get('web_slow_severity', 1)
                web_duration = trap_def.get('web_duration', 5)
                
                trap_component = Trap(
                    trap_type=trap_type,
                    detectable=is_detectable,
                    passive_detect_chance=passive_detect_chance,
                    web_slow_severity=web_slow_severity,
                    web_duration=web_duration
                )
            
            elif trap_type == "alarm_plate":
                alarm_faction = trap_def.get('alarm_faction', 'orc')
                alarm_radius = trap_def.get('alarm_radius', 8)
                
                trap_component = Trap(
                    trap_type=trap_type,
                    detectable=is_detectable,
                    passive_detect_chance=passive_detect_chance,
                    alarm_faction=alarm_faction,
                    alarm_radius=alarm_radius
                )
            
            elif trap_type == "root_trap":
                # Phase 21.1: Root trap applies EntangledEffect
                entangle_duration = trap_def.get('entangle_duration', 3)
                
                trap_component = Trap(
                    trap_type=trap_type,
                    detectable=is_detectable,
                    passive_detect_chance=passive_detect_chance,
                    entangle_duration=entangle_duration
                )
            
            else:
                # Generic trap for unknown types
                trap_component = Trap(
                    trap_type=trap_type,
                    detectable=is_detectable,
                    passive_detect_chance=passive_detect_chance
                )
            
            # Create entity
            trap_entity = Entity(
                x=x,
                y=y,
                char=char,
                color=color,
                name=name,
                blocks=blocks,
                render_order=RenderOrder.ITEM
            )
            
            # Attach trap component (auto-registers via __setattr__)
            trap_entity.trap = trap_component
            trap_component.owner = trap_entity
            
            logger.debug(f"Created trap: {name} at ({x}, {y}) [type: {trap_type}]")
            return trap_entity
        
        except Exception as e:
            logger.error(f"Error creating trap {trap_type}: {e}")
            return None
    
    def get_player_stats(self):
        """Get player starting stats from configuration.
        
        Returns:
            EntityStats for player if configured, None otherwise
        """
        from config.entity_registry import EntityStats
        
        stats = self.registry.get_player_stats()
        if not stats:
            logger.warning("No player stats configured, using fallback values")
            return EntityStats(hp=100, power=0, defense=1, xp=0, damage_min=3, damage_max=4)  # Updated to new system
        
        return stats

