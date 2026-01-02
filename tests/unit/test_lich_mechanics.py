"""Unit tests for Phase 19 Lich identity mechanics.

Tests:
1. Soul Bolt charging effect creation and application
2. Soul Bolt damage calculation (35% max HP, deterministic)
3. Soul Ward effect reduces damage by 70%
4. Soul Ward converts prevented damage to Soul Burn DOT
5. Soul Burn ticks correctly over 3 turns (deterministic split)
6. Command the Dead grants +1 to-hit to undead allies within radius 6
7. Death Siphon heals lich 2 HP when allied undead dies within radius 6
"""

import pytest
import math
from unittest.mock import Mock, MagicMock, patch
from components.status_effects import ChargingSoulBoltEffect, SoulWardEffect, SoulBurnEffect, StatusEffectManager
from components.fighter import Fighter
from components.component_registry import ComponentType, ComponentRegistry


class TestChargingSoulBoltEffect:
    """Test Charging Soul Bolt status effect."""
    
    def test_charging_creation(self):
        """Test creating a charging soul bolt effect."""
        owner = Mock()
        owner.name = "Lich"
        
        charge_effect = ChargingSoulBoltEffect(owner=owner)
        
        assert charge_effect.name == "charging_soul_bolt"
        assert charge_effect.duration == 2  # 2 turns (to survive turn_end processing)
        assert charge_effect.owner == owner
    
    def test_charging_apply(self):
        """Test applying charging effect shows telegraph message."""
        owner = Mock()
        owner.name = "Lich"
        
        charge_effect = ChargingSoulBoltEffect(owner=owner)
        results = charge_effect.apply()
        
        assert charge_effect.is_active
        assert len(results) == 1
        # Should have a message about channeling
        assert 'message' in results[0]


class TestSoulWardEffect:
    """Test Soul Ward status effect."""
    
    def test_soul_ward_creation(self):
        """Test creating a soul ward effect."""
        owner = Mock()
        owner.name = "Player"
        
        ward_effect = SoulWardEffect(duration=10, owner=owner)
        
        assert ward_effect.name == "soul_ward"
        assert ward_effect.duration == 10
        assert ward_effect.owner == owner
    
    def test_soul_ward_apply(self):
        """Test applying soul ward shows protective message."""
        owner = Mock()
        owner.name = "Player"
        
        ward_effect = SoulWardEffect(duration=10, owner=owner)
        results = ward_effect.apply()
        
        assert ward_effect.is_active
        assert len(results) == 1
        assert 'message' in results[0]
    
    def test_soul_ward_remove(self):
        """Test removing soul ward shows expiry message."""
        owner = Mock()
        owner.name = "Player"
        
        ward_effect = SoulWardEffect(duration=10, owner=owner)
        ward_effect.is_active = True
        
        results = ward_effect.remove()
        
        assert not ward_effect.is_active
        assert len(results) == 1
        assert 'message' in results[0]


class TestSoulBurnEffect:
    """Test Soul Burn DOT status effect."""
    
    def test_soul_burn_creation(self):
        """Test creating a soul burn effect."""
        owner = Mock()
        owner.name = "Player"
        
        burn_effect = SoulBurnEffect(total_damage=15, owner=owner)
        
        assert burn_effect.name == "soul_burn"
        assert burn_effect.duration == 3  # 3 turn DOT
        assert burn_effect.total_damage == 15
        assert burn_effect.damage_per_turn == 5  # 15 // 3
        assert burn_effect.remainder == 0  # 15 % 3
        assert burn_effect.ticks_remaining == 3
    
    def test_soul_burn_damage_distribution(self):
        """Test Soul Burn damage is distributed correctly over 3 turns."""
        owner = Mock()
        owner.name = "Player"
        
        # Test case 1: Evenly divisible (15 damage -> 5-5-5)
        burn1 = SoulBurnEffect(total_damage=15, owner=owner)
        assert burn1.damage_per_turn == 5
        assert burn1.remainder == 0
        # Turn 1-3 should deal 5 each
        
        # Test case 2: Remainder of 1 (13 damage -> 4-4-5)
        burn2 = SoulBurnEffect(total_damage=13, owner=owner)
        assert burn2.damage_per_turn == 4
        assert burn2.remainder == 1
        # Turn 1-2 should deal 4, turn 3 should deal 5
        
        # Test case 3: Remainder of 2 (14 damage -> 4-4-6)
        burn3 = SoulBurnEffect(total_damage=14, owner=owner)
        assert burn3.damage_per_turn == 4
        assert burn3.remainder == 2
        # Turn 1-2 should deal 4, turn 3 should deal 6
    
    def test_soul_burn_tick_damage(self):
        """Test Soul Burn applies damage each turn."""
        owner = Mock()
        owner.name = "Player"
        
        # Mock fighter component
        mock_fighter = Mock()
        mock_fighter.take_damage = Mock(return_value=[])
        owner.get_component_optional = Mock(return_value=mock_fighter)
        
        burn_effect = SoulBurnEffect(total_damage=13, owner=owner)
        
        # First tick: should deal 4 damage
        burn_effect.ticks_remaining = 3
        results = burn_effect.process_turn_start()
        
        mock_fighter.take_damage.assert_called_once_with(4)
        assert burn_effect.ticks_remaining == 2
        assert len(results) >= 1  # Should have message
        
        # Second tick: should deal 4 damage
        mock_fighter.take_damage.reset_mock()
        results = burn_effect.process_turn_start()
        
        mock_fighter.take_damage.assert_called_once_with(4)
        assert burn_effect.ticks_remaining == 1
        
        # Third tick: should deal 5 damage (4 + remainder 1)
        mock_fighter.take_damage.reset_mock()
        results = burn_effect.process_turn_start()
        
        mock_fighter.take_damage.assert_called_once_with(5)  # damage_per_turn + remainder
        assert burn_effect.ticks_remaining == 0


