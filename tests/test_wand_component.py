"""Tests for the Wand component."""

import pytest
from components.wand import Wand
from entity import Entity


class TestWandInitialization:
    """Test Wand component initialization."""
    
    def test_wand_basic_initialization(self):
        """Test creating a wand with default values."""
        wand = Wand(spell_type="fireball")
        
        assert wand.spell_type == "fireball"
        assert wand.charges == 1
        assert wand.owner is None
    
    def test_wand_with_custom_charges(self):
        """Test creating a wand with custom charge count."""
        wand = Wand(spell_type="lightning", charges=5)
        
        assert wand.spell_type == "lightning"
        assert wand.charges == 5
    
    def test_wand_with_zero_charges(self):
        """Test creating an empty wand."""
        wand = Wand(spell_type="fireball", charges=0)
        
        assert wand.charges == 0
        assert wand.is_empty()


class TestWandCharges:
    """Test wand charge management."""
    
    def test_use_charge_success(self):
        """Test using a charge from a wand with charges."""
        wand = Wand(spell_type="fireball", charges=3)
        
        result = wand.use_charge()
        
        assert result is True
        assert wand.charges == 2
    
    def test_use_charge_until_empty(self):
        """Test using all charges from a wand."""
        wand = Wand(spell_type="fireball", charges=2)
        
        assert wand.use_charge() is True
        assert wand.charges == 1
        assert wand.use_charge() is True
        assert wand.charges == 0
        assert wand.is_empty()
    
    def test_use_charge_when_empty(self):
        """Test trying to use a charge from an empty wand."""
        wand = Wand(spell_type="fireball", charges=0)
        
        result = wand.use_charge()
        
        assert result is False
        assert wand.charges == 0
    
    def test_add_charge_single(self):
        """Test adding a single charge."""
        wand = Wand(spell_type="fireball", charges=3)
        
        wand.add_charge()
        
        assert wand.charges == 4
    
    def test_add_charge_multiple(self):
        """Test adding multiple charges at once."""
        wand = Wand(spell_type="fireball", charges=2)
        
        wand.add_charge(5)
        
        assert wand.charges == 7
    
    def test_add_charge_to_empty_wand(self):
        """Test recharging an empty wand."""
        wand = Wand(spell_type="fireball", charges=0)
        
        wand.add_charge()
        
        assert wand.charges == 1
        assert not wand.is_empty()
    
    def test_unlimited_charges(self):
        """Test that wands can have unlimited charges (no max)."""
        wand = Wand(spell_type="fireball", charges=100)
        
        wand.add_charge(50)
        
        assert wand.charges == 150
        # No max limit enforced


class TestWandDisplayName:
    """Test wand display name generation."""
    
    def test_display_name_without_owner(self):
        """Test display name when wand has no owner."""
        wand = Wand(spell_type="fireball", charges=5)
        
        display_name = wand.get_display_name()
        
        # Should include charge indicator (● for 5+ charges)
        assert display_name == "Wand ● 5"
    
    def test_display_name_with_owner(self):
        """Test display name when wand is attached to an entity."""
        wand = Wand(spell_type="fireball", charges=7)
        entity = Entity(0, 0, '/', (255, 255, 255), 'Wand of Fireball', blocks=False)
        wand.owner = entity
        
        display_name = wand.get_display_name()
        
        # Should include charge indicator (● for 5+ charges)
        assert display_name == "Wand of Fireball ● 7"
    
    def test_display_name_updates_with_charges(self):
        """Test that display name reflects current charge count and indicator changes."""
        wand = Wand(spell_type="fireball", charges=5)
        entity = Entity(0, 0, '/', (255, 255, 255), 'Wand of Fireball', blocks=False)
        wand.owner = entity
        
        # 5 charges = ● (full circle)
        assert wand.get_display_name() == "Wand of Fireball ● 5"
        
        wand.use_charge()
        # 4 charges = ◕ (three-quarter filled)
        assert wand.get_display_name() == "Wand of Fireball ◕ 4"
        
        wand.add_charge(3)
        # 7 charges = ● (full circle, 5+)
        assert wand.get_display_name() == "Wand of Fireball ● 7"
    
    def test_display_name_with_zero_charges(self):
        """Test display name shows zero for empty wands."""
        wand = Wand(spell_type="fireball", charges=0)
        entity = Entity(0, 0, '/', (255, 255, 255), 'Wand of Fireball', blocks=False)
        wand.owner = entity
        
        display_name = wand.get_display_name()
        
        # 0 charges = ○ (empty circle)
        assert display_name == "Wand of Fireball ○ 0"


class TestWandIsEmpty:
    """Test wand empty state checking."""
    
    def test_is_empty_with_charges(self):
        """Test that wand with charges is not empty."""
        wand = Wand(spell_type="fireball", charges=5)
        
        assert not wand.is_empty()
    
    def test_is_empty_with_zero_charges(self):
        """Test that wand with zero charges is empty."""
        wand = Wand(spell_type="fireball", charges=0)
        
        assert wand.is_empty()
    
    def test_is_empty_after_depleting(self):
        """Test that wand becomes empty after using all charges."""
        wand = Wand(spell_type="fireball", charges=1)
        
        assert not wand.is_empty()
        wand.use_charge()
        assert wand.is_empty()


class TestWandSpellType:
    """Test wand spell type tracking."""
    
    def test_different_spell_types(self):
        """Test wands with different spell types."""
        fireball_wand = Wand(spell_type="fireball", charges=3)
        lightning_wand = Wand(spell_type="lightning", charges=5)
        confusion_wand = Wand(spell_type="confusion", charges=2)
        
        assert fireball_wand.spell_type == "fireball"
        assert lightning_wand.spell_type == "lightning"
        assert confusion_wand.spell_type == "confusion"
    
    def test_spell_type_immutable(self):
        """Test that spell type doesn't change with charge operations."""
        wand = Wand(spell_type="fireball", charges=3)
        original_spell = wand.spell_type
        
        wand.use_charge()
        wand.add_charge(2)
        
        assert wand.spell_type == original_spell


class TestWandIntegration:
    """Integration tests for wand component."""
    
    def test_wand_lifecycle(self):
        """Test complete wand lifecycle: use, deplete, recharge."""
        wand = Wand(spell_type="fireball", charges=2)
        entity = Entity(0, 0, '/', (255, 255, 255), 'Wand of Fireball', blocks=False)
        wand.owner = entity
        
        # Use charges - 2 charges = ◐ (half-filled)
        assert wand.get_display_name() == "Wand of Fireball ◐ 2"
        wand.use_charge()
        assert wand.get_display_name() == "Wand of Fireball ◐ 1"
        
        # Deplete
        wand.use_charge()
        assert wand.is_empty()
        # 0 charges = ○ (empty circle)
        assert wand.get_display_name() == "Wand of Fireball ○ 0"
        
        # Try to use when empty
        assert wand.use_charge() is False
        assert wand.charges == 0
        
        # Recharge by picking up scroll - 1 charge = ◐ (half-filled)
        wand.add_charge()
        assert not wand.is_empty()
        assert wand.get_display_name() == "Wand of Fireball ◐ 1"
        
        # Continue using
        assert wand.use_charge() is True
        assert wand.charges == 0

