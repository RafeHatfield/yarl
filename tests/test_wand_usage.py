"""Tests for wand usage and recharge mechanics."""

import pytest
from unittest.mock import Mock, MagicMock
from components.wand import Wand
from components.inventory import Inventory
from components.item import Item
from entity import Entity
from game_messages import Message


class TestWandUsage:
    """Test wand usage mechanics (consume charges, not items)."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a mock player with inventory
        self.player = Mock()
        self.player.name = "Player"
        
        # Create inventory
        self.inventory = Inventory(capacity=26)
        self.inventory.owner = self.player
        self.player.inventory = self.inventory
        
        # Create a wand with 3 charges
        self.wand_entity = Entity(0, 0, '/', (255, 200, 0), 'Wand of Fireball', blocks=False)
        self.wand_component = Wand(spell_type="fireball_scroll", charges=3)
        self.wand_entity.wand = self.wand_component
        self.wand_component.owner = self.wand_entity
        
        # Create a mock item component with use function
        self.mock_use_function = Mock(return_value=[{"consumed": True, "message": Message("Fireball!", (255, 0, 0))}])
        self.item_component = Item(use_function=self.mock_use_function)
        self.wand_entity.item = self.item_component
    
    def test_using_wand_consumes_charge_not_item(self):
        """Test that using a wand consumes a charge but doesn't remove the item."""
        # Add wand to inventory
        self.inventory.items.append(self.wand_entity)
        initial_charge = self.wand_component.charges
        
        # Use the wand
        results = self.inventory.use(self.wand_entity)
        
        # Wand should still be in inventory
        assert self.wand_entity in self.inventory.items
        # Charge should be consumed
        assert self.wand_component.charges == initial_charge - 1
        # Use function should have been called
        assert self.mock_use_function.called
    
    def test_using_wand_shows_remaining_charges(self):
        """Test that using a wand shows remaining charge count."""
        self.inventory.items.append(self.wand_entity)
        
        results = self.inventory.use(self.wand_entity)
        
        # Should have message about remaining charges
        messages = [r.get("message") for r in results if r.get("message")]
        charge_messages = [m for m in messages if "charges remaining" in str(m).lower()]
        assert len(charge_messages) > 0
    
    def test_using_empty_wand_shows_fizzle_message(self):
        """Test that using an empty wand shows a fizzle message."""
        # Create an empty wand
        empty_wand = Entity(0, 0, '/', (255, 200, 0), 'Wand of Fireball', blocks=False)
        empty_wand_component = Wand(spell_type="fireball_scroll", charges=0)
        empty_wand.wand = empty_wand_component
        empty_wand_component.owner = empty_wand
        empty_wand.item = self.item_component
        
        self.inventory.items.append(empty_wand)
        
        results = self.inventory.use(empty_wand)
        
        # Should have fizzle message
        messages = [r.get("message") for r in results if r.get("message")]
        fizzle_messages = [m for m in messages if "fizzles" in str(m).lower()]
        assert len(fizzle_messages) > 0
        
        # Use function should NOT have been called
        assert not self.mock_use_function.called
        
        # Wand should still be in inventory (not removed)
        assert empty_wand in self.inventory.items
    
    def test_wand_depletes_to_zero(self):
        """Test that a wand can be depleted to zero charges."""
        self.inventory.items.append(self.wand_entity)
        initial_charges = self.wand_component.charges
        
        # Use all charges
        for _ in range(initial_charges):
            results = self.inventory.use(self.wand_entity)
        
        # Wand should have 0 charges
        assert self.wand_component.charges == 0
        assert self.wand_component.is_empty()
        
        # Wand should still be in inventory
        assert self.wand_entity in self.inventory.items
        
        # Trying to use again should fizzle
        results = self.inventory.use(self.wand_entity)
        messages = [r.get("message") for r in results if r.get("message")]
        fizzle_messages = [m for m in messages if "fizzles" in str(m).lower()]
        assert len(fizzle_messages) > 0
    
    def test_scroll_usage_still_removes_item(self):
        """Test that using a scroll (non-wand) still removes it from inventory."""
        # Create a scroll (no wand component)
        scroll = Entity(0, 0, '~', (255, 0, 0), 'Fireball Scroll', blocks=False)
        scroll_use_function = Mock(return_value=[{"consumed": True}])
        scroll.item = Item(use_function=scroll_use_function)
        
        self.inventory.items.append(scroll)
        
        results = self.inventory.use(scroll)
        
        # Scroll should be removed from inventory
        assert scroll not in self.inventory.items


