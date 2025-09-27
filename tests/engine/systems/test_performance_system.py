"""Tests for the PerformanceSystem."""

import pytest
from unittest.mock import Mock, patch

from engine.systems.performance_system import PerformanceSystem


class TestPerformanceSystemInitialization:
    """Test PerformanceSystem initialization."""

    def test_performance_system_initialization(self):
        """Test PerformanceSystem initialization with default values."""
        perf_system = PerformanceSystem()

        assert perf_system.name == "performance"
        assert perf_system.priority == 5  # Very early priority
        assert len(perf_system.dirty_rectangles) == 0
        assert perf_system.full_redraw_needed is True
        assert len(perf_system.spatial_index) == 0
        assert perf_system.spatial_grid_size == 8
        assert len(perf_system.fov_cache) == 0
        assert len(perf_system.visible_entities) == 0
        assert perf_system.optimization_enabled is True
        assert perf_system.debug_mode is False

    def test_performance_system_custom_priority(self):
        """Test PerformanceSystem initialization with custom priority."""
        perf_system = PerformanceSystem(priority=3)

        assert perf_system.priority == 3


class TestPerformanceSystemMethods:
    """Test PerformanceSystem methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.perf_system = PerformanceSystem()
        self.mock_engine = Mock()
        self.mock_state_manager = Mock()
        self.mock_engine.state_manager = self.mock_state_manager
        self.perf_system.initialize(self.mock_engine)

    def test_mark_dirty_rectangle(self):
        """Test marking dirty rectangles."""
        self.perf_system.mark_dirty_rectangle(10, 20, 5, 5)

        assert (10, 20, 5, 5) in self.perf_system.dirty_rectangles

    def test_mark_entity_dirty(self):
        """Test marking entity areas as dirty."""
        entity = Mock()
        entity.x = 15
        entity.y = 25

        self.perf_system.mark_entity_dirty(entity)

        assert (15, 25, 1, 1) in self.perf_system.dirty_rectangles

    def test_mark_entity_dirty_with_old_position(self):
        """Test marking entity dirty with old position."""
        entity = Mock()
        entity.x = 15
        entity.y = 25

        self.perf_system.mark_entity_dirty(entity, old_x=10, old_y=20)

        assert (15, 25, 1, 1) in self.perf_system.dirty_rectangles
        assert (10, 20, 1, 1) in self.perf_system.dirty_rectangles

    def test_request_full_redraw(self):
        """Test requesting full redraw."""
        # Add some dirty rectangles first
        self.perf_system.mark_dirty_rectangle(1, 1, 1, 1)

        self.perf_system.request_full_redraw()

        assert self.perf_system.full_redraw_needed is True
        assert len(self.perf_system.dirty_rectangles) == 0

    def test_clear_dirty_rectangles(self):
        """Test clearing dirty rectangles."""
        self.perf_system.mark_dirty_rectangle(1, 1, 1, 1)
        self.perf_system.full_redraw_needed = True

        self.perf_system.clear_dirty_rectangles()

        assert len(self.perf_system.dirty_rectangles) == 0
        assert self.perf_system.full_redraw_needed is False

    def test_cache_fov_result(self):
        """Test caching FOV results."""
        mock_fov_map = Mock()

        self.perf_system.cache_fov_result(10, 20, 5, mock_fov_map)

        assert (10, 20, 5) in self.perf_system.fov_cache
        assert self.perf_system.fov_cache[(10, 20, 5)] is mock_fov_map

    def test_get_cached_fov(self):
        """Test getting cached FOV results."""
        mock_fov_map = Mock()
        self.perf_system.cache_fov_result(10, 20, 5, mock_fov_map)

        result = self.perf_system.get_cached_fov(10, 20, 5)

        assert result is mock_fov_map
        assert self.perf_system.render_stats["fov_cache_hits"] == 1

    def test_get_cached_fov_miss(self):
        """Test getting cached FOV when not cached."""
        result = self.perf_system.get_cached_fov(10, 20, 5)

        assert result is None
        assert self.perf_system.render_stats["fov_cache_hits"] == 0

    def test_should_recompute_fov_position_changed(self):
        """Test FOV recomputation when position changes."""
        # First call should always return True
        result = self.perf_system.should_recompute_fov(10, 20, 5)
        assert result is True

        # Same position should return False
        result = self.perf_system.should_recompute_fov(10, 20, 5)
        assert result is False

        # Different position should return True
        result = self.perf_system.should_recompute_fov(15, 25, 5)
        assert result is True

    def test_should_recompute_fov_radius_changed(self):
        """Test FOV recomputation when radius changes."""
        self.perf_system.should_recompute_fov(10, 20, 5)  # Initialize

        # Different radius should return True
        result = self.perf_system.should_recompute_fov(10, 20, 8)
        assert result is True

    def test_enable_disable_optimizations(self):
        """Test enabling and disabling optimizations."""
        assert self.perf_system.optimization_enabled is True

        self.perf_system.disable_optimizations()
        assert self.perf_system.optimization_enabled is False

        self.perf_system.enable_optimizations()
        assert self.perf_system.optimization_enabled is True

    def test_set_debug_mode(self):
        """Test setting debug mode."""
        assert self.perf_system.debug_mode is False

        self.perf_system.set_debug_mode(True)
        assert self.perf_system.debug_mode is True

        self.perf_system.set_debug_mode(False)
        assert self.perf_system.debug_mode is False

    def test_get_performance_stats(self):
        """Test getting performance statistics."""
        stats = self.perf_system.get_performance_stats()

        assert "frames_rendered" in stats
        assert "dirty_rectangles_used" in stats
        assert "entities_culled" in stats
        assert "fov_cache_hits" in stats
        assert "spatial_lookups" in stats
        assert isinstance(stats, dict)

    def test_reset_performance_stats(self):
        """Test resetting performance statistics."""
        # Modify stats first
        self.perf_system.render_stats["frames_rendered"] = 10
        self.perf_system.render_stats["fov_cache_hits"] = 5

        self.perf_system.reset_performance_stats()

        assert self.perf_system.render_stats["frames_rendered"] == 0
        assert self.perf_system.render_stats["fov_cache_hits"] == 0

    def test_cleanup(self):
        """Test cleanup method."""
        # Set up some state
        self.perf_system.mark_dirty_rectangle(1, 1, 1, 1)
        self.perf_system.cache_fov_result(1, 1, 1, Mock())
        entity = Mock()
        entity.x = 1
        entity.y = 1
        self.perf_system.visible_entities.add(entity)

        self.perf_system.cleanup()

        assert len(self.perf_system.dirty_rectangles) == 0
        assert len(self.perf_system.spatial_index) == 0
        assert len(self.perf_system.fov_cache) == 0
        assert len(self.perf_system.visible_entities) == 0


class TestPerformanceSystemSpatialIndex:
    """Test spatial indexing functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.perf_system = PerformanceSystem()

        # Create mock entities
        self.entity1 = Mock()
        self.entity1.x = 5
        self.entity1.y = 5

        self.entity2 = Mock()
        self.entity2.x = 15
        self.entity2.y = 15

        self.entity3 = Mock()
        self.entity3.x = 7
        self.entity3.y = 6

    def test_update_spatial_index(self):
        """Test updating the spatial index."""
        entities = [self.entity1, self.entity2, self.entity3]

        self.perf_system._update_spatial_index(entities)

        # Check that entities are in correct grid cells
        # Grid size is 8, so:
        # entity1 (5,5) -> grid (0,0)
        # entity2 (15,15) -> grid (1,1)
        # entity3 (7,6) -> grid (0,0)

        assert self.entity1 in self.perf_system.spatial_index[(0, 0)]
        assert self.entity3 in self.perf_system.spatial_index[(0, 0)]
        assert self.entity2 in self.perf_system.spatial_index[(1, 1)]

    def test_get_entities_at_position(self):
        """Test getting entities at a specific position."""
        entities = [self.entity1, self.entity2, self.entity3]
        self.perf_system._update_spatial_index(entities)

        # Get entities at position (5, 5)
        result = self.perf_system.get_entities_at_position(5, 5)

        assert self.entity1 in result
        assert self.entity2 not in result

    def test_get_entities_in_area(self):
        """Test getting entities in a rectangular area."""
        entities = [self.entity1, self.entity2, self.entity3]
        self.perf_system._update_spatial_index(entities)

        # Get entities in area covering both entity1 and entity3
        result = self.perf_system.get_entities_in_area(4, 4, 5, 5)

        assert self.entity1 in result
        assert self.entity3 in result
        assert self.entity2 not in result

    def test_spatial_index_with_entities_without_position(self):
        """Test spatial index with entities that don't have x/y attributes."""
        entity_no_pos = Mock(spec=[])  # No x, y attributes
        entities = [self.entity1, entity_no_pos]

        # Should not raise an exception
        self.perf_system._update_spatial_index(entities)

        # Only entity1 should be indexed
        assert self.entity1 in self.perf_system.spatial_index[(0, 0)]


