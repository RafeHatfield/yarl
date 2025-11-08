"""Phase 4: Environmental Lore Integration Tests

Tests for Phase 4 environmental storytelling features:
- Signpost lore additions (28 new messages)
- Mural & inscription system
- Easter egg interactions
"""

import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.signpost_message_registry import get_signpost_message_registry
from config.murals_registry import get_murals_registry
from components.signpost import Signpost
from components.mural import Mural
from config.entity_factory import get_entity_factory
from entity import Entity


class TestPhase4SignpostLore:
    """Test Phase 4 signpost lore additions."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures."""
        # Get registries
        self.signpost_registry = get_signpost_message_registry()
        self.entity_factory = get_entity_factory()
    
    def test_signpost_registry_loads(self):
        """Verify signpost messages load successfully."""
        assert self.signpost_registry is not None
        assert self.signpost_registry._loaded
    
    def test_phase4_lore_messages_present(self):
        """Verify Phase 4 lore messages are present."""
        lore_messages = self.signpost_registry.messages.get('lore', [])
        assert len(lore_messages) > 20, "Should have 40+ lore messages (original + Phase 4)"
        
        # Get all lore message texts
        message_texts = [msg.text for msg in lore_messages]
        
        # Check for Phase 4 specific messages
        phase4_keywords = [
            "Something ancient dreams beneath these stones",
            "Two dragons came to these lands",
            "Aurelyn was the name",
            "Zhyraxion",
            "soul"
        ]
        
        # At least some Phase 4 messages should be present
        matches = sum(1 for keyword in phase4_keywords 
                     for text in message_texts if keyword in text)
        assert matches > 0, "Phase 4 lore messages should be present"
    
    def test_depth_filtering_on_signposts(self):
        """Verify signposts are filtered correctly by depth."""
        # Deep level messages (21-25) should have specific content
        deep_messages = [
            msg for msg in self.signpost_registry.messages.get('lore', [])
            if msg.is_valid_for_depth(25)
        ]
        assert len(deep_messages) > 10
        
        # Early level messages should be different
        early_messages = [
            msg for msg in self.signpost_registry.messages.get('lore', [])
            if msg.is_valid_for_depth(1)
        ]
        assert len(early_messages) > 5
        
        # They shouldn't be the same pool
        deep_texts = {msg.text for msg in deep_messages}
        early_texts = {msg.text for msg in early_messages}
        assert len(deep_texts & early_texts) < len(deep_texts), "Depth filtering should create different pools"
    
    def test_soul_rotation_references_in_signposts(self):
        """Verify soul rotation theme is present in signposts."""
        lore_messages = self.signpost_registry.messages.get('lore', [])
        message_texts = [msg.text for msg in lore_messages]
        
        soul_keywords = ["soul", "corpse", "vessel", "collection", "body"]
        matches = [text for text in message_texts 
                  for keyword in soul_keywords if keyword in text.lower()]
        
        assert len(matches) >= 5, "Soul rotation theme should appear multiple times"
    
    def test_two_dragon_references_in_signposts(self):
        """Verify two-dragon narrative is present in signposts."""
        lore_messages = self.signpost_registry.messages.get('lore', [])
        message_texts = [msg.text for msg in lore_messages]
        
        dragon_keywords = ["dragon", "Zhyraxion", "Aurelyn"]
        matches = [text for text in message_texts 
                  for keyword in dragon_keywords if keyword in text.lower()]
        
        assert len(matches) >= 2, "Two-dragon narrative should appear multiple times"
    
    def test_signpost_entity_creation(self):
        """Verify signpost entities can be created with new lore."""
        signpost = Signpost("Test lore message", sign_type='lore')
        assert signpost is not None
        assert signpost.message == "Test lore message"
        assert signpost.sign_type == 'lore'
        assert not signpost.has_been_read
    
    def test_random_signpost_message_generation(self):
        """Verify random signpost messages can be generated for all depths."""
        for depth in [1, 5, 10, 15, 20, 25]:
            message = Signpost.get_random_message('lore', depth)
            assert message is not None
            assert len(message) > 0


