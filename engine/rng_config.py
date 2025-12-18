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
    
    # For deterministic scenario runs (balance suite):
    from engine.rng_config import stable_scenario_seed
    seed = stable_scenario_seed("depth3_orc_brutal", run_idx=5, seed_base=1337)
"""

import hashlib
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


def stable_scenario_seed(scenario_id: str, run_idx: int, seed_base: int = 1337) -> int:
    """Generate a stable, deterministic seed for a scenario run.
    
    Uses SHA-256 to produce a reproducible seed from the combination of
    scenario_id, run index, and a base seed. This ensures:
    - Same inputs always produce same seed (deterministic)
    - Different runs get different but predictable seeds
    - Seed is stable across Python versions (unlike built-in hash())
    
    Args:
        scenario_id: Unique identifier for the scenario (e.g., "depth3_orc_brutal")
        run_idx: Zero-based index of the current run within the batch
        seed_base: Base seed value (default: 1337). Change this to get
                   an entirely different sequence of runs.
    
    Returns:
        int: A stable 32-bit seed value suitable for random.seed()
    
    Example:
        >>> stable_scenario_seed("depth3_orc_brutal", 0, 1337)
        1234567890  # Always the same for these inputs
        >>> stable_scenario_seed("depth3_orc_brutal", 1, 1337)
        987654321   # Different but also stable
    """
    # Create a unique string from all inputs
    key = f"{scenario_id}:{run_idx}:{seed_base}"
    
    # Hash with SHA-256 (stable across Python versions and platforms)
    hash_bytes = hashlib.sha256(key.encode('utf-8')).digest()
    
    # Take first 4 bytes as a 32-bit unsigned int
    seed = int.from_bytes(hash_bytes[:4], byteorder='big')
    
    return seed

