"""Tests for tooltip entity ordering stability.

Verifies that get_all_entities_at_position returns entities in a stable,
deterministic order across multiple calls, even when called repeatedly.
This ensures tooltips don't flicker due to ordering changes.
"""

import pytest
from config.factories import EntityFactory
from config.entity_registry import load_entity_config
from ui.tooltip import get_all_entities_at_position
from render_functions import RenderOrder
from components.component_registry import ComponentType


@pytest.fixture(scope="module")
def entity_factory():
    """Create entity factory with loaded config."""
    load_entity_config('config/entities.yaml')
    return EntityFactory()


class TestTooltipOrderingStability:
    """Test that tooltip entity ordering is stable and deterministic."""
    
    def test_weapon_and_corpse_ordering_stable(self, entity_factory):
        """Test that weapon + corpse order is consistent across 100 calls.
        
        This is the exact scenario that was causing flicker:
        - A weapon (Club) on a tile
        - A corpse (Remains Of Orc) on the same tile
        
        We verify that get_all_entities_at_position returns them in the same
        order every single time, preventing tooltip flicker.
        """
        # Create entities at same position
        world_x, world_y = 10, 10
        
        # Create a corpse (dead orc, simulating kill_monster)
        corpse = entity_factory.create_monster('orc', world_x, world_y)
        corpse.render_order = RenderOrder.CORPSE  # Mark as corpse
        corpse.components.remove(ComponentType.FIGHTER)  # Remove combat components
        corpse.components.remove(ComponentType.AI)
        corpse.fighter = None
        corpse.ai = None
        
        # Create a weapon on the same tile
        weapon = entity_factory.create_weapon('club', world_x, world_y)
        
        # Create dummy player for filtering
        player = entity_factory.create_monster('orc', 0, 0)
        
        # Create entities list
        entities = [corpse, weapon, player]
        
        # Call get_all_entities_at_position multiple times
        results = []
        for i in range(100):
            result = get_all_entities_at_position(world_x, world_y, entities, player, fov_map=None)
            results.append(result)
        
        # All results should be identical
        first_result = results[0]
        for i, result in enumerate(results[1:], 1):
            assert len(result) == len(first_result), \
                f"Call {i}: result length {len(result)} != first result length {len(first_result)}"
            
            for j, (e1, e2) in enumerate(zip(first_result, result)):
                assert e1 is e2, \
                    f"Call {i}, entity {j}: {e1.name} (id:{id(e1)}) != {e2.name} (id:{id(e2)})"
    
    def test_multiple_items_ordering_stable(self, entity_factory):
        """Test that multiple items at same position maintain stable order.
        
        Scenario: Club and Dagger both on same tile (stacked items).
        """
        world_x, world_y = 20, 20
        
        club = entity_factory.create_weapon('club', world_x, world_y)
        dagger = entity_factory.create_weapon('dagger', world_x, world_y)
        
        player = entity_factory.create_monster('orc', 0, 0)
        entities = [club, dagger, player]
        
        # Call multiple times
        results = []
        for i in range(50):
            result = get_all_entities_at_position(world_x, world_y, entities, player, fov_map=None)
            results.append(result)
        
        # All results should be identical
        first_result = results[0]
        for i, result in enumerate(results[1:], 1):
            assert len(result) == len(first_result)
            for j, (e1, e2) in enumerate(zip(first_result, result)):
                assert e1 is e2, \
                    f"Call {i}, entity {j} ordering changed"
    
    def test_mixed_entities_ordering_stable(self, entity_factory):
        """Test stable ordering with living monster, items, and corpse.
        
        Scenario:
        - Living orc
        - Club item
        - Corpse of another orc
        
        Order should always be: living_monsters, items, corpses
        """
        world_x, world_y = 30, 30
        
        # Living monster
        live_orc = entity_factory.create_monster('orc', world_x, world_y)
        if live_orc.fighter:
            live_orc.fighter.hp = 10  # Alive
        
        # Item
        weapon = entity_factory.create_weapon('club', world_x, world_y)
        
        # Dead monster (corpse, simulating kill_monster)
        dead_orc = entity_factory.create_monster('orc', world_x, world_y)
        dead_orc.render_order = RenderOrder.CORPSE  # Mark as corpse
        dead_orc.components.remove(ComponentType.FIGHTER)  # Remove combat components
        dead_orc.components.remove(ComponentType.AI)
        dead_orc.fighter = None
        dead_orc.ai = None
        
        player = entity_factory.create_monster('orc', 0, 0)
        
        # Add them in random order to entities list
        entities = [weapon, dead_orc, player, live_orc]
        
        # Call multiple times
        results = []
        for i in range(50):
            result = get_all_entities_at_position(world_x, world_y, entities, player, fov_map=None)
            results.append(result)
        
        # All results should be identical
        first_result = results[0]
        
        # Verify order is: live monster, item, corpse
        assert len(first_result) == 3
        assert first_result[0] is live_orc, "First should be live monster"
        assert first_result[1] is weapon, "Second should be weapon"
        assert first_result[2] is dead_orc, "Third should be corpse"
        
        # Verify stability across all calls
        for i, result in enumerate(results[1:], 1):
            assert len(result) == 3
            assert result[0] is live_orc
            assert result[1] is weapon
            assert result[2] is dead_orc
    
    def test_empty_position_returns_empty(self, entity_factory):
        """Test that empty position returns empty list consistently."""
        world_x, world_y = 99, 99
        
        player = entity_factory.create_monster('orc', 0, 0)
        entities = [player]
        
        # No entities at this position
        for i in range(10):
            result = get_all_entities_at_position(world_x, world_y, entities, player, fov_map=None)
            assert result == []

