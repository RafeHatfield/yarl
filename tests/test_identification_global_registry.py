"""Test global identification registry.

Critical regression test: Identification must work at the TYPE level, not instance level.
When you identify one healing potion, ALL healing potions become identified.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from components.item import Item
from config.identification_manager import IdentificationManager, reset_identification_manager
from config.entity_factory import EntityFactory
from config.game_constants import GameConstants


class TestIdentificationManager:
    """Test the IdentificationManager class."""
    
    def test_new_manager_starts_empty(self):
        """New manager should have no identified types."""
        manager = IdentificationManager()
        assert not manager.is_identified("healing_potion")
        assert not manager.is_identified("fireball_scroll")
        assert len(manager.get_identified_types()) == 0
    
    def test_identify_type_once(self):
        """Identifying a type for the first time should return True."""
        manager = IdentificationManager()
        
        was_new = manager.identify_type("healing_potion")
        
        assert was_new is True
        assert manager.is_identified("healing_potion")
        assert "healing_potion" in manager.get_identified_types()
    
    def test_identify_type_twice(self):
        """Identifying the same type twice should return False the second time."""
        manager = IdentificationManager()
        
        first = manager.identify_type("healing_potion")
        second = manager.identify_type("healing_potion")
        
        assert first is True
        assert second is False
        assert manager.is_identified("healing_potion")
    
    def test_multiple_types_tracked_independently(self):
        """Different item types are tracked independently."""
        manager = IdentificationManager()
        
        manager.identify_type("healing_potion")
        manager.identify_type("fireball_scroll")
        
        assert manager.is_identified("healing_potion")
        assert manager.is_identified("fireball_scroll")
        assert not manager.is_identified("speed_potion")
        
        types = manager.get_identified_types()
        assert len(types) == 2
        assert "healing_potion" in types
        assert "fireball_scroll" in types
    
    def test_reset_clears_all_types(self):
        """Reset should clear all identified types."""
        manager = IdentificationManager()
        manager.identify_type("healing_potion")
        manager.identify_type("fireball_scroll")
        
        manager.reset()
        
        assert not manager.is_identified("healing_potion")
        assert not manager.is_identified("fireball_scroll")
        assert len(manager.get_identified_types()) == 0
    
    def test_to_dict_serialization(self):
        """Manager should serialize to dict for saving."""
        manager = IdentificationManager()
        manager.identify_type("healing_potion")
        manager.identify_type("fireball_scroll")
        
        data = manager.to_dict()
        
        assert "identified_types" in data
        assert set(data["identified_types"]) == {"healing_potion", "fireball_scroll"}
    
    def test_from_dict_deserialization(self):
        """Manager should load from dict when loading save."""
        manager = IdentificationManager()
        data = {
            "identified_types": ["healing_potion", "speed_potion", "confusion_scroll"]
        }
        
        manager.from_dict(data)
        
        assert manager.is_identified("healing_potion")
        assert manager.is_identified("speed_potion")
        assert manager.is_identified("confusion_scroll")
        assert not manager.is_identified("fireball_scroll")


class TestItemIdentifyRegistersType:
    """Test that Item.identify() registers the type globally."""
    
    def test_identify_registers_type_globally(self):
        """When an item is identified, its type is registered globally."""
        manager = reset_identification_manager()  # Fresh manager
        
        # Create unidentified item
        entity = Mock()
        entity.name = "healing_potion"
        
        item = Item(identified=False, appearance="cyan potion")
        item.owner = entity
        
        # Initially not identified globally
        assert not manager.is_identified("healing_potion")
        
        # Identify the item
        item.identify()
        
        # Should now be identified globally
        assert manager.is_identified("healing_potion")
    
    def test_identify_uses_owner_name(self):
        """Identification should use the owner's name to determine type."""
        manager = reset_identification_manager()
        
        # Create item with owner having display name (spaces)
        entity = Mock()
        entity.name = "Healing Potion"  # Display name with spaces
        
        item = Item(identified=False, appearance="cyan potion")
        item.owner = entity
        
        item.identify()
        
        # Should convert to internal name (lowercase, underscores)
        assert manager.is_identified("healing_potion")
    
    def test_identify_without_owner_doesnt_crash(self):
        """Identifying an item without an owner shouldn't crash."""
        reset_identification_manager()
        
        item = Item(identified=False, appearance="cyan potion")
        item.owner = None
        
        # Should not crash
        was_unidentified = item.identify()
        
        assert was_unidentified is True
        assert item.identified is True


