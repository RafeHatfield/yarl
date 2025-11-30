#!/usr/bin/env python3
"""Loot Sanity Harness - Test loot distribution across all bands.

This script generates test levels for each band (B1-B5) and reports per-room
and per-band loot statistics to validate the loot system is properly balanced.

Usage:
    python3 loot_sanity.py                    # Run sanity check with default settings
    python3 loot_sanity.py --bands            # Test one representative depth per band
    python3 loot_sanity.py --runs 10          # Run 10 iterations per band
    python3 loot_sanity.py --depth 5          # Test single depth only
    python3 loot_sanity.py --verbose          # Show detailed per-item breakdown
    python3 loot_sanity.py --category healing # Filter to specific category
"""

import argparse
import sys
import os
import logging
from typing import List, Dict, Tuple, Any, Optional
from dataclasses import dataclass, field
from collections import Counter, defaultdict

# Force headless mode before any tcod imports
os.environ['SDL_VIDEODRIVER'] = 'dummy'

# Suppress tcod/SDL warnings for cleaner output
import warnings
warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.WARNING)  # Only show warnings+

# Now import game modules
from balance.loot_tags import (
    get_loot_tags,
    get_band_for_depth,
    get_depth_for_band,
    LOOT_TAGS,
    LOOT_CATEGORIES,
    LootTags,
)
from balance.pity import (
    reset_pity_state,
    reset_pity_trigger_stats,
    get_pity_trigger_stats,
    get_healing_pity_threshold,
    get_panic_pity_threshold,
    get_weapon_pity_threshold,
    get_armor_pity_threshold,
)
from config.testing_config import set_testing_mode
from config.level_template_registry import (
    get_level_template_registry,
    load_level_templates,
)
from components.component_registry import ComponentType


@dataclass
class ItemResult:
    """Result for a single item found during analysis."""
    item_id: str
    item_name: str
    x: int
    y: int
    room_index: int
    categories: List[str]
    tags: Optional[LootTags]


@dataclass
class RoomLootResult:
    """Result of loot analysis for a single room."""
    room_index: int
    room_x: int
    room_y: int
    items: List[ItemResult]
    category_counts: Dict[str, int]
    
    @property
    def total_items(self) -> int:
        return len(self.items)
    
    @property
    def has_healing(self) -> bool:
        return self.category_counts.get("healing", 0) > 0


@dataclass
class LevelLootResult:
    """Result of loot analysis for a full level."""
    depth: int
    band: int
    rooms: List[RoomLootResult]
    all_items: List[ItemResult]
    category_totals: Dict[str, int]
    item_totals: Dict[str, int]
    
    @property
    def total_items(self) -> int:
        return len(self.all_items)
    
    @property
    def room_count(self) -> int:
        return len(self.rooms)


@dataclass
class BandSummary:
    """Aggregated statistics for a band across multiple runs."""
    band: int
    depth: int
    runs: int
    total_rooms: int
    total_items: int
    category_totals: Dict[str, int] = field(default_factory=dict)
    item_totals: Dict[str, int] = field(default_factory=dict)
    # Pity tracking
    pity_healing_triggers: int = 0
    pity_panic_triggers: int = 0
    pity_weapon_triggers: int = 0
    pity_armor_triggers: int = 0
    pity_normal_rooms: int = 0  # Rooms where pity was checked
    pity_skipped_rooms: int = 0  # Special rooms where pity was skipped
    
    @property
    def items_per_run(self) -> float:
        return self.total_items / self.runs if self.runs else 0
    
    @property
    def items_per_room(self) -> float:
        return self.total_items / self.total_rooms if self.total_rooms else 0
    
    def category_per_run(self, category: str) -> float:
        return self.category_totals.get(category, 0) / self.runs if self.runs else 0
    
    def category_per_room(self, category: str) -> float:
        return self.category_totals.get(category, 0) / self.total_rooms if self.total_rooms else 0
    
    def pity_trigger_rate(self, pity_type: str) -> float:
        """Get the pity trigger rate as a fraction of normal rooms."""
        if self.pity_normal_rooms == 0:
            return 0.0
        triggers = {
            "healing": self.pity_healing_triggers,
            "panic": self.pity_panic_triggers,
            "weapon": self.pity_weapon_triggers,
            "armor": self.pity_armor_triggers,
        }
        return triggers.get(pity_type, 0) / self.pity_normal_rooms


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


