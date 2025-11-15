"""Shared dataclasses for renderer frame orchestration."""

from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence, Tuple


@dataclass
class FrameContext:
    """Immutable snapshot of the data required to draw a single frame."""

    entities: Sequence[Any]
    player: Any
    game_map: Any
    fov_map: Any
    fov_recompute: bool
    message_log: Any
    screen_width: int
    screen_height: int
    bar_width: int
    panel_height: int
    panel_y: int
    mouse: Any
    colors: Dict[str, Any]
    game_state: Any
    sidebar_console: Optional[Any] = None
    camera: Optional[Any] = None
    death_screen_quote: Optional[str] = None
    use_optimization: bool = True


@dataclass
class FrameVisuals:
    """Console surfaces populated during a frame render."""

    viewport_console: Any
    status_console: Any
    sidebar_console: Optional[Any] = None
    hover_probe: Optional["HoverProbe"] = None


@dataclass
class HoverProbe:
    """Intermediate data describing what the mouse is hovering over."""

    screen_position: Optional[Tuple[int, int]]
    world_position: Optional[Tuple[int, int]]
    entities: Sequence[Any]
    visible: bool
