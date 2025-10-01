"""
Level Template Registry - Manages level generation overrides and guaranteed spawns.

This module provides functionality to load and manage level templates from YAML files,
supporting both normal gameplay and testing mode configurations.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import yaml

from config.testing_config import is_testing_mode


logger = logging.getLogger(__name__)


@dataclass
class GuaranteedSpawn:
    """Represents a guaranteed spawn (monster or item)."""
    entity_type: str
    count: int


@dataclass
class LevelOverride:
    """Represents overrides for a specific dungeon level."""
    level_number: int
    mode: str  # "additional" or "replace"
    guaranteed_monsters: List[GuaranteedSpawn]
    guaranteed_items: List[GuaranteedSpawn]
    guaranteed_equipment: List[GuaranteedSpawn]
    
    @property
    def all_guaranteed_spawns(self) -> List[GuaranteedSpawn]:
        """Get all guaranteed spawns combined."""
        return (self.guaranteed_monsters + 
                self.guaranteed_items + 
                self.guaranteed_equipment)


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
        
        Args:
            level_num: The level number
            data: The YAML data for this level
            
        Returns:
            LevelOverride object
        """
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
            monsters.append(GuaranteedSpawn(
                entity_type=monster_data['type'],
                count=monster_data['count']
            ))
            
        # Parse items
        items = []
        for item_data in guaranteed_spawns.get('items', []):
            items.append(GuaranteedSpawn(
                entity_type=item_data['type'],
                count=item_data['count']
            ))
            
        # Parse equipment
        equipment = []
        for equip_data in guaranteed_spawns.get('equipment', []):
            equipment.append(GuaranteedSpawn(
                entity_type=equip_data['type'],
                count=equip_data['count']
            ))
            
        return LevelOverride(
            level_number=level_num,
            mode=mode,
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

