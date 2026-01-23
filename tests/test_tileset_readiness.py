"""Tests for tileset readiness groundwork.

These tests verify the minimal seams added for future tileset support:
1. Entity.render_key property (deterministic visual identity)
2. Visual registry (centralized char/color lookup)
3. TileRenderer protocol (interface definition)

These are lightweight tests that don't require game state or scenarios.
"""

import pytest
from unittest.mock import MagicMock


class TestEntityRenderKey:
    """Tests for Entity.render_key property."""
    
    def test_render_key_from_species_id(self):
        """Entity.render_key falls back to species_id."""
        from entity import Entity
        from render_functions import RenderOrder
        
        entity = Entity(
            x=0, y=0, char='o', color=(63, 127, 63),
            name='Orc', blocks=True, render_order=RenderOrder.ACTOR
        )
        entity.species_id = 'orc'
        
        assert entity.render_key == 'orc'
    
    def test_render_key_from_name_fallback(self):
        """Entity.render_key derives from name if no species_id."""
        from entity import Entity
        from render_functions import RenderOrder
        
        entity = Entity(
            x=0, y=0, char='T', color=(0, 127, 0),
            name='Ancient Troll', blocks=True, render_order=RenderOrder.ACTOR
        )
        
        # species_id falls back to name.lower().replace(" ", "_")
        assert entity.render_key == 'ancient_troll'
    
    def test_render_key_explicit_override(self):
        """Explicit _render_key takes priority over species_id."""
        from entity import Entity
        from render_functions import RenderOrder
        
        entity = Entity(
            x=0, y=0, char='X', color=(255, 0, 0),
            name='Test Entity', blocks=False, render_order=RenderOrder.ITEM
        )
        entity.species_id = 'test_entity'
        entity.render_key = 'custom_visual'
        
        assert entity.render_key == 'custom_visual'
    
    def test_render_key_deterministic(self):
        """Entity.render_key is deterministic across multiple calls."""
        from entity import Entity
        from render_functions import RenderOrder
        
        entity = Entity(
            x=5, y=10, char='@', color=(255, 255, 255),
            name='Player', blocks=True, render_order=RenderOrder.ACTOR
        )
        
        # Multiple calls should return the same value
        key1 = entity.render_key
        key2 = entity.render_key
        key3 = entity.render_key
        
        assert key1 == key2 == key3
    
    def test_trap_render_key_hidden_state(self):
        """Trap entity returns state-aware render_key when hidden."""
        from entity import Entity
        from render_functions import RenderOrder
        from components.trap import Trap
        from components.component_registry import ComponentType
        
        entity = Entity(
            x=0, y=0, char='^', color=(192, 32, 32),
            name='Spike Trap', blocks=False, render_order=RenderOrder.ITEM
        )
        
        trap = Trap(trap_type='spike_trap')
        trap.is_detected = False
        trap.is_disarmed = False
        entity.components.add(ComponentType.TRAP, trap)
        
        assert entity.render_key == 'trap_spike_trap_hidden'
    
    def test_trap_render_key_detected_state(self):
        """Trap entity returns state-aware render_key when detected."""
        from entity import Entity
        from render_functions import RenderOrder
        from components.trap import Trap
        from components.component_registry import ComponentType
        
        entity = Entity(
            x=0, y=0, char='^', color=(192, 32, 32),
            name='Spike Trap', blocks=False, render_order=RenderOrder.ITEM
        )
        
        trap = Trap(trap_type='spike_trap')
        trap.is_detected = True
        trap.is_disarmed = False
        entity.components.add(ComponentType.TRAP, trap)
        
        assert entity.render_key == 'trap_spike_trap_detected'
    
    def test_trap_render_key_disarmed_state(self):
        """Trap entity returns state-aware render_key when disarmed."""
        from entity import Entity
        from render_functions import RenderOrder
        from components.trap import Trap
        from components.component_registry import ComponentType
        
        entity = Entity(
            x=0, y=0, char='x', color=(80, 80, 80),
            name='Spike Trap', blocks=False, render_order=RenderOrder.ITEM
        )
        
        trap = Trap(trap_type='spike_trap')
        trap.is_detected = True
        trap.is_disarmed = True
        entity.components.add(ComponentType.TRAP, trap)
        
        assert entity.render_key == 'trap_spike_trap_disarmed'
    
    def test_chest_render_key_closed_state(self):
        """Chest entity returns state-aware render_key when closed."""
        from entity import Entity
        from render_functions import RenderOrder
        from components.chest import Chest, ChestState
        from components.component_registry import ComponentType
        
        entity = Entity(
            x=0, y=0, char='C', color=(139, 69, 19),
            name='Chest', blocks=False, render_order=RenderOrder.ITEM
        )
        
        chest = Chest(state=ChestState.CLOSED)
        entity.components.add(ComponentType.CHEST, chest)
        
        assert entity.render_key == 'chest_closed'
    
    def test_chest_render_key_open_state(self):
        """Chest entity returns state-aware render_key when open."""
        from entity import Entity
        from render_functions import RenderOrder
        from components.chest import Chest, ChestState
        from components.component_registry import ComponentType
        
        entity = Entity(
            x=0, y=0, char='C', color=(100, 100, 100),
            name='Chest', blocks=False, render_order=RenderOrder.ITEM
        )
        
        chest = Chest(state=ChestState.OPEN)
        entity.components.add(ComponentType.CHEST, chest)
        
        assert entity.render_key == 'chest_open'


