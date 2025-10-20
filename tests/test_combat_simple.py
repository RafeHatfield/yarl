"""
Simple, focused combat tests.

Tests core combat mechanics with real entities.
Focuses on behavior, not implementation details.
"""

import pytest
from entity import Entity
from components.fighter import Fighter
from components.equipment import Equipment
from components.equippable import Equippable
from equipment_slots import EquipmentSlots


class TestBasicCombat:
    """Test basic combat mechanics with real entities."""

    def test_attack_reduces_target_hp(self):
        """Test that attacks reduce target HP."""
        # Create attacker
        attacker = Entity(0, 0, '@', (255, 255, 255), 'Attacker', blocks=True)
        attacker.fighter = Fighter(hp=100, defense=0, power=5)
        attacker.fighter.owner = attacker
        attacker.equipment = Equipment(attacker)
        
        # Create target
        target = Entity(1, 0, 'o', (255, 0, 0), 'Target', blocks=True)
        target.fighter = Fighter(hp=50, defense=0, power=0)
        target.fighter.owner = target
        target.equipment = Equipment(target)
        
        # Attack
        results = attacker.fighter.attack(target)
        
        # Target should have taken damage
        assert target.fighter.hp < 50, "Target should have taken damage"

    def test_attack_can_kill_target(self):
        """Test that sufficient damage kills target."""
        # Create powerful attacker
        attacker = Entity(0, 0, '@', (255, 255, 255), 'Attacker', blocks=True)
        attacker.fighter = Fighter(hp=100, defense=0, power=100)  # Very powerful
        attacker.fighter.owner = attacker
        attacker.equipment = Equipment(attacker)
        
        # Create weak target
        target = Entity(1, 0, 'o', (255, 0, 0), 'Target', blocks=True)
        target.fighter = Fighter(hp=10, defense=0, power=0)
        target.fighter.owner = target
        target.equipment = Equipment(target)
        
        # Attack should kill
        results = attacker.fighter.attack(target)
        
        # Check if death occurred (results should contain death info)
        has_death = any('dead' in result for result in results if isinstance(result, dict))
        assert has_death or target.fighter.hp <= 0, "Target should be dead"

    def test_defense_reduces_damage(self):
        """Test that defense reduces incoming damage."""
        # Create attacker with low power
        attacker = Entity(0, 0, '@', (255, 255, 255), 'Attacker', blocks=True)
        attacker.fighter = Fighter(hp=100, defense=0, power=3)
        attacker.fighter.owner = attacker
        attacker.equipment = Equipment(attacker)
        
        # Create target with no defense
        target_no_def = Entity(1, 0, 'o', (255, 0, 0), 'No Defense', blocks=True)
        target_no_def.fighter = Fighter(hp=50, defense=0, power=0)
        target_no_def.fighter.owner = target_no_def
        target_no_def.equipment = Equipment(target_no_def)
        
        # Create target with defense
        target_with_def = Entity(2, 0, 'o', (255, 0, 0), 'With Defense', blocks=True)
        target_with_def.fighter = Fighter(hp=50, defense=2, power=0)
        target_with_def.fighter.owner = target_with_def
        target_with_def.equipment = Equipment(target_with_def)
        
        # Attack both
        attacker.fighter.attack(target_no_def)
        attacker.fighter.attack(target_with_def)
        
        # Target with defense should have more HP remaining
        assert target_with_def.fighter.hp > target_no_def.fighter.hp, \
            "Defense should reduce damage taken"

    def test_equipped_weapon_affects_damage(self):
        """Test that equipped weapons change damage output."""
        # Create attacker
        attacker = Entity(0, 0, '@', (255, 255, 255), 'Attacker', blocks=True)
        attacker.fighter = Fighter(hp=100, defense=0, power=1)
        attacker.fighter.owner = attacker
        attacker.equipment = Equipment(attacker)
        
        # Create two identical targets
        target1 = Entity(1, 0, 'o', (255, 0, 0), 'Target1', blocks=True)
        target1.fighter = Fighter(hp=100, defense=0, power=0)
        target1.fighter.owner = target1
        target1.equipment = Equipment(target1)
        
        target2 = Entity(2, 0, 'o', (255, 0, 0), 'Target2', blocks=True)
        target2.fighter = Fighter(hp=100, defense=0, power=0)
        target2.fighter.owner = target2
        target2.equipment = Equipment(target2)
        
        # Attack with bare hands
        attacker.fighter.attack(target1)
        damage_unarmed = 100 - target1.fighter.hp
        
        # Equip a weapon with power bonus
        weapon = Entity(0, 0, '/', (255, 255, 255), 'Sword', blocks=False)
        weapon.equippable = Equippable(EquipmentSlots.MAIN_HAND, power_bonus=5)
        attacker.equipment.toggle_equip(weapon)
        
        # Attack with weapon
        attacker.fighter.attack(target2)
        damage_armed = 100 - target2.fighter.hp
        
        # Weapon should increase damage
        assert damage_armed > damage_unarmed, "Weapon should increase damage"


class TestCombatIntegrity:
    """Test combat system integrity."""
    
    def test_massive_overkill_damage_works(self):
        """Test that massive overkill damage doesn't break anything."""
        entity = Entity(0, 0, 'o', (255, 0, 0), 'Target', blocks=True)
        entity.fighter = Fighter(hp=10, defense=0, power=0)
        entity.fighter.owner = entity
        
        # Take massive damage
        results = entity.fighter.take_damage(1000)
        
        # Entity should be dead (HP <= 0)
        assert entity.fighter.hp <= 0, "Entity should be dead"
        
        # Should return death result
        has_death = any('dead' in result for result in results if isinstance(result, dict))
        assert has_death, "Should indicate death"

    def test_entities_start_with_correct_hp(self):
        """Test that entities initialize with correct HP."""
        entity = Entity(0, 0, 'o', (255, 0, 0), 'Test', blocks=True)
        entity.fighter = Fighter(hp=50, defense=0, power=5)
        entity.fighter.owner = entity
        
        assert entity.fighter.hp == 50
        assert entity.fighter.max_hp == 50

    def test_defense_cannot_make_attacks_heal(self):
        """Test that high defense doesn't cause healing."""
        # Create weak attacker
        attacker = Entity(0, 0, '@', (255, 255, 255), 'Attacker', blocks=True)
        attacker.fighter = Fighter(hp=100, defense=0, power=1)
        attacker.fighter.owner = attacker
        attacker.equipment = Equipment(attacker)
        
        # Create target with very high defense
        target = Entity(1, 0, 'o', (255, 0, 0), 'Tank', blocks=True)
        target.fighter = Fighter(hp=50, defense=100, power=0)
        target.fighter.owner = target
        target.equipment = Equipment(target)
        
        original_hp = target.fighter.hp
        
        # Attack
        attacker.fighter.attack(target)
        
        # Target HP should not increase
        assert target.fighter.hp <= original_hp, \
            "Defense shouldn't cause healing (HP should not increase)"

