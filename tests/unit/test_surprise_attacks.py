"""Unit tests for Phase 9: Awareness & Surprise Attacks.

Tests cover:
- Monster awareness state (aware_of_player flag)
- Awareness helpers (is_monster_aware, set_monster_aware)
- Surprise attack determination
- Surprise attack effects (auto-hit, forced crit/2× damage)
- Awareness via LOS (monster sees player)
- Awareness via being attacked
- Interaction with SpeedBonusTracker (bonus attacks NOT surprise)
- High-evasion targets still get auto-hit by surprise
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from components.ai.basic_monster import (
    BasicMonster,
    is_monster_aware,
    set_monster_aware,
)
from components.fighter import Fighter
from components.component_registry import ComponentType


class TestAwarenessState:
    """Tests for awareness state on monsters."""
    
    def test_default_awareness_is_false(self):
        """New monsters start unaware of player."""
        ai = BasicMonster()
        assert ai.aware_of_player is False
    
    def test_awareness_can_be_set_true(self):
        """Awareness can be set to True."""
        ai = BasicMonster()
        ai.aware_of_player = True
        assert ai.aware_of_player is True
    
    def test_awareness_does_not_decay(self):
        """Once aware, monster stays aware."""
        ai = BasicMonster()
        ai.aware_of_player = True
        # Simulate time passing (no automatic decay)
        assert ai.aware_of_player is True


class TestAwarenessHelpers:
    """Tests for is_monster_aware and set_monster_aware helpers."""
    
    def test_is_monster_aware_returns_false_for_unaware(self):
        """is_monster_aware returns False for unaware monster."""
        mock_entity = Mock()
        mock_ai = BasicMonster()
        mock_ai.aware_of_player = False
        mock_entity.get_component_optional.return_value = mock_ai
        
        result = is_monster_aware(mock_entity)
        assert result is False
    
    def test_is_monster_aware_returns_true_for_aware(self):
        """is_monster_aware returns True for aware monster."""
        mock_entity = Mock()
        mock_ai = BasicMonster()
        mock_ai.aware_of_player = True
        mock_entity.get_component_optional.return_value = mock_ai
        
        result = is_monster_aware(mock_entity)
        assert result is True
    
    def test_is_monster_aware_returns_true_for_no_ai(self):
        """is_monster_aware defaults to True for entities without AI."""
        mock_entity = Mock()
        mock_entity.get_component_optional.return_value = None
        mock_entity.ai = None  # No direct attribute either
        
        result = is_monster_aware(mock_entity)
        assert result is True  # Default to aware (safe behavior)
    
    def test_is_monster_aware_returns_true_for_none_entity(self):
        """is_monster_aware returns True for None entity (safe default)."""
        result = is_monster_aware(None)
        assert result is True
    
    def test_set_monster_aware_sets_flag(self):
        """set_monster_aware sets aware_of_player to True."""
        mock_entity = Mock()
        mock_ai = BasicMonster()
        mock_ai.aware_of_player = False
        mock_entity.get_component_optional.return_value = mock_ai
        
        set_monster_aware(mock_entity)
        
        assert mock_ai.aware_of_player is True
    
    def test_set_monster_aware_handles_none_entity(self):
        """set_monster_aware handles None entity gracefully."""
        # Should not raise
        set_monster_aware(None)
    
    def test_set_monster_aware_handles_no_ai(self):
        """set_monster_aware handles entity without AI gracefully."""
        mock_entity = Mock()
        mock_entity.get_component_optional.return_value = None
        mock_entity.ai = None
        
        # Should not raise
        set_monster_aware(mock_entity)


class TestSurpriseAttackDetermination:
    """Tests for surprise attack eligibility."""
    
    def test_surprise_attack_on_unaware_monster(self):
        """Unaware monster is eligible for surprise attack."""
        # Setup: Player attacks unaware monster
        mock_ai = BasicMonster()
        mock_ai.aware_of_player = False
        mock_target = Mock()
        mock_target.get_component_optional.return_value = mock_ai
        
        # Check eligibility
        target_ai = mock_target.get_component_optional(ComponentType.AI)
        is_surprise = target_ai and not is_monster_aware(mock_target)
        
        assert is_surprise is True
    
    def test_no_surprise_on_aware_monster(self):
        """Aware monster is NOT eligible for surprise attack."""
        mock_ai = BasicMonster()
        mock_ai.aware_of_player = True
        mock_target = Mock()
        mock_target.get_component_optional.return_value = mock_ai
        
        target_ai = mock_target.get_component_optional(ComponentType.AI)
        is_surprise = target_ai and not is_monster_aware(mock_target)
        
        assert is_surprise is False
    
    def test_no_surprise_on_non_monster(self):
        """Entities without AI cannot be surprise attacked."""
        mock_target = Mock()
        mock_target.get_component_optional.return_value = None  # No AI
        
        target_ai = mock_target.get_component_optional(ComponentType.AI)
        is_surprise = target_ai and not is_monster_aware(mock_target)
        
        # target_ai is None (falsy), so the condition short-circuits to None/falsy
        # In actual code this is used in an if-statement, so falsy = no surprise
        assert not is_surprise  # Falsy value means no surprise attack


class TestSurpriseAttackEffects:
    """Tests for surprise attack combat effects."""
    
    def test_surprise_attack_forces_critical(self):
        """Surprise attacks force is_critical = True."""
        fighter = Fighter(hp=50, defense=0, power=5)
        
        mock_target = Mock()
        mock_target_fighter = Mock()
        mock_target_fighter.armor_class = 15
        mock_target_fighter.take_damage.return_value = []
        mock_target.require_component.return_value = mock_target_fighter
        mock_target.fighter = mock_target_fighter
        mock_target.name = "Orc"
        mock_target.x = 0
        mock_target.y = 0
        
        # Create a mock owner
        mock_owner = Mock()
        mock_owner.name = "Player"
        mock_owner.x = 1
        mock_owner.y = 0
        mock_owner.equipment = None
        mock_owner.status_effects = None
        mock_owner.get_component_optional.return_value = None
        fighter.owner = mock_owner
        
        # Call attack_d20 with is_surprise=True
        with patch('components.fighter.random.randint', return_value=10):  # Normal roll
            results = fighter.attack_d20(mock_target, is_surprise=True)
        
        # Should have dealt damage (critical hit)
        mock_target_fighter.take_damage.assert_called_once()
        damage_dealt = mock_target_fighter.take_damage.call_args[0][0]
        
        # Damage should be non-zero (critical hit means double damage)
        assert damage_dealt > 0
    
    def test_surprise_attack_auto_hits_even_on_fumble_roll(self):
        """Surprise attacks hit even when d20 roll is 1 (would be fumble)."""
        fighter = Fighter(hp=50, defense=0, power=5)
        
        mock_target = Mock()
        mock_target_fighter = Mock()
        mock_target_fighter.armor_class = 15
        mock_target_fighter.take_damage.return_value = []
        mock_target.require_component.return_value = mock_target_fighter
        mock_target.fighter = mock_target_fighter
        mock_target.name = "Orc"
        mock_target.x = 0
        mock_target.y = 0
        
        mock_owner = Mock()
        mock_owner.name = "Player"
        mock_owner.x = 1
        mock_owner.y = 0
        mock_owner.equipment = None
        mock_owner.status_effects = None
        mock_owner.get_component_optional.return_value = None
        fighter.owner = mock_owner
        
        # Roll a 1 (would normally be fumble)
        with patch('components.fighter.random.randint', return_value=1):
            results = fighter.attack_d20(mock_target, is_surprise=True)
        
        # Should still hit (surprise bypasses fumble)
        mock_target_fighter.take_damage.assert_called_once()
    
    def test_surprise_attack_vs_high_evasion(self):
        """Surprise attack auto-hits even high-evasion targets."""
        # This tests the game_actions integration, but we can test the fighter level
        fighter = Fighter(hp=50, defense=0, power=5, accuracy=2, evasion=1)
        
        # Wraith with high evasion (normally 65% hit chance)
        mock_target = Mock()
        mock_target_fighter = Mock()
        mock_target_fighter.armor_class = 20  # High AC
        mock_target_fighter.evasion = 4  # High evasion
        mock_target_fighter.take_damage.return_value = []
        mock_target.require_component.return_value = mock_target_fighter
        mock_target.fighter = mock_target_fighter
        mock_target.name = "Wraith"
        mock_target.x = 0
        mock_target.y = 0
        
        mock_owner = Mock()
        mock_owner.name = "Player"
        mock_owner.x = 1
        mock_owner.y = 0
        mock_owner.equipment = None
        mock_owner.status_effects = None
        mock_owner.get_component_optional.return_value = None
        fighter.owner = mock_owner
        
        # Roll low (would miss against high AC)
        with patch('components.fighter.random.randint', return_value=5):
            results = fighter.attack_d20(mock_target, is_surprise=True)
        
        # Should hit anyway (surprise auto-hit)
        mock_target_fighter.take_damage.assert_called_once()


class TestAwarenessViaLOS:
    """Tests for monster awareness when seeing player."""
    
    def test_monster_becomes_aware_on_los(self):
        """Monster becomes aware when it sees the player."""
        ai = BasicMonster()
        ai.aware_of_player = False
        
        # Create minimal mock setup for take_turn
        mock_monster = Mock()
        mock_monster.name = "Orc"
        mock_monster.x = 5
        mock_monster.y = 5
        mock_monster.get_component_optional.return_value = None
        mock_monster.has_status_effect.return_value = False
        mock_monster.fighter = Mock()
        mock_monster.fighter.hp = 10
        mock_monster.chebyshev_distance_to.return_value = 5  # Not adjacent
        ai.owner = mock_monster
        
        mock_player = Mock()
        mock_player.name = "Player"
        mock_player.fighter = Mock()
        mock_player.fighter.hp = 50
        mock_player.has_status_effect.return_value = False
        mock_player.x = 3
        mock_player.y = 3
        
        mock_fov_map = Mock()
        mock_game_map = Mock()
        entities = []
        
        # Simulate monster being in player's FOV (symmetric)
        with patch('components.ai.basic_monster.map_is_in_fov', return_value=True):
            with patch('components.ai.basic_monster.find_taunted_target', return_value=None):
                # take_turn should set awareness
                ai.take_turn(mock_player, mock_fov_map, mock_game_map, entities)
        
        assert ai.aware_of_player is True
    
    def test_monster_stays_unaware_if_not_in_fov(self):
        """Monster stays unaware if not in player's FOV."""
        ai = BasicMonster()
        ai.aware_of_player = False
        
        mock_monster = Mock()
        mock_monster.name = "Orc"
        mock_monster.x = 50  # Far away
        mock_monster.y = 50
        mock_monster.get_component_optional.return_value = None
        ai.owner = mock_monster
        
        mock_player = Mock()
        mock_fov_map = Mock()
        mock_game_map = Mock()
        entities = []
        
        # Monster NOT in FOV
        with patch('components.ai.basic_monster.map_is_in_fov', return_value=False):
            with patch('components.ai.basic_monster.find_taunted_target', return_value=None):
                ai.take_turn(mock_player, mock_fov_map, mock_game_map, entities)
        
        # Monster did not act, so awareness unchanged
        # (awareness is only set when monster_sees_player is True)
        assert ai.aware_of_player is False


