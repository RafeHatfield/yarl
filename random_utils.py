"""Utility functions for random number generation and weighted choices.

This module provides helper functions for making weighted random choices
and level-based value lookups commonly used in roguelike games.
"""

from random import randint


def random_choice_index(chances):
    """Choose a random index based on weighted chances.

    Args:
        chances (list): List of weights for each choice

    Returns:
        int: Index of the chosen option
    """
    random_chance = randint(1, sum(chances))

    running_sum = 0
    choice = 0
    for w in chances:
        running_sum += w

        if random_chance <= running_sum:
            return choice
        choice += 1


def random_choice_from_dict(choice_dict):
    """Choose a random key from a dictionary based on weighted values.

    Args:
        choice_dict (dict): Dictionary with choices as keys and weights as values

    Returns:
        Any: Randomly chosen key from the dictionary
    """
    choices = list(choice_dict.keys())
    chances = list(choice_dict.values())

    return choices[random_choice_index(chances)]


def from_dungeon_level(table, dungeon_level):
    """Get a value from a level-based progression table.

    Looks up a value based on the current dungeon level from a table
    of (value, minimum_level) tuples. Returns the highest applicable value.

    Args:
        table (list): List of (value, minimum_level) tuples
        dungeon_level (int): Current dungeon level

    Returns:
        Any: Value from the table appropriate for the current level
    """
    for value, level in reversed(table):
        if dungeon_level >= level:
            return value

    return 0
