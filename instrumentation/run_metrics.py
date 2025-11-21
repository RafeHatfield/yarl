"""Run metrics tracking for gameplay sessions.

This module provides a comprehensive metrics system for tracking individual game runs,
supporting both human and bot play modes. It integrates cleanly with the existing
telemetry infrastructure without duplicating counters from the Statistics component.

Architecture:
- RunMetrics: Immutable data class representing a completed run
- RunMetricsRecorder: Stateful recorder that captures run lifecycle and builds final metrics

Integration Points:
- Initialized in get_game_variables() (run start)
- Finalized on death/victory/quit (run end)
- Consumed by TelemetryService for JSON export
- Displayed in death/victory screens for user feedback
"""

import logging
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Literal

logger = logging.getLogger(__name__)


@dataclass
class RunMetrics:
    """Immutable record of a single game run's metrics.
    
    This class represents the final state of a completed run. It is designed to be
    easily serializable to JSON for telemetry output and human-readable for display.
    
    Attributes:
        run_id: Unique identifier for this run (UUID hex)
        mode: "human" for keyboard input, "bot" for automated play
        seed: Optional RNG seed (for future deterministic replay)
        
        start_time_utc: When the run started (ISO 8601 format)
        end_time_utc: When the run ended (ISO 8601 format, None if in progress)
        duration_seconds: Total run duration (None if in progress)
        
        deepest_floor: Deepest dungeon level reached
        floors_visited: Total unique floors visited
        start_floor: Starting floor for this run (default: 1)
        
        steps_taken: Total player movement steps (from turns_taken)
        tiles_explored: Total map tiles explored
        
        monsters_killed: Total monsters defeated
        items_picked_up: Total items picked up from ground
        portals_used: Total portals created/used (wand of portals)
        
        outcome: Final outcome - "death", "victory", "quit", "bot_abort", "max_turns", "max_floors", "in_progress"
        max_turns_limit: Optional maximum turns limit for this run
        max_floors_limit: Optional maximum floors limit for this run
    """
    run_id: str
    mode: Literal["human", "bot"]
    seed: Optional[int] = None
    
    start_time_utc: str = ""
    end_time_utc: Optional[str] = None
    duration_seconds: Optional[float] = None
    
    deepest_floor: int = 1
    floors_visited: int = 1
    start_floor: int = 1
    
    steps_taken: int = 0
    tiles_explored: int = 0
    
    monsters_killed: int = 0
    items_picked_up: int = 0
    portals_used: int = 0
    
    outcome: Literal["death", "victory", "quit", "bot_abort", "max_turns", "max_floors", "in_progress"] = "in_progress"
    max_turns_limit: Optional[int] = None
    max_floors_limit: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for JSON export.
        
        Returns:
            Dictionary representation suitable for telemetry JSON
        """
        return asdict(self)
    
    def get_summary_text(self) -> str:
        """Generate human-readable summary for death/victory screens.
        
        Returns:
            Multi-line string summarizing the run
        """
        lines = []
        
        # Mode indicator (unobtrusive)
        if self.mode == "bot":
            lines.append("[Bot Run]")
        
        # Core exploration stats
        if self.tiles_explored > 0 or self.steps_taken > 0:
            lines.append(
                f"You explored {self.tiles_explored} tiles over {self.steps_taken} steps "
                f"and reached floor {self.deepest_floor}."
            )
        
        # Combat and loot
        parts = []
        if self.monsters_killed > 0:
            parts.append(f"Monsters defeated: {self.monsters_killed}")
        if self.items_picked_up > 0:
            parts.append(f"Items collected: {self.items_picked_up}")
        if parts:
            lines.append(", ".join(parts))
        
        # Portal usage (if relevant)
        if self.portals_used > 0:
            lines.append(f"Portals used: {self.portals_used}")
        
        # Duration (if available)
        if self.duration_seconds is not None and self.duration_seconds > 0:
            minutes = int(self.duration_seconds // 60)
            seconds = int(self.duration_seconds % 60)
            if minutes > 0:
                lines.append(f"Run duration: {minutes}m {seconds}s")
            else:
                lines.append(f"Run duration: {seconds}s")
        
        return "\n".join(lines)


class RunMetricsRecorder:
    """Stateful recorder for building RunMetrics across a game run.
    
    This class is responsible for:
    - Creating a new run record on game start
    - Updating timestamps and outcome on run end
    - Computing final metrics from Statistics component and game state
    - Providing the final RunMetrics for telemetry and display
    
    Usage:
        # On game start
        recorder = RunMetricsRecorder(mode="human", seed=None)
        recorder.start()
        
        # On game end
        recorder.finalize(
            outcome="death",
            statistics=player.statistics,
            game_map=game_map
        )
        
        # Export metrics
        metrics = recorder.get_metrics()
        telemetry.add_run_metrics(metrics.to_dict())
    """
    
    def __init__(self, mode: Literal["human", "bot"], seed: Optional[int] = None, 
                 start_floor: int = 1, max_turns: Optional[int] = None, max_floors: Optional[int] = None):
        """Initialize recorder for a new run.
        
        Args:
            mode: "human" for keyboard input, "bot" for automated play
            seed: Optional RNG seed (for future deterministic replay)
            start_floor: Starting floor for this run (default: 1)
            max_turns: Optional maximum turns limit
            max_floors: Optional maximum floors limit
        """
        self.run_id = uuid.uuid4().hex
        self.mode = mode
        self.seed = seed
        self.start_floor = start_floor
        self.max_turns_limit = max_turns
        self.max_floors_limit = max_floors
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self._metrics: Optional[RunMetrics] = None
        
        logger.info(f"RunMetricsRecorder initialized: run_id={self.run_id}, mode={mode}, start_floor={start_floor}")
    
    def start(self) -> None:
        """Mark the run as started with current timestamp."""
        self.start_time = datetime.now(timezone.utc)
        logger.debug(f"Run started: {self.run_id} at {self.start_time.isoformat()}")
    
    def finalize(
        self,
        outcome: Literal["death", "victory", "quit", "bot_abort", "max_turns", "max_floors"],
        statistics,  # components.statistics.Statistics
        game_map,    # map_objects.game_map.GameMap
    ) -> None:
        """Finalize the run and compute metrics from game state.
        
        Args:
            outcome: Final outcome of the run
            statistics: Player's Statistics component (source of most counters)
            game_map: Current game map (for tiles_explored calculation)
        """
        self.end_time = datetime.now(timezone.utc)
        
        # Compute duration
        duration_seconds = None
        if self.start_time and self.end_time:
            duration_seconds = (self.end_time - self.start_time).total_seconds()
        
        # Compute tiles explored from game map
        tiles_explored = self._count_explored_tiles(game_map)
        
        # Build final metrics by pulling from Statistics component
        # (avoid duplicating counters - reuse existing tracking)
        self._metrics = RunMetrics(
            run_id=self.run_id,
            mode=self.mode,
            seed=self.seed,
            start_time_utc=self.start_time.isoformat() if self.start_time else "",
            end_time_utc=self.end_time.isoformat() if self.end_time else None,
            duration_seconds=duration_seconds,
            deepest_floor=statistics.deepest_level,
            floors_visited=statistics.deepest_level,  # Simplified: assume linear descent
            start_floor=self.start_floor,
            steps_taken=statistics.turns_taken,
            tiles_explored=tiles_explored,
            monsters_killed=statistics.total_kills,
            items_picked_up=statistics.items_picked_up,
            portals_used=statistics.portals_used,
            outcome=outcome,
            max_turns_limit=self.max_turns_limit,
            max_floors_limit=self.max_floors_limit,
        )
        
        logger.info(
            f"Run finalized: {self.run_id}, outcome={outcome}, "
            f"duration={duration_seconds:.1f}s, floor={statistics.deepest_level}"
        )
    
    def get_metrics(self) -> Optional[RunMetrics]:
        """Get the finalized run metrics.
        
        Returns:
            RunMetrics if finalized, None if still in progress
        """
        return self._metrics
    
    def is_finalized(self) -> bool:
        """Check if the run has been finalized.
        
        Returns:
            True if finalize() has been called
        """
        return self._metrics is not None
    
    def _count_explored_tiles(self, game_map) -> int:
        """Count explored tiles in the current game map.
        
        Args:
            game_map: GameMap instance with tiles[x][y].explored flags
            
        Returns:
            Total count of explored tiles
        """
        if not game_map or not hasattr(game_map, 'tiles'):
            return 0
        
        count = 0
        try:
            for x in range(game_map.width):
                for y in range(game_map.height):
                    if game_map.tiles[x][y].explored:
                        count += 1
        except (AttributeError, IndexError) as e:
            logger.warning(f"Failed to count explored tiles: {e}")
            return 0
        
        return count


# Global singleton instance
_run_metrics_recorder: Optional[RunMetricsRecorder] = None


def initialize_run_metrics_recorder(
    mode: Literal["human", "bot"],
    seed: Optional[int] = None,
    start_floor: int = 1,
    max_turns: Optional[int] = None,
    max_floors: Optional[int] = None
) -> RunMetricsRecorder:
    """Initialize the global run metrics recorder for a new game.
    
    This should be called once at the start of a new game (in get_game_variables).
    
    Args:
        mode: "human" for keyboard input, "bot" for automated play
        seed: Optional RNG seed (for future deterministic replay)
        start_floor: Starting floor for this run (default: 1)
        max_turns: Optional maximum turns limit
        max_floors: Optional maximum floors limit
        
    Returns:
        Initialized RunMetricsRecorder singleton
    """
    global _run_metrics_recorder
    _run_metrics_recorder = RunMetricsRecorder(
        mode=mode, 
        seed=seed,
        start_floor=start_floor,
        max_turns=max_turns,
        max_floors=max_floors
    )
    _run_metrics_recorder.start()
    return _run_metrics_recorder


def get_run_metrics_recorder() -> Optional[RunMetricsRecorder]:
    """Get the current run metrics recorder.
    
    Returns:
        Current RunMetricsRecorder if initialized, None otherwise
    """
    return _run_metrics_recorder


def reset_run_metrics_recorder() -> None:
    """Reset the global run metrics recorder (for testing)."""
    global _run_metrics_recorder
    _run_metrics_recorder = None


def finalize_run_metrics(
    outcome: Literal["death", "victory", "quit", "bot_abort", "max_turns", "max_floors"],
    player,
    game_map,
) -> Optional[RunMetrics]:
    """Finalize the current run metrics and return the result.
    
    This is a convenience function that calls finalize() on the global recorder
    and returns the metrics. It should be called at run end (death/victory/quit).
    
    Args:
        outcome: Final outcome of the run
        player: Player entity with statistics component
        game_map: Current game map
        
    Returns:
        Finalized RunMetrics, or None if no recorder exists
    """
    global _run_metrics_recorder
    
    if _run_metrics_recorder is None:
        logger.warning("finalize_run_metrics called but no recorder exists")
        return None
    
    # Get statistics component
    from components.component_registry import ComponentType
    statistics = player.get_component_optional(ComponentType.STATISTICS)
    if not statistics:
        logger.error("Player has no statistics component - cannot finalize run metrics")
        return None
    
    # Finalize and return
    _run_metrics_recorder.finalize(outcome, statistics, game_map)
    return _run_metrics_recorder.get_metrics()

