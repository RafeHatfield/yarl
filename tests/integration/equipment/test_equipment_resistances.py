"""
Unit tests for equipment resistance bonuses.

Tests the equipment resistance system including:
- Resistance bonuses from individual equipment pieces
- Resistance aggregation from multiple equipped items
- Resistance stacking with ring bonuses
- Fighter integration with equipment resistances
"""

import pytest
from unittest.mock import Mock

from components.equipment import Equipment
from components.equippable import Equippable
from components.fighter import Fighter, ResistanceType
from components.ring import Ring, RingEffect
from equipment_slots import EquipmentSlots
from entity import Entity


from components.component_registry import ComponentType
class TestEquippableResistances:
    """Test Equippable component resistance functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        pass

    def test_equippable_has_resistances_field(self):
        """Test that Equippable can store resistance bonuses."""
        # Create equippable with fire resistance
        equippable = Equippable(
            slot=EquipmentSlots.CHEST,
            armor_class_bonus=5,
            resistances={ResistanceType.FIRE: 30}
        )
        
        assert hasattr(equippable, 'resistances')
        assert equippable.resistances[ResistanceType.FIRE] == 30

    def test_equippable_resistances_defaults_to_empty_dict(self):
        """Test that Equippable resistances defaults to empty dict if not provided."""
        equippable = Equippable(
            slot=EquipmentSlots.CHEST,
            armor_class_bonus=5
        )
        
        assert hasattr(equippable, 'resistances')
        assert equippable.resistances == {}

    def test_equippable_multiple_resistances(self):
        """Test that Equippable can store multiple resistance types."""
        equippable = Equippable(
            slot=EquipmentSlots.CHEST,
            armor_class_bonus=5,
            resistances={
                ResistanceType.FIRE: 30,
                ResistanceType.COLD: 20,
                ResistanceType.POISON: 15
            }
        )
        
        assert equippable.resistances[ResistanceType.FIRE] == 30
        assert equippable.resistances[ResistanceType.COLD] == 20
        assert equippable.resistances[ResistanceType.POISON] == 15


class TestEquipmentResistanceBonuses:
    """Test Equipment component resistance aggregation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.equipment = Equipment()

    def test_equipment_has_resistance_bonus_method(self):
        """Test that Equipment has get_resistance_bonus method."""
        assert hasattr(self.equipment, 'get_resistance_bonus')

    def test_resistance_bonus_no_equipment(self):
        """Test resistance bonus with no equipment returns 0."""
        fire_bonus = self.equipment.get_resistance_bonus(ResistanceType.FIRE)
        
        assert fire_bonus == 0

    def test_resistance_bonus_single_item(self):
        """Test resistance bonus from single equipped item."""
        # Create chest armor with fire resistance
        chest = Mock()
        chest.equippable = Mock()
        chest.equippable.resistances = {ResistanceType.FIRE: 30}
        
        self.equipment.chest = chest
        
        fire_bonus = self.equipment.get_resistance_bonus(ResistanceType.FIRE)
        assert fire_bonus == 30

    def test_resistance_bonus_multiple_items_same_type(self):
        """Test resistance bonus stacks from multiple items with same resistance."""
        # Dragon Scale Mail: +30% fire
        chest = Mock()
        chest.equippable = Mock()
        chest.equippable.resistances = {ResistanceType.FIRE: 30}
        
        # Ring of Fire Resistance: +25% fire
        ring = Mock()
        ring.equippable = Mock()
        ring.equippable.resistances = {ResistanceType.FIRE: 25}
        
        self.equipment.chest = chest
        self.equipment.left_ring = ring
        
        fire_bonus = self.equipment.get_resistance_bonus(ResistanceType.FIRE)
        assert fire_bonus == 55  # 30 + 25 = 55% total

    def test_resistance_bonus_multiple_resistance_types(self):
        """Test different resistance types on different items."""
        # Dragon Scale Mail: +30% fire
        chest = Mock()
        chest.equippable = Mock()
        chest.equippable.resistances = {ResistanceType.FIRE: 30}
        
        # Frost Cloak: +25% cold
        head = Mock()
        head.equippable = Mock()
        head.equippable.resistances = {ResistanceType.COLD: 25}
        
        self.equipment.chest = chest
        self.equipment.head = head
        
        assert self.equipment.get_resistance_bonus(ResistanceType.FIRE) == 30
        assert self.equipment.get_resistance_bonus(ResistanceType.COLD) == 25
        assert self.equipment.get_resistance_bonus(ResistanceType.POISON) == 0

    def test_resistance_bonus_item_with_no_resistances(self):
        """Test item without resistances doesn't contribute."""
        # Regular leather armor (no resistances)
        chest = Mock()
        chest.equippable = Mock()
        chest.equippable.resistances = {}
        
        self.equipment.chest = chest
        
        fire_bonus = self.equipment.get_resistance_bonus(ResistanceType.FIRE)
        assert fire_bonus == 0

    def test_resistance_bonus_with_rings(self):
        """Test resistance bonus includes both ring slots."""
        # Left ring: +10% fire
        left_ring = Mock()
        left_ring.equippable = Mock()
        left_ring.equippable.resistances = {ResistanceType.FIRE: 10}
        
        # Right ring: +15% fire
        right_ring = Mock()
        right_ring.equippable = Mock()
        right_ring.equippable.resistances = {ResistanceType.FIRE: 15}
        
        self.equipment.left_ring = left_ring
        self.equipment.right_ring = right_ring
        
        fire_bonus = self.equipment.get_resistance_bonus(ResistanceType.FIRE)
        assert fire_bonus == 25  # 10 + 15 = 25%


