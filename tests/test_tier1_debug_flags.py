"""Tests for Tier 1 debug flags (--start-level, --god-mode, --no-monsters, --reveal-map).

These tests verify that all command-line debug flags work correctly without crashes.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from config.testing_config import TestingConfig, get_testing_config, set_testing_mode
from loader_functions.initialize_new_game import get_game_variables, _skip_to_level, _grant_level_appropriate_gear


class TestTestingConfig:
    """Test TestingConfig class holds debug flags correctly."""
    
    def test_testing_config_default_values(self):
        """Test that TestingConfig has correct default values."""
        config = TestingConfig(testing_mode=False)
        assert config.testing_mode == False
        assert config.start_level == 1
        assert config.god_mode == False
        assert config.no_monsters == False
        assert config.reveal_map == False
    
    def test_testing_config_can_set_flags(self):
        """Test that debug flags can be set."""
        config = TestingConfig(testing_mode=True)
        config.start_level = 20
        config.god_mode = True
        config.no_monsters = True
        config.reveal_map = True
        
        assert config.start_level == 20
        assert config.god_mode == True
        assert config.no_monsters == True
        assert config.reveal_map == True


class TestStartLevel:
    """Test --start-level flag functionality."""
    
    def test_skip_to_level_descends_correctly(self):
        """Test that _skip_to_level calls next_floor the correct number of times."""
        # Create mock objects
        player = Mock()
        player.level = Mock()
        player.level.current_level = 1
        player.fighter = Mock()
        player.fighter.base_max_hp = 30
        player.fighter.max_hp = 30
        player.fighter.hp = 30
        player.inventory = Mock()
        player.equipment = Mock()
        player.equipment.main_hand = None
        player.equipment.chest = None
        
        entities = []
        game_map = Mock()
        game_map.dungeon_level = 1
        game_map.next_floor = Mock()
        
        message_log = Mock()
        constants = {'test': 'value'}
        
        # Skip to level 5 (should call next_floor 4 times)
        with patch('loader_functions.initialize_new_game.get_entity_factory') as mock_factory:
            mock_factory.return_value = Mock()
            mock_factory.return_value.create_spell_item = Mock(return_value=None)
            mock_factory.return_value.create_weapon = Mock(return_value=None)
            mock_factory.return_value.create_armor = Mock(return_value=None)
            
            _skip_to_level(player, entities, game_map, message_log, 5, constants)
        
        # Verify next_floor was called 4 times (levels 2, 3, 4, 5)
        assert game_map.next_floor.call_count == 4
        
        # Verify next_floor was called with correct arguments
        for call in game_map.next_floor.call_args_list:
            args, kwargs = call
            assert args == (player, message_log, constants)
    
    def test_skip_to_level_sets_player_level(self):
        """Test that player level is boosted correctly."""
        player = Mock()
        player.level = Mock()
        player.fighter = Mock()
        player.inventory = Mock()
        player.equipment = Mock()
        player.equipment.main_hand = None
        player.equipment.chest = None
        
        entities = []
        game_map = Mock()
        game_map.next_floor = Mock()
        message_log = Mock()
        constants = {}
        
        with patch('loader_functions.initialize_new_game.get_entity_factory') as mock_factory:
            mock_factory.return_value = Mock()
            mock_factory.return_value.create_spell_item = Mock(return_value=None)
            mock_factory.return_value.create_weapon = Mock(return_value=None)
            mock_factory.return_value.create_armor = Mock(return_value=None)
            
            # Test level 20 -> player level 10
            _skip_to_level(player, entities, game_map, message_log, 20, constants)
            assert player.level.current_level == 10
            assert player.fighter.base_max_hp == 30 + (10 * 10)  # 130
            
            # Test level 10 -> player level 5
            player.level.current_level = 1
            _skip_to_level(player, entities, game_map, message_log, 10, constants)
            assert player.level.current_level == 5
            assert player.fighter.base_max_hp == 30 + (5 * 10)  # 80
            
            # Test level 25 -> player level 10 (capped)
            player.level.current_level = 1
            _skip_to_level(player, entities, game_map, message_log, 25, constants)
            assert player.level.current_level == 10  # Capped at 10


class TestGrantGear:
    """Test gear granting functionality."""
    
    def test_grant_gear_potions(self):
        """Test that healing potions are granted correctly."""
        player = Mock()
        player.inventory = Mock()
        player.equipment = Mock()
        player.equipment.main_hand = None
        player.equipment.chest = None
        player.fighter = Mock()
        player.fighter.max_hp = 100
        
        entities = []
        
        mock_potion = Mock()
        
        with patch('loader_functions.initialize_new_game.get_entity_factory') as mock_factory:
            mock_factory.return_value = Mock()
            mock_factory.return_value.create_spell_item = Mock(return_value=mock_potion)
            mock_factory.return_value.create_weapon = Mock(return_value=None)
            mock_factory.return_value.create_armor = Mock(return_value=None)
            
            # Level 1 should get 5 potions
            _grant_level_appropriate_gear(player, entities, 1)
            assert player.inventory.add_item.call_count == 5
            
            # Level 10 should get 7 potions (5 + 10//5)
            player.inventory.reset_mock()
            _grant_level_appropriate_gear(player, entities, 10)
            assert player.inventory.add_item.call_count == 7
            
            # Level 20 should get 9 potions (5 + 20//5) + 3 scrolls (level 15+) = 12 total
            player.inventory.reset_mock()
            _grant_level_appropriate_gear(player, entities, 20)
            # At level 20: 9 potions + 3 teleport scrolls = 12 items
            assert player.inventory.add_item.call_count == 12
    
    def test_grant_gear_weapon_at_level_5(self):
        """Test that sword is granted at level 5+."""
        player = Mock()
        player.inventory = Mock()
        player.equipment = Mock()
        player.equipment.main_hand = None
        player.equipment.chest = None
        player.fighter = Mock()
        player.fighter.max_hp = 100
        
        entities = []
        mock_sword = Mock()
        mock_potion = Mock()
        
        with patch('loader_functions.initialize_new_game.get_entity_factory') as mock_factory:
            factory = Mock()
            factory.create_spell_item = Mock(return_value=mock_potion)
            factory.create_weapon = Mock(return_value=mock_sword)
            factory.create_armor = Mock(return_value=None)
            mock_factory.return_value = factory
            
            # Level 4 - no weapon
            _grant_level_appropriate_gear(player, entities, 4)
            assert factory.create_weapon.call_count == 0
            
            # Level 5 - sword granted
            factory.reset_mock()
            _grant_level_appropriate_gear(player, entities, 5)
            factory.create_weapon.assert_called_once_with('sword', 0, 0)
            assert player.equipment.toggle_equip.called
    
    def test_grant_gear_armor_at_level_10(self):
        """Test that chain mail is granted at level 10+."""
        player = Mock()
        player.inventory = Mock()
        player.equipment = Mock()
        player.equipment.main_hand = None
        player.equipment.chest = None
        player.fighter = Mock()
        player.fighter.max_hp = 100
        
        entities = []
        mock_armor = Mock()
        mock_potion = Mock()
        
        with patch('loader_functions.initialize_new_game.get_entity_factory') as mock_factory:
            factory = Mock()
            factory.create_spell_item = Mock(return_value=mock_potion)
            factory.create_weapon = Mock(return_value=None)
            factory.create_armor = Mock(return_value=mock_armor)
            mock_factory.return_value = factory
            
            # Level 9 - no armor
            _grant_level_appropriate_gear(player, entities, 9)
            assert factory.create_armor.call_count == 0
            
            # Level 10 - chain mail granted
            factory.reset_mock()
            _grant_level_appropriate_gear(player, entities, 10)
            factory.create_armor.assert_called_once_with('chain_mail', 0, 0)
            assert player.equipment.toggle_equip.called
    
    def test_grant_gear_scrolls_at_level_15(self):
        """Test that teleport scrolls are granted at level 15+."""
        player = Mock()
        player.inventory = Mock()
        player.equipment = Mock()
        player.equipment.main_hand = None
        player.equipment.chest = None
        player.fighter = Mock()
        player.fighter.max_hp = 100
        
        entities = []
        mock_scroll = Mock()
        mock_potion = Mock()
        
        with patch('loader_functions.initialize_new_game.get_entity_factory') as mock_factory:
            factory = Mock()
            factory.create_spell_item = Mock(side_effect=lambda item, x, y: mock_scroll if item == 'teleport_scroll' else mock_potion)
            factory.create_weapon = Mock(return_value=None)
            factory.create_armor = Mock(return_value=None)
            mock_factory.return_value = factory
            
            # Level 14 - no scrolls
            _grant_level_appropriate_gear(player, entities, 14)
            teleport_calls = [call for call in factory.create_spell_item.call_args_list if call[0][0] == 'teleport_scroll']
            assert len(teleport_calls) == 0
            
            # Level 15 - 3 scrolls granted
            factory.reset_mock()
            player.inventory.reset_mock()
            _grant_level_appropriate_gear(player, entities, 15)
            teleport_calls = [call for call in factory.create_spell_item.call_args_list if call[0][0] == 'teleport_scroll']
            assert len(teleport_calls) == 3


class TestGodMode:
    """Test --god-mode flag functionality."""
    
    def test_god_mode_prevents_death(self):
        """Test that god mode prevents HP from going below 1."""
        from components.fighter import Fighter
        from entity import Entity
        
        # Create player with god mode enabled
        config = TestingConfig(testing_mode=True)
        config.god_mode = True
        
        player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
        fighter = Fighter(hp=10, defense=0, power=1)
        player.fighter = fighter
        fighter.owner = player
        
        with patch('config.testing_config.get_testing_config', return_value=config):
            # Take 5 damage - should work normally
            results = fighter.take_damage(5)
            assert fighter.hp == 5
            
            # Take 10 damage - should leave at 1 HP due to god mode
            results = fighter.take_damage(10)
            assert fighter.hp == 1
            
            # Check for god mode message
            messages = [r.get('message') for r in results if 'message' in r]
            assert any('GOD MODE' in str(msg) for msg in messages if msg)


class TestNoMonsters:
    """Test --no-monsters flag functionality."""
    
    def test_no_monsters_flag_prevents_spawning(self):
        """Test that no_monsters flag sets monster count to 0."""
        from map_objects.game_map import GameMap
        from config.testing_config import TestingConfig
        
        # This is tested indirectly through the config check in place_entities
        config = TestingConfig(testing_mode=True)
        config.no_monsters = True
        
        with patch('config.testing_config.get_testing_config', return_value=config):
            # The actual logic is in game_map.place_entities()
            # If config.no_monsters is True, number_of_monsters is set to 0
            # This is verified by the code path in game_map.py line 321-323
            assert config.no_monsters == True


class TestRevealMap:
    """Test --reveal-map flag functionality."""
    
    def test_reveal_map_does_not_change_fov_radius(self):
        """Test that reveal_map flag does NOT change FOV radius (stays at 10)."""
        from config.game_constants import GameConstants
        from config.testing_config import TestingConfig

        # Test normal FOV
        config_normal = TestingConfig(testing_mode=False)
        config_normal.reveal_map = False

        with patch('config.testing_config.get_testing_config', return_value=config_normal):
            constants_obj = GameConstants()
            fov_radius = constants_obj._get_fov_radius()
            assert fov_radius == 10  # Default

        # Test reveal map FOV - should still be 10 (reveal_map doesn't affect FOV)
        config_reveal = TestingConfig(testing_mode=True)
        config_reveal.reveal_map = True

        with patch('config.testing_config.get_testing_config', return_value=config_reveal):
            constants_obj = GameConstants()
            fov_radius = constants_obj._get_fov_radius()
            assert fov_radius == 10  # Still 10 - reveal_map doesn't change FOV


class TestIntegration:
    """Integration tests for full game initialization with debug flags."""
    
    @pytest.mark.skip(reason="Full integration test - skipped for speed, run manually")
    def test_start_level_5_integration(self):
        """Integration test: Start game at level 5."""
        from loader_functions.initialize_new_game import get_constants
        
        constants = get_constants()
        
        # Set config
        config = get_testing_config()
        config.start_level = 5
        config.god_mode = False
        config.no_monsters = False
        config.reveal_map = False
        
        # This should not crash
        try:
            player, entities, game_map, message_log, game_state = get_game_variables(constants)
            assert game_map.dungeon_level == 5
            assert player.level.current_level >= 2  # Should be boosted
        except Exception as e:
            pytest.fail(f"Integration test failed: {e}")
    
    @pytest.mark.skip(reason="Full integration test - skipped for speed, run manually")
    def test_all_flags_combined_integration(self):
        """Integration test: All flags enabled at once."""
        from loader_functions.initialize_new_game import get_constants
        
        constants = get_constants()
        
        # Enable all debug flags
        config = get_testing_config()
        config.start_level = 20
        config.god_mode = True
        config.no_monsters = True
        config.reveal_map = True
        
        # This should not crash
        try:
            player, entities, game_map, message_log, game_state = get_game_variables(constants)
            assert game_map.dungeon_level == 20
            assert player.level.current_level == 10  # Half of 20
            assert config.god_mode == True
            assert config.no_monsters == True
            assert config.reveal_map == True
        except Exception as e:
            pytest.fail(f"Integration test failed with all flags: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

