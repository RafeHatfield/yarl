"""RNG configuration and seed management for deterministic runs.

This module provides a centralized way to seed all random number generators
used in the game, enabling deterministic/reproducible runs for debugging
and replay functionality.

Usage:
    from engine.rng_config import set_global_seed, get_current_seed, generate_seed
    
    # At start of a run with explicit seed:
    set_global_seed(12345)
    
    # At start of a run with random seed (logs the seed for later replay):
    seed = generate_seed()
    set_global_seed(seed)
    
    # Query current seed:
    current = get_current_seed()
"""

import logging
import random
import time
from typing import Optional

logger = logging.getLogger(__name__)

# Global state for current seed
_current_seed: Optional[int] = None


def generate_seed() -> int:
    """Generate a new random seed based on current time.
    
    Returns:
        int: A seed value derived from current time (microseconds)
    """
    # Use time-based seed with microsecond precision
    return int(time.time() * 1000000) % (2**31)


def set_global_seed(seed: int) -> None:
    """Set the global RNG seed for all random sources.
    
    This function initializes:
    - Python's built-in random module
    - Any other RNG sources used by the game (extend as needed)
    
    Args:
        seed: Integer seed value
    """
    global _current_seed
    _current_seed = seed
    
    # Seed Python's built-in random module
    random.seed(seed)
    
    # NOTE: If numpy is used elsewhere, add: numpy.random.seed(seed)
    # NOTE: If tcod's RNG is used, add appropriate seeding
    
    logger.info(f"Global RNG seed set: {seed}")


def get_current_seed() -> Optional[int]:
    """Get the current global RNG seed.
    
    Returns:
        The seed value if set_global_seed was called, None otherwise
    """
    return _current_seed


def reset_rng_state() -> None:
    """Reset the global RNG state.
    
    Clears the stored seed. Used primarily for testing.
    """
    global _current_seed
    _current_seed = None
    logger.debug("RNG state reset")

