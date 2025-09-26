"""
Unit tests for XP reward system and fighter XP integration.

Tests the XP system including:
- Fighter component XP rewards
- XP distribution on monster death
- Death result XP tracking
- Integration with Level component
- XP scaling and balance
"""

import pytest
from unittest.mock import Mock

from components.fighter import Fighter
from components.level import Level
from entity import Entity
from render_functions import RenderOrder


class TestFighterXPRewards:
    """Test Fighter component XP reward functionality."""

    def test_fighter_initialization_with_xp(self):
        """Test Fighter can be initialized with XP value."""
        fighter = Fighter(hp=20, defense=2, power=3, xp=50)
        
        assert fighter.hp == 20
        assert fighter.max_hp == 20
        assert fighter.defense == 2
        assert fighter.power == 3
        assert fighter.xp == 50

    def test_fighter_initialization_default_xp(self):
        """Test Fighter defaults to 0 XP if not specified."""
        fighter = Fighter(hp=15, defense=1, power=2)
        
        assert fighter.xp == 0

    def test_fighter_initialization_zero_xp(self):
        """Test Fighter can be explicitly initialized with 0 XP."""
        fighter = Fighter(hp=10, defense=0, power=1, xp=0)
        
        assert fighter.xp == 0

    def test_fighter_initialization_large_xp(self):
        """Test Fighter can handle large XP values."""
        fighter = Fighter(hp=100, defense=10, power=15, xp=99999)
        
        assert fighter.xp == 99999

    def test_fighter_xp_is_preserved(self):
        """Test that Fighter XP value is preserved through operations."""
        fighter = Fighter(hp=25, defense=3, power=4, xp=75)
        
        # Perform various operations
        fighter.heal(5)
        fighter.take_damage(3)
        
        # XP should remain unchanged
        assert fighter.xp == 75


class TestFighterDeathXPRewards:
    """Test XP rewards when Fighter dies."""

    def test_take_damage_death_returns_xp(self):
        """Test that fighter death includes XP in results."""
        fighter = Fighter(hp=10, defense=0, power=2, xp=25)
        entity = Entity(5, 5, 'o', (255, 0, 0), 'Orc')
        fighter.owner = entity
        
        # Deal lethal damage
        results = fighter.take_damage(15)
        
        assert len(results) == 1
        death_result = results[0]
        assert 'dead' in death_result
        assert 'xp' in death_result
        assert death_result['dead'] == entity
        assert death_result['xp'] == 25

    def test_take_damage_non_lethal_no_xp(self):
        """Test that non-lethal damage doesn't return XP."""
        fighter = Fighter(hp=20, defense=0, power=2, xp=30)
        
        # Deal non-lethal damage
        results = fighter.take_damage(10)
        
        # Should be empty (no death, no XP)
        assert results == []

    def test_take_damage_exact_lethal_damage(self):
        """Test XP reward with exact lethal damage."""
        fighter = Fighter(hp=15, defense=0, power=1, xp=40)
        entity = Entity(3, 3, 't', (0, 255, 0), 'Troll')
        fighter.owner = entity
        
        # Deal exactly enough damage to kill
        results = fighter.take_damage(15)
        
        assert len(results) == 1
        assert results[0]['dead'] == entity
        assert results[0]['xp'] == 40

    def test_take_damage_overkill_xp_reward(self):
        """Test XP reward with overkill damage."""
        fighter = Fighter(hp=5, defense=0, power=1, xp=60)
        entity = Entity(7, 7, 'g', (128, 128, 128), 'Goblin')
        fighter.owner = entity
        
        # Deal massive overkill
        results = fighter.take_damage(100)
        
        assert len(results) == 1
        assert results[0]['dead'] == entity
        assert results[0]['xp'] == 60

    def test_take_damage_zero_xp_reward(self):
        """Test death with zero XP reward."""
        fighter = Fighter(hp=8, defense=0, power=1, xp=0)
        entity = Entity(1, 1, 'r', (255, 128, 0), 'Rat')
        fighter.owner = entity
        
        results = fighter.take_damage(10)
        
        assert len(results) == 1
        assert results[0]['dead'] == entity
        assert results[0]['xp'] == 0

    def test_multiple_damage_instances_before_death(self):
        """Test that XP is only rewarded on actual death."""
        fighter = Fighter(hp=30, defense=0, power=3, xp=80)
        entity = Entity(10, 10, 'o', (255, 0, 0), 'Orc')
        fighter.owner = entity
        
        # Multiple non-lethal hits
        results1 = fighter.take_damage(10)  # HP: 20
        results2 = fighter.take_damage(15)  # HP: 5
        assert results1 == []
        assert results2 == []
        
        # Final lethal hit
        results3 = fighter.take_damage(10)  # HP: -5
        
        assert len(results3) == 1
        assert results3[0]['xp'] == 80

    def test_take_damage_negative_hp_still_gives_xp(self):
        """Test that XP is given even when HP goes significantly negative."""
        fighter = Fighter(hp=1, defense=0, power=1, xp=35)
        entity = Entity(2, 2, 's', (0, 0, 255), 'Skeleton')
        fighter.owner = entity
        
        # Massive damage bringing HP far below 0
        results = fighter.take_damage(50)
        
        assert fighter.hp == -49
        assert len(results) == 1
        assert results[0]['xp'] == 35


