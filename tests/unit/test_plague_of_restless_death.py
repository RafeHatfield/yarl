"""Unit tests for Phase 10: Plague of Restless Death.

Tests cover:
- PlagueOfRestlessDeathEffect status effect
- Plague damage mechanics (can't kill, stops at 1 HP)
- Revenant zombie stat calculations
- Corporeal flesh eligibility checking
- Reanimation scheduling and execution
"""

import pytest
import math
from unittest.mock import Mock, MagicMock, patch

from components.status_effects import PlagueOfRestlessDeathEffect, StatusEffectManager
from components.component_registry import ComponentType
from components.faction import Faction


class TestPlagueOfRestlessDeathEffect:
    """Tests for the PlagueOfRestlessDeathEffect status effect."""
    
    def create_mock_entity(self, name="Test Orc", hp=20, max_hp=20, 
                          damage_min=4, damage_max=6, accuracy=2, evasion=1,
                          defense=0, power=0):
        """Helper to create a mock entity with fighter stats."""
        entity = Mock()
        entity.name = name
        entity.char = 'o'
        entity.color = (63, 127, 63)
        entity.x, entity.y = 5, 5
        
        fighter = Mock()
        fighter.hp = hp
        fighter.max_hp = max_hp
        fighter.damage_min = damage_min
        fighter.damage_max = damage_max
        fighter.accuracy = accuracy
        fighter.evasion = evasion
        fighter.base_defense = defense
        fighter.power = power
        
        entity.get_component_optional = Mock(return_value=fighter)
        entity.fighter = fighter
        
        return entity
    
    def test_effect_creation(self):
        """Effect should be created with correct attributes."""
        owner = self.create_mock_entity()
        
        effect = PlagueOfRestlessDeathEffect(
            duration=20,
            owner=owner,
            damage_per_turn=1
        )
        
        assert effect.name == "plague_of_restless_death"
        assert effect.duration == 20
        assert effect.damage_per_turn == 1
        assert effect.owner == owner
    
    def test_effect_apply_captures_stats(self):
        """Applying effect should capture original stats."""
        owner = self.create_mock_entity(hp=20, max_hp=20, damage_min=4, 
                                         damage_max=6, accuracy=2, evasion=1)
        
        effect = PlagueOfRestlessDeathEffect(
            duration=20,
            owner=owner,
            damage_per_turn=1
        )
        
        effect.apply()
        
        assert effect.original_stats is not None
        assert effect.original_stats['max_hp'] == 20
        assert effect.original_stats['damage_min'] == 4
        assert effect.original_stats['damage_max'] == 6
        assert effect.original_stats['accuracy'] == 2
        assert effect.original_stats['evasion'] == 1
    
    def test_plague_damage_never_kills(self):
        """Plague damage should never reduce HP below 1."""
        owner = self.create_mock_entity(hp=2, max_hp=20)
        fighter = owner.get_component_optional(ComponentType.FIGHTER)
        
        effect = PlagueOfRestlessDeathEffect(
            duration=20,
            owner=owner,
            damage_per_turn=5  # High damage
        )
        effect.apply()
        
        # Process turn - should not reduce below 1
        results = effect.process_turn_start()
        
        # HP should be exactly 1, not 0 or negative
        assert fighter.hp == 1
    
    def test_plague_damage_normal_when_hp_high(self):
        """Plague should deal full damage when HP is high enough."""
        owner = self.create_mock_entity(hp=20, max_hp=20)
        fighter = owner.get_component_optional(ComponentType.FIGHTER)
        
        effect = PlagueOfRestlessDeathEffect(
            duration=20,
            owner=owner,
            damage_per_turn=2
        )
        effect.apply()
        
        # Process turn
        results = effect.process_turn_start()
        
        # HP should decrease by damage_per_turn
        assert fighter.hp == 18


