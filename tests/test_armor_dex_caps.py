"""Tests for armor DEX cap system.

Verifies that light/medium/heavy armor correctly caps DEX modifier
when calculating Armor Class (AC).
"""


# QUARANTINED: DEX cap feature needs verification
# See QUARANTINED_TESTS.md for details.

import pytest

# Quarantine entire file
# pytestmark = pytest.mark.skip(reason="Quarantined - DEX cap feature needs verification. See QUARANTINED_TESTS.md")  # REMOVED Session 2

import pytest
from entity import Entity
from components.fighter import Fighter
from components.equipment import Equipment
from components.equippable import Equippable
from equipment_slots import EquipmentSlots


class TestArmorDEXCaps:
    """Test DEX cap functionality for different armor types."""
    
    def test_no_armor_full_dex_bonus(self):
        """No armor should apply full DEX bonus to AC."""
        player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
        player.fighter = Fighter(hp=60, defense=1, power=0, dexterity=18)  # +4 DEX mod
        player.fighter.owner = player
        player.equipment = Equipment()
        player.equipment.owner = player
        
        # AC = 10 + 4 (DEX) + 0 (no armor) = 14
        assert player.fighter.armor_class == 14
    
    def test_light_armor_no_dex_cap(self):
        """Light armor should have no DEX cap - full DEX bonus applies."""
        player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
        player.fighter = Fighter(hp=60, defense=1, power=0, dexterity=18)  # +4 DEX mod
        player.fighter.owner = player
        player.equipment = Equipment()
        player.equipment.owner = player
        
        # Create leather armor (light, +2 AC, no DEX cap)
        leather = Entity(0, 0, '[', (139, 69, 19), 'Leather Armor')
        leather.equippable = Equippable(
            slot=EquipmentSlots.CHEST,
            armor_class_bonus=2,
            armor_type='light',
            dex_cap=None  # No cap
        )
        leather.equippable.owner = leather
        
        # Equip it
        player.equipment.chest = leather
        
        # AC = 10 + 4 (DEX, uncapped) + 2 (leather) = 16
        assert player.fighter.armor_class == 16
    
    def test_medium_armor_dex_cap_2(self):
        """Medium armor should cap DEX bonus at +2."""
        player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
        player.fighter = Fighter(hp=60, defense=1, power=0, dexterity=18)  # +4 DEX mod
        player.fighter.owner = player
        player.equipment = Equipment()
        player.equipment.owner = player
        
        # Create chain mail (medium, +4 AC, DEX cap +2)
        chain_mail = Entity(0, 0, '[', (169, 169, 169), 'Chain Mail')
        chain_mail.equippable = Equippable(
            slot=EquipmentSlots.CHEST,
            armor_class_bonus=4,
            armor_type='medium',
            dex_cap=2  # Cap at +2
        )
        chain_mail.equippable.owner = chain_mail
        
        # Equip it
        player.equipment.chest = chain_mail
        
        # AC = 10 + 2 (DEX capped at +2) + 4 (chain) = 16
        assert player.fighter.armor_class == 16
    
    def test_heavy_armor_dex_cap_0(self):
        """Heavy armor should cap DEX bonus at 0 (no DEX bonus!)."""
        player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
        player.fighter = Fighter(hp=60, defense=1, power=0, dexterity=18)  # +4 DEX mod
        player.fighter.owner = player
        player.equipment = Equipment()
        player.equipment.owner = player
        
        # Create plate mail (heavy, +6 AC, DEX cap 0)
        plate_mail = Entity(0, 0, '[', (220, 220, 220), 'Plate Mail')
        plate_mail.equippable = Equippable(
            slot=EquipmentSlots.CHEST,
            armor_class_bonus=6,
            armor_type='heavy',
            dex_cap=0  # No DEX bonus!
        )
        plate_mail.equippable.owner = plate_mail
        
        # Equip it
        player.equipment.chest = plate_mail
        
        # AC = 10 + 0 (DEX capped at 0) + 6 (plate) = 16
        assert player.fighter.armor_class == 16
    
    def test_low_dex_not_affected_by_cap(self):
        """Players with low DEX shouldn't be affected by DEX caps."""
        player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
        player.fighter = Fighter(hp=60, defense=1, power=0, dexterity=10)  # +0 DEX mod
        player.fighter.owner = player
        player.equipment = Equipment()
        player.equipment.owner = player
        
        # Create plate mail (heavy, +6 AC, DEX cap 0)
        plate_mail = Entity(0, 0, '[', (220, 220, 220), 'Plate Mail')
        plate_mail.equippable = Equippable(
            slot=EquipmentSlots.CHEST,
            armor_class_bonus=6,
            armor_type='heavy',
            dex_cap=0
        )
        plate_mail.equippable.owner = plate_mail
        
        # Equip it
        player.equipment.chest = plate_mail
        
        # AC = 10 + 0 (DEX already 0) + 6 (plate) = 16
        assert player.fighter.armor_class == 16
    
    def test_multiple_armor_pieces_most_restrictive_cap(self):
        """When wearing multiple armor pieces, use the most restrictive DEX cap."""
        player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
        player.fighter = Fighter(hp=60, defense=1, power=0, dexterity=18)  # +4 DEX mod
        player.fighter.owner = player
        player.equipment = Equipment()
        player.equipment.owner = player
        
        # Create light helmet (+1 AC, no cap)
        helmet = Entity(0, 0, '^', (160, 82, 45), 'Leather Helmet')
        helmet.equippable = Equippable(
            slot=EquipmentSlots.HEAD,
            armor_class_bonus=1,
            armor_type='light',
            dex_cap=None
        )
        helmet.equippable.owner = helmet
        
        # Create medium chest (+4 AC, cap +2)
        chain_mail = Entity(0, 0, '[', (169, 169, 169), 'Chain Mail')
        chain_mail.equippable = Equippable(
            slot=EquipmentSlots.CHEST,
            armor_class_bonus=4,
            armor_type='medium',
            dex_cap=2  # Most restrictive cap
        )
        chain_mail.equippable.owner = chain_mail
        
        # Equip both
        player.equipment.head = helmet
        player.equipment.chest = chain_mail
        
        # AC = 10 + 2 (DEX capped at +2 by chain mail) + 1 (helmet) + 4 (chain) = 17
        assert player.fighter.armor_class == 17
    
    def test_shield_does_not_apply_dex_cap(self):
        """Shields should not apply DEX caps."""
        player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
        player.fighter = Fighter(hp=60, defense=1, power=0, dexterity=18)  # +4 DEX mod
        player.fighter.owner = player
        player.equipment = Equipment()
        player.equipment.owner = player
        
        # Create shield (+2 AC, shield type)
        shield = Entity(0, 0, '[', (139, 69, 19), 'Shield')
        shield.equippable = Equippable(
            slot=EquipmentSlots.OFF_HAND,
            armor_class_bonus=2,
            armor_type='shield',  # Shield type doesn't affect DEX
            dex_cap=None
        )
        shield.equippable.owner = shield
        
        # Equip it
        player.equipment.off_hand = shield
        
        # AC = 10 + 4 (DEX, uncapped) + 2 (shield) = 16
        assert player.fighter.armor_class == 16
    
    def test_heavy_armor_with_shield(self):
        """Heavy armor + shield should cap DEX at 0."""
        player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
        player.fighter = Fighter(hp=60, defense=1, power=0, dexterity=18)  # +4 DEX mod
        player.fighter.owner = player
        player.equipment = Equipment()
        player.equipment.owner = player
        
        # Create plate mail (heavy, +6 AC, DEX cap 0)
        plate_mail = Entity(0, 0, '[', (220, 220, 220), 'Plate Mail')
        plate_mail.equippable = Equippable(
            slot=EquipmentSlots.CHEST,
            armor_class_bonus=6,
            armor_type='heavy',
            dex_cap=0
        )
        plate_mail.equippable.owner = plate_mail
        
        # Create shield (+2 AC, shield type)
        shield = Entity(0, 0, '[', (139, 69, 19), 'Shield')
        shield.equippable = Equippable(
            slot=EquipmentSlots.OFF_HAND,
            armor_class_bonus=2,
            armor_type='shield',
            dex_cap=None
        )
        shield.equippable.owner = shield
        
        # Equip both
        player.equipment.chest = plate_mail
        player.equipment.off_hand = shield
        
        # AC = 10 + 0 (DEX capped at 0 by plate) + 6 (plate) + 2 (shield) = 18
        assert player.fighter.armor_class == 18
    
    def test_negative_dex_not_improved_by_cap(self):
        """Negative DEX modifier should not be "improved" by DEX caps."""
        player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
        player.fighter = Fighter(hp=60, defense=1, power=0, dexterity=8)  # -1 DEX mod
        player.fighter.owner = player
        player.equipment = Equipment()
        player.equipment.owner = player
        
        # Create chain mail (medium, +4 AC, DEX cap +2)
        chain_mail = Entity(0, 0, '[', (169, 169, 169), 'Chain Mail')
        chain_mail.equippable = Equippable(
            slot=EquipmentSlots.CHEST,
            armor_class_bonus=4,
            armor_type='medium',
            dex_cap=2
        )
        chain_mail.equippable.owner = chain_mail
        
        # Equip it
        player.equipment.chest = chain_mail
        
        # AC = 10 + (-1) (DEX is negative, cap doesn't help) + 4 (chain) = 13
        # The cap is a maximum, not a minimum
        assert player.fighter.armor_class == 13


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

