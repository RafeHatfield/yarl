from game_messages import Message


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

        Calculates damage based on attacker's power vs target's defense.
        Generates combat messages and applies damage to the target.

        Args:
            target (Entity): The target entity to attack

        Returns:
            list: List of result dictionaries with combat messages and effects
        """
        results = []

        damage = self.power - target.fighter.defense

        if damage > 0:
            results.append(
                {
                    "message": Message(
                        "{0} attacks {1} for {2} hit points.".format(
                            self.owner.name.capitalize(), target.name, str(damage)
                        ),
                        (255, 255, 255),
                    )
                }
            )
            results.extend(target.fighter.take_damage(damage))
        else:
            results.append(
                {
                    "message": Message(
                        "{0} attacks {1} but does no damage.".format(
                            self.owner.name.capitalize(), target.name
                        ),
                        (255, 255, 255),
                    )
                }
            )

        return results
