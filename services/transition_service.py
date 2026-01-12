"""Transition Service - Canonical level transition request mechanism.

Phase 21.5: Provides a lightweight data structure for requesting level transitions
from trap triggers or other game events. This decouples the transition request
(created at trap execution point) from the transition execution (handled in
gameplay loop via game_map.next_floor()).

Purpose:
- Hole traps can request level transitions without directly calling next_floor()
- Scenario harness can verify transition requests without multi-level support
- Maintains single canonical transition execution point (game_map.next_floor)

Usage:
    from services.transition_service import TransitionRequest, get_transition_service
    
    # At trap trigger point:
    transition_service = get_transition_service()
    transition_service.request_transition("next_floor", "hole_trap", entity)
    
    # In gameplay loop (near stairs handling):
    if transition_service.has_pending_transition():
        request = transition_service.consume_transition()
        if request.transition_type == "next_floor":
            entities = game_map.next_floor(player, message_log, constants)
"""

from dataclasses import dataclass
from typing import Optional, Any
from logger_config import get_logger

logger = get_logger(__name__)


@dataclass
class TransitionRequest:
    """Represents a requested level transition.
    
    Phase 21.5: Created by hole traps (and potentially other sources) to request
    a level transition. The actual transition is executed by the gameplay loop.
    
    Attributes:
        transition_type: Type of transition ("next_floor", "prev_floor", etc.)
        cause: What triggered the transition ("hole_trap", "stairs", etc.)
        entity: Entity that triggered the transition (typically player)
    """
    transition_type: str
    cause: str
    entity: Any


class TransitionService:
    """Service for managing level transition requests.
    
    Phase 21.5: Provides a single canonical place to request and consume
    level transitions. This decouples trap triggers from level transition execution.
    """
    
    def __init__(self):
        """Initialize transition service."""
        self._pending_request: Optional[TransitionRequest] = None
    
    def request_transition(self, transition_type: str, cause: str, entity: Any) -> None:
        """Request a level transition.
        
        Args:
            transition_type: Type of transition ("next_floor", "prev_floor")
            cause: What triggered the transition ("hole_trap", "stairs")
            entity: Entity that triggered the transition
        """
        if self._pending_request is not None:
            logger.warning(
                f"Overwriting pending transition request: {self._pending_request.cause} "
                f"-> {cause}"
            )
        
        self._pending_request = TransitionRequest(
            transition_type=transition_type,
            cause=cause,
            entity=entity
        )
        
        logger.info(f"Transition requested: {transition_type} (cause: {cause}, entity: {entity.name})")
    
    def has_pending_transition(self) -> bool:
        """Check if there is a pending transition request.
        
        Returns:
            True if a transition is pending, False otherwise
        """
        return self._pending_request is not None
    
    def consume_transition(self) -> Optional[TransitionRequest]:
        """Consume and return the pending transition request.
        
        Returns:
            TransitionRequest if one was pending, None otherwise
        """
        request = self._pending_request
        self._pending_request = None
        
        if request:
            logger.info(f"Transition consumed: {request.transition_type} (cause: {request.cause})")
        
        return request
    
    def clear_transition(self) -> None:
        """Clear any pending transition request without consuming it."""
        if self._pending_request:
            logger.debug(f"Transition cleared: {self._pending_request.cause}")
        self._pending_request = None
    
    def get_pending_request(self) -> Optional[TransitionRequest]:
        """Get the pending request without consuming it.
        
        Returns:
            TransitionRequest if one is pending, None otherwise
        """
        return self._pending_request


# Singleton instance
_transition_service: Optional[TransitionService] = None


def get_transition_service() -> TransitionService:
    """Get the global transition service instance.
    
    Returns:
        TransitionService singleton
    """
    global _transition_service
    if _transition_service is None:
        _transition_service = TransitionService()
    return _transition_service


def reset_transition_service() -> None:
    """Reset the transition service (for testing)."""
    global _transition_service
    _transition_service = None
