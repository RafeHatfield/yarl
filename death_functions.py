"""Functions for handling entity death and cleanup.

This module contains functions that are called when entities die,
handling the visual and mechanical changes that occur.
"""

from game_messages import Message
from game_states import GameStates
from render_functions import RenderOrder


def kill_player(player):
    """Handle player death.

    Changes the player's appearance to a corpse and returns
    the death message and new game state.

    Args:
        player (Entity): The player entity that died

    Returns:
        tuple: (death_message, new_game_state) for game over handling
    """
    player.char = "%"
    player.color = (127, 0, 0)

    # return 'You died!', GameStates.PLAYER_DEAD
    return Message("You died!", (255, 0, 0)), GameStates.PLAYER_DEAD


def kill_monster(monster):
    """Handle monster death.

    Transforms a monster into a non-blocking corpse, removes its
    combat and AI components, and returns a death message.

    Args:
        monster (Entity): The monster entity that died

    Returns:
        Message: Death message to display to the player
    """
    # death_message = '{0} is dead!'.format(monster.name.capitalize())
    death_message = Message(
        "{0} is dead!".format(monster.name.capitalize()), (255, 127, 0)
    )

    monster.char = "%"
    monster.color = (127, 0, 0)
    monster.blocks = False
    monster.fighter = None
    monster.ai = None
    monster.name = "remains of " + monster.name
    monster.render_order = RenderOrder.CORPSE

    return death_message
