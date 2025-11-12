# Test package for rlike roguelike game
# If you currently import `.performance` here, replace with a safe try/except.
try:
    from .performance import get_performance_config  # legacy path
except Exception:
    # Fallback to the new canonical location if the shim isn't present for any reason
    from performance.config import get_performance_config  # type: ignore
