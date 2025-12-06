"""Equipment management component.

This module defines the Equipment component which manages equipped items
and calculates total stat bonuses from all equipped gear.
"""

import logging
from typing import Optional, List, Dict, Any
from equipment_slots import EquipmentSlots
from components.component_registry import ComponentType

logger = logging.getLogger(__name__)


class Equipment:
    """Component that manages equipped items and their stat bonuses.

    This component handles equipment slots (weapons, shields, armor, rings) and
    calculates the total stat bonuses provided by all equipped items.
    It supports equipping, unequipping, and replacing items.

    Attributes:
        main_hand (Entity): Item equipped in the main hand slot (weapon)
        off_hand (Entity): Item equipped in the off hand slot (shield/weapon)
        head (Entity): Item equipped in the head slot (helmet)
        chest (Entity): Item equipped in the chest slot (armor)
        feet (Entity): Item equipped in the feet slot (boots)
        left_ring (Entity): Item equipped in the left ring slot
        right_ring (Entity): Item equipped in the right ring slot
        owner (Entity): The entity that owns this equipment component
    """

    def __init__(self, main_hand: Optional[Any] = None, off_hand: Optional[Any] = None, 
                 head: Optional[Any] = None, chest: Optional[Any] = None, feet: Optional[Any] = None,
                 left_ring: Optional[Any] = None, right_ring: Optional[Any] = None) -> None:
        """Initialize the Equipment component.

        Args:
            main_hand (Optional[Any], optional): Initial main hand equipment (Entity type)
            off_hand (Optional[Any], optional): Initial off hand equipment (Entity type)
            head (Optional[Any], optional): Initial head equipment (Entity type)
            chest (Optional[Any], optional): Initial chest equipment (Entity type)
            feet (Optional[Any], optional): Initial feet equipment (Entity type)
            left_ring (Optional[Any], optional): Initial left ring equipment (Entity type)
            right_ring (Optional[Any], optional): Initial right ring equipment (Entity type)
        """
        self.main_hand: Optional[Any] = main_hand
        self.off_hand: Optional[Any] = off_hand
        self.head: Optional[Any] = head
        self.chest: Optional[Any] = chest
        self.feet: Optional[Any] = feet
        self.left_ring: Optional[Any] = left_ring
        self.right_ring: Optional[Any] = right_ring
        self.owner: Optional[Any] = None  # Entity, Will be set when component is registered

    @property
    def max_hp_bonus(self) -> int:
        """Calculate total max HP bonus from all equipped items.

        Returns:
            int: Total maximum HP bonus from equipped items
        """
        bonus = 0

        for item in [self.main_hand, self.off_hand, self.head, self.chest, self.feet, self.left_ring, self.right_ring]:
            if item and item.equippable:
                item_bonus = item.equippable.max_hp_bonus
                # Defensive: treat None as 0
                if item_bonus is not None:
                    bonus += item_bonus

        return bonus

    @property
    def power_bonus(self) -> int:
        """Calculate total power bonus from all equipped items.

        Returns:
            int: Total attack power bonus from equipped items
        """
        bonus = 0

        for item in [self.main_hand, self.off_hand, self.head, self.chest, self.feet, self.left_ring, self.right_ring]:
            if item and item.equippable:
                item_bonus = item.equippable.power_bonus
                # Defensive: treat None as 0
                if item_bonus is not None:
                    bonus += item_bonus

        return bonus

    @property
    def defense_bonus(self) -> int:
        """Calculate total defense bonus from all equipped items.

        Returns:
            int: Total defense bonus from equipped items
        """
        bonus = 0

        for item in [self.main_hand, self.off_hand, self.head, self.chest, self.feet, self.left_ring, self.right_ring]:
            if item and item.equippable:
                item_bonus = item.equippable.defense_bonus
                # Defensive: treat None as 0
                if item_bonus is not None:
                    bonus += item_bonus

        return bonus

    def get_resistance_bonus(self, resistance_type: Any) -> int:
        """Calculate total resistance bonus for a specific resistance type from all equipped items.

        Args:
            resistance_type: The resistance type to calculate bonus for (ResistanceType enum)

        Returns:
            int: Total resistance percentage bonus from all equipped items (0-100+)
        """
        bonus = 0

        for item in [self.main_hand, self.off_hand, self.head, self.chest, self.feet, self.left_ring, self.right_ring]:
            if item and item.equippable:
                # Check if equippable has resistances dict
                if hasattr(item.equippable, 'resistances') and item.equippable.resistances:
                    # Get resistance bonus for this type (default to 0 if not present)
                    item_resistance = item.equippable.resistances.get(resistance_type, 0)
                    if item_resistance is not None:
                        bonus += item_resistance

        return bonus

    def toggle_equip(self, equippable_entity: Any) -> List[Dict[str, Any]]:
        """Equip, unequip, or replace an item in the appropriate slot.

        If the item is already equipped, it will be unequipped.
        If the slot is empty, the item will be equipped.
        If the slot has a different item, it will be replaced.
        
        Two-handed weapons prevent shield use:
        - Equipping a two-handed weapon will unequip any shield
        - Equipping a shield will unequip any two-handed weapon

        Args:
            equippable_entity (Any): The entity with an equippable component (Entity type)

        Returns:
            List[Dict[str, Any]]: List of result dictionaries with 'equipped', 'dequipped', or 'cannot_equip' keys
        """
        results = []
        slot = equippable_entity.equippable.slot

        # Special handling for RING slot: choose left or right automatically
        # IMPORTANT: Do this BEFORE the slot_map check!
        if slot == EquipmentSlots.RING:
            # Check if this ring is already equipped in either slot
            if self.left_ring == equippable_entity:
                slot_attr = 'left_ring'
            elif self.right_ring == equippable_entity:
                slot_attr = 'right_ring'
            else:
                # Not currently equipped - find an available slot
                if self.left_ring is None:
                    slot_attr = 'left_ring'
                elif self.right_ring is None:
                    slot_attr = 'right_ring'
                else:
                    # Both slots full, replace left ring
                    slot_attr = 'left_ring'
        else:
            # Map slots to their attributes
            slot_map = {
                EquipmentSlots.MAIN_HAND: 'main_hand',
                EquipmentSlots.OFF_HAND: 'off_hand',
                EquipmentSlots.HEAD: 'head',
                EquipmentSlots.CHEST: 'chest',
                EquipmentSlots.FEET: 'feet',
                EquipmentSlots.LEFT_RING: 'left_ring',
                EquipmentSlots.RIGHT_RING: 'right_ring'
            }

            slot_attr = slot_map.get(slot)
            if not slot_attr:
                return results  # Unknown slot

        current_item = getattr(self, slot_attr)

        if current_item == equippable_entity:
            # Unequip the item
            setattr(self, slot_attr, None)
            
            # CRITICAL: Add back to inventory when unequipping (if there's space)
            # This ensures the item doesn't disappear and can be dropped properly
            if self.owner and hasattr(self.owner, 'inventory') and self.owner.require_component(ComponentType.INVENTORY):
                if equippable_entity not in self.owner.require_component(ComponentType.INVENTORY).items:
                    if len(self.owner.require_component(ComponentType.INVENTORY).items) < self.owner.require_component(ComponentType.INVENTORY).capacity:
                        self.owner.require_component(ComponentType.INVENTORY).items.append(equippable_entity)
                        logger.debug(f"Added {equippable_entity.name} back to {self.owner.name}'s inventory (unequipped)")
                    else:
                        logger.warning(f"Cannot unequip {equippable_entity.name} - {self.owner.name}'s inventory is full!")
            
            results.append({"dequipped": equippable_entity})
        else:
            # Check for two-handed weapon conflicts BEFORE equipping
            two_handed_conflict = False
            
            # Trying to equip a two-handed weapon while holding a shield
            if (slot == EquipmentSlots.MAIN_HAND and 
                hasattr(equippable_entity.equippable, 'two_handed') and
                equippable_entity.equippable.two_handed is True and 
                self.off_hand is not None):
                # Add shield back to inventory before unequipping
                if self.owner:
                    inventory = self.owner.get_component_optional(ComponentType.INVENTORY)
                    if inventory:
                        if self.off_hand not in inventory.items:
                            if len(inventory.items) < inventory.capacity:
                                inventory.items.append(self.off_hand)
                                logger.debug(f"Added auto-unequipped {self.off_hand.name} back to inventory")
                
                # Auto-unequip the shield
                results.append({"dequipped": self.off_hand})
                self.off_hand = None
                logger.debug(f"Auto-unequipped off_hand to equip two-handed weapon: {equippable_entity.name}")
            
            # Trying to equip a shield while holding a two-handed weapon
            elif (slot == EquipmentSlots.OFF_HAND and 
                  self.main_hand is not None and
                  hasattr(self.main_hand.equippable, 'two_handed') and
                  self.main_hand.equippable.two_handed is True):
                # Add two-handed weapon back to inventory before unequipping
                if self.owner:
                    inventory = self.owner.get_component_optional(ComponentType.INVENTORY)
                    if inventory:
                        if self.main_hand not in inventory.items:
                            if len(inventory.items) < inventory.capacity:
                                inventory.items.append(self.main_hand)
                                logger.debug(f"Added auto-unequipped {self.main_hand.name} back to inventory")
                
                # Auto-unequip the two-handed weapon
                results.append({"dequipped": self.main_hand})
                self.main_hand = None
                logger.debug(f"Auto-unequipped two-handed weapon to equip shield: {equippable_entity.name}")
            
            # Replace or equip
            if current_item:
                # Add the replaced item back to inventory (if there's space)
                if self.owner:
                    inventory = self.owner.get_component_optional(ComponentType.INVENTORY)
                    if inventory:
                        if current_item not in inventory.items:
                            if len(inventory.items) < inventory.capacity:
                                inventory.items.append(current_item)
                                logger.debug(f"Added replaced {current_item.name} back to {self.owner.name}'s inventory")
                
                results.append({"dequipped": current_item})

            setattr(self, slot_attr, equippable_entity)
            
            # CRITICAL: Remove from inventory when equipping (prevents duplicate drops on death)
            # When a monster equips an item, it should only be in the equipment slot, NOT inventory
            if self.owner:
                inventory = self.owner.get_component_optional(ComponentType.INVENTORY)
                if inventory:
                    if equippable_entity in inventory.items:
                        inventory.items.remove(equippable_entity)
                        logger.debug(f"Removed {equippable_entity.name} from {self.owner.name}'s inventory (now equipped)")
            
            # Auto-identify equipment when equipped (traditional roguelike behavior)
            if hasattr(equippable_entity, 'item') and equippable_entity.get_component_optional(ComponentType.ITEM):
                was_unidentified = equippable_entity.get_component_optional(ComponentType.ITEM).identify()
                if was_unidentified:
                    # Add identification message
                    from message_builder import MessageBuilder as MB
                    results.append({
                        "message": MB.success(f"You recognize this as {equippable_entity.name}!"),
                        "identified": True
                    })
            
            results.append({"equipped": equippable_entity})

        # Phase 5: Handle speed bonus changes on equip/unequip
        self._update_speed_bonus_from_equipment(results)
        
        return results
    
    def _update_speed_bonus_from_equipment(self, results: List[Dict[str, Any]]) -> None:
        """Recalculate speed bonus from all equipped items.
        
        Phase 5: Called after equip/unequip to update the owner's SpeedBonusTracker.
        
        Args:
            results: Results list to add messages to
        """
        if not self.owner:
            return
        
        # Get or create speed bonus tracker
        speed_tracker = self.owner.get_component_optional(ComponentType.SPEED_BONUS_TRACKER)
        if not speed_tracker:
            # Check if any equipped item has speed_bonus
            total_speed_bonus = self._calculate_total_speed_bonus()
            if total_speed_bonus > 0:
                # Create new tracker with equipment bonus
                from components.speed_bonus_tracker import SpeedBonusTracker
                speed_tracker = SpeedBonusTracker(speed_bonus_ratio=0.0)  # Base 0, equipment will be added
                self.owner.speed_bonus_tracker = speed_tracker
                speed_tracker.owner = self.owner
                self.owner.components.add(ComponentType.SPEED_BONUS_TRACKER, speed_tracker)
                logger.debug(f"Created SpeedBonusTracker for {self.owner.name}")
        
        if speed_tracker:
            # Reset equipment bonus and recalculate
            old_ratio = speed_tracker.speed_bonus_ratio
            speed_tracker._equipment_ratio = 0.0
            speed_tracker._equipment_sources.clear()
            
            # Add bonuses from all equipped items
            for item in self._get_all_equipped_items():
                if hasattr(item, 'equippable') and item.equippable:
                    item_speed = getattr(item.equippable, 'speed_bonus', 0.0)
                    if item_speed > 0:
                        speed_tracker.add_equipment_bonus(item_speed, item.name)
            
            new_ratio = speed_tracker.speed_bonus_ratio
            
            # Log change message if significant
            if old_ratio != new_ratio and self.owner.name.lower() == "player":
                from message_builder import MessageBuilder as MB
                if new_ratio > old_ratio:
                    results.append({
                        "message": MB.success(f"You feel faster! (+{int((new_ratio - old_ratio) * 100)}% speed)")
                    })
                elif new_ratio < old_ratio:
                    results.append({
                        "message": MB.warning(f"You feel slower. (-{int((old_ratio - new_ratio) * 100)}% speed)")
                    })
    
    def _calculate_total_speed_bonus(self) -> float:
        """Calculate total speed bonus from all equipped items.
        
        Returns:
            float: Total speed bonus ratio from equipment
        """
        total = 0.0
        for item in self._get_all_equipped_items():
            if hasattr(item, 'equippable') and item.equippable:
                item_speed = getattr(item.equippable, 'speed_bonus', 0.0)
                total += item_speed
        return total
    
    def _get_all_equipped_items(self) -> list:
        """Get list of all currently equipped items.
        
        Returns:
            list: All equipped item entities
        """
        items = []
        for slot_attr in ['main_hand', 'off_hand', 'head', 'chest', 'feet', 'left_ring', 'right_ring']:
            item = getattr(self, slot_attr, None)
            if item:
                items.append(item)
        return items
