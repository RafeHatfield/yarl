"""Tests for the AISystem."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import time

from engine.systems.ai_system import AISystem
from game_states import GameStates


class TestAISystemInitialization:
    """Test AISystem initialization."""

    def test_ai_system_initialization(self):
        """Test AISystem initialization with default values."""
        ai_system = AISystem()

        assert ai_system.name == "ai"
        assert ai_system.priority == 50  # Middle priority
        assert ai_system.ai_strategies == {}
        assert len(ai_system.ai_callbacks) == 4  # Default event types
        assert ai_system.turn_queue == []
        assert ai_system.current_turn_entity is None
        assert ai_system.turn_processing is False
        assert ai_system.ai_debug_mode is False

    def test_ai_system_custom_priority(self):
        """Test AISystem initialization with custom priority."""
        ai_system = AISystem(priority=25)

        assert ai_system.priority == 25

    def test_ai_system_has_default_callbacks(self):
        """Test that AISystem has default callback categories."""
        ai_system = AISystem()

        expected_callbacks = ["entity_death", "turn_start", "turn_end", "state_change"]
        for callback_type in expected_callbacks:
            assert callback_type in ai_system.ai_callbacks
            assert isinstance(ai_system.ai_callbacks[callback_type], list)


class TestAISystemMethods:
    """Test AISystem methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ai_system = AISystem()
        self.mock_engine = Mock()
        self.mock_state_manager = Mock()
        self.mock_engine.state_manager = self.mock_state_manager
        self.ai_system.initialize(self.mock_engine)

    def test_register_ai_strategy(self):
        """Test registering AI strategies."""
        strategy_func = Mock()

        self.ai_system.register_ai_strategy("aggressive", strategy_func)

        assert "aggressive" in self.ai_system.ai_strategies
        assert self.ai_system.ai_strategies["aggressive"] is strategy_func

    def test_unregister_ai_strategy(self):
        """Test unregistering AI strategies."""
        strategy_func = Mock()
        self.ai_system.register_ai_strategy("defensive", strategy_func)

        self.ai_system.unregister_ai_strategy("defensive")

        assert "defensive" not in self.ai_system.ai_strategies

    def test_unregister_nonexistent_strategy(self):
        """Test unregistering a strategy that doesn't exist."""
        # Should not raise an exception
        self.ai_system.unregister_ai_strategy("nonexistent")

    def test_register_ai_callback(self):
        """Test registering AI event callbacks."""
        callback = Mock()

        self.ai_system.register_ai_callback("entity_death", callback)

        assert callback in self.ai_system.ai_callbacks["entity_death"]

    def test_register_ai_callback_new_event_type(self):
        """Test registering callback for new event type."""
        callback = Mock()

        self.ai_system.register_ai_callback("custom_event", callback)

        assert "custom_event" in self.ai_system.ai_callbacks
        assert callback in self.ai_system.ai_callbacks["custom_event"]

    def test_unregister_ai_callback(self):
        """Test unregistering AI event callbacks."""
        callback = Mock()
        self.ai_system.register_ai_callback("turn_start", callback)

        self.ai_system.unregister_ai_callback("turn_start", callback)

        assert callback not in self.ai_system.ai_callbacks["turn_start"]

    def test_unregister_nonexistent_callback(self):
        """Test unregistering a callback that doesn't exist."""
        callback = Mock()
        # Should not raise an exception
        self.ai_system.unregister_ai_callback("turn_start", callback)

    def test_set_debug_mode(self):
        """Test enabling and disabling debug mode."""
        assert self.ai_system.ai_debug_mode is False

        self.ai_system.set_debug_mode(True)
        assert self.ai_system.ai_debug_mode is True

        self.ai_system.set_debug_mode(False)
        assert self.ai_system.ai_debug_mode is False

    def test_get_turn_stats(self):
        """Test getting turn statistics."""
        stats = self.ai_system.get_turn_stats()

        assert "total_turns" in stats
        assert "average_turn_time" in stats
        assert "entities_processed" in stats
        assert isinstance(stats, dict)

    def test_reset_turn_stats(self):
        """Test resetting turn statistics."""
        # Modify stats first
        self.ai_system.turn_stats["total_turns"] = 10
        self.ai_system.turn_stats["average_turn_time"] = 0.5

        self.ai_system.reset_turn_stats()

        assert self.ai_system.turn_stats["total_turns"] == 0
        assert self.ai_system.turn_stats["average_turn_time"] == 0.0
        assert self.ai_system.turn_stats["entities_processed"] == 0

    def test_pause_resume_ai(self):
        """Test pausing and resuming AI processing."""
        assert self.ai_system.enabled is True

        self.ai_system.pause_ai()
        assert self.ai_system.enabled is False

        self.ai_system.resume_ai()
        assert self.ai_system.enabled is True

    def test_cleanup(self):
        """Test cleanup method."""
        # Set up some state
        self.ai_system.register_ai_strategy("test", Mock())
        self.ai_system.register_ai_callback("test_event", Mock())
        self.ai_system.turn_queue = [Mock()]
        self.ai_system.current_turn_entity = Mock()
        self.ai_system.turn_processing = True

        self.ai_system.cleanup()

        assert len(self.ai_system.ai_strategies) == 0
        assert len(self.ai_system.ai_callbacks) == 0
        assert len(self.ai_system.turn_queue) == 0
        assert self.ai_system.current_turn_entity is None
        assert self.ai_system.turn_processing is False


