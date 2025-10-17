"""Test suite for exploration features infrastructure (Slice 1).

Tests the basic map feature components (MapFeature, Chest, Signpost)
to ensure the foundational plumbing is working correctly.
"""

import pytest
from entity import Entity
from components.map_feature import MapFeature, MapFeatureType
from components.chest import Chest, ChestState
from components.signpost import Signpost
from components.component_registry import ComponentType


class TestMapFeatureBase:
    """Test the base MapFeature component."""
    
    def test_map_feature_creation(self):
        """Test creating a basic map feature."""
        feature = MapFeature(MapFeatureType.CHEST)
        
        assert feature.feature_type == MapFeatureType.CHEST
        assert feature.discovered is False
        assert feature.interactable is True
    
    def test_map_feature_discovery(self):
        """Test discovering a map feature."""
        feature = MapFeature(MapFeatureType.CHEST)
        
        assert not feature.discovered
        results = feature.discover()
        assert feature.discovered
        assert len(results) == 1
        assert results[0]['discovered'] is True
    
    def test_map_feature_can_interact(self):
        """Test interaction availability."""
        feature = MapFeature(MapFeatureType.CHEST, discovered=False)
        
        assert not feature.can_interact()  # Not discovered yet
        
        feature.discover()
        assert feature.can_interact()  # Now discovered


class TestChest:
    """Test the Chest component."""
    
    def test_chest_creation_closed(self):
        """Test creating a closed chest."""
        chest = Chest(ChestState.CLOSED)
        
        assert chest.state == ChestState.CLOSED
        assert chest.feature_type == MapFeatureType.CHEST
        assert chest.is_mimic is False
        assert chest.can_interact()
    
    def test_chest_creation_trapped(self):
        """Test creating a trapped chest."""
        chest = Chest(
            state=ChestState.TRAPPED,
            trap_type='damage'
        )
        
        assert chest.is_trapped()
        assert not chest.is_locked()
        assert chest.trap_type == 'damage'
    
    def test_chest_creation_locked(self):
        """Test creating a locked chest."""
        chest = Chest(
            state=ChestState.LOCKED,
            key_id='test_key'
        )
        
        assert chest.is_locked()
        assert not chest.is_trapped()
        assert chest.key_id == 'test_key'
    
    def test_chest_open_normal(self):
        """Test opening a normal chest."""
        player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
        chest = Chest(ChestState.CLOSED)
        
        results = chest.open(player)
        
        assert chest.state == ChestState.OPEN
        assert any(r.get('chest_opened') for r in results)
        assert any(r.get('loot') is not None for r in results)
    
    def test_chest_open_locked_without_key(self):
        """Test opening a locked chest without a key."""
        player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
        chest = Chest(ChestState.LOCKED, key_id='test_key')
        
        results = chest.open(player, has_key=False)
        
        assert chest.state == ChestState.LOCKED  # Still locked
        assert any('locked' in str(r.get('message', '')).lower() for r in results)
    
    def test_chest_open_locked_with_key(self):
        """Test opening a locked chest with a key."""
        player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
        chest = Chest(ChestState.LOCKED, key_id='test_key')
        
        results = chest.open(player, has_key=True)
        
        assert chest.state == ChestState.OPEN  # Now open
        assert any(r.get('chest_opened') for r in results)
    
    def test_chest_open_trapped(self):
        """Test opening a trapped chest triggers the trap."""
        player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
        chest = Chest(ChestState.TRAPPED, trap_type='damage')
        
        results = chest.open(player)
        
        assert chest.state == ChestState.OPEN  # Trap sprung, now open
        assert any(r.get('trap_triggered') for r in results)
        assert any(r.get('trap_type') == 'damage' for r in results)
    
    def test_chest_mimic_revealed(self):
        """Test opening a mimic chest reveals the monster."""
        player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
        chest = Chest(is_mimic=True)
        
        results = chest.open(player)
        
        assert any(r.get('mimic_revealed') for r in results)
        assert chest.state != ChestState.OPEN  # Mimics don't open
    
    def test_chest_already_open(self):
        """Test interacting with an already-opened chest."""
        player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
        chest = Chest(ChestState.OPEN)
        
        results = chest.open(player)
        
        assert any('empty' in str(r.get('message', '')).lower() for r in results)
    
    def test_chest_descriptions(self):
        """Test chest descriptions for different states."""
        normal = Chest(ChestState.CLOSED)
        assert 'Chest' in normal.get_description()
        
        trapped = Chest(ChestState.TRAPPED)
        assert 'suspicious' in trapped.get_description()
        
        locked = Chest(ChestState.LOCKED)
        assert 'Locked' in locked.get_description()
        
        empty = Chest(ChestState.OPEN)
        assert 'Empty' in empty.get_description()
        
        mimic = Chest(is_mimic=True)
        assert 'off' in mimic.get_description()


class TestSignpost:
    """Test the Signpost component."""
    
    def test_signpost_creation(self):
        """Test creating a signpost."""
        signpost = Signpost("Test message", sign_type='lore')
        
        assert signpost.message == "Test message"
        assert signpost.sign_type == 'lore'
        assert signpost.feature_type == MapFeatureType.SIGNPOST
        assert not signpost.has_been_read
    
    def test_signpost_read(self):
        """Test reading a signpost."""
        player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
        signpost = Signpost("Beware: Dragon ahead!", sign_type='warning')
        
        results = signpost.read(player)
        
        assert signpost.has_been_read
        assert any(r.get('signpost_read') for r in results)
        assert any(r.get('sign_type') == 'warning' for r in results)
    
    def test_signpost_descriptions(self):
        """Test signpost descriptions."""
        unread = Signpost("Test", sign_type='lore')
        assert 'unread' in unread.get_description()
        
        read = Signpost("Test", sign_type='lore')
        read.has_been_read = True
        assert 'read' in read.get_description()
    
    def test_signpost_random_messages(self):
        """Test getting random messages for each type."""
        for sign_type in ['lore', 'warning', 'humor', 'hint', 'directional']:
            message = Signpost.get_random_message(sign_type)
            assert isinstance(message, str)
            assert len(message) > 0


class TestComponentRegistry:
    """Test that new components are registered correctly."""
    
    def test_map_feature_types_registered(self):
        """Test that new component types exist in the registry."""
        from components.component_registry import ComponentType
        
        # Check all new types are registered
        assert hasattr(ComponentType, 'MAP_FEATURE')
        assert hasattr(ComponentType, 'CHEST')
        assert hasattr(ComponentType, 'SIGNPOST')
        
        # Check they're enum values
        assert isinstance(ComponentType.MAP_FEATURE, ComponentType)
        assert isinstance(ComponentType.CHEST, ComponentType)
        assert isinstance(ComponentType.SIGNPOST, ComponentType)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

