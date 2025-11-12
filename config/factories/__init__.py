"""Factory module for entity creation.

This module provides unified access to all factory classes for creating
game entities (monsters, items, equipment, map features, etc.).

The factories are organized by responsibility:
- MonsterFactory: Creates monsters with AI and equipment
- EquipmentFactory: Creates weapons, armor, and rings
- ItemFactory: Creates consumables and wands
- SpawnFactory: Creates map features (chests, signposts, murals, portals) and unique items

Example:
    from config.factories import EntityFactory
    factory = EntityFactory()
    orc = factory.create_monster("orc", 10, 20)
    sword = factory.create_weapon("sword", 10, 20)
"""

from config.factories._factory_base import FactoryBase
from config.factories.monster_factory import MonsterFactory
from config.factories.equipment_factory import EquipmentFactory
from config.factories.item_factory import ItemFactory
from config.factories.spawn_factory import SpawnFactory


class EntityFactory(
    MonsterFactory,
    EquipmentFactory,
    ItemFactory,
    SpawnFactory
):
    """Unified entity factory combining all factory types.
    
    Provides a single interface for creating any entity type. Methods are
    organized by category but accessible through a single factory instance.
    
    Categories:
    - Monsters: create_monster()
    - Equipment: create_weapon(), create_armor(), create_ring()
    - Items: create_spell_item(), create_wand()
    - Features: create_chest(), create_signpost(), create_mural(),
               create_portal(), create_wand_of_portals()
    - Unique: create_unique_item(), create_unique_npc()
    - Player: get_player_stats()
    """
    pass


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


__all__ = [
    'EntityFactory',
    'MonsterFactory',
    'EquipmentFactory',
    'ItemFactory',
    'SpawnFactory',
    'FactoryBase',
    'get_entity_factory',
    'set_entity_factory',
]

