"""
Unit tests for components/fighter.py

Tests combat mechanics including attack, defense, damage, and death.
"""
import pytest
from unittest.mock import Mock
from components.fighter import Fighter
from entity import Entity
from game_messages import Message
from render_functions import RenderOrder


class TestFighterBasics:
    """Test basic Fighter functionality."""
    
    def test_fighter_creation(self):
        """Test basic fighter creation."""
        # Act
        fighter = Fighter(hp=30, defense=2, power=5)
        
        # Assert
        assert fighter.max_hp == 30
        assert fighter.hp == 30
        assert fighter.defense == 2
        assert fighter.power == 5
        # Note: Fighter doesn't have owner attribute until assigned to entity

    def test_fighter_with_owner(self, mock_libtcod):
        """Test fighter with owner assignment."""
        # Arrange
        fighter = Fighter(hp=20, defense=1, power=3)
        entity = Entity(10, 10, 'o', mock_libtcod.red, 'Orc', fighter=fighter)
        
        # Assert
        assert fighter.owner == entity

    def test_fighter_zero_stats(self):
        """Test fighter with zero stats."""
        # Act
        fighter = Fighter(hp=0, defense=0, power=0)
        
        # Assert
        assert fighter.max_hp == 0
        assert fighter.hp == 0
        assert fighter.defense == 0
        assert fighter.power == 0

    def test_fighter_negative_stats(self):
        """Test fighter with negative stats."""
        # Act
        fighter = Fighter(hp=-5, defense=-2, power=-1)
        
        # Assert
        assert fighter.max_hp == -5
        assert fighter.hp == -5
        assert fighter.defense == -2
        assert fighter.power == -1


class TestFighterTakeDamage:
    """Test taking damage mechanics."""
    
    def test_take_damage_normal(self, mock_libtcod):
        """Test taking normal damage."""
        # Arrange
        fighter = Fighter(hp=30, defense=2, power=5)
        entity = Entity(10, 10, 'o', mock_libtcod.red, 'Orc', fighter=fighter)
        
        # Act
        results = fighter.take_damage(10)
        
        # Assert
        assert fighter.hp == 20  # 30 - 10
        assert len(results) == 0  # No death

    def test_take_damage_with_defense(self, mock_libtcod):
        """Test taking damage - defense is NOT applied in take_damage method."""
        # Arrange
        fighter = Fighter(hp=30, defense=5, power=5)
        entity = Entity(10, 10, 'o', mock_libtcod.red, 'Orc', fighter=fighter)
        
        # Act
        results = fighter.take_damage(10)
        
        # Assert
        # NOTE: take_damage() does NOT apply defense - that's only in attack()
        assert fighter.hp == 20  # 30 - 10 (defense not applied)
        assert len(results) == 0  # No death

    def test_take_damage_defense_blocks_all(self, mock_libtcod):
        """Test that take_damage doesn't apply defense (defense only in attack)."""
        # Arrange
        fighter = Fighter(hp=30, defense=15, power=5)
        entity = Entity(10, 10, 'o', mock_libtcod.red, 'Orc', fighter=fighter)
        
        # Act
        results = fighter.take_damage(10)
        
        # Assert
        # NOTE: Defense is NOT applied in take_damage, only in attack method
        assert fighter.hp == 20  # 30 - 10 (defense ignored)
        assert len(results) == 0  # No death

    def test_take_damage_lethal(self, mock_libtcod):
        """Test taking lethal damage."""
        # Arrange
        fighter = Fighter(hp=10, defense=0, power=5)
        entity = Entity(10, 10, 'o', mock_libtcod.red, 'Orc', fighter=fighter)
        
        # Act
        results = fighter.take_damage(15)
        
        # Assert
        assert fighter.hp <= 0
        assert len(results) == 1
        assert 'dead' in results[0]
        assert results[0]['dead'] == entity

    def test_take_damage_exact_lethal(self, mock_libtcod):
        """Test taking exactly lethal damage."""
        # Arrange
        fighter = Fighter(hp=10, defense=0, power=5)
        entity = Entity(10, 10, 'o', mock_libtcod.red, 'Orc', fighter=fighter)
        
        # Act
        results = fighter.take_damage(10)
        
        # Assert
        assert fighter.hp == 0
        assert len(results) == 1
        assert 'dead' in results[0]

    def test_take_damage_zero(self, mock_libtcod):
        """Test taking zero damage."""
        # Arrange
        fighter = Fighter(hp=30, defense=2, power=5)
        entity = Entity(10, 10, 'o', mock_libtcod.red, 'Orc', fighter=fighter)
        original_hp = fighter.hp
        
        # Act
        results = fighter.take_damage(0)
        
        # Assert
        assert fighter.hp == original_hp
        assert len(results) == 0

    def test_take_damage_negative(self, mock_libtcod):
        """Test taking negative damage (actually heals due to current implementation)."""
        # Arrange
        fighter = Fighter(hp=20, defense=2, power=5)
        entity = Entity(10, 10, 'o', mock_libtcod.red, 'Orc', fighter=fighter)
        original_hp = fighter.hp
        
        # Act
        results = fighter.take_damage(-5)
        
        # Assert
        # NOTE: Current implementation allows negative damage to heal
        assert fighter.hp == original_hp + 5  # 20 - (-5) = 25
        assert len(results) == 0

    def test_take_damage_massive_overkill(self, mock_libtcod):
        """Test taking massive overkill damage."""
        # Arrange
        fighter = Fighter(hp=10, defense=0, power=5)
        entity = Entity(10, 10, 'o', mock_libtcod.red, 'Orc', fighter=fighter)
        
        # Act
        results = fighter.take_damage(1000)
        
        # Assert
        assert fighter.hp <= 0
        assert len(results) == 1
        assert 'dead' in results[0]


