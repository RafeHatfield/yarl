"""Balance module for Effective Threat Points (ETP) encounter budgeting.

This module provides tools for:
- Calculating monster ETP values at different dungeon depths
- Budgeting encounters for rooms and floors
- Scaling monster stats by band
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

__all__ = [
    "get_monster_etp",
    "get_band_for_depth",
    "get_band_config",
    "get_room_etp_budget",
    "get_floor_etp_budget",
    "ETP_CONFIG",
    "BandConfig",
]

