"""Performance configuration module for Yarl.

Provides configuration for frame rate limiting, logging behavior, and debug overlay.
Supports layered precedence: defaults → environment variables → YAML constants.
"""

import os
import logging
from typing import Any, Dict, Optional

_DEFAULTS = {
    "frame_rate_limit": 60,
    "logging_enabled": True,
    "debug_overlay": False,
}


def _parse_bool(val: Any) -> Optional[bool]:
    """Parse a boolean value from various input types.

    Args:
        val: Value to parse (bool, str, or other)

    Returns:
        bool if successfully parsed, None otherwise
    """
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        v = val.strip().lower()
        if v in {"1", "true", "yes", "on"}:
            return True
        if v in {"0", "false", "no", "off"}:
            return False
    return None


def get_performance_config(constants: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get the effective performance configuration.

    Merges configuration from multiple sources in order of precedence:
    1. Hardcoded defaults
    2. Environment variables (YARL_* prefix)
    3. constants["performance"] dict (highest precedence)

    Args:
        constants: Optional dict containing game configuration, including a
                  "performance" key with override values

    Returns:
        Dict with keys: frame_rate_limit (int), logging_enabled (bool), debug_overlay (bool)

    Example:
        >>> cfg = get_performance_config({"performance": {"frame_rate_limit": 75}})
        >>> cfg["frame_rate_limit"]
        75
    """
    cfg = dict(_DEFAULTS)

    # Layer 1: Environment variables (optional convenience)
    env_fps = os.getenv("YARL_FRAME_RATE_LIMIT")
    if env_fps:
        try:
            cfg["frame_rate_limit"] = int(env_fps)
        except ValueError:
            logging.warning(
                "Invalid YARL_FRAME_RATE_LIMIT=%r; using default %s",
                env_fps,
                _DEFAULTS["frame_rate_limit"],
            )

    env_log = os.getenv("YARL_LOGGING_ENABLED")
    b = _parse_bool(env_log) if env_log is not None else None
    if b is not None:
        cfg["logging_enabled"] = b

    env_dbg = os.getenv("YARL_DEBUG_OVERLAY")
    b = _parse_bool(env_dbg) if env_dbg is not None else None
    if b is not None:
        cfg["debug_overlay"] = b

    # Layer 2: constants["performance"] dict (highest precedence)
    perf = (constants or {}).get("performance", {})

    if isinstance(perf, dict):
        # frame_rate_limit
        if "frame_rate_limit" in perf:
            try:
                cfg["frame_rate_limit"] = int(perf["frame_rate_limit"])
            except (TypeError, ValueError):
                logging.warning(
                    "performance.frame_rate_limit is invalid; keeping %s",
                    cfg["frame_rate_limit"],
                )

        # logging_enabled
        if "logging_enabled" in perf:
            b = _parse_bool(perf["logging_enabled"])
            if b is not None:
                cfg["logging_enabled"] = b
            else:
                logging.warning(
                    "performance.logging_enabled is invalid; keeping %s",
                    cfg["logging_enabled"],
                )

        # debug_overlay
        if "debug_overlay" in perf:
            b = _parse_bool(perf["debug_overlay"])
            if b is not None:
                cfg["debug_overlay"] = b
            else:
                logging.warning(
                    "performance.debug_overlay is invalid; keeping %s",
                    cfg["debug_overlay"],
                )
    elif perf:  # perf is truthy but not a dict
        logging.warning(
            "constants['performance'] is not a dict (got %s); using effective cfg as-is",
            type(perf).__name__,
        )

    return cfg

