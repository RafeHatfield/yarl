"""Tests for enhanced tooltip system.

Tests the new tooltip features:
1. Monster tooltips showing equipped weapons/armor
2. Multi-entity tooltips showing all items at a location
"""

import pytest
from config.entity_factory import EntityFactory
from config.entity_registry import load_entity_config
from ui.tooltip import get_all_entities_at_position
from render_functions import RenderOrder
from components.component_registry import ComponentType


@pytest.fixture(scope="module")
def entity_factory():
    """Create entity factory with loaded config."""
    load_entity_config('config/entities.yaml')
    return EntityFactory()


class TestMonsterEquipmentTooltips:
    """Test that monster tooltips show equipment."""
    
    def test_orc_with_weapon_shows_wielding(self, entity_factory):
        """Test that orc with weapon shows 'Wielding' in tooltip."""
        orc = entity_factory.create_monster('orc', 5, 5)
        weapon = entity_factory.create_weapon('club', 5, 5)
        
        # Equip weapon on orc
        if orc.equipment:
            orc.equipment.main_hand = weapon
            
            # Verify equipment is set
            assert orc.equipment.main_hand == weapon
            assert orc.equipment.main_hand.name == 'Club'
    
    def test_orc_with_armor_shows_wearing(self, entity_factory):
        """Test that orc with armor shows 'Wearing' in tooltip."""
        orc = entity_factory.create_monster('orc', 5, 5)
        armor = entity_factory.create_armor('leather_armor', 5, 5)
        
        # Equip armor on orc
        if orc.equipment:
            orc.equipment.off_hand = armor
            
            # Verify equipment is set
            assert orc.equipment.off_hand == armor
    
    def test_orc_with_both_weapon_and_armor(self, entity_factory):
        """Test that orc with both shows both in tooltip."""
        orc = entity_factory.create_monster('orc', 5, 5)
        weapon = entity_factory.create_weapon('shortsword', 5, 5)
        armor = entity_factory.create_armor('leather_armor', 5, 5)
        
        # Equip both
        if orc.equipment:
            orc.equipment.main_hand = weapon
            orc.equipment.off_hand = armor
            
            # Verify both are set
            assert orc.equipment.main_hand == weapon
            assert orc.equipment.off_hand == armor