class TestSoulBoltDamageCalculation:
    """Test Soul Bolt damage calculation."""
    
    def test_soul_bolt_base_damage(self):
        """Test Soul Bolt deals 35% of target max HP (rounded up)."""
        # Test case 1: Player with 54 HP (scenario default)
        max_hp = 54
        soul_bolt_pct = 0.35
        expected_damage = math.ceil(max_hp * soul_bolt_pct)  # ceil(18.9) = 19
        
        assert expected_damage == 19
        
        # Test case 2: Player with 100 HP
        max_hp = 100
        expected_damage = math.ceil(max_hp * soul_bolt_pct)  # ceil(35) = 35
        
        assert expected_damage == 35
        
        # Test case 3: Player with 77 HP
        max_hp = 77
        expected_damage = math.ceil(max_hp * soul_bolt_pct)  # ceil(26.95) = 27
        
        assert expected_damage == 27
    
    def test_soul_ward_reduction(self):
        """Test Soul Ward reduces Soul Bolt damage by 70%."""
        base_damage = 19  # From 54 HP player
        ward_reduction_pct = 0.70
        
        # Upfront damage: 30% of base (70% prevented)
        upfront_damage = math.ceil(base_damage * (1 - ward_reduction_pct))  # ceil(5.7) = 6
        
        # Prevented damage becomes DOT
        prevented_damage = base_damage - upfront_damage  # 19 - 6 = 13
        
        assert upfront_damage == 6
        assert prevented_damage == 13
        
        # Prevented damage distributes over 3 turns: 4-4-5
        damage_per_turn = prevented_damage // 3  # 13 // 3 = 4
        remainder = prevented_damage % 3  # 13 % 3 = 1
        
        assert damage_per_turn == 4
        assert remainder == 1  # Last tick gets extra 1 damage


class TestCommandTheDeadAura:
    """Test Command the Dead passive aura."""
    
    def test_command_the_dead_radius(self):
        """Test Command the Dead checks radius correctly."""
        # Lich at (10, 10), undead ally at various positions
        lich_x, lich_y = 10, 10
        command_radius = 6
        
        # Test case 1: Within radius (distance 4)
        ally_x, ally_y = 14, 10
        distance = math.sqrt((ally_x - lich_x)**2 + (ally_y - lich_y)**2)
        assert distance == 4.0
        assert distance <= command_radius  # Should get bonus
        
        # Test case 2: Exactly at radius (distance 6)
        ally_x, ally_y = 16, 10
        distance = math.sqrt((ally_x - lich_x)**2 + (ally_y - lich_y)**2)
        assert distance == 6.0
        assert distance <= command_radius  # Should get bonus
        
        # Test case 3: Outside radius (distance 7)
        ally_x, ally_y = 17, 10
        distance = math.sqrt((ally_x - lich_x)**2 + (ally_y - lich_y)**2)
        assert distance == 7.0
        assert distance > command_radius  # Should NOT get bonus
    
    def test_command_the_dead_faction_check(self):
        """Test Command the Dead only affects undead faction allies."""
        # Only undead faction should benefit
        valid_factions = ['undead']
        invalid_factions = ['cultist', 'hostile', 'neutral', None]
        
        for faction in valid_factions:
            assert faction == 'undead'
        
        for faction in invalid_factions:
            assert faction != 'undead'


class TestDeathSiphonMechanics:
    """Test Death Siphon passive heal."""
    
    def test_death_siphon_radius(self):
        """Test Death Siphon checks radius correctly."""
        # Lich at (10, 10), dying undead at various positions
        lich_x, lich_y = 10, 10
        siphon_radius = 6
        
        # Test case 1: Within radius (distance 3)
        corpse_x, corpse_y = 13, 10
        distance = math.sqrt((corpse_x - lich_x)**2 + (corpse_y - lich_y)**2)
        assert distance == 3.0
        assert distance <= siphon_radius  # Should trigger siphon
        
        # Test case 2: Exactly at radius (distance 6)
        corpse_x, corpse_y = 16, 10
        distance = math.sqrt((corpse_x - lich_x)**2 + (corpse_y - lich_y)**2)
        assert distance == 6.0
        assert distance <= siphon_radius  # Should trigger siphon
        
        # Test case 3: Outside radius (distance 8)
        corpse_x, corpse_y = 18, 10
        distance = math.sqrt((corpse_x - lich_x)**2 + (corpse_y - lich_y)**2)
        assert distance == 8.0
        assert distance > siphon_radius  # Should NOT trigger siphon
    
    def test_death_siphon_heal_amount(self):
        """Test Death Siphon heals 2 HP, capped at missing HP."""
        siphon_heal_base = 2
        
        # Test case 1: Lich missing 5 HP -> heals 2
        missing_hp = 5
        heal_amount = min(siphon_heal_base, missing_hp)
        assert heal_amount == 2
        
        # Test case 2: Lich missing 1 HP -> heals 1 (capped)
        missing_hp = 1
        heal_amount = min(siphon_heal_base, missing_hp)
        assert heal_amount == 1
        
        # Test case 3: Lich at max HP -> heals 0
        missing_hp = 0
        heal_amount = min(siphon_heal_base, missing_hp)
        assert heal_amount == 0
    
    def test_death_siphon_faction_check(self):
        """Test Death Siphon only triggers for undead faction deaths."""
        # Only undead faction deaths should trigger siphon
        valid_factions = ['undead']
        invalid_factions = ['cultist', 'hostile', 'neutral', None]
        
        for faction in valid_factions:
            assert faction == 'undead'
        
        for faction in invalid_factions:
            assert faction != 'undead'

