"""Tests for the Statistics component.

This module tests the statistics tracking functionality that records
player performance metrics throughout a game run.
"""

import pytest
from components.statistics import Statistics


class TestStatisticsComponent:
    """Test Statistics component functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.stats = Statistics()
    
    def test_statistics_initialization(self):
        """Test that statistics are initialized to zero."""
        assert self.stats.total_kills == 0
        assert self.stats.damage_dealt == 0
        assert self.stats.damage_taken == 0
        assert self.stats.healing_received == 0
        assert self.stats.attacks_made == 0
        assert self.stats.attacks_hit == 0
        assert self.stats.critical_hits == 0
        assert self.stats.fumbles == 0
        assert self.stats.deepest_level == 1
        assert self.stats.rooms_explored == 0
        assert self.stats.turns_taken == 0
        assert self.stats.gold_collected == 0
        assert len(self.stats.monsters_killed) == 0
    
    def test_record_kill(self):
        """Test recording monster kills."""
        self.stats.record_kill("orc")
        assert self.stats.total_kills == 1
        assert self.stats.monsters_killed["orc"] == 1
        
        self.stats.record_kill("orc")
        self.stats.record_kill("troll")
        assert self.stats.total_kills == 3
        assert self.stats.monsters_killed["orc"] == 2
        assert self.stats.monsters_killed["troll"] == 1
    
    def test_record_damage(self):
        """Test recording damage dealt and taken."""
        self.stats.record_damage_dealt(10)
        self.stats.record_damage_dealt(5)
        assert self.stats.damage_dealt == 15
        
        self.stats.record_damage_taken(8)
        self.stats.record_damage_taken(3)
        assert self.stats.damage_taken == 11
    
    def test_record_healing(self):
        """Test recording healing received."""
        self.stats.record_healing(20)
        self.stats.record_healing(15)
        assert self.stats.healing_received == 35
    
    def test_record_attack_hit(self):
        """Test recording successful attacks."""
        self.stats.record_attack(hit=True)
        assert self.stats.attacks_made == 1
        assert self.stats.attacks_hit == 1
        assert self.stats.critical_hits == 0
    
    def test_record_attack_critical(self):
        """Test recording critical hits."""
        self.stats.record_attack(hit=True, critical=True)
        assert self.stats.attacks_made == 1
        assert self.stats.attacks_hit == 1
        assert self.stats.critical_hits == 1
    
    def test_record_attack_miss(self):
        """Test recording missed attacks."""
        self.stats.record_attack(hit=False)
        assert self.stats.attacks_made == 1
        assert self.stats.attacks_hit == 0
    
    def test_record_attack_fumble(self):
        """Test recording fumbled attacks."""
        self.stats.record_attack(hit=False, fumble=True)
        assert self.stats.attacks_made == 1
        assert self.stats.attacks_hit == 0
        assert self.stats.fumbles == 1
    
    def test_record_spell_cast(self):
        """Test recording spell casts."""
        self.stats.record_spell_cast("lightning_scroll")
        self.stats.record_spell_cast("fireball_scroll")
        self.stats.record_spell_cast("lightning_scroll")
        # spells_cast is a dict
        assert self.stats.spells_cast["lightning_scroll"] == 2
        assert self.stats.spells_cast["fireball_scroll"] == 1
    
    def test_record_item_used(self):
        """Test recording item usage."""
        self.stats.record_item_use("healing_potion")
        self.stats.record_item_use("healing_potion")
        self.stats.record_item_use("invisibility_scroll")
        # items_used is a dict
        assert self.stats.items_used["healing_potion"] == 2
        assert self.stats.items_used["invisibility_scroll"] == 1
    
    def test_statistics_has_tracking_fields(self):
        """Test that statistics has all expected tracking fields."""
        assert hasattr(self.stats, 'gold_collected')
        assert hasattr(self.stats, 'deepest_level')
        assert hasattr(self.stats, 'rooms_explored')
        assert hasattr(self.stats, 'turns_taken')
        assert hasattr(self.stats, 'equipment_found')
        assert hasattr(self.stats, 'monsters_killed')
        assert hasattr(self.stats, 'items_used')
        assert hasattr(self.stats, 'spells_cast')
    
    def test_to_dict(self):
        """Test converting statistics to dictionary."""
        self.stats.record_kill("orc")
        self.stats.record_damage_dealt(10)
        self.stats.record_damage_taken(5)
        
        data = self.stats.to_dict()
        assert isinstance(data, dict)
        assert data["total_kills"] == 1
        assert data["damage_dealt"] == 10
        assert data["damage_taken"] == 5
        assert "orc" in data["monsters_killed"]
    
    def test_from_dict(self):
        """Test creating statistics from dictionary."""
        data = {
            "total_kills": 5,
            "monsters_killed": {"orc": 3, "troll": 2},
            "damage_dealt": 100,
            "damage_taken": 50,
            "healing_received": 30,
            "attacks_made": 20,
            "attacks_hit": 15,
            "critical_hits": 3,
            "fumbles": 2,
            "spells_cast": {"lightning_scroll": 3, "fireball_scroll": 2},
            "items_used": {"healing_potion": 5, "invisibility_scroll": 3},
            "gold_collected": 150,
            "deepest_level": 4,
            "rooms_explored": 12,
            "turns_taken": 200,
            "equipment_found": {"dagger": 2, "leather_armor": 1, "iron_sword": 3}
        }
        
        stats = Statistics.from_dict(data)
        assert stats.total_kills == 5
        assert stats.monsters_killed["orc"] == 3
        assert stats.damage_dealt == 100
        assert stats.deepest_level == 4
        assert stats.spells_cast["lightning_scroll"] == 3
        assert stats.items_used["healing_potion"] == 5
        assert stats.equipment_found["dagger"] == 2
    
    def test_get_summary(self):
        """Test generating summary structure."""
        self.stats.record_kill("orc")
        self.stats.record_kill("troll")
        self.stats.record_damage_dealt(50)
        self.stats.record_damage_taken(20)
        self.stats.record_attack(hit=True)
        self.stats.record_attack(hit=True)
        self.stats.record_attack(hit=False)
        
        summary = self.stats.get_summary()
        assert isinstance(summary, dict)
        assert 'combat' in summary
        assert 'exploration' in summary
        assert summary['combat']['total_kills'] == 2
        assert summary['combat']['damage_dealt'] == 50
        assert summary['combat']['damage_taken'] == 20
    
    def test_accuracy_calculation(self):
        """Test accuracy calculation."""
        self.stats.record_attack(hit=True)
        self.stats.record_attack(hit=True)
        self.stats.record_attack(hit=False)
        
        summary = self.stats.get_summary()
        assert abs(summary['combat']['accuracy'] - 66.67) < 0.1  # 2/3 = 66.67%


class TestStatisticsIntegration:
    """Test statistics integration with game components."""
    
    def test_statistics_owner_reference(self):
        """Test that statistics can reference their owner."""
        from entity import Entity
        
        stats = Statistics()
        player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
        player.statistics = stats
        stats.owner = player
        
        assert stats.owner == player
        assert player.statistics == stats

