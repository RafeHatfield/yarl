"""
Level Template Registry - Manages level generation overrides and guaranteed spawns.

This module provides functionality to load and manage level templates from YAML files,
supporting both normal gameplay and testing mode configurations.

Tier 1: Guaranteed spawns
Tier 2: Level parameters and special themed rooms
"""

import os
import logging
import re
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field

import yaml

from config.testing_config import is_testing_mode


logger = logging.getLogger(__name__)


def parse_count_range(count_value: Union[int, str]) -> Tuple[int, int]:
    """
    Parse a count value that may be an integer or a range string.
    
    Args:
        count_value: Either an integer or a string like "3-5"
        
    Returns:
        Tuple of (min_count, max_count)
        
    Examples:
        parse_count_range(5) -> (5, 5)
        parse_count_range("3-5") -> (3, 5)
        parse_count_range("1-10") -> (1, 10)
    """
    if isinstance(count_value, int):
        return (count_value, count_value)
    
    if isinstance(count_value, str):
        # Try to parse range format "X-Y"
        match = re.match(r'^(\d+)-(\d+)$', count_value.strip())
        if match:
            min_val = int(match.group(1))
            max_val = int(match.group(2))
            if min_val <= max_val:
                return (min_val, max_val)
            else:
                logger.warning(
                    f"Invalid range '{count_value}': min > max, using ({max_val}, {min_val})"
                )
                return (max_val, min_val)
        
        # Try to parse as single integer
        try:
            val = int(count_value)
            return (val, val)
        except ValueError:
            pass
    
    logger.warning(f"Invalid count value '{count_value}', defaulting to (1, 1)")
    return (1, 1)


@dataclass
class GuaranteedSpawn:
    """Represents a guaranteed spawn (monster or item)."""
    entity_type: str
    count_min: int
    count_max: int
    
    def get_random_count(self) -> int:
        """Get a random count within the configured range."""
        from random import randint
        return randint(self.count_min, self.count_max)


@dataclass
class LevelParameters:
    """
    Parameters that control level generation.
    
    All parameters are optional - if not specified, defaults from
    GameConstants will be used.
    """
    max_rooms: Optional[int] = None
    min_room_size: Optional[int] = None
    max_room_size: Optional[int] = None
    max_monsters_per_room: Optional[int] = None
    max_items_per_room: Optional[int] = None
    
    def has_overrides(self) -> bool:
        """Check if any parameters are overridden."""
        return any([
            self.max_rooms is not None,
            self.min_room_size is not None,
            self.max_room_size is not None,
            self.max_monsters_per_room is not None,
            self.max_items_per_room is not None
        ])


@dataclass
class SpecialRoom:
    """
    Defines a special themed room with guaranteed spawns.
    
    Special rooms are selected from generated rooms based on size
    and placement strategy, then populated with guaranteed entities.
    """
    room_type: str
    count: int  # How many of this room type to create
    min_room_size: Optional[int] = None  # Minimum room size required
    placement: str = "random"  # "random", "largest", "smallest"
    guaranteed_monsters: List[GuaranteedSpawn] = field(default_factory=list)
    guaranteed_items: List[GuaranteedSpawn] = field(default_factory=list)
    guaranteed_equipment: List[GuaranteedSpawn] = field(default_factory=list)
    
    @property
    def all_guaranteed_spawns(self) -> List[GuaranteedSpawn]:
        """Get all guaranteed spawns combined."""
        return (self.guaranteed_monsters + 
                self.guaranteed_items + 
                self.guaranteed_equipment)


@dataclass
class LevelOverride:
    """Represents overrides for a specific dungeon level."""
    level_number: int
    mode: str  # "additional" or "replace" (for Tier 1 guaranteed spawns)
    guaranteed_monsters: List[GuaranteedSpawn]
    guaranteed_items: List[GuaranteedSpawn]
    guaranteed_equipment: List[GuaranteedSpawn]
    parameters: Optional[LevelParameters] = None  # Tier 2
    special_rooms: List[SpecialRoom] = field(default_factory=list)  # Tier 2
    
    @property
    def all_guaranteed_spawns(self) -> List[GuaranteedSpawn]:
        """Get all guaranteed spawns combined (Tier 1 only)."""
        return (self.guaranteed_monsters + 
                self.guaranteed_items + 
                self.guaranteed_equipment)
    
    def has_special_rooms(self) -> bool:
        """Check if this override has any special rooms configured."""
        return len(self.special_rooms) > 0
    
    def has_parameters(self) -> bool:
        """Check if this override has level parameters configured."""
        return self.parameters is not None and self.parameters.has_overrides()


