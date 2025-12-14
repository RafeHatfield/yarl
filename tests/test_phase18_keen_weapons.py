"""Tests for Phase 18 Keen Weapon crit mechanics.

Tests that:
- Keen weapons have crit_threshold = 19
- Crits occur on rolls >= crit_threshold
- Normal weapons still crit only on natural 20
- Keen weapons crit on 19-20 (10% chance)
"""

import pytest
from unittest.mock import Mock, patch

from entity import Entity
from components.equippable import Equippable
from components.fighter import Fighter
from components.equipment import Equipment
from components.component_registry import ComponentType
from equipment_slots import EquipmentSlots


class TestKeenWeaponCritThreshold:
    """Tests for Keen weapon expanded crit range."""
    
    def _create_attacker_with_weapon(self, crit_threshold=20):
        """Helper to create attacker with specified crit threshold weapon."""
        # Create attacker entity
        attacker = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
        
        # Create fighter
        attacker.fighter = Fighter(hp=30, defense=2, power=3, strength=14, dexterity=14)
        attacker.fighter.owner = attacker
        
        # Create equipment component
        attacker.equipment = Equipment(attacker)
        
        # Create weapon with crit threshold
        weapon = Entity(0, 0, '/', (200, 200, 200), 'Sword', blocks=False)
        weapon.equippable = Equippable(
            slot=EquipmentSlots.MAIN_HAND,
            damage_dice="1d8",
            to_hit_bonus=0,
            crit_threshold=crit_threshold  # Phase 18: Keen weapons have 19
        )
        weapon.components = Mock()
        weapon.components.has = Mock(return_value=True)
        
        # Equip weapon
        attacker.equipment.main_hand = weapon
        
        return attacker
    
    def _create_target(self, ac=15):
        """Helper to create target with specified AC."""
        target = Entity(1, 1, 'o', (0, 255, 0), 'Orc', blocks=True)
        target.fighter = Fighter(hp=20, defense=2, power=3)
        target.fighter.owner = target
        return target
    
    @patch('components.fighter.random.randint')
    def test_normal_weapon_crits_only_on_20(self, mock_randint):
        """Normal weapons (crit_threshold=20) crit only on natural 20."""
        attacker = self._create_attacker_with_weapon(crit_threshold=20)
        target = self._create_target(ac=15)
        
        # Roll 19 - should NOT crit for normal weapon
        mock_randint.return_value = 19
        with patch('components.fighter.show_hit'), patch('components.fighter.show_miss'):
            results = attacker.fighter.attack_d20(target, is_surprise=False)
        
        # Check results - should be normal hit, not crit
        crit_messages = [r for r in results if r.get('message') and 'CRITICAL' in str(r['message'])]
        assert len(crit_messages) == 0, "Roll 19 with normal weapon should NOT crit"
    
    @patch('components.fighter.random.randint')
    def test_keen_weapon_crits_on_19(self, mock_randint):
        """Keen weapons (crit_threshold=19) crit on roll 19."""
        attacker = self._create_attacker_with_weapon(crit_threshold=19)
        target = self._create_target(ac=15)
        
        # Roll 19 - should crit for Keen weapon
        mock_randint.return_value = 19
        with patch('components.fighter.show_hit'), patch('components.fighter.show_miss'):
            results = attacker.fighter.attack_d20(target, is_surprise=False)
        
        # Check results - should be critical hit
        crit_messages = [r for r in results if r.get('message') and 'CRITICAL' in str(r['message'])]
        assert len(crit_messages) > 0, "Roll 19 with Keen weapon SHOULD crit"
    
    @patch('components.fighter.random.randint')
    def test_keen_weapon_still_crits_on_20(self, mock_randint):
        """Keen weapons also crit on natural 20."""
        attacker = self._create_attacker_with_weapon(crit_threshold=19)
        target = self._create_target(ac=15)
        
        # Roll 20 - should always crit
        mock_randint.return_value = 20
        with patch('components.fighter.show_hit'), patch('components.fighter.show_miss'):
            results = attacker.fighter.attack_d20(target, is_surprise=False)
        
        # Check results - should be critical hit
        crit_messages = [r for r in results if r.get('message') and 'CRITICAL' in str(r['message'])]
        assert len(crit_messages) > 0, "Roll 20 should always crit"
    
    @patch('components.fighter.random.randint')
    def test_normal_weapon_crits_on_20(self, mock_randint):
        """Normal weapons crit on natural 20."""
        attacker = self._create_attacker_with_weapon(crit_threshold=20)
        target = self._create_target(ac=15)
        
        # Roll 20 - should crit
        mock_randint.return_value = 20
        with patch('components.fighter.show_hit'), patch('components.fighter.show_miss'):
            results = attacker.fighter.attack_d20(target, is_surprise=False)
        
        # Check results - should be critical hit
        crit_messages = [r for r in results if r.get('message') and 'CRITICAL' in str(r['message'])]
        assert len(crit_messages) > 0, "Roll 20 should always crit"
    
    def test_surprise_attacks_still_force_crit(self):
        """Surprise attacks force crit regardless of weapon."""
        # Test with normal weapon
        attacker = self._create_attacker_with_weapon(crit_threshold=20)
        target = self._create_target(ac=15)
        
        with patch('components.fighter.random.randint', return_value=10):  # Non-crit roll
            with patch('components.fighter.show_hit'), patch('components.fighter.show_miss'):
                results = attacker.fighter.attack_d20(target, is_surprise=True)
        
        # Check results - surprise should force crit
        crit_messages = [r for r in results if r.get('message') and 'CRITICAL' in str(r['message'])]
        assert len(crit_messages) > 0, "Surprise attack should force crit"
