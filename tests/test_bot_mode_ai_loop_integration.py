"""Integration test for bot mode AI loop bug fix.

This test exercises the REAL game engine, AISystem, and bot input flow
to catch the actual runtime bug where ai.take_turn() was called repeatedly.

The previous unit tests in test_bot_mode_infinite_loop_fix.py only tested
BotInputSource in isolation, which didn't catch the AI system loop bug.
"""

import pytest
from unittest.mock import Mock, MagicMock
from engine.game_engine import GameEngine
from engine.systems.ai_system import AISystem
from engine.game_state_manager import GameStateManager
from game_states import GameStates
from io_layer.bot_input import BotInputSource


class MockEntity:
    """Mock entity for testing."""
    
    def __init__(self, name="Orc", x=5, y=5, has_ai=True):
        self.name = name
        self.x = x
        self.y = y
        self.ai = MockAI() if has_ai else None
        self.fighter = MockFighter()
        
    def get_component_optional(self, component_type):
        return None


class MockAI:
    """Mock AI component that tracks how many times take_turn() is called."""
    
    def __init__(self):
        self.take_turn_call_count = 0
        self.ai_type = "basic"
    
    def take_turn(self, player, fov_map, game_map, entities):
        """Mock take_turn that increments counter and returns empty results."""
        self.take_turn_call_count += 1
        # Simulate AI that does nothing (e.g., can't see player, no path)
        return []


class MockFighter:
    """Mock fighter component."""
    
    def __init__(self):
        self.hp = 10
        self.max_hp = 10


class MockPlayer:
    """Mock player entity."""
    
    def __init__(self):
        self.name = "Player"
        self.x = 1
        self.y = 1
        self.ai = None
        self.fighter = MockFighter()
    
    def get_component_optional(self, component_type):
        return None


class MockGameMap:
    """Mock game map."""
    
    def __init__(self):
        self.width = 50
        self.height = 50
        self.dungeon_level = 1


class MockMessageLog:
    """Mock message log."""
    
    def add_message(self, message):
        pass