class TestVisualRegistry:
    """Tests for rendering/visual_registry.py."""
    
    def test_get_visual_returns_visual_spec(self):
        """get_visual returns a VisualSpec with expected attributes."""
        from rendering.visual_registry import get_visual, VisualSpec
        
        visual = get_visual('orc')
        
        assert isinstance(visual, VisualSpec)
        assert hasattr(visual, 'char')
        assert hasattr(visual, 'fg_color')
    
    def test_get_visual_orc_has_correct_values(self):
        """get_visual('orc') returns expected char and color."""
        from rendering.visual_registry import get_visual
        
        visual = get_visual('orc')
        
        assert visual.char == 'o'
        assert visual.fg_color == (63, 127, 63)
    
    def test_get_visual_unknown_returns_default(self):
        """get_visual with unknown key returns default visual."""
        from rendering.visual_registry import get_visual, DEFAULT_VISUAL
        
        visual = get_visual('nonexistent_entity_xyz')
        
        assert visual == DEFAULT_VISUAL
        assert visual.char == '?'
        assert visual.fg_color == (255, 255, 255)
    
    def test_get_visual_trap_detected_state(self):
        """get_visual returns correct visual for trap detected state."""
        from rendering.visual_registry import get_visual
        
        visual = get_visual('trap_spike_trap_detected')
        
        assert visual.char == '^'
        # Color should be the trap's color (dark red)
        assert visual.fg_color[0] > visual.fg_color[1]  # More red than green
    
    def test_get_visual_trap_hidden_state(self):
        """get_visual returns floor appearance for hidden trap."""
        from rendering.visual_registry import get_visual
        
        visual = get_visual('trap_spike_trap_hidden')
        
        assert visual.char == '.'  # Appears as floor
    
    def test_get_visual_chest_states(self):
        """get_visual returns different visuals for chest states."""
        from rendering.visual_registry import get_visual
        
        closed = get_visual('chest_closed')
        opened = get_visual('chest_open')
        
        assert closed.char == 'C'
        assert opened.char == 'C'
        # Open chest should be greyer
        assert opened.fg_color[0] == opened.fg_color[1] == opened.fg_color[2]
    
    def test_has_visual(self):
        """has_visual returns True for registered keys."""
        from rendering.visual_registry import has_visual
        
        assert has_visual('orc') is True
        assert has_visual('player') is True
        assert has_visual('nonexistent_xyz') is False
    
    def test_get_all_render_keys_returns_list(self):
        """get_all_render_keys returns a non-empty list."""
        from rendering.visual_registry import get_all_render_keys
        
        keys = get_all_render_keys()
        
        assert isinstance(keys, list)
        assert len(keys) > 0
        assert 'orc' in keys
        assert 'player' in keys


class TestTileRendererProtocol:
    """Tests for TileRenderer protocol definition."""
    
    def test_tile_renderer_protocol_exists(self):
        """TileRenderer protocol is importable."""
        from io_layer.interfaces import TileRenderer
        
        assert TileRenderer is not None
    
    def test_tile_renderer_is_runtime_checkable(self):
        """TileRenderer can be used with isinstance checks."""
        from io_layer.interfaces import TileRenderer
        
        class MockTileRenderer:
            def draw_tile(self, x, y, render_key, fg_color=None, bg_color=None):
                pass
            
            def draw_text(self, x, y, text, fg_color=None, bg_color=None):
                pass
            
            def clear(self):
                pass
            
            def present(self):
                pass
        
        renderer = MockTileRenderer()
        assert isinstance(renderer, TileRenderer)
    
    def test_tile_renderer_protocol_has_draw_tile(self):
        """TileRenderer protocol defines draw_tile method."""
        from io_layer.interfaces import TileRenderer
        import inspect
        
        # Check that draw_tile is defined on the protocol
        assert hasattr(TileRenderer, 'draw_tile')
    
    def test_tile_renderer_protocol_has_draw_text(self):
        """TileRenderer protocol defines draw_text method."""
        from io_layer.interfaces import TileRenderer
        
        assert hasattr(TileRenderer, 'draw_text')


class TestIntegration:
    """Integration tests between Entity.render_key and visual_registry."""
    
    def test_entity_render_key_resolves_in_registry(self):
        """Entity.render_key can be used to look up visuals."""
        from entity import Entity
        from render_functions import RenderOrder
        from rendering.visual_registry import get_visual, has_visual
        
        entity = Entity(
            x=0, y=0, char='o', color=(63, 127, 63),
            name='Orc', blocks=True, render_order=RenderOrder.ACTOR
        )
        entity.species_id = 'orc'
        
        # Get the render_key
        key = entity.render_key
        
        # Verify it's registered
        assert has_visual(key)
        
        # Verify we can look up the visual
        visual = get_visual(key)
        assert visual.char == 'o'
    
    def test_trap_state_transition_updates_render_key(self):
        """Trap state changes are reflected in render_key."""
        from entity import Entity
        from render_functions import RenderOrder
        from components.trap import Trap
        from components.component_registry import ComponentType
        from rendering.visual_registry import get_visual
        
        entity = Entity(
            x=5, y=5, char='^', color=(192, 32, 32),
            name='Spike Trap', blocks=False, render_order=RenderOrder.ITEM
        )
        
        trap = Trap(trap_type='spike_trap')
        trap.is_detected = False
        trap.is_disarmed = False
        entity.components.add(ComponentType.TRAP, trap)
        
        # Initially hidden
        assert entity.render_key == 'trap_spike_trap_hidden'
        visual_hidden = get_visual(entity.render_key)
        assert visual_hidden.char == '.'  # Floor appearance
        
        # Detect the trap
        trap.is_detected = True
        
        # Now detected
        assert entity.render_key == 'trap_spike_trap_detected'
        visual_detected = get_visual(entity.render_key)
        assert visual_detected.char == '^'  # Trap appearance