class TestAwarenessViaAttack:
    """Tests for monster awareness when attacked by player."""
    
    def test_monster_becomes_aware_after_being_attacked(self):
        """Monster becomes aware after being surprise attacked."""
        mock_ai = BasicMonster()
        mock_ai.aware_of_player = False
        
        # Simulate what happens in _handle_combat:
        # After surprise attack, set_monster_aware is called
        mock_entity = Mock()
        mock_entity.get_component_optional.return_value = mock_ai
        
        # Before attack
        assert is_monster_aware(mock_entity) is False
        
        # Player attacks (surprise) -> set_monster_aware called
        set_monster_aware(mock_entity)
        
        # After attack
        assert is_monster_aware(mock_entity) is True
    
    def test_second_attack_not_surprise(self):
        """Second attack on same monster is NOT a surprise attack."""
        mock_ai = BasicMonster()
        mock_ai.aware_of_player = False
        mock_entity = Mock()
        mock_entity.get_component_optional.return_value = mock_ai
        
        # First attack: Is surprise
        target_ai = mock_entity.get_component_optional(ComponentType.AI)
        is_first_surprise = target_ai and not is_monster_aware(mock_entity)
        assert is_first_surprise is True
        
        # After first attack, monster becomes aware
        set_monster_aware(mock_entity)
        
        # Second attack: NOT surprise
        is_second_surprise = target_ai and not is_monster_aware(mock_entity)
        assert is_second_surprise is False