class TestAISystemUpdate:
    """Test AISystem update method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ai_system = AISystem()
        self.mock_engine = Mock()
        self.mock_state_manager = Mock()
        self.mock_game_state = Mock()

        self.mock_engine.state_manager = self.mock_state_manager
        self.mock_state_manager.state = self.mock_game_state
        self.mock_game_state.current_state = GameStates.ENEMY_TURN
        
        # Mock player with pathfinding component
        from components.component_registry import ComponentType
        mock_pathfinding = Mock()
        mock_pathfinding.is_path_active.return_value = False
        mock_pathfinding.get_next_move.return_value = None
        self.mock_game_state.player = Mock()
        self.mock_game_state.player.pathfinding = mock_pathfinding
        # Mock new component access helper
        self.mock_game_state.player.get_component_optional = Mock(side_effect=lambda comp_type: 
            mock_pathfinding if comp_type == ComponentType.PATHFINDING else None)
        self.mock_game_state.entities = []

        self.ai_system.initialize(self.mock_engine)

    def test_update_without_engine(self):
        """Test update when no engine is available."""
        self.ai_system._engine = None

        # Should not raise any exceptions
        self.ai_system.update(0.016)

    def test_update_without_state_manager(self):
        """Test update when engine has no state manager."""
        self.mock_engine.state_manager = None

        # Should not raise any exceptions
        self.ai_system.update(0.016)

    def test_update_wrong_game_state(self):
        """Test update when not in enemy turn state."""
        self.mock_game_state.current_state = GameStates.PLAYERS_TURN
        
        # Phase 2: Add mock turn_manager
        from engine.turn_manager import TurnManager, TurnPhase
        mock_turn_manager = Mock(spec=TurnManager)
        mock_turn_manager.is_phase.return_value = False  # Not ENEMY phase
        self.mock_engine.turn_manager = mock_turn_manager

        with patch.object(self.ai_system, "_process_ai_turns") as mock_process:
            self.ai_system.update(0.016)
            mock_process.assert_not_called()

    def test_update_during_enemy_turn(self):
        """Test update during enemy turn state."""
        # Mock player with no active pathfinding
        mock_pathfinding = Mock()
        mock_pathfinding.is_path_active.return_value = False
        self.mock_game_state.player = Mock()
        self.mock_game_state.player.get_component_optional = Mock(return_value=mock_pathfinding)
        
        with patch.object(self.ai_system, "_process_ai_turns") as mock_process:
            self.ai_system.update(0.016)
            mock_process.assert_called_once_with(self.mock_game_state)

    def test_update_switches_to_player_turn(self):
        """Test that update switches back to player turn when AI is done."""
        self.ai_system.turn_processing = False  # AI processing complete

        # Mock the entities to avoid iteration error
        self.mock_game_state.entities = []
        
        # Mock player with pathfinding component that's not active
        from components.component_registry import ComponentType
        mock_pathfinding = Mock()
        mock_pathfinding.is_path_active.return_value = False
        mock_pathfinding.get_next_move.return_value = None
        self.mock_game_state.player = Mock()
        self.mock_game_state.player.pathfinding = mock_pathfinding
        # Mock new component access helper
        self.mock_game_state.player.get_component_optional = Mock(side_effect=lambda comp_type: 
            mock_pathfinding if comp_type == ComponentType.PATHFINDING else None)

        self.ai_system.update(0.016)

        self.mock_state_manager.set_game_state.assert_called_with(
            GameStates.PLAYERS_TURN
        )


class TestAISystemTurnProcessing:
    """Test AI turn processing methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ai_system = AISystem()
        self.mock_engine = Mock()
        self.mock_state_manager = Mock()
        self.mock_engine.state_manager = self.mock_state_manager
        self.ai_system.initialize(self.mock_engine)

        # Create mock entities
        self.mock_player = Mock()
        self.mock_ai_entity = Mock()
        self.mock_ai_entity.ai = Mock()
        self.mock_ai_entity.fighter = Mock()
        self.mock_ai_entity.fighter.hp = 10
        self.mock_ai_entity.name = "Orc"

        self.mock_dead_entity = Mock()
        self.mock_dead_entity.ai = Mock()
        self.mock_dead_entity.fighter = Mock()
        self.mock_dead_entity.fighter.hp = 0

        self.mock_game_state = Mock()
        self.mock_game_state.entities = [
            self.mock_player,
            self.mock_ai_entity,
            self.mock_dead_entity,
        ]
        self.mock_game_state.player = self.mock_player
        self.mock_game_state.game_map = Mock()
        self.mock_game_state.fov_map = Mock()

    def test_get_ai_entities(self):
        """Test getting AI entities that should take turns."""
        entities = self.ai_system._get_ai_entities(
            self.mock_game_state.entities, self.mock_game_state.player
        )

        # Should only include living AI entities, not player or dead entities
        assert len(entities) == 1
        assert entities[0] == self.mock_ai_entity

    def test_get_ai_entities_no_ai(self):
        """Test getting AI entities when none have AI."""
        no_ai_entity = Mock()
        no_ai_entity.ai = None
        entities = [self.mock_player, no_ai_entity]

        result = self.ai_system._get_ai_entities(entities, self.mock_player)

        assert len(result) == 0

    def test_process_ai_turns(self):
        """Test processing AI turns."""
        with patch.object(
            self.ai_system, "_process_entity_turn"
        ) as mock_process_turn, patch.object(
            self.ai_system, "_get_ai_entities", return_value=[self.mock_ai_entity]
        ):

            self.ai_system._process_ai_turns(self.mock_game_state)

            mock_process_turn.assert_called_once_with(
                self.mock_ai_entity, self.mock_game_state
            )

    def test_process_ai_turns_handles_death(self):
        """Test that AI turns handle entity death."""
        # Create entity that will die during processing
        dying_entity = Mock()
        dying_entity.ai = Mock()
        dying_entity.fighter = Mock()
        dying_entity.fighter.hp = 10  # Alive initially
        dying_entity.name = "Goblin"

        def kill_entity_during_turn(entity, game_state):
            # Simulate entity dying during turn processing
            entity.fighter.hp = 0

        with patch.object(
            self.ai_system, "_process_entity_turn", side_effect=kill_entity_during_turn
        ) as mock_process_turn, patch.object(
            self.ai_system, "_handle_entity_death"
        ) as mock_handle_death, patch.object(
            self.ai_system, "_get_ai_entities", return_value=[dying_entity]
        ):

            self.ai_system._process_ai_turns(self.mock_game_state)

            mock_process_turn.assert_called_once_with(
                dying_entity, self.mock_game_state
            )
            mock_handle_death.assert_called_once_with(
                dying_entity, self.mock_game_state
            )

    def test_process_ai_turns_prevents_recursion(self):
        """Test that AI turn processing prevents recursion."""
        self.ai_system.turn_processing = True

        with patch.object(self.ai_system, "_get_ai_entities") as mock_get_entities:
            self.ai_system._process_ai_turns(self.mock_game_state)
            mock_get_entities.assert_not_called()

    def test_process_entity_turn_default_ai(self):
        """Test processing entity turn with default AI."""
        with patch.object(self.ai_system, "_notify_callbacks") as mock_notify:
            self.ai_system._process_entity_turn(
                self.mock_ai_entity, self.mock_game_state
            )

            # Should call the entity's AI take_turn method
            self.mock_ai_entity.ai.take_turn.assert_called_once_with(
                self.mock_game_state.player,
                self.mock_game_state.fov_map,
                self.mock_game_state.game_map,
                self.mock_game_state.entities,
            )

            # Should notify callbacks
            assert mock_notify.call_count >= 2  # turn_start and turn_end

    def test_process_entity_turn_custom_strategy(self):
        """Test processing entity turn with custom AI strategy."""
        # Register custom strategy
        custom_strategy = Mock()
        self.ai_system.register_ai_strategy("aggressive", custom_strategy)

        # Set entity to use custom strategy
        self.mock_ai_entity.ai.ai_type = "aggressive"

        self.ai_system._process_entity_turn(self.mock_ai_entity, self.mock_game_state)

        # Should call custom strategy instead of default AI
        custom_strategy.assert_called_once_with(
            self.mock_ai_entity,
            self.mock_game_state.player,
            self.mock_game_state.game_map,
            self.mock_game_state.entities,
        )
        self.mock_ai_entity.ai.take_turn.assert_not_called()

    def test_process_entity_turn_handles_exception(self):
        """Test that entity turn processing handles exceptions gracefully."""
        self.mock_ai_entity.ai.take_turn.side_effect = Exception("AI Error")

        # Should not raise exception
        self.ai_system._process_entity_turn(self.mock_ai_entity, self.mock_game_state)

    def test_handle_entity_death(self):
        """Test handling entity death."""
        with patch.object(self.ai_system, "_notify_callbacks") as mock_notify:
            self.ai_system._handle_entity_death(
                self.mock_ai_entity, self.mock_game_state
            )

            mock_notify.assert_called_with("entity_death", self.mock_ai_entity)

    def test_handle_entity_death_requests_fov_recompute(self):
        """Test that entity death requests FOV recompute."""
        self.mock_engine.state_manager.request_fov_recompute = Mock()

        self.ai_system._handle_entity_death(self.mock_ai_entity, self.mock_game_state)

        self.mock_engine.state_manager.request_fov_recompute.assert_called_once()


