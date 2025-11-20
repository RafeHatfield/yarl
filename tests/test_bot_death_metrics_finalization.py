"""Tests for bot death metrics finalization fix.

This module tests that run_metrics are properly finalized and bot results
summary is written when the player dies during an enemy turn (AISystem path),
not just when dying during a player action (ActionProcessor path).
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from engine import GameEngine
from engine.systems.ai_system import AISystem
from engine.game_state_manager import GameStateManager
from game_states import GameStates
from instrumentation.run_metrics import (
    initialize_run_metrics_recorder,
    reset_run_metrics_recorder,
    get_run_metrics_recorder,
)
from components.component_registry import ComponentType
from components.statistics import Statistics


class MockPlayer:
    """Mock player entity."""
    
    def __init__(self):
        self.name = "Player"
        self.x = 1
        self.y = 1
        self.fighter = Mock()
        self.fighter.hp = 0  # Dead
        self.fighter.max_hp = 100
        
        # Statistics component
        self.stats = Statistics()
        self.stats.total_kills = 3
        self.stats.deepest_level = 2
        self.stats.turns_taken = 50
        self.stats.items_picked_up = 2
        self.stats.portals_used = 1
    
    def get_component_optional(self, component_type):
        if component_type == ComponentType.STATISTICS:
            return self.stats
        return None


class MockEnemy:
    """Mock enemy entity."""
    
    def __init__(self, name="Orc"):
        self.name = name
        self.x = 2
        self.y = 2
        self.fighter = Mock()
        self.fighter.hp = 50
        self.fighter.max_hp = 50
        
        # AI component
        self.ai = Mock()
        self.ai.take_turn = Mock()
    
    def get_component_optional(self, component_type):
        return None


class MockGameMap:
    """Mock game map."""
    
    def __init__(self):
        self.width = 10
        self.height = 10
        self.tiles = [[Mock(explored=True) for _ in range(10)] for _ in range(10)]


class MockMessageLog:
    """Mock message log."""
    
    def __init__(self):
        self.messages = []
    
    def add_message(self, message):
        self.messages.append(message)


class TestBotDeathMetricsFinalization:
    """Test that player death finalizes metrics regardless of death source."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Reset run metrics recorder before each test
        reset_run_metrics_recorder()
    
    def teardown_method(self):
        """Clean up after each test."""
        reset_run_metrics_recorder()
    
    def test_ai_system_player_death_finalizes_metrics(self):
        """Test that AISystem player death finalizes run_metrics.
        
        This is the core bug fix: when player dies during enemy turn,
        run_metrics should be finalized and stored on game_state.
        """
        # Initialize run metrics recorder in bot mode
        initialize_run_metrics_recorder(mode="bot")
        
        # Create game engine with AISystem
        engine = GameEngine(target_fps=60)
        ai_system = AISystem(priority=50)
        engine.register_system(ai_system)
        
        # Initialize state manager
        engine.state_manager = GameStateManager()
        player = MockPlayer()
        enemy = MockEnemy("Orc")
        entities = [player, enemy]
        
        constants = {
            "input_config": {"bot_enabled": True}
        }
        
        engine.state_manager.initialize_game(
            player=player,
            entities=entities,
            game_map=MockGameMap(),
            message_log=MockMessageLog(),
            game_state=GameStates.ENEMY_TURN,
            constants=constants
        )
        
        # Initialize AI system with engine
        ai_system.initialize(engine)
        
        # Simulate enemy attack that kills player
        # This mimics what happens in AISystem._process_ai_results()
        results = [{
            "dead": player,  # Player died
            "message": Mock()
        }]
        
        # Process AI results (this should trigger finalize_player_death)
        ai_system._process_ai_results(results, engine.state_manager.state)
        
        # ASSERT: run_metrics should be finalized and stored on game_state
        run_metrics = getattr(engine.state_manager.state, 'run_metrics', None)
        assert run_metrics is not None, "run_metrics should be stored on game_state after player death"
        assert run_metrics.outcome == "death", f"Expected outcome='death', got '{run_metrics.outcome}'"
        assert run_metrics.mode == "bot", f"Expected mode='bot', got '{run_metrics.mode}'"
        assert run_metrics.monsters_killed == 3, f"Expected 3 kills, got {run_metrics.monsters_killed}"
        assert run_metrics.deepest_floor == 2, f"Expected floor 2, got {run_metrics.deepest_floor}"
        
        # ASSERT: Game state should be PLAYER_DEAD
        assert engine.state_manager.state.current_state == GameStates.PLAYER_DEAD, \
            f"Expected PLAYER_DEAD state, got {engine.state_manager.state.current_state}"
        
        # ASSERT: Death message should be added
        assert len(engine.state_manager.state.message_log.messages) > 0, \
            "Death message should be added to message log"
    
    def test_action_processor_player_death_still_works(self):
        """Regression test: ensure ActionProcessor path still finalizes metrics.
        
        This ensures we didn't break the existing working path.
        """
        from game_actions import ActionProcessor
        from engine.game_state_manager import GameStateManager
        from systems.turn_controller import initialize_turn_controller
        from engine.turn_manager import TurnManager
        
        # Initialize run metrics recorder in bot mode
        initialize_run_metrics_recorder(mode="bot")
        
        # Create state manager
        state_manager = GameStateManager()
        player = MockPlayer()
        entities = [player]
        
        constants = {
            "input_config": {"bot_enabled": True}
        }
        
        # Set up game state using update_state
        state_manager.update_state(
            player=player,
            entities=entities,
            game_map=MockGameMap(),
            message_log=MockMessageLog(),
            current_state=GameStates.PLAYERS_TURN,
            constants=constants
        )
        
        # Create ActionProcessor (it gets constants internally via get_constants())
        # We need to patch get_constants to return our test constants
        from config.game_constants import get_constants
        with patch('game_actions.get_constants', return_value=constants):
            action_processor = ActionProcessor(state_manager, is_bot_mode=True)
        
        # Simulate player death via ActionProcessor
        action_processor._handle_entity_death(player)
        
        # ASSERT: run_metrics should be finalized and stored
        run_metrics = getattr(state_manager.state, 'run_metrics', None)
        assert run_metrics is not None, "run_metrics should be stored on game_state after player death"
        assert run_metrics.outcome == "death", f"Expected outcome='death', got '{run_metrics.outcome}'"
        assert run_metrics.mode == "bot", f"Expected mode='bot', got '{run_metrics.mode}'"
        
        # ASSERT: Game state should be PLAYER_DEAD
        assert state_manager.state.current_state == GameStates.PLAYER_DEAD, \
            f"Expected PLAYER_DEAD state, got {state_manager.state.current_state}"
    
    @patch('engine_integration._log_bot_results_summary')
    def test_bot_results_summary_logged_on_ai_death(self, mock_log_summary):
        """Test that bot results summary is logged when player dies during enemy turn."""
        # Initialize run metrics recorder in bot mode
        initialize_run_metrics_recorder(mode="bot")
        
        # Create game engine with AISystem
        engine = GameEngine(target_fps=60)
        ai_system = AISystem(priority=50)
        engine.register_system(ai_system)
        
        # Initialize state manager
        engine.state_manager = GameStateManager()
        player = MockPlayer()
        enemy = MockEnemy("Orc")
        entities = [player, enemy]
        
        constants = {
            "input_config": {"bot_enabled": True}
        }
        
        engine.state_manager.initialize_game(
            player=player,
            entities=entities,
            game_map=MockGameMap(),
            message_log=MockMessageLog(),
            game_state=GameStates.ENEMY_TURN,
            constants=constants
        )
        
        # Initialize AI system with engine
        ai_system.initialize(engine)
        
        # Simulate enemy attack that kills player
        results = [{
            "dead": player,
            "message": Mock()
        }]
        
        # Process AI results (should trigger finalize_player_death and log summary)
        ai_system._process_ai_results(results, engine.state_manager.state)
        
        # ASSERT: Bot results summary should have been logged
        mock_log_summary.assert_called_once()
        call_args = mock_log_summary.call_args
        assert call_args[0][0].outcome == "death", "Summary should be logged with death outcome"
        assert call_args[0][1] == constants, "Summary should be logged with correct constants"
    
    def test_environment_system_player_death_finalizes_metrics(self):
        """Test that EnvironmentSystem player death also finalizes metrics.
        
        This ensures all death paths go through the shared helper.
        """
        from engine.systems.environment_system import EnvironmentSystem
        
        # Initialize run metrics recorder in bot mode
        initialize_run_metrics_recorder(mode="bot")
        
        # Create game engine with EnvironmentSystem
        engine = GameEngine(target_fps=60)
        env_system = EnvironmentSystem(priority=30)
        engine.register_system(env_system)
        
        # Initialize state manager
        engine.state_manager = GameStateManager()
        player = MockPlayer()
        entities = [player]
        
        constants = {
            "input_config": {"bot_enabled": True}
        }
        
        engine.state_manager.initialize_game(
            player=player,
            entities=entities,
            game_map=MockGameMap(),
            message_log=MockMessageLog(),
            game_state=GameStates.PLAYERS_TURN,
            constants=constants
        )
        
        # Initialize environment system with engine
        env_system.initialize(engine)
        
        # Simulate hazard death
        env_system._handle_hazard_death(player, "fire", engine.state_manager.state)
        
        # ASSERT: run_metrics should be finalized and stored
        run_metrics = getattr(engine.state_manager.state, 'run_metrics', None)
        assert run_metrics is not None, "run_metrics should be stored on game_state after hazard death"
        assert run_metrics.outcome == "death", f"Expected outcome='death', got '{run_metrics.outcome}'"
        
        # ASSERT: Game state should be PLAYER_DEAD
        assert engine.state_manager.state.current_state == GameStates.PLAYER_DEAD, \
            f"Expected PLAYER_DEAD state, got {engine.state_manager.state.current_state}"

