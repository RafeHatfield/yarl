"""Game systems package.

This package contains larger game systems like Hall of Fame tracking,
achievement systems, and other meta-game features.
"""

from .hall_of_fame import HallOfFame, get_hall_of_fame

__all__ = [
    'HallOfFame',
    'get_hall_of_fame',
]

