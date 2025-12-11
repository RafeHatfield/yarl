"""Wizard Mode debug menu wrapper.

Delegates rendering/input to the IO-layer renderer to keep libtcod usage
confined to renderer modules.
"""

from io_layer.wizard_menu_renderer import (
    show_wizard_menu,
    wizard_heal,
    wizard_toggle_god_mode,
    wizard_reveal_map,
    wizard_gain_xp,
    wizard_teleport_to_level,
    wizard_spawn_npc,
    wizard_spawn_monster,
    wizard_spawn_item,
    wizard_unlock_knowledge,
)

__all__ = [
    "show_wizard_menu",
    "wizard_heal",
    "wizard_toggle_god_mode",
    "wizard_reveal_map",
    "wizard_gain_xp",
    "wizard_teleport_to_level",
    "wizard_spawn_npc",
    "wizard_spawn_monster",
    "wizard_spawn_item",
    "wizard_unlock_knowledge",
]
