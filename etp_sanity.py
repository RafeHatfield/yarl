#!/usr/bin/env python3
"""ETP Sanity Harness - Test encounter budgeting across all bands.

This script generates test levels for each band (B1-B5) and reports per-room ETP
to validate that the encounter budgeting system is working correctly.

Usage:
    python3 etp_sanity.py                    # Run sanity check, print CSV summary
    python3 etp_sanity.py --strict           # Fail if any room exceeds budget
    python3 etp_sanity.py --verbose          # Show detailed per-monster ETP
    python3 etp_sanity.py --depth 3          # Test single depth only
    python3 etp_sanity.py --runs 5           # Multiple runs per band for statistics
"""

import argparse
import sys
import os
import logging
from typing import List, Dict, Tuple, Any, Optional
from dataclasses import dataclass, field
from collections import Counter

# Force headless mode before any tcod imports
os.environ['SDL_VIDEODRIVER'] = 'dummy'

# Suppress tcod/SDL warnings for cleaner output
import warnings
warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.WARNING)  # Only show warnings+

# Now import game modules
from balance.etp import (
    get_etp_config, 
    get_band_for_depth, 
    get_band_config,
    get_room_etp_budget,
    get_monster_etp,
    BandConfig,
)
from config.testing_config import set_testing_mode
from config.level_template_registry import (
    get_level_template_registry, 
    load_level_templates,
    EncounterBudget,
    RoomMetadata,
)
from components.component_registry import ComponentType


# Room status constants
STATUS_OK = "OK"
STATUS_UNDER = "UNDER"
STATUS_OVER = "OVER"
STATUS_EMPTY = "EMPTY"
STATUS_BOSS = "BOSS"
STATUS_MINIBOSS = "MINIBOSS"
STATUS_ENDBOSS = "ENDBOSS"
STATUS_SPIKE = "SPIKE"
STATUS_EXEMPT = "EXEMPT"

# Statuses that don't count as violations
NON_VIOLATION_STATUSES = {STATUS_OK, STATUS_EMPTY, STATUS_BOSS, STATUS_MINIBOSS, 
                          STATUS_ENDBOSS, STATUS_SPIKE, STATUS_EXEMPT}


@dataclass
class RoomETPResult:
    """Result of ETP analysis for a single room."""
    room_index: int
    room_x: int
    room_y: int
    total_etp: float
    monster_counts: Dict[str, int]  # monster_type -> count
    etp_breakdown: Dict[str, float]  # monster_type -> total_etp for that type
    within_budget: bool
    budget_min: float
    budget_max: float
    status: str = STATUS_OK  # OK, UNDER, OVER, EMPTY, BOSS, MINIBOSS, SPIKE, EXEMPT
    role: str = "normal"  # Room role from metadata
    
    def is_violation(self) -> bool:
        """Check if this room counts as a budget violation (UNDER or OVER)."""
        return self.status not in NON_VIOLATION_STATUSES
    
    def is_over_violation(self) -> bool:
        """Check if this room is OVER budget (used for strict CI mode)."""
        return self.status == STATUS_OVER
    
    def should_include_in_stats(self) -> bool:
        """Check if this room should be included in per-band statistics."""
        # Don't include empty or exempt rooms in stats
        return self.status not in {STATUS_EMPTY, STATUS_EXEMPT}


@dataclass  
class LevelETPResult:
    """Result of ETP analysis for a full level."""
    depth: int
    band: str
    rooms: List[RoomETPResult]
    total_floor_etp: float
    floor_budget_min: float
    floor_budget_max: float
    within_floor_budget: bool


