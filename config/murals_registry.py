"""Murals & Inscriptions Registry - Manages mural descriptions from YAML configuration.

This module loads and provides access to mural scenes from the configuration file.
Murals can be filtered by dungeon depth for contextual storytelling about the ritual
and the dragons' tragedy.
"""

import os
import logging
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class MuralScene:
    """Represents a mural or inscription with optional depth constraints."""
    mural_id: str
    mural_type: str  # 'mural' or 'inscription'
    text: str
    min_depth: Optional[int] = None
    max_depth: Optional[int] = None
    
    def is_valid_for_depth(self, depth: int) -> bool:
        """Check if this mural is valid for the given dungeon depth.
        
        Args:
            depth: Current dungeon level
            
        Returns:
            True if mural can appear at this depth
        """
        if self.min_depth is not None and depth < self.min_depth:
            return False
        if self.max_depth is not None and depth > self.max_depth:
            return False
        return True


class MuralsRegistry:
    """Registry for managing murals and inscriptions from YAML configuration."""
    
    def __init__(self):
        """Initialize the registry."""
        self.murals: List[MuralScene] = []
        self.version: Optional[str] = None
        self._loaded = False
    
    def load_from_file(self, config_path: Optional[str] = None) -> None:
        """Load murals from YAML configuration file.
        
        Args:
            config_path: Path to murals_inscriptions.yaml. If None, uses default location.
        """
        if not YAML_AVAILABLE:
            logger.warning("YAML support not available. Using fallback murals.")
            self._load_fallback_murals()
            return
        
        if config_path is None:
            config_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(config_dir, 'murals_inscriptions.yaml')
        
        if not os.path.exists(config_path):
            logger.warning(f"Murals file not found at {config_path}. Using fallback murals.")
            self._load_fallback_murals()
            return
        
        try:
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f)
            
            if not data:
                logger.warning("Empty murals file. Using fallback murals.")
                self._load_fallback_murals()
                return
            
            self.version = data.get('version', 'unknown')
            
            # Load murals
            murals_data = data.get('murals', [])
            for mural_data in murals_data:
                if isinstance(mural_data, dict):
                    mural = MuralScene(
                        mural_id=mural_data.get('id', ''),
                        mural_type=mural_data.get('type', 'mural'),
                        text=mural_data.get('text', ''),
                        min_depth=mural_data.get('min_depth'),
                        max_depth=mural_data.get('max_depth')
                    )
                    self.murals.append(mural)
            
            self._loaded = True
            logger.info(
                f"Loaded murals (version {self.version}): "
                f"total={len(self.murals)}"
            )
            
        except Exception as e:
            logger.error(f"Error loading murals from {config_path}: {e}")
            self._load_fallback_murals()
    
    def _load_fallback_murals(self) -> None:
        """Load hardcoded fallback murals if YAML loading fails."""
        self.murals = [
            MuralScene(
                mural_id="fallback_1",
                mural_type="mural",
                text="A faded mural depicts ancient rituals and preparation.",
                min_depth=1,
                max_depth=10
            ),
            MuralScene(
                mural_id="fallback_2",
                mural_type="mural",
                text="Two dragons depicted together, flying across ancient skies.",
                min_depth=11,
                max_depth=20
            ),
            MuralScene(
                mural_id="fallback_3",
                mural_type="inscription",
                text="Carved into stone: 'The dragon's power lies in the Ruby Heart.'",
                min_depth=15,
                max_depth=25
            ),
        ]
        self._loaded = True
        logger.info("Loaded fallback murals")
    
    def get_random_mural(self, depth: int = 1) -> Tuple[Optional[str], Optional[str]]:
        """Get a random mural for the specified depth.
        
        Args:
            depth: Current dungeon level (for depth-specific murals)
            
        Returns:
            Tuple of (mural_text, mural_id) or (None, None) if no mural found
        """
        if not self._loaded:
            self.load_from_file()
        
        # Filter murals by depth
        valid_murals = [
            mural for mural in self.murals 
            if mural.is_valid_for_depth(depth)
        ]
        
        # If no murals valid for this depth, return None
        if not valid_murals:
            return (None, None)
        
        selected_mural = random.choice(valid_murals)
        return (selected_mural.text, selected_mural.mural_id)
    
    def get_all_murals_for_depth(self, depth: int) -> List[Tuple[str, str]]:
        """Get all murals available at a specific depth.
        
        Args:
            depth: Dungeon depth to filter by
            
        Returns:
            List of (mural_text, mural_id) tuples
        """
        if not self._loaded:
            self.load_from_file()
        
        valid_murals = [
            (mural.text, mural.mural_id)
            for mural in self.murals 
            if mural.is_valid_for_depth(depth)
        ]
        return valid_murals
    
    def get_mural_by_id(self, mural_id: str) -> Optional[Tuple[str, str]]:
        """Get a specific mural by ID.
        
        Args:
            mural_id: The ID of the mural to retrieve
            
        Returns:
            Tuple of (mural_text, mural_id) or None if not found
        """
        if not self._loaded:
            self.load_from_file()
        
        for mural in self.murals:
            if mural.mural_id == mural_id:
                return (mural.text, mural.mural_id)
        
        return None


# Global registry instance
_murals_registry = None


def get_murals_registry() -> MuralsRegistry:
    """Get the global murals registry instance.
    
    Returns:
        MuralsRegistry singleton instance
    """
    global _murals_registry
    if _murals_registry is None:
        _murals_registry = MuralsRegistry()
        _murals_registry.load_from_file()
    return _murals_registry

