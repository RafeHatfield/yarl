"""Test that bot mode properly handles turn transitions without hanging.

This test verifies the Phase 0 bot mode fix where:
- Enemy AI is disabled (no entity.ai.take_turn() calls)
- BUT the turn state machine still works (ENEMY → PLAYERS_TURN transitions)
- The game doesn't hang in a tight loop
"""

import pytest
from unittest.mock import Mock
from engine.game_engine import GameEngine
from engine.systems.ai_system import AISystem
from engine.game_state_manager import GameStateManager
from game_states import GameStates
from engine.turn_manager import TurnPhase


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
        self.status_effects = MockStatusEffects()
    
    def get_component_optional(self, component_type):
        return None


class MockStatusEffects:
    """Mock status effects."""
    
    def process_turn_start(self, **kwargs):
        return []


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


class TestBotModeTurnTransitions:
    """Test that bot mode turn transitions work without hanging."""
    
    def setup_method(self):
        """Reset singletons before each test."""
        from systems.turn_controller import reset_turn_controller
        reset_turn_controller()
    
    def test_bot_mode_enemies_dont_act_but_turns_advance(self):
        """Test that in bot mode, enemies don't act but turn phases still advance.
        
        This is the core fix: AISystem.update() should:
        1. NOT call entity.ai.take_turn() when disable_enemy_ai_for_bot=True
        2. BUT still run the turn transition logic (ENEMY → PLAYERS_TURN)
        """
        # Create game engine with AISystem
        engine = GameEngine(target_fps=60)
        ai_system = AISystem(priority=50)
        engine.register_system(ai_system)
        
        # Initialize state manager with mock game state
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
        
        # Enable bot mode (Phase 0 fix)
        engine.disable_enemy_ai_for_bot = True
        
        # Sync TurnManager with GameState (advance to ENEMY phase)
        engine.turn_manager.advance_turn(TurnPhase.ENEMY)
        
        # Start engine (initializes timing)
        engine.start()
        
        # Simulate one update cycle during ENEMY_TURN
        engine.update()
        
        # ASSERT 1: Enemy AI should NOT have been called (bot mode disables it)
        assert orc.ai.take_turn_call_count == 0, \
            f"Bot mode should prevent AI from acting, but Orc.ai.take_turn() was called {orc.ai.take_turn_call_count} times"
        
        # ASSERT 2: Game state should have transitioned back to PLAYERS_TURN
        # (This is the critical fix - turn transitions still work even when AI is disabled)
        assert engine.state_manager.state.current_state == GameStates.PLAYERS_TURN, \
            f"Expected PLAYERS_TURN after bot mode enemy phase, got {engine.state_manager.state.current_state}"
    
    def test_bot_mode_multiple_update_cycles_no_hang(self):
        """Test that bot mode can run multiple update cycles without hanging.
        
        Previously, bot mode would hang because AISystem.update() returned early,
        preventing the ENEMY → PLAYERS_TURN transition. The game would get stuck
        in ENEMY_TURN and spam AISystem logs.
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
            game_state=GameStates.PLAYERS_TURN,
            constants={}
        )
        
        # Enable bot mode
        engine.disable_enemy_ai_for_bot = True
        
        # Start engine
        engine.start()
        
        # Simulate multiple cycles: PLAYERS_TURN → ENEMY_TURN → PLAYERS_TURN
        for cycle in range(10):
            # Player turn
            assert engine.state_manager.state.current_state == GameStates.PLAYERS_TURN
            
            # Simulate player action (wait) → transition to ENEMY_TURN
            engine.state_manager.set_game_state(GameStates.ENEMY_TURN)
            engine.turn_manager.advance_turn(TurnPhase.ENEMY)
            
            # Update engine (AISystem should process ENEMY turn)
            engine.update()
            
            # Should be back to PLAYERS_TURN
            assert engine.state_manager.state.current_state == GameStates.PLAYERS_TURN, \
                f"Cycle {cycle}: Expected PLAYERS_TURN after enemy update, got {engine.state_manager.state.current_state}"
        
        # ASSERT: Enemy AI was never called during any cycle
        assert orc.ai.take_turn_call_count == 0, \
            f"Bot mode should prevent AI throughout all cycles, but was called {orc.ai.take_turn_call_count} times"
    
    def test_normal_mode_enemies_still_act(self):
        """Test that normal mode (disable_enemy_ai_for_bot=False) still works.
        
        This ensures our fix didn't break normal gameplay where enemies should act.
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
        
        # NORMAL MODE: disable_enemy_ai_for_bot=False (or not set)
        engine.disable_enemy_ai_for_bot = False
        
        # Sync TurnManager
        engine.turn_manager.advance_turn(TurnPhase.ENEMY)
        
        # Start engine
        engine.start()
        
        # Update once
        engine.update()
        
        # ASSERT 1: Enemy AI SHOULD have been called in normal mode
        assert orc.ai.take_turn_call_count == 1, \
            f"Normal mode should allow AI to act, but Orc.ai.take_turn() was called {orc.ai.take_turn_call_count} times (expected 1)"
        
        # ASSERT 2: State should still transition correctly
        assert engine.state_manager.state.current_state == GameStates.PLAYERS_TURN, \
            f"Expected PLAYERS_TURN after normal enemy phase, got {engine.state_manager.state.current_state}"
    
    def test_bot_mode_with_no_enemies_doesnt_hang(self):
        """Test that bot mode works even with no enemies (empty room).
        
        This was the original bug scenario: spawning in an empty room would cause
        the game to hang because the turn state machine got stuck.
        """
        # Create game engine with AISystem
        engine = GameEngine(target_fps=60)
        ai_system = AISystem(priority=50)
        engine.register_system(ai_system)
        
        # Initialize with NO enemies (just player)
        engine.state_manager = GameStateManager()
        player = MockPlayer()
        entities = [player]  # Empty room
        
        engine.state_manager.initialize_game(
            player=player,
            entities=entities,
            game_map=MockGameMap(),
            message_log=MockMessageLog(),
            game_state=GameStates.PLAYERS_TURN,
            constants={}
        )
        
        # Enable bot mode
        engine.disable_enemy_ai_for_bot = True
        
        # Start engine
        engine.start()
        
        # Run multiple cycles to verify no hang
        for cycle in range(20):
            # Player turn
            assert engine.state_manager.state.current_state == GameStates.PLAYERS_TURN
            
            # Transition to ENEMY_TURN
            engine.state_manager.set_game_state(GameStates.ENEMY_TURN)
            engine.turn_manager.advance_turn(TurnPhase.ENEMY)
            
            # Update (should not hang)
            engine.update()
            
            # Should be back to PLAYERS_TURN
            assert engine.state_manager.state.current_state == GameStates.PLAYERS_TURN
        
        # Test completes without hanging
        assert True, "Bot mode with empty room completed without hanging"

