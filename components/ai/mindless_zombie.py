from random import randint
from typing import List, Optional, Any, Dict, TYPE_CHECKING

from game_messages import Message

# Legacy libtcod hooks retained for tests/monkeypatching.
libtcod = None
libtcodpy = None
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


class MindlessZombieAI:
    """AI for mindless zombies that attack everything.
    
    Zombies wander randomly and attack ANY adjacent entity - player,
    monsters, or other zombies. They have no faction loyalty and are
    completely mindless, making them chaotic but not reliable allies.
    
    Once locked onto a target, zombies continue attacking it relentlessly.
    If another entity gets adjacent, there's a 50% chance to switch targets.
    
    Attributes:
        owner (Entity): The entity that owns this AI component
        current_target (Entity): Current entity being attacked (sticky targeting)
    """
    
    def __init__(self):
        """Initialize a MindlessZombieAI."""
        self.owner = None
        self.current_target = None  # Track current target for sticky behavior
        self.in_combat = False  # Tracks if zombie has been attacked (for consistency)
        self.portal_usable = True  # Mindless zombies can use portals (mindless = no tactics)
    
    def take_turn(self, target, fov_map, game_map, entities):
        """Execute one turn of mindless zombie behavior.
        
        Zombies are hungry! They chase and attack any living creature in their FOV.
        Once locked onto a target, they pursue it relentlessly until it's dead
        or out of sight. If adjacent, they attack. If in FOV but not adjacent, they chase.
        
        Args:
            target (Entity): Ignored - zombies don't target specifically
            fov_map: Field of view map for detecting targets
            game_map (GameMap): The game map for movement
            entities (list): List of all entities for finding attack targets
            
        Returns:
            list: List of result dictionaries with AI actions
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Debug logging for zombie behavior
        logger.debug(f"Zombie {self.owner.name} taking turn at ({self.owner.x}, {self.owner.y}), target: {self.current_target.name if self.current_target else 'None'}")
        
        results = []
        
        # NOTE: Status effects are now processed at the AI system level (with state_manager)
        # before take_turn is called. This ensures DOT effects can finalize deaths properly.
        # Do NOT process them here again.
        
        # Check for paralysis - completely prevents all actions
        if (hasattr(self.owner, 'has_status_effect') and 
            callable(self.owner.has_status_effect) and 
            self.owner.has_status_effect('paralysis')):
            results.append({'message': MB.custom(f"{self.owner.name} is paralyzed and cannot act!", (150, 75, 200))})
            return results
        
        # Check if there's a taunted target (Yo Mama spell effect)
        # Even mindless zombies are drawn to the insult!
        taunted_target = find_taunted_target(entities)
        is_pursuing_taunt = False
        if taunted_target and taunted_target != self.owner:
            # Override current target with taunted target
            self.current_target = taunted_target
            is_pursuing_taunt = True
        
        # Zombies have limited FOV (radius 5)
        zombie_fov_radius = 5
        
        # Check if current target is still valid (alive and in FOV)
        if self.current_target:
            # Is target still alive and in FOV?
            target_in_entities = self.current_target in entities
            target_has_fighter = self.current_target.components.has(ComponentType.FIGHTER)
            
            if target_in_entities and target_has_fighter:
                # Use Euclidean distance for FOV check (sight range)
                sight_distance = self.owner.distance_to(self.current_target)
                # If pursuing taunt, always "see" the target (entire dungeon heard the insult!)
                in_fov = is_pursuing_taunt or sight_distance <= zombie_fov_radius
                
                if in_fov:
                    # Target still in FOV!
                    # Use Chebyshev distance for melee range (treats diagonal as adjacent)
                    distance = self.owner.chebyshev_distance_to(self.current_target)
                    weapon_reach = get_weapon_reach(self.owner)
                    if distance <= weapon_reach:
                        # Within attack range - ATTACK!
                        # Check for other adjacent targets first
                        adjacent_targets = self._find_adjacent_targets(entities)
                        
                        # Check if there are OTHER targets besides current one
                        other_adjacent = [e for e in adjacent_targets if e != self.current_target]
                        
                        if other_adjacent:
                            # There's at least one other adjacent target - 50% chance to switch
                            from random import random
                            if random() < 0.5:
                                from random import choice
                                old_target = self.current_target
                                self.current_target = choice(other_adjacent)
                                logger.info(f"Zombie {self.owner.name} switched target from {old_target.name} to {self.current_target.name}")
                        
                        # Attack current target (use new d20 system)
                        owner_fighter = self.owner.require_component(ComponentType.FIGHTER)
                        attack_results = owner_fighter.attack_d20(self.current_target)
                        results.extend(attack_results)
                        return results
                    else:
                        # In FOV but not adjacent - CHASE!
                        # Check if immobilized (Glue spell)
                        if (hasattr(self.owner, 'has_status_effect') and 
                            callable(self.owner.has_status_effect) and 
                            self.owner.has_status_effect('immobilized')):
                            results.append({'message': MB.custom(f"{self.owner.name} struggles against the glue!", (139, 69, 19))})
                            return results
                        
                        self.owner.move_astar(self.current_target, entities, game_map)
                        return results
                else:
                    # Target out of FOV - lose interest
                    logger.debug(f"Zombie {self.owner.name} lost sight of target")
                    self.current_target = None
            else:
                # Target dead or removed - clear it
                logger.debug(f"Zombie {self.owner.name} target is dead/invalid")
                self.current_target = None
        
        # No current target - look for any living entity in FOV
        visible_targets = self._find_visible_targets(entities, zombie_fov_radius)
        
        if visible_targets:
            # Pick closest target and lock onto it (Euclidean distance for "closest")
            closest = min(visible_targets, key=lambda e: self.owner.distance_to(e))
            self.current_target = closest
            
            # If adjacent, attack immediately (use Chebyshev for melee range)
            melee_distance = self.owner.chebyshev_distance_to(closest)
            weapon_reach = get_weapon_reach(self.owner)
            if melee_distance <= weapon_reach:
                owner_fighter = self.owner.require_component(ComponentType.FIGHTER)
                attack_results = owner_fighter.attack_d20(closest)
                results.extend(attack_results)
                return results
            else:
                # Chase it!
                # Check if immobilized (Glue spell)
                if (hasattr(self.owner, 'has_status_effect') and 
                    callable(self.owner.has_status_effect) and 
                    self.owner.has_status_effect('immobilized')):
                    results.append({'message': MB.custom(f"{self.owner.name} struggles against the glue!", (139, 69, 19))})
                    return results
                
                self.owner.move_astar(closest, entities, game_map)
                return results
        
        # No visible targets - wander randomly
        # Check if immobilized (Glue spell) - can't even wander
        if (hasattr(self.owner, 'has_status_effect') and 
            callable(self.owner.has_status_effect) and 
            self.owner.has_status_effect('immobilized')):
            results.append({'message': MB.custom(f"{self.owner.name} struggles against the glue!", (139, 69, 19))})
            return results
        
        dx = randint(-1, 1)
        dy = randint(-1, 1)
        
        # Check if destination is valid
        if dx != 0 or dy != 0:
            destination_x = self.owner.x + dx
            destination_y = self.owner.y + dy
            
            # Check bounds and blocking
            if (0 <= destination_x < game_map.width and 
                0 <= destination_y < game_map.height and
                not game_map.is_blocked(destination_x, destination_y)):
                
                # Check for entity blocking
                blocking_entity = None
                for entity in entities:
                    if entity.blocks and entity.x == destination_x and entity.y == destination_y:
                        blocking_entity = entity
                        break
                
                # Only move if not blocked by entity
                if not blocking_entity:
                    self.owner.move(dx, dy)
        
        # Process status effects at turn end (decrement durations, remove expired effects)
        status_effects = self.owner.get_component_optional(ComponentType.STATUS_EFFECTS)
        if status_effects:
            end_results = status_effects.process_turn_end()
            results.extend(end_results)
        
        return results
    
    def _find_adjacent_targets(self, entities):
        """Find all adjacent living entities that can be attacked.
        
        Args:
            entities (list): List of all entities
            
        Returns:
            list: List of adjacent entities with fighter components
        """
        adjacent = []
        
        for entity in entities:
            # Skip self
            if entity == self.owner:
                continue
            
            # Skip non-living entities (corpses, items)
            if not entity.components.has(ComponentType.FIGHTER):
                continue
            
            # Check if adjacent using Chebyshev distance (treats diagonals as adjacent)
            if self.owner.chebyshev_distance_to(entity) <= 1:
                adjacent.append(entity)
        
        return adjacent
    
    def _find_visible_targets(self, entities, fov_radius):
        """Find all living entities within FOV radius.
        
        Args:
            entities (list): List of all entities
            fov_radius (int): Vision radius for zombie
            
        Returns:
            list: List of entities within FOV with fighter components
        """
        visible = []
        
        for entity in entities:
            # Skip self
            if entity == self.owner:
                continue
            
            # Skip non-living entities (corpses, items)
            if not entity.components.has(ComponentType.FIGHTER):
                continue
            
            # Check if within FOV radius
            if self.owner.distance_to(entity) <= fov_radius:
                visible.append(entity)
        
        return visible


