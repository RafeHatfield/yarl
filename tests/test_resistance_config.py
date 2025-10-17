"""Tests for resistance system configuration integration.

This test ensures that the resistance system properly integrates with:
- Entity YAML configuration
- EntityStats dataclass
- Fighter component creation
- Entity factory monster creation
"""

import pytest
from config.entity_registry import EntityStats, EntityRegistry
from config.entity_factory import EntityFactory
from components.fighter import Fighter, ResistanceType


class TestResistanceConfiguration:
    """Test resistance system configuration and integration."""
    
    def test_entity_stats_accepts_resistances(self):
        """EntityStats should accept resistances parameter."""
        resistances = {
            'fire': 100,
            'cold': 50,
            'poison': 30
        }
        
        stats = EntityStats(
            hp=100,
            power=20,
            defense=15,
            xp=500,
            strength=18,
            dexterity=14,
            constitution=16,
            resistances=resistances
        )
        
        assert stats.resistances == resistances
        assert stats.resistances['fire'] == 100
        assert stats.resistances['cold'] == 50
        assert stats.resistances['poison'] == 30
    
    def test_entity_stats_resistances_optional(self):
        """EntityStats should work without resistances (backward compatible)."""
        stats = EntityStats(
            hp=50,
            power=10,
            defense=10,
            xp=100
        )
        
        assert stats.resistances is None
    
    def test_fighter_accepts_resistances_dict(self):
        """Fighter component should accept resistances as dict."""
        resistances = {
            'fire': 75,
            'cold': 50
        }
        
        fighter = Fighter(
            hp=100,
            defense=15,
            power=20,
            resistances=resistances
        )
        
        assert fighter.base_resistances == resistances
        assert fighter.base_resistances['fire'] == 75
        assert fighter.base_resistances['cold'] == 50
    
    def test_fighter_accepts_no_resistances(self):
        """Fighter should work without resistances (backward compatible)."""
        fighter = Fighter(
            hp=50,
            defense=10,
            power=10
        )
        
        assert fighter.base_resistances == {}
    
    def test_dragon_lord_config_loads(self):
        """Dragon Lord configuration should load with resistances from YAML."""
        registry = EntityRegistry()
        
        # Create minimal test config for dragon lord
        test_config = {
            'monsters': {
                'dragon_lord': {
                    'name': 'Dragon Lord',
                    'char': 'D',
                    'color': [255, 0, 0],
                    'ai_type': 'boss',
                    'is_boss': True,
                    'boss_name': 'Dragon Lord',
                    'stats': {
                        'hp': 500,
                        'defense': 25,
                        'power': 30,
                        'xp': 5000,
                        'strength': 22,
                        'dexterity': 16,
                        'constitution': 20,
                        'damage_min': 15,
                        'damage_max': 30,
                        'resistances': {
                            'fire': 100,
                            'cold': 50,
                            'poison': 30
                        }
                    }
                }
            }
        }
        
        # Process the config
        registry._process_config_data(test_config)
        
        # Get the monster definition
        dragon_lord = registry.get_monster('dragon_lord')
        
        assert dragon_lord is not None
        assert dragon_lord.stats.resistances is not None
        assert dragon_lord.stats.resistances['fire'] == 100
        assert dragon_lord.stats.resistances['cold'] == 50
        assert dragon_lord.stats.resistances['poison'] == 30
    
    def test_demon_king_config_loads(self):
        """Demon King configuration should load with resistances from YAML."""
        registry = EntityRegistry()
        
        # Create minimal test config for demon king
        test_config = {
            'monsters': {
                'demon_king': {
                    'name': 'Demon King',
                    'char': 'K',
                    'color': [128, 0, 128],
                    'ai_type': 'boss',
                    'is_boss': True,
                    'boss_name': 'Demon King',
                    'stats': {
                        'hp': 600,
                        'defense': 28,
                        'power': 35,
                        'xp': 6000,
                        'strength': 24,
                        'dexterity': 14,
                        'constitution': 22,
                        'damage_min': 18,
                        'damage_max': 35,
                        'resistances': {
                            'fire': 75,
                            'poison': 100,
                            'lightning': 50
                        }
                    }
                }
            }
        }
        
        # Process the config
        registry._process_config_data(test_config)
        
        # Get the monster definition
        demon_king = registry.get_monster('demon_king')
        
        assert demon_king is not None
        assert demon_king.stats.resistances is not None
        assert demon_king.stats.resistances['fire'] == 75
        assert demon_king.stats.resistances['poison'] == 100
        assert demon_king.stats.resistances['lightning'] == 50
    
    def test_entity_factory_creates_monster_with_resistances(self):
        """Entity factory should create monsters with resistances."""
        registry = EntityRegistry()
        
        # Create test config
        test_config = {
            'monsters': {
                'fire_dragon': {
                    'name': 'Fire Dragon',
                    'char': 'D',
                    'color': [255, 100, 0],
                    'ai_type': 'basic',
                    'stats': {
                        'hp': 200,
                        'defense': 20,
                        'power': 25,
                        'xp': 1000,
                        'strength': 20,
                        'dexterity': 12,
                        'constitution': 18,
                        'damage_min': 10,
                        'damage_max': 20,
                        'resistances': {
                            'fire': 100,  # Immune to fire
                            'cold': 0     # Vulnerable to cold
                        }
                    }
                }
            }
        }
        
        registry._process_config_data(test_config)
        factory = EntityFactory(registry)
        
        # Create the monster
        dragon = factory.create_monster('fire_dragon', 5, 5)
        
        assert dragon is not None
        assert dragon.fighter is not None
        assert dragon.fighter.base_resistances is not None
        assert dragon.fighter.base_resistances['fire'] == 100
        assert dragon.fighter.get_resistance(ResistanceType.FIRE) == 100
    
    def test_monster_without_resistances_works(self):
        """Monsters without resistances should still work (backward compatible)."""
        registry = EntityRegistry()
        
        # Create test config without resistances
        test_config = {
            'monsters': {
                'orc': {
                    'name': 'Orc',
                    'char': 'o',
                    'color': [0, 127, 0],
                    'ai_type': 'basic',
                    'stats': {
                        'hp': 30,
                        'defense': 5,
                        'power': 8,
                        'xp': 50,
                        'damage_min': 3,
                        'damage_max': 8
                    }
                }
            }
        }
        
        registry._process_config_data(test_config)
        factory = EntityFactory(registry)
        
        # Create the monster
        orc = factory.create_monster('orc', 5, 5)
        
        assert orc is not None
        assert orc.fighter is not None
        assert orc.fighter.base_resistances == {}
        assert orc.fighter.get_resistance(ResistanceType.FIRE) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

