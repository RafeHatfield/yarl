"""Tests for TurnManager system."""

import unittest
from unittest.mock import Mock, call

from engine.turn_manager import TurnManager, TurnPhase


class TestTurnPhase(unittest.TestCase):
    """Test TurnPhase enum."""
    
    def test_phase_values(self):
        """Test that phases have correct string values."""
        self.assertEqual(TurnPhase.PLAYER.value, "player")
        self.assertEqual(TurnPhase.ENEMY.value, "enemy")
        self.assertEqual(TurnPhase.ENVIRONMENT.value, "environment")
    
    def test_phase_string_representation(self):
        """Test string representation of phases."""
        self.assertEqual(str(TurnPhase.PLAYER), "player")
        self.assertEqual(repr(TurnPhase.PLAYER), "TurnPhase.PLAYER")


class TestTurnManagerBasics(unittest.TestCase):
    """Test basic TurnManager functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = TurnManager()
    
    def test_initial_state(self):
        """Test initial turn manager state."""
        self.assertEqual(self.manager.current_phase, TurnPhase.PLAYER)
        self.assertEqual(self.manager.turn_number, 1)
        self.assertFalse(self.manager.phase_in_progress)
    
    def test_initial_state_custom_phase(self):
        """Test initialization with custom starting phase."""
        manager = TurnManager(start_phase=TurnPhase.ENEMY)
        self.assertEqual(manager.current_phase, TurnPhase.ENEMY)
        self.assertEqual(manager.turn_number, 1)
    
    def test_is_phase(self):
        """Test phase checking."""
        self.assertTrue(self.manager.is_phase(TurnPhase.PLAYER))
        self.assertFalse(self.manager.is_phase(TurnPhase.ENEMY))
        self.assertFalse(self.manager.is_phase(TurnPhase.ENVIRONMENT))
    
    def test_phase_name_property(self):
        """Test phase_name property."""
        self.assertEqual(self.manager.phase_name, "player")
        self.manager.current_phase = TurnPhase.ENEMY
        self.assertEqual(self.manager.phase_name, "enemy")
    
    def test_repr(self):
        """Test string representation."""
        repr_str = repr(self.manager)
        self.assertIn("turn=1", repr_str)
        self.assertIn("phase=", repr_str)
        # Actual output: "TurnManager(turn=1, phase=player)"
        self.assertTrue(repr_str.startswith("TurnManager"))


class TestTurnAdvancement(unittest.TestCase):
    """Test turn advancement logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = TurnManager()
    
    def test_advance_turn_sequence(self):
        """Test that turns advance in correct sequence."""
        # PLAYER → ENEMY
        phase = self.manager.advance_turn()
        self.assertEqual(phase, TurnPhase.ENEMY)
        self.assertEqual(self.manager.current_phase, TurnPhase.ENEMY)
        self.assertEqual(self.manager.turn_number, 1)
        
        # ENEMY → ENVIRONMENT
        phase = self.manager.advance_turn()
        self.assertEqual(phase, TurnPhase.ENVIRONMENT)
        self.assertEqual(self.manager.current_phase, TurnPhase.ENVIRONMENT)
        self.assertEqual(self.manager.turn_number, 1)
        
        # ENVIRONMENT → PLAYER (turn increments!)
        phase = self.manager.advance_turn()
        self.assertEqual(phase, TurnPhase.PLAYER)
        self.assertEqual(self.manager.current_phase, TurnPhase.PLAYER)
        self.assertEqual(self.manager.turn_number, 2)  # New turn!
    
    def test_advance_turn_explicit_phase(self):
        """Test advancing to explicit phase."""
        # Skip directly to ENVIRONMENT
        phase = self.manager.advance_turn(to_phase=TurnPhase.ENVIRONMENT)
        self.assertEqual(phase, TurnPhase.ENVIRONMENT)
        self.assertEqual(self.manager.current_phase, TurnPhase.ENVIRONMENT)
    
    def test_advance_turn_blocked_when_in_progress(self):
        """Test that turn cannot advance while phase in progress."""
        self.manager.start_phase()
        
        # Attempt to advance (should be blocked)
        phase = self.manager.advance_turn()
        
        # Should still be on PLAYER phase
        self.assertEqual(phase, TurnPhase.PLAYER)
        self.assertEqual(self.manager.current_phase, TurnPhase.PLAYER)
    
    def test_start_and_end_phase(self):
        """Test phase in-progress tracking."""
        self.assertFalse(self.manager.phase_in_progress)
        
        self.manager.start_phase()
        self.assertTrue(self.manager.phase_in_progress)
        
        self.manager.end_phase()
        self.assertFalse(self.manager.phase_in_progress)
    
    def test_full_turn_cycle(self):
        """Test complete turn cycle."""
        # Complete 3 full turns
        for turn in range(1, 4):
            # Each turn has 3 phases
            for phase in [TurnPhase.ENEMY, TurnPhase.ENVIRONMENT, TurnPhase.PLAYER]:
                self.manager.advance_turn()
            
            # After PLAYER phase starts, turn number should increment
            self.assertEqual(self.manager.turn_number, turn + 1)


