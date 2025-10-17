"""Equipment management component.

This module defines the Equipment component which manages equipped items
and calculates total stat bonuses from all equipped gear.
"""

import logging
from typing import Optional, List, Dict, Any
from equipment_slots import EquipmentSlots

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
            results.append({"dequipped": equippable_entity})
        else:
            # Check for two-handed weapon conflicts BEFORE equipping
            two_handed_conflict = False
            
            # Trying to equip a two-handed weapon while holding a shield
            if (slot == EquipmentSlots.MAIN_HAND and 
                hasattr(equippable_entity.equippable, 'two_handed') and
                equippable_entity.equippable.two_handed is True and 
                self.off_hand is not None):
                # Auto-unequip the shield
                results.append({"dequipped": self.off_hand})
                self.off_hand = None
                logger.debug(f"Auto-unequipped off_hand to equip two-handed weapon: {equippable_entity.name}")
            
            # Trying to equip a shield while holding a two-handed weapon
            elif (slot == EquipmentSlots.OFF_HAND and 
                  self.main_hand is not None and
                  hasattr(self.main_hand.equippable, 'two_handed') and
                  self.main_hand.equippable.two_handed is True):
                # Auto-unequip the two-handed weapon
                results.append({"dequipped": self.main_hand})
                self.main_hand = None
                logger.debug(f"Auto-unequipped two-handed weapon to equip shield: {equippable_entity.name}")
            
            # Replace or equip
            if current_item:
                results.append({"dequipped": current_item})

            setattr(self, slot_attr, equippable_entity)
            
            # Auto-identify equipment when equipped (traditional roguelike behavior)
            if hasattr(equippable_entity, 'item') and equippable_entity.item:
                was_unidentified = equippable_entity.item.identify()
                if was_unidentified:
                    # Add identification message
                    from message_builder import MessageBuilder as MB
                    results.append({
                        "message": MB.success(f"You recognize this as {equippable_entity.name}!"),
                        "identified": True
                    })
            
            results.append({"equipped": equippable_entity})

        return results
