"""Tests for Phase 18 Damage Type resistance/vulnerability system.

Tests that:
- Vulnerable targets take +1 damage
- Resistant targets take -1 damage (minimum 1)
- Damage type modifiers apply before crit multiplier
- Neutral targets are unaffected
"""

import pytest
from unittest.mock import patch

from entity import Entity
from components.equippable import Equippable
from components.fighter import Fighter
from components.equipment import Equipment
from equipment_slots import EquipmentSlots


class TestDamageTypeVulnerability:
    """Tests for damage type vulnerability (+1 damage)."""
    
    def _create_attacker_with_weapon(self, damage_type):
        """Helper to create attacker with weapon of specified damage type."""
        attacker = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
        attacker.fighter = Fighter(hp=30, defense=2, power=3, strength=14, dexterity=14)
        attacker.fighter.owner = attacker
        attacker.equipment = Equipment(attacker)
        
        # Create weapon with damage type
        weapon = Entity(0, 0, '/', (200, 200, 200), 'Weapon', blocks=False)
        weapon.equippable = Equippable(
            slot=EquipmentSlots.MAIN_HAND,
            damage_dice="1d8",
            to_hit_bonus=0,
            damage_type=damage_type  # Phase 18: slashing/piercing/bludgeoning
        )
        weapon.equippable.owner = weapon
        
        from unittest.mock import Mock
        weapon.components = Mock()
        weapon.components.has = Mock(return_value=True)
        
        attacker.equipment.main_hand = weapon
        return attacker
    
    def _create_target(self, vulnerability=None, resistance=None):
        """Helper to create target with damage type vulnerability/resistance."""
        target = Entity(1, 1, 'z', (128, 128, 96), 'Zombie', blocks=True)
        target.fighter = Fighter(hp=20, defense=2, power=3)
        target.fighter.owner = target
        
        # Phase 18: Add damage type fields
        if vulnerability:
            target.damage_vulnerability = vulnerability
        if resistance:
            target.damage_resistance = resistance
        
        return target
    
    @patch('components.fighter.random.randint')
    def test_vulnerable_target_takes_extra_damage(self, mock_randint):
        """Vulnerable targets take +1 damage."""
        attacker = self._create_attacker_with_weapon(damage_type="bludgeoning")
        target = self._create_target(vulnerability="bludgeoning")
        
        # Mock d20 roll to ensure hit (not crit)
        mock_randint.return_value = 15  # Sufficient to hit, not a crit
        
        with patch('components.fighter.show_hit'), patch('components.fighter.show_miss'):
            with patch('dice.roll_dice', return_value=5):  # 1d8 = 5
                results = attacker.fighter.attack_d20(target)
        
        # Base: 5 (weapon) + 2 (STR) = 7
        # Vulnerable: +1 = 8
        damage_messages = [r for r in results if r.get('message') and 'damage' in str(r['message']).lower()]
        assert any('8 damage' in str(m['message']) for m in damage_messages), \
            "Vulnerable target should take +1 damage (expected 8)"
    
    @patch('components.fighter.random.randint')
    def test_resistant_target_takes_reduced_damage(self, mock_randint):
        """Resistant targets take -1 damage."""
        attacker = self._create_attacker_with_weapon(damage_type="piercing")
        target = self._create_target(resistance="piercing")
        
        # Mock d20 roll to ensure hit (not crit)
        mock_randint.return_value = 15
        
        with patch('components.fighter.show_hit'), patch('components.fighter.show_miss'):
            with patch('dice.roll_dice', return_value=5):  # 1d8 = 5
                results = attacker.fighter.attack_d20(target)
        
        # Base: 5 (weapon) + 2 (STR) = 7
        # Resistant: -1 = 6
        damage_messages = [r for r in results if r.get('message') and 'damage' in str(r['message']).lower()]
        assert any('6 damage' in str(m['message']) for m in damage_messages), \
            "Resistant target should take -1 damage (expected 6)"
    
    @patch('components.fighter.random.randint')
    def test_neutral_target_takes_normal_damage(self, mock_randint):
        """Neutral targets (no resistance/vulnerability) take normal damage."""
        attacker = self._create_attacker_with_weapon(damage_type="slashing")
        target = self._create_target()  # No resistance or vulnerability
        
        # Mock d20 roll to ensure hit (not crit)
        mock_randint.return_value = 15
        
        with patch('components.fighter.show_hit'), patch('components.fighter.show_miss'):
            with patch('dice.roll_dice', return_value=5):  # 1d8 = 5
                results = attacker.fighter.attack_d20(target)
        
        # Base: 5 (weapon) + 2 (STR) = 7
        # Neutral: no modifier = 7
        damage_messages = [r for r in results if r.get('message') and 'damage' in str(r['message']).lower()]
        assert any('7 damage' in str(m['message']) for m in damage_messages), \
            "Neutral target should take normal damage (expected 7)"
    
    @patch('components.fighter.random.randint')
    def test_damage_type_applies_before_crit_multiplier(self, mock_randint):
        """Damage type modifier should apply before crit doubles damage."""
        attacker = self._create_attacker_with_weapon(damage_type="bludgeoning")
        target = self._create_target(vulnerability="bludgeoning")
        
        # Mock d20 roll for critical hit
        mock_randint.return_value = 20  # Natural 20 = crit
        
        with patch('components.fighter.show_hit'), patch('components.fighter.show_miss'):
            with patch('dice.roll_dice', return_value=5):  # 1d8 = 5
                results = attacker.fighter.attack_d20(target)
        
        # Base: 5 (weapon) + 2 (STR) = 7
        # Vulnerable: +1 = 8
        # Crit: × 2 = 16
        damage_messages = [r for r in results if r.get('message') and 'CRITICAL' in str(r['message'])]
        assert any('16 damage' in str(m['message']) for m in damage_messages), \
            "Vulnerable + crit should be (base+STR+1)×2 = 16"
    
    @patch('components.fighter.random.randint')
    def test_resistance_cannot_reduce_below_1_damage(self, mock_randint):
        """Damage cannot be reduced below 1 by resistance."""
        attacker = self._create_attacker_with_weapon(damage_type="piercing")
        
        # Create very weak attacker (low STR for low damage)
        attacker.fighter.strength = 8  # -1 modifier
        
        target = self._create_target(resistance="piercing")
        
        # Mock d20 roll to ensure hit
        mock_randint.return_value = 15
        
        with patch('components.fighter.show_hit'), patch('components.fighter.show_miss'):
            with patch('dice.roll_dice', return_value=1):  # 1d8 = 1 (minimum)
                results = attacker.fighter.attack_d20(target)
        
        # Base: 1 (weapon) + (-1) (weak STR) = 0
        # Resistant: -1 = -1
        # Floor: max(1, -1) = 1
        damage_messages = [r for r in results if r.get('message') and 'damage' in str(r['message']).lower()]
        # Should have at least 1 damage message
        assert len(damage_messages) > 0, "Should deal at least 1 damage"
        # Check that damage is at least 1
        assert any('1 damage' in str(m['message']) for m in damage_messages), \
            "Damage should never go below 1"