class TestRevenantStatCalculations:
    """Tests for revenant zombie stat transformations."""
    
    def test_revenant_hp_doubled(self):
        """Revenant should have double the original max HP."""
        owner = Mock()
        owner.name = "Orc Warrior"
        owner.char = 'o'
        owner.color = (63, 127, 63)
        
        fighter = Mock()
        fighter.max_hp = 20
        fighter.damage_min = 4
        fighter.damage_max = 6
        fighter.accuracy = 2
        fighter.evasion = 1
        fighter.base_defense = 0
        fighter.power = 0
        owner.get_component_optional = Mock(return_value=fighter)
        
        effect = PlagueOfRestlessDeathEffect(duration=20, owner=owner)
        effect.apply()
        
        revenant_stats = effect.get_revenant_stats()
        
        assert revenant_stats['max_hp'] == 40  # 20 * 2
        assert revenant_stats['hp'] == 40  # Full HP on reanimate
    
    def test_revenant_damage_75_percent(self):
        """Revenant damage should be 75% of original (floored)."""
        owner = Mock()
        owner.name = "Orc"
        owner.char = 'o'
        owner.color = (0, 0, 0)
        
        fighter = Mock()
        fighter.max_hp = 20
        fighter.damage_min = 4
        fighter.damage_max = 6
        fighter.accuracy = 2
        fighter.evasion = 2
        fighter.base_defense = 0
        fighter.power = 0
        owner.get_component_optional = Mock(return_value=fighter)
        
        effect = PlagueOfRestlessDeathEffect(duration=20, owner=owner)
        effect.apply()
        
        revenant_stats = effect.get_revenant_stats()
        
        # 4 * 0.75 = 3.0 -> 3
        # 6 * 0.75 = 4.5 -> 4
        assert revenant_stats['damage_min'] == 3
        assert revenant_stats['damage_max'] == 4
    
    def test_revenant_accuracy_75_percent(self):
        """Revenant accuracy should be 75% of original (floored)."""
        owner = Mock()
        owner.name = "Cultist"
        owner.char = 'c'
        owner.color = (0, 0, 0)
        
        fighter = Mock()
        fighter.max_hp = 30
        fighter.damage_min = 6
        fighter.damage_max = 10
        fighter.accuracy = 4
        fighter.evasion = 3
        fighter.base_defense = 2
        fighter.power = 1
        owner.get_component_optional = Mock(return_value=fighter)
        
        effect = PlagueOfRestlessDeathEffect(duration=20, owner=owner)
        effect.apply()
        
        revenant_stats = effect.get_revenant_stats()
        
        # 4 * 0.75 = 3.0 -> 3
        assert revenant_stats['accuracy'] == 3
    
    def test_revenant_evasion_50_percent(self):
        """Revenant evasion should be 50% of original (floored)."""
        owner = Mock()
        owner.name = "Spider"
        owner.char = 'S'
        owner.color = (0, 0, 0)
        
        fighter = Mock()
        fighter.max_hp = 18
        fighter.damage_min = 4
        fighter.damage_max = 8
        fighter.accuracy = 3
        fighter.evasion = 3
        fighter.base_defense = 1
        fighter.power = 0
        owner.get_component_optional = Mock(return_value=fighter)
        
        effect = PlagueOfRestlessDeathEffect(duration=20, owner=owner)
        effect.apply()
        
        revenant_stats = effect.get_revenant_stats()
        
        # 3 * 0.5 = 1.5 -> 1
        assert revenant_stats['evasion'] == 1


class TestCorporealFleshEligibility:
    """Tests for corporeal flesh checking."""
    
    def test_player_is_corporeal_flesh(self):
        """Player should be corporeal flesh."""
        from item_functions import _is_corporeal_flesh
        
        player = Mock()
        player.faction = Faction.PLAYER
        player.name = "Player"
        player.tags = None
        
        assert _is_corporeal_flesh(player) is True
    
    def test_orc_is_corporeal_flesh(self):
        """Orcs should be corporeal flesh."""
        from item_functions import _is_corporeal_flesh
        
        orc = Mock()
        orc.faction = Faction.ORC_FACTION
        orc.name = "Orc"
        orc.tags = None
        
        assert _is_corporeal_flesh(orc) is True
    
    def test_wraith_not_corporeal_flesh(self):
        """Wraiths (incorporeal undead) should NOT be corporeal flesh."""
        from item_functions import _is_corporeal_flesh
        
        wraith = Mock()
        wraith.faction = Faction.UNDEAD
        wraith.name = "Wraith"
        wraith.tags = None
        
        assert _is_corporeal_flesh(wraith) is False
    
    def test_skeleton_not_corporeal_flesh(self):
        """Skeletons should NOT be corporeal flesh (no flesh)."""
        from item_functions import _is_corporeal_flesh
        
        skeleton = Mock()
        skeleton.faction = Faction.UNDEAD
        skeleton.name = "Skeleton"
        skeleton.tags = None
        
        assert _is_corporeal_flesh(skeleton) is False
    
    def test_zombie_is_corporeal_flesh(self):
        """Zombies should be corporeal flesh (rotting flesh)."""
        from item_functions import _is_corporeal_flesh
        
        zombie = Mock()
        zombie.faction = Faction.UNDEAD
        zombie.name = "Zombie"
        zombie.tags = None
        
        assert _is_corporeal_flesh(zombie) is True
    
    def test_slime_not_corporeal_flesh(self):
        """Slimes should NOT be corporeal flesh."""
        from item_functions import _is_corporeal_flesh
        
        slime = Mock()
        slime.faction = Faction.HOSTILE_ALL
        slime.name = "Slime"
        slime.tags = None
        
        assert _is_corporeal_flesh(slime) is False
    
    def test_entity_with_corporeal_flesh_tag(self):
        """Entity with corporeal_flesh tag should be eligible."""
        from item_functions import _is_corporeal_flesh
        
        entity = Mock()
        entity.faction = Faction.NEUTRAL
        entity.name = "Custom Beast"
        entity.tags = ["corporeal_flesh", "beast"]
        
        assert _is_corporeal_flesh(entity) is True
    
    def test_entity_with_incorporeal_tag(self):
        """Entity with incorporeal tag should NOT be eligible."""
        from item_functions import _is_corporeal_flesh
        
        entity = Mock()
        entity.faction = Faction.NEUTRAL
        entity.name = "Ghost"
        entity.tags = ["incorporeal", "undead"]
        
        assert _is_corporeal_flesh(entity) is False