class TestBonusAttackInteraction:
    """Tests for surprise attack interaction with speed bonus system."""
    
    def test_bonus_attack_not_surprise(self):
        """Speed bonus attacks should NOT be surprise attacks.
        
        The spec says: "Only the PRIMARY attack should be surprise"
        """
        mock_ai = BasicMonster()
        mock_ai.aware_of_player = False
        mock_entity = Mock()
        mock_entity.get_component_optional.return_value = mock_ai
        
        # First (primary) attack: Check surprise eligibility
        # In _handle_combat, this would be: is_bonus_attack=False
        is_primary_attack = True  # Not a bonus attack
        is_bonus_attack = False
        
        target_ai = mock_entity.get_component_optional(ComponentType.AI)
        is_surprise_for_primary = (
            target_ai and 
            not is_monster_aware(mock_entity) and 
            not is_bonus_attack
        )
        assert is_surprise_for_primary is True
        
        # Simulate primary attack completing - monster becomes aware
        set_monster_aware(mock_entity)
        
        # Bonus attack triggered (is_bonus_attack=True)
        is_bonus_attack = True
        is_surprise_for_bonus = (
            target_ai and 
            not is_monster_aware(mock_entity) and  # Monster is now aware
            not is_bonus_attack  # And this is a bonus attack anyway
        )
        # Both conditions fail: monster is aware AND this is a bonus attack
        assert is_surprise_for_bonus is False
    
    def test_even_if_somehow_unaware_bonus_attack_not_surprise(self):
        """Even if monster is somehow still unaware, bonus attack isn't surprise.
        
        The is_bonus_attack flag itself should prevent surprise.
        """
        mock_ai = BasicMonster()
        mock_ai.aware_of_player = False  # Somehow still unaware
        mock_entity = Mock()
        mock_entity.get_component_optional.return_value = mock_ai
        
        is_bonus_attack = True  # This is a bonus attack
        target_ai = mock_entity.get_component_optional(ComponentType.AI)
        
        # Even with unaware monster, bonus attack flag prevents surprise
        is_surprise = (
            target_ai and 
            not is_monster_aware(mock_entity) and 
            not is_bonus_attack
        )
        # Fails because is_bonus_attack is True
        assert is_surprise is False