class TestEntityFactoryUsesGlobalRegistry:
    """Test that EntityFactory checks global registry when creating items."""
    
    def test_globally_identified_type_creates_identified_item(self):
        """If a type is globally identified, new items of that type start identified."""
        manager = reset_identification_manager()
        manager.identify_type("healing_potion")  # Mark as globally identified
        
        # Create factory with mock constants
        constants = GameConstants.load_from_file("config/game_constants.yaml")
        factory = EntityFactory(difficulty_level="medium", game_constants=constants)
        
        # Create a healing potion
        with patch('config.identification_manager.get_identification_manager', return_value=manager):
            potion = factory.create_spell_item("healing_potion", 0, 0)
        
        # Should start identified (because type is globally identified)
        assert potion.item.identified is True
        assert potion.item.appearance is None
    
    def test_unidentified_type_may_create_unidentified_item(self):
        """If a type is NOT globally identified, items may start unidentified (based on difficulty)."""
        manager = reset_identification_manager()
        # Don't identify healing_potion globally
        
        constants = GameConstants.load_from_file("config/game_constants.yaml")
        factory = EntityFactory(difficulty_level="hard", game_constants=constants)  # Hard = low pre-ID%
        
        # Create multiple potions and check if at least one is unidentified
        unidentified_found = False
        with patch('config.identification_manager.get_identification_manager', return_value=manager):
            for _ in range(20):  # Create multiple to account for randomness
                potion = factory.create_spell_item("speed_potion", 0, 0)
                if not potion.item.identified:
                    unidentified_found = True
                    break
        
        # At hard difficulty with no global ID, we should find unidentified items
        # (This test may occasionally fail due to randomness, but is unlikely with 20 attempts)
        assert unidentified_found, "Expected at least one unidentified potion at hard difficulty"


class TestGlobalIdentificationScenario:
    """Test the full scenario: identify one, all become identified."""
    
    def test_identify_one_healing_potion_identifies_all(self):
        """
        USER SCENARIO: Identify one healing potion, pick up another, it's already identified.
        
        This is the core bug that was reported:
        - Pick up unidentified "cyan potion"
        - Drink it, discover it's a healing potion
        - Pick up another item, which happens to also be a healing potion
        - That new item should ALSO be identified (same type)
        """
        manager = reset_identification_manager()
        constants = GameConstants.load_from_file("config/game_constants.yaml")
        factory = EntityFactory(difficulty_level="hard", game_constants=constants)
        
        # Patch the factory to use our manager
        with patch('config.identification_manager.get_identification_manager', return_value=manager):
            # Step 1: Find first healing potion (unidentified)
            potion1 = factory.create_spell_item("healing_potion", 0, 0)
            
            # Force it to be unidentified (might be pre-ID'd by chance)
            potion1.item.identified = False
            potion1.item.appearance = "cyan potion"
            
            # Verify it starts unidentified
            assert not potion1.item.identified
            assert potion1.item.appearance == "cyan potion"
            
            # Step 2: Drink it (identifies it)
            potion1.item.identify()
            
            # Verify the item is now identified
            assert potion1.item.identified
            
            # Verify the TYPE is globally identified
            assert manager.is_identified("healing_potion")
            
            # Step 3: Pick up another healing potion
            potion2 = factory.create_spell_item("healing_potion", 5, 5)
            
            # Step 4: NEW POTION SHOULD BE AUTOMATICALLY IDENTIFIED!
            assert potion2.item.identified is True, \
                "Second healing potion should be identified because type is now globally identified"
            assert potion2.item.appearance is None, \
                "Identified items should not have an appearance string"
    
    def test_different_types_remain_independent(self):
        """Identifying healing_potion doesn't identify speed_potion."""
        manager = reset_identification_manager()
        constants = GameConstants.load_from_file("config/game_constants.yaml")
        factory = EntityFactory(difficulty_level="hard", game_constants=constants)
        
        with patch('config.identification_manager.get_identification_manager', return_value=manager):
            # Identify healing potion
            healing = factory.create_spell_item("healing_potion", 0, 0)
            healing.item.identified = False  # Force unidentified
            healing.item.identify()
            
            assert manager.is_identified("healing_potion")
            
            # Speed potion should still be unidentified
            speed = factory.create_spell_item("speed_potion", 0, 0)
            
            # Might be pre-ID'd by difficulty, but type should not be globally identified yet
            if not speed.item.identified:
                # If it spawned unidentified, the type shouldn't be globally known
                assert not manager.is_identified("speed_potion")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