def get_item_id(entity: Any) -> Optional[str]:
    """Extract item ID from an entity.
    
    Args:
        entity: Entity to check
        
    Returns:
        Item ID string or None if not an item
    """
    # Get the entity name and normalize it
    name = getattr(entity, 'name', '')
    if not name:
        return None
    
    # Normalize to match LOOT_TAGS keys
    item_id = name.lower().replace(' ', '_')
    return item_id


def is_item_entity(entity: Any) -> bool:
    """Check if an entity is an item (not monster, player, or feature).
    
    Args:
        entity: Entity to check
        
    Returns:
        True if entity is an item
    """
    # Skip player
    if getattr(entity, 'name', '').lower() == 'player':
        return False
    
    # Skip monsters (have AI)
    has_ai = hasattr(entity, 'ai') and entity.ai is not None
    if has_ai:
        return False
    
    # Check if it has item component
    has_item = hasattr(entity, 'item') and entity.item is not None
    
    # Check if it has equippable component (weapons/armor are items)
    has_equippable = hasattr(entity, 'equippable') and entity.equippable is not None
    
    # Check if it's a wand
    has_wand = hasattr(entity, 'wand') and entity.wand is not None
    
    # Skip map features like chests, signposts, stairs
    # Note: Check for actual components, not just attribute existence (they default to None)
    has_chest = getattr(entity, 'chest', None) is not None
    has_signpost = getattr(entity, 'signpost', None) is not None
    has_stairs = getattr(entity, 'stairs', None) is not None
    
    if has_chest or has_signpost or has_stairs:
        return False
    
    # Skip portals and special entities
    has_portal = getattr(entity, 'portal', None) is not None
    is_portal = getattr(entity, 'is_portal', False)
    
    if has_portal or is_portal:
        return False
    
    return has_item or has_equippable or has_wand


def analyze_room_loot(
    room_entities: List[Any],
    depth: int,
    room_index: int,
    room_x: int,
    room_y: int,
) -> RoomLootResult:
    """Analyze loot for all items in a room.
    
    Args:
        room_entities: List of item entities in the room
        depth: Dungeon depth
        room_index: Index of this room
        room_x: Room center X coordinate
        room_y: Room center Y coordinate
        
    Returns:
        RoomLootResult with analysis
    """
    items: List[ItemResult] = []
    category_counts: Dict[str, int] = Counter()
    
    for entity in room_entities:
        item_id = get_item_id(entity)
        if not item_id:
            continue
        
        tags = get_loot_tags(item_id)
        categories = tags.categories if tags else []
        
        item_result = ItemResult(
            item_id=item_id,
            item_name=getattr(entity, 'name', item_id),
            x=entity.x,
            y=entity.y,
            room_index=room_index,
            categories=categories,
            tags=tags,
        )
        items.append(item_result)
        
        # Count categories
        for category in categories:
            category_counts[category] += 1
        
        # Count as "untagged" if no categories
        if not categories:
            category_counts["untagged"] += 1
    
    return RoomLootResult(
        room_index=room_index,
        room_x=room_x,
        room_y=room_y,
        items=items,
        category_counts=dict(category_counts),
    )