class TestFighterAttack:
    """Test attack mechanics."""
    
    def test_attack_successful_hit(self, mock_libtcod):
        """Test successful attack against target."""
        # Arrange
        attacker_fighter = Fighter(hp=30, defense=2, power=8)
        attacker = Entity(10, 10, '@', mock_libtcod.white, 'Player', fighter=attacker_fighter)
        
        target_fighter = Fighter(hp=20, defense=3, power=5)
        target = Entity(15, 15, 'o', mock_libtcod.red, 'Orc', fighter=target_fighter)
        
        # Act
        results = attacker_fighter.attack(target)
        
        # Assert
        assert len(results) >= 1
        # Check for attack message
        message_result = next((r for r in results if 'message' in r), None)
        assert message_result is not None
        # Target should take damage (8 power - 3 defense = 5 damage)
        assert target_fighter.hp == 15  # 20 - 5

    def test_attack_target_dies(self, mock_libtcod):
        """Test attack that kills the target."""
        # Arrange
        attacker_fighter = Fighter(hp=30, defense=2, power=20)
        attacker = Entity(10, 10, '@', mock_libtcod.white, 'Player', fighter=attacker_fighter)
        
        target_fighter = Fighter(hp=5, defense=0, power=5)
        target = Entity(15, 15, 'o', mock_libtcod.red, 'Orc', fighter=target_fighter)
        
        # Act
        results = attacker_fighter.attack(target)
        
        # Assert
        assert len(results) >= 2  # Attack message + death
        # Check for death
        death_result = next((r for r in results if 'dead' in r), None)
        assert death_result is not None
        assert death_result['dead'] == target
        assert target_fighter.hp <= 0

    def test_attack_no_damage(self, mock_libtcod):
        """Test attack that deals no damage due to high defense."""
        # Arrange
        attacker_fighter = Fighter(hp=30, defense=2, power=5)
        attacker = Entity(10, 10, '@', mock_libtcod.white, 'Player', fighter=attacker_fighter)
        
        target_fighter = Fighter(hp=20, defense=10, power=5)
        target = Entity(15, 15, 'o', mock_libtcod.red, 'Orc', fighter=target_fighter)
        original_hp = target_fighter.hp
        
        # Act
        results = attacker_fighter.attack(target)
        
        # Assert
        assert len(results) >= 1
        # Target should take no damage
        assert target_fighter.hp == original_hp
        # Should still get attack message
        message_result = next((r for r in results if 'message' in r), None)
        assert message_result is not None

    def test_attack_target_without_fighter(self, mock_libtcod):
        """Test attacking a target without fighter component."""
        # Arrange
        attacker_fighter = Fighter(hp=30, defense=2, power=8)
        attacker = Entity(10, 10, '@', mock_libtcod.white, 'Player', fighter=attacker_fighter)
        
        target = Entity(15, 15, '!', mock_libtcod.violet, 'Potion')  # No fighter
        
        # Act & Assert
        with pytest.raises(AttributeError):
            attacker_fighter.attack(target)

    def test_attack_none_target(self, mock_libtcod):
        """Test attacking None target."""
        # Arrange
        attacker_fighter = Fighter(hp=30, defense=2, power=8)
        attacker = Entity(10, 10, '@', mock_libtcod.white, 'Player', fighter=attacker_fighter)
        
        # Act & Assert
        with pytest.raises(AttributeError):
            attacker_fighter.attack(None)

    def test_attack_zero_power(self, mock_libtcod):
        """Test attack with zero power."""
        # Arrange
        attacker_fighter = Fighter(hp=30, defense=2, power=0)
        attacker = Entity(10, 10, '@', mock_libtcod.white, 'Player', fighter=attacker_fighter)
        
        target_fighter = Fighter(hp=20, defense=3, power=5)
        target = Entity(15, 15, 'o', mock_libtcod.red, 'Orc', fighter=target_fighter)
        original_hp = target_fighter.hp
        
        # Act
        results = attacker_fighter.attack(target)
        
        # Assert
        assert len(results) >= 1
        # Target should take no damage (0 - 3 = 0, minimum 0)
        assert target_fighter.hp == original_hp

    def test_attack_negative_power(self, mock_libtcod):
        """Test attack with negative power."""
        # Arrange
        attacker_fighter = Fighter(hp=30, defense=2, power=-5)
        attacker = Entity(10, 10, '@', mock_libtcod.white, 'Player', fighter=attacker_fighter)
        
        target_fighter = Fighter(hp=20, defense=0, power=5)
        target = Entity(15, 15, 'o', mock_libtcod.red, 'Orc', fighter=target_fighter)
        original_hp = target_fighter.hp
        
        # Act
        results = attacker_fighter.attack(target)
        
        # Assert
        assert len(results) >= 1
        # Target should take no damage (negative damage = 0)
        assert target_fighter.hp == original_hp


