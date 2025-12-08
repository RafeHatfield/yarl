"""Balance module for Effective Threat Points (ETP) encounter budgeting.

This module provides tools for:
- Calculating monster ETP values at different dungeon depths
- Budgeting encounters for rooms and floors
- Scaling monster stats by band
- Hit/miss probability calculations (Phase 8)
"""

from balance.etp import (
    get_monster_etp,
    get_band_for_depth,
    get_band_config,
    get_room_etp_budget,
    get_floor_etp_budget,
    ETP_CONFIG,
    BandConfig,
)

from balance.hit_model import (
    BASE_HIT,
    STEP,
    MIN_HIT,
    MAX_HIT,
    DEFAULT_ACCURACY,
    DEFAULT_EVASION,
    compute_hit_chance,
    roll_to_hit,
    get_accuracy,
    get_evasion,
    get_hit_chance_for_entities,
    roll_to_hit_entities,
    get_accuracy_bonus_display,
    get_evasion_bonus_display,
)

__all__ = [
    # ETP system
    "get_monster_etp",
    "get_band_for_depth",
    "get_band_config",
    "get_room_etp_budget",
    "get_floor_etp_budget",
    "ETP_CONFIG",
    "BandConfig",
    # Hit model (Phase 8)
    "BASE_HIT",
    "STEP",
    "MIN_HIT",
    "MAX_HIT",
    "DEFAULT_ACCURACY",
    "DEFAULT_EVASION",
    "compute_hit_chance",
    "roll_to_hit",
    "get_accuracy",
    "get_evasion",
    "get_hit_chance_for_entities",
    "roll_to_hit_entities",
    "get_accuracy_bonus_display",
    "get_evasion_bonus_display",
]

