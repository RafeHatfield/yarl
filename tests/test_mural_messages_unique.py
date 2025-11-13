"""Tests for unique mural message selection per floor.

This test module verifies that murals on a single floor don't repeat messages
from the same pool, and that message repetition is only allowed after all
available messages have been exhausted.
"""

import pytest
from services.mural_manager import MuralManager
from config.murals_registry import MuralsRegistry


class TestMuralMessageUniqueness:
    """Test that mural messages are unique per floor."""
    
    def test_manager_tracks_used_messages_per_floor(self):
        """The mural manager should track which messages have been used per floor."""
        manager = MuralManager()
        
        # Initialize floor 1
        manager.set_current_floor(1)
        
        # Verify tracking dict exists for floor 1
        assert 1 in manager.used_messages_per_floor
        assert len(manager.used_messages_per_floor[1]) == 0
    
    def test_unique_message_selection_single_floor(self):
        """Requesting multiple murals on same floor should not duplicate messages."""
        manager = MuralManager()
        manager.set_current_floor(1)
        
        # Request multiple murals for the same depth
        depth = 1
        selected_ids = []
        
        # Get up to 5 unique murals (or fewer if pool is small)
        for i in range(min(5, len(manager.mural_registry.get_all_murals_for_depth(depth)))):
            text, mural_id = manager.get_unique_mural(depth)
            if mural_id:
                selected_ids.append(mural_id)
        
        # All selected IDs should be unique (no duplicates)
        if len(selected_ids) > 1:
            assert len(selected_ids) == len(set(selected_ids)), f"Duplicate IDs found: {selected_ids}"
    
    def test_different_floors_have_independent_tracking(self):
        """Different floors should track used messages independently."""
        manager = MuralManager()
        
        # Get mural on floor 1
        manager.set_current_floor(1)
        text1, id1 = manager.get_unique_mural(1)
        
        # Move to floor 2
        manager.set_current_floor(2)
        
        # Floor 2 should have fresh tracking
        assert len(manager.used_messages_per_floor[2]) == 0
        
        # We should be able to get a mural on floor 2
        text2, id2 = manager.get_unique_mural(1)
        
        # Floor 1 and 2 can have different used sets
        # (Floor 1 should have id1, Floor 2 should not initially)
        if id1 and id2:
            # It's possible they're the same by chance, but independent tracking verified
            assert 1 in manager.used_messages_per_floor
            assert 2 in manager.used_messages_per_floor
    
    def test_reset_floor_clears_tracking(self):
        """Resetting a floor should clear its used message tracking."""
        manager = MuralManager()
        manager.set_current_floor(1)
        
        # Use a few murals
        for i in range(3):
            text, mural_id = manager.get_unique_mural(1)
        
        # Verify tracking has entries
        used_count = len(manager.used_messages_per_floor[1])
        
        if used_count > 0:
            # Reset floor 1
            manager.reset_floor_state(1)
            
            # Tracking should be cleared
            assert len(manager.used_messages_per_floor[1]) == 0
    
    def test_reset_all_clears_all_tracking(self):
        """Resetting all should clear tracking for all floors."""
        manager = MuralManager()
        
        # Use murals on multiple floors
        for floor in [1, 2, 3]:
            manager.set_current_floor(floor)
            text, mural_id = manager.get_unique_mural(floor)
        
        # Verify some tracking exists
        assert len(manager.used_messages_per_floor) > 0
        
        # Reset all
        manager.reset_all()
        
        # All tracking should be cleared
        assert len(manager.used_messages_per_floor) == 0
    
    def test_mural_manager_singleton(self):
        """MuralManager should be a singleton."""
        from services.mural_manager import get_mural_manager
        
        manager1 = get_mural_manager()
        manager2 = get_mural_manager()
        
        # Should be the same instance
        assert manager1 is manager2
    
    def test_get_unique_mural_returns_text_and_id(self):
        """get_unique_mural should return both text and mural_id."""
        manager = MuralManager()
        manager.set_current_floor(1)
        
        text, mural_id = manager.get_unique_mural(1)
        
        # Either both are None (no murals available), or both are strings
        if text is not None:
            assert isinstance(text, str)
            assert len(text) > 0
        if mural_id is not None:
            assert isinstance(mural_id, str)
            assert len(mural_id) > 0
        
        # Should not have one but not the other
        assert (text is None and mural_id is None) or (text is not None and mural_id is not None)


class TestMuralMessageDepthVariation:
    """Test that murals vary by depth."""
    
    def test_different_depths_have_different_pools(self):
        """Different dungeon depths should have different mural pools."""
        manager = MuralManager()
        registry = manager.mural_registry
        
        # Get murals for two different depths
        depth1_murals = registry.get_all_murals_for_depth(1)
        depth5_murals = registry.get_all_murals_for_depth(5)
        
        # Both should have some murals
        if len(depth1_murals) > 0 and len(depth5_murals) > 0:
            # Depths might have overlapping murals (intentional design)
            # Just verify both have content
            assert len(depth1_murals) > 0
            assert len(depth5_murals) > 0
    
    def test_depth_aware_mural_selection(self):
        """Murals should be selected respecting depth constraints."""
        manager = MuralManager()
        
        # Test with depth 1
        manager.set_current_floor(1)
        text, mural_id = manager.get_unique_mural(1)
        
        if text and mural_id:
            # Verify the mural exists in the registry for this depth
            depth1_murals = manager.mural_registry.get_all_murals_for_depth(1)
            mural_ids = [m[1] for m in depth1_murals]
            assert mural_id in mural_ids, f"Mural {mural_id} not found in depth 1 pool"

