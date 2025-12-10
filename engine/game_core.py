"""IO-agnostic game façade coordinating input → turn progression → frame state.

GameCore centralizes the minimal orchestration that frontends need:
- Holds the canonical state_manager/turn_manager references.
- Exposes a TurnStateAdapter for consistent phase queries and synchronization.
- Provides helper methods to process input actions and decide when the world
  should tick (player turn gating) without depending on any rendering or input
  technology.

The intent is to route entrypoints (interactive, bot, soak, future frontends)
through this façade so turn progression lives in one place. Rendering and input
creation stay outside, honoring IO abstraction contracts.
"""

from __future__ import annotations

from components.component_registry import ComponentType
from game_states import GameStates
from io_layer.interfaces import ActionDict

from .turn_state_adapter import TurnStateAdapter


class GameCore:
    """Lightweight orchestration boundary for a single game instance.

    This class is intentionally small: it owns turn/phase synchronization and
    player-turn gating but defers game rules to ActionProcessor/systems and IO
    setup to callers.
    """

    def __init__(self, state_manager, turn_manager, action_processor) -> None:
        self.state_manager = state_manager
        self.turn_manager = turn_manager
        self.action_processor = action_processor
        self.turn_state = TurnStateAdapter(state_manager, turn_manager)

    # --------------------------------------------------------------------- API
    def process_input(self, action: ActionDict, mouse_action: ActionDict) -> None:
        """Apply player input through the shared action processor and sync phases.

        IMPORTANT: We must call process_actions when autoexplore is active even if
        there's no explicit input. The autoexplore turn processing logic lives inside
        ActionProcessor.process_actions (in the PLAYERS_TURN handling block), so
        skipping it when action/mouse_action are empty would cause autoexplore to
        stall after a single step.
        """
        if action or mouse_action or self._auto_explore_active():
            self.action_processor.process_actions(action, mouse_action)
        self._sync_turn_state()

    def should_tick_world(
        self,
        input_mode: str,
        action: ActionDict,
        mouse_action: ActionDict,
        first_frame: bool = False,
    ) -> bool:
        """Determine whether world systems should update this frame.

        Manual mode enforces the invariant: one player input (or auto-explore)
        → one world tick. Bot mode and non-player states always tick.
        """
        current_state = self.state_manager.state.current_state

        # Bots advance continuously; harnesses throttle externally.
        if input_mode == "bot":
            return True

        # Outside PLAYERS_TURN (menus, dialogue, enemy/env phases) always tick.
        if current_state != GameStates.PLAYERS_TURN:
            return True

        # First frame needs a render/update to show the map.
        if first_frame:
            return True

        has_action = bool(action or mouse_action)
        auto_explore_active = self._auto_explore_active()
        return has_action or auto_explore_active

    def frame_state(self):
        """Return the current game state snapshot for renderers/frontends."""
        return self.state_manager.state

    # --------------------------------------------------------------- Internals
    def _sync_turn_state(self) -> None:
        """Keep GameStates and TurnManager phases aligned via the adapter."""
        if not self.turn_state.has_turn_manager:
            return

        if (
            self.turn_state.is_player_turn()
            and not self.turn_state.is_player_phase_consistent()
        ):
            self.turn_state.set_player_state(GameStates.PLAYERS_TURN)
        elif (
            self.turn_state.is_enemy_turn()
            and not self.turn_state.is_enemy_phase_consistent()
        ):
            self.turn_state.set_enemy_state()

    def _auto_explore_active(self) -> bool:
        player = self.state_manager.state.player
        auto_explore = (
            player.get_component_optional(ComponentType.AUTO_EXPLORE) if player else None
        )
        return bool(auto_explore and auto_explore.is_active())