class TestAISystemCallbacks:
    """Test AI system callback functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ai_system = AISystem()

    def test_notify_callbacks(self):
        """Test notifying callbacks for events."""
        callback1 = Mock()
        callback2 = Mock()
        entity = Mock()

        self.ai_system.register_ai_callback("turn_start", callback1)
        self.ai_system.register_ai_callback("turn_start", callback2)

        self.ai_system._notify_callbacks("turn_start", entity)

        callback1.assert_called_once_with(entity)
        callback2.assert_called_once_with(entity)

    def test_notify_callbacks_handles_exception(self):
        """Test that callback notification handles exceptions gracefully."""
        failing_callback = Mock(side_effect=Exception("Callback error"))
        working_callback = Mock()
        entity = Mock()

        self.ai_system.register_ai_callback("turn_end", failing_callback)
        self.ai_system.register_ai_callback("turn_end", working_callback)

        # Should not raise exception
        self.ai_system._notify_callbacks("turn_end", entity)

        # Working callback should still be called
        working_callback.assert_called_once_with(entity)

    def test_notify_callbacks_nonexistent_event(self):
        """Test notifying callbacks for non-existent event type."""
        entity = Mock()

        # Should not raise exception
        self.ai_system._notify_callbacks("nonexistent_event", entity)


class TestAISystemStatistics:
    """Test AI system statistics tracking."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ai_system = AISystem()

    def test_update_turn_stats(self):
        """Test updating turn statistics."""
        initial_stats = self.ai_system.get_turn_stats()
        assert initial_stats["total_turns"] == 0
        assert initial_stats["average_turn_time"] == 0.0

        self.ai_system._update_turn_stats(0.1)

        stats = self.ai_system.get_turn_stats()
        assert stats["total_turns"] == 1
        assert stats["average_turn_time"] == 0.1
        assert stats["entities_processed"] == 1

    def test_update_turn_stats_rolling_average(self):
        """Test that turn statistics calculate rolling average correctly."""
        self.ai_system._update_turn_stats(0.1)  # First turn: 0.1s
        self.ai_system._update_turn_stats(0.3)  # Second turn: 0.3s

        stats = self.ai_system.get_turn_stats()
        assert stats["total_turns"] == 2
        assert stats["average_turn_time"] == 0.2  # (0.1 + 0.3) / 2
        assert stats["entities_processed"] == 2