class LevelTemplateRegistry:
    """
    Manages level templates and overrides from YAML configuration files.
    
    Supports two configuration files:
    - level_templates.yaml: Normal gameplay overrides
    - level_templates_testing.yaml: Testing mode overrides (takes precedence)
    """
    
    def __init__(self):
        """Initialize the registry."""
        self.overrides: Dict[int, LevelOverride] = {}
        self.version: Optional[str] = None
        
    def load_templates(self, config_dir: Optional[str] = None) -> None:
        """
        Load level templates from YAML files.
        
        Args:
            config_dir: Directory containing template files. If None, uses default.
        """
        if config_dir is None:
            config_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__))
            )
        
        # Load normal templates first
        normal_template_path = os.path.join(config_dir, 'level_templates.yaml')
        self._load_template_file(normal_template_path, is_testing=False)
        
        # Load testing templates if in testing mode (these override normal templates)
        if is_testing_mode():
            testing_template_path = os.path.join(
                config_dir, 'level_templates_testing.yaml'
            )
            self._load_template_file(testing_template_path, is_testing=True)
            
    def _load_template_file(self, filepath: str, is_testing: bool = False) -> None:
        """
        Load a single template file.
        
        Args:
            filepath: Path to the YAML file
            is_testing: Whether this is the testing template file
        """
        if not os.path.exists(filepath):
            mode_str = "testing" if is_testing else "normal"
            logger.info(f"No {mode_str} level template file found at {filepath}, skipping")
            return
            
        try:
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)
                
            if not data:
                logger.warning(f"Empty template file: {filepath}")
                return
                
            # Store version (last loaded file wins)
            self.version = data.get('version', 'unknown')
            
            # Parse level overrides
            level_overrides = data.get('level_overrides', {})
            for level_num, override_data in level_overrides.items():
                level_override = self._parse_level_override(level_num, override_data)
                
                # Testing templates override normal templates
                if is_testing or level_num not in self.overrides:
                    self.overrides[level_num] = level_override
                    mode_str = "testing" if is_testing else "normal"
                    logger.info(
                        f"Loaded {mode_str} template for level {level_num} "
                        f"(mode: {level_override.mode})"
                    )
                    
        except yaml.YAMLError as e:
            logger.error(f"Error parsing template file {filepath}: {e}")
        except Exception as e:
            logger.error(f"Error loading template file {filepath}: {e}")
            
    def _parse_level_override(
        self, 
        level_num: int, 
        data: Dict[str, Any]
    ) -> LevelOverride:
        """
        Parse a level override from YAML data.
        
        Supports both Tier 1 (guaranteed_spawns) and Tier 2 (parameters, special_rooms).
        
        Args:
            level_num: The level number
            data: The YAML data for this level
            
        Returns:
            LevelOverride object
        """
        # Parse Tier 1: guaranteed_spawns
        guaranteed_spawns = data.get('guaranteed_spawns', {})
        mode = guaranteed_spawns.get('mode', 'additional')
        
        # Validate mode
        if mode not in ['additional', 'replace']:
            logger.warning(
                f"Invalid mode '{mode}' for level {level_num}, "
                f"defaulting to 'additional'"
            )
            mode = 'additional'
        
        # Parse monsters
        monsters = []
        for monster_data in guaranteed_spawns.get('monsters', []):
            count_min, count_max = parse_count_range(monster_data['count'])
            monsters.append(GuaranteedSpawn(
                entity_type=monster_data['type'],
                count_min=count_min,
                count_max=count_max
            ))
            
        # Parse items
        items = []
        for item_data in guaranteed_spawns.get('items', []):
            count_min, count_max = parse_count_range(item_data['count'])
            items.append(GuaranteedSpawn(
                entity_type=item_data['type'],
                count_min=count_min,
                count_max=count_max
            ))
            
        # Parse equipment
        equipment = []
        for equip_data in guaranteed_spawns.get('equipment', []):
            count_min, count_max = parse_count_range(equip_data['count'])
            equipment.append(GuaranteedSpawn(
                entity_type=equip_data['type'],
                count_min=count_min,
                count_max=count_max
            ))
        
        # Parse Tier 2: parameters
        parameters = None
        if 'parameters' in data:
            params_data = data['parameters']
            parameters = LevelParameters(
                max_rooms=params_data.get('max_rooms'),
                min_room_size=params_data.get('min_room_size'),
                max_room_size=params_data.get('max_room_size'),
                max_monsters_per_room=params_data.get('max_monsters_per_room'),
                max_items_per_room=params_data.get('max_items_per_room')
            )
            
        # Parse Tier 2: special_rooms
        special_rooms = []
        for room_data in data.get('special_rooms', []):
            special_room = self._parse_special_room(room_data)
            special_rooms.append(special_room)
            
        return LevelOverride(
            level_number=level_num,
            mode=mode,
            guaranteed_monsters=monsters,
            guaranteed_items=items,
            guaranteed_equipment=equipment,
            parameters=parameters,
            special_rooms=special_rooms
        )
    
    def _parse_special_room(self, data: Dict[str, Any]) -> SpecialRoom:
        """
        Parse a special room definition from YAML data.
        
        Args:
            data: The YAML data for this special room
            
        Returns:
            SpecialRoom object
        """
        room_type = data.get('type', 'unknown')
        count = data.get('count', 1)
        min_room_size = data.get('min_room_size')
        placement = data.get('placement', 'random')
        
        # Validate placement strategy
        if placement not in ['random', 'largest', 'smallest']:
            logger.warning(
                f"Invalid placement '{placement}' for special room '{room_type}', "
                f"defaulting to 'random'"
            )
            placement = 'random'
        
        # Parse guaranteed spawns for this room
        spawns_data = data.get('guaranteed_spawns', {})
        
        monsters = []
        for monster_data in spawns_data.get('monsters', []):
            count_min, count_max = parse_count_range(monster_data['count'])
            monsters.append(GuaranteedSpawn(
                entity_type=monster_data['type'],
                count_min=count_min,
                count_max=count_max
            ))
        
        items = []
        for item_data in spawns_data.get('items', []):
            count_min, count_max = parse_count_range(item_data['count'])
            items.append(GuaranteedSpawn(
                entity_type=item_data['type'],
                count_min=count_min,
                count_max=count_max
            ))
        
        equipment = []
        for equip_data in spawns_data.get('equipment', []):
            count_min, count_max = parse_count_range(equip_data['count'])
            equipment.append(GuaranteedSpawn(
                entity_type=equip_data['type'],
                count_min=count_min,
                count_max=count_max
            ))
        
        return SpecialRoom(
            room_type=room_type,
            count=count,
            min_room_size=min_room_size,
            placement=placement,
            guaranteed_monsters=monsters,
            guaranteed_items=items,
            guaranteed_equipment=equipment
        )
        
    def get_level_override(self, level_number: int) -> Optional[LevelOverride]:
        """
        Get the override configuration for a specific level.
        
        Args:
            level_number: The dungeon level number
            
        Returns:
            LevelOverride if configured, None otherwise
        """
        return self.overrides.get(level_number)
        
    def has_override(self, level_number: int) -> bool:
        """
        Check if a level has an override configured.
        
        Args:
            level_number: The dungeon level number
            
        Returns:
            True if override exists, False otherwise
        """
        return level_number in self.overrides
        
    def clear(self) -> None:
        """Clear all loaded overrides (useful for testing)."""
        self.overrides.clear()
        self.version = None


# Global registry instance
_level_template_registry: Optional[LevelTemplateRegistry] = None


def get_level_template_registry() -> LevelTemplateRegistry:
    """
    Get the global level template registry instance.
    
    Returns:
        The global LevelTemplateRegistry instance
    """
    global _level_template_registry
    if _level_template_registry is None:
        _level_template_registry = LevelTemplateRegistry()
        _level_template_registry.load_templates()
    return _level_template_registry


def load_level_templates() -> None:
    """Load (or reload) level templates from YAML files."""
    global _level_template_registry
    _level_template_registry = LevelTemplateRegistry()
    _level_template_registry.load_templates()

