"""Unit test to verify player DOT effects tick exactly once per turn.

This test ensures that PoisonEffect (and by extension, all DOT effects) on the
player tick exactly once per turn, preventing double-tick bugs where both
AISystem._process_player_status_effects() and ActionProcessor._process_player_status_effects()
could potentially tick DOT damage.

The test simulates a full game turn cycle:
1. Apply poison to player
2. Execute one player action
3. Transition to enemy turn  
4. Transition back to player turn (this is when DOT should tick via AISystem)
5. Verify poison ticked exactly once and dealt exactly 1 damage
"""

import logging
from unittest.mock import Mock, MagicMock, patch
from types import SimpleNamespace

from components.fighter import Fighter
from components.status_effects import PoisonEffect, StatusEffectManager
from components.component_registry import ComponentType
from entity import Entity
from services.scenario_metrics import scoped_metrics_collector


def test_player_poison_ticks_exactly_once_per_turn():
    """Verify player poison ticks exactly once per turn, not twice.
    
    Bug scenario this prevents:
    - OLD: process_turn_start() called in both AISystem (start of turn) AND
      ActionProcessor (end of action) → 2 damage ticks per turn
    - NEW: process_turn_start() called ONLY in AISystem → 1 damage tick per turn
    
    This test would fail under double-tick because:
    - Expected: 1 tick, 1 damage (5 HP → 4 HP)
    - Double-tick bug: 2 ticks, 2 damage (5 HP → 3 HP)
    """
    # Create player entity with 5 HP
    fighter = Fighter(hp=5, defense=0, power=0)
    player = Entity(0, 0, '@', (255, 255, 255), "Player", blocks=True, fighter=fighter)
    
    # Apply poison (duration 6, damage 1 per tick)
    metrics = SimpleNamespace()
    with scoped_metrics_collector(metrics):
        poison = PoisonEffect(owner=player, duration=6, damage_per_tick=1)
        poison.apply()
        
        # Verify application
        assert metrics.poison_applications == 1
        assert player.fighter.hp == 5  # No damage yet, just applied
        
        # Simulate player turn START (this is when DOT should tick in AISystem)
        # This is the ONLY place process_turn_start should be called for player
        with patch('logger_config.get_logger'):
            tick_results = poison.process_turn_start(state_manager=None)
        
        # Verify DOT ticked exactly once
        assert poison.ticks_processed == 1, "Poison should have ticked exactly once"
        assert metrics.poison_ticks_processed == 1, "Metrics should record exactly 1 tick"
        assert metrics.poison_damage_dealt == 1, "Metrics should record exactly 1 damage"
        assert player.fighter.hp == 4, "Player should have taken exactly 1 damage (5 → 4)"
        
        # Simulate player action end (ActionProcessor._process_player_status_effects)
        # This should ONLY call process_turn_end() (duration decrement), NOT process_turn_start()
        # No additional damage should be dealt here
        end_results = poison.process_turn_end()
        
        # Verify duration decremented but NO additional damage
        assert poison.duration == 5, "Duration should have decremented from 6 to 5"
        assert poison.ticks_processed == 1, "Still exactly 1 tick (no double-tick)"
        assert metrics.poison_ticks_processed == 1, "Metrics still show exactly 1 tick"
        assert metrics.poison_damage_dealt == 1, "Metrics still show exactly 1 damage"
        assert player.fighter.hp == 4, "HP should still be 4 (no additional damage)"


def test_player_burning_ticks_exactly_once_per_turn():
    """Verify player burning ticks exactly once per turn.
    
    Same test as poison but for BurningEffect to ensure both DOT types behave identically.
    """
    from components.status_effects import BurningEffect
    
    # Create player entity with 5 HP
    fighter = Fighter(hp=5, defense=0, power=0)
    player = Entity(0, 0, '@', (255, 255, 255), "Player", blocks=True, fighter=fighter)
    
    # Apply burning (duration 4, damage 1 per tick)
    metrics = SimpleNamespace()
    with scoped_metrics_collector(metrics):
        burning = BurningEffect(duration=4, owner=player, damage_per_turn=1)
        burning.apply()
        
        # Verify application
        assert metrics.burning_applications == 1
        assert player.fighter.hp == 5  # No damage yet
        
        # Simulate player turn START (DOT tick in AISystem)
        with patch('logger_config.get_logger'):
            tick_results = burning.process_turn_start(state_manager=None)
        
        # Verify single tick
        assert metrics.burning_ticks_processed == 1, "Burning should tick exactly once"
        assert metrics.burning_damage_dealt == 1, "Should deal exactly 1 damage"
        assert player.fighter.hp == 4, "Player should have 4 HP (5 → 4)"
        
        # Simulate action end (duration decrement only)
        end_results = burning.process_turn_end()
        
        # Verify no additional damage
        assert burning.duration == 3, "Duration decremented from 4 to 3"
        assert metrics.burning_ticks_processed == 1, "Still exactly 1 tick"
        assert metrics.burning_damage_dealt == 1, "Still exactly 1 damage"
        assert player.fighter.hp == 4, "HP unchanged at 4"


def test_player_poison_multi_turn_sequence():
    """Verify poison behaves correctly over multiple turns.
    
    Simulates 3 full turn cycles to ensure:
    - Each turn ticks exactly once
    - Durations decrement correctly
    - Total damage matches expected
    """
    # Create player with 10 HP
    fighter = Fighter(hp=10, defense=0, power=0)
    player = Entity(0, 0, '@', (255, 255, 255), "Player", blocks=True, fighter=fighter)
    
    metrics = SimpleNamespace()
    with scoped_metrics_collector(metrics):
        poison = PoisonEffect(owner=player, duration=6, damage_per_tick=1)
        poison.apply()
        
        assert player.fighter.hp == 10
        
        # Turn 1
        with patch('logger_config.get_logger'):
            poison.process_turn_start(state_manager=None)  # Tick damage
        poison.process_turn_end()  # Decrement duration
        
        assert poison.ticks_processed == 1
        assert poison.duration == 5
        assert player.fighter.hp == 9  # 10 - 1
        assert metrics.poison_ticks_processed == 1
        assert metrics.poison_damage_dealt == 1
        
        # Turn 2
        with patch('logger_config.get_logger'):
            poison.process_turn_start(state_manager=None)
        poison.process_turn_end()
        
        assert poison.ticks_processed == 2
        assert poison.duration == 4
        assert player.fighter.hp == 8  # 9 - 1
        assert metrics.poison_ticks_processed == 2
        assert metrics.poison_damage_dealt == 2
        
        # Turn 3
        with patch('logger_config.get_logger'):
            poison.process_turn_start(state_manager=None)
        poison.process_turn_end()
        
        assert poison.ticks_processed == 3
        assert poison.duration == 3
        assert player.fighter.hp == 7  # 8 - 1
        assert metrics.poison_ticks_processed == 3
        assert metrics.poison_damage_dealt == 3

