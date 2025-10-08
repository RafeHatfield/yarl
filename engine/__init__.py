"""Game engine module.

This module contains the core game engine architecture including
the main GameEngine class and system management functionality.
"""

from .game_engine import GameEngine
from .system import System
from .turn_manager import TurnManager, TurnPhase

__all__ = ["GameEngine", "System", "TurnManager", "TurnPhase"]
