"""Debug flags for tooltip rendering diagnostics.

This module provides toggleable debug switches to help diagnose tooltip flickering
and other rendering issues. When enabled, detailed logging will be output to the
game's debug log files.

Usage:
    from ui.debug_flags import ENABLE_TOOLTIP_DEBUG, TOOLTIP_IGNORE_FOV
    
    # Enable full tooltip debugging
    ENABLE_TOOLTIP_DEBUG = True
    
    # Experiment: ignore FOV for tooltip visibility
    TOOLTIP_IGNORE_FOV = True
    
    # Experiment: disable visual effects (isolate tooltip rendering)
    TOOLTIP_DISABLE_EFFECTS = True
"""

# Master switch for all tooltip debug logging.
# When True, the tooltip pipeline logs detailed frame-by-frame diagnostics.
ENABLE_TOOLTIP_DEBUG = True

# Experiment switch: ignore FOV visibility when gathering entities for tooltips.
# When True, tooltips can appear for entities outside the player's FOV.
# This helps determine if FOV flapping is causing tooltip flicker.
TOOLTIP_IGNORE_FOV = False

# Experiment switch: disable visual effects during rendering.
# When True, visual effects (particle systems, hit flickers, etc.) are skipped.
# This helps isolate whether effect rendering is interfering with tooltip stability.
TOOLTIP_DISABLE_EFFECTS = False


