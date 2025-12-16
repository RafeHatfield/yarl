"""Tests for equipment corrosion mechanics."""


# QUARANTINED: Corrosion feature needs verification
# See QUARANTINED_TESTS.md for details.

import pytest

# Quarantine entire file
# pytestmark = pytest.mark.skip(reason="Quarantined - Corrosion feature needs verification. See QUARANTINED_TESTS.md")  # REMOVED Session 2
import pytest
import unittest.mock
from unittest.mock import Mock, patch

from entity import Entity
from components.fighter import Fighter
from components.equipment import Equipment
from components.equippable import Equippable
from components.faction import Faction
from equipment_slots import EquipmentSlots
from render_functions import RenderOrder


class TestCorrosionMechanics:
    """Test equipment corrosion functionality."""
    
    def setup_method(self):
        """Set up test entities with equipment."""
        # Create slime with corrosion ability
        self.slime = Entity(
            x=5, y=5, char='s', color=(0, 255, 0), name='Slime',
            blocks=True, render_order=RenderOrder.ACTOR, faction=Faction.HOSTILE_ALL,
            fighter=Fighter(hp=15, defense=0, power=0, xp=25, damage_min=1, damage_max=3)
        )
        self.slime.special_abilities = ['corrosion']
        
        # Create player with equipment
        self.player = Entity(
            x=3, y=3, char='@', color=(255, 255, 255), name='Player',
            blocks=True, render_order=RenderOrder.ACTOR, faction=Faction.PLAYER,
            fighter=Fighter(hp=100, defense=1, power=0, xp=0, damage_min=3, damage_max=4),
            equipment=Equipment()
        )
        
        # Create weapon and armor for player
        self.sword = Entity(
            x=0, y=0, char='/', color=(192, 192, 192), name='Sword',
            equippable=Equippable(EquipmentSlots.MAIN_HAND, power_bonus=0, damage_min=4, damage_max=7, material="metal")
        )
        
        self.shield = Entity(
            x=0, y=0, char='[', color=(139, 69, 19), name='Shield',
            equippable=Equippable(EquipmentSlots.OFF_HAND, defense_bonus=0, defense_min=1, defense_max=3)
        )
        
        # Equip items
        self.player.equipment.toggle_equip(self.sword)
        self.player.equipment.toggle_equip(self.shield)
    
    def test_slime_has_corrosion_ability(self):
        """Test that slimes are detected as having corrosion ability."""
        # First slime has special_abilities set in setup_method
        assert self.slime.fighter._has_corrosion_ability()
        
        # Create another slime with special_abilities
        slime_with_abilities = Entity(
            x=0, y=0, char='s', color=(0, 255, 0), name='Slime2',
            faction=Faction.HOSTILE_ALL,
            fighter=Fighter(hp=15, defense=0, power=0, xp=25)
        )
        slime_with_abilities.special_abilities = ['corrosion']
        assert slime_with_abilities.fighter._has_corrosion_ability()
    
    def test_non_slime_no_corrosion_ability(self):
        """Test that non-slimes don't have corrosion ability."""
        orc = Entity(
            x=0, y=0, char='o', color=(63, 127, 63), name='Orc',
            faction=Faction.NEUTRAL,
            fighter=Fighter(hp=20, defense=0, power=0, xp=35)
        )
        assert not orc.fighter._has_corrosion_ability()
        
        # Player shouldn't have corrosion either
        assert not self.player.fighter._has_corrosion_ability()
    
    def test_weapon_corrosion(self):
        """Test that weapons can be corroded."""
        initial_max_damage = self.sword.equippable.damage_max
        
        # Corrode weapon
        results = self.slime.fighter._corrode_weapon(self.player)
        
        # Check that damage was reduced
        assert self.sword.equippable.damage_max == initial_max_damage - 1
        assert len(results) == 1
        assert 'corrodes' in results[0]['message'].text
        assert 'Sword' in results[0]['message'].text
    
    def test_weapon_corrosion_minimum_protection(self):
        """Test that weapons can't be corroded below 50% of base damage."""
        # Phase 19: Corrosion floor is 50% of base_damage_max
        base_max = self.sword.equippable.base_damage_max
        floor = max(1, int(base_max * 0.5))
        
        # Set weapon to floor
        self.sword.equippable.damage_max = floor
        
        # Try to corrode
        results = self.slime.fighter._corrode_weapon(self.player)
        
        # Should not corrode further
        assert len(results) == 0
        assert self.sword.equippable.damage_max == floor
    
    def test_non_metal_weapon_immune(self):
        """Test that non-metal weapons are immune to corrosion."""
        # Create a wooden club
        wooden_club = Entity(
            x=0, y=0, char=')', color=(101, 67, 33), name='Wooden Club',
            equippable=Equippable(EquipmentSlots.MAIN_HAND, damage_min=3, damage_max=6, material="wood")
        )
        self.player.equipment.toggle_equip(wooden_club)
        
        initial_max = wooden_club.equippable.damage_max
        
        # Try to corrode wooden weapon
        results = self.slime.fighter._corrode_weapon(self.player)
        
        # Should NOT corrode (wood is immune)
        assert len(results) == 0
        assert wooden_club.equippable.damage_max == initial_max
    
    def test_weapon_without_material_immune(self):
        """Test that weapons without material field are immune to corrosion."""
        # Create a weapon without material field
        mysterious_weapon = Entity(
            x=0, y=0, char='?', color=(255, 0, 255), name='Mysterious Weapon',
            equippable=Equippable(EquipmentSlots.MAIN_HAND, damage_min=2, damage_max=5)
        )
        self.player.equipment.toggle_equip(mysterious_weapon)
        
        initial_max = mysterious_weapon.equippable.damage_max
        
        # Try to corrode
        results = self.slime.fighter._corrode_weapon(self.player)
        
        # Should NOT corrode (no material = immune)
        assert len(results) == 0
        assert mysterious_weapon.equippable.damage_max == initial_max
    
    def test_corrosion_no_equipment(self):
        """Test corrosion when target has no equipment."""
        # Create entity with no equipment
        unequipped_entity = Entity(
            x=0, y=0, char='@', color=(255, 255, 255), name='Unequipped',
            fighter=Fighter(hp=50, defense=0, power=0, xp=0)
        )
        
        # Try to corrode - should not crash and return no results
        weapon_results = self.slime.fighter._corrode_weapon(unequipped_entity)
        
        assert len(weapon_results) == 0
    
    def test_corrosion_integration_with_combat(self):
        """Test that corrosion is applied during combat."""
        # Create a stronger slime to ensure damage is dealt
        strong_slime = Entity(
            x=5, y=5, char='s', color=(0, 255, 0), name='Strong Slime',
            blocks=True, render_order=RenderOrder.ACTOR, faction=Faction.HOSTILE_ALL,
            fighter=Fighter(hp=15, defense=0, power=10, xp=25, damage_min=5, damage_max=8)  # Higher power
        )
        strong_slime.special_abilities = ['corrosion']
        
        # Mock random to always trigger corrosion (5% chance)
        with patch('random.random', return_value=0.01):  # Less than 5%
            # Mock take_damage to avoid actual damage processing
            with patch.object(self.player.fighter, 'take_damage', return_value=[]):
                # Strong slime attacks player
                results = strong_slime.fighter.attack(self.player)
                
                # Should have attack message and corrosion message (Phase 19: weapon only)
                messages = [r for r in results if 'message' in r]
                assert len(messages) >= 2  # At least attack + corrosion messages
                
                # Check for corrosion messages (only weapon, not armor)
                corrosion_messages = [m for m in messages if 'corrodes' in m['message'].text]
                assert len(corrosion_messages) == 1  # Exactly one corrosion message (weapon only)
    
    def test_no_corrosion_on_miss(self):
        """Test that corrosion doesn't apply when no damage is dealt."""
        # Create a player with very high defense to block all damage
        invulnerable_player = Entity(
            x=0, y=0, char='@', color=(255, 255, 255), name='Invulnerable Player',
            fighter=Fighter(hp=100, defense=1000, power=0, xp=0),  # Very high defense
            equipment=Equipment()
        )
        
        # Equip weapon for corrosion testing
        sword = Entity(
            x=0, y=0, char='/', color=(192, 192, 192), name='Sword',
            equippable=Equippable(EquipmentSlots.MAIN_HAND, damage_min=4, damage_max=7, material="metal")
        )
        invulnerable_player.equipment.toggle_equip(sword)
        
        with patch('random.random', return_value=0.01):  # Would trigger corrosion if damage dealt
            results = self.slime.fighter.attack(invulnerable_player)
            
            # Should have attack message but no corrosion
            messages = [r for r in results if 'message' in r]
            corrosion_messages = [m for m in messages if 'corrodes' in m['message'].text]
            assert len(corrosion_messages) == 0
    
    def test_corrosion_mechanism_works(self):
        """Test that corrosion mechanism is properly integrated."""
        # The corrosion mechanism is tested through the individual methods
        # and integration test. The exact probability is less important than
        # the mechanism working correctly.
        
        # Make slime strong enough to deal damage
        strong_slime = Entity(
            x=5, y=5, char='s', color=(0, 255, 0), name='Strong Slime',
            blocks=True, render_order=RenderOrder.ACTOR, faction=Faction.HOSTILE_ALL,
            fighter=Fighter(hp=15, defense=0, power=10, xp=25, damage_min=5, damage_max=8)
        )
        strong_slime.special_abilities = ['corrosion']
        
        # Test that _apply_corrosion_effects is called during combat
        with patch.object(strong_slime.fighter, '_apply_corrosion_effects', return_value=[]) as mock_corrosion:
            with patch.object(self.player.fighter, 'take_damage', return_value=[]):
                results = strong_slime.fighter.attack(self.player)
                
                # Corrosion method should have been called
                mock_corrosion.assert_called_once_with(self.player, unittest.mock.ANY)
    
    def test_special_abilities_attribute_corrosion(self):
        """Test corrosion detection via special_abilities attribute."""
        # Create entity with special_abilities list
        acid_monster = Entity(
            x=0, y=0, char='A', color=(0, 255, 0), name='Acid Monster',
            faction=Faction.NEUTRAL,  # Not HOSTILE_ALL
            fighter=Fighter(hp=20, defense=0, power=0, xp=50)
        )
        acid_monster.special_abilities = ['corrosion', 'other_ability']
        
        assert acid_monster.fighter._has_corrosion_ability()
        
        # Test without corrosion ability
        normal_monster = Entity(
            x=0, y=0, char='N', color=(255, 0, 0), name='Normal Monster',
            faction=Faction.NEUTRAL,
            fighter=Fighter(hp=20, defense=0, power=0, xp=50)
        )
        normal_monster.special_abilities = ['other_ability']
        
        assert not normal_monster.fighter._has_corrosion_ability()


class TestCorrosionMessageColors:
    """Test that corrosion messages have correct colors."""
    
    def setup_method(self):
        """Set up test entities."""
        self.slime = Entity(
            x=0, y=0, char='s', color=(0, 255, 0), name='Slime',
            faction=Faction.HOSTILE_ALL,
            fighter=Fighter(hp=15, defense=0, power=0, xp=25)
        )
        self.slime.special_abilities = ['corrosion']
        
        self.player = Entity(
            x=0, y=0, char='@', color=(255, 255, 255), name='Player',
            fighter=Fighter(hp=100, defense=0, power=0, xp=0),
            equipment=Equipment()
        )
        
        # Equip a metal weapon
        sword = Entity(
            x=0, y=0, char='/', color=(192, 192, 192), name='Sword',
            equippable=Equippable(EquipmentSlots.MAIN_HAND, damage_min=4, damage_max=7, material="metal")
        )
        self.player.equipment.toggle_equip(sword)
    
    def test_corrosion_message_color(self):
        """Test that corrosion messages use orange warning color."""
        results = self.slime.fighter._corrode_weapon(self.player)
        
        assert len(results) == 1
        message = results[0]['message']
        assert message.color == (255, 165, 0)  # Orange warning color