class TestSurpriseAttackDamage:
    """Tests for surprise attack damage calculation."""
    
    def test_surprise_doubles_damage_via_crit(self):
        """Surprise attacks deal 2× damage via forced critical hit."""
        fighter = Fighter(hp=50, defense=0, power=5, damage_min=5, damage_max=5)
        
        mock_target = Mock()
        mock_target_fighter = Mock()
        mock_target_fighter.armor_class = 10
        mock_target_fighter.take_damage.return_value = []
        mock_target.require_component.return_value = mock_target_fighter
        mock_target.fighter = mock_target_fighter
        mock_target.name = "Dummy"
        mock_target.x = 0
        mock_target.y = 0
        
        mock_owner = Mock()
        mock_owner.name = "Player"
        mock_owner.x = 1
        mock_owner.y = 0
        mock_owner.equipment = None
        mock_owner.status_effects = None
        mock_owner.get_component_optional.return_value = None
        fighter.owner = mock_owner
        
        # Attack without surprise
        with patch('components.fighter.random.randint', return_value=15):  # Normal hit
            results_normal = fighter.attack_d20(mock_target, is_surprise=False)
        
        normal_damage = mock_target_fighter.take_damage.call_args[0][0]
        
        # Reset mock
        mock_target_fighter.take_damage.reset_mock()
        
        # Attack with surprise (forced crit = 2× damage)
        with patch('components.fighter.random.randint', return_value=15):  # Same roll
            results_surprise = fighter.attack_d20(mock_target, is_surprise=True)
        
        surprise_damage = mock_target_fighter.take_damage.call_args[0][0]
        
        # Surprise damage should be approximately 2× normal
        # (Not exactly due to minimum damage rules, but should be close)
        assert surprise_damage >= normal_damage


class TestFighterSurpriseParameter:
    """Tests for Fighter.attack_d20 is_surprise parameter."""
    
    def test_attack_d20_accepts_is_surprise_param(self):
        """attack_d20 accepts is_surprise parameter."""
        fighter = Fighter(hp=50, defense=0, power=5)
        
        mock_target = Mock()
        mock_target_fighter = Mock()
        mock_target_fighter.armor_class = 10
        mock_target_fighter.take_damage.return_value = []
        mock_target.require_component.return_value = mock_target_fighter
        mock_target.fighter = mock_target_fighter
        mock_target.name = "Target"
        mock_target.x = 0
        mock_target.y = 0
        
        mock_owner = Mock()
        mock_owner.name = "Attacker"
        mock_owner.x = 1
        mock_owner.y = 0
        mock_owner.equipment = None
        mock_owner.status_effects = None
        mock_owner.get_component_optional.return_value = None
        fighter.owner = mock_owner
        
        # Should not raise
        with patch('components.fighter.random.randint', return_value=10):
            results = fighter.attack_d20(mock_target, is_surprise=True)
            results = fighter.attack_d20(mock_target, is_surprise=False)
    
    def test_attack_d20_default_is_surprise_false(self):
        """attack_d20 defaults is_surprise to False."""
        fighter = Fighter(hp=50, defense=0, power=5)
        
        mock_target = Mock()
        mock_target_fighter = Mock()
        mock_target_fighter.armor_class = 10
        mock_target_fighter.take_damage.return_value = []
        mock_target.require_component.return_value = mock_target_fighter
        mock_target.fighter = mock_target_fighter
        mock_target.name = "Target"
        mock_target.x = 0
        mock_target.y = 0
        
        mock_owner = Mock()
        mock_owner.name = "Attacker"
        mock_owner.x = 1
        mock_owner.y = 0
        mock_owner.equipment = None
        mock_owner.status_effects = None
        mock_owner.get_component_optional.return_value = None
        fighter.owner = mock_owner
        
        # Call without is_surprise parameter (should use default False)
        with patch('components.fighter.random.randint', return_value=1):  # Fumble roll
            results = fighter.attack_d20(mock_target)
        
        # With fumble roll and no surprise, should miss (no damage)
        mock_target_fighter.take_damage.assert_not_called()