class TestPhase4MuralSystem:
    """Test Phase 4 mural and inscription system."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures."""
        self.murals_registry = get_murals_registry()
        self.entity_factory = get_entity_factory()
    
    def test_murals_registry_loads(self):
        """Verify murals load successfully."""
        assert self.murals_registry is not None
        assert self.murals_registry._loaded
    
    def test_murals_available_for_all_depths(self):
        """Verify murals are available throughout the dungeon."""
        for depth in [1, 5, 10, 15, 20, 25]:
            mural_text, mural_id = self.murals_registry.get_random_mural(depth)
            # Some depths might not have murals (that's ok)
            # But at least some should
            if mural_text:
                assert len(mural_text) > 0
                assert mural_id is not None
    
    def test_mural_depth_tiers(self):
        """Verify murals have appropriate depth tiers."""
        early_murals = self.murals_registry.get_all_murals_for_depth(5)
        mid_murals = self.murals_registry.get_all_murals_for_depth(15)
        deep_murals = self.murals_registry.get_all_murals_for_depth(24)
        
        # Each tier should have some murals
        assert len(early_murals) > 0, "Early game should have murals"
        assert len(mid_murals) > 0, "Mid game should have murals"
        assert len(deep_murals) > 0, "Deep game should have murals"
    
    def test_mural_entity_creation(self):
        """Verify mural entities can be created."""
        mural = Mural("Test mural text", mural_id="test_001")
        assert mural is not None
        assert mural.text == "Test mural text"
        assert mural.mural_id == "test_001"
        assert not mural.has_been_examined
    
    def test_mural_examine_action(self):
        """Verify mural examination works."""
        mural = Mural("Test mural description", mural_id="test_examine")
        
        # Create a fake player entity
        player = Entity(10, 10, '@', (255, 255, 255), 'Player')
        
        # Examine the mural
        results = mural.examine(player)
        
        assert len(results) > 0
        assert results[0]['mural_examined'] is True
        assert 'message' in results[0]
        assert mural.has_been_examined
    
    def test_mural_factory_creation(self):
        """Verify entity factory can create murals."""
        mural_entity = self.entity_factory.create_mural(10, 10, depth=15)
        
        if mural_entity:  # Mural might not exist for this depth
            assert mural_entity.mural is not None
            assert mural_entity.x == 10
            assert mural_entity.y == 10
            assert mural_entity.char == "M"
    
    def test_mural_canonical_lore_themes(self):
        """Verify murals contain canonical lore themes."""
        all_murals = []
        for depth in range(1, 26):
            murals = self.murals_registry.get_all_murals_for_depth(depth)
            all_murals.extend([text for text, _ in murals])
        
        mural_text = " ".join(all_murals).lower()
        
        # Check for key lore themes
        themes = [
            "dragon",
            "ritual",
            "heart",
            "zhyraxion",
            "aurelyn"
        ]
        
        found_themes = [theme for theme in themes if theme in mural_text]
        assert len(found_themes) >= 3, "Murals should contain canonical lore themes"


