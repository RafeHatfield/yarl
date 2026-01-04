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


class SlimeAI:
    """AI component for slimes that can attack multiple factions.
    
    Slimes are hostile to all other entities (HOSTILE_ALL faction) and will
    prioritize the player over other monsters, but will attack any visible
    hostile target. This enables monster-vs-monster combat scenarios.
    
    Attributes:
        owner (Entity): The entity that owns this AI component
    """
    
    def __init__(self):
        """Initialize a SlimeAI."""
        self.owner = None  # Will be set by Entity when component is registered
        self.in_combat = False  # Tracks if slime has been attacked (for consistency)
        self.portal_usable = True  # Slimes can use portals (they're somewhat tactical)
    
    def take_turn(self, target, fov_map, game_map, entities):
        """Execute one turn of slime AI behavior.
        
        Slimes will target the closest hostile entity, prioritizing the player
        if they are within the same distance as other targets.
        
        Args:
            target (Entity): The primary target entity (usually the player)
            fov_map: Field of view map for visibility checks
            game_map (GameMap): The game map for pathfinding
            entities (list): List of all entities for collision detection
            
        Returns:
            list: List of result dictionaries with AI actions and effects
        """
        results = []
        monster = self.owner
        
        # NOTE: Status effects are now processed at the AI system level (with state_manager)
        # before take_turn is called. This ensures DOT effects can finalize deaths properly.
        # Do NOT process them here again.
        
        # Check for paralysis - completely prevents all actions
        if (hasattr(monster, 'has_status_effect') and 
            callable(monster.has_status_effect) and 
            monster.has_status_effect('paralysis')):
            results.append({'message': MB.custom(f"{monster.name} is paralyzed and cannot act!", (150, 75, 200))})
            return results
        
        # Check if there's a taunted target (Yo Mama spell effect)
        taunted_target = find_taunted_target(entities)
        is_pursuing_taunt = False
        
        if taunted_target and taunted_target != self.owner:
            # Override normal targeting - slimes are drawn to the insult!
            best_target = taunted_target
            is_pursuing_taunt = True
        else:
            # Only act when pursuing taunt or in player's FOV
            # This prevents off-screen monster-vs-monster chaos
            if not map_is_in_fov(fov_map, monster.x, monster.y):
                return results
            
            # Find the best target based on faction relationships and distance
            best_target = self._find_best_target(entities, fov_map)
        
        if best_target:
            # Calculate distance to target using Chebyshev for melee range
            distance = monster.chebyshev_distance_to(best_target)
            weapon_reach = get_weapon_reach(monster)
            
            if distance > weapon_reach:
                # Too far to attack - move towards target using A* pathfinding
                # Check if immobilized (Glue spell)
                if (hasattr(monster, 'has_status_effect') and 
                    callable(monster.has_status_effect) and 
                    monster.has_status_effect('immobilized')):
                    results.append({'message': MB.custom(f"{monster.name} struggles against the glue!", (139, 69, 19))})
                    return results
                
                monster.move_astar(best_target, entities, game_map)
                MonsterActionLogger.log_action_attempt(
                    monster, "move", f"moving towards {best_target.name}"
                )
            elif best_target.fighter:
                # Within attack range - attack the target (use new d20 system)
                attack_results = monster.fighter.attack_d20(best_target)
                results.extend(attack_results)
                MonsterActionLogger.log_action_attempt(
                    monster, "attack", f"attacking {best_target.name}"
                )
        
        # Process status effects at turn end (decrement durations, remove expired effects)
        status_effects = monster.get_component_optional(ComponentType.STATUS_EFFECTS)
        if status_effects:
            end_results = status_effects.process_turn_end()
            results.extend(end_results)
        
        return results
    
    def _find_best_target(self, entities, fov_map) -> Optional[Any]:
        """Find the best target based on faction relationships and proximity.
        
        Args:
            entities: List of all entities to consider
            fov_map: Field of view map for visibility checks
            
        Returns:
            Entity or None: The best target to attack, or None if no valid targets
        """
        visible_targets = []
        
        for entity in entities:
            entity_fighter = entity.get_component_optional(ComponentType.FIGHTER)
            if (entity != self.owner and 
                entity_fighter and 
                self._can_see_target(entity, fov_map) and
                self._is_hostile_to(entity)):
                
                distance = self.owner.distance_to(entity)
                priority = get_target_priority(self.owner.faction, entity.faction)
                visible_targets.append((entity, distance, priority))
        
        if not visible_targets:
            return None
        
        # Sort by priority (higher first), then by distance (closer first)
        visible_targets.sort(key=lambda x: (-x[2], x[1]))
        return visible_targets[0][0]
    
    def _can_see_target(self, target, fov_map) -> bool:
        """Check if this AI can see the target.
        
        Slimes use distance-based vision (radius 10) rather than player FOV,
        allowing them to act independently even when off-screen.
        
        Args:
            target: Entity to check visibility for
            fov_map: Field of view map (unused for slimes)
            
        Returns:
            bool: True if target is visible
        """
        # Slimes have a fixed vision radius of 10 tiles
        SLIME_VISION_RADIUS = 10
        distance = self.owner.distance_to(target)
        
        if distance > SLIME_VISION_RADIUS:
            return False
        
        # Check invisibility
        if hasattr(target, 'invisible') and target.invisible:
            # Future: Some monsters might see through invisibility
            return False
        
        return True
    
    def _is_hostile_to(self, target) -> bool:
        """Check if this slime should attack the target based on factions.
        
        Args:
            target: Entity to check hostility against
            
        Returns:
            bool: True if slime should attack the target
        """
        return are_factions_hostile(self.owner.faction, target.faction)