class TestAISystemIntegration:
    """Integration tests for AISystem."""

    def test_ai_system_with_engine(self):
        """Test AISystem integration with GameEngine."""
        from engine.game_engine import GameEngine

        ai_system = AISystem(priority=30)
        engine = GameEngine()
        engine.register_system(ai_system)

        assert engine.get_system("ai") is ai_system
        assert ai_system.engine is engine

        # Test update through engine
        with patch.object(ai_system, "update") as mock_update:
            engine.update()
            mock_update.assert_called_once()

    def test_ai_system_priority_ordering(self):
        """Test that AISystem has appropriate priority for proper ordering."""
        from engine.game_engine import GameEngine
        from engine.systems import RenderSystem, InputSystem

        input_system = InputSystem()  # Priority 10
        ai_system = AISystem()  # Priority 50
        render_system = RenderSystem(Mock(), Mock(), 80, 50, {}, priority=100)

        engine = GameEngine()
        engine.register_system(render_system)
        engine.register_system(ai_system)
        engine.register_system(input_system)

        # Should be ordered: input, ai, render
        system_names = list(engine.systems.keys())
        assert system_names.index("input") < system_names.index("ai")
        assert system_names.index("ai") < system_names.index("render")

    def test_get_active_ai_entities_integration(self):
        """Test getting active AI entities with full integration."""
        ai_system = AISystem()
        mock_engine = Mock()
        mock_state_manager = Mock()
        mock_game_state = Mock()

        # Set up mock entities
        player = Mock()
        ai_entity = Mock()
        ai_entity.ai = Mock()
        ai_entity.fighter = Mock()
        ai_entity.fighter.hp = 10

        mock_game_state.entities = [player, ai_entity]
        mock_game_state.player = player
        mock_state_manager.state = mock_game_state
        mock_engine.state_manager = mock_state_manager

        ai_system.initialize(mock_engine)

        active_entities = ai_system.get_active_ai_entities()

        assert len(active_entities) == 1
        assert active_entities[0] == ai_entity