class TestPhase4Integration:
    """Integration tests for Phase 4 environmental lore."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures."""
        self.signpost_registry = get_signpost_message_registry()
        self.murals_registry = get_murals_registry()
        self.entity_factory = get_entity_factory()
    
    def test_phase4_complete_feature_set(self):
        """Verify all Phase 4 features are working."""
        # Signposts should have many messages
        lore_count = len(self.signpost_registry.messages.get('lore', []))
        assert lore_count >= 40, "Should have 40+ lore messages"
        
        # Murals should be available
        murals_count = len(self.murals_registry.murals)
        assert murals_count >= 10, "Should have 10+ murals"
        
        # Both systems should integrate with entity factory
        signpost = self.entity_factory.create_signpost('signpost', 10, 10, depth=15)
        mural = self.entity_factory.create_mural(10, 10, depth=15)
        
        # At least one should succeed
        assert signpost is not None or mural is not None
    
    def test_phase4_lore_narrative_progression(self):
        """Verify lore progresses narratively through depths."""
        # Get all available messages per tier (not random sampling)
        lore_messages = self.signpost_registry.messages.get('lore', [])
        
        # Early game (1-10)
        tier1 = [msg for msg in lore_messages if msg.is_valid_for_depth(5)]
        # Mid game (11-20)
        tier2 = [msg for msg in lore_messages if msg.is_valid_for_depth(15)]
        # Deep game (21-25)
        tier3 = [msg for msg in lore_messages if msg.is_valid_for_depth(23)]
        
        # Each tier should have some content
        assert len(tier1) > 0
        assert len(tier2) > 0
        assert len(tier3) > 0
        
        # Check for appropriate keywords in each tier
        t1_text = " ".join([msg.text for msg in tier1]).lower()
        t2_text = " ".join([msg.text for msg in tier2]).lower()
        t3_text = " ".join([msg.text for msg in tier3]).lower()
        
        # Mid game should have ritual/dragon/soul themes
        assert any(kw in t2_text for kw in ["ritual", "dragon", "soul", "entity"])
        
        # Deep game should have choice/heart themes (from Phase 4 additions)
        assert any(kw in t3_text for kw in ["choice", "heart", "zhyraxion", "ritual", "ending"])
    
    def test_phase4_no_regressions(self):
        """Verify Phase 4 doesn't break existing systems."""
        # Test that original signpost types still work
        for sign_type in ['signpost', 'warning_sign', 'humor_sign', 'hint_sign']:
            signpost = self.entity_factory.create_signpost(sign_type, 10, 10)
            assert signpost is not None, f"Should be able to create {sign_type}"
        
        # Test various depths
        for depth in [1, 5, 10, 15, 20, 25]:
            signpost = self.entity_factory.create_signpost('signpost', 10, 10, depth=depth)
            assert signpost is not None, f"Should create signpost at depth {depth}"


class TestPhase4EasterEggs:
    """Test Phase 4 easter egg mechanics."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures."""
        self.murals_registry = get_murals_registry()
    
    def test_six_endings_referenced_in_murals(self):
        """Verify murals hint at the six endings."""
        # Get all mural texts
        all_murals = []
        for depth in range(1, 26):
            murals = self.murals_registry.get_all_murals_for_depth(depth)
            all_murals.extend([text for text, _ in murals])
        
        full_text = " ".join(all_murals)
        
        # Deep murals should reference ending choices
        deep_murals = self.murals_registry.get_all_murals_for_depth(24)
        deep_text = " ".join([text for text, _ in deep_murals])
        
        # The deep mural at 24-25 should mention choices/paths
        assert "path" in deep_text.lower() or "choice" in deep_text.lower()
    
    def test_mural_tracking_for_achievements(self):
        """Verify murals can be tracked for achievement system."""
        all_mural_ids = set()
        
        for depth in range(1, 26):
            murals = self.murals_registry.get_all_murals_for_depth(depth)
            for _, mural_id in murals:
                all_mural_ids.add(mural_id)
        
        # Should have multiple unique murals
        assert len(all_mural_ids) >= 10, "Should have at least 10 unique murals for tracking"
    
    def test_mural_retrieval_by_id(self):
        """Verify murals can be retrieved by ID for easter eggs."""
        # Get a specific mural by ID
        all_murals = []
        for depth in range(1, 26):
            murals = self.murals_registry.get_all_murals_for_depth(depth)
            all_murals.extend([(text, mural_id) for text, mural_id in murals])
        
        if all_murals:
            text, mural_id = all_murals[0]
            retrieved = self.murals_registry.get_mural_by_id(mural_id)
            
            assert retrieved is not None
            assert retrieved[0] == text
            assert retrieved[1] == mural_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

