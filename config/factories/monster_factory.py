"""Monster creation factory.

Handles creation of all monster entities including:
- Basic monsters with AI and fighter components
- Equipment spawning on monsters
- Boss creation
- Fallback monsters
- Speed bonus tracking (Phase 4)
"""

import logging
from typing import Optional

from entity import Entity
from components.component_registry import ComponentType
from components.fighter import Fighter
from components.ai import BasicMonster, SlimeAI, BossAI
from components.inventory import Inventory
from components.equipment import Equipment
from components.faction import Faction, get_faction_from_string
from components.speed_bonus_tracker import SpeedBonusTracker
from render_functions import RenderOrder
from config.factories._factory_base import FactoryBase

logger = logging.getLogger(__name__)


class MonsterFactory(FactoryBase):
    """Factory for creating monster entities."""
    
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
                resistances=getattr(monster_def.stats, 'resistances', None),
                # Phase 8: Accuracy and Evasion (defaults if not specified in YAML)
                accuracy=getattr(monster_def.stats, 'accuracy', None),
                evasion=getattr(monster_def.stats, 'evasion', None)
            )

            # Create AI component based on ai_type
            ai_component = self._create_ai_component(monster_def.ai_type)
            
            # Create equipment component for monsters (needed for equipment system)
            equipment_component = Equipment()
            
            # Create inventory component for monsters that can seek items OR have equipment
            inventory_component = None
            has_equipment_config = hasattr(monster_def, 'equipment') and monster_def.equipment
            if (monster_def.can_seek_items and monster_def.inventory_size > 0) or has_equipment_config:
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
            
            # Set tags if defined (Phase 10: for plague_carrier, corporeal_flesh, etc.)
            if hasattr(monster_def, 'tags') and monster_def.tags:
                monster.tags = set(monster_def.tags)
            
            # Create item-seeking AI if monster can seek items
            if monster_def.can_seek_items:
                from components.item_seeking_ai import create_item_seeking_ai
                item_seeking_ai = create_item_seeking_ai(monster, monster_def)
                if item_seeking_ai:
                    # Note: Setting monster.item_seeking_ai triggers __setattr__ which auto-registers in components
                    monster.item_seeking_ai = item_seeking_ai  # Legacy attribute for backward compatibility
                    logger.debug(f"Added item-seeking AI to {monster_def.name}")
                else:
                    logger.warning(f"Failed to create item-seeking AI for {monster_def.name}")
            
            # Create item usage component if monster has inventory
            if inventory_component:
                from components.monster_item_usage import create_monster_item_usage
                item_usage = create_monster_item_usage(monster)
                if item_usage:
                    # Note: Setting monster.item_usage triggers __setattr__ which auto-registers in components
                    monster.item_usage = item_usage  # Legacy attribute for backward compatibility
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
                    # Note: Setting monster.boss triggers __setattr__ which auto-registers in components
                    monster.boss = boss_component
                    monster.is_boss = True  # Set attribute for death handler check (Phase 5)
                    logger.info(f"Created BOSS: {boss_component.boss_name}")

            # Create speed bonus tracker if monster has speed bonus (Phase 4)
            if hasattr(monster_def, 'speed_bonus') and monster_def.speed_bonus > 0:
                speed_tracker = SpeedBonusTracker(speed_bonus_ratio=monster_def.speed_bonus)
                monster.speed_bonus_tracker = speed_tracker
                speed_tracker.owner = monster
                monster.components.add(ComponentType.SPEED_BONUS_TRACKER, speed_tracker)
                logger.debug(f"Added speed bonus tracker to {monster_def.name}: +{int(monster_def.speed_bonus * 100)}%")

            logger.debug(f"Created monster: {monster_def.name} at ({x}, {y})")
            return monster

        except Exception as e:
            logger.error(f"Error creating monster {monster_type}: {e}")
            return self._create_fallback_monster(monster_type, x, y)

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
            monster_type: Type of monster (e.g., "dragon_lord", "demon_king", "zhyraxion_human")
            boss_name: Display name for the boss
            
        Returns:
            Boss component instance
        """
        from components.boss import create_dragon_lord_boss, create_demon_king_boss, Boss
        
        # Use prefab boss configurations
        if monster_type == "dragon_lord":
            return create_dragon_lord_boss()
        elif monster_type == "demon_king":
            return create_demon_king_boss()
        elif monster_type in ["zhyraxion_human", "zhyraxion_full_dragon", "zhyraxion_grief_dragon"]:
            # Phase 5 Zhyraxion bosses - use generic Boss with their configured boss_name
            logger.info(f"Creating Zhyraxion boss: {boss_name or monster_type}")
            return Boss(boss_name=boss_name or monster_type.replace('_', ' ').title())
        else:
            # Generic boss for unknown types
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
            # Import factories to avoid circular imports
            from config.factories.equipment_factory import EquipmentFactory
            
            equipment_factory = EquipmentFactory(
                entity_registry=self._registry,
                game_constants=self._game_constants,
                difficulty_level=self.difficulty_level
            )
            
            # Items spawn at monster's position but will be immediately equipped
            item_entity = None
            if slot_name == 'main_hand' or slot_name == 'off_hand':
                item_entity = equipment_factory.create_weapon(selected_item, monster.x, monster.y)
            elif slot_name in ['head', 'chest', 'feet']:
                item_entity = equipment_factory.create_armor(selected_item, monster.x, monster.y)
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

