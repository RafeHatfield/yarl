"""Spell Registry - Central manager for all spells.

This module provides the SpellRegistry class that stores and retrieves
spell definitions and coordinates spell casting.
"""

from typing import Dict, Optional, List
from spells.spell_definition import SpellDefinition
from game_messages import Message


class SpellRegistry:
    """Central registry for all spells.
    
    The SpellRegistry stores all spell definitions and provides methods
    to register, retrieve, and list spells. It acts as a single source
    of truth for all spell data in the game.
    
    Example:
        >>> registry = SpellRegistry()
        >>> registry.register(fireball_spell)
        >>> spell = registry.get("fireball")
        >>> spell.damage  # "3d6"
    """
    
    def __init__(self):
        """Initialize empty spell registry."""
        self._spells: Dict[str, SpellDefinition] = {}
    
    def register(self, spell: SpellDefinition) -> None:
        """Register a spell in the registry.
        
        Args:
            spell: SpellDefinition to register
            
        Raises:
            ValueError: If spell_id already exists
        """
        if spell.spell_id in self._spells:
            # Already registered, skip silently for idempotency
            return
        
        self._spells[spell.spell_id] = spell
    
    def get(self, spell_id: str) -> Optional[SpellDefinition]:
        """Get a spell definition by ID.
        
        Args:
            spell_id: Unique spell identifier
            
        Returns:
            SpellDefinition if found, None otherwise
        """
        return self._spells.get(spell_id)
    
    def has(self, spell_id: str) -> bool:
        """Check if a spell is registered.
        
        Args:
            spell_id: Unique spell identifier
            
        Returns:
            True if spell exists, False otherwise
        """
        return spell_id in self._spells
    
    def list_all(self) -> List[SpellDefinition]:
        """Get all registered spells.
        
        Returns:
            List of all SpellDefinitions
        """
        return list(self._spells.values())
    
    def list_by_category(self, category) -> List[SpellDefinition]:
        """Get all spells in a category.
        
        Args:
            category: SpellCategory to filter by
            
        Returns:
            List of SpellDefinitions in that category
        """
        return [spell for spell in self._spells.values() if spell.category == category]
    
    def clear(self) -> None:
        """Clear all registered spells. Useful for testing."""
        self._spells.clear()
    
    def __len__(self) -> int:
        """Return number of registered spells."""
        return len(self._spells)
    
    def __contains__(self, spell_id: str) -> bool:
        """Check if spell_id is in registry using 'in' operator."""
        return spell_id in self._spells
    
    def __repr__(self) -> str:
        """String representation of registry."""
        return f"<SpellRegistry: {len(self._spells)} spells registered>"


# Global spell registry instance
_global_registry: Optional[SpellRegistry] = None


def get_spell_registry() -> SpellRegistry:
    """Get the global spell registry instance.
    
    Returns:
        The singleton SpellRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = SpellRegistry()
    return _global_registry


def register_spell(spell: SpellDefinition) -> None:
    """Convenience function to register a spell in the global registry.
    
    Args:
        spell: SpellDefinition to register
    """
    get_spell_registry().register(spell)


def get_spell(spell_id: str) -> Optional[SpellDefinition]:
    """Convenience function to get a spell from the global registry.
    
    Args:
        spell_id: Unique spell identifier
        
    Returns:
        SpellDefinition if found, None otherwise
    """
    return get_spell_registry().get(spell_id)