class TestTurnListeners(unittest.TestCase):
    """Test listener registration and notification."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = TurnManager()
        self.mock_callback = Mock()
    
    def test_register_listener_start(self):
        """Test registering start listener."""
        self.manager.register_listener(TurnPhase.ENEMY, self.mock_callback, "start")
        
        # Advance to ENEMY phase
        self.manager.advance_turn()  # PLAYER → ENEMY
        
        # Callback should be called
        self.mock_callback.assert_called_once()
    
    def test_register_listener_end(self):
        """Test registering end listener."""
        self.manager.register_listener(TurnPhase.PLAYER, self.mock_callback, "end")
        
        # Advance from PLAYER phase
        self.manager.advance_turn()  # PLAYER → ENEMY
        
        # Callback should be called when PLAYER ends
        self.mock_callback.assert_called_once()
    
    def test_multiple_listeners_same_phase(self):
        """Test multiple listeners for same phase."""
        callback1 = Mock()
        callback2 = Mock()
        callback3 = Mock()
        
        self.manager.register_listener(TurnPhase.ENEMY, callback1, "start")
        self.manager.register_listener(TurnPhase.ENEMY, callback2, "start")
        self.manager.register_listener(TurnPhase.ENEMY, callback3, "start")
        
        # Advance to ENEMY
        self.manager.advance_turn()
        
        # All callbacks should be called
        callback1.assert_called_once()
        callback2.assert_called_once()
        callback3.assert_called_once()
    
    def test_listeners_for_different_phases(self):
        """Test listeners for different phases."""
        player_callback = Mock()
        enemy_callback = Mock()
        env_callback = Mock()
        
        self.manager.register_listener(TurnPhase.PLAYER, player_callback, "end")
        self.manager.register_listener(TurnPhase.ENEMY, enemy_callback, "start")
        self.manager.register_listener(TurnPhase.ENVIRONMENT, env_callback, "start")
        
        # Advance PLAYER → ENEMY
        self.manager.advance_turn()
        
        player_callback.assert_called_once()  # PLAYER ended
        enemy_callback.assert_called_once()   # ENEMY started
        env_callback.assert_not_called()      # ENV not reached yet
        
        # Advance ENEMY → ENVIRONMENT
        self.manager.advance_turn()
        env_callback.assert_called_once()     # Now ENV started
    
    def test_unregister_listener(self):
        """Test unregistering listeners."""
        self.manager.register_listener(TurnPhase.ENEMY, self.mock_callback, "start")
        
        # Unregister
        result = self.manager.unregister_listener(TurnPhase.ENEMY, self.mock_callback, "start")
        self.assertTrue(result)
        
        # Advance to ENEMY phase
        self.manager.advance_turn()
        
        # Callback should NOT be called
        self.mock_callback.assert_not_called()
    
    def test_unregister_nonexistent_listener(self):
        """Test unregistering listener that wasn't registered."""
        result = self.manager.unregister_listener(TurnPhase.ENEMY, self.mock_callback, "start")
        self.assertFalse(result)
    
    def test_invalid_event_type(self):
        """Test that invalid event types raise error."""
        with self.assertRaises(ValueError):
            self.manager.register_listener(TurnPhase.PLAYER, self.mock_callback, "invalid")
        
        with self.assertRaises(ValueError):
            self.manager.register_listener(TurnPhase.PLAYER, self.mock_callback, "middle")
    
    def test_listener_exception_handling(self):
        """Test that listener exceptions don't break turn advancement."""
        def bad_callback():
            raise RuntimeError("Listener error!")
        
        good_callback = Mock()
        
        self.manager.register_listener(TurnPhase.ENEMY, bad_callback, "start")
        self.manager.register_listener(TurnPhase.ENEMY, good_callback, "start")
        
        # Advance should work despite bad callback
        phase = self.manager.advance_turn()
        
        # Should still advance to ENEMY
        self.assertEqual(phase, TurnPhase.ENEMY)
        
        # Good callback should still be called
        good_callback.assert_called_once()


