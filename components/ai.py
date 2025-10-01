from random import randint
from typing import List, Optional, Any, Dict

import tcod as libtcod
import tcod.libtcodpy as libtcodpy

from game_messages import Message
from fov_functions import map_is_in_fov
from components.monster_action_logger import MonsterActionLogger
from components.faction import Faction, are_factions_hostile, get_target_priority


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
        actions_taken = []

        # print('The ' + self.owner.name + ' wonders when it will get to move.')
        monster = self.owner
        if map_is_in_fov(fov_map, monster.x, monster.y):
            # Check if target is invisible - if so, can't see them
            if (hasattr(target, 'has_status_effect') and 
                callable(target.has_status_effect) and 
                target.has_status_effect('invisibility') is True):
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

            if monster.distance_to(target) >= 2:
                # monster.move_towards(target.x, target.y, game_map, entities)
                MonsterActionLogger.log_action_attempt(monster, "movement", f"moving towards {target.name}")
                monster.move_astar(target, entities, game_map)
                actions_taken.append("movement")
            elif target.fighter.hp > 0:
                # print('The {0} insults you!'.format(monster.name))
                # Use new d20-based attack system
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
        # Check if monster has item usage capability
        if not (hasattr(self.owner, 'item_usage') and self.owner.item_usage):
            return None
            
        return self.owner.item_usage.get_item_usage_action(target, game_map, entities)
    
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
            if hasattr(self.owner, 'item_usage') and self.owner.item_usage:
                usage_results = self.owner.item_usage.use_item_with_failure(item, target, entities)
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
        # Check if monster has item-seeking AI capability
        if not (hasattr(self.owner, 'item_seeking_ai') and self.owner.item_seeking_ai):
            return None
            
        return self.owner.item_seeking_ai.get_item_seeking_action(game_map, entities, target)
    
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
        
        # Check if monster has inventory space
        if not (hasattr(self.owner, 'inventory') and self.owner.inventory):
            MonsterActionLogger.log_item_pickup(self.owner, item, False, "no inventory")
            return results
            
        if len(self.owner.inventory.items) >= self.owner.inventory.capacity:
            MonsterActionLogger.log_item_pickup(self.owner, item, False, "inventory full")
            return results
            
        # Add item to monster's inventory
        self.owner.inventory.add_item(item)
        MonsterActionLogger.log_inventory_change(self.owner, item, "added")
        
        # Remove item from world
        if item in entities:
            entities.remove(item)
            
        # Try to equip the item if it's equipment
        equipped = False
        if hasattr(item, 'equippable') and item.equippable:
            if hasattr(self.owner, 'equipment') and self.owner.equipment:
                # Simple equipping logic - equip if slot is empty
                if item.equippable.slot.value == "main_hand" and not self.owner.equipment.main_hand:
                    self.owner.equipment.toggle_equip(item)
                    MonsterActionLogger.log_equipment_change(self.owner, item, "equipped")
                    equipped = True
                elif item.equippable.slot.value == "off_hand" and not self.owner.equipment.off_hand:
                    self.owner.equipment.toggle_equip(item)
                    MonsterActionLogger.log_equipment_change(self.owner, item, "equipped")
                    equipped = True
        
        # Log successful pickup
        pickup_details = f"picked up and {'equipped' if equipped else 'stored'} {item.name}"
        MonsterActionLogger.log_item_pickup(self.owner, item, True, pickup_details)
        
        results.append({
            "message": Message(f"{self.owner.name.capitalize()} picks up the {item.name}!", (255, 255, 0))
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
        results = []
        
        # Zombies have limited FOV (radius 5)
        zombie_fov_radius = 5
        
        # Check if current target is still valid (alive and in FOV)
        if self.current_target:
            # Is target still alive and in FOV?
            if (self.current_target in entities and
                hasattr(self.current_target, 'fighter') and 
                self.current_target.fighter):
                
                distance = self.owner.distance_to(self.current_target)
                in_fov = distance <= zombie_fov_radius
                
                if in_fov:
                    # Target still in FOV!
                    if distance == 1:
                        # Adjacent - ATTACK!
                        # Check for other adjacent targets first
                        adjacent_targets = self._find_adjacent_targets(entities)
                        
                        if len(adjacent_targets) > 1:
                            # 50% chance to switch to different adjacent target
                            from random import random
                            if random() < 0.5:
                                from random import choice
                                other_targets = [e for e in adjacent_targets if e != self.current_target]
                                if other_targets:
                                    self.current_target = choice(other_targets)
                        
                        # Attack current target (use new d20 system)
                        attack_results = self.owner.fighter.attack_d20(self.current_target)
                        results.extend(attack_results)
                        return results
                    else:
                        # In FOV but not adjacent - CHASE!
                        self.owner.move_astar(self.current_target, entities, game_map)
                        return results
                else:
                    # Target out of FOV - lose interest
                    self.current_target = None
            else:
                # Target dead or removed - clear it
                self.current_target = None
        
        # No current target - look for any living entity in FOV
        visible_targets = self._find_visible_targets(entities, zombie_fov_radius)
        
        if visible_targets:
            # Pick closest target and lock onto it
            closest = min(visible_targets, key=lambda e: self.owner.distance_to(e))
            self.current_target = closest
            
            # If adjacent, attack immediately (use new d20 system)
            if self.owner.distance_to(closest) == 1:
                attack_results = self.owner.fighter.attack_d20(closest)
                results.extend(attack_results)
                return results
            else:
                # Chase it!
                self.owner.move_astar(closest, entities, game_map)
                return results
        
        # No visible targets - wander randomly
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
            if not (hasattr(entity, 'fighter') and entity.fighter):
                continue
            
            # Check if adjacent
            if self.owner.distance_to(entity) == 1:
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
            if not (hasattr(entity, 'fighter') and entity.fighter):
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
                    "message": Message(
                        "The {0} is no longer confused!".format(self.owner.name),
                        (255, 0, 0),
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
        
        # Only act when monster is in player's FOV (prevents off-screen monster-vs-monster)
        # This keeps the action focused on what the player can see
        if not map_is_in_fov(fov_map, monster.x, monster.y):
            return results
        
        # Find the best target based on faction relationships and distance
        best_target = self._find_best_target(entities, fov_map)
        
        if best_target:
            # Calculate distance to target
            distance = monster.distance_to(best_target)
            
            if distance >= 2:
                # Move towards target using A* pathfinding
                monster.move_astar(best_target, entities, game_map)
                MonsterActionLogger.log_action_attempt(
                    monster, "move", f"moving towards {best_target.name}"
                )
            elif best_target.fighter:
                # Attack the target (use new d20 system)
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