def analyze_room_etp(
    room_entities: List[Any], 
    depth: int, 
    room_index: int,
    room_x: int,
    room_y: int,
    budget_min: float,
    budget_max: float,
    metadata: Optional[RoomMetadata] = None,
) -> RoomETPResult:
    """Analyze ETP for all monsters in a room.
    
    Args:
        room_entities: List of monster entities in the room
        depth: Dungeon depth for band scaling
        room_index: Index of this room
        room_x: Room X coordinate
        room_y: Room Y coordinate
        budget_min: Minimum ETP budget
        budget_max: Maximum ETP budget
        metadata: Optional room metadata for role/spike handling
        
    Returns:
        RoomETPResult with analysis
    """
    monster_counts: Dict[str, int] = Counter()
    etp_breakdown: Dict[str, float] = {}
    total_etp = 0.0
    
    for entity in room_entities:
        # Get monster type from entity - use name which includes (Elite) suffix
        monster_type = getattr(entity, 'name', 'unknown')
        
        monster_counts[monster_type] += 1
        monster_etp = get_monster_etp(monster_type, depth)
        
        if monster_type not in etp_breakdown:
            etp_breakdown[monster_type] = 0.0
        etp_breakdown[monster_type] += monster_etp
        total_etp += monster_etp
    
    # Determine status based on metadata and budget
    role = "normal"
    status = STATUS_OK
    
    if metadata:
        role = metadata.role
        # Check for special status overrides
        status_override = metadata.get_etp_status_override()
        if status_override:
            status = status_override
    
    # Check for empty rooms
    if total_etp == 0 and len(monster_counts) == 0:
        status = STATUS_EMPTY
    elif status == STATUS_OK:
        # Only compute UNDER/OVER for normal rooms
        if total_etp < budget_min:
            status = STATUS_UNDER
        elif total_etp > budget_max:
            status = STATUS_OVER
    
    within_budget = status in {STATUS_OK, STATUS_EMPTY} or (
        metadata and metadata.allow_spike and total_etp <= budget_max * 1.5
    )
    
    return RoomETPResult(
        room_index=room_index,
        room_x=room_x,
        room_y=room_y,
        total_etp=total_etp,
        monster_counts=dict(monster_counts),
        etp_breakdown=etp_breakdown,
        within_budget=within_budget,
        budget_min=budget_min,
        budget_max=budget_max,
        status=status,
        role=role,
    )


def generate_test_level(depth: int) -> Tuple[Any, List[Any], List[Any]]:
    """Generate a test level at the specified depth.
    
    Args:
        depth: Dungeon level to generate
        
    Returns:
        Tuple of (game_map, entities, rooms)
    """
    from map_objects.game_map import GameMap
    from entity import Entity
    from components.fighter import Fighter
    from components.inventory import Inventory
    from components.component_registry import ComponentType
    
    # Create a minimal player entity for map generation
    player = Entity(
        0, 0, '@', (255, 255, 255), 
        'Player', blocks=True, 
        render_order='actor'
    )
    fighter = Fighter(hp=100, defense=1, power=4)
    player.components.add(ComponentType.FIGHTER, fighter)
    inventory = Inventory(26)
    player.components.add(ComponentType.INVENTORY, inventory)
    
    # Create game map
    game_map = GameMap(80, 45, dungeon_level=depth)
    
    entities = [player]
    
    # Generate map with standard parameters
    game_map.make_map(
        max_rooms=9,
        room_min_size=6,
        room_max_size=10,
        map_width=80,
        map_height=45,
        player=player,
        entities=entities,
    )
    
    return game_map, entities, game_map.rooms if hasattr(game_map, 'rooms') else []


