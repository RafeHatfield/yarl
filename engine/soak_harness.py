"""Bot soak harness for running multiple automated game sessions.

This module provides infrastructure for running multiple bot games back-to-back
for stability testing, telemetry collection, and performance analysis.

Phase 1.6: Bot Soak Harness
- Run N bot games sequentially
- Capture run_metrics and telemetry per run
- Aggregate session-level statistics
- Write per-run telemetry to JSONL format
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import json

logger = logging.getLogger(__name__)


@dataclass
class SoakRunResult:
    """Metrics snapshot for a single bot run.
    
    Attributes:
        run_number: Sequential run number (1-based)
        run_id: Unique run ID from RunMetrics
        outcome: Final outcome (death, victory, quit, bot_abort)
        duration_seconds: Run duration
        deepest_floor: Deepest floor reached
        floors_visited: Total floors visited
        monsters_killed: Total monsters defeated
        tiles_explored: Total tiles explored
        steps_taken: Total steps taken
        floor_count: Number of floors in telemetry
        avg_etp_per_floor: Average ETP per floor
        exception: Optional exception message if run crashed
    """
    run_number: int
    run_id: str = ""
    outcome: str = "unknown"
    duration_seconds: float = 0.0
    deepest_floor: int = 1
    floors_visited: int = 1
    monsters_killed: int = 0
    tiles_explored: int = 0
    steps_taken: int = 0
    floor_count: int = 0
    avg_etp_per_floor: float = 0.0
    exception: Optional[str] = None
    
    @classmethod
    def from_run_metrics_and_telemetry(
        cls, 
        run_number: int,
        run_metrics,  # RunMetrics or None
        telemetry_stats: Dict[str, Any],
        exception: Optional[str] = None
    ) -> "SoakRunResult":
        """Create from run metrics and telemetry.
        
        Args:
            run_number: Sequential run number
            run_metrics: RunMetrics instance or None
            telemetry_stats: Telemetry stats dict from get_stats()
            exception: Optional exception message
            
        Returns:
            SoakRunResult instance
        """
        if run_metrics:
            return cls(
                run_number=run_number,
                run_id=run_metrics.run_id,
                outcome=run_metrics.outcome,
                duration_seconds=run_metrics.duration_seconds or 0.0,
                deepest_floor=run_metrics.deepest_floor,
                floors_visited=run_metrics.floors_visited,
                monsters_killed=run_metrics.monsters_killed,
                tiles_explored=run_metrics.tiles_explored,
                steps_taken=run_metrics.steps_taken,
                floor_count=telemetry_stats.get('floors', 0),
                avg_etp_per_floor=telemetry_stats.get('avg_etp_per_floor', 0.0),
                exception=exception,
            )
        else:
            # Fallback for missing run_metrics
            return cls(
                run_number=run_number,
                outcome="error",
                floor_count=telemetry_stats.get('floors', 0),
                avg_etp_per_floor=telemetry_stats.get('avg_etp_per_floor', 0.0),
                exception=exception,
            )


@dataclass
class SoakSessionResult:
    """Aggregate statistics for a soak session.
    
    Attributes:
        total_runs: Total runs requested
        completed_runs: Runs that completed successfully
        bot_crashes: Runs that crashed with exceptions
        runs: List of per-run results
        session_duration_seconds: Total session duration
        avg_duration: Average run duration
        avg_deepest_floor: Average deepest floor reached
        avg_floors_per_run: Average floors visited per run
        total_monsters_killed: Total monsters killed across all runs
    """
    total_runs: int
    completed_runs: int = 0
    bot_crashes: int = 0
    runs: List[SoakRunResult] = field(default_factory=list)
    session_duration_seconds: float = 0.0
    avg_duration: float = 0.0
    avg_deepest_floor: float = 0.0
    avg_floors_per_run: float = 0.0
    total_monsters_killed: int = 0
    
    def compute_aggregates(self) -> None:
        """Compute aggregate statistics from run results."""
        if not self.runs:
            return
        
        # Filter out crashed runs for meaningful aggregates
        valid_runs = [r for r in self.runs if r.exception is None]
        
        if valid_runs:
            self.avg_duration = sum(r.duration_seconds for r in valid_runs) / len(valid_runs)
            self.avg_deepest_floor = sum(r.deepest_floor for r in valid_runs) / len(valid_runs)
            self.avg_floors_per_run = sum(r.floors_visited for r in valid_runs) / len(valid_runs)
            self.total_monsters_killed = sum(r.monsters_killed for r in self.runs)
    
    def print_summary(self) -> None:
        """Print human-readable session summary to stdout."""
        print("\n" + "="*60)
        print("🧪 Bot Soak Session Summary")
        print("="*60)
        print(f"   Runs: {self.total_runs}")
        print(f"   Completed: {self.completed_runs}")
        print(f"   Crashes: {self.bot_crashes}")
        print()
        print(f"   Session Duration: {self.session_duration_seconds:.1f}s")
        print(f"   Avg Run Duration: {self.avg_duration:.1f}s")
        print(f"   Avg Deepest Floor: {self.avg_deepest_floor:.1f}")
        print(f"   Avg Floors per Run: {self.avg_floors_per_run:.1f}")
        print(f"   Total Monsters Killed: {self.total_monsters_killed}")
        print("="*60)
        
        # Per-run breakdown (compact)
        if self.runs:
            print("\n📋 Per-Run Breakdown:")
            print(f"{'Run':<5} {'Outcome':<12} {'Duration':<10} {'Floor':<7} {'Kills':<7} {'Exception'}")
            print("-" * 70)
            for run in self.runs:
                duration_str = f"{run.duration_seconds:.1f}s"
                exception_str = run.exception[:30] if run.exception else ""
                print(f"{run.run_number:<5} {run.outcome:<12} {duration_str:<10} "
                      f"{run.deepest_floor:<7} {run.monsters_killed:<7} {exception_str}")


def run_bot_soak(
    runs: int,
    telemetry_enabled: bool,
    telemetry_output_path: Optional[str] = None,
    constants: Optional[Dict[str, Any]] = None,
) -> SoakSessionResult:
    """Run multiple bot games back-to-back for soak testing.
    
    This function orchestrates N sequential bot runs, capturing run_metrics
    and telemetry for each run. It resets global state between runs to ensure
    each run is independent.
    
    Args:
        runs: Number of bot runs to execute
        telemetry_enabled: Whether to collect telemetry
        telemetry_output_path: Base path for telemetry JSONL output
        constants: Game constants (if None, will call get_constants())
        
    Returns:
        SoakSessionResult with aggregate statistics
    """
    from loader_functions.initialize_new_game import get_constants, get_game_variables
    from engine_integration import play_game_with_engine, create_game_engine, initialize_game_engine
    from services.telemetry_service import get_telemetry_service, reset_telemetry_service
    from instrumentation.run_metrics import (
        get_run_metrics_recorder,
        reset_run_metrics_recorder,
        finalize_run_metrics,
    )
    from game_states import GameStates
    import tcod.libtcodpy as libtcod
    from config.ui_layout import get_ui_layout
    
    logger.info(f"Starting bot soak session: {runs} runs, telemetry={telemetry_enabled}")
    
    session_start = time.time()
    session_result = SoakSessionResult(total_runs=runs)
    
    # Get constants once (reuse across runs)
    if constants is None:
        constants = get_constants()
    
    # Enable bot mode in constants
    constants.setdefault("input_config", {})
    constants["input_config"]["bot_enabled"] = True
    
    # Get UI layout for console creation
    ui_layout = get_ui_layout()
    
    # Prepare telemetry JSONL output
    jsonl_path = None
    if telemetry_enabled and telemetry_output_path:
        base_path = Path(telemetry_output_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        jsonl_path = base_path.parent / f"{base_path.stem}_soak_{timestamp}.jsonl"
        jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Telemetry JSONL output: {jsonl_path}")
    
    # Run N bot games
    for run_num in range(1, runs + 1):
        logger.info(f"=== Starting run {run_num}/{runs} ===")
        print(f"\n🤖 Bot Run {run_num}/{runs}...")
        
        run_result = None
        exception_msg = None
        
        try:
            # Reset global singletons for clean run
            reset_run_metrics_recorder()
            reset_telemetry_service()
            
            # Initialize telemetry for this run
            if telemetry_enabled and telemetry_output_path:
                # Use a temporary path for this run (we'll extract JSON to JSONL)
                temp_telemetry_path = f"/tmp/rlike_soak_run_{run_num}.json"
                telemetry_service = get_telemetry_service(temp_telemetry_path)
            else:
                telemetry_service = get_telemetry_service(None)
            
            # Create new game
            player, entities, game_map, message_log, game_state = get_game_variables(constants)
            game_state = GameStates.PLAYERS_TURN
            
            # Create consoles (required for rendering)
            sidebar_console = libtcod.console_new(ui_layout.sidebar_width, ui_layout.screen_height)
            viewport_console = libtcod.console_new(ui_layout.viewport_width, ui_layout.viewport_height)
            status_console = libtcod.console_new(ui_layout.status_panel_width, ui_layout.status_panel_height)
            
            # Play the game in bot mode
            # Note: play_game_with_engine will return when the run ends (death/quit)
            result = play_game_with_engine(
                player,
                entities,
                game_map,
                message_log,
                game_state,
                sidebar_console,
                viewport_console,
                status_console,
                constants,
            )
            
            # Capture run metrics and telemetry
            run_metrics_recorder = get_run_metrics_recorder()
            run_metrics = run_metrics_recorder.get_metrics() if run_metrics_recorder else None
            
            telemetry_stats = telemetry_service.get_stats() if telemetry_service else {}
            
            # Create run result
            run_result = SoakRunResult.from_run_metrics_and_telemetry(
                run_number=run_num,
                run_metrics=run_metrics,
                telemetry_stats=telemetry_stats,
                exception=None,
            )
            
            session_result.completed_runs += 1
            
            # Write telemetry to JSONL
            if telemetry_enabled and jsonl_path and run_metrics:
                _append_run_to_jsonl(jsonl_path, run_metrics, telemetry_service)
            
            logger.info(f"Run {run_num} completed: outcome={run_result.outcome}, "
                       f"duration={run_result.duration_seconds:.1f}s, "
                       f"floor={run_result.deepest_floor}")
        
        except Exception as e:
            exception_msg = str(e)
            logger.error(f"Run {run_num} crashed: {exception_msg}", exc_info=True)
            
            # Create error result
            run_result = SoakRunResult(
                run_number=run_num,
                outcome="crash",
                exception=exception_msg,
            )
            
            session_result.bot_crashes += 1
        
        # Add run result to session
        if run_result:
            session_result.runs.append(run_result)
    
    # Compute session aggregates
    session_end = time.time()
    session_result.session_duration_seconds = session_end - session_start
    session_result.compute_aggregates()
    
    logger.info(f"Bot soak session complete: {session_result.completed_runs}/{runs} completed, "
               f"{session_result.bot_crashes} crashes")
    
    return session_result


def _append_run_to_jsonl(
    jsonl_path: Path,
    run_metrics,  # RunMetrics
    telemetry_service,  # TelemetryService
) -> None:
    """Append a single run's telemetry to JSONL file.
    
    Args:
        jsonl_path: Path to JSONL file
        run_metrics: RunMetrics instance
        telemetry_service: TelemetryService instance
    """
    try:
        # Build combined JSON object
        telemetry_stats = telemetry_service.get_stats()
        
        run_data = {
            'run_metrics': run_metrics.to_dict(),
            'telemetry': {
                'floor_count': telemetry_stats.get('floors', 0),
                'avg_etp_per_floor': telemetry_stats.get('avg_etp_per_floor', 0.0),
                'total_traps': telemetry_stats.get('total_traps', 0),
                'total_secrets': telemetry_stats.get('total_secrets', 0),
                'total_doors': telemetry_stats.get('total_doors', 0),
                'total_keys': telemetry_stats.get('total_keys', 0),
            },
            'timestamp': datetime.now().isoformat(),
        }
        
        # Append as single JSON line
        with open(jsonl_path, 'a') as f:
            f.write(json.dumps(run_data) + '\n')
        
        logger.debug(f"Appended run {run_metrics.run_id} to {jsonl_path}")
    
    except Exception as e:
        logger.error(f"Failed to append run to JSONL: {e}")

