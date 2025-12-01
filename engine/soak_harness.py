"""Bot soak harness for running multiple automated game sessions.

This module provides infrastructure for running multiple bot games back-to-back
for stability testing, telemetry collection, and performance analysis.

Phase 1.6: Bot Soak Harness
- Run N bot games sequentially
- Capture run_metrics and telemetry per run
- Aggregate session-level statistics
- Write per-run telemetry to JSONL format

LIBTCOD LIFECYCLE FOR BOT SOAK MODE:
------------------------------------
Bot soak mode requires a valid libtcod root console for the renderer to work.
The lifecycle is:

1. INITIALIZATION (once per session):
   - run_bot_soak() calls _initialize_libtcod_for_soak() ONCE at session start
   - This creates the root console and font setup needed for console_flush()
   
2. PER-RUN (N times):
   - Each run creates its own viewport/sidebar/status consoles with console_new()
   - play_game_with_engine() renders normally using the shared root console
   - Consoles are automatically cleaned up by libtcod when the run ends
   
3. TEARDOWN (once per session):
   - No explicit teardown needed - root console persists until process exit
   - This is safe and matches normal mode behavior

This approach ensures ConsoleRenderer.render() → console_flush() never crashes
with "Console must not be NULL or root console must exist" errors.
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import json
import tcod.libtcodpy as libtcod

logger = logging.getLogger(__name__)


@dataclass
class SoakRunResult:
    """Metrics snapshot for a single bot run.
    
    Attributes:
        run_number: Sequential run number (1-based)
        run_id: Unique run ID from RunMetrics
        seed: RNG seed used for this run (if deterministic)
        persona: Bot persona name used for this run
        outcome: Final outcome (death, victory, quit, bot_abort, max_turns, max_floors)
        failure_type: Structured failure classification:
            - "none": Run completed successfully (victory, max_floors reached)
            - "death": Player died
            - "turn_limit": Hit max_turns limit
            - "stuck": Bot detected stuck/oscillation
            - "no_stairs": Bot couldn't reach stairs
            - "error": Crash or unhandled exception
        failure_detail: Human-readable detail about the failure (e.g., monster name, position)
        duration_seconds: Run duration
        deepest_floor: Deepest floor reached
        floors_visited: Total floors visited
        monsters_killed: Total monsters defeated
        items_picked_up: Total items picked up from ground
        potions_used: Total potions consumed
        portals_used: Total portals created/used
        tiles_explored: Total tiles explored
        steps_taken: Total steps taken
        floor_count: Number of floors in telemetry
        avg_etp_per_floor: Average ETP per floor
        exception: Optional exception message if run crashed
        timestamp: ISO timestamp when run completed
    """
    run_number: int
    run_id: str = ""
    seed: Optional[int] = None
    persona: str = "balanced"
    outcome: str = "unknown"
    failure_type: str = "none"
    failure_detail: str = ""
    duration_seconds: float = 0.0
    deepest_floor: int = 1
    floors_visited: int = 1
    monsters_killed: int = 0
    items_picked_up: int = 0
    potions_used: int = 0
    portals_used: int = 0
    tiles_explored: int = 0
    steps_taken: int = 0
    floor_count: int = 0
    avg_etp_per_floor: float = 0.0
    exception: Optional[str] = None
    timestamp: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'run_number': self.run_number,
            'run_id': self.run_id,
            'seed': self.seed,
            'persona': self.persona,
            'outcome': self.outcome,
            'failure_type': self.failure_type,
            'failure_detail': self.failure_detail,
            'duration_seconds': round(self.duration_seconds, 2),
            'deepest_floor': self.deepest_floor,
            'floors_visited': self.floors_visited,
            'monsters_killed': self.monsters_killed,
            'items_picked_up': self.items_picked_up,
            'potions_used': self.potions_used,
            'portals_used': self.portals_used,
            'tiles_explored': self.tiles_explored,
            'steps_taken': self.steps_taken,
            'floor_count': self.floor_count,
            'avg_etp_per_floor': round(self.avg_etp_per_floor, 2),
            'exception': self.exception,
            'timestamp': self.timestamp,
        }
    
    @staticmethod
    def classify_failure(outcome: str, exception: Optional[str] = None, 
                         bot_abort_reason: Optional[str] = None) -> tuple:
        """Classify failure type based on outcome and context.
        
        Args:
            outcome: Run outcome string (death, victory, max_turns, bot_abort, etc.)
            exception: Optional exception message
            bot_abort_reason: Optional reason for bot_abort (from BotBrain or harness)
            
        Returns:
            Tuple of (failure_type, failure_detail)
        """
        # Success cases
        if outcome in ("victory", "max_floors"):
            return ("none", "")
        
        # Death
        if outcome == "death":
            return ("death", "")
        
        # Turn limit
        if outcome == "max_turns":
            return ("turn_limit", "Hit maximum turn limit")
        
        # Bot abort - check reason for more specific classification
        if outcome == "bot_abort":
            if bot_abort_reason:
                reason_lower = bot_abort_reason.lower()
                if "stuck" in reason_lower or "movement blocked" in reason_lower:
                    return ("stuck", bot_abort_reason)
                elif "stairs" in reason_lower:
                    return ("no_stairs", bot_abort_reason)
            # Default bot_abort without specific reason
            return ("stuck", bot_abort_reason or "Bot aborted run")
        
        # Crash/error
        if outcome in ("crash", "error") or exception:
            return ("error", exception or "Unknown error")
        
        # Unknown/other
        return ("none", "")
    
    @classmethod
    def from_run_metrics_and_telemetry(
        cls, 
        run_number: int,
        run_metrics,  # RunMetrics or None
        telemetry_stats: Dict[str, Any],
        exception: Optional[str] = None,
        persona: str = "balanced",
        bot_abort_reason: Optional[str] = None,
    ) -> "SoakRunResult":
        """Create from run metrics and telemetry.
        
        Args:
            run_number: Sequential run number
            run_metrics: RunMetrics instance or None
            telemetry_stats: Telemetry stats dict from get_stats()
            exception: Optional exception message
            persona: Bot persona name used for this run
            bot_abort_reason: Optional reason string for bot_abort outcomes
            
        Returns:
            SoakRunResult instance
        """
        timestamp = datetime.now().isoformat()
        
        if run_metrics:
            # Classify failure
            failure_type, failure_detail = cls.classify_failure(
                run_metrics.outcome, exception, bot_abort_reason
            )
            
            return cls(
                run_number=run_number,
                run_id=run_metrics.run_id,
                seed=run_metrics.seed,
                persona=persona,
                outcome=run_metrics.outcome,
                failure_type=failure_type,
                failure_detail=failure_detail,
                duration_seconds=run_metrics.duration_seconds or 0.0,
                deepest_floor=run_metrics.deepest_floor,
                floors_visited=run_metrics.floors_visited,
                monsters_killed=run_metrics.monsters_killed,
                items_picked_up=run_metrics.items_picked_up,
                potions_used=telemetry_stats.get('potions_used', 0),
                portals_used=run_metrics.portals_used,
                tiles_explored=run_metrics.tiles_explored,
                steps_taken=run_metrics.steps_taken,
                floor_count=telemetry_stats.get('floors', 0),
                avg_etp_per_floor=telemetry_stats.get('avg_etp_per_floor', 0.0),
                exception=exception,
                timestamp=timestamp,
            )
        else:
            # Fallback for missing run_metrics - classify as error
            failure_type, failure_detail = cls.classify_failure("error", exception)
            
            return cls(
                run_number=run_number,
                persona=persona,
                outcome="error",
                failure_type=failure_type,
                failure_detail=failure_detail,
                floor_count=telemetry_stats.get('floors', 0),
                avg_etp_per_floor=telemetry_stats.get('avg_etp_per_floor', 0.0),
                exception=exception,
                timestamp=timestamp,
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
        total_items_picked_up: Total items picked up across all runs
        persona: Bot persona used for this session
        session_timestamp: ISO timestamp when session started
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
    total_items_picked_up: int = 0
    persona: str = "balanced"
    session_timestamp: str = ""
    
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
        
        # Totals include all runs
        self.total_monsters_killed = sum(r.monsters_killed for r in self.runs)
        self.total_items_picked_up = sum(r.items_picked_up for r in self.runs)
    
    def print_summary(self) -> None:
        """Print human-readable session summary to stdout."""
        print("\n" + "="*60)
        print("🧪 Bot Soak Session Summary")
        print("="*60)
        print(f"   Persona: {self.persona}")
        print(f"   Runs: {self.total_runs}")
        print(f"   Completed: {self.completed_runs}")
        print(f"   Crashes: {self.bot_crashes}")
        print()
        print(f"   Session Duration: {self.session_duration_seconds:.1f}s")
        print(f"   Avg Run Duration: {self.avg_duration:.1f}s")
        print(f"   Avg Deepest Floor: {self.avg_deepest_floor:.1f}")
        print(f"   Avg Floors per Run: {self.avg_floors_per_run:.1f}")
        print(f"   Total Monsters Killed: {self.total_monsters_killed}")
        print(f"   Total Items Picked Up: {self.total_items_picked_up}")
        print("="*60)
        
        # Per-run breakdown (compact)
        if self.runs:
            print("\n📋 Per-Run Breakdown:")
            print(f"{'Run':<5} {'Outcome':<12} {'Duration':<10} {'Floor':<7} {'Kills':<7} {'Items':<7} {'Exception'}")
            print("-" * 80)
            for run in self.runs:
                duration_str = f"{run.duration_seconds:.1f}s"
                exception_str = run.exception[:25] if run.exception else ""
                print(f"{run.run_number:<5} {run.outcome:<12} {duration_str:<10} "
                      f"{run.deepest_floor:<7} {run.monsters_killed:<7} {run.items_picked_up:<7} {exception_str}")
    
    def write_csv(self, output_path: Path) -> None:
        """Write per-run metrics to CSV file.
        
        Creates a CSV file with one row per run, suitable for analysis.
        The output directory is created if it doesn't exist.
        
        Args:
            output_path: Path to the CSV file to write
        """
        import csv
        
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Define CSV columns (matches SoakRunResult.to_dict() keys)
        fieldnames = [
            'run_number', 'run_id', 'seed', 'persona', 'outcome',
            'failure_type', 'failure_detail',
            'duration_seconds', 'deepest_floor', 'floors_visited',
            'monsters_killed', 'items_picked_up', 'potions_used', 'portals_used',
            'tiles_explored', 'steps_taken', 'floor_count', 'avg_etp_per_floor',
            'exception', 'timestamp'
        ]
        
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for run in self.runs:
                writer.writerow(run.to_dict())
        
        logger.info(f"Wrote {len(self.runs)} run metrics to {output_path}")


def _initialize_libtcod_for_soak(constants: Dict[str, Any]) -> None:
    """Initialize libtcod root console for bot soak mode.
    
    This function must be called ONCE at the start of a soak session to create
    the libtcod root console. Without this, ConsoleRenderer.render() will crash
    when it calls console_flush() because no root console exists.
    
    This matches the initialization done in engine.py main() for normal mode,
    but is isolated here for soak testing.
    
    Args:
        constants: Game constants dictionary with screen dimensions and window title
    """
    from config.ui_layout import get_ui_layout
    
    ui_layout = get_ui_layout()
    
    # Set up font (required before init_root)
    libtcod.console_set_custom_font(
        "arial10x10.png", 
        libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD
    )
    
    # Initialize root console (creates the window/screen context)
    libtcod.console_init_root(
        ui_layout.screen_width,
        ui_layout.screen_height,
        constants.get("window_title", "Yarl - Bot Soak Testing"),
        False,  # Not fullscreen
    )
    
    logger.info(f"Libtcod root console initialized: {ui_layout.screen_width}x{ui_layout.screen_height}")


def run_bot_soak(
    runs: int,
    telemetry_enabled: bool,
    telemetry_output_path: Optional[str] = None,
    constants: Optional[Dict[str, Any]] = None,
    max_turns: Optional[int] = None,
    max_floors: Optional[int] = None,
    start_floor: int = 1,
    metrics_log_path: Optional[str] = None,
    base_seed: Optional[int] = None,
    replay_log_path: Optional[str] = None,
) -> SoakSessionResult:
    """Run multiple bot games back-to-back for soak testing.
    
    This function orchestrates N sequential bot runs, capturing run_metrics
    and telemetry for each run. It resets global state between runs to ensure
    each run is independent.
    
    CRITICAL: SINGLETON SERVICE RESET REQUIREMENTS
    ================================================
    Each bot run creates a fresh game (new player, map, entities, state_manager).
    However, many services are implemented as singletons that hold references to
    the state_manager or game objects. Without resetting these singletons between
    runs, run 2+ will use stale references from run 1, causing:
    - Movement validation against the wrong map (blocked tiles from old map)
    - Pickup checks against wrong inventory
    - Stale floor state from previous game
    
    Services that MUST be reset before each run:
    - RunMetricsRecorder: Tracks per-run statistics
    - TelemetryService: Tracks per-run telemetry data
    - MovementService: Holds state_manager reference for movement validation
    - PickupService: Holds state_manager reference for item pickup
    - FloorStateManager: Tracks cross-floor state (not used in soak but reset for cleanliness)
    - BotInputSource: Per-run exploration tracking (reset via reset_bot_run_state())
    
    If a new singleton service is added that holds game object references,
    add a reset call in the per-run loop below or you will see cross-run state leakage.
    
    Args:
        runs: Number of bot runs to execute
        telemetry_enabled: Whether to collect telemetry
        telemetry_output_path: Base path for telemetry JSONL output
        constants: Game constants (if None, will call get_constants())
        max_turns: Optional maximum turns per run (ends with "max_turns" outcome)
        max_floors: Optional maximum floor depth per run (ends with "max_floors" outcome)
        start_floor: Starting floor for runs (default: 1)
        metrics_log_path: Optional path for per-run JSONL metrics output
        base_seed: Optional base RNG seed. If provided, run N uses seed = base_seed + N.
                   If None, each run generates a random seed (logged in output).
        replay_log_path: Optional base path for action replay logs.
        
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
    from config.ui_layout import get_ui_layout
    
    logger.info(f"Starting bot soak session: {runs} runs, telemetry={telemetry_enabled}, "
                f"max_turns={max_turns}, max_floors={max_floors}, start_floor={start_floor}")
    
    session_start = time.time()
    session_timestamp = datetime.now().isoformat()
    
    # Get constants once (reuse across runs)
    if constants is None:
        constants = get_constants()
    
    # Extract persona from bot_config (default: balanced)
    bot_config = constants.get("bot_config", {})
    persona = bot_config.get("persona", "balanced")
    
    session_result = SoakSessionResult(
        total_runs=runs,
        persona=persona,
        session_timestamp=session_timestamp,
    )
    
    # Enable bot mode in constants
    constants.setdefault("input_config", {})
    constants["input_config"]["bot_enabled"] = True
    
    # Mark this as bot soak mode for engine_integration to disable enemy AI
    constants["bot_soak_mode"] = True
    
    # Store soak harness config in constants for per-run access
    # Note: seed is set per-run in the loop below
    constants["soak_config"] = {
        "max_turns": max_turns,
        "max_floors": max_floors,
        "start_floor": start_floor,
        "seed": None,  # Will be set per-run
    }
    
    # Prepare metrics JSONL output if requested
    metrics_jsonl_path = None
    if metrics_log_path:
        metrics_jsonl_path = Path(metrics_log_path)
        metrics_jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Metrics JSONL output: {metrics_jsonl_path}")
    
    # CRITICAL: Initialize libtcod root console ONCE for the entire session
    # Without this, ConsoleRenderer.render() will crash on console_flush()
    # because no root console exists. This matches normal mode initialization.
    _initialize_libtcod_for_soak(constants)
    
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
    
    # Import RNG config
    from engine.rng_config import set_global_seed, generate_seed
    
    # Run N bot games
    for run_num in range(1, runs + 1):
        logger.info(f"=== Starting run {run_num}/{runs} ===")
        print(f"\n🤖 Bot Run {run_num}/{runs}...")
        
        # Determine seed for this run
        if base_seed is not None:
            run_seed = base_seed + (run_num - 1)  # Deterministic: base_seed, base_seed+1, ...
        else:
            run_seed = generate_seed()  # Random seed
        
        # Set the global RNG seed for this run
        set_global_seed(run_seed)
        logger.info(f"Run {run_num} seed: {run_seed}")
        
        # Update soak_config with current run's seed for run_metrics
        constants["soak_config"]["seed"] = run_seed
        
        run_result = None
        exception_msg = None
        
        try:
            # Reset global singletons for clean run
            # CRITICAL: These must be reset before each run to prevent state leakage
            # between runs. Each run needs fresh service instances that reference
            # the NEW state_manager for that run, not the old one from previous runs.
            reset_run_metrics_recorder()
            reset_telemetry_service()
            
            # Reset movement service (holds reference to state_manager)
            # Without this, run 2+ will use run 1's stale state_manager for movement
            # validation, causing all moves to fail against the wrong map
            from services.movement_service import reset_movement_service
            reset_movement_service()
            logger.debug(f"Reset MovementService singleton for run {run_num}")
            
            # Reset pickup service (also holds state_manager reference)
            from services.pickup_service import reset_pickup_service
            reset_pickup_service()
            logger.debug(f"Reset PickupService singleton for run {run_num}")
            
            # Reset floor state manager (tracks cross-floor state, not needed in soak)
            # Each bot soak run is a fresh game starting at floor 1
            from services.floor_state_manager import reset_floor_state_manager
            reset_floor_state_manager()
            logger.debug(f"Reset FloorStateManager singleton for run {run_num}")
            
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
            
            # Phase 1.6: Reset bot input source state for this run
            # This clears any exploration tracking from previous runs
            from io_layer.bot_input import BotInputSource
            bot_input_source = BotInputSource()
            bot_input_source.reset_bot_run_state()
            logger.debug(f"Bot input source state reset for run {run_num}")
            
            # Create consoles (required for rendering)
            sidebar_console = libtcod.console_new(ui_layout.sidebar_width, ui_layout.screen_height)
            viewport_console = libtcod.console_new(ui_layout.viewport_width, ui_layout.viewport_height)
            status_console = libtcod.console_new(ui_layout.status_panel_width, ui_layout.status_panel_height)
            
            # Play the game in bot mode
            # Note: play_game_with_engine will return when the run ends (death/quit/bot_completed)
            # The return dict may contain bot_completed=True, which indicates the bot finished exploring
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
            
            # Phase 1.6: If play_game_with_engine returned bot_completed, ensure run_metrics reflects it
            # The finalize_run_metrics("bot_completed", ...) should have been called in engine_integration
            # but verify it's set correctly
            if result and result.get("bot_completed") and run_metrics:
                logger.info(f"Run {run_num}: bot_completed outcome confirmed from play_game_with_engine result")
                # run_metrics should already have outcome="bot_completed" from finalize_run_metrics call
            
            telemetry_stats = telemetry_service.get_stats() if telemetry_service else {}
            
            # Create run result
            run_result = SoakRunResult.from_run_metrics_and_telemetry(
                run_number=run_num,
                run_metrics=run_metrics,
                telemetry_stats=telemetry_stats,
                exception=None,
                persona=persona,
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
            
            # Classify the error
            failure_type, failure_detail = SoakRunResult.classify_failure(
                "crash", exception_msg
            )
            
            # Create error result
            run_result = SoakRunResult(
                run_number=run_num,
                persona=persona,
                outcome="crash",
                failure_type=failure_type,
                failure_detail=failure_detail,
                exception=exception_msg,
                timestamp=datetime.now().isoformat(),
            )
            
            session_result.bot_crashes += 1
        
        # Add run result to session
        if run_result:
            session_result.runs.append(run_result)
    
    # Compute session aggregates
    session_end = time.time()
    session_result.session_duration_seconds = session_end - session_start
    session_result.compute_aggregates()
    
    # Write CSV output if metrics log path was provided
    if metrics_log_path:
        # Create timestamped output directory
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_dir = Path(metrics_log_path).parent / f"soak_{timestamp_str}"
        csv_path = csv_dir / "metrics.csv"
        session_result.write_csv(csv_path)
        print(f"📊 CSV metrics written to: {csv_path}")
    
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

