import logging
from game_messages import Message
from config.testing_config import is_testing_mode

# Set up combat debug logger
combat_logger = logging.getLogger('combat_debug')
combat_logger.setLevel(logging.DEBUG)


class Fighter:
    """Component that handles combat statistics and actions.

    This component manages health points, attack power, defense, and experience
    points for entities that can engage in combat. It also handles equipment
    bonuses that modify base stats.

    Attributes:
        base_max_hp (int): Base maximum health points
        hp (int): Current health points
        base_defense (int): Base defense value
        base_power (int): Base attack power
        xp (int): Experience points earned
        owner (Entity): The entity that owns this component
    """

    def __init__(self, hp, defense, power, xp=0):
        """Initialize a Fighter component.

        Args:
            hp (int): Maximum health points
            defense (int): Defense value
            power (int): Attack power
            xp (int, optional): Starting experience points. Defaults to 0.
        """
        self.base_max_hp = hp
        self.hp = hp
        self.base_defense = defense
        self.base_power = power
        self.xp = xp
        self.owner = None  # Will be set by Entity when component is registered

    @property
    def max_hp(self):
        """Get maximum HP including equipment bonuses.

        Returns:
            int: Maximum health points including equipment bonuses
        """
        if self.owner and self.owner.equipment:
            bonus = self.owner.equipment.max_hp_bonus
        else:
            bonus = 0

        return self.base_max_hp + bonus

    @property
    def power(self):
        """Get attack power including equipment bonuses.

        Returns:
            int: Attack power including equipment bonuses
        """
        if self.owner and self.owner.equipment:
            bonus = self.owner.equipment.power_bonus
        else:
            bonus = 0

        return self.base_power + bonus

    @property
    def defense(self):
        """Get defense value including equipment bonuses.

        Returns:
            int: Defense value including equipment bonuses
        """
        if self.owner and self.owner.equipment:
            bonus = self.owner.equipment.defense_bonus
        else:
            bonus = 0

        return self.base_defense + bonus

    def take_damage(self, amount):
        """Apply damage to this fighter.

        Reduces current HP by the damage amount. If HP drops to 0 or below,
        marks the fighter as dead and returns XP reward information.

        Args:
            amount (int): Amount of damage to apply

        Returns:
            list: List of result dictionaries, may include 'dead' and 'xp' keys
        """
        results = []

        self.hp -= amount

        if self.hp <= 0:
            results.append({"dead": self.owner, "xp": self.xp})
            # Note: HP can go negative for XP calculation purposes, but should be
            # displayed as 0 in UI. The UI layer should handle the display clamping.

        return results

    def heal(self, amount):
        """Restore health points to this fighter.

        Increases current HP by the heal amount, capped at maximum HP.

        Args:
            amount (int): Amount of health to restore
        """
        self.hp += amount

        if self.hp > self.max_hp:
            self.hp = self.max_hp

    def attack(self, target):
        """Perform an attack against a target entity.

        Calculates damage based on attacker's power vs target's defense,
        including variable damage from equipped weapons and variable defense from armor.

        Args:
            target (Entity): The target entity to attack

        Returns:
            list: List of result dictionaries with combat messages and effects
        """
        results = []

        # Calculate base damage from attacker's power
        base_damage = self.power
        
        # Add variable weapon damage if equipped
        weapon_damage = self._get_weapon_damage()
        total_attack = base_damage + weapon_damage
        
        # Get variable armor defense from target
        armor_defense = target.fighter._get_armor_defense()
        
        # Apply defense (including base defense, equipment defense_bonus, and variable armor)
        total_defense = target.fighter.defense + armor_defense
        final_damage = max(0, total_attack - total_defense)

        if final_damage > 0:
            # Create detailed combat message
            weapon_text = f" (+{weapon_damage} weapon)" if weapon_damage > 0 else ""
            armor_text = f" ({armor_defense} absorbed by armor)" if armor_defense > 0 else ""
            
            message_text = "{0} attacks {1} for {2} hit points{3}{4}.".format(
                self.owner.name.capitalize(), 
                target.name, 
                str(final_damage),
                weapon_text,
                armor_text
            )
            
            results.append({
                "message": Message(message_text, (255, 255, 255))
            })
            
            # Log detailed combat breakdown in testing mode
            if is_testing_mode():
                self._log_combat_debug(target, total_attack, weapon_damage, total_defense, armor_defense, final_damage)
            
            results.extend(target.fighter.take_damage(final_damage))
        else:
            # Attack was completely blocked
            if armor_defense > 0:
                results.append({
                    "message": Message(
                        "{0} attacks {1} but the attack is completely blocked by armor.".format(
                            self.owner.name.capitalize(), target.name
                        ),
                        (255, 255, 255),
                    )
                })
            else:
                results.append({
                    "message": Message(
                        "{0} attacks {1} but does no damage.".format(
                            self.owner.name.capitalize(), target.name
                        ),
                        (255, 255, 255),
                    )
                })
            
            # Log detailed combat breakdown for blocked attacks in testing mode
            if is_testing_mode():
                self._log_combat_debug(target, total_attack, weapon_damage, total_defense, armor_defense, final_damage)

        return results
    
    def _log_combat_debug(self, target, total_attack: int, weapon_damage: int, 
                         total_defense: int, armor_defense: int, final_damage: int) -> None:
        """Log detailed combat breakdown for debugging in testing mode.
        
        Args:
            target: Target entity being attacked
            total_attack: Total attack value (power + weapon damage)
            weapon_damage: Variable weapon damage rolled
            total_defense: Total defense value (defense + armor)
            armor_defense: Variable armor defense rolled
            final_damage: Final damage after calculations
        """
        # Get weapon and armor range info for display
        weapon_range = ""
        if (hasattr(self.owner, 'equipment') and self.owner.equipment and
            self.owner.equipment.main_hand and self.owner.equipment.main_hand.equippable):
            equip = self.owner.equipment.main_hand.equippable
            if equip.damage_min > 0 and equip.damage_max > 0:
                weapon_range = f" ({equip.damage_min}-{equip.damage_max} dmg)"
        
        armor_range = ""
        if (hasattr(target, 'equipment') and target.equipment and
            target.equipment.off_hand and target.equipment.off_hand.equippable):
            equip = target.equipment.off_hand.equippable
            if equip.defense_min > 0 and equip.defense_max > 0:
                armor_range = f" ({equip.defense_min}-{equip.defense_max} def)"
        
        # Build and log debug information
        attacker_name = self.owner.name.capitalize()
        target_name = target.name
        
        debug_text = (f"{attacker_name} [power:{self.base_power}+{self.power-self.base_power}]{weapon_range} attacks for {total_attack} "
                     f"({self.power} power + {weapon_damage} rolled), "
                     f"{target_name} [def:{target.fighter.base_defense}+{target.fighter.defense-target.fighter.base_defense}]{armor_range} blocks {total_defense} "
                     f"({target.fighter.defense} defense + {armor_defense} rolled) "
                     f"= {final_damage} total damage")
        
        combat_logger.debug(debug_text)
    
    def _get_weapon_damage(self) -> int:
        """Get variable damage from equipped weapon.
        
        Returns:
            int: Random damage from equipped weapon, or 0 if no weapon
        """
        if (hasattr(self.owner, 'equipment') and self.owner.equipment and
            self.owner.equipment.main_hand and 
            self.owner.equipment.main_hand.equippable):
            return self.owner.equipment.main_hand.equippable.roll_damage()
        return 0
    
    def _get_armor_defense(self) -> int:
        """Get variable defense from equipped armor.
        
        Returns:
            int: Random defense from equipped armor, or 0 if no armor
        """
        try:
            if (hasattr(self.owner, 'equipment') and self.owner.equipment and
                hasattr(self.owner.equipment, 'off_hand') and self.owner.equipment.off_hand and 
                hasattr(self.owner.equipment.off_hand, 'equippable') and
                self.owner.equipment.off_hand.equippable):
                return self.owner.equipment.off_hand.equippable.roll_defense()
        except (AttributeError, TypeError):
            pass
        return 0