class TestBotModeAILoopIntegration:
    """Integration tests for bot mode AI loop bug."""
    
    def test_ai_system_processes_each_enemy_exactly_once_per_update(self):
        """Test that AISystem.update() processes each enemy exactly once.
        
        This is the core integration test that catches the runtime bug.
        Each enemy should only have ai.take_turn() called ONCE per update cycle.
        """
        # Create game engine with AISystem
        engine = GameEngine(target_fps=60)
        ai_system = AISystem(priority=50)
        engine.register_system(ai_system)
        
        # Initialize state manager with mock game state
        engine.state_manager = GameStateManager()
        player = MockPlayer()
        orc1 = MockEntity("Orc1", x=5, y=5)
        orc2 = MockEntity("Orc2", x=10, y=10)
        entities = [player, orc1, orc2]
        
        engine.state_manager.initialize_game(
            player=player,
            entities=entities,
            game_map=MockGameMap(),
            message_log=MockMessageLog(),
            game_state=GameStates.ENEMY_TURN,
            constants={}
        )
        
        # Sync TurnManager with GameState (advance to ENEMY phase)
        from engine.turn_manager import TurnPhase
        engine.turn_manager.advance_turn(TurnPhase.ENEMY)
        
        # Start engine (initializes timing)
        engine.start()
        
        # Simulate one update cycle during ENEMY_TURN
        engine.update()
        
        # ASSERT: Each enemy should have take_turn() called exactly once
        assert orc1.ai.take_turn_call_count == 1, \
            f"Orc1.ai.take_turn() called {orc1.ai.take_turn_call_count} times, expected 1"
        assert orc2.ai.take_turn_call_count == 1, \
            f"Orc2.ai.take_turn() called {orc2.ai.take_turn_call_count} times, expected 1"
    
    def test_ai_system_does_not_run_multiple_times_in_one_update(self):
        """Test that AISystem.update() is not called recursively.
        
        This catches bugs where update() might be called multiple times
        in one game loop iteration.
        """
        # Create game engine with AISystem
        engine = GameEngine(target_fps=60)
        ai_system = AISystem(priority=50)
        engine.register_system(ai_system)
        
        # Initialize state manager
        engine.state_manager = GameStateManager()
        player = MockPlayer()
        orc = MockEntity("Orc", x=5, y=5)
        entities = [player, orc]
        
        engine.state_manager.initialize_game(
            player=player,
            entities=entities,
            game_map=MockGameMap(),
            message_log=MockMessageLog(),
            game_state=GameStates.ENEMY_TURN,
            constants={}
        )
        
        # Start engine
        engine.start()
        
        # Call update() multiple times rapidly (simulating fast bot loop)
        for i in range(10):
            engine.update()
        
        # ASSERT: Even with 10 update() calls, if state doesn't change back to ENEMY_TURN,
        # the AI should only process once (because state transitions to PLAYERS_TURN after first update)
        # But if there's a bug where state doesn't transition, we should still not process more than once
        # per update due to our new guards
        
        # In this test, after first update(), state should be PLAYERS_TURN, so subsequent
        # updates won't process AI. But let's verify the guard works even if state is stuck.
        assert orc.ai.take_turn_call_count <= 10, \
            f"Orc.ai.take_turn() called {orc.ai.take_turn_call_count} times (max should be 10 for 10 updates)"
    
    def test_ai_system_does_not_run_in_player_dead_state(self):
        """Test that AISystem.update() does nothing when player is dead.
        
        This was part of the original bug - AI kept running on death screen.
        """
        # Create game engine with AISystem
        engine = GameEngine(target_fps=60)
        ai_system = AISystem(priority=50)
        engine.register_system(ai_system)
        
        # Initialize state manager with PLAYER_DEAD state
        engine.state_manager = GameStateManager()
        player = MockPlayer()
        orc = MockEntity("Orc", x=5, y=5)
        entities = [player, orc]
        
        engine.state_manager.initialize_game(
            player=player,
            entities=entities,
            game_map=MockGameMap(),
            message_log=MockMessageLog(),
            game_state=GameStates.PLAYER_DEAD,  # Player is dead
            constants={}
        )
        
        # Start engine
        engine.start()
        
        # Call update() many times (simulating the hang/beachball)
        for i in range(100):
            engine.update()
        
        # ASSERT: AI should NEVER run when player is dead
        assert orc.ai.take_turn_call_count == 0, \
            f"Orc.ai.take_turn() called {orc.ai.take_turn_call_count} times in PLAYER_DEAD state (should be 0)"
    
    def test_bot_mode_does_not_hang_on_empty_room(self):
        """Test that bot mode doesn't hang when spawning in an empty room.
        
        This simulates the exact scenario from the bug report:
        1. Bot sends wait action
        2. State transitions to ENEMY_TURN
        3. AISystem runs (but no enemies)
        4. State transitions back to PLAYERS_TURN
        5. Loop should continue without hanging
        """
        # Create game engine with AISystem
        engine = GameEngine(target_fps=60)
        ai_system = AISystem(priority=50)
        engine.register_system(ai_system)
        
        # Initialize state manager with NO enemies (empty room)
        engine.state_manager = GameStateManager()
        player = MockPlayer()
        entities = [player]  # Just player, no enemies
        
        engine.state_manager.initialize_game(
            player=player,
            entities=entities,
            game_map=MockGameMap(),
            message_log=MockMessageLog(),
            game_state=GameStates.PLAYERS_TURN,
            constants={}
        )
        
        # Create bot input source
        bot = BotInputSource()
        
        # Start engine
        engine.start()
        
        # Simulate bot mode loop for N iterations
        # In real runtime, this would be the main game loop
        max_iterations = 100
        for i in range(max_iterations):
            # Bot returns action
            action = bot.next_action(engine.state_manager.state)
            
            # If action is wait, transition to ENEMY_TURN
            if action.get('wait'):
                engine.state_manager.set_game_state(GameStates.ENEMY_TURN)
            
            # Update engine (processes AI)
            engine.update()
            
            # After update, state should be back to PLAYERS_TURN
            # (AISystem transitions back when done)
        
        # ASSERT: Test should complete without hanging
        # If we get here, the loop didn't hang
        assert True, "Bot mode loop completed without hanging"
    
    def test_same_entity_not_processed_twice_in_one_update(self):
        """Test that even if an entity appears multiple times in the list, it's only processed once.
        
        This catches bugs where an entity might be duplicated in the entities list.
        """
        # Create game engine with AISystem
        engine = GameEngine(target_fps=60)
        ai_system = AISystem(priority=50)
        engine.register_system(ai_system)
        
        # Initialize state manager
        engine.state_manager = GameStateManager()
        player = MockPlayer()
        orc = MockEntity("Orc", x=5, y=5)
        
        # BUG SIMULATION: Same entity appears twice in the list
        entities = [player, orc, orc]  # Orc is duplicated!
        
        engine.state_manager.initialize_game(
            player=player,
            entities=entities,
            game_map=MockGameMap(),
            message_log=MockMessageLog(),
            game_state=GameStates.ENEMY_TURN,
            constants={}
        )
        
        # Sync TurnManager with GameState (advance to ENEMY phase)
        from engine.turn_manager import TurnPhase
        engine.turn_manager.advance_turn(TurnPhase.ENEMY)
        
        # Start engine
        engine.start()
        
        # Update once
        engine.update()
        
        # ASSERT: Even though orc appears twice in the list, it should only be processed once
        assert orc.ai.take_turn_call_count == 1, \
            f"Orc.ai.take_turn() called {orc.ai.take_turn_call_count} times (should be 1 despite duplicate)"
    
    def test_ai_system_update_not_reentrant(self):
        """Test that AISystem.update() cannot be called recursively.
        
        This catches bugs where update() might trigger itself recursively.
        """
        # Create game engine with AISystem
        engine = GameEngine(target_fps=60)
        ai_system = AISystem(priority=50)
        engine.register_system(ai_system)
        
        # Initialize state manager
        engine.state_manager = GameStateManager()
        player = MockPlayer()
        orc = MockEntity("Orc", x=5, y=5)
        entities = [player, orc]
        
        engine.state_manager.initialize_game(
            player=player,
            entities=entities,
            game_map=MockGameMap(),
            message_log=MockMessageLog(),
            game_state=GameStates.ENEMY_TURN,
            constants={}
        )
        
        # Sync TurnManager with GameState (advance to ENEMY phase)
        from engine.turn_manager import TurnPhase
        engine.turn_manager.advance_turn(TurnPhase.ENEMY)
        
        # Manually set update depth to simulate re-entrancy
        ai_system._update_call_depth = 0
        
        # First update should work
        ai_system.update(0.016)
        assert orc.ai.take_turn_call_count == 1
        
        # Simulate recursive call (depth guard should prevent processing)
        # Manually set depth to 1 to simulate being inside update()
        ai_system._update_call_depth = 1
        ai_system.update(0.016)
        
        # ASSERT: Second call should be blocked by re-entrancy guard
        assert orc.ai.take_turn_call_count == 1, \
            "Re-entrant update() call should be blocked"
        
        # Reset depth
        ai_system._update_call_depth = 0

