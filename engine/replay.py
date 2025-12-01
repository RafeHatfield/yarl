"""Replay system for recording and replaying bot/player actions.

This module provides minimal infrastructure for:
1. Recording actions during a game run (for later replay/debugging)
2. Replaying recorded actions to reproduce a run deterministically

CRITICAL DESIGN CONSTRAINTS:
- Replay must NOT bypass the normal action processing pipeline
- Replay must NOT introduce new game loops or threads
- Replay uses the same main loop, just substitutes the input source
- All actions go through the standard ECS/action processor path

Usage (Recording):
    logger = ActionLogger()
    logger.start(seed=12345)
    
    # During game loop, after each action:
    logger.log_action(tick=turn_count, action=action_dict)
    
    # At end of run:
    logger.save("logs/replays/run_12345.jsonl")

Usage (Replay):
    driver = ReplayDriver("logs/replays/run_12345.jsonl")
    seed = driver.get_seed()
    
    # In game loop, instead of querying input source:
    action = driver.get_next_action()
    if action is None:
        # Replay complete
        break
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Iterator

logger = logging.getLogger(__name__)


@dataclass
class ActionRecord:
    """A single recorded action from a game tick.
    
    Attributes:
        tick: Turn/tick number when action occurred
        action: The action dictionary (e.g., {"move": (1, 0)}, {"pickup": True})
        game_state: Optional game state name at time of action
        timestamp: ISO timestamp when action was recorded
    """
    tick: int
    action: Dict[str, Any]
    game_state: Optional[str] = None
    timestamp: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for JSON output."""
        return {
            "tick": self.tick,
            "action": self.action,
            "game_state": self.game_state,
            "timestamp": self.timestamp,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActionRecord":
        """Deserialize from dictionary."""
        return cls(
            tick=data.get("tick", 0),
            action=data.get("action", {}),
            game_state=data.get("game_state"),
            timestamp=data.get("timestamp", ""),
        )


@dataclass
class ReplayHeader:
    """Metadata header for a replay file.
    
    Attributes:
        seed: RNG seed used for this run
        persona: Bot persona used (if applicable)
        start_floor: Starting dungeon floor
        version: Replay format version
        recorded_at: ISO timestamp when recording started
    """
    seed: int
    persona: str = "balanced"
    start_floor: int = 1
    version: str = "1.0"
    recorded_at: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for JSON output."""
        return {
            "type": "header",
            "seed": self.seed,
            "persona": self.persona,
            "start_floor": self.start_floor,
            "version": self.version,
            "recorded_at": self.recorded_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReplayHeader":
        """Deserialize from dictionary."""
        return cls(
            seed=data.get("seed", 0),
            persona=data.get("persona", "balanced"),
            start_floor=data.get("start_floor", 1),
            version=data.get("version", "1.0"),
            recorded_at=data.get("recorded_at", ""),
        )


class ActionLogger:
    """Records actions during a game run for later replay.
    
    This logger is opt-in and has minimal overhead when not enabled.
    Actions are stored in memory and written to disk at the end of the run.
    
    Thread Safety: Not thread-safe. Intended for single-threaded game loop use.
    """
    
    def __init__(self):
        """Initialize an empty action logger."""
        self._actions: List[ActionRecord] = []
        self._header: Optional[ReplayHeader] = None
        self._enabled = False
        self._tick_counter = 0
    
    def start(
        self, 
        seed: int, 
        persona: str = "balanced", 
        start_floor: int = 1
    ) -> None:
        """Start recording a new run.
        
        Args:
            seed: RNG seed for this run
            persona: Bot persona name
            start_floor: Starting dungeon floor
        """
        self._header = ReplayHeader(
            seed=seed,
            persona=persona,
            start_floor=start_floor,
            recorded_at=datetime.now().isoformat(),
        )
        self._actions = []
        self._enabled = True
        self._tick_counter = 0
        logger.debug(f"ActionLogger started: seed={seed}, persona={persona}")
    
    def stop(self) -> None:
        """Stop recording actions."""
        self._enabled = False
        logger.debug(f"ActionLogger stopped: {len(self._actions)} actions recorded")
    
    def log_action(
        self, 
        action: Dict[str, Any], 
        game_state: Optional[str] = None,
        tick: Optional[int] = None,
    ) -> None:
        """Log a single action.
        
        Args:
            action: The action dictionary
            game_state: Optional current game state name
            tick: Optional tick number (auto-increments if not provided)
        """
        if not self._enabled:
            return
        
        if tick is None:
            tick = self._tick_counter
            self._tick_counter += 1
        else:
            self._tick_counter = tick + 1
        
        record = ActionRecord(
            tick=tick,
            action=action,
            game_state=game_state,
            timestamp=datetime.now().isoformat(),
        )
        self._actions.append(record)
    
    def save(self, path: str) -> None:
        """Save recorded actions to a JSONL file.
        
        Format: First line is header JSON, subsequent lines are action records.
        
        Args:
            path: Path to output file
        """
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            # Write header
            if self._header:
                f.write(json.dumps(self._header.to_dict()) + '\n')
            
            # Write actions
            for action in self._actions:
                f.write(json.dumps(action.to_dict()) + '\n')
        
        logger.info(f"Replay saved: {output_path} ({len(self._actions)} actions)")
    
    @property
    def action_count(self) -> int:
        """Number of actions recorded."""
        return len(self._actions)
    
    @property
    def is_enabled(self) -> bool:
        """Whether recording is currently enabled."""
        return self._enabled
    
    def get_actions(self) -> List[ActionRecord]:
        """Get a copy of the recorded actions (for testing)."""
        return list(self._actions)


class ReplayDriver:
    """Drives replay by feeding recorded actions into the game.
    
    CRITICAL: This driver provides actions to the game loop but does NOT
    bypass the normal action processing pipeline. The game loop should:
    1. Query this driver for the next action instead of input sources
    2. Pass the action through the normal ActionProcessor
    3. Let ECS systems handle the action as usual
    
    Usage:
        driver = ReplayDriver("path/to/replay.jsonl")
        seed = driver.get_seed()  # Set this seed before starting
        
        while not driver.is_complete():
            action = driver.get_next_action()
            # Pass action to normal action processor
            action_processor.process(action)
    """
    
    def __init__(self, replay_path: str):
        """Load a replay file.
        
        Args:
            replay_path: Path to the JSONL replay file
        """
        self._path = Path(replay_path)
        self._header: Optional[ReplayHeader] = None
        self._actions: List[ActionRecord] = []
        self._current_index = 0
        
        self._load()
    
    def _load(self) -> None:
        """Load the replay file into memory."""
        if not self._path.exists():
            raise FileNotFoundError(f"Replay file not found: {self._path}")
        
        with open(self._path, 'r') as f:
            for i, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    data = json.loads(line)
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping malformed line {i}: {e}")
                    continue
                
                # First line with type="header" is the header
                if data.get("type") == "header":
                    self._header = ReplayHeader.from_dict(data)
                else:
                    self._actions.append(ActionRecord.from_dict(data))
        
        logger.info(f"Replay loaded: {self._path} ({len(self._actions)} actions)")
    
    def get_seed(self) -> Optional[int]:
        """Get the RNG seed from the replay header."""
        return self._header.seed if self._header else None
    
    def get_persona(self) -> str:
        """Get the persona from the replay header."""
        return self._header.persona if self._header else "balanced"
    
    def get_start_floor(self) -> int:
        """Get the start floor from the replay header."""
        return self._header.start_floor if self._header else 1
    
    def get_next_action(self) -> Optional[Dict[str, Any]]:
        """Get the next action to replay.
        
        Returns:
            Action dictionary, or None if replay is complete
        """
        if self._current_index >= len(self._actions):
            return None
        
        record = self._actions[self._current_index]
        self._current_index += 1
        return record.action
    
    def peek_next_action(self) -> Optional[ActionRecord]:
        """Peek at the next action without advancing.
        
        Returns:
            Full ActionRecord, or None if replay is complete
        """
        if self._current_index >= len(self._actions):
            return None
        return self._actions[self._current_index]
    
    def is_complete(self) -> bool:
        """Check if all actions have been replayed."""
        return self._current_index >= len(self._actions)
    
    def reset(self) -> None:
        """Reset replay to the beginning."""
        self._current_index = 0
    
    @property
    def total_actions(self) -> int:
        """Total number of actions in the replay."""
        return len(self._actions)
    
    @property
    def actions_remaining(self) -> int:
        """Number of actions remaining to replay."""
        return len(self._actions) - self._current_index


# Global singleton for action logging (opt-in, disabled by default)
_action_logger: Optional[ActionLogger] = None


def get_action_logger() -> ActionLogger:
    """Get or create the global action logger singleton.
    
    Returns:
        The global ActionLogger instance
    """
    global _action_logger
    if _action_logger is None:
        _action_logger = ActionLogger()
    return _action_logger


def reset_action_logger() -> None:
    """Reset the global action logger (for testing)."""
    global _action_logger
    _action_logger = None