class TestPerformanceSystemUpdate:
    """Test PerformanceSystem update method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.perf_system = PerformanceSystem()
        self.mock_engine = Mock()
        self.mock_state_manager = Mock()
        self.mock_game_state = Mock()

        self.mock_engine.state_manager = self.mock_state_manager
        self.mock_state_manager.state = self.mock_game_state

        # Set up mock entities
        self.mock_entity = Mock()
        self.mock_entity.x = 10
        self.mock_entity.y = 15
        self.mock_game_state.entities = [self.mock_entity]
        self.mock_game_state.fov_map = Mock()
        self.mock_game_state.game_map = Mock()

        self.perf_system.initialize(self.mock_engine)

    def test_update_without_engine(self):
        """Test update when no engine is available."""
        self.perf_system._engine = None

        # Should not raise any exceptions
        self.perf_system.update(0.016)

    def test_update_without_state_manager(self):
        """Test update when engine has no state manager."""
        self.mock_engine.state_manager = None

        # Should not raise any exceptions
        self.perf_system.update(0.016)

    def test_update_optimizations_disabled(self):
        """Test update when optimizations are disabled."""
        self.perf_system.disable_optimizations()

        # Should not raise any exceptions
        self.perf_system.update(0.016)

    @patch("tcod.libtcodpy.map_is_in_fov")
    def test_update_with_valid_state(self, mock_is_in_fov):
        """Test update with valid game state."""
        mock_is_in_fov.return_value = True

        # Set up game map tiles - create a larger grid to avoid index errors
        mock_tile = Mock()
        mock_tile.explored = True
        # Create a 20x20 grid of tiles
        self.mock_game_state.game_map.tiles = [
            [mock_tile for _ in range(20)] for _ in range(20)
        ]

        self.perf_system.update(0.016)

        # Check that spatial index was updated
        assert len(self.perf_system.spatial_index) > 0

        # Check that optimization data was stored
        self.mock_state_manager.set_extra_data.assert_any_call(
            "spatial_index", self.perf_system.spatial_index
        )
        self.mock_state_manager.set_extra_data.assert_any_call(
            "visible_entities", self.perf_system.visible_entities
        )


class TestPerformanceSystemIntegration:
    """Integration tests for PerformanceSystem."""

    def test_performance_system_with_engine(self):
        """Test PerformanceSystem integration with GameEngine."""
        from engine.game_engine import GameEngine

        perf_system = PerformanceSystem(priority=5)
        engine = GameEngine()
        engine.register_system(perf_system)

        assert engine.get_system("performance") is perf_system
        assert perf_system.engine is engine

        # Test update through engine
        with patch.object(perf_system, "update") as mock_update:
            engine.update()
            mock_update.assert_called_once()

    def test_performance_system_priority_ordering(self):
        """Test that PerformanceSystem has very early priority."""
        from engine.game_engine import GameEngine
        from engine.systems import RenderSystem, InputSystem, AISystem

        perf_system = PerformanceSystem()  # Priority 5
        input_system = InputSystem()  # Priority 10
        ai_system = AISystem()  # Priority 50
        render_system = RenderSystem(Mock(), Mock(), 80, 50, {}, priority=100)

        engine = GameEngine()
        engine.register_system(render_system)
        engine.register_system(ai_system)
        engine.register_system(input_system)
        engine.register_system(perf_system)

        # Should be ordered: performance, input, ai, render
        system_names = list(engine.systems.keys())
        assert system_names.index("performance") < system_names.index("input")
        assert system_names.index("input") < system_names.index("ai")
        assert system_names.index("ai") < system_names.index("render")

    def test_fov_cache_size_limit(self):
        """Test that FOV cache doesn't grow indefinitely."""
        perf_system = PerformanceSystem()

        # Add more than 100 entries to trigger cache cleanup
        for i in range(105):
            perf_system.cache_fov_result(i, i, 5, Mock())

        # Cache should be limited to 100 entries
        assert len(perf_system.fov_cache) <= 100
