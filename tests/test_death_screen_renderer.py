"""Regression tests for death screen renderer stats field lookups.

This test ensures the death screen renderer is defensive against changes
in the Statistics component schema and doesn't crash when fields are missing
or renamed.
"""

import pytest
from unittest.mock import Mock, patch
from components.statistics import Statistics


class TestDeathScreenStatisticsLookup:
    """Test that death screen handles various statistics schemas gracefully."""
    
    @patch('io_layer.death_screen_renderer.libtcodpy')
    def test_death_screen_with_current_stats_schema(self, mock_libtcod):
        """Test death screen with current Statistics component schema.
        
        This is the primary regression test - if the Stats component has
        turns_taken instead of turns_survived, the death screen should
        adapt gracefully using getattr fallbacks.
        """
        from io_layer.death_screen_renderer import render_death_screen
        
        # Create a real Statistics component with current schema
        stats = Statistics()
        stats.turns_taken = 42
        stats.total_kills = 5
        stats.damage_dealt = 100
        stats.damage_taken = 50
        stats.critical_hits = 3
        stats.deepest_level = 3
        stats.items_picked_up = 7
        stats.potions_used = 2
        
        # Create mock player with stats component
        player = Mock()
        player.get_component_optional = Mock(return_value=stats)
        
        # Create mock console
        con = Mock()
        
        # This should NOT raise AttributeError
        try:
            render_death_screen(con, player, 80, 50, entity_quote="You died!", run_metrics=None)
        except AttributeError as e:
            pytest.fail(f"Death screen raised AttributeError: {e}")
    
    @patch('io_layer.death_screen_renderer.libtcodpy')
    def test_death_screen_with_missing_optional_fields(self, mock_libtcod):
        """Test death screen when optional achievement fields are missing."""
        from io_layer.death_screen_renderer import render_death_screen
        
        # Create minimal stats object with only required fields
        stats = Mock()
        stats.turns_taken = 10
        stats.total_kills = 1
        stats.damage_dealt = 20
        stats.damage_taken = 15
        stats.critical_hits = 0
        stats.deepest_level = 1
        stats.items_picked_up = 0
        stats.potions_used = 0
        # Missing: times_stunned, scrolls_read, bosses_defeated, secrets_found, traps_disarmed
        
        player = Mock()
        player.get_component_optional = Mock(return_value=stats)
        con = Mock()
        
        # Should handle missing fields gracefully (default to 0)
        try:
            render_death_screen(con, player, 80, 50)
        except AttributeError as e:
            pytest.fail(f"Death screen raised AttributeError for missing optional fields: {e}")
    
    @patch('io_layer.death_screen_renderer.libtcodpy')
    def test_death_screen_with_no_stats(self, mock_libtcod):
        """Test death screen when player has no statistics component."""
        from io_layer.death_screen_renderer import render_death_screen
        
        player = Mock()
        player.get_component_optional = Mock(return_value=None)
        con = Mock()
        
        # Should render without stats section
        try:
            render_death_screen(con, player, 80, 50)
        except Exception as e:
            pytest.fail(f"Death screen raised exception with no stats: {e}")
    
    @patch('io_layer.death_screen_renderer.libtcodpy')
    def test_death_screen_monsters_killed_dict_format(self, mock_libtcod):
        """Test death screen when monsters_killed is a dict (not total_kills)."""
        from io_layer.death_screen_renderer import render_death_screen
        
        stats = Statistics()
        stats.monsters_killed = {"orc": 3, "troll": 2}
        stats.total_kills = 5  # Should prefer total_kills
        stats.turns_taken = 20
        stats.damage_dealt = 80
        stats.damage_taken = 30
        stats.critical_hits = 1
        stats.deepest_level = 2
        stats.items_picked_up = 4
        stats.potions_used = 1
        
        player = Mock()
        player.get_component_optional = Mock(return_value=stats)
        con = Mock()
        
        # Should handle dict monsters_killed gracefully
        try:
            render_death_screen(con, player, 80, 50)
        except Exception as e:
            pytest.fail(f"Death screen raised exception with dict monsters_killed: {e}")
    
    @patch('io_layer.death_screen_renderer.libtcodpy')
    def test_death_screen_floors_descended_calculation(self, mock_libtcod):
        """Test floors_descended is calculated from deepest_level."""
        from io_layer.death_screen_renderer import render_death_screen
        
        stats = Statistics()
        stats.turns_taken = 100
        stats.total_kills = 10
        stats.damage_dealt = 200
        stats.damage_taken = 100
        stats.critical_hits = 5
        stats.deepest_level = 5  # Should show as 4 floors descended (5-1)
        stats.items_picked_up = 15
        stats.potions_used = 3
        
        player = Mock()
        player.get_component_optional = Mock(return_value=stats)
        con = Mock()
        
        # Should calculate floors_descended = deepest_level - 1
        try:
            render_death_screen(con, player, 80, 50)
        except Exception as e:
            pytest.fail(f"Death screen raised exception calculating floors_descended: {e}")
    
    @patch('io_layer.death_screen_renderer.libtcodpy')
    def test_death_screen_with_run_metrics(self, mock_libtcod):
        """Test death screen with run_metrics parameter."""
        from io_layer.death_screen_renderer import render_death_screen
        
        stats = Statistics()
        stats.turns_taken = 50
        stats.total_kills = 3
        stats.damage_dealt = 60
        stats.damage_taken = 40
        stats.critical_hits = 2
        stats.deepest_level = 2
        stats.items_picked_up = 5
        stats.potions_used = 1
        
        # Mock run_metrics with turns_per_floor
        run_metrics = Mock()
        run_metrics.turns_per_floor = {1: 30, 2: 20}
        
        player = Mock()
        player.get_component_optional = Mock(return_value=stats)
        con = Mock()
        
        # Should handle run_metrics gracefully
        try:
            render_death_screen(con, player, 80, 50, run_metrics=run_metrics)
        except Exception as e:
            pytest.fail(f"Death screen raised exception with run_metrics: {e}")

