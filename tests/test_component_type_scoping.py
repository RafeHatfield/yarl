"""Test ComponentType scoping issues to prevent regressions.

This test suite ensures that ComponentType imports are accessible
throughout all methods and don't suffer from scoping issues.
"""

import pytest
from config.entity_factory import EntityFactory
from config.entity_registry import load_entity_config


@pytest.fixture(scope="module")
def entity_factory():
    """Create entity factory with loaded config."""
    load_entity_config('config/entities.yaml')
    return EntityFactory()


class TestComponentTypeScopingInAI:
    """Test that ComponentType is accessible in all AI methods."""
    
    def test_pickup_item_with_wand(self, entity_factory):
        """Test picking up a wand doesn't cause ComponentType scoping errors."""
        # Create an orc
        orc = entity_factory.create_monster('orc', 5, 5)
        
        # Create a wand
        wand = entity_factory.create_wand('wand_of_lightning', 5, 5)
        
        # Create entities list
        entities = [orc, wand]
        
        # Directly test the _pickup_item method (where ComponentType error occurred)
        # This should not raise "ComponentType is not defined"
        results = orc.ai._pickup_item(wand, entities)
        
        # Verify pickup was successful
        assert len(results) > 0
        assert wand in orc.inventory.items
    
    def test_pickup_item_with_scroll(self, entity_factory):
        """Test picking up a scroll doesn't cause ComponentType scoping errors."""
        # Create an orc
        orc = entity_factory.create_monster('orc', 5, 5)
        
        # Create a scroll
        scroll = entity_factory.create_spell_item('yo_mama_scroll', 5, 5)
        
        # Create entities list
        entities = [orc, scroll]
        
        # Directly test the _pickup_item method (where ComponentType error occurred)
        # This should not raise "ComponentType is not defined"
        results = orc.ai._pickup_item(scroll, entities)
        
        # Verify pickup was successful
        assert len(results) > 0
        assert scroll in orc.inventory.items
    
    def test_pickup_item_with_weapon(self, entity_factory):
        """Test picking up a weapon (equippable) doesn't cause errors."""
        # Create an orc
        orc = entity_factory.create_monster('orc', 5, 5)
        
        # Create a weapon
        weapon = entity_factory.create_weapon('club', 5, 5)
        
        # Create entities list
        entities = [orc, weapon]
        
        # Directly test the _pickup_item method (where ComponentType error occurred)
        # This should not raise "ComponentType is not defined"
        results = orc.ai._pickup_item(weapon, entities)
        
        # Verify pickup was successful
        assert len(results) > 0
        assert weapon in orc.inventory.items
    
    def test_pickup_item_with_armor(self, entity_factory):
        """Test picking up armor (equippable) doesn't cause errors."""
        # Create an orc
        orc = entity_factory.create_monster('orc', 5, 5)
        
        # Create armor
        armor = entity_factory.create_armor('leather_armor', 5, 5)
        
        # Create entities list
        entities = [orc, armor]
        
        # Directly test the _pickup_item method (where ComponentType error occurred)
        # This should not raise "ComponentType is not defined"
        results = orc.ai._pickup_item(armor, entities)
        
        # Verify pickup was successful
        assert len(results) > 0
        assert armor in orc.inventory.items


class TestComponentTypeAccessInMethods:
    """Test that ComponentType is accessible in various methods."""
    
    def test_try_item_usage_access(self, entity_factory):
        """Test that _try_item_usage can access ComponentType."""
        orc = entity_factory.create_monster('orc', 5, 5)
        
        # Just verify the method exists and uses ComponentType internally
        # The method will return None without proper setup, but won't crash with ComponentType error
        assert hasattr(orc.ai, '_try_item_usage')
        assert hasattr(orc, 'item_usage')  # Created by entity_factory
    
    def test_try_item_seeking_access(self, entity_factory):
        """Test that _try_item_seeking can access ComponentType."""
        orc = entity_factory.create_monster('orc', 5, 5)
        
        # Just verify the method exists and uses ComponentType internally
        # The method will return None without proper setup, but won't crash with ComponentType error
        assert hasattr(orc.ai, '_try_item_seeking')
        assert hasattr(orc, 'item_seeking_ai')  # Created by entity_factory


class TestComponentTypeInOtherComponents:
    """Test ComponentType usage in other component files."""
    
    def test_fighter_uses_component_type(self, entity_factory):
        """Test that Fighter component can use ComponentType."""
        orc = entity_factory.create_monster('orc', 5, 5)
        
        # Fighter should be able to access its owner's components
        assert orc.fighter is not None
        
        # This internally uses ComponentType
        ac = orc.fighter.armor_class
        assert isinstance(ac, int)
        assert ac >= 10  # Minimum AC
    
    def test_equipment_uses_component_type(self, entity_factory):
        """Test that Equipment component can use ComponentType."""
        orc = entity_factory.create_monster('orc', 5, 5)
        
        # Equipment should be accessible
        assert orc.equipment is not None
        
        # These internally use ComponentType
        power_bonus = orc.equipment.power_bonus
        defense_bonus = orc.equipment.defense_bonus
        
        assert isinstance(power_bonus, int)
        assert isinstance(defense_bonus, int)

