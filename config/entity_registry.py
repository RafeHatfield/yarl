"""Entity configuration registry system.

This module provides a centralized system for loading and managing entity
definitions from YAML configuration files. It supports inheritance, validation,
and fallback behavior for robust entity creation.

The EntityRegistry is designed to be loaded once at startup and provide
fast lookups during entity creation.
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    yaml = None

logger = logging.getLogger(__name__)


@dataclass
class EntityStats:
    """Base stats for any entity (player, monster, etc.)."""
    hp: int
    power: int
    defense: int
    xp: int = 0
    damage_min: Optional[int] = None
    damage_max: Optional[int] = None
    defense_min: Optional[int] = None
    defense_max: Optional[int] = None

    def __post_init__(self):
        """Validate stats after creation."""
        if self.hp < 1:
            raise ValueError(f"Entity HP must be >= 1, got {self.hp}")
        if self.power < 0:
            raise ValueError(f"Entity power must be >= 0, got {self.power}")
        if self.defense < 0:
            raise ValueError(f"Entity defense must be >= 0, got {self.defense}")
        if self.xp < 0:
            raise ValueError(f"Entity XP must be >= 0, got {self.xp}")
        
        # Validate damage range if specified
        if self.damage_min is not None and self.damage_max is not None:
            if self.damage_min > self.damage_max:
                raise ValueError(f"damage_min ({self.damage_min}) cannot be greater than damage_max ({self.damage_max})")
            if self.damage_min < 0:
                raise ValueError(f"damage_min must be >= 0, got {self.damage_min}")
        
        # Validate defense range if specified
        if self.defense_min is not None and self.defense_max is not None:
            if self.defense_min > self.defense_max:
                raise ValueError(f"defense_min ({self.defense_min}) cannot be greater than defense_max ({self.defense_max})")
            if self.defense_min < 0:
                raise ValueError(f"defense_min must be >= 0, got {self.defense_min}")


@dataclass
class MonsterDefinition:
    """Definition for a monster entity."""
    name: str
    stats: EntityStats
    char: str
    color: Tuple[int, int, int]
    ai_type: str = "basic"
    render_order: str = "actor"
    blocks: bool = True
    extends: Optional[str] = None
    # Item-seeking behavior
    can_seek_items: bool = False
    inventory_size: int = 0
    seek_distance: int = 5


@dataclass  
class WeaponDefinition:
    """Definition for a weapon item."""
    name: str
    power_bonus: int = 0
    damage_min: int = 0
    damage_max: int = 0
    slot: str = "main_hand"
    char: str = "/"
    color: Tuple[int, int, int] = (139, 69, 19)  # Brown
    extends: Optional[str] = None

    def __post_init__(self):
        """Validate weapon definition."""
        if self.power_bonus < 0:
            raise ValueError(f"Weapon power_bonus must be >= 0, got {self.power_bonus}")
        if self.damage_min < 0:
            raise ValueError(f"Weapon damage_min must be >= 0, got {self.damage_min}")
        if self.damage_max < self.damage_min:
            raise ValueError(f"Weapon damage_max ({self.damage_max}) cannot be less than damage_min ({self.damage_min})")
        if self.slot not in ["main_hand", "off_hand"]:
            raise ValueError(f"Weapon slot must be 'main_hand' or 'off_hand', got '{self.slot}'")


@dataclass
class ArmorDefinition:
    """Definition for an armor item."""
    name: str
    defense_bonus: int = 0
    defense_min: int = 0
    defense_max: int = 0
    slot: str = "off_hand"
    char: str = "["
    color: Tuple[int, int, int] = (139, 69, 19)  # Brown
    extends: Optional[str] = None

    def __post_init__(self):
        """Validate armor definition."""
        if self.defense_bonus < 0:
            raise ValueError(f"Armor defense_bonus must be >= 0, got {self.defense_bonus}")
        if self.defense_min < 0:
            raise ValueError(f"Armor defense_min must be >= 0, got {self.defense_min}")
        if self.defense_max < self.defense_min:
            raise ValueError(f"Armor defense_max ({self.defense_max}) cannot be less than defense_min ({self.defense_min})")
        if self.slot not in ["main_hand", "off_hand"]:
            raise ValueError(f"Armor slot must be 'main_hand' or 'off_hand', got '{self.slot}'")


@dataclass
class SpellDefinition:
    """Definition for a spell/consumable item."""
    name: str
    spell_type: str  # "damage", "heal", "utility"
    damage: int = 0
    heal_amount: int = 0
    maximum_range: int = 0
    radius: int = 0
    char: str = "?"
    color: Tuple[int, int, int] = (255, 255, 0)  # Yellow
    extends: Optional[str] = None

    def __post_init__(self):
        """Validate spell definition."""
        if self.damage < 0:
            raise ValueError(f"Spell damage must be >= 0, got {self.damage}")
        if self.heal_amount < 0:
            raise ValueError(f"Spell heal_amount must be >= 0, got {self.heal_amount}")
        if self.maximum_range < 0:
            raise ValueError(f"Spell maximum_range must be >= 0, got {self.maximum_range}")
        if self.radius < 0:
            raise ValueError(f"Spell radius must be >= 0, got {self.radius}")


class EntityRegistry:
    """Registry for all entity definitions loaded from configuration files.
    
    This class handles loading entity definitions from YAML files, resolving
    inheritance relationships, and providing fast lookups for entity creation.
    
    The registry supports:
    - Multiple configuration files
    - Entity inheritance via 'extends' keyword
    - Validation of all entity definitions
    - Fallback to default values for missing definitions
    """

    def __init__(self):
        """Initialize an empty entity registry."""
        self.monsters: Dict[str, MonsterDefinition] = {}
        self.weapons: Dict[str, WeaponDefinition] = {}
        self.armor: Dict[str, ArmorDefinition] = {}
        self.spells: Dict[str, SpellDefinition] = {}
        self.player_stats: Optional[EntityStats] = None
        self._loaded = False

    def load_from_file(self, config_path: str) -> None:
        """Load entity definitions from a YAML configuration file.
        
        Args:
            config_path: Path to the YAML configuration file
            
        Raises:
            FileNotFoundError: If the configuration file doesn't exist
            ValueError: If the configuration file is invalid
            RuntimeError: If YAML support is not available
        """
        if not YAML_AVAILABLE:
            raise RuntimeError("YAML support not available. Install PyYAML: pip install PyYAML")

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Entity configuration file not found: {config_path}")

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            if not config_data:
                logger.warning(f"Empty or invalid YAML file: {config_path}")
                return

            self._process_config_data(config_data)
            self._resolve_inheritance()
            self._loaded = True
            
            logger.info(f"Loaded entity configuration from {config_path}")
            logger.info(f"  Monsters: {len(self.monsters)}")
            logger.info(f"  Weapons: {len(self.weapons)}")
            logger.info(f"  Armor: {len(self.armor)}")
            logger.info(f"  Spells: {len(self.spells)}")

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in entity configuration: {e}")
        except Exception as e:
            logger.error(f"Error loading entity configuration from {config_path}: {e}")
            raise

    def _process_config_data(self, config_data: Dict[str, Any]) -> None:
        """Process raw configuration data into entity definitions.
        
        Args:
            config_data: Raw configuration data from YAML file
        """
        # Load player stats
        if 'player' in config_data:
            try:
                self.player_stats = EntityStats(**config_data['player'])
            except Exception as e:
                logger.error(f"Error loading player stats: {e}")
                raise ValueError(f"Invalid player configuration: {e}")

        # Load monsters
        if 'monsters' in config_data:
            for monster_id, monster_data in config_data['monsters'].items():
                try:
                    # Handle stats sub-object
                    stats_data = monster_data.get('stats', {})
                    stats = EntityStats(**stats_data)
                    
                    # Create monster definition
                    monster_def = MonsterDefinition(
                        name=monster_id.title(),
                        stats=stats,
                        char=monster_data.get('char', '?'),
                        color=tuple(monster_data.get('color', [255, 255, 255])),
                        ai_type=monster_data.get('ai_type', 'basic'),
                        render_order=monster_data.get('render_order', 'actor'),
                        blocks=monster_data.get('blocks', True),
                        extends=monster_data.get('extends'),
                        # Item-seeking behavior
                        can_seek_items=monster_data.get('can_seek_items', False),
                        inventory_size=monster_data.get('inventory_size', 0),
                        seek_distance=monster_data.get('seek_distance', 5)
                    )
                    
                    self.monsters[monster_id] = monster_def
                    
                except Exception as e:
                    logger.error(f"Error loading monster '{monster_id}': {e}")
                    raise ValueError(f"Invalid monster configuration for '{monster_id}': {e}")

        # Load weapons
        if 'weapons' in config_data:
            for weapon_id, weapon_data in config_data['weapons'].items():
                try:
                    weapon_def = WeaponDefinition(
                        name=weapon_id.title(),
                        power_bonus=weapon_data.get('power_bonus', 0),
                        damage_min=weapon_data.get('damage_min', 0),
                        damage_max=weapon_data.get('damage_max', 0),
                        slot=weapon_data.get('slot', 'main_hand'),
                        char=weapon_data.get('char', '/'),
                        color=tuple(weapon_data.get('color', [139, 69, 19])),
                        extends=weapon_data.get('extends')
                    )
                    
                    self.weapons[weapon_id] = weapon_def
                    
                except Exception as e:
                    logger.error(f"Error loading weapon '{weapon_id}': {e}")
                    raise ValueError(f"Invalid weapon configuration for '{weapon_id}': {e}")

        # Load armor
        if 'armor' in config_data:
            for armor_id, armor_data in config_data['armor'].items():
                try:
                    armor_def = ArmorDefinition(
                        name=armor_id.title(),
                        defense_bonus=armor_data.get('defense_bonus', 0),
                        defense_min=armor_data.get('defense_min', 0),
                        defense_max=armor_data.get('defense_max', 0),
                        slot=armor_data.get('slot', 'off_hand'),
                        char=armor_data.get('char', '['),
                        color=tuple(armor_data.get('color', [139, 69, 19])),
                        extends=armor_data.get('extends')
                    )
                    
                    self.armor[armor_id] = armor_def
                    
                except Exception as e:
                    logger.error(f"Error loading armor '{armor_id}': {e}")
                    raise ValueError(f"Invalid armor configuration for '{armor_id}': {e}")

        # Load spells
        if 'spells' in config_data:
            for spell_id, spell_data in config_data['spells'].items():
                try:
                    spell_def = SpellDefinition(
                        name=spell_id.replace('_', ' ').title(),
                        spell_type=spell_data.get('spell_type', 'utility'),
                        damage=spell_data.get('damage', 0),
                        heal_amount=spell_data.get('heal_amount', 0),
                        maximum_range=spell_data.get('maximum_range', 0),
                        radius=spell_data.get('radius', 0),
                        char=spell_data.get('char', '?'),
                        color=tuple(spell_data.get('color', [255, 255, 0])),
                        extends=spell_data.get('extends')
                    )
                    
                    self.spells[spell_id] = spell_def
                    
                except Exception as e:
                    logger.error(f"Error loading spell '{spell_id}': {e}")
                    raise ValueError(f"Invalid spell configuration for '{spell_id}': {e}")

    def _resolve_inheritance(self) -> None:
        """Resolve inheritance relationships between entity definitions.
        
        This method processes 'extends' relationships to apply inheritance,
        allowing entities to inherit properties from parent definitions.
        """
        # Resolve monster inheritance
        self._resolve_entity_inheritance(self.monsters, 'monster')
        
        # Resolve weapon inheritance  
        self._resolve_entity_inheritance(self.weapons, 'weapon')
        
        # Resolve armor inheritance
        self._resolve_entity_inheritance(self.armor, 'armor')
        
        # Resolve spell inheritance
        self._resolve_entity_inheritance(self.spells, 'spell')

    def _resolve_entity_inheritance(self, entity_dict: Dict[str, Any], entity_type: str) -> None:
        """Resolve inheritance for a specific entity type.
        
        Args:
            entity_dict: Dictionary of entity definitions
            entity_type: Type of entity for error reporting
        """
        # Simple inheritance resolution - could be enhanced for multi-level inheritance
        for entity_id, entity_def in entity_dict.items():
            if entity_def.extends:
                parent_id = entity_def.extends
                if parent_id not in entity_dict:
                    logger.warning(f"{entity_type} '{entity_id}' extends unknown parent '{parent_id}'")
                    continue
                
                # TODO: Implement inheritance merging logic
                # For now, we just log the inheritance relationship
                logger.debug(f"{entity_type} '{entity_id}' extends '{parent_id}'")

    def get_monster(self, monster_id: str) -> Optional[MonsterDefinition]:
        """Get a monster definition by ID.
        
        Args:
            monster_id: The monster identifier
            
        Returns:
            MonsterDefinition if found, None otherwise
        """
        return self.monsters.get(monster_id)

    def get_weapon(self, weapon_id: str) -> Optional[WeaponDefinition]:
        """Get a weapon definition by ID.
        
        Args:
            weapon_id: The weapon identifier
            
        Returns:
            WeaponDefinition if found, None otherwise
        """
        return self.weapons.get(weapon_id)

    def get_armor(self, armor_id: str) -> Optional[ArmorDefinition]:
        """Get an armor definition by ID.
        
        Args:
            armor_id: The armor identifier
            
        Returns:
            ArmorDefinition if found, None otherwise
        """
        return self.armor.get(armor_id)

    def get_spell(self, spell_id: str) -> Optional[SpellDefinition]:
        """Get a spell definition by ID.
        
        Args:
            spell_id: The spell identifier
            
        Returns:
            SpellDefinition if found, None otherwise
        """
        return self.spells.get(spell_id)

    def get_player_stats(self) -> Optional[EntityStats]:
        """Get the player starting stats.
        
        Returns:
            EntityStats for player if loaded, None otherwise
        """
        return self.player_stats

    def is_loaded(self) -> bool:
        """Check if the registry has been loaded from configuration.
        
        Returns:
            True if configuration has been loaded, False otherwise
        """
        return self._loaded

    def get_all_monster_ids(self) -> List[str]:
        """Get a list of all available monster IDs.
        
        Returns:
            List of monster identifiers
        """
        return list(self.monsters.keys())

    def get_all_weapon_ids(self) -> List[str]:
        """Get a list of all available weapon IDs.
        
        Returns:
            List of weapon identifiers
        """
        return list(self.weapons.keys())

    def get_all_armor_ids(self) -> List[str]:
        """Get a list of all available armor IDs.
        
        Returns:
            List of armor identifiers
        """
        return list(self.armor.keys())

    def get_all_spell_ids(self) -> List[str]:
        """Get a list of all available spell IDs.
        
        Returns:
            List of spell identifiers
        """
        return list(self.spells.keys())


# Global entity registry instance
_entity_registry = EntityRegistry()


def get_entity_registry() -> EntityRegistry:
    """Get the global entity registry instance.
    
    Returns:
        The global EntityRegistry instance
    """
    return _entity_registry


def load_entity_config(config_path: str = None) -> None:
    """Load entity configuration from file.
    
    Args:
        config_path: Path to configuration file. If None, uses path from GameConstants.
    """
    if config_path is None:
        # Get path from GameConstants
        from config.game_constants import get_entity_config
        entity_config = get_entity_config()
        config_path = entity_config.ENTITIES_CONFIG_PATH
        
        # Make path relative to project root if it's not absolute
        if not os.path.isabs(config_path):
            config_dir = Path(__file__).parent.parent  # Go up to project root
            config_path = config_dir / config_path
    
    _entity_registry.load_from_file(str(config_path))