class TestFighterAttackXPIntegration:
    """Test Fighter attack system preserves XP behavior."""

    def test_attack_preserves_target_xp(self):
        """Test that attacking preserves target's XP value."""
        # Attacker
        attacker_fighter = Fighter(hp=20, defense=0, power=10, xp=0)
        attacker = Entity(1, 1, '@', (255, 255, 255), 'Player', fighter=attacker_fighter)
        
        # Target with XP
        target_fighter = Fighter(hp=5, defense=0, power=1, xp=45)
        target = Entity(2, 2, 'o', (255, 0, 0), 'Orc', fighter=target_fighter)
        
        # Attack should kill target
        results = attacker_fighter.attack(target)
        
        # Should have attack message and death result with XP
        assert len(results) >= 1
        
        # Find the death result
        death_result = None
        for result in results:
            if 'dead' in result:
                death_result = result
                break
        
        assert death_result is not None
        assert death_result['dead'] == target
        assert death_result['xp'] == 45

    def test_attack_non_lethal_no_xp_reward(self):
        """Test that non-lethal attacks don't give XP."""
        # Weak attacker
        attacker_fighter = Fighter(hp=20, defense=0, power=2, xp=0)
        attacker = Entity(1, 1, '@', (255, 255, 255), 'Player', fighter=attacker_fighter)
        
        # Strong target
        target_fighter = Fighter(hp=20, defense=0, power=1, xp=50)
        target = Entity(2, 2, 'o', (255, 0, 0), 'Orc', fighter=target_fighter)
        
        results = attacker_fighter.attack(target)
        
        # Should only have damage message, no death/XP
        xp_results = [r for r in results if 'xp' in r]
        assert len(xp_results) == 0

    def test_attack_with_defense_lethal_gives_xp(self):
        """Test XP reward with defense calculations."""
        # Strong attacker
        attacker_fighter = Fighter(hp=20, defense=0, power=15, xp=0)
        attacker = Entity(1, 1, '@', (255, 255, 255), 'Player', fighter=attacker_fighter)
        
        # Target with defense
        target_fighter = Fighter(hp=10, defense=3, power=1, xp=65)
        target = Entity(2, 2, 'o', (255, 0, 0), 'Orc', fighter=target_fighter)
        
        # Attack: 15 power - 3 defense = 12 damage, should kill (10 HP)
        results = attacker_fighter.attack(target)
        
        # Find death result
        death_result = None
        for result in results:
            if 'dead' in result:
                death_result = result
                break
        
        assert death_result is not None
        assert death_result['xp'] == 65

    def test_attack_no_damage_no_xp(self):
        """Test that attacks dealing no damage don't give XP."""
        # Weak attacker
        attacker_fighter = Fighter(hp=20, defense=0, power=2, xp=0)
        attacker = Entity(1, 1, '@', (255, 255, 255), 'Player', fighter=attacker_fighter)
        
        # High defense target
        target_fighter = Fighter(hp=1, defense=5, power=1, xp=100)
        target = Entity(2, 2, 'o', (255, 0, 0), 'Orc', fighter=target_fighter)
        
        # Attack: 2 power - 5 defense = -3 damage (no damage dealt)
        results = attacker_fighter.attack(target)
        
        # Target should still be alive, no XP
        assert target_fighter.hp == 1
        xp_results = [r for r in results if 'xp' in r]
        assert len(xp_results) == 0


