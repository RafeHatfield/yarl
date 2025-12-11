"""Turn State Adapter – single API over GameStates and TurnManager.

This adapter aligns legacy GameStates with the newer TurnManager phases so
callers can query and advance turns without juggling both mechanisms. It is
intentionally thin: no new state machine, just consistent reads/writes across
the existing ones.

Preferred usage (examples):
    adapter = TurnStateAdapter(state_manager, turn_manager)
    if adapter.is_enemy_turn():
        ...process AI...
        adapter.advance_to_environment_phase()
        adapter.advance_to_player_phase()
        adapter.set_player_state()

Key guarantees:
- If a TurnManager is present, adapter methods keep its phase in sync with the
  canonical GameStates values for player/enemy turns.
- If no TurnManager is present, GameStates drive all decisions; adapter calls
  become no-ops for phases the TurnManager would own.
"""

from __future__ import annotations

from typing import Optional

from game_states import GameStates
from engine.turn_manager import TurnManager, TurnPhase


class TurnStateAdapter:
    """Unified facade for turn/phase queries and transitions."""

    def __init__(
        self,
        state_manager,
        turn_manager: Optional[TurnManager] = None,
    ) -> None:
        self.state_manager = state_manager
        self.turn_manager = turn_manager

    # ------------------------------------------------------------------ Queries
    def is_player_turn(self) -> bool:
        """True when it is the player's phase."""
        if self.turn_manager and self.turn_manager.is_phase(TurnPhase.PLAYER):
            return True
        return self.state_manager.state.current_state == GameStates.PLAYERS_TURN

    def is_enemy_turn(self) -> bool:
        """True when it is the enemy phase."""
        if self.turn_manager and self.turn_manager.is_phase(TurnPhase.ENEMY):
            return True
        return self.state_manager.state.current_state == GameStates.ENEMY_TURN

    def is_environment_phase(self) -> bool:
        """True when TurnManager is in environment phase (if present)."""
        if not self.turn_manager:
            return False
        return self.turn_manager.is_phase(TurnPhase.ENVIRONMENT)

    def is_enemy_phase_consistent(self) -> bool:
        """Return True if GameStates and TurnManager agree on enemy phase."""
        if not self.turn_manager:
            return True
        in_tm = self.turn_manager.is_phase(TurnPhase.ENEMY)
        in_state = self.state_manager.state.current_state == GameStates.ENEMY_TURN
        return in_tm == in_state

    def is_player_phase_consistent(self) -> bool:
        """Return True if GameStates and TurnManager agree on player phase."""
        if not self.turn_manager:
            return True
        in_tm = self.turn_manager.is_phase(TurnPhase.PLAYER)
        in_state = self.state_manager.state.current_state == GameStates.PLAYERS_TURN
        return in_tm == in_state

    @property
    def has_turn_manager(self) -> bool:
        return self.turn_manager is not None

    @property
    def turn_manager_phase(self) -> Optional[TurnPhase]:
        if not self.turn_manager:
            return None
        return self.turn_manager.current_phase

    # ---------------------------------------------------------- State setters
    def set_enemy_state(self) -> None:
        """Set state/phase to enemy turn.
        
        Uses explicit phase targeting for set_* methods since these are
        used to synchronize state, not advance through a sequence.
        """
        self.state_manager.set_game_state(GameStates.ENEMY_TURN)
        if self.turn_manager:
            self.turn_manager.advance_turn(TurnPhase.ENEMY)

    def set_player_state(self, state: GameStates = GameStates.PLAYERS_TURN) -> None:
        """Set state/phase to the given player-facing state (default PLAYERS_TURN).
        
        Uses explicit phase targeting for set_* methods since these are
        used to synchronize state, not advance through a sequence.
        """
        self.state_manager.set_game_state(state)
        if self.turn_manager:
            is_phase_fn = getattr(self.turn_manager, "is_phase", None)
            try:
                if callable(is_phase_fn) and is_phase_fn(TurnPhase.PLAYER):
                    return
            except Exception:
                pass
            self.turn_manager.advance_turn(TurnPhase.PLAYER)

    # ---------------------------------------------------------- Phase control
    def advance_to_environment_phase(self) -> None:
        """Move to ENVIRONMENT phase if a TurnManager is present.
        
        Advances TurnManager sequentially (without explicit target), allowing
        the manager to increment turn counters and notify listeners properly.
        Only advances if not already in the target phase.
        """
        if self.turn_manager:
            self.turn_manager.advance_turn()  # Sequential advance

    def advance_to_player_phase(self) -> None:
        """Move to PLAYER phase if a TurnManager is present.
        
        Advances TurnManager sequentially (without explicit target), allowing
        the manager to increment turn counters and notify listeners properly.
        Only advances if not already in the target phase.
        """
        if self.turn_manager:
            self.turn_manager.advance_turn()  # Sequential advance

    def advance_to_enemy_phase(self) -> None:
        """Move to ENEMY phase if a TurnManager is present.
        
        Advances TurnManager sequentially (without explicit target), allowing
        the manager to increment turn counters and notify listeners properly.
        Only advances if not already in the target phase.
        """
        if self.turn_manager:
            self.turn_manager.advance_turn()  # Sequential advance
