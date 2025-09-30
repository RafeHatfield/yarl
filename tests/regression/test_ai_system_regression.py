"""Regression tests for AI system bugs.

This module contains tests specifically designed to prevent regression
of bugs that have been fixed in the AI system. Each test should be
clearly documented with the bug it prevents.
"""

import pytest
from unittest.mock import Mock, patch
import inspect

from engine.systems.ai_system import AISystem
from components.ai import BasicMonster, ConfusedMonster
from game_states import GameStates


class TestAISystemRegressions:
    """Regression tests for AI system bugs."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ai_system = AISystem()
        self.mock_engine = Mock()
        self.mock_state_manager = Mock()
        self.mock_game_state = Mock()

        self.mock_engine.state_manager = self.mock_state_manager
        self.mock_state_manager.state = self.mock_game_state
        self.mock_game_state.current_state = GameStates.ENEMY_TURN

        # Set up complete game state
        self.mock_player = Mock()
        self.mock_game_map = Mock()
        self.mock_fov_map = Mock()
        self.mock_entities = [self.mock_player]

        self.mock_game_state.player = self.mock_player
        self.mock_game_state.game_map = self.mock_game_map
        self.mock_game_state.fov_map = self.mock_fov_map
        self.mock_game_state.entities = self.mock_entities

        self.ai_system.initialize(self.mock_engine)

    def test_ai_take_turn_argument_signature_regression(self):
        """Regression test: Ensure AI take_turn is called with correct arguments.

        Bug: AISystem was calling BasicMonster.take_turn() with wrong number of arguments.
        The method expects (target, fov_map, game_map, entities) but was being called
        with (target, game_map, entities), missing fov_map.

        This test ensures the AISystem calls take_turn with the exact signature
        that BasicMonster and ConfusedMonster expect.
        """
        # Create a real BasicMonster AI to test against
        basic_monster = BasicMonster()
        basic_monster.owner = Mock()
        basic_monster.owner.name = "Test Orc"
        basic_monster.owner.x = 5
        basic_monster.owner.y = 5
        basic_monster.owner.fighter = Mock()
        basic_monster.owner.fighter.hp = 10

        # Create entity with real AI
        entity = Mock()
        entity.ai = basic_monster
        entity.fighter = Mock()
        entity.fighter.hp = 10
        entity.name = "Test Orc"

        # Mock the AI's take_turn method to verify arguments
        with patch.object(
            basic_monster, "take_turn", return_value=[]
        ) as mock_take_turn:
            self.ai_system._process_entity_turn(entity, self.mock_game_state)

            # Verify take_turn was called with exactly the right arguments
            mock_take_turn.assert_called_once_with(
                self.mock_player,  # target
                self.mock_fov_map,  # fov_map
                self.mock_game_map,  # game_map
                self.mock_entities,  # entities
            )

    def test_confused_monster_take_turn_signature_regression(self):
        """Regression test: Ensure ConfusedMonster.take_turn gets correct arguments.

        This ensures that ConfusedMonster AI also receives the correct arguments,
        preventing the same bug from affecting confused entities.
        """
        # Create a real ConfusedMonster AI
        previous_ai = Mock()
        confused_monster = ConfusedMonster(previous_ai, number_of_turns=5)
        confused_monster.owner = Mock()
        confused_monster.owner.name = "Confused Orc"
        confused_monster.owner.x = 5
        confused_monster.owner.y = 5
        confused_monster.owner.fighter = Mock()
        confused_monster.owner.fighter.hp = 10

        # Create entity with confused AI
        entity = Mock()
        entity.ai = confused_monster
        entity.fighter = Mock()
        entity.fighter.hp = 10
        entity.name = "Confused Orc"

        # Mock the AI's take_turn method to verify arguments
        with patch.object(
            confused_monster, "take_turn", return_value=[]
        ) as mock_take_turn:
            self.ai_system._process_entity_turn(entity, self.mock_game_state)

            # Verify take_turn was called with exactly the right arguments
            mock_take_turn.assert_called_once_with(
                self.mock_player,  # target
                self.mock_fov_map,  # fov_map
                self.mock_game_map,  # game_map
                self.mock_entities,  # entities
            )

    def test_ai_method_signature_compatibility_check(self):
        """Meta-test: Verify AI classes have compatible take_turn signatures.

        This test inspects the actual method signatures of AI classes to ensure
        they all expect the same arguments. If a new AI class is added with
        a different signature, this test will fail and alert us to update
        the AISystem accordingly.
        """
        # Get the signature of BasicMonster.take_turn
        basic_sig = inspect.signature(BasicMonster.take_turn)
        basic_params = list(basic_sig.parameters.keys())

        # Get the signature of ConfusedMonster.take_turn
        confused_sig = inspect.signature(ConfusedMonster.take_turn)
        confused_params = list(confused_sig.parameters.keys())

        # They should have the same parameter names (excluding 'self')
        assert basic_params == confused_params, (
            f"AI classes have incompatible take_turn signatures: "
            f"BasicMonster{basic_params} vs ConfusedMonster{confused_params}"
        )

        # Verify the expected signature matches what AISystem provides
        expected_params = ["self", "target", "fov_map", "game_map", "entities"]
        assert basic_params == expected_params, (
            f"BasicMonster.take_turn signature {basic_params} doesn't match "
            f"expected {expected_params}. AISystem may need updating."
        )

    def test_ai_system_handles_missing_fov_map_gracefully(self):
        """Regression test: Ensure AISystem handles missing fov_map gracefully.

        This tests the edge case where game_state.fov_map might be None,
        ensuring the system doesn't crash.
        """
        # Set fov_map to None
        self.mock_game_state.fov_map = None

        # Create entity with AI
        entity = Mock()
        entity.ai = Mock()
        entity.ai.take_turn = Mock(return_value=[])
        entity.fighter = Mock()
        entity.fighter.hp = 10
        entity.name = "Test Entity"

        # This should not raise an exception
        self.ai_system._process_entity_turn(entity, self.mock_game_state)

        # Verify take_turn was still called (with None fov_map)
        entity.ai.take_turn.assert_called_once_with(
            self.mock_player,  # target
            None,  # fov_map (None)
            self.mock_game_map,  # game_map
            self.mock_entities,  # entities
        )

    def test_ai_system_integration_with_real_ai_classes(self):
        """Integration test: Verify AISystem works with actual AI implementations.

        This test uses real AI classes (not mocks) to ensure the integration
        works end-to-end and catches any signature mismatches.
        """
        # Create a real entity with BasicMonster AI
        entity = Mock()
        entity.name = "Integration Test Orc"
        entity.x = 10
        entity.y = 10
        entity.fighter = Mock()
        entity.fighter.hp = 15
        entity.fighter.attack = Mock(return_value=[])
        entity.distance_to = Mock(return_value=5)  # Far from player
        entity.move_astar = Mock()
        
        # Ensure no item usage or item seeking to avoid interference
        entity.item_usage = None
        entity.item_seeking_ai = None

        # Create real BasicMonster AI
        basic_ai = BasicMonster()
        basic_ai.owner = entity
        entity.ai = basic_ai

        # Set up FOV map to return True (entity can see player)
        with patch("components.ai.map_is_in_fov", return_value=True):
            # This should execute without errors
            result = self.ai_system._process_entity_turn(entity, self.mock_game_state)

            # Verify the AI actually executed (entity tried to move)
            entity.move_astar.assert_called_once()


class TestAISystemInterfaceContract:
    """Tests to ensure AI system interface contracts are maintained."""

    def test_all_ai_classes_implement_take_turn(self):
        """Ensure all AI classes implement the take_turn method.

        This test discovers all AI classes and verifies they have
        the required take_turn method with the correct signature.
        """
        # Import all AI classes (add new ones here as they're created)
        ai_classes = [BasicMonster, ConfusedMonster]

        for ai_class in ai_classes:
            # Verify the class has a take_turn method
            assert hasattr(
                ai_class, "take_turn"
            ), f"{ai_class.__name__} must implement take_turn method"

            # Verify the method signature
            sig = inspect.signature(ai_class.take_turn)
            params = list(sig.parameters.keys())
            expected = ["self", "target", "fov_map", "game_map", "entities"]

            assert params == expected, (
                f"{ai_class.__name__}.take_turn has signature {params}, "
                f"expected {expected}"
            )

    def test_ai_system_provides_correct_arguments(self):
        """Verify AISystem._process_entity_turn provides all required arguments.

        This test ensures that when new arguments are added to AI take_turn
        methods, the AISystem is updated to provide them.
        """
        ai_system = AISystem()
        mock_engine = Mock()
        mock_state_manager = Mock()
        mock_game_state = Mock()

        # Set up complete game state with all required attributes
        required_attributes = ["player", "fov_map", "game_map", "entities"]

        for attr in required_attributes:
            setattr(mock_game_state, attr, Mock())

        mock_state_manager.state = mock_game_state
        mock_engine.state_manager = mock_state_manager
        ai_system.initialize(mock_engine)

        # Create entity with mock AI
        entity = Mock()
        entity.ai = Mock()
        entity.ai.take_turn = Mock(return_value=[])
        entity.fighter = Mock()
        entity.fighter.hp = 10
        entity.name = "Test Entity"

        # Process the turn
        ai_system._process_entity_turn(entity, mock_game_state)

        # Verify all required arguments were provided
        call_args = entity.ai.take_turn.call_args[0]
        expected_args = [
            mock_game_state.player,
            mock_game_state.fov_map,
            mock_game_state.game_map,
            mock_game_state.entities,
        ]

        assert len(call_args) == len(expected_args), (
            f"AISystem provides {len(call_args)} arguments, "
            f"expected {len(expected_args)}"
        )

        for i, (actual, expected) in enumerate(zip(call_args, expected_args)):
            assert (
                actual is expected
            ), f"Argument {i}: got {actual}, expected {expected}"
