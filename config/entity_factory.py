"""DEPRECATED: Backward-compatible shim for entity factory.

This module provides backward compatibility for code that imports from
the old location (config/entity_factory.py). All functionality has been
moved to config/factories/ organized by entity type.

MIGRATION PATH:
    Old: from config.entity_factory import EntityFactory, get_entity_factory
    New: from config.factories import EntityFactory, get_entity_factory

    Old: factory.create_monster("orc", 10, 20)
    New: factory.create_monster("orc", 10, 20)  # No change needed!

This shim ensures existing imports continue to work while allowing
gradual migration to the new module structure.
"""

import warnings

# Re-export everything from the new location
from config.factories import (
    EntityFactory,
    MonsterFactory,
    EquipmentFactory,
    ItemFactory,
    SpawnFactory,
    FactoryBase,
    get_entity_factory,
    set_entity_factory,
)

# Issue deprecation warning when this module is imported
warnings.warn(
    "Importing from config.entity_factory is deprecated. "
    "Please use 'from config.factories import EntityFactory' instead.",
    DeprecationWarning,
    stacklevel=2
)

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
