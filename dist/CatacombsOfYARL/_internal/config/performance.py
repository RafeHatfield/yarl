# config/performance.py
# Back-compat shim so existing imports keep working.
from performance.config import get_performance_config  # re-export
__all__ = ["get_performance_config"]
