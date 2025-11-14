import types

from rendering.frame_models import FrameContext, HoverProbe
from render_functions import get_names_under_mouse
from ui.tooltip import TooltipAnchor, TooltipKind, resolve_hover


def _dummy_components():
    return types.SimpleNamespace(
        has=lambda *_args, **_kwargs: False,
    )


def _dummy_player():
    return types.SimpleNamespace(
        components=_dummy_components(),
        get_component_optional=lambda *_args, **_kwargs: None,
    )


def _build_frame_context(mouse_x: int, mouse_y: int, entity):
    mouse = types.SimpleNamespace(cx=mouse_x, cy=mouse_y)
    return FrameContext(
        entities=[entity],
        player=_dummy_player(),
        game_map=None,
        fov_map=None,
        fov_recompute=False,
        message_log=types.SimpleNamespace(messages=[]),
        screen_width=104,
        screen_height=52,
        bar_width=20,
        panel_height=7,
        panel_y=45,
        mouse=mouse,
        colors={},
        game_state=None,
        sidebar_console=None,
        camera=None,
        death_screen_quote=None,
        use_optimization=True,
    )


def test_get_names_under_mouse_prefers_hover_probe():
    entity = types.SimpleNamespace(name="orc")
    hover = HoverProbe(screen_position=(5, 5), world_position=(1, 1), entities=[entity], visible=True)

    result = get_names_under_mouse(None, [], None, hover_probe=hover)

    assert result == "Orc"


def test_resolve_hover_returns_single_entity_model():
    entity = types.SimpleNamespace(
        name="orc",
        components=_dummy_components(),
        get_display_name=lambda: "Orc",
    )
    hover = HoverProbe(screen_position=(30, 10), world_position=(5, 5), entities=[entity], visible=True)
    frame_ctx = _build_frame_context(30, 10, entity)

    model = resolve_hover(hover, frame_ctx)

    assert model.kind is TooltipKind.SINGLE
    assert model.anchor is TooltipAnchor.VIEWPORT
    assert model.lines and model.lines[0] == "Orc"
