"""Configuration package for Yarl (Catacombs of Yarl)."""

from .testing_config import get_testing_config, set_testing_mode, is_testing_mode

__all__ = ['get_testing_config', 'set_testing_mode', 'is_testing_mode']