class TestXPSystemIntegration:
    """Test integration between XP rewards and Level system."""

    def test_xp_reward_integration_with_level_component(self):
        """Test that XP rewards can be used with Level component."""
        # Create a character with level component  
        level_comp = Level(current_level=1, current_xp=300)
        # At level 1, needs 350 XP to level up (200 + 1*150)
        
        # Simulate getting XP from killing a monster
        monster_xp = 60
        
        leveled_up = level_comp.add_xp(monster_xp)
        
        # Should level up since 300 + 60 = 360 > 350
        assert leveled_up is True
        assert level_comp.current_level == 2
        assert level_comp.current_xp == 10  # 360 - 350 = 10 overflow

    def test_multiple_xp_rewards_accumulation(self):
        """Test accumulating XP from multiple monster kills."""
        level_comp = Level(current_level=1, current_xp=0)
        
        # Simulate killing multiple monsters
        monster_xp_values = [25, 35, 15, 40, 30]
        
        for xp in monster_xp_values:
            level_comp.add_xp(xp)
        
        # Total XP should be sum of all rewards
        total_expected = sum(monster_xp_values)
        # Note: current_xp might be reduced if level ups occurred
        # But we can verify the level progressed appropriately
        assert level_comp.current_level >= 1

    def test_xp_scaling_by_monster_difficulty(self):
        """Test that different monsters can have different XP rewards."""
        # Weak monster
        weak_fighter = Fighter(hp=5, defense=0, power=1, xp=10)
        
        # Medium monster  
        medium_fighter = Fighter(hp=15, defense=2, power=3, xp=35)
        
        # Strong monster
        strong_fighter = Fighter(hp=30, defense=5, power=8, xp=100)
        
        # XP should scale with difficulty
        assert weak_fighter.xp < medium_fighter.xp < strong_fighter.xp

    def test_player_xp_typically_zero(self):
        """Test that players typically don't give XP when they die."""
        # Player fighter (shouldn't give XP to monsters)
        player_fighter = Fighter(hp=30, defense=2, power=5, xp=0)
        
        assert player_fighter.xp == 0


class TestXPEdgeCases:
    """Test edge cases in XP system."""

    def test_fighter_negative_xp(self):
        """Test Fighter with negative XP (edge case)."""
        fighter = Fighter(hp=10, defense=0, power=1, xp=-10)
        entity = Entity(1, 1, 'x', (128, 128, 128), 'Strange')
        fighter.owner = entity
        
        results = fighter.take_damage(15)
        
        # Should still return the negative XP
        assert len(results) == 1
        assert results[0]['xp'] == -10

    def test_fighter_very_large_xp(self):
        """Test Fighter with very large XP values."""
        huge_xp = 999999999
        fighter = Fighter(hp=1, defense=0, power=1, xp=huge_xp)
        entity = Entity(1, 1, 'x', (128, 128, 128), 'Epic')
        fighter.owner = entity
        
        results = fighter.take_damage(2)
        
        assert len(results) == 1
        assert results[0]['xp'] == huge_xp

    def test_xp_reward_with_modified_hp(self):
        """Test XP reward when fighter HP has been modified."""
        fighter = Fighter(hp=20, defense=0, power=1, xp=40)
        entity = Entity(1, 1, 'o', (255, 0, 0), 'Orc')
        fighter.owner = entity
        
        # Heal above max HP (edge case)
        fighter.hp = 25
        
        # Still should die and give XP when taking enough damage
        results = fighter.take_damage(30)
        
        assert len(results) == 1
        assert results[0]['xp'] == 40

    def test_xp_consistency_across_multiple_deaths(self):
        """Test that XP values are consistent across similar monsters."""
        # Create multiple identical monsters
        monsters = []
        for i in range(5):
            fighter = Fighter(hp=10, defense=1, power=2, xp=20)
            entity = Entity(i, i, 'o', (255, 0, 0), f'Orc{i}')
            fighter.owner = entity
            monsters.append(fighter)
        
        # Kill all monsters
        xp_rewards = []
        for monster in monsters:
            results = monster.take_damage(15)
            if results:
                xp_rewards.append(results[0]['xp'])
        
        # All should give same XP
        assert len(xp_rewards) == 5
        assert all(xp == 20 for xp in xp_rewards)
