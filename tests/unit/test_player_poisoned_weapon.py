import pytest
from unittest.mock import MagicMock, patch

from entity import Entity
from components.fighter import Fighter
from components.equipment import Equipment
from components.equippable import Equippable
from components.faction import Faction


def _make_player_with_poisoned_weapon():
    player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
    # Match canonical player identity used in production (Entity.create_player sets this)
    player.faction = Faction.PLAYER
    player.fighter = Fighter(
        hp=30, defense=0, power=0,
        strength=14, dexterity=14, constitution=10,
        damage_min=1, damage_max=2
    )
    player.fighter.owner = player
    player.equipment = Equipment()
    
    # Keep weapon damage deterministic and easy to patch (range roll, not dice parsing)
    poisoned_equippable = Equippable(
        slot="main_hand",
        to_hit_bonus=1,
        damage_min=1,
        damage_max=1,
        damage_type="piercing",
        material="metal",
        applies_poison_on_hit=True,
    )
    weapon = Entity(0, 0, '-', (80, 170, 80), 'Poisoned Dagger', blocks=False, equippable=poisoned_equippable)
    # Ensure d20 combat code path uses direct attribute access for equippable
    weapon.components = MagicMock()
    weapon.components.has.return_value = False
    
    player.equipment.main_hand = weapon
    return player


def _make_target():
    target = Entity(1, 0, 'T', (255, 0, 0), 'Target', blocks=True)
    target.fighter = Fighter(hp=30, defense=0, power=0, strength=10, dexterity=10, constitution=10)
    target.fighter.owner = target
    target.equipment = Equipment()
    return target


def test_poisoned_weapon_applies_poison_on_successful_hit_and_not_on_miss():
    player = _make_player_with_poisoned_weapon()
    target = _make_target()
    
    # Hit: d20 roll then weapon damage roll
    with patch('random.randint', side_effect=[15, 1]):
        results = player.fighter.attack_d20(target)
    assert results
    assert target.status_effects is not None
    assert target.status_effects.has_effect('poison')
    
    # Miss: only d20 roll (no damage roll)
    target2 = _make_target()
    with patch('random.randint', return_value=1):
        results = player.fighter.attack_d20(target2)
    assert results
    assert not getattr(target2, 'status_effects', None) or not target2.status_effects.has_effect('poison')


def test_poisoned_weapon_repeated_hits_refresh_duration_not_stack():
    player = _make_player_with_poisoned_weapon()
    target = _make_target()
    
    # Two hits: (d20, dmg) × 2
    with patch('random.randint', side_effect=[15, 1, 15, 1]):
        player.fighter.attack_d20(target)
        # Tick down duration a bit
        effect = target.status_effects.get_effect('poison')
        assert effect is not None
        effect.process_turn_end()
        effect.process_turn_end()
        assert target.status_effects.get_effect('poison').duration == 4
        
        player.fighter.attack_d20(target)
    
    # Should still be exactly one poison effect, refreshed to default duration (6)
    assert target.status_effects.has_effect('poison')
    assert target.status_effects.get_effect('poison').duration == 6
    assert list(target.status_effects.active_effects.keys()).count('poison') == 1


def test_poisoned_weapon_increments_poison_applications_metric():
    player = _make_player_with_poisoned_weapon()
    target = _make_target()
    
    collector = MagicMock()
    with patch('services.scenario_metrics.get_active_metrics_collector', return_value=collector):
        with patch('random.randint', side_effect=[15, 1]):
            player.fighter.attack_d20(target)
    
    collector.increment.assert_any_call('poison_applications')


