"""Tests for Phase 19 Skeleton Shield Wall mechanics.

Tests:
- Shield wall AC bonus calculation (4-way adjacency)
- No cap on shield wall bonus
- Damage type modifiers (0.5x piercing, 1.5x bludgeoning)
- Formation AI behavior
- Bone pile spawning on death
"""

import pytest
from unittest.mock import Mock, patch

from entity import Entity
from components.fighter import Fighter
from components.equipment import Equipment
from components.equippable import Equippable
from equipment_slots import EquipmentSlots
from services.skeleton_service import (
    count_adjacent_skeleton_allies,
    update_skeleton_shield_wall_cache,
    _is_skeleton,
)


class TestShieldWallACBonus:
    """Tests for shield wall AC bonus calculation."""
    
    def test_skeleton_with_no_adjacent_allies_has_no_bonus(self):
        """Skeleton with no adjacent allies gets no shield wall bonus."""
        skeleton = self._create_skeleton(5, 5)
        entities = [skeleton]
        
        # Update cache
        update_skeleton_shield_wall_cache(skeleton, entities)
        
        # Check AC (base 10 + DEX 1 = 11, no shield wall bonus)
        assert skeleton.fighter.armor_class == 11
    
    def test_skeleton_with_one_adjacent_ally_gets_plus_one_ac(self):
        """Skeleton with 1 adjacent ally gets +1 AC."""
        skeleton1 = self._create_skeleton(5, 5)
        skeleton2 = self._create_skeleton(6, 5)  # East of skeleton1
        entities = [skeleton1, skeleton2]
        
        # Update cache
        update_skeleton_shield_wall_cache(skeleton1, entities)
        
        # Check AC (base 11 + 1 shield wall = 12)
        assert skeleton1.fighter.armor_class == 12
    
    def test_skeleton_with_two_adjacent_allies_gets_plus_two_ac(self):
        """Skeleton with 2 adjacent allies gets +2 AC."""
        skeleton1 = self._create_skeleton(5, 5)
        skeleton2 = self._create_skeleton(6, 5)  # East
        skeleton3 = self._create_skeleton(5, 6)  # South
        entities = [skeleton1, skeleton2, skeleton3]
        
        # Update cache
        update_skeleton_shield_wall_cache(skeleton1, entities)
        
        # Check AC (base 11 + 2 shield wall = 13)
        assert skeleton1.fighter.armor_class == 13
    
    def test_skeleton_with_four_adjacent_allies_gets_plus_four_ac(self):
        """Skeleton with 4 adjacent allies gets +4 AC (no cap)."""
        skeleton1 = self._create_skeleton(5, 5)
        skeleton2 = self._create_skeleton(6, 5)  # East
        skeleton3 = self._create_skeleton(4, 5)  # West
        skeleton4 = self._create_skeleton(5, 6)  # South
        skeleton5 = self._create_skeleton(5, 4)  # North
        entities = [skeleton1, skeleton2, skeleton3, skeleton4, skeleton5]
        
        # Update cache
        update_skeleton_shield_wall_cache(skeleton1, entities)
        
        # Check AC (base 11 + 4 shield wall = 15)
        assert skeleton1.fighter.armor_class == 15
    
    def test_shield_wall_uses_four_way_adjacency_not_eight_way(self):
        """Shield wall only counts 4-way adjacent (N/S/E/W), not diagonals."""
        skeleton1 = self._create_skeleton(5, 5)
        skeleton2 = self._create_skeleton(6, 6)  # Diagonal (SE)
        skeleton3 = self._create_skeleton(4, 4)  # Diagonal (NW)
        entities = [skeleton1, skeleton2, skeleton3]
        
        # Update cache
        update_skeleton_shield_wall_cache(skeleton1, entities)
        
        # Diagonals don't count - should have 0 adjacent
        assert skeleton1.fighter.armor_class == 11  # No bonus
    
    def test_shield_wall_only_counts_living_skeletons(self):
        """Dead skeletons don't contribute to shield wall."""
        skeleton1 = self._create_skeleton(5, 5)
        skeleton2 = self._create_skeleton(6, 5)  # East, alive
        skeleton3 = self._create_skeleton(5, 6)  # South, dead
        skeleton3.fighter.hp = 0  # Dead
        entities = [skeleton1, skeleton2, skeleton3]
        
        # Update cache
        update_skeleton_shield_wall_cache(skeleton1, entities)
        
        # Only 1 living adjacent skeleton
        assert skeleton1.fighter.armor_class == 12
    
    def test_non_skeleton_entities_dont_get_shield_wall_bonus(self):
        """Non-skeleton entities don't get shield wall bonus."""
        orc = self._create_orc(5, 5)
        skeleton = self._create_skeleton(6, 5)
        entities = [orc, skeleton]
        
        # Update cache (should do nothing for orc)
        update_skeleton_shield_wall_cache(orc, entities)
        
        # Orc has no shield wall bonus
        assert orc.fighter.armor_class == 10  # Base AC only
    
    def _create_skeleton(self, x, y):
        """Helper to create a skeleton entity."""
        skeleton = Entity(x, y, 's', (200, 200, 200), 'Skeleton', blocks=True)
        skeleton.fighter = Fighter(
            hp=20, defense=0, power=0, xp=30,
            damage_min=3, damage_max=5,
            strength=10, dexterity=12, constitution=10,
            accuracy=2, evasion=1
        )
        skeleton.fighter.owner = skeleton
        skeleton.equipment = Equipment(skeleton)
        
        # Mark as skeleton with shield wall ability
        skeleton.shieldwall_ac_per_adjacent = 1
        skeleton._cached_adjacent_skeleton_count = 0
        
        return skeleton
    
    def _create_orc(self, x, y):
        """Helper to create an orc entity (non-skeleton)."""
        orc = Entity(x, y, 'o', (63, 127, 63), 'Orc', blocks=True)
        orc.fighter = Fighter(
            hp=28, defense=0, power=0, xp=35,
            damage_min=4, damage_max=6,
            strength=14, dexterity=10, constitution=12
        )
        orc.fighter.owner = orc
        orc.equipment = Equipment(orc)
        
        return orc


