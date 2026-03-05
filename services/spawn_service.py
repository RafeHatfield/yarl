"""
Spawn/placement policy helpers for map generation.

This module centralizes spawn decision logic (what to spawn) while keeping
placement, ETP tracking, and pity systems in mapgen. It is renderer-agnostic
and does not mutate map state.
"""

from dataclasses import dataclass
from random import randint
from typing import Dict, List

from balance.etp import get_monster_etp
from balance.loot_tags import (
    get_band_density_multiplier,
    get_healing_multiplier,
    get_loot_tags,
    get_rare_multiplier,
)
from random_utils import from_dungeon_level, random_choice_from_dict


@dataclass
class EncounterBudget:
    etp_min: float
    etp_max: float
    allow_spike: bool


@dataclass
class SpawnContext:
    depth: int
    band_id: str
    band_num: int
    max_monsters: int
    max_items: int
    encounter_budget: EncounterBudget
    testing_mode: bool
    no_monsters: bool
    item_spawn_config: Dict


@dataclass
class RoomSpawnPlan:
    num_monsters: int
    num_items: int
    monster_chances: Dict[str, int]
    item_chances: Dict[str, int]


class SpawnService:
    """Encapsulates spawn decision logic for map generation."""

    def __init__(self, depth: int) -> None:
        self.depth = depth

    def scale_max_items_per_room(self, max_items: int, band_num: int) -> int:
        """Apply band density scaling to item cap."""
        density_multiplier = get_band_density_multiplier(band_num)
        return max(1, int(max_items * density_multiplier))

    def _build_monster_chances(self, testing_mode: bool, band_id: str) -> Dict[str, int]:
        """Construct monster spawn chance table for the given depth."""
        monster_chances: Dict[str, int] = {
            "orc": 80,
            "troll": from_dungeon_level(
                [[15, 3], [30, 5], [60, 7]], self.depth
            ),
        }

        # B1 spawn constraints: make trolls rarer early
        if band_id == "B1":
            monster_chances["troll"] = from_dungeon_level(
                [[5, 3], [10, 4], [15, 5]], self.depth
            )

        if testing_mode:
            monster_chances["slime"] = 40
            monster_chances["large_slime"] = from_dungeon_level(
                [[10, 1], [20, 3]], self.depth
            )
        else:
            monster_chances["slime"] = from_dungeon_level(
                [[20, 2], [40, 4], [60, 6]], self.depth
            )
            monster_chances["large_slime"] = from_dungeon_level(
                [[5, 3], [15, 5], [25, 7]], self.depth
            )

        monster_chances["zombie"] = from_dungeon_level(
            [[20, 10], [40, 13], [60, 16]], self.depth
        )
        monster_chances["plague_zombie"] = from_dungeon_level(
            [[10, 13], [20, 16], [35, 19]], self.depth
        )
        monster_chances["wraith"] = from_dungeon_level(
            [[5, 15], [15, 18], [25, 21]], self.depth
        )
        monster_chances["giant_spider"] = from_dungeon_level(
            [[15, 8], [30, 11], [45, 14]], self.depth
        )
        monster_chances["cultist_blademaster"] = from_dungeon_level(
            [[10, 12], [20, 15], [35, 18]], self.depth
        )

        # Filter out zero/negative chances
        return {k: v for k, v in monster_chances.items() if v > 0}

    def _build_item_chances(self, item_spawn_config: Dict, band_num: int) -> Dict[str, int]:
        """Construct item spawn chance table for the given depth and band."""
        item_chances: Dict[str, int] = {}
        healing_mult = get_healing_multiplier(band_num)
        rare_mult = get_rare_multiplier(band_num)

        for item_name, chance_config in item_spawn_config.items():
            if isinstance(chance_config, int):
                base_chance = chance_config
            else:
                base_chance = from_dungeon_level(chance_config, self.depth)

            item_tags = get_loot_tags(item_name)
            if item_tags:
                if item_tags.has_category("healing"):
                    base_chance = int(base_chance * healing_mult)
                if item_tags.has_category("rare"):
                    base_chance = int(base_chance * rare_mult)

            if base_chance > 0:
                item_chances[item_name] = base_chance

        return item_chances

    def generate_room_plan(
        self,
        context: SpawnContext,
        randint_fn=randint,
        choice_fn=random_choice_from_dict,
    ) -> RoomSpawnPlan:
        """Generate spawn counts and chance tables for a single room.

        Args:
            context: Spawn parameters for this room.
            randint_fn: Optional randint override (useful for tests mocking RNG).
            choice_fn: Optional weighted choice override.
        """
        monster_chances = self._build_monster_chances(context.testing_mode, context.band_id)
        item_chances = self._build_item_chances(context.item_spawn_config, context.band_num)

        num_monsters = 0 if context.no_monsters else randint_fn(0, context.max_monsters)
        num_items = randint_fn(0, context.max_items)

        return RoomSpawnPlan(
            num_monsters=num_monsters,
            num_items=num_items,
            monster_chances=monster_chances,
            item_chances=item_chances,
        )

    def pick_monster(self, monster_chances: Dict[str, int], choice_fn=random_choice_from_dict) -> str | None:
        """Select a monster type from the chance table."""
        if not monster_chances:
            return None
        base_choice = choice_fn(monster_chances)
        
        # Phase 22.3.2: Resolve orc variants (skirmisher, brute, shaman)
        # 
        # IMPORTANT: Variant resolution ONLY applies to the generic "orc" ID.
        # 
        # Why generic "orc" resolves to variants:
        #   - Worldgen uses "orc" as a faction placeholder that expands into
        #     depth-appropriate composition (normal orcs, brutes, shamans, skirmishers)
        #   - This creates encounter variety without hardcoding specific orc types
        # 
        # Why explicit IDs bypass this logic:
        #   - Scenarios need deterministic spawns (e.g., "orc_skirmisher" must spawn exactly 1 skirmisher)
        #   - Tests rely on exact monster types for validation
        #   - Future faction variants (troll_berserker, zombie_plague, etc.) need the same pattern
        #   - Explicit IDs (orc_grunt, orc_brute, orc_shaman, orc_skirmisher) preserve user intent
        # 
        # Rule: If ID is exactly "orc" → resolve to variant mix. Otherwise → spawn exact ID.
        if base_choice == "orc":
            return self._resolve_orc_variant()
        
        return base_choice

    def pick_item(self, item_chances: Dict[str, int], choice_fn=random_choice_from_dict) -> str | None:
        """Select an item type from the chance table."""
        if not item_chances:
            return None
        return choice_fn(item_chances)
    
    def _resolve_orc_variant(self) -> str:
        """Resolve orc encounter composition with variant inclusion.
        
        Phase 22.3.2: Skirmisher integration into orc encounters.
        
        Design:
        - At depth 3: ~5-10% of orcs become skirmishers
        - At depth 4-5: ~10-15% become skirmishers
        - At depth 6+: ~15-20% become skirmishers
        - Very rare at depth 6+: ~2-5% chance of returning "orc_skirmisher" twice (handled by caller)
        
        Brutes and shamans also occasionally appear in mid-to-late depths.
        
        Returns:
            Resolved monster type: "orc", "orc_brute", "orc_shaman", or "orc_skirmisher"
        """
        from random import random
        
        depth = self.depth
        
        # No skirmishers below depth 3
        if depth < 3:
            # Can still have brutes/shamans at depth 1-2 (rare)
            if depth >= 2:
                roll = random()
                if roll < 0.05:  # 5% brute
                    return "orc_brute"
                elif roll < 0.08:  # 3% shaman
                    return "orc_shaman"
            return "orc"
        
        # Depth 3: 5-10% skirmisher
        if depth == 3:
            roll = random()
            if roll < 0.075:  # 7.5% skirmisher (midpoint of 5-10%)
                return "orc_skirmisher"
            elif roll < 0.15:  # 7.5% brute
                return "orc_brute"
            elif roll < 0.22:  # 7% shaman
                return "orc_shaman"
            return "orc"
        
        # Depth 4-5: 10-15% skirmisher
        if depth in [4, 5]:
            roll = random()
            if roll < 0.125:  # 12.5% skirmisher (midpoint of 10-15%)
                return "orc_skirmisher"
            elif roll < 0.225:  # 10% brute
                return "orc_brute"
            elif roll < 0.325:  # 10% shaman
                return "orc_shaman"
            return "orc"
        
        # Depth 6+: 15-20% skirmisher, with rare chance of "premium" encounters
        roll = random()
        if roll < 0.175:  # 17.5% skirmisher (midpoint of 15-20%)
            return "orc_skirmisher"
        elif roll < 0.275:  # 10% brute
            return "orc_brute"
        elif roll < 0.375:  # 10% shaman
            return "orc_shaman"
        return "orc"