class TestFighterHeal:
    """Test healing mechanics."""
    
    def test_heal_injured_fighter(self, mock_libtcod):
        """Test healing an injured fighter."""
        # Arrange
        fighter = Fighter(hp=30, defense=2, power=5)
        entity = Entity(10, 10, '@', mock_libtcod.white, 'Player', fighter=fighter)
        fighter.hp = 15  # Injured
        
        # Act
        fighter.heal(10)
        
        # Assert
        assert fighter.hp == 25

    def test_heal_to_max_hp(self, mock_libtcod):
        """Test healing beyond max HP."""
        # Arrange
        fighter = Fighter(hp=30, defense=2, power=5)
        entity = Entity(10, 10, '@', mock_libtcod.white, 'Player', fighter=fighter)
        fighter.hp = 25
        
        # Act
        fighter.heal(10)  # Would go to 35, but max is 30
        
        # Assert
        assert fighter.hp == 30  # Should cap at max_hp

    def test_heal_full_health_fighter(self, mock_libtcod):
        """Test healing a fighter already at full health."""
        # Arrange
        fighter = Fighter(hp=30, defense=2, power=5)
        entity = Entity(10, 10, '@', mock_libtcod.white, 'Player', fighter=fighter)
        
        # Act
        fighter.heal(5)
        
        # Assert
        assert fighter.hp == 30  # Should remain at max

    def test_heal_zero_amount(self, mock_libtcod):
        """Test healing with zero amount."""
        # Arrange
        fighter = Fighter(hp=30, defense=2, power=5)
        entity = Entity(10, 10, '@', mock_libtcod.white, 'Player', fighter=fighter)
        fighter.hp = 20
        
        # Act
        fighter.heal(0)
        
        # Assert
        assert fighter.hp == 20  # No change

    def test_heal_negative_amount(self, mock_libtcod):
        """Test healing with negative amount (actually damages due to current implementation)."""
        # Arrange
        fighter = Fighter(hp=30, defense=2, power=5)
        entity = Entity(10, 10, '@', mock_libtcod.white, 'Player', fighter=fighter)
        fighter.hp = 20
        
        # Act
        fighter.heal(-5)
        
        # Assert
        # NOTE: Current implementation allows negative healing (damage)
        assert fighter.hp == 15  # 20 + (-5) = 15

    def test_heal_massive_amount(self, mock_libtcod):
        """Test healing with massive amount."""
        # Arrange
        fighter = Fighter(hp=30, defense=2, power=5)
        entity = Entity(10, 10, '@', mock_libtcod.white, 'Player', fighter=fighter)
        fighter.hp = 1
        
        # Act
        fighter.heal(1000)
        
        # Assert
        assert fighter.hp == 30  # Should cap at max_hp


