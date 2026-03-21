"""Expected player gear at each depth checkpoint.

Derives what equipment a typical player should have at each depth,
based on:
  - Loot tag availability per band (balance/loot_tags.py)
  - Pity system guarantees (balance/pity.py)
  - Approximate rooms cleared per depth (~4 rooms/depth)
  - Conservative assumptions (median luck, not best case)

These expectations are used to create gear-aware probes that model
a realistic player rather than a worst-case (starting gear) player.

Band boundaries:
  B1: Depths 1-5 (Early Game)
  B2: Depths 6-10 (Early-Mid Game)
  B3: Depths 11-15 (Mid Game)
  B4: Depths 16-20 (Mid-Late Game)
  B5: Depths 21-25 (Late Game)

Pity guarantees (rooms before forced drop):
  Weapon: 8 (B1), 7 (B2), 6 (B3+)
  Armor:  8 (B1), 7 (B2), 6 (B3+)

Assumptions:
  - ~4 rooms per depth (conservative; actual may be 3-5)
  - Pity fires at threshold (worst case for pity)
  - Player equips upgrades when found
  - "Conservative" = what the player has with below-average luck
  - "Expected" = what the player has with median luck
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class GearCheckpoint:
    """Expected player equipment at a depth checkpoint."""

    depth: int
    band: int
    rooms_cleared_approx: int  # ~4 rooms/depth cumulative

    # Conservative gear (pity only, bad luck)
    conservative_weapon: str
    conservative_armor: str

    # Expected gear (median luck — at least 1 upgrade beyond pity)
    expected_weapon: str
    expected_armor: str

    # Notes on reasoning
    notes: str


# Approximately 4 rooms per depth.
# Pity weapon fires by room 8 (B1), pity armor fires by room 8 (B1).
# So by depth 2 (~8 rooms), player has at least 1 pity weapon.
# By depth 2 (~8 rooms), player has at least 1 pity armor piece.
# Most common B1 weapon drops: shortsword (weight 4.0), mace (weight 4.0).
# Most common B1 armor drops: leather_armor (5.0), shield (4.0), leather_helmet (4.0).

GEAR_CHECKPOINTS: Dict[int, GearCheckpoint] = {
    1: GearCheckpoint(
        depth=1, band=1, rooms_cleared_approx=4,
        conservative_weapon="dagger",
        conservative_armor="leather_armor",
        expected_weapon="dagger",
        expected_armor="leather_armor",
        notes="Starting gear. Too few rooms for pity to fire.",
    ),
    2: GearCheckpoint(
        depth=2, band=1, rooms_cleared_approx=8,
        conservative_weapon="dagger",
        conservative_armor="leather_armor",
        expected_weapon="shortsword",
        expected_armor="leather_armor",
        notes="Pity weapon fires at room 8. Most likely shortsword/mace.",
    ),
    3: GearCheckpoint(
        depth=3, band=1, rooms_cleared_approx=12,
        conservative_weapon="shortsword",
        conservative_armor="leather_armor",
        expected_weapon="shortsword",
        expected_armor="leather_armor",
        notes="Pity weapon guaranteed by now. Armor pity also fired but "
              "leather_armor is the most common B1 drop (no upgrade from starting).",
    ),
    4: GearCheckpoint(
        depth=4, band=1, rooms_cleared_approx=16,
        conservative_weapon="shortsword",
        conservative_armor="leather_armor",
        expected_weapon="mace",
        expected_armor="leather_armor",
        notes="Multiple pity cycles. Player likely has shortsword or mace. "
              "Shield possible but not guaranteed (competes with armor pity). "
              "Armor options at B1 are mostly leather variants.",
    ),
    5: GearCheckpoint(
        depth=5, band=1, rooms_cleared_approx=20,
        conservative_weapon="shortsword",
        conservative_armor="leather_armor",
        expected_weapon="mace",
        expected_armor="leather_armor",
        notes="End of Band 1. Player has had 2-3 weapon pity cycles. "
              "Best B1 melee: shortsword/mace. Shield likely found.",
    ),
    6: GearCheckpoint(
        depth=6, band=2, rooms_cleared_approx=24,
        conservative_weapon="shortsword",
        conservative_armor="leather_armor",
        expected_weapon="longsword",
        expected_armor="studded_leather_armor",
        notes="Band 2 starts. Longsword, rapier, spear, chain_mail, "
              "studded_leather now available. With median luck, player "
              "has found at least one B2 weapon by depth 6-7.",
    ),
}


def get_gear_checkpoint(depth: int) -> Optional[GearCheckpoint]:
    """Get the gear checkpoint for a depth. Returns None if not defined."""
    return GEAR_CHECKPOINTS.get(depth)


def get_expected_weapon(depth: int) -> str:
    """Get the expected weapon at a depth. Falls back to 'dagger'."""
    cp = GEAR_CHECKPOINTS.get(depth)
    return cp.expected_weapon if cp else "dagger"


def get_expected_armor(depth: int) -> str:
    """Get the expected armor at a depth. Falls back to 'leather_armor'."""
    cp = GEAR_CHECKPOINTS.get(depth)
    return cp.expected_armor if cp else "leather_armor"


def get_conservative_weapon(depth: int) -> str:
    """Get the conservative (bad luck) weapon at a depth."""
    cp = GEAR_CHECKPOINTS.get(depth)
    return cp.conservative_weapon if cp else "dagger"


def get_conservative_armor(depth: int) -> str:
    """Get the conservative (bad luck) armor at a depth."""
    cp = GEAR_CHECKPOINTS.get(depth)
    return cp.conservative_armor if cp else "leather_armor"