def analyze_level_etp(depth: int, verbose: bool = False) -> LevelETPResult:
    """Generate and analyze a level for ETP compliance.
    
    Args:
        depth: Dungeon depth to analyze
        verbose: Whether to print detailed info
        
    Returns:
        LevelETPResult with full analysis
    """
    # Generate the level
    game_map, entities, _ = generate_test_level(depth)
    
    # Get band info
    band = get_band_for_depth(depth)
    band_config = get_band_config(depth)
    
    # Get level override for custom budget if exists
    template_registry = get_level_template_registry()
    level_override = template_registry.get_level_override(depth)
    
    etp_min, etp_max = get_room_etp_budget(depth)
    if level_override and level_override.encounter_budget:
        etp_min = level_override.encounter_budget.etp_min
        etp_max = level_override.encounter_budget.etp_max
    
    # Analyze each room
    rooms_results: List[RoomETPResult] = []
    
    # Get all monsters from entities (filter to actual monsters only)
    # Monsters have 'ai' attribute or are marked as blocking actors with fighter component
    monsters = []
    for e in entities:
        # Skip player
        if getattr(e, 'name', '').lower() == 'player':
            continue
        
        # Check if it's a monster (has AI or is a blocking actor with fighter)
        has_ai = hasattr(e, 'ai') and e.ai is not None
        has_fighter = (hasattr(e, 'components') and 
                      hasattr(e.components, 'has') and 
                      e.components.has(ComponentType.FIGHTER))
        is_blocking_actor = getattr(e, 'blocks', False) and getattr(e, 'render_order', None) == 'actor'
        
        if has_ai or (has_fighter and is_blocking_actor):
            monsters.append(e)
    
    # Group monsters by the room they're in
    # We need to check which room each monster position falls into
    room_entries = []
    if hasattr(game_map, 'rooms'):
        room_entries = game_map.rooms  # Now list of dicts with 'rect' and 'metadata'
    
    # Create room to monsters mapping
    room_monsters: Dict[int, List[Any]] = {i: [] for i in range(len(room_entries))}
    
    for monster in monsters:
        for i, room_entry in enumerate(room_entries):
            room = room_entry.get('rect') if isinstance(room_entry, dict) else room_entry
            if hasattr(room, 'x1') and hasattr(room, 'x2'):
                if room.x1 <= monster.x <= room.x2 and room.y1 <= monster.y <= room.y2:
                    room_monsters[i].append(monster)
                    break
    
    # Analyze each room
    total_floor_etp = 0.0
    for room_idx, room_entry in enumerate(room_entries):
        # Extract rect and metadata from room entry
        if isinstance(room_entry, dict):
            room = room_entry.get('rect')
            metadata = room_entry.get('metadata')
        else:
            room = room_entry
            metadata = None
        
        room_ents = room_monsters.get(room_idx, [])
        room_x, room_y = room.center() if hasattr(room, 'center') else (room.x1, room.y1)
        
        result = analyze_room_etp(
            room_ents, depth, room_idx,
            room_x, room_y,
            etp_min, etp_max,
            metadata=metadata
        )
        rooms_results.append(result)
        total_floor_etp += result.total_etp
    
    # Check floor budget
    floor_min = band_config.floor_etp_min
    floor_max = band_config.floor_etp_max
    within_floor_budget = floor_min <= total_floor_etp <= floor_max
    
    return LevelETPResult(
        depth=depth,
        band=band,
        rooms=rooms_results,
        total_floor_etp=total_floor_etp,
        floor_budget_min=floor_min,
        floor_budget_max=floor_max,
        within_floor_budget=within_floor_budget,
    )


def format_monster_list(monster_counts: Dict[str, int]) -> str:
    """Format monster counts as a compact string."""
    if not monster_counts:
        return ""
    return ",".join(f"{t}:{c}" for t, c in sorted(monster_counts.items()))


def print_csv_header():
    """Print CSV header row."""
    print("depth,band,room_index,etp_total,budget_min,budget_max,status,role,monsters")


def print_room_csv(depth: int, band: str, room: RoomETPResult):
    """Print a single room result as CSV."""
    monsters_str = format_monster_list(room.monster_counts)
    print(f"{depth},{band},{room.room_index},{room.total_etp:.1f},{room.budget_min},{room.budget_max},{room.status},{room.role},{monsters_str}")


