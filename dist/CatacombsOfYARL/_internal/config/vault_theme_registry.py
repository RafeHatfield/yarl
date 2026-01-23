"""Vault Theme Registry.

This module manages loading and accessing vault theme configurations from YAML.
Provides a centralized registry for all vault themes with depth-based spawn rates.

Example:
    >>> from config.vault_theme_registry import get_vault_theme_registry
    >>> registry = get_vault_theme_registry()
    >>> theme = registry.get_theme('treasure')
    >>> print(theme['name'])  # "Treasure Vault"
"""

import yaml
import logging
import os
from typing import Dict, Optional, List, Any

from utils.resource_paths import get_resource_path

logger = logging.getLogger(__name__)

class VaultThemeRegistry:
    """Registry for vault theme configurations.
    
    Loads vault themes from vault_themes.yaml and provides access methods
    for retrieving theme data, spawn rates, and configuration.
    
    Attributes:
        themes: Dictionary mapping theme IDs to theme configurations
        default_theme: Fallback theme configuration
    """
    
    def __init__(self):
        """Initialize the vault theme registry."""
        self.themes: Dict[str, Dict[str, Any]] = {}
        self.default_theme: Dict[str, Any] = {}
        self._loaded = False
    
    def load_themes(self, config_path: Optional[str] = None) -> None:
        """Load vault themes from YAML configuration file.
        
        Args:
            config_path: Optional path to vault_themes.yaml. If None, uses default location.
        """
        if self._loaded:
            return  # Already loaded
        
        if config_path is None:
            # Default path using resource path helper
            config_path = get_resource_path("config/vault_themes.yaml")
        
        try:
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f)
            
            # Load vault themes
            if 'vault_themes' in data:
                self.themes = data['vault_themes']
                logger.info(f"Loaded {len(self.themes)} vault themes from {config_path}")
            
            # Load default theme
            if 'default_vault' in data:
                self.default_theme = data['default_vault']
                logger.info(f"Loaded default vault theme")
            
            self._loaded = True
            
        except FileNotFoundError:
            logger.error(f"Vault themes file not found: {config_path}")
            self._load_fallback_themes()
        except yaml.YAMLError as e:
            logger.error(f"Error parsing vault themes YAML: {e}")
            self._load_fallback_themes()
        except Exception as e:
            logger.error(f"Unexpected error loading vault themes: {e}")
            self._load_fallback_themes()
    
    def _load_fallback_themes(self) -> None:
        """Load minimal fallback themes if YAML loading fails."""
        logger.warning("Loading fallback vault themes")
        
        self.default_theme = {
            'name': 'Treasure Room',
            'wall_color': [200, 150, 50],
            'monsters': {'orc': 100},
            'elite_scaling': {
                'hp_multiplier': 2.0,
                'power_bonus': 2,
                'defense_bonus': 1
            },
            'chest_count': {'min': 2, 'max': 3},
            'chest_quality': [
                {'quality': 'rare', 'weight': 70},
                {'quality': 'legendary', 'weight': 30}
            ],
            'bonus_items': {'min': 1, 'max': 2}
        }
        
        self.themes = {
            'default': self.default_theme
        }
        
        self._loaded = True
    
    def get_theme(self, theme_id: str) -> Optional[Dict[str, Any]]:
        """Get a vault theme configuration by ID.
        
        Args:
            theme_id: Theme identifier (e.g., 'treasure', 'armory', 'library')
            
        Returns:
            Theme configuration dictionary, or None if not found
        """
        if not self._loaded:
            self.load_themes()
        
        return self.themes.get(theme_id)
    
    def get_default_theme(self) -> Dict[str, Any]:
        """Get the default vault theme configuration.
        
        Returns:
            Default theme configuration dictionary
        """
        if not self._loaded:
            self.load_themes()
        
        return self.default_theme
    
    def get_available_themes(self, depth: int) -> List[str]:
        """Get list of theme IDs available at the given depth.
        
        Filters themes based on their spawn_chance configuration.
        
        Args:
            depth: Current dungeon depth
            
        Returns:
            List of theme IDs that can spawn at this depth
        """
        if not self._loaded:
            self.load_themes()
        
        available = []
        
        for theme_id, theme_config in self.themes.items():
            if self._can_spawn_at_depth(theme_config, depth):
                available.append(theme_id)
        
        return available
    
    def _can_spawn_at_depth(self, theme_config: Dict[str, Any], depth: int) -> bool:
        """Check if a theme can spawn at the given depth.
        
        Args:
            theme_config: Theme configuration dictionary
            depth: Current dungeon depth
            
        Returns:
            True if theme can spawn at this depth
        """
        if 'spawn_chance' not in theme_config:
            return True  # No restrictions
        
        spawn_config = theme_config['spawn_chance']
        
        # Check depth ranges
        if depth <= 6:
            chance = spawn_config.get('depth_1_6', 0.0)
        elif depth <= 9:
            chance = spawn_config.get('depth_7_9', 0.0)
        else:
            chance = spawn_config.get('depth_10_plus', 0.0)
        
        return chance > 0.0
    
    def get_spawn_chance(self, theme_id: str, depth: int) -> float:
        """Get the spawn chance for a theme at the given depth.
        
        Args:
            theme_id: Theme identifier
            depth: Current dungeon depth
            
        Returns:
            Spawn chance as a float (0.0-1.0), or 0.0 if theme not found
        """
        theme = self.get_theme(theme_id)
        if not theme or 'spawn_chance' not in theme:
            return 0.0
        
        spawn_config = theme['spawn_chance']
        
        # Determine which depth range we're in
        if depth <= 6:
            return spawn_config.get('depth_1_6', 0.0)
        elif depth <= 9:
            return spawn_config.get('depth_7_9', 0.0)
        else:
            return spawn_config.get('depth_10_plus', 0.0)
    
    def get_all_themes(self) -> Dict[str, Dict[str, Any]]:
        """Get all vault theme configurations.
        
        Returns:
            Dictionary mapping theme IDs to configurations
        """
        if not self._loaded:
            self.load_themes()
        
        return self.themes


# Singleton instance
_vault_theme_registry = None


def get_vault_theme_registry() -> VaultThemeRegistry:
    """Get the singleton vault theme registry instance.
    
    Returns:
        VaultThemeRegistry singleton instance
    """
    global _vault_theme_registry
    
    if _vault_theme_registry is None:
        _vault_theme_registry = VaultThemeRegistry()
        _vault_theme_registry.load_themes()
    
    return _vault_theme_registry

