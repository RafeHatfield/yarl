"""Configuration package for Yarl (Catacombs of Yarl)."""

from .testing_config import get_testing_config, set_testing_mode, is_testing_mode
from .performance import get_performance_config

__all__ = ['get_testing_config', 'set_testing_mode', 'is_testing_mode', 'get_performance_config']
