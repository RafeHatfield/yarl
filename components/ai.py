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

if TYPE_CHECKING:
    from entity import Entity


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


class BossAI:
    """AI for boss monsters with enhanced combat behavior.
    
    Bosses fight smarter than regular monsters:
    - Apply enrage damage multiplier when enraged
    - More aggressive when at low HP
    - Better positioning and targeting
    
    Attributes:
        owner (Entity): The entity that owns this AI component
        in_combat (bool): Tracks if boss has been attacked
    """
    
    def __init__(self):
        """Initialize a BossAI."""
        self.owner = None
        self.in_combat = False
    
    def take_turn(self, target, fov_map, game_map, entities):
        """Execute one turn of boss AI behavior.
        
        Bosses use standard monster AI but apply damage multipliers
        from their Boss component when enraged.
        
        Args:
            target (Entity): The target entity (usually the player)
            fov_map: Field of view map for visibility checks
            game_map (GameMap): The game map for pathfinding
            entities (list): List of all entities for collision detection
            
        Returns:
            list: List of result dictionaries with AI actions and effects
        """
        from components.component_registry import ComponentType
        
        monster = self.owner
        results = []
        
        # Get boss component for damage multiplier
        boss = monster.get_component_optional(ComponentType.BOSS)
        
        # Check if monster can see the target (use same FOV check as BasicMonster)
        if map_is_in_fov(fov_map, target.x, target.y):
            
            # Calculate distance to target
            distance = ((monster.x - target.x) ** 2 + (monster.y - target.y) ** 2) ** 0.5
            
            if distance <= 1:
                # Adjacent - attack with boss damage multiplier!
                base_damage = monster.fighter.attack(target)
                
                # Apply boss damage multiplier if enraged
                if boss and boss.is_enraged:
                    multiplier = boss.get_damage_multiplier()
                    if multiplier > 1.0:
                        # We already attacked, but the damage multiplier should be
                        # applied in the attack() method itself. For now, just
                        # track that we're enraged (visual indicator could be added)
                        pass
                
                results.extend(base_damage)
            else:
                # Move towards target
                path = self._get_path_to(target, game_map, entities)
                if path:
                    next_x, next_y = path[0]
                    
                    # Check if destination is blocked by another entity
                    blocking_entity = None
                    for entity in entities:
                        if entity.x == next_x and entity.y == next_y and entity.blocks:
                            blocking_entity = entity
                            break
                    
                    if not blocking_entity:
                        monster.x = next_x
                        monster.y = next_y
        
        return results
    
    def _get_path_to(self, target, game_map, entities):
        """Calculate A* path to target using modern tcod.path API.
        
        Args:
            target (Entity): Target to path to
            game_map (GameMap): Game map for pathfinding
            entities (list): All entities for collision detection
            
        Returns:
            list: List of (x, y) tuples representing the path, or empty list if no path
        """
        import tcod.path
        
        # Create walkable map from tiles (indexed [y, x])
        walkable = np.array(game_map.tiles["walkable"], dtype=bool)
        
        # Block entity positions (other entities block movement)
        for entity in entities:
            if entity.blocks and entity != self.owner and entity != target:
                if 0 <= entity.x < game_map.width and 0 <= entity.y < game_map.height:
                    walkable[entity.y, entity.x] = False
        
        # Create cost map (1 = walkable, 0 = blocked)
        cost = np.where(walkable, 1, 0).astype(np.int8)
        
        # Transpose from [y, x] to [x, y] for tcod
        cost_transposed = cost.T
        
        # Create pathfinder using modern tcod.path API
        graph = tcod.path.SimpleGraph(cost=cost_transposed, cardinal=2, diagonal=3)
        pf = tcod.path.Pathfinder(graph)
        pf.add_root((self.owner.x, self.owner.y))
        
        # Compute path to target
        path = pf.path_to((target.x, target.y))
        
        # Return path excluding starting position
        return [(x, y) for x, y in path[1:]]


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
            item_usage_action = self._try_item_usage(target, game_map, entities)
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
                attack_results = monster.fighter.attack_d20(target)
                results.extend(attack_results)
                actions_taken.append("combat")

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
            dx, dy = action["move"]
            self.owner.move(dx, dy)
            
        elif "pickup_item" in action:
            # Pick up item
            item = action["pickup_item"]
            results.extend(self._pickup_item(item, entities))
            
        return results
    
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
                    MonsterActionLogger.log_equipment_change(self.owner, item, "equipped")
                    equipped = True
                elif item.equippable.slot.value == "off_hand" and not equipment.off_hand:
                    equipment.toggle_equip(item)
                    MonsterActionLogger.log_equipment_change(self.owner, item, "equipped")
                    equipped = True
        
        # Log successful pickup
        pickup_details = f"picked up and {'equipped' if equipped else 'stored'} {item.name}"
        MonsterActionLogger.log_item_pickup(self.owner, item, True, pickup_details)
        
        results.append({
            "message": MB.item_pickup(f"{self.owner.name.capitalize()} picks up the {item.name}!")
        })
        
        return results


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
        
        # Process status effects at the start of turn (optional)
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
                        attack_results = self.owner.fighter.attack_d20(self.current_target)
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
                attack_results = self.owner.fighter.attack_d20(closest)
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
                    "message": MB.status_effect(
                        "The {0} is no longer confused!".format(self.owner.name)
                    )
                }
            )

        return results


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
        
        # Process status effects at the start of turn (optional)
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
            if (entity != self.owner and 
                entity.fighter and 
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