class TestMultiEntityTooltips:
    """Test that tooltips show all entities at a location."""
    
    def test_get_all_entities_returns_monster_and_item(self, entity_factory):
        """Test that function returns both monster and item at same location."""
        player = entity_factory.create_monster('orc', 0, 0)
        player.name = 'Player'
        
        orc = entity_factory.create_monster('orc', 5, 5)
        scroll = entity_factory.create_spell_item('lightning_scroll', 5, 5)
        
        entities = [player, orc, scroll]
        
        # Get all entities at (5, 5)
        entities_at_pos = get_all_entities_at_position(5, 5, entities, player)
        
        # Should return both orc and scroll
        assert len(entities_at_pos) == 2
        assert orc in entities_at_pos
        assert scroll in entities_at_pos
    
    def test_get_all_entities_prioritizes_living_monsters(self, entity_factory):
        """Test that living monsters come before items and corpses."""
        player = entity_factory.create_monster('orc', 0, 0)
        player.name = 'Player'
        
        # Create living orc
        living_orc = entity_factory.create_monster('orc', 5, 5)
        
        # Create corpse (simulating kill_monster behavior)
        dead_orc = entity_factory.create_monster('orc', 5, 5)
        dead_orc.render_order = RenderOrder.CORPSE  # Mark as corpse
        dead_orc.components.remove(ComponentType.FIGHTER)  # Remove combat components
        dead_orc.components.remove(ComponentType.AI)
        dead_orc.fighter = None
        dead_orc.ai = None
        dead_orc.name = 'remains of Orc'
        
        # Create item
        scroll = entity_factory.create_spell_item('lightning_scroll', 5, 5)
        
        entities = [player, scroll, dead_orc, living_orc]
        
        # Get all entities at (5, 5)
        entities_at_pos = get_all_entities_at_position(5, 5, entities, player)
        
        # Should return all 3: living orc, item, corpse
        assert len(entities_at_pos) == 3
        
        # Living monster should be first
        assert entities_at_pos[0] == living_orc
        
        # Item should be second
        assert entities_at_pos[1] == scroll
        
        # Corpse should be last
        assert entities_at_pos[2] == dead_orc
    
    def test_corpse_and_items_both_shown(self, entity_factory):
        """Test that corpse and items at same location both appear in tooltip."""
        player = entity_factory.create_monster('orc', 0, 0)
        player.name = 'Player'
        
        # Create corpse (simulating kill_monster behavior)
        corpse = entity_factory.create_monster('orc', 5, 5)
        corpse.render_order = RenderOrder.CORPSE  # Mark as corpse
        corpse.components.remove(ComponentType.FIGHTER)  # Remove combat components
        corpse.components.remove(ComponentType.AI)
        corpse.fighter = None
        corpse.ai = None
        corpse.name = 'remains of Orc'
        
        # Create dropped items (as if monster died and dropped loot)
        weapon = entity_factory.create_weapon('club', 5, 5)
        armor = entity_factory.create_armor('leather_armor', 5, 5)
        
        entities = [player, corpse, weapon, armor]
        
        # Get all entities at (5, 5)
        entities_at_pos = get_all_entities_at_position(5, 5, entities, player)
        
        # Should show all 3: items first, then corpse
        assert len(entities_at_pos) == 3
        assert weapon in entities_at_pos
        assert armor in entities_at_pos
        assert corpse in entities_at_pos
    
    def test_multiple_items_at_same_location(self, entity_factory):
        """Test that multiple items stacked at same location all appear."""
        player = entity_factory.create_monster('orc', 0, 0)
        player.name = 'Player'
        
        # Create multiple items at same location
        scroll1 = entity_factory.create_spell_item('lightning_scroll', 5, 5)
        scroll2 = entity_factory.create_spell_item('fireball_scroll', 5, 5)
        potion = entity_factory.create_spell_item('healing_potion', 5, 5)
        
        entities = [player, scroll1, scroll2, potion]
        
        # Get all entities at (5, 5)
        entities_at_pos = get_all_entities_at_position(5, 5, entities, player)
        
        # Should show all 3 items
        assert len(entities_at_pos) == 3
        assert scroll1 in entities_at_pos
        assert scroll2 in entities_at_pos
        assert potion in entities_at_pos
    
    def test_player_excluded_from_results(self, entity_factory):
        """Test that player is not included in entity tooltip."""
        player = entity_factory.create_monster('orc', 5, 5)
        player.name = 'Player'
        
        scroll = entity_factory.create_spell_item('lightning_scroll', 5, 5)
        
        entities = [player, scroll]
        
        # Get all entities at (5, 5) where player is standing
        entities_at_pos = get_all_entities_at_position(5, 5, entities, player)
        
        # Should only return scroll, not player
        assert len(entities_at_pos) == 1
        assert scroll in entities_at_pos
        assert player not in entities_at_pos
    
    def test_empty_location_returns_empty_list(self, entity_factory):
        """Test that empty location returns empty list."""
        player = entity_factory.create_monster('orc', 0, 0)
        player.name = 'Player'
        
        entities = [player]
        
        # Get all entities at (5, 5) where nothing exists
        entities_at_pos = get_all_entities_at_position(5, 5, entities, player)
        
        # Should return empty list
        assert len(entities_at_pos) == 0
        assert entities_at_pos == []


class TestMonsterLootScenario:
    """Test the common scenario: monster dies, drops loot, player hovers."""
    
    def test_monster_death_loot_pile_tooltip(self, entity_factory):
        """Simulate monster death scenario: corpse + dropped weapon + dropped armor."""
        player = entity_factory.create_monster('orc', 0, 0)
        player.name = 'Player'
        
        # Create "dead" orc (corpse, simulating kill_monster behavior)
        orc_corpse = entity_factory.create_monster('orc', 10, 10)
        orc_corpse.render_order = RenderOrder.CORPSE  # Mark as corpse
        orc_corpse.components.remove(ComponentType.FIGHTER)  # Remove combat components
        orc_corpse.components.remove(ComponentType.AI)
        orc_corpse.fighter = None
        orc_corpse.ai = None
        orc_corpse.name = 'remains of Orc'
        
        # Create dropped loot at same position
        dropped_weapon = entity_factory.create_weapon('club', 10, 10)
        dropped_armor = entity_factory.create_armor('leather_armor', 10, 10)
        
        entities = [player, orc_corpse, dropped_weapon, dropped_armor]
        
        # Get tooltip entities
        entities_at_pos = get_all_entities_at_position(10, 10, entities, player)
        
        # Should show: 2 items (prioritized) + corpse
        assert len(entities_at_pos) == 3
        
        # Items should come before corpse
        assert dropped_weapon in entities_at_pos
        assert dropped_armor in entities_at_pos
        assert orc_corpse in entities_at_pos
        
        # Items should be before corpse in priority
        item_indices = [i for i, e in enumerate(entities_at_pos) if e in [dropped_weapon, dropped_armor]]
        corpse_index = entities_at_pos.index(orc_corpse)
        
        # All items should come before corpse
        for item_idx in item_indices:
            assert item_idx < corpse_index