class TestTurnHistory(unittest.TestCase):
    """Test turn history tracking."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = TurnManager()
    
    def test_history_records_transitions(self):
        """Test that phase transitions are recorded."""
        # Advance a few times
        self.manager.advance_turn()  # PLAYER → ENEMY
        self.manager.advance_turn()  # ENEMY → ENVIRONMENT
        self.manager.advance_turn()  # ENVIRONMENT → PLAYER
        
        history = self.manager.get_history()
        
        self.assertEqual(len(history), 3)
        
        # Check first transition
        self.assertEqual(history[0]["turn"], 1)
        self.assertEqual(history[0]["from"], "player")
        self.assertEqual(history[0]["to"], "enemy")
        
        # Check second transition
        self.assertEqual(history[1]["turn"], 1)
        self.assertEqual(history[1]["from"], "enemy")
        self.assertEqual(history[1]["to"], "environment")
        
        # Check third transition (turn hasn't incremented yet when recorded!)
        self.assertEqual(history[2]["turn"], 1)  # Still turn 1 in history
        self.assertEqual(history[2]["from"], "environment")
        self.assertEqual(history[2]["to"], "player")
    
    def test_history_limited_length(self):
        """Test that history is limited to prevent memory issues."""
        # Advance many times
        for _ in range(150):  # More than max_history (100)
            self.manager.advance_turn()
        
        history = self.manager.get_history(last_n=200)  # Request more than exists
        
        # Should be capped at max
        self.assertLessEqual(len(history), 100)
    
    def test_get_history_last_n(self):
        """Test getting last N history entries."""
        # Advance 10 times
        for _ in range(10):
            self.manager.advance_turn()
        
        # Get last 3
        history = self.manager.get_history(last_n=3)
        self.assertEqual(len(history), 3)
        
        # After 10 advances from PLAYER: ends at PLAYER → ENEMY (10th transition)
        self.assertEqual(history[-1]["to"], "enemy")  # Most recent


class TestTurnManagerReset(unittest.TestCase):
    """Test turn manager reset functionality."""
    
    def test_reset(self):
        """Test resetting turn manager."""
        manager = TurnManager()
        
        # Advance a few turns
        manager.advance_turn()
        manager.advance_turn()
        manager.advance_turn()  # Should be turn 2 now
        
        self.assertEqual(manager.turn_number, 2)
        self.assertEqual(manager.current_phase, TurnPhase.PLAYER)
        self.assertGreater(len(manager.get_history()), 0)
        
        # Reset
        manager.reset()
        
        # Should be back to initial state
        self.assertEqual(manager.turn_number, 1)
        self.assertEqual(manager.current_phase, TurnPhase.PLAYER)
        self.assertFalse(manager.phase_in_progress)
        self.assertEqual(len(manager.get_history()), 0)


class TestTurnManagerIntegration(unittest.TestCase):
    """Integration tests simulating real gameplay."""
    
    def test_typical_turn_sequence(self):
        """Test typical turn sequence with listeners."""
        manager = TurnManager()
        
        # Track what happens
        actions = []
        
        def player_end():
            actions.append("player_end")
        
        def enemy_start():
            actions.append("enemy_start")
        
        def enemy_end():
            actions.append("enemy_end")
        
        def env_start():
            actions.append("env_start")
        
        manager.register_listener(TurnPhase.PLAYER, player_end, "end")
        manager.register_listener(TurnPhase.ENEMY, enemy_start, "start")
        manager.register_listener(TurnPhase.ENEMY, enemy_end, "end")
        manager.register_listener(TurnPhase.ENVIRONMENT, env_start, "start")
        
        # Simulate one full turn
        manager.advance_turn()  # PLAYER → ENEMY
        manager.advance_turn()  # ENEMY → ENVIRONMENT
        manager.advance_turn()  # ENVIRONMENT → PLAYER
        
        # Check sequence
        self.assertEqual(actions, [
            "player_end",   # Player turn ended
            "enemy_start",  # Enemy turn started
            "enemy_end",    # Enemy turn ended
            "env_start",    # Environment turn started
        ])
    
    def test_yo_mama_style_scenario(self):
        """Test a yo_mama-style scenario with turn tracking."""
        manager = TurnManager()
        
        # Simulate: player casts yo_mama, monsters attack target, target dies
        
        # Turn 1: Player casts yo_mama
        self.assertEqual(manager.turn_number, 1)
        self.assertEqual(manager.current_phase, TurnPhase.PLAYER)
        
        # Player action complete → Enemy turn
        manager.advance_turn()
        self.assertEqual(manager.current_phase, TurnPhase.ENEMY)
        
        # Monsters act (attack taunted target)
        # ... AI processing happens here ...
        
        # Enemy turn complete → Environment turn
        manager.advance_turn()
        self.assertEqual(manager.current_phase, TurnPhase.ENVIRONMENT)
        
        # Environment processes (hazards, etc.)
        manager.advance_turn()
        
        # Back to player turn, turn number incremented
        self.assertEqual(manager.current_phase, TurnPhase.PLAYER)
        self.assertEqual(manager.turn_number, 2)
        
        # History shows clear sequence
        history = manager.get_history()
        self.assertEqual(len(history), 3)  # 3 transitions in one cycle


if __name__ == '__main__':
    unittest.main()