class TestDamageTypeModifiers:
    """Tests for skeleton damage type modifiers."""
    
    def test_skeleton_takes_half_damage_from_piercing(self):
        """Skeletons take 50% damage from piercing weapons."""
        attacker = self._create_attacker_with_weapon("piercing")
        skeleton = self._create_skeleton_target()
        
        # Mock d20 roll to ensure hit (not crit)
        with patch('components.fighter.random.randint', return_value=15):
            with patch('components.fighter.show_hit'), patch('components.fighter.show_miss'):
                with patch('dice.roll_dice', return_value=6):  # 1d8 = 6
                    results = attacker.fighter.attack_d20(skeleton)
        
        # Base: 6 (weapon) + 2 (STR) = 8
        # Piercing modifier: 8 * 0.5 = 4
        damage_messages = [r for r in results if r.get('message') and 'damage' in str(r['message']).lower()]
        assert any('4 damage' in str(m['message']) for m in damage_messages), \
            "Skeleton should take 50% damage from piercing (expected 4)"
    
    def test_skeleton_takes_one_and_half_damage_from_bludgeoning(self):
        """Skeletons take 150% damage from bludgeoning weapons."""
        attacker = self._create_attacker_with_weapon("bludgeoning")
        skeleton = self._create_skeleton_target()
        
        # Mock d20 roll to ensure hit (not crit)
        with patch('components.fighter.random.randint', return_value=15):
            with patch('components.fighter.show_hit'), patch('components.fighter.show_miss'):
                with patch('dice.roll_dice', return_value=6):  # 1d8 = 6
                    results = attacker.fighter.attack_d20(skeleton)
        
        # Base: 6 (weapon) + 2 (STR) = 8
        # Bludgeoning modifier: 8 * 1.5 = 12
        damage_messages = [r for r in results if r.get('message') and 'damage' in str(r['message']).lower()]
        assert any('12 damage' in str(m['message']) for m in damage_messages), \
            "Skeleton should take 150% damage from bludgeoning (expected 12)"
    
    def test_skeleton_takes_normal_damage_from_slashing(self):
        """Skeletons take normal damage from slashing weapons."""
        attacker = self._create_attacker_with_weapon("slashing")
        skeleton = self._create_skeleton_target()
        
        # Mock d20 roll to ensure hit (not crit)
        with patch('components.fighter.random.randint', return_value=15):
            with patch('components.fighter.show_hit'), patch('components.fighter.show_miss'):
                with patch('dice.roll_dice', return_value=6):  # 1d8 = 6
                    results = attacker.fighter.attack_d20(skeleton)
        
        # Base: 6 (weapon) + 2 (STR) = 8
        # No modifier for slashing
        damage_messages = [r for r in results if r.get('message') and 'damage' in str(r['message']).lower()]
        assert any('8 damage' in str(m['message']) for m in damage_messages), \
            "Skeleton should take normal damage from slashing (expected 8)"
    
    def test_damage_type_modifier_applies_before_crit_multiplier(self):
        """Damage type modifier should apply before crit doubles damage."""
        attacker = self._create_attacker_with_weapon("bludgeoning")
        skeleton = self._create_skeleton_target()
        
        # Mock d20 roll for critical hit
        with patch('components.fighter.random.randint', return_value=20):  # Natural 20
            with patch('components.fighter.show_hit'), patch('components.fighter.show_miss'):
                with patch('dice.roll_dice', return_value=6):  # 1d8 = 6
                    results = attacker.fighter.attack_d20(skeleton)
        
        # Base: 6 (weapon) + 2 (STR) = 8
        # Bludgeoning modifier: 8 * 1.5 = 12
        # Crit: 12 * 2 = 24
        damage_messages = [r for r in results if r.get('message') and 'CRITICAL' in str(r['message'])]
        assert any('24 damage' in str(m['message']) for m in damage_messages), \
            "Bludgeoning crit should be (base*1.5)*2 = 24"
    
    def _create_attacker_with_weapon(self, damage_type):
        """Helper to create attacker with weapon of specified damage type."""
        attacker = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
        attacker.fighter = Fighter(
            hp=30, defense=2, power=3,
            strength=14, dexterity=14, constitution=14
        )
        attacker.fighter.owner = attacker
        attacker.equipment = Equipment(attacker)
        
        # Create weapon with damage type
        weapon = Entity(0, 0, '/', (200, 200, 200), 'Weapon', blocks=False)
        weapon.equippable = Equippable(
            slot=EquipmentSlots.MAIN_HAND,
            damage_dice="1d8",
            to_hit_bonus=0,
            damage_type=damage_type
        )
        weapon.equippable.owner = weapon
        
        weapon.components = Mock()
        weapon.components.has = Mock(return_value=True)
        
        attacker.equipment.main_hand = weapon
        return attacker
    
    def _create_skeleton_target(self):
        """Helper to create skeleton target with damage type modifiers."""
        skeleton = Entity(1, 1, 's', (200, 200, 200), 'Skeleton', blocks=True)
        skeleton.fighter = Fighter(
            hp=20, defense=0, power=0, xp=30,
            damage_min=3, damage_max=5,
            strength=10, dexterity=12, constitution=10
        )
        skeleton.fighter.owner = skeleton
        
        # Add damage type modifiers
        skeleton.damage_type_modifiers = {
            'piercing': 0.5,
            'bludgeoning': 1.5
        }
        
        return skeleton


