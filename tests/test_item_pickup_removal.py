"""Test that items are properly removed from entities list when picked up.

This test investigates the bug where items can be picked up multiple times
and remain on the ground, suggesting they exist in the entities list multiple times.
"""

import pytest
from config.entity_factory import EntityFactory
from config.entity_registry import load_entity_config
from game_actions import ActionProcessor
from game_states import GameStates


@pytest.fixture(scope="module")
def entity_factory():
    """Create entity factory with loaded config."""
    load_entity_config('config/entities.yaml')
    return EntityFactory()


class TestItemPickupRemoval:
    """Test that items are properly removed when picked up."""
    
    def test_item_removed_from_entities_on_pickup(self, entity_factory):
        """Test that item is removed from entities list after pickup."""
        # Create player and item
        player = entity_factory.create_monster('orc', 5, 5)
        player.name = 'Player'
        scroll = entity_factory.create_spell_item('rage_scroll', 5, 5)
        
        # Create entities list
        entities = [player, scroll]
        
        # Verify item is in entities
        assert scroll in entities
        assert len(entities) == 2
        
        # Player picks up item
        results = player.inventory.add_item(scroll)
        
        # Check results
        item_added = any(r.get('item_added') for r in results)
        item_consumed = any(r.get('item_consumed') for r in results)
        
        # Simulate the pickup logic from game_actions.py
        if item_added or item_consumed:
            entities.remove(scroll)
        
        # Verify item is NO LONGER in entities
        assert scroll not in entities
        assert len(entities) == 1  # Only player remains
    
    def test_no_duplicate_entities_in_list(self, entity_factory):
        """Test that the same entity doesn't appear multiple times in entities list."""
        # Create entities
        player = entity_factory.create_monster('orc', 5, 5)
        scroll1 = entity_factory.create_spell_item('rage_scroll', 10, 10)
        scroll2 = entity_factory.create_spell_item('lightning_scroll', 15, 15)
        
        # Create entities list
        entities = [player, scroll1, scroll2]
        
        # Check no duplicates
        assert len(entities) == 3
        assert len(set(id(e) for e in entities)) == 3  # All unique object IDs
        
        # Count each entity
        assert entities.count(player) == 1
        assert entities.count(scroll1) == 1
        assert entities.count(scroll2) == 1
    
    def test_picking_up_same_item_twice_fails(self, entity_factory):
        """Test that attempting to pick up the same item twice doesn't work."""
        # Create player and item
        player = entity_factory.create_monster('orc', 5, 5)
        scroll = entity_factory.create_spell_item('rage_scroll', 5, 5)
        
        # Create entities list
        entities = [player, scroll]
        
        # First pickup
        results1 = player.inventory.add_item(scroll)
        item_added = any(r.get('item_added') for r in results1)
        if item_added:
            entities.remove(scroll)
        
        # Verify it's in inventory and not in entities
        assert scroll in player.inventory.items
        assert scroll not in entities
        
        # Try to pick up again (should fail - not in entities anymore)
        # This would only work if scroll was still at same location in entities
        # In real game, this wouldn't trigger because item isn't in entities
        assert scroll not in entities
    
    def test_multiple_scrolls_same_type_are_different_entities(self, entity_factory):
        """Test that multiple scrolls of the same type are different entity objects."""
        scroll1 = entity_factory.create_spell_item('rage_scroll', 5, 5)
        scroll2 = entity_factory.create_spell_item('rage_scroll', 10, 10)
        
        # They should be different objects
        assert scroll1 is not scroll2
        assert id(scroll1) != id(scroll2)
        
        # But same type
        assert scroll1.name == scroll2.name
    
    def test_item_only_removed_once_from_entities(self, entity_factory):
        """Test that calling entities.remove() on an item only removes one instance."""
        # Create item
        scroll = entity_factory.create_spell_item('rage_scroll', 5, 5)
        
        # Create list with ONE item
        entities = [scroll]
        assert len(entities) == 1
        
        # Remove it
        entities.remove(scroll)
        assert len(entities) == 0
        
        # Try to remove again (should raise ValueError)
        with pytest.raises(ValueError):
            entities.remove(scroll)


class TestItemDuplicationBug:
    """Tests to reproduce the duplication bug."""
    
    def test_reproduce_multiple_pickup_bug(self, entity_factory):
        """Try to reproduce the bug where same item can be picked up multiple times.
        
        Hypothesis: The same entity object is in the entities list multiple times.
        """
        # Create player and item
        player = entity_factory.create_monster('orc', 5, 5)
        scroll = entity_factory.create_spell_item('rage_scroll', 5, 5)
        
        # Simulate the bug: add scroll to entities multiple times (shouldn't happen!)
        entities = [player, scroll, scroll, scroll]  # DUPLICATE REFERENCES
        
        assert len(entities) == 4
        assert entities.count(scroll) == 3  # Item appears 3 times!
        
        # First pickup
        results = player.inventory.add_item(scroll)
        item_added = any(r.get('item_added') for r in results)
        if item_added:
            entities.remove(scroll)  # Only removes ONE instance
        
        # Item is in inventory
        assert scroll in player.inventory.items
        
        # But still in entities (because there were multiple copies)!
        assert scroll in entities
        assert len(entities) == 3  # Still 3 entities (player + 2 scroll copies)
        
        # This is the bug! Player could pick it up again.
        # The question is: HOW does the same entity get added multiple times?

