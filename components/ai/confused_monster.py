from random import randint
from typing import List, Optional, Any, Dict, TYPE_CHECKING

import tcod as libtcod
import tcod.libtcodpy as libtcodpy

from game_messages import Message
from message_builder import MessageBuilder as MB
from fov_functions import map_is_in_fov
from components.monster_action_logger import MonsterActionLogger
from components.faction import Faction, are_factions_hostile, get_target_priority
from components.component_registry import ComponentType
from logger_config import get_logger

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)


def find_taunted_target(entities: list) -> Optional['Entity']:
    """Find if there's an entity with the 'taunted' status effect.
    
    Used by the Yo Mama spell to redirect all hostiles to attack a single target.
    
    Args:
        entities (list): List of all entities in the game
        
    Returns:
        Entity or None: The taunted entity, or None if no entity is taunted
    """
    for entity in entities:
        # Check for taunt effect (optional - not all entities have status effects)
        status_effects = entity.get_component_optional(ComponentType.STATUS_EFFECTS)
        if status_effects and status_effects.has_effect('taunted'):
            # CRITICAL: Check if entity is still ALIVE (hp > 0)
            # Dead entities keep their fighter component, so we must check hp!
            fighter = entity.get_component_optional(ComponentType.FIGHTER)
            
            if fighter:
                try:
                    # Check hp (handle Mock objects in tests gracefully)
                    if fighter.hp > 0:
                        return entity
                except (TypeError, AttributeError):
                    # Mock object or invalid hp - assume alive for tests
                    return entity
            # Target is dead - return None so monsters stop pursuing
    return None


def get_weapon_reach(entity: 'Entity') -> int:
    """Get the reach of the entity's equipped weapon.
    
    Args:
        entity (Entity): The entity to check
        
    Returns:
        int: The reach of the weapon in tiles (default 1 for adjacent)
    """
    try:
        equipment = entity.get_component_optional(ComponentType.EQUIPMENT)
        if (equipment and equipment.main_hand and 
            hasattr(equipment.main_hand, 'equippable')):
            weapon = entity.equipment.main_hand.equippable
            reach = getattr(weapon, 'reach', 1)
            # Defensive: ensure reach is an int (for tests with Mocks)
            return reach if isinstance(reach, int) else 1
    except (AttributeError, TypeError):
        # Handle Mocks or incomplete test objects
        pass
    return 1  # Default reach for unarmed/no weapon


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
        self.portal_usable = False  # Confused monsters won't use portals (too chaotic)

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
            self.owner.components.add(ComponentType.AI, self.previous_ai)
            self.previous_ai.owner = self.owner
            results.append(
                {
                    "message": MB.status_effect(
                        "The {0} is no longer confused!".format(self.owner.name)
                    )
                }
            )

        return results


