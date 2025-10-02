"""Dice rolling utilities for D&D-style combat.

This module provides functions for parsing and rolling dice using
standard D&D notation (e.g., "1d4", "2d6+3", "1d20").
"""

import random
import re
from typing import Tuple


def parse_dice(dice_str: str) -> Tuple[int, int, int]:
    """Parse dice notation string into components.
    
    Supports formats:
    - "1d4" -> (1, 4, 0)
    - "2d6" -> (2, 6, 0)
    - "1d8+2" -> (1, 8, 2)
    - "3d6-1" -> (3, 6, -1)
    
    Args:
        dice_str: Dice notation string (e.g., "1d4", "2d6+3")
        
    Returns:
        tuple: (num_dice, die_size, modifier)
            - num_dice: Number of dice to roll
            - die_size: Size of each die (4, 6, 8, 10, 12, 20, etc.)
            - modifier: Fixed bonus/penalty to add
            
    Raises:
        ValueError: If dice notation is invalid
    """
    # Remove whitespace
    dice_str = dice_str.strip().lower()
    
    # Pattern: NdS+M or NdS-M or NdS
    # N = number of dice (optional, defaults to 1)
    # S = die size (required)
    # M = modifier (optional)
    pattern = r'^(\d*)d(\d+)([+-]\d+)?$'
    match = re.match(pattern, dice_str)
    
    if not match:
        raise ValueError(f"Invalid dice notation: '{dice_str}'. Expected format like '1d4', '2d6+3', etc.")
    
    num_dice_str, die_size_str, modifier_str = match.groups()
    
    # Parse components
    num_dice = int(num_dice_str) if num_dice_str else 1
    die_size = int(die_size_str)
    modifier = int(modifier_str) if modifier_str else 0
    
    # Validate
    if num_dice < 1:
        raise ValueError(f"Number of dice must be >= 1, got {num_dice}")
    if die_size < 2:
        raise ValueError(f"Die size must be >= 2, got {die_size}")
    
    return (num_dice, die_size, modifier)


def roll_dice(dice_str: str) -> int:
    """Roll dice using D&D notation and return the total.
    
    Examples:
        roll_dice("1d4") -> random value 1-4
        roll_dice("2d6") -> sum of 2d6 (2-12)
        roll_dice("1d8+2") -> 1d8 plus 2 (3-10)
    
    Args:
        dice_str: Dice notation string (e.g., "1d4", "2d6+3")
        
    Returns:
        int: Total rolled value
        
    Raises:
        ValueError: If dice notation is invalid
    """
    num_dice, die_size, modifier = parse_dice(dice_str)
    
    # Roll each die and sum
    total = sum(random.randint(1, die_size) for _ in range(num_dice))
    
    return total + modifier


def get_dice_average(dice_str: str) -> float:
    """Calculate the average roll for given dice notation.
    
    Average of a single die: (1 + die_size) / 2
    Example: 1d6 average = (1+6)/2 = 3.5
    
    Args:
        dice_str: Dice notation string (e.g., "1d4", "2d6+3")
        
    Returns:
        float: Average roll value
    """
    num_dice, die_size, modifier = parse_dice(dice_str)
    
    # Average of one die: (1 + die_size) / 2
    die_average = (1 + die_size) / 2.0
    
    return (num_dice * die_average) + modifier


def get_dice_min_max(dice_str: str) -> Tuple[int, int]:
    """Get the minimum and maximum possible rolls for dice notation.
    
    Args:
        dice_str: Dice notation string (e.g., "1d4", "2d6+3")
        
    Returns:
        tuple: (min_roll, max_roll)
    """
    num_dice, die_size, modifier = parse_dice(dice_str)
    
    min_roll = num_dice + modifier  # All 1s
    max_roll = (num_dice * die_size) + modifier  # All max
    
    return (min_roll, max_roll)


def dice_to_range_string(dice_str: str) -> str:
    """Convert dice notation to a range string for display.
    
    Examples:
        "1d4" -> "1-4"
        "2d6" -> "2-12"
        "1d8+2" -> "3-10"
    
    Args:
        dice_str: Dice notation string
        
    Returns:
        str: Range string (e.g., "1-4", "3-10")
    """
    min_val, max_val = get_dice_min_max(dice_str)
    
    if min_val == max_val:
        return str(min_val)
    return f"{min_val}-{max_val}"