class TestFighterEdgeCases:
    """Test edge cases and error conditions for Fighter."""
    
    def test_fighter_massive_stats(self):
        """Test fighter with very large stats."""
        # Act
        fighter = Fighter(hp=999999, defense=999999, power=999999)
        
        # Assert
        assert fighter.max_hp == 999999
        assert fighter.hp == 999999
        assert fighter.defense == 999999
        assert fighter.power == 999999

    def test_fighter_without_owner_attack(self):
        """Test fighter attacking without being assigned to an entity."""
        # Arrange
        attacker_fighter = Fighter(hp=30, defense=2, power=8)
        # Don't assign to entity
        
        target_fighter = Fighter(hp=20, defense=3, power=5)
        target = Entity(15, 15, 'o', (255, 0, 0), 'Orc', fighter=target_fighter)
        
        # Act & Assert
        with pytest.raises(AttributeError):
            attacker_fighter.attack(target)

    def test_fighter_death_twice(self, mock_libtcod):
        """Test fighter death behavior (current implementation allows multiple death results)."""
        # Arrange
        fighter = Fighter(hp=10, defense=0, power=5)
        entity = Entity(10, 10, 'o', mock_libtcod.red, 'Orc', fighter=fighter)
        
        # Act
        results1 = fighter.take_damage(15)  # Should kill
        results2 = fighter.take_damage(15)  # Already dead
        
        # Assert
        assert len(results1) == 1  # Death result
        # NOTE: Current implementation doesn't prevent multiple death results
        assert len(results2) == 1  # Another death result (current behavior)
        assert fighter.hp <= 0

    def test_fighter_str_representation(self, mock_libtcod):
        """Test string representation of fighter."""
        # Arrange
        fighter = Fighter(hp=30, defense=2, power=5)
        entity = Entity(10, 10, '@', mock_libtcod.white, 'Player', fighter=fighter)
        
        # Act
        str_repr = str(fighter)
        
        # Assert - should not raise exception
        assert isinstance(str_repr, str)

    def test_fighter_hp_modification_direct(self, mock_libtcod):
        """Test directly modifying fighter HP."""
        # Arrange
        fighter = Fighter(hp=30, defense=2, power=5)
        entity = Entity(10, 10, '@', mock_libtcod.white, 'Player', fighter=fighter)
        
        # Act
        fighter.hp = 50  # Direct modification beyond max_hp
        
        # Assert
        assert fighter.hp == 50  # Should allow direct modification
        assert fighter.max_hp == 30  # max_hp unchanged

    def test_fighter_components_integration(self, mock_libtcod):
        """Test fighter integration with other components."""
        # Arrange
        fighter = Fighter(hp=30, defense=2, power=5)
        entity = Entity(10, 10, '@', mock_libtcod.white, 'Player', 
                       fighter=fighter, blocks=True)
        
        # Assert that fighter is properly integrated
        assert entity.fighter == fighter
        assert fighter.owner == entity
        assert entity.blocks is True
