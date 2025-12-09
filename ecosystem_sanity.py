#!/usr/bin/env python3
"""Ecosystem Sanity - Scenario Simulation Harness CLI.

Phase 12B: Scenario Harness & Basic Metrics

This script provides a CLI interface for running scenario simulations:
- List available scenarios
- Run scenarios with configurable parameters
- Collect and display basic metrics

Usage:
    python3 ecosystem_sanity.py --list                     # List scenarios
    python3 ecosystem_sanity.py --scenario backstab_training  # Run scenario
    python3 ecosystem_sanity.py --scenario backstab_training --runs 20
    python3 ecosystem_sanity.py --scenario plague_arena --turn-limit 500 --player-bot observe_only

Examples:
    # List all available scenarios
    python3 ecosystem_sanity.py --list
    
    # Run backstab scenario 10 times (default)
    python3 ecosystem_sanity.py --scenario backstab_training
    
    # Run plague arena 20 times with custom turn limit
    python3 ecosystem_sanity.py --scenario plague_arena --runs 20 --turn-limit 300
"""

import argparse
import os
import sys
import logging
import warnings

# Force headless mode before any tcod imports
os.environ['SDL_VIDEODRIVER'] = 'dummy'

# Suppress tcod/SDL warnings for cleaner output
warnings.filterwarnings('ignore')

# Configure logging based on verbosity
logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def setup_logging(verbose: bool) -> None:
    """Configure logging based on verbosity flag.
    
    Args:
        verbose: If True, enable INFO level logging
    """
    if verbose:
        logging.getLogger().setLevel(logging.INFO)
        logging.getLogger('services.scenario_harness').setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARNING)


def list_scenarios() -> None:
    """Print a formatted table of available scenarios."""
    from config.level_template_registry import get_scenario_registry
    
    registry = get_scenario_registry()
    scenario_ids = registry.list_scenarios()
    
    if not scenario_ids:
        print("No scenarios found.")
        print("\nScenarios should be placed in config/levels/ with names like scenario_*.yaml")
        return
    
    # Print header
    print("\n" + "=" * 80)
    print("Available Scenarios")
    print("=" * 80)
    print(f"{'ID':<25} {'Name':<25} {'Description':<30}")
    print("-" * 80)
    
    # Print each scenario
    for scenario_id in scenario_ids:
        scenario = registry.get_scenario_definition(scenario_id)
        if scenario:
            name = scenario.name[:24] if len(scenario.name) > 24 else scenario.name
            desc = scenario.description or ""
            desc = desc[:29] if len(desc) > 29 else desc
            print(f"{scenario_id:<25} {name:<25} {desc:<30}")
    
    print("-" * 80)
    print(f"Total: {len(scenario_ids)} scenario(s)")
    print()


def run_scenario(
    scenario_id: str,
    runs: int,
    turn_limit: int,
    player_bot: str,
    verbose: bool,
) -> int:
    """Run a scenario and display results.
    
    Args:
        scenario_id: Scenario identifier
        runs: Number of runs to execute
        turn_limit: Maximum turns per run
        player_bot: Bot policy name
        verbose: Enable verbose output
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    from config.level_template_registry import get_scenario_registry
    from services.scenario_harness import run_scenario_many, make_bot_policy
    
    # Look up scenario
    registry = get_scenario_registry()
    scenario = registry.get_scenario_definition(scenario_id)
    
    if scenario is None:
        print(f"Error: Scenario '{scenario_id}' not found.")
        print("\nAvailable scenarios:")
        for sid in registry.list_scenarios():
            print(f"  - {sid}")
        return 1
    
    # Create bot policy
    try:
        policy = make_bot_policy(player_bot)
    except ValueError as e:
        print(f"Error: {e}")
        print("\nAvailable bot policies:")
        print("  - observe_only")
        return 1
    
    # Print run info
    print("\n" + "=" * 60)
    print(f"Scenario: {scenario.name}")
    print(f"ID: {scenario_id}")
    print(f"Description: {scenario.description or 'N/A'}")
    print("-" * 60)
    print(f"Runs: {runs}")
    print(f"Turn Limit: {turn_limit}")
    print(f"Bot Policy: {player_bot}")
    print("=" * 60)
    print()
    
    # Run the scenario
    print("Running scenarios...")
    if verbose:
        print()
    
    try:
        metrics = run_scenario_many(scenario, policy, runs, turn_limit)
    except Exception as e:
        print(f"Error during scenario execution: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    # Print results
    print("\n" + "=" * 60)
    print("Results")
    print("=" * 60)
    print(f"Runs: {metrics.runs}")
    print(f"Average Turns: {metrics.average_turns:.1f}")
    print(f"Player Deaths: {metrics.player_deaths}")
    
    if metrics.total_kills_by_faction:
        print("\nKills by Faction:")
        for faction, count in sorted(metrics.total_kills_by_faction.items()):
            print(f"  {faction}: {count}")
    else:
        print("\nKills by Faction: (none recorded)")
    
    print("=" * 60)
    print()
    
    return 0


def main() -> int:
    """Main entry point.
    
    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(
        description='Ecosystem Sanity - Scenario Simulation Harness',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --list                              List all scenarios
  %(prog)s --scenario backstab_training        Run backstab scenario
  %(prog)s --scenario plague_arena --runs 20   Run 20 iterations
  %(prog)s --scenario backstab_training -v     Verbose output
        """
    )
    
    # Mode selection
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        '--list',
        action='store_true',
        help='List available scenarios'
    )
    mode_group.add_argument(
        '--scenario',
        type=str,
        metavar='ID',
        help='Run a specific scenario by ID'
    )
    
    # Run configuration
    parser.add_argument(
        '--runs', '-n',
        type=int,
        default=None,
        help='Number of runs (default: from scenario defaults, or 10)'
    )
    parser.add_argument(
        '--turn-limit', '-t',
        type=int,
        default=None,
        help='Maximum turns per run (default: from scenario defaults, or 200)'
    )
    parser.add_argument(
        '--player-bot', '-b',
        type=str,
        default=None,
        help='Bot policy for player control (default: from scenario defaults, or observe_only)'
    )
    
    # Output options
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Handle --list mode
    if args.list:
        list_scenarios()
        return 0
    
    # Handle --scenario mode
    if args.scenario:
        # Get scenario defaults
        from config.level_template_registry import get_scenario_registry
        
        registry = get_scenario_registry()
        scenario = registry.get_scenario_definition(args.scenario)
        
        # Determine run parameters from: CLI > scenario defaults > hardcoded defaults
        if scenario:
            default_runs = scenario.get_default('runs', 10)
            default_turn_limit = scenario.get_default('turn_limit', 200)
            default_player_bot = scenario.get_default('player_bot', 'observe_only')
        else:
            default_runs = 10
            default_turn_limit = 200
            default_player_bot = 'observe_only'
        
        runs = args.runs if args.runs is not None else default_runs
        turn_limit = args.turn_limit if args.turn_limit is not None else default_turn_limit
        player_bot = args.player_bot if args.player_bot is not None else default_player_bot
        
        return run_scenario(
            scenario_id=args.scenario,
            runs=runs,
            turn_limit=turn_limit,
            player_bot=player_bot,
            verbose=args.verbose,
        )
    
    # Should not reach here due to mutually exclusive group
    parser.print_help()
    return 1


if __name__ == '__main__':
    sys.exit(main())
