"""Turn Manager System.

Centralized turn sequencing and phase management for the game engine.
Replaces scattered turn logic across multiple systems.
"""

from enum import Enum
from typing import Dict, List, Callable, Optional, Any
import logging

logger = logging.getLogger(__name__)


class TurnPhase(Enum):
    """Turn phases in sequence.
    
    The game progresses through phases in order:
    PLAYER → ENEMY → ENVIRONMENT → PLAYER (cycle repeats)
    """
    PLAYER = "player"           # Player input and actions
    ENEMY = "enemy"             # AI processing for all monsters
    ENVIRONMENT = "environment" # Hazards, timed events, environmental effects
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"TurnPhase.{self.name}"


class TurnManager:
    """Manages turn phases and sequencing.
    
    The TurnManager is the single source of truth for "whose turn is it?"
    Systems register listeners to be notified when phases start/end.
    
    Example:
        manager = TurnManager()
        manager.register_listener(TurnPhase.ENEMY, ai_system.process_turn, "start")
        
        # Advance turn
        manager.advance_turn()  # PLAYER → ENEMY
        manager.advance_turn()  # ENEMY → ENVIRONMENT  
        manager.advance_turn()  # ENVIRONMENT → PLAYER (turn 2 begins!)
    """
    
    def __init__(self, start_phase: TurnPhase = TurnPhase.PLAYER):
        """Initialize turn manager.
        
        Args:
            start_phase: Starting turn phase (default: PLAYER)
        """
        self.current_phase: TurnPhase = start_phase
        self.turn_number: int = 1
        self.phase_in_progress: bool = False
        
        # Event listeners: {phase: {"start": [callbacks], "end": [callbacks]}}
        self._listeners: Dict[TurnPhase, Dict[str, List[Callable]]] = {
            phase: {"start": [], "end": []} for phase in TurnPhase
        }
        
        # Turn history for debugging
        self._history: List[Dict[str, Any]] = []
        self._max_history = 100  # Keep last 100 turns
        
        logger.info(f"TurnManager initialized: Starting phase={start_phase}, turn={self.turn_number}")
    
    @property
    def phase_name(self) -> str:
        """Get current phase name as string."""
        return self.current_phase.value
    
    def is_phase(self, phase: TurnPhase) -> bool:
        """Check if currently in specified phase.
        
        Args:
            phase: Phase to check
            
        Returns:
            bool: True if current phase matches
        """
        return self.current_phase == phase
    
    def advance_turn(self, to_phase: Optional[TurnPhase] = None) -> TurnPhase:
        """Advance to next turn phase.
        
        If no phase specified, automatically advances to next phase in sequence.
        Notifies listeners of phase transitions.
        
        Args:
            to_phase: Optional specific phase to transition to (for special cases)
            
        Returns:
            TurnPhase: The new current phase
        """
        if self.phase_in_progress:
            logger.warning(f"Attempted to advance turn while phase {self.current_phase} still in progress")
            return self.current_phase
        
        # Auto-advance if no phase specified
        if to_phase is None:
            to_phase = self._get_next_phase()
        
        old_phase = self.current_phase
        
        # Notify listeners of phase end
        self._notify_listeners(old_phase, "end")
        
        # Record in history BEFORE changing phase (so turn number is correct)
        self._record_phase_transition(old_phase, to_phase)
        
        # Switch phase
        self.current_phase = to_phase
        logger.debug(f"Turn {self.turn_number}: {old_phase} → {to_phase}")
        
        # Increment turn counter when cycle completes (ENV → PLAYER)
        if old_phase == TurnPhase.ENVIRONMENT and to_phase == TurnPhase.PLAYER:
            self.turn_number += 1
            logger.info(f"=== Turn {self.turn_number} begins ===")
        
        # Notify listeners of phase start
        self._notify_listeners(to_phase, "start")
        
        return to_phase
    
    def register_listener(self, phase: TurnPhase, callback: Callable, 
                         event: str = "start") -> None:
        """Register callback for phase events.
        
        Args:
            phase: Phase to listen to
            callback: Function to call when event occurs
            event: Event type ("start" or "end")
            
        Raises:
            ValueError: If event is not "start" or "end"
        """
        if event not in ("start", "end"):
            raise ValueError(f"Event must be 'start' or 'end', got: {event}")
        
        self._listeners[phase][event].append(callback)
        callback_name = getattr(callback, '__name__', repr(callback))
        logger.debug(f"Registered listener for {phase}.{event}: {callback_name}")
    
    def unregister_listener(self, phase: TurnPhase, callback: Callable, 
                           event: str = "start") -> bool:
        """Unregister callback for phase events.
        
        Args:
            phase: Phase to stop listening to
            callback: Function to remove
            event: Event type ("start" or "end")
            
        Returns:
            bool: True if callback was found and removed
        """
        if event not in ("start", "end"):
            return False
        
        try:
            self._listeners[phase][event].remove(callback)
            callback_name = getattr(callback, '__name__', repr(callback))
            logger.debug(f"Unregistered listener for {phase}.{event}: {callback_name}")
            return True
        except ValueError:
            return False
    
    def start_phase(self) -> None:
        """Mark current phase as in progress.
        
        Used to prevent phase changes while processing is happening.
        """
        self.phase_in_progress = True
    
    def end_phase(self) -> None:
        """Mark current phase as complete.
        
        Allows phase transitions to occur.
        """
        self.phase_in_progress = False
    
    def get_history(self, last_n: int = 10) -> List[Dict[str, Any]]:
        """Get turn history for debugging.
        
        Args:
            last_n: Number of recent turns to return
            
        Returns:
            List of turn history entries
        """
        return self._history[-last_n:]
    
    def reset(self) -> None:
        """Reset turn manager to initial state."""
        self.current_phase = TurnPhase.PLAYER
        self.turn_number = 1
        self.phase_in_progress = False
        self._history.clear()
        logger.info("TurnManager reset to initial state")
    
    def _get_next_phase(self) -> TurnPhase:
        """Get next phase in natural sequence.
        
        Sequence: PLAYER → ENEMY → ENVIRONMENT → PLAYER
        
        Returns:
            TurnPhase: Next phase in cycle
        """
        sequence = [TurnPhase.PLAYER, TurnPhase.ENEMY, TurnPhase.ENVIRONMENT]
        try:
            current_idx = sequence.index(self.current_phase)
            next_idx = (current_idx + 1) % len(sequence)
            return sequence[next_idx]
        except ValueError:
            # Current phase not in sequence (shouldn't happen)
            logger.error(f"Unknown phase in sequence: {self.current_phase}")
            return TurnPhase.PLAYER
    
    def _notify_listeners(self, phase: TurnPhase, event: str) -> None:
        """Notify all registered listeners for a phase event.
        
        Args:
            phase: Phase that triggered event
            event: Event type ("start" or "end")
        """
        callbacks = self._listeners[phase][event]
        if callbacks:
            logger.debug(f"Notifying {len(callbacks)} listeners for {phase}.{event}")
            
        for callback in callbacks:
            try:
                callback()
            except Exception as e:
                callback_name = getattr(callback, '__name__', repr(callback))
                logger.error(f"Error in {phase}.{event} listener {callback_name}: {e}", 
                           exc_info=True)
    
    def _record_phase_transition(self, from_phase: TurnPhase, to_phase: TurnPhase) -> None:
        """Record phase transition in history.
        
        Args:
            from_phase: Phase transitioning from
            to_phase: Phase transitioning to
        """
        entry = {
            "turn": self.turn_number,
            "from": from_phase.value,
            "to": to_phase.value,
        }
        
        self._history.append(entry)
        
        # Trim history if too long
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
    
    def __repr__(self) -> str:
        return f"TurnManager(turn={self.turn_number}, phase={self.current_phase})"