class TestBonePileSpawn:
    """Tests for bone pile spawning on skeleton death."""
    
    def test_skeleton_death_calls_spawn_function(self):
        """Skeleton death should call _spawn_death_feature."""
        from death_functions import kill_monster, _spawn_death_feature
        
        skeleton = Entity(5, 5, 's', (200, 200, 200), 'Skeleton', blocks=True)
        skeleton.fighter = Fighter(hp=20, defense=0, power=0, xp=30)
        skeleton.fighter.owner = skeleton
        skeleton.death_spawns = "bone_pile"
        
        # Mock components
        skeleton.components = Mock()
        skeleton.components.has = Mock(return_value=True)
        skeleton.components.remove = Mock()
        skeleton.get_component_optional = Mock(return_value=None)
        
        # Mock _spawn_death_feature to verify it's called
        with patch('death_functions._spawn_death_feature') as mock_spawn:
            kill_monster(skeleton)
            
            # Verify _spawn_death_feature was called with correct args
            mock_spawn.assert_called_once()
            call_args = mock_spawn.call_args[0]
            assert call_args[0] == skeleton, "Should be called with skeleton"
    
    def test_spawn_death_feature_creates_bone_pile(self):
        """_spawn_death_feature should create bone pile for skeletons."""
        from death_functions import _spawn_death_feature
        
        skeleton = Entity(5, 5, 's', (200, 200, 200), 'Skeleton', blocks=True)
        skeleton.death_spawns = "bone_pile"
        
        # Mock the entity factory
        mock_bone_pile = Entity(5, 5, '%', (180, 180, 180), 'Bone Pile', blocks=False)
        
        with patch('death_functions.get_entity_factory') as mock_factory:
            mock_factory_instance = Mock()
            mock_factory_instance.create_map_feature = Mock(return_value=mock_bone_pile)
            mock_factory.return_value = mock_factory_instance
            
            # Call spawn function
            _spawn_death_feature(skeleton, None, [])
        
        # Check if bone pile was queued
        assert hasattr(skeleton, '_death_spawned_features'), \
            "Skeleton should have death spawned features"
        assert len(skeleton._death_spawned_features) == 1, \
            "Should have exactly one death spawned feature"