def analyze_level_loot(depth: int, verbose: bool = False) -> LevelLootResult:
    """Generate and analyze a level for loot distribution.
    
    Args:
        depth: Dungeon depth to analyze
        verbose: Whether to print detailed info
        
    Returns:
        LevelLootResult with full analysis
    """
    # Generate the level
    game_map, entities, _ = generate_test_level(depth)
    
    band = get_band_for_depth(depth)
    
    # Get all items from entities
    items = [e for e in entities if is_item_entity(e)]
    
    # Get room entries
    room_entries = []
    if hasattr(game_map, 'rooms'):
        room_entries = game_map.rooms
    
    # Create room to items mapping
    room_items: Dict[int, List[Any]] = {i: [] for i in range(len(room_entries))}
    unassigned_items: List[Any] = []
    
    for item in items:
        assigned = False
        for i, room_entry in enumerate(room_entries):
            room = room_entry.get('rect') if isinstance(room_entry, dict) else room_entry
            if hasattr(room, 'x1') and hasattr(room, 'x2'):
                if room.x1 <= item.x <= room.x2 and room.y1 <= item.y <= room.y2:
                    room_items[i].append(item)
                    assigned = True
                    break
        if not assigned:
            unassigned_items.append(item)
    
    # Analyze each room
    room_results: List[RoomLootResult] = []
    all_items: List[ItemResult] = []
    category_totals: Dict[str, int] = Counter()
    item_totals: Dict[str, int] = Counter()
    
    for room_idx, room_entry in enumerate(room_entries):
        if isinstance(room_entry, dict):
            room = room_entry.get('rect')
        else:
            room = room_entry
        
        room_ents = room_items.get(room_idx, [])
        room_x, room_y = room.center() if hasattr(room, 'center') else (room.x1, room.y1)
        
        result = analyze_room_loot(
            room_ents, depth, room_idx, room_x, room_y
        )
        room_results.append(result)
        
        # Aggregate
        all_items.extend(result.items)
        for category, count in result.category_counts.items():
            category_totals[category] += count
        for item in result.items:
            item_totals[item.item_id] += 1
    
    # Handle unassigned items (in corridors, etc.)
    for item in unassigned_items:
        item_id = get_item_id(item)
        if item_id:
            tags = get_loot_tags(item_id)
            categories = tags.categories if tags else []
            item_result = ItemResult(
                item_id=item_id,
                item_name=getattr(item, 'name', item_id),
                x=item.x,
                y=item.y,
                room_index=-1,  # Not in a room
                categories=categories,
                tags=tags,
            )
            all_items.append(item_result)
            item_totals[item_id] += 1
            for category in categories:
                category_totals[category] += 1
    
    return LevelLootResult(
        depth=depth,
        band=band,
        rooms=room_results,
        all_items=all_items,
        category_totals=dict(category_totals),
        item_totals=dict(item_totals),
    )


def print_csv_header():
    """Print CSV header row for item data."""
    print("depth,band,item_id,categories,count")


def print_item_csv(depth: int, band: int, item_id: str, categories: List[str], count: int):
    """Print a single item result as CSV."""
    cat_str = "|".join(categories) if categories else "untagged"
    print(f"{depth},{band},{item_id},{cat_str},{count}")


def run_loot_analysis(
    depths: Optional[List[int]] = None,
    runs_per_depth: int = 5,
    verbose: bool = False,
    category_filter: Optional[str] = None,
    normal_mode: bool = False,
) -> Dict[int, BandSummary]:
    """Run loot analysis across bands.
    
    Args:
        depths: Specific depths to test (None = representative per band)
        runs_per_depth: Number of test runs per depth
        verbose: Show detailed output
        category_filter: Only show items in this category
        normal_mode: If True, use normal game mode instead of testing mode
        
    Returns:
        Dictionary of band number to BandSummary
    """
    # Enable testing mode for consistent spawns (unless --normal flag)
    set_testing_mode(not normal_mode)
    load_level_templates()
    
    # Representative depths for each band (or use provided depths)
    if depths is None:
        if normal_mode:
            # Normal mode: Use center depths (no testing template overrides to worry about)
            depths = [get_depth_for_band(b) for b in range(1, 6)]  # 3, 8, 13, 18, 23
        else:
            # Testing mode: Use depths without testing template overrides
            # Testing templates exist for depths 1-8, 81-85, 91
            # So we use: B1=4 (has template), B2=9/10 (no template), B3-B5 unchanged
            # Note: B1 can't avoid templates in testing mode (all 1-8 have them)
            depths = [4, 10, 13, 18, 23]  # B1, B2, B3, B4, B5
    
    # Track results per band
    band_summaries: Dict[int, BandSummary] = {}
    
    # Print CSV header
    print_csv_header()
    
    for depth in depths:
        band = get_band_for_depth(depth)
        
        # Initialize summary for this band if needed
        if band not in band_summaries:
            band_summaries[band] = BandSummary(
                band=band,
                depth=depth,
                runs=0,
                total_rooms=0,
                total_items=0,
            )
        
        summary = band_summaries[band]
        
        for run in range(runs_per_depth):
            # Reset pity state before each run (fresh start)
            reset_pity_state()
            reset_pity_trigger_stats()
            
            result = analyze_level_loot(depth, verbose)
            
            # Capture pity stats from this run
            pity_stats = get_pity_trigger_stats()
            summary.pity_healing_triggers += pity_stats.healing_triggers
            summary.pity_panic_triggers += pity_stats.panic_triggers
            summary.pity_weapon_triggers += pity_stats.weapon_triggers
            summary.pity_armor_triggers += pity_stats.armor_triggers
            summary.pity_normal_rooms += pity_stats.normal_rooms_processed
            summary.pity_skipped_rooms += pity_stats.skipped_rooms
            
            # Update summary
            summary.runs += 1
            summary.total_rooms += result.room_count
            summary.total_items += result.total_items
            
            # Aggregate category totals
            for category, count in result.category_totals.items():
                summary.category_totals[category] = (
                    summary.category_totals.get(category, 0) + count
                )
            
            # Aggregate item totals
            for item_id, count in result.item_totals.items():
                summary.item_totals[item_id] = (
                    summary.item_totals.get(item_id, 0) + count
                )
            
            # Print per-item CSV (optional filter)
            for item_id, count in sorted(result.item_totals.items()):
                tags = get_loot_tags(item_id)
                categories = tags.categories if tags else []
                
                # Apply category filter
                if category_filter:
                    if category_filter not in categories:
                        continue
                
                print_item_csv(depth, band, item_id, categories, count)
    
    return band_summaries