class TestFighterEquipmentResistanceIntegration:
    """Test Fighter component integrates equipment resistances."""

    def setup_method(self):
        """Set up test fixtures."""
        self.player = Entity(
            x=0, y=0, char='@', color=(255, 255, 255),
            name='Player', blocks=True,
            fighter=Fighter(hp=100, defense=5, power=5)
        )
        self.player.equipment = Equipment()

    def test_fighter_get_resistance_includes_equipment(self):
        """Test that Fighter.get_resistance includes equipment bonuses."""
        # Give player Dragon Scale Mail with +30% fire resistance
        chest = Mock()
        chest.equippable = Mock()
        chest.equippable.resistances = {ResistanceType.FIRE: 30}
        
        self.player.equipment.chest = chest
        
        # Fighter should include equipment bonus
        fire_resist = self.player.fighter.get_resistance(ResistanceType.FIRE)
        assert fire_resist >= 30  # At least 30% from equipment

    def test_fighter_resistance_stacks_base_and_equipment(self):
        """Test that base resistances and equipment resistances stack."""
        # Create fighter with 20% base fire resistance
        fighter_with_base = Fighter(
            hp=100, defense=5, power=5,
            resistances={ResistanceType.FIRE: 20}
        )
        entity = Entity(
            x=0, y=0, char='@', color=(255, 255, 255),
            name='Player', blocks=True,
            fighter=fighter_with_base
        )
        entity.equipment = Equipment()
        
        # Add Dragon Scale Mail with +30% fire resistance
        chest = Mock()
        chest.equippable = Mock()
        chest.equippable.resistances = {ResistanceType.FIRE: 30}
        
        entity.equipment.chest = chest
        
        # Should get 20% (base) + 30% (equipment) = 50% total
        fire_resist = entity.fighter.get_resistance(ResistanceType.FIRE)
        assert fire_resist == 50

    def test_fighter_resistance_caps_at_100(self):
        """Test that total resistance caps at 100% (immunity)."""
        # Create fighter with 50% base fire resistance
        fighter_with_base = Fighter(
            hp=100, defense=5, power=5,
            resistances={ResistanceType.FIRE: 50}
        )
        entity = Entity(
            x=0, y=0, char='@', color=(255, 255, 255),
            name='Player', blocks=True,
            fighter=fighter_with_base
        )
        entity.equipment = Equipment()
        
        # Add Dragon Scale Mail with +60% fire resistance (would be 110% total)
        chest = Mock()
        chest.equippable = Mock()
        chest.equippable.resistances = {ResistanceType.FIRE: 60}
        
        entity.equipment.chest = chest
        
        # Should cap at 100% (immunity)
        fire_resist = entity.fighter.get_resistance(ResistanceType.FIRE)
        assert fire_resist == 100

    def test_fighter_takes_reduced_damage_with_equipment_resistance(self):
        """Test that equipment resistances actually reduce damage taken."""
        # Give player Dragon Scale Mail with +50% fire resistance
        chest = Mock()
        chest.equippable = Mock()
        chest.equippable.resistances = {ResistanceType.FIRE: 50}
        
        self.player.equipment.chest = chest
        
        initial_hp = self.player.fighter.hp
        
        # Take 20 fire damage (should be reduced to 10)
        self.player.fighter.take_damage(20, damage_type='fire')
        
        # Should have taken only 10 damage (50% reduction)
        assert self.player.fighter.hp == initial_hp - 10


class TestRingOfResistance:
    """Test Ring of Resistance integration with equipment resistances."""

    def setup_method(self):
        """Set up test fixtures."""
        self.player = Entity(
            x=0, y=0, char='@', color=(255, 255, 255),
            name='Player', blocks=True,
            fighter=Fighter(hp=100, defense=5, power=5)
        )
        self.player.equipment = Equipment()

    def test_ring_of_resistance_provides_all_resistances(self):
        """Test that Ring of Resistance provides bonus to all resistance types."""
        # Create Ring of Resistance (+10% all resistances)
        ring_entity = Mock()
        ring_entity.equippable = Mock()
        ring_entity.equippable.resistances = {
            ResistanceType.FIRE: 10,
            ResistanceType.COLD: 10,
            ResistanceType.POISON: 10,
            ResistanceType.LIGHTNING: 10,
            ResistanceType.ACID: 10
        }
        
        self.player.equipment.left_ring = ring_entity
        
        # Check all resistance types
        assert self.player.equipment.get_resistance_bonus(ResistanceType.FIRE) == 10
        assert self.player.equipment.get_resistance_bonus(ResistanceType.COLD) == 10
        assert self.player.equipment.get_resistance_bonus(ResistanceType.POISON) == 10
        assert self.player.equipment.get_resistance_bonus(ResistanceType.LIGHTNING) == 10
        assert self.player.equipment.get_resistance_bonus(ResistanceType.ACID) == 10

    def test_ring_of_resistance_stacks_with_armor(self):
        """Test that Ring of Resistance stacks with armor resistances."""
        # Dragon Scale Mail: +30% fire
        chest = Mock()
        chest.equippable = Mock()
        chest.equippable.resistances = {ResistanceType.FIRE: 30}
        
        # Ring of Resistance: +10% all (including fire)
        ring = Mock()
        ring.equippable = Mock()
        ring.equippable.resistances = {
            ResistanceType.FIRE: 10,
            ResistanceType.COLD: 10,
            ResistanceType.POISON: 10,
            ResistanceType.LIGHTNING: 10,
            ResistanceType.ACID: 10
        }
        
        self.player.equipment.chest = chest
        self.player.equipment.left_ring = ring
        
        # Should get 30% (armor) + 10% (ring) = 40% fire
        assert self.player.equipment.get_resistance_bonus(ResistanceType.FIRE) == 40
        # Other resistances should only get ring bonus
        assert self.player.equipment.get_resistance_bonus(ResistanceType.COLD) == 10


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