class TestSkeletonService:
    """Tests for skeleton service utility functions."""
    
    def test_count_adjacent_skeleton_allies_four_way(self):
        """count_adjacent_skeleton_allies should use 4-way adjacency."""
        skeleton1 = self._create_skeleton(5, 5)
        skeleton2 = self._create_skeleton(6, 5)  # East
        skeleton3 = self._create_skeleton(5, 6)  # South
        skeleton4 = self._create_skeleton(6, 6)  # Diagonal (should not count)
        entities = [skeleton1, skeleton2, skeleton3, skeleton4]
        
        count = count_adjacent_skeleton_allies(skeleton1, entities)
        assert count == 2, "Should only count 4-way adjacent (not diagonals)"
    
    def test_is_skeleton_recognizes_skeleton_by_attribute(self):
        """_is_skeleton should recognize skeletons by shieldwall attribute."""
        skeleton = self._create_skeleton(5, 5)
        assert _is_skeleton(skeleton), "Should recognize skeleton by shieldwall_ac_per_adjacent"
    
    def test_is_skeleton_returns_false_for_non_skeleton(self):
        """_is_skeleton should return False for non-skeleton entities."""
        orc = Entity(5, 5, 'o', (63, 127, 63), 'Orc', blocks=True)
        assert not _is_skeleton(orc), "Should not recognize orc as skeleton"
    
    def _create_skeleton(self, x, y):
        """Helper to create a skeleton entity."""
        skeleton = Entity(x, y, 's', (200, 200, 200), 'Skeleton', blocks=True)
        skeleton.fighter = Fighter(
            hp=20, defense=0, power=0, xp=30,
            damage_min=3, damage_max=5
        )
        skeleton.fighter.owner = skeleton
        skeleton.shieldwall_ac_per_adjacent = 1
        return skeleton
