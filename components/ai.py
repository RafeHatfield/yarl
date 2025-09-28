from random import randint

import tcod as libtcod
import tcod.libtcodpy as libtcodpy

from game_messages import Message
from fov_functions import map_is_in_fov


class BasicMonster:
    """Basic AI component for hostile monsters.

    This AI makes monsters move towards and attack the player when they
    can see them. Uses A* pathfinding for intelligent movement around obstacles.

    Attributes:
        owner (Entity): The entity that owns this AI component
    """
    
    def __init__(self):
        """Initialize a BasicMonster AI."""
        self.owner = None  # Will be set by Entity when component is registered

    def take_turn(self, target, fov_map, game_map, entities):
        """Execute one turn of AI behavior.

        If the monster can see the target, it will either move towards them
        (if far away) or attack them (if adjacent).

        Args:
            target (Entity): The target entity (usually the player)
            fov_map: Field of view map for visibility checks
            game_map (GameMap): The game map for pathfinding
            entities (list): List of all entities for collision detection

        Returns:
            list: List of result dictionaries with AI actions and effects
        """
        results = []

        # print('The ' + self.owner.name + ' wonders when it will get to move.')
        monster = self.owner
        if map_is_in_fov(fov_map, monster.x, monster.y):

            if monster.distance_to(target) >= 2:
                # monster.move_towards(target.x, target.y, game_map, entities)
                monster.move_astar(target, entities, game_map)
            elif target.fighter.hp > 0:
                # print('The {0} insults you!'.format(monster.name))
                # monster.fighter.attack(target)
                attack_results = monster.fighter.attack(target)
                results.extend(attack_results)

        return results


class ConfusedMonster:
    """Temporary AI component for confused monsters.

    This AI makes monsters move randomly for a limited number of turns,
    then restores their previous AI behavior. Used by confusion spells.

    Attributes:
        previous_ai: The AI component to restore after confusion ends
        number_of_turns (int): Remaining turns of confusion
        owner (Entity): The entity that owns this AI component
    """

    def __init__(self, previous_ai, number_of_turns=10):
        """Initialize a ConfusedMonster AI.

        Args:
            previous_ai: The AI component to restore when confusion ends
            number_of_turns (int, optional): Duration of confusion. Defaults to 10.
        """
        self.previous_ai = previous_ai
        self.number_of_turns = number_of_turns
        self.owner = None  # Will be set by Entity when component is registered

    def take_turn(self, target, fov_map, game_map, entities):
        """Execute one turn of confused AI behavior.

        Makes the monster move randomly. Decrements confusion duration
        and restores previous AI when confusion ends.

        Args:
            target (Entity): The target entity (ignored during confusion)
            fov_map: Field of view map (ignored during confusion)
            game_map (GameMap): The game map for movement
            entities (list): List of all entities for collision detection

        Returns:
            list: List of result dictionaries with AI actions and messages
        """
        results = []

        if self.number_of_turns > 0:
            random_x = self.owner.x + randint(0, 2) - 1
            random_y = self.owner.y + randint(0, 2) - 1

            if random_x != self.owner.x and random_y != self.owner.y:
                self.owner.move_towards(random_x, random_y, game_map, entities)

            self.number_of_turns -= 1
        else:
            self.owner.ai = self.previous_ai
            results.append(
                {
                    "message": Message(
                        "The {0} is no longer confused!".format(self.owner.name),
                        (255, 0, 0),
                    )
                }
            )

        return results
