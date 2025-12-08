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
        self.in_combat = False  # Tracks if monster has been attacked
        self.portal_usable = True  # Basic monsters can use portals tactically

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
        actions_taken = []

        # Process status effects at the start of turn
        status_effects = self.owner.get_component_optional(ComponentType.STATUS_EFFECTS)
        if status_effects:
            effect_results = status_effects.process_turn_start()
            for result in effect_results:
                # Check if status effect wants to skip this turn (e.g., Slow effect)
                if result.get('skip_turn'):
                    from game_messages import Message
                    results.append(result)
                    return results  # Skip turn entirely
                results.append(result)

        # Check for paralysis - completely prevents all actions
        if (hasattr(self.owner, 'has_status_effect') and 
            callable(self.owner.has_status_effect) and 
            self.owner.has_status_effect('paralysis')):
            results.append({'message': MB.custom(f"{self.owner.name} is paralyzed and cannot act!", (150, 75, 200))})
            MonsterActionLogger.log_turn_summary(self.owner, ["paralyzed"])
            return results
        
        # Check for fear - causes monster to flee
        if (hasattr(self.owner, 'has_status_effect') and 
            callable(self.owner.has_status_effect) and 
            self.owner.has_status_effect('fear')):
            # Try to move away from target
            flee_results = self._flee_from_target(target, game_map, entities)
            if flee_results:
                results.extend(flee_results)
            MonsterActionLogger.log_turn_summary(self.owner, ["fleeing"])
            # Process status effects at turn end
            status_effects = self.owner.get_component_optional(ComponentType.STATUS_EFFECTS)
            if status_effects:
                end_results = status_effects.process_turn_end()
                results.extend(end_results)
            return results

        # Check if there's a taunted target (Yo Mama spell effect)
        taunted_target = find_taunted_target(entities)
        is_pursuing_taunt = False
        is_taunted_target = False  # Is THIS monster the taunted one?
        
        if taunted_target:
            if taunted_target == self.owner:
                # THIS monster is taunted - it should fight back against attackers!
                is_taunted_target = True
            else:
                # Another monster is taunted - pursue it!
                target = taunted_target
                is_pursuing_taunt = True

        # print('The ' + self.owner.name + ' wonders when it will get to move.')
        monster = self.owner
        
        # Simple AI decision: Act if pursuing taunt, in combat with player, or in player's FOV
        # When taunt ends, monsters return to normal behavior (only act when in FOV or in combat)
        if is_pursuing_taunt or self.in_combat or map_is_in_fov(fov_map, monster.x, monster.y):
            # If THIS monster is the taunted target, fight back against nearest attacker!
            if is_taunted_target:
                from components.faction import are_factions_hostile
                
                # When taunted, being attacked from all sides - fight the CLOSEST threat in FOV!
                # Only aware of what we can see - no omniscience
                closest_hostile = None
                closest_distance = float('inf')
                
                monster_faction = getattr(self.owner, 'faction', None)
                
                for entity in entities:
                    if entity == self.owner:  # Skip self
                        continue
                    
                    # ONLY check entities in OUR FOV - we can only see what's around us!
                    if not map_is_in_fov(fov_map, entity.x, entity.y):
                        continue
                    
                    # Check if entity is a hostile with fighter
                    fighter = entity.get_component_optional(ComponentType.FIGHTER)
                    if fighter and fighter.hp > 0:
                        # Check if hostile based on faction (or just check if has fighter for simplicity)
                        entity_faction = getattr(entity, 'faction', None)
                        
                        # Attack anything with a fighter that's in our FOV (we're being attacked!)
                        # This includes: player, slimes, other factions
                        # Exclude friendly same-faction entities
                        if monster_faction and entity_faction:
                            is_hostile = are_factions_hostile(monster_faction, entity_faction)
                        else:
                            # No faction info - assume hostile if they have fighter
                            is_hostile = True
                        
                        if is_hostile:
                            # Find CLOSEST hostile in FOV
                            distance = self.owner.distance_to(entity)
                            if distance < closest_distance:
                                closest_distance = distance
                                closest_hostile = entity
                
                if closest_hostile:
                    # Fight back against the nearest visible attacker!
                    target = closest_hostile
                    # Note: This might be player, slime, or anything else attacking us
                # If no hostiles in FOV, keep original target (player)
            
            # Check if target is invisible - but taunt overrides invisibility!
            if (not is_pursuing_taunt and not is_taunted_target and
                hasattr(target, 'has_status_effect') and 
                callable(target.has_status_effect) and 
                target.has_status_effect('invisibility') is True):
                
                # IMPORTANT: If player is invisible but monster is in combat,
                # look for OTHER visible hostiles based on FACTION (e.g., slime attacking us!)
                if self.in_combat or True:  # Always check for visible hostiles when player invisible
                    from components.faction import are_factions_hostile, get_target_priority
                    
                    # Find nearest visible hostile based on faction relationships
                    closest_hostile = None
                    closest_distance = float('inf')
                    best_priority = 0
                    
                    monster_faction = getattr(self.owner, 'faction', None)
                    
                    for entity in entities:
                        if entity == self.owner or entity == target:  # Skip self and invisible player
                            continue
                        
                        # Check if entity is a hostile with fighter
                        fighter = entity.get_component_optional(ComponentType.FIGHTER)
                        if fighter and fighter.hp > 0:
                            # Check if visible in FOV
                            if map_is_in_fov(fov_map, entity.x, entity.y):
                                # Check if hostile based on faction
                                entity_faction = getattr(entity, 'faction', None)
                                if monster_faction and entity_faction:
                                    if are_factions_hostile(monster_faction, entity_faction):
                                        distance = self.owner.distance_to(entity)
                                        priority = get_target_priority(monster_faction, entity_faction)
                                        
                                        # Only consider targets with positive priority (actually hostile)
                                        if priority > 0:
                                            # Pick highest priority target, or closest if same priority
                                            if (priority > best_priority or 
                                                (priority == best_priority and distance < closest_distance)):
                                                closest_distance = distance
                                                best_priority = priority
                                                closest_hostile = entity
                    
                    if closest_hostile:
                        # Fight the visible hostile! (e.g., slime that's attacking us)
                        target = closest_hostile
                    else:
                        # No visible targets - can't do anything
                        MonsterActionLogger.log_turn_summary(monster, ["cannot_see_invisible_target"])
                        return results
            
            # Check for item usage first (scrolls, potions, etc.)
            # Only try to use items occasionally to avoid overuse of valuable resources
            from random import random
            from config.game_constants import get_monster_equipment_config
            monster_config = get_monster_equipment_config()
            if random() < monster_config.ITEM_USAGE_ATTEMPT_RATE:
                item_usage_action = self._try_item_usage(target, game_map, entities)
            else:
                item_usage_action = None
            
            if item_usage_action:
                MonsterActionLogger.log_action_attempt(monster, "item_usage", 
                    f"attempting to use {item_usage_action.get('use_item', {}).name if item_usage_action.get('use_item') else 'unknown item'}")
                results.extend(self._process_item_usage_action(item_usage_action, entities))
                actions_taken.append("item_usage")
                MonsterActionLogger.log_turn_summary(monster, actions_taken)
                return results
            
            # Check for item-seeking behavior (if monster has this capability)
            # BUT only if monster hasn't been attacked yet (not in combat)
            # Once attacked, prioritize fighting over looting!
            # ALSO: Don't seek items when taunted - being attacked from all sides!
            if not self.in_combat and not is_taunted_target:
                item_action = self._try_item_seeking(target, game_map, entities)
                if item_action:
                    if "pickup_item" in item_action:
                        MonsterActionLogger.log_action_attempt(monster, "item_pickup", 
                            f"attempting to pick up {item_action['pickup_item'].name}")
                    elif "move" in item_action:
                        MonsterActionLogger.log_action_attempt(monster, "item_seeking_movement", 
                            f"moving towards item")
                    results.extend(self._process_item_action(item_action, entities))
                    actions_taken.append("item_seeking")
                    MonsterActionLogger.log_turn_summary(monster, actions_taken)
                    return results

            # Check weapon reach for attack range
            # Use Chebyshev distance (chessboard/king's move) for melee range
            # This treats all 8 surrounding tiles as distance 1
            distance = monster.chebyshev_distance_to(target)
            weapon_reach = get_weapon_reach(monster)
            
            if distance > weapon_reach:
                # Too far to attack - move towards target
                # Check if immobilized (Glue spell)
                if (hasattr(monster, 'has_status_effect') and 
                    callable(monster.has_status_effect) and 
                    monster.has_status_effect('immobilized')):
                    results.append({'message': MB.custom(f"{monster.name} struggles against the glue!", (139, 69, 19))})
                    MonsterActionLogger.log_turn_summary(monster, ["immobilized"])
                    return results
                
                MonsterActionLogger.log_action_attempt(monster, "movement", f"moving towards {target.name}")
                monster.move_astar(target, entities, game_map)
                actions_taken.append("movement")
            elif target.fighter and target.fighter.hp > 0:
                # Within attack range - attack!
                MonsterActionLogger.log_action_attempt(monster, "combat", f"attacking {target.name}")
                
                # Phase 8: Roll for hit before damage
                attack_results, attack_hit = self._perform_hit_checked_attack(monster, target, fov_map)
                results.extend(attack_results)
                actions_taken.append("combat")
                
                # Check for speed bonus attack (Phase 4)
                # Only if target is still alive and monster has speed tracker
                # Phase 8: Momentum still builds even on miss
                if target.fighter.hp > 0:
                    bonus_results = self._try_bonus_attack(monster, target, fov_map)
                    if bonus_results:
                        results.extend(bonus_results)
                        actions_taken.append("bonus_attack")

        # Process status effects at turn end (decrement durations, remove expired effects)
        status_effects = monster.get_component_optional(ComponentType.STATUS_EFFECTS)
        if status_effects:
            end_results = status_effects.process_turn_end()
            results.extend(end_results)

        MonsterActionLogger.log_turn_summary(monster, actions_taken)
        return results
    
    def _try_item_usage(self, target, game_map, entities):
        """Try to get an item usage action for this monster.
        
        Args:
            target: The target entity (player)
            game_map: Current game map
            entities: List of all entities
            
        Returns:
            dict: Item usage action if available, None otherwise
        """
        # Check if monster has item usage capability (optional)
        item_usage = self.owner.get_component_optional(ComponentType.ITEM_USAGE)
        if not item_usage:
            return None
            
        return item_usage.get_item_usage_action(target, game_map, entities)
    
    def _process_item_usage_action(self, action, entities):
        """Process an item usage action.
        
        Args:
            action: Item usage action dictionary
            entities: List of all entities
            
        Returns:
            list: List of result dictionaries
        """
        results = []
        
        if "use_item" in action:
            item = action["use_item"]
            target = action.get("target")
            
            # Use item with failure mechanics
            # Item usage is optional (not all monsters can use items)
            item_usage = self.owner.get_component_optional(ComponentType.ITEM_USAGE)
            if item_usage:
                usage_results = item_usage.use_item_with_failure(item, target, entities)
                results.extend(usage_results)
            
        return results
    
    def _try_item_seeking(self, target, game_map, entities):
        """Try to get an item-seeking action for this monster.
        
        Args:
            target: The target entity (player)
            game_map: Current game map
            entities: List of all entities
            
        Returns:
            dict: Item action if available, None otherwise
        """
        # Check if monster has item-seeking AI capability (optional)
        item_seeking_ai = self.owner.get_component_optional(ComponentType.ITEM_SEEKING_AI)
        if not item_seeking_ai:
            return None
            
        return item_seeking_ai.get_item_seeking_action(game_map, entities, target)
    
    def _process_item_action(self, action, entities):
        """Process an item-related action.
        
        Args:
            action: Action dictionary
            entities: List of all entities
            
        Returns:
            list: List of result dictionaries
        """
        results = []
        
        if "move" in action:
            # Move towards item
            # Check if immobilized (Glue spell)
            if (hasattr(self.owner, 'has_status_effect') and 
                callable(self.owner.has_status_effect) and 
                self.owner.has_status_effect('immobilized')):
                results.append({'message': MB.custom(f"{self.owner.name} struggles against the glue!", (139, 69, 19))})
                return results
            
            dx, dy = action["move"]
            self.owner.move(dx, dy)
            
        elif "pickup_item" in action:
            # Pick up item
            item = action["pickup_item"]
            results.extend(self._pickup_item(item, entities))
            
        return results
    
    def _get_speed_bonus_ratio(self, entity) -> float:
        """Get the speed bonus ratio for an entity.
        
        Used for relative speed gating - only the faster entity can build momentum.
        
        Args:
            entity: The entity to check
            
        Returns:
            float: Speed bonus ratio (0.0 if entity has no SpeedBonusTracker)
        """
        if not entity:
            return 0.0
        speed_tracker = entity.get_component_optional(ComponentType.SPEED_BONUS_TRACKER)
        if speed_tracker:
            return speed_tracker.speed_bonus_ratio
        return 0.0

    def _pickup_item(self, item, entities):
        """Handle picking up an item.
        
        Args:
            item: Item entity to pick up
            entities: List of all entities
            
        Returns:
            list: List of result dictionaries
        """
        results = []
        
        # Check if monster has inventory space (required for pickup)
        inventory = self.owner.require_component(ComponentType.INVENTORY)
            
        if len(inventory.items) >= inventory.capacity:
            MonsterActionLogger.log_item_pickup(self.owner, item, False, "inventory full")
            return results
            
        # Add item to monster's inventory
        inventory.add_item(item)
        MonsterActionLogger.log_inventory_change(self.owner, item, "added")
        
        # Remove item from world
        if item in entities:
            entities.remove(item)
            
        # Try to equip the item if it's equipment
        equipped = False
        if item.components.has(ComponentType.EQUIPPABLE):
            equipment = self.owner.get_component_optional(ComponentType.EQUIPMENT)
            if equipment:
                # Simple equipping logic - equip if slot is empty
                if item.equippable.slot.value == "main_hand" and not equipment.main_hand:
                    self.owner.equipment.toggle_equip(item)
                    # CRITICAL: Remove from inventory when equipped!
                    # Otherwise item exists in BOTH inventory AND equipment slot
                    # causing duplicate drops on death
                    inventory.items.remove(item)
                    MonsterActionLogger.log_equipment_change(self.owner, item, "equipped")
                    equipped = True
                elif item.equippable.slot.value == "off_hand" and not equipment.off_hand:
                    equipment.toggle_equip(item)
                    # CRITICAL: Remove from inventory when equipped!
                    inventory.items.remove(item)
                    MonsterActionLogger.log_equipment_change(self.owner, item, "equipped")
                    equipped = True
        
        # Log successful pickup
        pickup_details = f"picked up and {'equipped' if equipped else 'stored'} {item.name}"
        MonsterActionLogger.log_item_pickup(self.owner, item, True, pickup_details)
        
        # Use display name to respect identification status
        display_name = item.name
        if item.item:
            display_name = item.item.get_display_name(show_quantity=False)
        
        results.append({
            "message": MB.item_pickup(f"{self.owner.name.capitalize()} picks up the {display_name}!")
        })
        
        return results
    
    def _perform_hit_checked_attack(self, monster, target, fov_map) -> tuple:
        """Perform an attack with Phase 8 hit/miss check.
        
        Args:
            monster: The attacking monster entity
            target: The target entity
            fov_map: FOV map for visibility checks
            
        Returns:
            tuple: (list of result dicts, bool indicating if attack hit)
        """
        from balance.hit_model import roll_to_hit_entities
        from visual_effects import show_miss
        
        results = []
        
        # Roll to hit based on accuracy vs evasion
        attack_hit = roll_to_hit_entities(monster, target)
        
        if not attack_hit:
            # Attack missed - show miss message if visible
            if map_is_in_fov(fov_map, monster.x, monster.y):
                show_miss(target.x, target.y, entity=target)
                
                # Generate miss message
                # If target is player, use "dodge" terminology for player agency feel
                if hasattr(target, 'name') and target.name == "Player":
                    miss_msg = MB.combat_dodge(f"{monster.name.capitalize()} attacks but you dodge nimbly!")
                else:
                    miss_msg = MB.combat_miss(f"{monster.name.capitalize()} misses {target.name}!")
                
                results.append({'message': miss_msg})
            
            logger.debug(f"[MONSTER MISS] {monster.name} missed {target.name}")
            return results, False
        
        # Attack hit - proceed with damage
        attack_results = monster.fighter.attack_d20(target)
        results.extend(attack_results)
        return results, True
    
    def _try_bonus_attack(self, monster, target, fov_map) -> list:
        """Try to execute a bonus attack based on speed bonus.
        
        Phase 4: Monster speed bonus system integration.
        Phase 8: Now includes hit/miss check on bonus attacks.
        
        Args:
            monster: The monster entity
            target: The target entity (player or other)
            fov_map: FOV map for visibility checks
            
        Returns:
            list: List of result dictionaries (attack results if bonus triggered)
        """
        results = []
        
        # Check if monster has speed bonus tracker
        speed_tracker = monster.get_component_optional(ComponentType.SPEED_BONUS_TRACKER)
        if not speed_tracker:
            return results
        
        # Gate: Only roll if monster is faster than target
        # Slower entities cannot build momentum against faster ones
        target_speed = self._get_speed_bonus_ratio(target)
        if speed_tracker.speed_bonus_ratio <= target_speed:
            # Monster is not faster than target - no momentum building
            return results
        
        # Roll for bonus attack
        if speed_tracker.roll_for_bonus_attack():
            # Bonus attack triggered!
            # Check if target is still valid
            if not target or not target.fighter or target.fighter.hp <= 0:
                return results
            
            # Show message and visual effect only if monster is visible to player
            if map_is_in_fov(fov_map, monster.x, monster.y):
                bonus_msg = MB.combat_monster_bonus_attack(
                    f"⚠️ [BONUS ATTACK] {monster.name} strikes twice with blinding speed!"
                )
                results.append({'message': bonus_msg})
                
                # Queue VFX flash for monster bonus attack (same as critical hit effect)
                from visual_effects import show_hit
                show_hit(monster.x, monster.y, entity=monster, is_critical=True)
            
            # Debug logging for balance testing
            logger.debug(f"[MONSTER BONUS ATTACK] {monster.name} triggered bonus attack "
                        f"(speed: +{int(speed_tracker.speed_bonus_ratio * 100)}%)")
            
            # Execute the bonus attack (with Phase 8 hit check)
            MonsterActionLogger.log_action_attempt(monster, "bonus_combat", 
                f"bonus attack on {target.name}")
            bonus_attack_results, _ = self._perform_hit_checked_attack(monster, target, fov_map)
            results.extend(bonus_attack_results)
        else:
            # Debug logging for balance testing (optional - shows momentum building)
            if speed_tracker.attack_counter > 0:
                logger.debug(f"[MONSTER MOMENTUM] {monster.name} building momentum: "
                            f"{int(speed_tracker.current_chance * 100)}% bonus chance")
        
        return results

    def _flee_from_target(self, target, game_map, entities):
        """Move away from target when afraid.
        
        Finds the best direction to flee (away from target) and moves there.
        
        Args:
            target (Entity): Entity to flee from
            game_map (GameMap): Game map for walkability checks
            entities (list): All entities for collision detection
            
        Returns:
            list: List of result dictionaries
        """
        monster = self.owner
        results = []
        
        # Calculate direction away from target
        dx = monster.x - target.x
        dy = monster.y - target.y
        
        # Normalize direction (make it unit length approximately)
        distance = max(abs(dx), abs(dy), 1)  # Avoid division by zero
        dx = dx / distance
        dy = dy / distance
        
        # Try to move in the flee direction (prefer diagonal if possible)
        flee_x = monster.x + (1 if dx > 0.3 else (-1 if dx < -0.3 else 0))
        flee_y = monster.y + (1 if dy > 0.3 else (-1 if dy < -0.3 else 0))
        
        # Check if flee position is valid
        if (0 <= flee_x < game_map.width and 0 <= flee_y < game_map.height and
            not game_map.is_blocked(flee_x, flee_y)):
            
            # Check for blocking entities
            blocked = False
            for entity in entities:
                if entity.x == flee_x and entity.y == flee_y and entity.blocks:
                    blocked = True
                    break
            
            if not blocked:
                monster.x = flee_x
                monster.y = flee_y
                return results
        
        # If direct flee failed, try cardinal directions away from target
        directions = []
        if dx > 0:
            directions.append((1, 0))
        if dx < 0:
            directions.append((-1, 0))
        if dy > 0:
            directions.append((0, 1))
        if dy < 0:
            directions.append((0, -1))
        
        for dir_x, dir_y in directions:
            new_x = monster.x + dir_x
            new_y = monster.y + dir_y
            
            if (0 <= new_x < game_map.width and 0 <= new_y < game_map.height and
                not game_map.is_blocked(new_x, new_y)):
                
                # Check for blocking entities
                blocked = False
                for entity in entities:
                    if entity.x == new_x and entity.y == new_y and entity.blocks:
                        blocked = True
                        break
                
                if not blocked:
                    monster.x = new_x
                    monster.y = new_y
                    return results
        
        # Can't flee - stay in place
        return results


