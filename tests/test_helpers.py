"""Test helper utilities for fixing mock component access patterns.

This module provides utilities to help fix tests affected by the transition
from components.get() to get_component_optional().
"""

from unittest.mock import Mock
from components.component_registry import ComponentType


def setup_component_optional_mock(entity_mock, component_map):
    """Helper to set up get_component_optional mock with a component map.
    
    Args:
        entity_mock: The mock entity to configure
        component_map: Dict mapping ComponentType to component instances (or None)
                      Example: {ComponentType.EQUIPMENT: mock_equipment}
    
    Usage:
        setup_component_optional_mock(monster, {
            ComponentType.EQUIPMENT: mock_equipment,
            ComponentType.INVENTORY: mock_inventory,
            ComponentType.BOSS: None,  # Not a boss
        })
    """
    def get_component(comp_type):
        return component_map.get(comp_type, None)
    
    entity_mock.components.get = Mock(side_effect=get_component)
    entity_mock.get_component_optional = Mock(side_effect=get_component)


def setup_non_boss_entity(entity_mock):
    """Configure entity mock to properly return None for boss component checks.
    
    This prevents "TypeError: unsupported operand type(s) for *: 'int' and 'Mock'"
    when fighter.attack() checks for boss damage multipliers.
    
    Args:
        entity_mock: The mock entity to configure
    """
    # Return None for ComponentType.BOSS checks
    if not hasattr(entity_mock, 'get_component_optional'):
        entity_mock.get_component_optional = Mock(return_value=None)
    else:
        # Update existing mock to handle BOSS specifically
        original_get = entity_mock.get_component_optional
        def safe_get(comp_type):
            if comp_type == ComponentType.BOSS:
                return None
            if callable(original_get):
                return original_get(comp_type)
            return original_get
        entity_mock.get_component_optional = Mock(side_effect=safe_get)


def make_iterable_inventory(inventory_mock, items=None):
    """Make an inventory mock have an iterable items list.
    
    Args:
        inventory_mock: The inventory mock to fix
        items: List of item entities (defaults to empty list)
    """
    if items is None:
        items = []
    inventory_mock.items = items