def print_summary(band_summaries: Dict[int, BandSummary], category_filter: Optional[str] = None):
    """Print summary statistics for each band.
    
    Args:
        band_summaries: Dictionary of band to BandSummary
        category_filter: If set, focus on this category
    """
    print("\n# ═══════════════════════════════════════════════════════════════════════")
    print("# LOOT DISTRIBUTION SUMMARY")
    print("# ═══════════════════════════════════════════════════════════════════════")
    
    # Overall stats
    total_runs = sum(s.runs for s in band_summaries.values())
    total_rooms = sum(s.total_rooms for s in band_summaries.values())
    total_items = sum(s.total_items for s in band_summaries.values())
    
    print(f"# Total runs: {total_runs}")
    print(f"# Total rooms analyzed: {total_rooms}")
    print(f"# Total items found: {total_items}")
    print(f"# Items per room (global avg): {total_items / total_rooms:.2f}" if total_rooms else "# No rooms")
    
    # Per-band breakdown
    print("\n# ───────────────────────────────────────────────────────────────────────")
    print("# Per-Band Statistics")
    print("# ───────────────────────────────────────────────────────────────────────")
    
    for band in sorted(band_summaries.keys()):
        summary = band_summaries[band]
        print(f"\n# Band {band} (depth {summary.depth}):")
        print(f"#   Runs: {summary.runs}, Rooms: {summary.total_rooms}, Items: {summary.total_items}")
        print(f"#   Items per run: {summary.items_per_run:.1f}")
        print(f"#   Items per room: {summary.items_per_room:.2f}")
        
        # Category breakdown
        print("#   Category breakdown:")
        for category in LOOT_CATEGORIES:
            count = summary.category_totals.get(category, 0)
            per_run = summary.category_per_run(category)
            per_room = summary.category_per_room(category)
            
            # Skip if filter active and doesn't match
            if category_filter and category != category_filter:
                continue
            
            if count > 0:
                print(f"#     {category}: {count} (avg {per_run:.1f}/run, {per_room:.2f}/room)")
        
        # Check for untagged items
        untagged = summary.category_totals.get("untagged", 0)
        if untagged > 0:
            print(f"#     [untagged]: {untagged}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # Pity Summary
    # ─────────────────────────────────────────────────────────────────────────
    print("\n# ───────────────────────────────────────────────────────────────────────")
    print("# Pity System Summary")
    print("# ───────────────────────────────────────────────────────────────────────")
    print("# Pity triggers as a safety net when players go too long without critical items.")
    print("# Target: 5-15% trigger rate per category is healthy; 50%+ indicates base rates too low.")
    
    for band in sorted(band_summaries.keys()):
        summary = band_summaries[band]
        print(f"\n# Band {band} (depth {summary.depth}):")
        print(f"#   Normal rooms processed: {summary.pity_normal_rooms}")
        print(f"#   Special rooms skipped:  {summary.pity_skipped_rooms}")
        
        # Pity thresholds for this band
        h_thresh = get_healing_pity_threshold(band)
        p_thresh = get_panic_pity_threshold(band)
        w_thresh = get_weapon_pity_threshold(band)
        a_thresh = get_armor_pity_threshold(band)
        
        print(f"#   Thresholds: healing={h_thresh}, panic={p_thresh}, weapon={w_thresh}, armor={a_thresh}")
        
        if summary.pity_normal_rooms > 0:
            h_rate = summary.pity_trigger_rate("healing") * 100
            p_rate = summary.pity_trigger_rate("panic") * 100
            w_rate = summary.pity_trigger_rate("weapon") * 100
            a_rate = summary.pity_trigger_rate("armor") * 100
            
            print(f"#   Triggers:")
            print(f"#     Healing: {summary.pity_healing_triggers} ({h_rate:.1f}% of normal rooms)")
            print(f"#     Panic:   {summary.pity_panic_triggers} ({p_rate:.1f}% of normal rooms)")
            print(f"#     Weapon:  {summary.pity_weapon_triggers} ({w_rate:.1f}% of normal rooms)")
            print(f"#     Armor:   {summary.pity_armor_triggers} ({a_rate:.1f}% of normal rooms)")
        else:
            print("#   (No normal rooms - pity not evaluated)")
    
    # Highlight potential issues
    print("\n# ───────────────────────────────────────────────────────────────────────")
    print("# Potential Issues")
    print("# ───────────────────────────────────────────────────────────────────────")
    
    issues_found = False
    
    for band in sorted(band_summaries.keys()):
        summary = band_summaries[band]
        
        # Check for healing starvation (< 0.5 per run)
        healing_per_run = summary.category_per_run("healing")
        if healing_per_run < 0.5:
            print(f"# ⚠️  Band {band}: Healing starvation ({healing_per_run:.2f}/run)")
            issues_found = True
        
        # Check for healing flood (> 5 per run)
        if healing_per_run > 5:
            print(f"# ⚠️  Band {band}: Healing flood ({healing_per_run:.2f}/run)")
            issues_found = True
        
        # Check for panic item shortage (< 0.3 per run in B2+)
        if band >= 2:
            panic_per_run = summary.category_per_run("panic")
            if panic_per_run < 0.3:
                print(f"# ⚠️  Band {band}: Panic item shortage ({panic_per_run:.2f}/run)")
                issues_found = True
    
    if not issues_found:
        print("# ✓ No obvious balance issues detected")
    
    print("\n# ═══════════════════════════════════════════════════════════════════════")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Loot Sanity Harness - Test loot distribution across bands'
    )
    parser.add_argument(
        '--bands', action='store_true',
        help='Test one representative depth per band (3, 8, 13, 18, 23)'
    )
    parser.add_argument(
        '--depth', type=int,
        help='Test a single specific depth only'
    )
    parser.add_argument(
        '--runs', type=int, default=5,
        help='Number of test runs per depth (default: 5)'
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true',
        help='Show detailed per-item breakdown'
    )
    parser.add_argument(
        '--category', '-c', type=str,
        help='Filter to specific category (healing, panic, offensive, etc.)'
    )
    parser.add_argument(
        '--list-categories', action='store_true',
        help='List all available loot categories and exit'
    )
    parser.add_argument(
        '--list-items', action='store_true',
        help='List all tagged items and their categories'
    )
    parser.add_argument(
        '--normal', action='store_true',
        help='Use normal mode instead of testing mode (tests actual game balance)'
    )
    
    args = parser.parse_args()
    
    # Handle info commands
    if args.list_categories:
        print("Available loot categories:")
        for cat in LOOT_CATEGORIES:
            items = [k for k, v in LOOT_TAGS.items() if cat in v.categories]
            print(f"  {cat}: {len(items)} items")
        sys.exit(0)
    
    if args.list_items:
        print("Tagged items:")
        for item_id, tags in sorted(LOOT_TAGS.items()):
            cats = ", ".join(tags.categories) if tags.categories else "none"
            print(f"  {item_id}: [{cats}] (bands {tags.band_min}-{tags.band_max})")
        sys.exit(0)
    
    # Determine depths to test
    depths = None
    if args.depth:
        depths = [args.depth]
    elif args.bands:
        # Let run_loot_analysis choose depths based on normal_mode flag
        # (It will use cleaner depths for testing mode to avoid template overrides)
        depths = None
    
    # Validate category filter
    if args.category and args.category not in LOOT_CATEGORIES:
        print(f"Unknown category: {args.category}")
        print(f"Available: {', '.join(LOOT_CATEGORIES)}")
        sys.exit(1)
    
    # Run analysis
    band_summaries = run_loot_analysis(
        depths=depths,
        runs_per_depth=args.runs,
        verbose=args.verbose,
        category_filter=args.category,
        normal_mode=args.normal,
    )
    
    # Print summary
    print_summary(band_summaries, args.category)
    
    sys.exit(0)


if __name__ == '__main__':
    main()

