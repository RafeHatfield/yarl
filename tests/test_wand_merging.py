"""Tests for wand-to-wand merging mechanics.

When picking up a wand of the same spell type as one you already have,
the charges should merge into the existing wand and the new wand should
be consumed (similar to scroll-to-wand recharge).
"""

import pytest
from unittest.mock import Mock, patch

from entity import Entity
from components.inventory import Inventory
from components.item import Item
from components.wand import Wand


class TestWandMerging:
    """Test that wands merge with other wands of the same type."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a mock player with inventory
        self.player = Mock()
        self.player.name = "Player"
        self.player.x = 10
        self.player.y = 10
        
        # Create inventory
        self.inventory = Inventory(capacity=26)
        self.inventory.owner = self.player
        self.player.inventory = self.inventory
        
        # Create a wand with 3 charges (already in inventory)
        self.existing_wand = Entity(0, 0, '/', (255, 200, 0), 'Wand of Fireball', blocks=False)
        self.existing_wand_component = Wand(spell_type="fireball_scroll", charges=3)
        self.existing_wand.wand = self.existing_wand_component
        self.existing_wand_component.owner = self.existing_wand
        
        # Add existing wand to inventory
        self.inventory.items.append(self.existing_wand)
    
    @patch('visual_effect_queue.get_effect_queue')
    def test_picking_up_matching_wand_merges_charges(self, mock_get_effect_queue):
        """Test that picking up a wand of the same type merges charges."""
        # Mock the effect queue
        mock_effect_queue = Mock()
        mock_get_effect_queue.return_value = mock_effect_queue
        
        # Create a new wand with 2 charges to pick up
        new_wand = Entity(0, 0, '/', (255, 200, 0), 'Wand of Fireball', blocks=False)
        new_wand_component = Wand(spell_type="fireball_scroll", charges=2)
        new_wand.wand = new_wand_component
        new_wand_component.owner = new_wand
        
        initial_charges = self.existing_wand_component.charges
        
        # Pick up the new wand
        results = self.inventory.add_item(new_wand)
        
        # Existing wand should have gained 2 charges (3 + 2 = 5)
        assert self.existing_wand_component.charges == initial_charges + 2
        assert self.existing_wand_component.charges == 5
        
        # New wand should NOT be in inventory (it was consumed)
        assert new_wand not in self.inventory.items
        
        # Should have a message about merging with correct pluralization
        messages = [r.get("message") for r in results if r.get("message")]
        merge_messages = [m for m in messages if "gains" in str(m).lower() and "charges" in str(m).lower()]
        assert len(merge_messages) > 0
        assert "2 charges" in str(merge_messages[0]).lower()
        
        # Should have visual effect
        mock_effect_queue.queue_wand_recharge.assert_called_once_with(10, 10, self.player)
        
        # Should have item_consumed flag
        consumed_results = [r for r in results if r.get("item_consumed")]
        assert len(consumed_results) == 1
        assert consumed_results[0]["item_consumed"] == new_wand
    
    @patch('visual_effect_queue.get_effect_queue')
    def test_picking_up_wand_with_one_charge_uses_singular(self, mock_get_effect_queue):
        """Test that the message uses 'charge' (singular) when merging 1 charge."""
        # Mock the effect queue
        mock_effect_queue = Mock()
        mock_get_effect_queue.return_value = mock_effect_queue
        
        # Create a new wand with 1 charge to pick up
        new_wand = Entity(0, 0, '/', (255, 200, 0), 'Wand of Fireball', blocks=False)
        new_wand_component = Wand(spell_type="fireball_scroll", charges=1)
        new_wand.wand = new_wand_component
        new_wand_component.owner = new_wand
        
        # Pick up the new wand
        results = self.inventory.add_item(new_wand)
        
        # Should have message with singular "charge"
        messages = [r.get("message") for r in results if r.get("message")]
        merge_messages = [m for m in messages if "gains" in str(m).lower()]
        assert len(merge_messages) > 0
        assert "1 charge" in str(merge_messages[0]).lower()
        assert "1 charges" not in str(merge_messages[0]).lower()  # Should NOT have plural
    
    @patch('visual_effect_queue.get_effect_queue')
    def test_picking_up_non_matching_wand_adds_normally(self, mock_get_effect_queue):
        """Test that picking up a different wand type adds it normally."""
        # Mock the effect queue
        mock_effect_queue = Mock()
        mock_get_effect_queue.return_value = mock_effect_queue
        
        # Create a different wand (lightning, not fireball)
        new_wand = Entity(0, 0, '/', (200, 200, 255), 'Wand of Lightning', blocks=False)
        new_wand_component = Wand(spell_type="lightning_scroll", charges=3)
        new_wand.wand = new_wand_component
        new_wand_component.owner = new_wand
        
        initial_charges = self.existing_wand_component.charges
        
        # Pick up the new wand
        results = self.inventory.add_item(new_wand)
        
        # Existing fireball wand charges should be unchanged
        assert self.existing_wand_component.charges == initial_charges
        
        # New lightning wand SHOULD be in inventory
        assert new_wand in self.inventory.items
        
        # Should have normal pickup message, not merge message
        messages = [r.get("message") for r in results if r.get("message")]
        pickup_messages = [m for m in messages if "pick up" in str(m).lower()]
        assert len(pickup_messages) > 0
    
    @patch('visual_effect_queue.get_effect_queue')
    def test_wand_merge_allows_unlimited_charges(self, mock_get_effect_queue):
        """Test that merged wands can accumulate unlimited charges."""
        # Mock the effect queue
        mock_effect_queue = Mock()
        mock_get_effect_queue.return_value = mock_effect_queue
        
        # Set existing wand to 9 charges
        self.existing_wand_component.charges = 9
        
        # Create a new wand with 5 charges to pick up
        new_wand = Entity(0, 0, '/', (255, 200, 0), 'Wand of Fireball', blocks=False)
        new_wand_component = Wand(spell_type="fireball_scroll", charges=5)
        new_wand.wand = new_wand_component
        new_wand_component.owner = new_wand
        
        # Pick up the new wand
        results = self.inventory.add_item(new_wand)
        
        # Existing wand should have all charges (9 + 5 = 14, no max limit)
        assert self.existing_wand_component.charges == 14
    
    @patch('visual_effect_queue.get_effect_queue')
    def test_merging_empty_wand_with_charged_wand(self, mock_get_effect_queue):
        """Test that an empty wand can be merged with a charged wand."""
        # Mock the effect queue
        mock_effect_queue = Mock()
        mock_get_effect_queue.return_value = mock_effect_queue
        
        # Create an empty wand to pick up
        empty_wand = Entity(0, 0, '/', (255, 200, 0), 'Wand of Fireball', blocks=False)
        empty_wand_component = Wand(spell_type="fireball_scroll", charges=0)
        empty_wand.wand = empty_wand_component
        empty_wand_component.owner = empty_wand
        
        initial_charges = self.existing_wand_component.charges
        
        # Pick up the empty wand
        results = self.inventory.add_item(empty_wand)
        
        # Existing wand should have same charges (gained 0)
        assert self.existing_wand_component.charges == initial_charges
        
        # Empty wand should NOT be in inventory (it was consumed)
        assert empty_wand not in self.inventory.items
        
        # Should still have merge message (even though 0 charges gained)
        messages = [r.get("message") for r in results if r.get("message")]
        merge_messages = [m for m in messages if "gains" in str(m).lower()]
        assert len(merge_messages) > 0
        assert "0 charges" in str(merge_messages[0]).lower()
    
    @patch('visual_effect_queue.get_effect_queue')
    def test_picking_up_first_wand_no_merge(self, mock_get_effect_queue):
        """Test that picking up the first wand of a type doesn't trigger merge."""
        # Mock the effect queue
        mock_effect_queue = Mock()
        mock_get_effect_queue.return_value = mock_effect_queue
        
        # Remove the existing wand
        self.inventory.items.remove(self.existing_wand)
        
        # Create a new wand to pick up
        new_wand = Entity(0, 0, '/', (255, 200, 0), 'Wand of Fireball', blocks=False)
        new_wand_component = Wand(spell_type="fireball_scroll", charges=3)
        new_wand.wand = new_wand_component
        new_wand_component.owner = new_wand
        
        # Pick up the wand
        results = self.inventory.add_item(new_wand)
        
        # Wand should be in inventory
        assert new_wand in self.inventory.items
        
        # Should have normal pickup message, not merge message
        messages = [r.get("message") for r in results if r.get("message")]
        pickup_messages = [m for m in messages if "pick up" in str(m).lower()]
        assert len(pickup_messages) > 0
        
        # Should NOT have merge message
        merge_messages = [m for m in messages if "vanishes" in str(m).lower()]
        assert len(merge_messages) == 0
    
    @patch('visual_effect_queue.get_effect_queue')
    def test_wand_merge_takes_priority_over_scroll_consumption(self, mock_get_effect_queue):
        """Test that wand merging happens before the wand tries to consume scrolls."""
        # Mock the effect queue
        mock_effect_queue = Mock()
        mock_get_effect_queue.return_value = mock_effect_queue
        
        # Add a fireball scroll to inventory
        scroll = Entity(0, 0, '~', (255, 0, 0), 'Fireball Scroll', blocks=False)
        scroll.item = Item(use_function=Mock())
        self.inventory.items.append(scroll)
        
        # Create a new wand with 2 charges to pick up
        new_wand = Entity(0, 0, '/', (255, 200, 0), 'Wand of Fireball', blocks=False)
        new_wand_component = Wand(spell_type="fireball_scroll", charges=2)
        new_wand.wand = new_wand_component
        new_wand_component.owner = new_wand
        
        initial_charges = self.existing_wand_component.charges
        
        # Pick up the new wand
        results = self.inventory.add_item(new_wand)
        
        # Existing wand should have gained charges from merge (not from scroll)
        assert self.existing_wand_component.charges == initial_charges + 2
        
        # New wand should NOT be in inventory (merged)
        assert new_wand not in self.inventory.items
        
        # Scroll should still be there (not consumed by the merge process)
        assert scroll in self.inventory.items
        
        # Should have merge message
        messages = [r.get("message") for r in results if r.get("message")]
        merge_messages = [m for m in messages if "vanishes" in str(m).lower()]
        assert len(merge_messages) > 0