def run_sanity_check(
    depths: Optional[List[int]] = None,
    strict: bool = False,
    verbose: bool = False,
    runs_per_band: int = 1,
) -> bool:
    """Run ETP sanity check across bands.
    
    Args:
        depths: Specific depths to test (None = representative per band)
        strict: Fail if any room exceeds budget
        verbose: Show detailed output
        runs_per_band: Number of test runs per band
        
    Returns:
        True if all checks pass, False otherwise
    """
    # Enable testing mode for consistent spawns
    set_testing_mode(True)
    load_level_templates()
    
    # Representative depths for each band (or use provided depths)
    if depths is None:
        # Use depths from each band: B1(1-5), B2(6-10), B3(11-15), B4(16-20), B5(21-25)
        depths = [3, 8, 13, 18, 23]
    
    all_results: List[LevelETPResult] = []
    violations: List[str] = []
    over_violations: List[str] = []  # Only OVER violations (for strict mode)
    
    # Print CSV header
    print_csv_header()
    
    # Track special room counts
    special_rooms_count = 0
    empty_rooms_count = 0
    
    for depth in depths:
        for run in range(runs_per_band):
            result = analyze_level_etp(depth, verbose)
            all_results.append(result)
            
            # Print room results
            for room in result.rooms:
                print_room_csv(depth, result.band, room)
                
                # Track special and empty rooms
                if room.status == STATUS_EMPTY:
                    empty_rooms_count += 1
                elif room.status in {STATUS_BOSS, STATUS_MINIBOSS, STATUS_ENDBOSS, 
                                     STATUS_SPIKE, STATUS_EXEMPT}:
                    special_rooms_count += 1
                
                # Track violations (only for normal rooms that are UNDER or OVER)
                if room.is_violation():
                    violation_msg = (
                        f"Depth {depth} (band {result.band}) room {room.room_index}: "
                        f"ETP {room.total_etp:.1f} {room.status} budget "
                        f"[{room.budget_min}-{room.budget_max}]"
                    )
                    violations.append(violation_msg)
                    # Track OVER violations separately for strict mode
                    if room.is_over_violation():
                        over_violations.append(violation_msg)
    
    # Print summary
    print("\n# Summary")
    total_rooms = sum(len(r.rooms) for r in all_results)
    normal_rooms = total_rooms - special_rooms_count - empty_rooms_count
    violations_count = len(violations)
    
    print(f"# Total rooms analyzed: {total_rooms}")
    print(f"#   Normal rooms: {normal_rooms}")
    print(f"#   Empty rooms: {empty_rooms_count}")
    print(f"#   Special rooms (boss/spike/exempt): {special_rooms_count}")
    print(f"# Violations: {violations_count}")
    
    if violations and (verbose or strict):
        print("\n# Violations detail:")
        for v in violations[:10]:  # Show first 10
            print(f"#   {v}")
        if len(violations) > 10:
            print(f"#   ... and {len(violations) - 10} more")
    
    # Print per-band summary
    print("\n# Per-band summary:")
    bands_seen = {}
    for result in all_results:
        if result.band not in bands_seen:
            bands_seen[result.band] = {
                'normal_rooms': 0, 
                'total_etp': 0.0, 
                'violations': 0,
                'depth': result.depth,
                'special_count': 0,
                'empty_count': 0,
            }
        # Only count normal rooms for stats
        for room in result.rooms:
            if room.should_include_in_stats():
                if room.status not in {STATUS_BOSS, STATUS_MINIBOSS, STATUS_ENDBOSS, 
                                       STATUS_SPIKE, STATUS_EXEMPT}:
                    bands_seen[result.band]['normal_rooms'] += 1
                    bands_seen[result.band]['total_etp'] += room.total_etp
                else:
                    bands_seen[result.band]['special_count'] += 1
            else:
                bands_seen[result.band]['empty_count'] += 1
            
            if room.is_violation():
                bands_seen[result.band]['violations'] += 1
    
    for band, stats in sorted(bands_seen.items()):
        band_config = get_band_config(stats['depth'])
        avg_room_etp = stats['total_etp'] / stats['normal_rooms'] if stats['normal_rooms'] else 0
        extra_info = ""
        if stats['special_count'] > 0:
            extra_info += f", special: {stats['special_count']}"
        if stats['empty_count'] > 0:
            extra_info += f", empty: {stats['empty_count']}"
        print(f"# {band}: {stats['normal_rooms']} normal rooms, "
              f"avg room ETP: {avg_room_etp:.1f} "
              f"(target: {band_config.room_etp_min}-{band_config.room_etp_max}), "
              f"violations: {stats['violations']}{extra_info}")
    
    # Strict mode check - only fail on OVER violations (UNDER is allowed)
    over_count = len(over_violations)
    if strict and over_violations:
        print(f"\n# STRICT MODE FAILURE: {over_count} OVER-budget violations detected")
        if verbose or over_count <= 10:
            print("# OVER violations:")
            for v in over_violations[:10]:
                print(f"#   {v}")
            if over_count > 10:
                print(f"#   ... and {over_count - 10} more")
        return False
    
    if strict:
        print(f"\n# STRICT MODE PASS: No OVER-budget violations (UNDER allowed)")
    
    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='ETP Sanity Harness - Test encounter budgeting across bands'
    )
    parser.add_argument(
        '--strict', action='store_true',
        help='Fail if any room exceeds budget (within tolerance)'
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true',
        help='Show detailed per-monster ETP breakdown'
    )
    parser.add_argument(
        '--depth', type=int,
        help='Test a single specific depth only'
    )
    parser.add_argument(
        '--runs', type=int, default=1,
        help='Number of test runs per band (default: 1)'
    )
    parser.add_argument(
        '--test-levels', action='store_true',
        help='Test ETP test levels 81-85 specifically'
    )
    
    args = parser.parse_args()
    
    # Determine depths to test
    depths = None
    if args.depth:
        depths = [args.depth]
    elif args.test_levels:
        depths = [81, 82, 83, 84, 85]
    
    # Run sanity check
    success = run_sanity_check(
        depths=depths,
        strict=args.strict,
        verbose=args.verbose,
        runs_per_band=args.runs,
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