class TestReanimationScheduling:
    """Tests for plague reanimation scheduling."""
    
    def test_pending_reanimation_created_on_death(self):
        """When plague-infected entity dies, reanimation should be scheduled."""
        from death_functions import _check_plague_reanimation
        
        # Create mock entity with plague effect
        monster = Mock()
        monster.x, monster.y = 5, 5
        monster.name = "Infected Orc"
        
        # Create mock status effects with plague
        status_effects = Mock()
        plague_effect = Mock()
        plague_effect.get_revenant_stats = Mock(return_value={
            'max_hp': 40,
            'hp': 40,
            'damage_min': 3,
            'damage_max': 4,
            'accuracy': 1,
            'evasion': 0,
            'defense': 0,
            'power': 0,
            'original_name': 'Orc',
        })
        status_effects.get_effect = Mock(return_value=plague_effect)
        monster.get_component_optional = Mock(return_value=status_effects)
        
        result = _check_plague_reanimation(monster, None, [])
        
        assert result is not None
        assert 'corpse_x' in result
        assert 'corpse_y' in result
        assert 'revenant_stats' in result
        assert 'reanimate_in_turns' in result
        assert 1 <= result['reanimate_in_turns'] <= 3
    
    def test_no_reanimation_without_plague(self):
        """Entity without plague should not schedule reanimation."""
        from death_functions import _check_plague_reanimation
        
        monster = Mock()
        monster.x, monster.y = 5, 5
        
        # No status effects
        monster.get_component_optional = Mock(return_value=None)
        
        result = _check_plague_reanimation(monster, None, [])
        
        assert result is None


class TestRevenantZombieCreation:
    """Tests for revenant zombie creation."""
    
    def test_revenant_has_undead_faction(self):
        """Created revenant should have UNDEAD faction."""
        from death_functions import create_revenant_zombie
        
        revenant_stats = {
            'max_hp': 40,
            'hp': 40,
            'damage_min': 3,
            'damage_max': 4,
            'accuracy': 1,
            'evasion': 0,
            'defense': 0,
            'power': 0,
            'original_name': 'Orc',
        }
        
        revenant = create_revenant_zombie(5, 5, revenant_stats)
        
        assert revenant is not None
        assert revenant.faction == Faction.UNDEAD
    
    def test_revenant_has_correct_name(self):
        """Revenant should have 'Revenant' prefix in name."""
        from death_functions import create_revenant_zombie
        
        revenant_stats = {
            'max_hp': 40,
            'hp': 40,
            'damage_min': 3,
            'damage_max': 4,
            'accuracy': 1,
            'evasion': 0,
            'defense': 0,
            'power': 0,
            'original_name': 'Orc Warrior',
        }
        
        revenant = create_revenant_zombie(5, 5, revenant_stats)
        
        assert "Revenant" in revenant.name
        assert "Orc Warrior" in revenant.name
    
    def test_revenant_has_swarm_ability(self):
        """Revenant should have swarm special ability."""
        from death_functions import create_revenant_zombie
        
        revenant_stats = {
            'max_hp': 40,
            'hp': 40,
            'damage_min': 3,
            'damage_max': 4,
            'accuracy': 1,
            'evasion': 0,
            'defense': 0,
            'power': 0,
            'original_name': 'Orc',
        }
        
        revenant = create_revenant_zombie(5, 5, revenant_stats)
        
        assert hasattr(revenant, 'special_abilities')
        assert 'swarm' in revenant.special_abilities