class TestWandMergingWithMultipleWands:
    """Test edge cases with multiple wands."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a mock player with inventory
        self.player = Mock()
        self.player.name = "Player"
        self.player.x = 10
        self.player.y = 10
        
        # Create inventory
        self.inventory = Inventory(capacity=26)
        self.inventory.owner = self.player
        self.player.inventory = self.inventory
    
    @patch('visual_effect_queue.get_effect_queue')
    def test_wand_merges_with_first_matching_wand_only(self, mock_get_effect_queue):
        """Test that a wand only merges with the first matching wand found."""
        # Mock the effect queue
        mock_effect_queue = Mock()
        mock_get_effect_queue.return_value = mock_effect_queue
        
        # Add two fireball wands to inventory (edge case - shouldn't happen normally, but test it)
        wand1 = Entity(0, 0, '/', (255, 200, 0), 'Wand of Fireball', blocks=False)
        wand1_component = Wand(spell_type="fireball_scroll", charges=3)
        wand1.wand = wand1_component
        wand1_component.owner = wand1
        self.inventory.items.append(wand1)
        
        wand2 = Entity(0, 0, '/', (255, 200, 0), 'Wand of Fireball', blocks=False)
        wand2_component = Wand(spell_type="fireball_scroll", charges=4)
        wand2.wand = wand2_component
        wand2_component.owner = wand2
        self.inventory.items.append(wand2)
        
        # Create a new wand with 2 charges to pick up
        new_wand = Entity(0, 0, '/', (255, 200, 0), 'Wand of Fireball', blocks=False)
        new_wand_component = Wand(spell_type="fireball_scroll", charges=2)
        new_wand.wand = new_wand_component
        new_wand_component.owner = new_wand
        
        # Pick up the new wand
        results = self.inventory.add_item(new_wand)
        
        # First wand should have gained charges
        assert wand1_component.charges == 5  # 3 + 2
        
        # Second wand should be unchanged
        assert wand2_component.charges == 4
        
        # New wand should NOT be in inventory
        assert new_wand not in self.inventory.items


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
