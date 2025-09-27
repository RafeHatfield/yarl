import tcod as libtcod

from game_messages import Message
from game_states import GameStates
from render_functions import RenderOrder


def kill_player(player):
    player.char = '%'
    player.color = (127, 0, 0)

    # return 'You died!', GameStates.PLAYER_DEAD
    return Message('You died!', (255, 0, 0)), GameStates.PLAYER_DEAD


def kill_monster(monster):
    # death_message = '{0} is dead!'.format(monster.name.capitalize())
    death_message = Message('{0} is dead!'.format(monster.name.capitalize()), (255, 127, 0))
    
    monster.char = '%'
    monster.color = (127, 0, 0)
    monster.blocks = False
    monster.fighter = None
    monster.ai = None
    monster.name = 'remains of ' + monster.name
    monster.render_order = RenderOrder.CORPSE

    return death_message