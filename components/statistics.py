"""Statistics tracking component for player performance and achievements.

This component tracks comprehensive gameplay statistics including combat metrics,
exploration data, and run progression for display on death screen and achievements.
"""

from typing import Dict, Optional
from collections import defaultdict


class Statistics:
    """Component that tracks player statistics throughout a run.
    
    Attributes:
        owner: The entity that owns this component (typically the player)
        monsters_killed: Dictionary mapping monster type to kill count
        total_kills: Total monsters killed this run
        attacks_made: Total attacks attempted (hits + misses)
        attacks_hit: Total attacks that connected
        attacks_missed: Total attacks that missed
        critical_hits: Total critical hits (nat 20s)
        fumbles: Total fumbles (nat 1s)
        damage_dealt: Total damage inflicted on enemies
        damage_taken: Total damage received from enemies
        healing_received: Total HP restored (potions, etc.)
        items_used: Dictionary mapping item type to usage count
        spells_cast: Dictionary mapping spell type to cast count
        deepest_level: Furthest dungeon level reached
        rooms_explored: Total rooms entered
        turns_taken: Total turns elapsed
        gold_collected: Total gold collected (future feature)
        equipment_found: Dictionary tracking equipment discoveries
    """
    
    def __init__(self, owner=None):
        """Initialize statistics component with zero values.
        
        Args:
            owner: The entity that owns this component
        """
        self.owner = owner
        
        # Combat statistics
        self.monsters_killed: Dict[str, int] = defaultdict(int)
        self.total_kills: int = 0
        self.attacks_made: int = 0
        self.attacks_hit: int = 0
        self.attacks_missed: int = 0
        self.critical_hits: int = 0
        self.fumbles: int = 0
        self.damage_dealt: int = 0
        self.damage_taken: int = 0
        
        # Consumable usage
        self.healing_received: int = 0
        self.items_used: Dict[str, int] = defaultdict(int)
        self.spells_cast: Dict[str, int] = defaultdict(int)
        
        # Exploration statistics
        self.deepest_level: int = 1
        self.rooms_explored: int = 0
        self.turns_taken: int = 0
        
        # Loot statistics
        self.gold_collected: int = 0
        self.equipment_found: Dict[str, int] = defaultdict(int)
    
    def record_kill(self, monster_name: str) -> None:
        """Record a monster kill.
        
        Args:
            monster_name: Name of the monster type killed (e.g., "orc", "troll")
        """
        self.monsters_killed[monster_name] += 1
        self.total_kills += 1
    
    def record_attack(self, hit: bool, critical: bool = False, fumble: bool = False) -> None:
        """Record an attack attempt.
        
        Args:
            hit: Whether the attack connected
            critical: Whether it was a critical hit (nat 20)
            fumble: Whether it was a fumble (nat 1)
        """
        self.attacks_made += 1
        if hit:
            self.attacks_hit += 1
            if critical:
                self.critical_hits += 1
        else:
            self.attacks_missed += 1
            if fumble:
                self.fumbles += 1
    
    def record_damage_dealt(self, amount: int) -> None:
        """Record damage dealt to an enemy.
        
        Args:
            amount: Amount of damage inflicted
        """
        self.damage_dealt += amount
    
    def record_damage_taken(self, amount: int) -> None:
        """Record damage taken from an enemy.
        
        Args:
            amount: Amount of damage received
        """
        self.damage_taken += amount
    
    def record_healing(self, amount: int) -> None:
        """Record healing received.
        
        Args:
            amount: Amount of HP restored
        """
        self.healing_received += amount
    
    def record_item_use(self, item_name: str) -> None:
        """Record item usage.
        
        Args:
            item_name: Name of the item used (e.g., "healing_potion")
        """
        self.items_used[item_name] += 1
    
    def record_spell_cast(self, spell_name: str) -> None:
        """Record spell casting.
        
        Args:
            spell_name: Name of the spell cast (e.g., "fireball_scroll")
        """
        self.spells_cast[spell_name] += 1
    
    def record_level_reached(self, level: int) -> None:
        """Record dungeon level reached.
        
        Args:
            level: Dungeon level number
        """
        if level > self.deepest_level:
            self.deepest_level = level
    
    def record_room_entered(self) -> None:
        """Record entering a new room."""
        self.rooms_explored += 1
    
    def record_turn(self) -> None:
        """Record a turn passing."""
        self.turns_taken += 1
    
    def record_equipment_found(self, equipment_name: str) -> None:
        """Record finding equipment.
        
        Args:
            equipment_name: Name of the equipment found
        """
        self.equipment_found[equipment_name] += 1
    
    def record_gold(self, amount: int) -> None:
        """Record gold collection.
        
        Args:
            amount: Amount of gold collected
        """
        self.gold_collected += amount
    
    def get_accuracy(self) -> float:
        """Calculate hit accuracy percentage.
        
        Returns:
            Hit percentage (0-100), or 0 if no attacks made
        """
        if self.attacks_made == 0:
            return 0.0
        return (self.attacks_hit / self.attacks_made) * 100
    
    def get_favorite_weapon(self) -> Optional[str]:
        """Get the most used weapon type.
        
        Returns:
            Name of most used weapon, or None if no weapons used
        """
        if not self.equipment_found:
            return None
        return max(self.equipment_found.items(), key=lambda x: x[1])[0]
    
    def get_kill_death_ratio(self) -> float:
        """Calculate kills per death (for future multi-run stats).
        
        Returns:
            Kills per death ratio (currently just total kills)
        """
        return float(self.total_kills)
    
    def get_summary(self) -> Dict[str, any]:
        """Get a comprehensive statistics summary.
        
        Returns:
            Dictionary containing all statistics for display or serialization
        """
        return {
            'combat': {
                'total_kills': self.total_kills,
                'monsters_killed': dict(self.monsters_killed),
                'attacks_made': self.attacks_made,
                'attacks_hit': self.attacks_hit,
                'attacks_missed': self.attacks_missed,
                'accuracy': self.get_accuracy(),
                'critical_hits': self.critical_hits,
                'fumbles': self.fumbles,
                'damage_dealt': self.damage_dealt,
                'damage_taken': self.damage_taken,
            },
            'consumables': {
                'healing_received': self.healing_received,
                'items_used': dict(self.items_used),
                'spells_cast': dict(self.spells_cast),
            },
            'exploration': {
                'deepest_level': self.deepest_level,
                'rooms_explored': self.rooms_explored,
                'turns_taken': self.turns_taken,
            },
            'loot': {
                'gold_collected': self.gold_collected,
                'equipment_found': dict(self.equipment_found),
            }
        }
    
    def to_dict(self) -> Dict:
        """Serialize statistics to dictionary for saving.
        
        Returns:
            Dictionary representation of all statistics
        """
        return {
            'monsters_killed': dict(self.monsters_killed),
            'total_kills': self.total_kills,
            'attacks_made': self.attacks_made,
            'attacks_hit': self.attacks_hit,
            'attacks_missed': self.attacks_missed,
            'critical_hits': self.critical_hits,
            'fumbles': self.fumbles,
            'damage_dealt': self.damage_dealt,
            'damage_taken': self.damage_taken,
            'healing_received': self.healing_received,
            'items_used': dict(self.items_used),
            'spells_cast': dict(self.spells_cast),
            'deepest_level': self.deepest_level,
            'rooms_explored': self.rooms_explored,
            'turns_taken': self.turns_taken,
            'gold_collected': self.gold_collected,
            'equipment_found': dict(self.equipment_found),
        }
    
    @staticmethod
    def from_dict(data: Dict, owner=None) -> 'Statistics':
        """Deserialize statistics from dictionary.
        
        Args:
            data: Dictionary containing statistics data
            owner: The entity that owns this component
            
        Returns:
            Statistics component with restored data
        """
        stats = Statistics(owner)
        stats.monsters_killed = defaultdict(int, data.get('monsters_killed', {}))
        stats.total_kills = data.get('total_kills', 0)
        stats.attacks_made = data.get('attacks_made', 0)
        stats.attacks_hit = data.get('attacks_hit', 0)
        stats.attacks_missed = data.get('attacks_missed', 0)
        stats.critical_hits = data.get('critical_hits', 0)
        stats.fumbles = data.get('fumbles', 0)
        stats.damage_dealt = data.get('damage_dealt', 0)
        stats.damage_taken = data.get('damage_taken', 0)
        stats.healing_received = data.get('healing_received', 0)
        stats.items_used = defaultdict(int, data.get('items_used', {}))
        stats.spells_cast = defaultdict(int, data.get('spells_cast', {}))
        stats.deepest_level = data.get('deepest_level', 1)
        stats.rooms_explored = data.get('rooms_explored', 0)
        stats.turns_taken = data.get('turns_taken', 0)
        stats.gold_collected = data.get('gold_collected', 0)
        stats.equipment_found = defaultdict(int, data.get('equipment_found', {}))
        return stats