class TestWandRecharge:
    """Test scroll-to-wand recharge mechanics."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a mock player with inventory
        self.player = Mock()
        self.player.name = "Player"
        
        # Create inventory
        self.inventory = Inventory(capacity=26)
        self.inventory.owner = self.player
        self.player.inventory = self.inventory
        
        # Create a wand with 3 charges
        self.wand_entity = Entity(0, 0, '/', (255, 200, 0), 'Wand of Fireball', blocks=False)
        self.wand_component = Wand(spell_type="fireball_scroll", charges=3)
        self.wand_entity.wand = self.wand_component
        self.wand_component.owner = self.wand_entity
        
        # Add wand to inventory
        self.inventory.items.append(self.wand_entity)
    
    def test_picking_up_matching_scroll_recharges_wand(self):
        """Test that picking up a scroll recharges a matching wand."""
        # Create a matching scroll
        scroll = Entity(0, 0, '~', (255, 0, 0), 'Fireball Scroll', blocks=False)
        scroll.item = Item(use_function=Mock())
        
        initial_charges = self.wand_component.charges
        
        # Pick up the scroll
        results = self.inventory.add_item(scroll)
        
        # Wand should have gained a charge
        assert self.wand_component.charges == initial_charges + 1
        
        # Scroll should NOT be in inventory (it was consumed)
        assert scroll not in self.inventory.items
        
        # Should have a message about recharging
        messages = [r.get("message") for r in results if r.get("message")]
        recharge_messages = [m for m in messages if "gains a charge" in str(m).lower()]
        assert len(recharge_messages) > 0
    
    def test_picking_up_non_matching_scroll_doesnt_recharge(self):
        """Test that picking up a non-matching scroll doesn't recharge the wand."""
        # Create a different scroll
        scroll = Entity(0, 0, '~', (255, 255, 0), 'Lightning Scroll', blocks=False)
        scroll.item = Item(use_function=Mock())
        
        initial_charges = self.wand_component.charges
        
        # Pick up the scroll
        results = self.inventory.add_item(scroll)
        
        # Wand charges should be unchanged
        assert self.wand_component.charges == initial_charges
        
        # Scroll SHOULD be in inventory (not consumed)
        assert scroll in self.inventory.items
    
    def test_picking_up_scroll_without_wand_adds_normally(self):
        """Test that picking up a scroll when you don't have a wand adds it normally."""
        # Remove the wand
        self.inventory.items.remove(self.wand_entity)
        
        # Create a scroll
        scroll = Entity(0, 0, '~', (255, 0, 0), 'Fireball Scroll', blocks=False)
        scroll.item = Item(use_function=Mock())
        
        # Pick up the scroll
        results = self.inventory.add_item(scroll)
        
        # Scroll should be in inventory
        assert scroll in self.inventory.items
    
    def test_recharging_empty_wand(self):
        """Test that an empty wand can be recharged with a scroll."""
        # Deplete the wand
        self.wand_component.charges = 0
        assert self.wand_component.is_empty()
        
        # Create a matching scroll
        scroll = Entity(0, 0, '~', (255, 0, 0), 'Fireball Scroll', blocks=False)
        scroll.item = Item(use_function=Mock())
        
        # Pick up the scroll
        results = self.inventory.add_item(scroll)
        
        # Wand should have 1 charge now
        assert self.wand_component.charges == 1
        assert not self.wand_component.is_empty()
        
        # Scroll should be consumed
        assert scroll not in self.inventory.items
    
    def test_multiple_scrolls_recharge_same_wand(self):
        """Test that multiple scrolls can recharge the same wand."""
        initial_charges = self.wand_component.charges
        
        # Pick up 3 matching scrolls
        for i in range(3):
            scroll = Entity(0, 0, '~', (255, 0, 0), 'Fireball Scroll', blocks=False)
            scroll.item = Item(use_function=Mock())
            self.inventory.add_item(scroll)
        
        # Wand should have 3 more charges
        assert self.wand_component.charges == initial_charges + 3
    
    def test_wand_has_unlimited_max_charges(self):
        """Test that wands can be recharged beyond typical limits."""
        self.wand_component.charges = 100
        
        # Pick up a scroll
        scroll = Entity(0, 0, '~', (255, 0, 0), 'Fireball Scroll', blocks=False)
        scroll.item = Item(use_function=Mock())
        self.inventory.add_item(scroll)
        
        # Should still recharge (no max limit)
        assert self.wand_component.charges == 101
    
    def test_picking_up_wand_consumes_existing_scrolls(self):
        """Test that picking up a wand consumes matching scrolls already in inventory."""
        # Start with 3 fireball scrolls in inventory
        for i in range(3):
            scroll = Entity(0, 0, '~', (255, 0, 0), 'Fireball Scroll', blocks=False)
            scroll.item = Item(use_function=Mock())
            self.inventory.items.append(scroll)
        
        # Create a new wand (not in inventory yet)
        new_wand = Entity(0, 0, '/', (255, 200, 0), 'Wand of Fireball', blocks=False)
        new_wand_component = Wand(spell_type="fireball_scroll", charges=2)
        new_wand.wand = new_wand_component
        new_wand_component.owner = new_wand
        
        # Pick up the wand
        results = self.inventory.add_item(new_wand)
        
        # Wand should have consumed all 3 scrolls
        assert new_wand_component.charges == 5  # 2 starting + 3 from scrolls
        
        # Scrolls should be gone from inventory
        scrolls_in_inventory = [item for item in self.inventory.items if 'Scroll' in item.name]
        assert len(scrolls_in_inventory) == 0
        
        # Should have message about absorption
        messages = [r.get("message") for r in results if r.get("message")]
        absorption_messages = [m for m in messages if "absorbs" in str(m).lower()]
        assert len(absorption_messages) > 0
    
    def test_picking_up_wand_with_no_matching_scrolls(self):
        """Test that picking up a wand when no matching scrolls exist works normally."""
        # Start with a lightning scroll (doesn't match fireball wand)
        scroll = Entity(0, 0, '~', (255, 255, 0), 'Lightning Scroll', blocks=False)
        scroll.item = Item(use_function=Mock())
        self.inventory.items.append(scroll)
        
        # Create a fireball wand
        new_wand = Entity(0, 0, '/', (255, 200, 0), 'Wand of Fireball', blocks=False)
        new_wand_component = Wand(spell_type="fireball_scroll", charges=3)
        new_wand.wand = new_wand_component
        new_wand_component.owner = new_wand
        
        # Pick up the wand
        results = self.inventory.add_item(new_wand)
        
        # Wand should have starting charges only
        assert new_wand_component.charges == 3
        
        # Lightning scroll should still be there
        assert scroll in self.inventory.items
        
        # Should NOT have absorption message
        messages = [r.get("message") for r in results if r.get("message")]
        absorption_messages = [m for m in messages if "absorbs" in str(m).lower()]
        assert len(absorption_messages) == 0


class TestWandDisplayName:
    """Test that wand display names show charge counts in UI."""
    
    def test_entity_display_name_uses_wand_charges(self):
        """Test that Entity.get_display_name() shows wand charges."""
        wand = Entity(0, 0, '/', (255, 200, 0), 'Wand of Fireball', blocks=False)
        wand_component = Wand(spell_type="fireball_scroll", charges=7)
        wand.wand = wand_component
        wand_component.owner = wand
        
        display_name = wand.get_display_name()
        
        # Should include charge count
        assert "7" in display_name
        assert "Wand of Fireball" in display_name
    
    def test_display_name_updates_with_charges(self):
        """Test that display name reflects current charge count."""
        wand = Entity(0, 0, '/', (255, 200, 0), 'Wand of Fireball', blocks=False)
        wand_component = Wand(spell_type="fireball_scroll", charges=5)
        wand.wand = wand_component
        wand_component.owner = wand
        
        assert "5" in wand.get_display_name()
        
        # Use a charge
        wand_component.use_charge()
        assert "4" in wand.get_display_name()
        
        # Add charges
        wand_component.add_charge(10)
        assert "14" in wand.get_display_name()

