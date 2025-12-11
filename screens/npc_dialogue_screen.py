"""NPC dialogue screen wrapper.

Delegates libtcod rendering/input to IO-layer renderer.
"""

from io_layer.npc_dialogue_renderer import show_npc_dialogue_screen

__all__ = ["show_npc_dialogue_screen"]
