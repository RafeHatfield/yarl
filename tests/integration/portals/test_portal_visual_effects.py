"""Portal Visual Effects Tests

Tests for portal teleportation visual feedback system.
"""

import pytest
from services.portal_visual_effects import (
    PortalVFXSystem, 
    TeleportationEffect, 
    PortalEffectQueue,
    get_portal_effect_queue
)


class TestPortalVFXSystem:
    """Test portal visual effects generation."""
    
    def test_player_teleportation_message(self):
        """Player teleportation should have dramatic message."""
        msg = PortalVFXSystem.create_teleportation_message(
            "Player",
            is_player=True,
            is_monster=False
        )
        
        assert 'message' in msg
        assert msg['effect_type'] == 'teleport_player'
        assert msg['intensity'] == 'high'
        # Message should include shimmer/warping effect
        assert '✨' in str(msg['message']) or 'warps' in str(msg['message']).lower()
    
    def test_monster_teleportation_message(self):
        """Monster teleportation should include monster name."""
        msg = PortalVFXSystem.create_teleportation_message(
            "Evil Orc",
            is_player=False,
            is_monster=True
        )
        
        assert 'message' in msg
        assert msg['effect_type'] == 'teleport_monster'
        assert msg['intensity'] == 'medium'
        # Message should include monster name
        assert 'Evil Orc' in str(msg['message'])
        assert '✨' in str(msg['message'])
    
    def test_portal_placement_message_entrance(self):
        """Entrance portal placement message."""
        msg = PortalVFXSystem.create_portal_placement_message('entrance')
        
        assert msg is not None
        assert 'entrance' in str(msg).lower() or 'blue' in str(msg).lower()
    
    def test_portal_placement_message_exit(self):
        """Exit portal placement message."""
        msg = PortalVFXSystem.create_portal_placement_message('exit')
        
        assert msg is not None
        assert 'exit' in str(msg).lower() or 'orange' in str(msg).lower()
    
    def test_portal_activation_message(self):
        """Portal activation message when stepped on."""
        msg = PortalVFXSystem.create_portal_activation_message("Player")
        
        assert msg is not None
        assert "Player" in str(msg)
        assert '✨' in str(msg)


class TestTeleportationEffect:
    """Test teleportation effect objects."""
    
    def test_create_teleportation_effect(self):
        """Create a teleportation effect."""
        effect = TeleportationEffect(
            from_pos=(5, 5),
            to_pos=(10, 10),
            entity_name="Orc",
            intensity='medium'
        )
        
        assert effect.from_pos == (5, 5)
        assert effect.to_pos == (10, 10)
        assert effect.entity_name == "Orc"
        assert effect.intensity == 'medium'
    
    def test_flash_color_low_intensity(self):
        """Low intensity effect has dim blue."""
        effect = TeleportationEffect(
            (5, 5), (10, 10), "Orc", intensity='low'
        )
        
        color = effect.get_flash_color()
        assert isinstance(color, tuple)
        assert len(color) == 3
        # Dim blue (lower values)
        assert color[2] <= 200  # Blue channel not too high
    
    def test_flash_color_medium_intensity(self):
        """Medium intensity effect has bright blue."""
        effect = TeleportationEffect(
            (5, 5), (10, 10), "Orc", intensity='medium'
        )
        
        color = effect.get_flash_color()
        # Bright blue
        assert color[2] >= 200  # Blue channel prominent
    
    def test_flash_color_high_intensity(self):
        """High intensity effect has very bright cyan."""
        effect = TeleportationEffect(
            (5, 5), (10, 10), "Player", intensity='high'
        )
        
        color = effect.get_flash_color()
        # Very bright cyan
        assert color[0] >= 200  # Red
        assert color[1] >= 200  # Green  
        assert color[2] >= 200  # Blue


class TestPortalEffectQueue:
    """Test the effect queue system."""
    
    def test_create_effect_queue(self):
        """Create effect queue."""
        queue = PortalEffectQueue()
        
        assert queue.effects == []
        assert queue.max_effects == 10
    
    def test_add_teleportation_effect(self):
        """Add a teleportation effect to queue."""
        queue = PortalEffectQueue()
        
        queue.add_teleportation(
            from_pos=(5, 5),
            to_pos=(10, 10),
            entity_name="Orc",
            intensity='medium'
        )
        
        assert len(queue.effects) == 1
        effect = queue.effects[0]
        assert effect.entity_name == "Orc"
        assert effect.from_pos == (5, 5)
        assert effect.to_pos == (10, 10)
    
    def test_add_multiple_effects(self):
        """Add multiple effects to queue."""
        queue = PortalEffectQueue()
        
        queue.add_teleportation((5, 5), (10, 10), "Orc", 'medium')
        queue.add_teleportation((15, 15), (20, 20), "Goblin", 'low')
        queue.add_teleportation((25, 25), (30, 30), "Player", 'high')
        
        assert len(queue.effects) == 3
    
    def test_effect_queue_respects_max(self):
        """Queue doesn't exceed max_effects."""
        queue = PortalEffectQueue()
        queue.max_effects = 3
        
        # Add 5 effects
        for i in range(5):
            queue.add_teleportation((i, i), (i+5, i+5), f"Entity{i}", 'low')
        
        # Should only have 3 (oldest 2 removed)
        assert len(queue.effects) == 3
    
    def test_clear_effects(self):
        """Clear all effects from queue."""
        queue = PortalEffectQueue()
        queue.add_teleportation((5, 5), (10, 10), "Orc", 'medium')
        queue.add_teleportation((15, 15), (20, 20), "Goblin", 'low')
        
        assert len(queue.effects) == 2
        
        queue.clear()
        
        assert len(queue.effects) == 0
    
    def test_get_effects_for_position(self):
        """Get effects at specific position."""
        queue = PortalEffectQueue()
        
        queue.add_teleportation((5, 5), (10, 10), "Orc", 'medium')
        queue.add_teleportation((5, 5), (15, 15), "Goblin", 'low')
        queue.add_teleportation((20, 20), (25, 25), "Player", 'high')
        
        # Get effects at (5, 5) - should get 2
        effects_at_5_5 = queue.get_effects_for_position(5, 5)
        assert len(effects_at_5_5) == 2
        
        # Get effects at (10, 10) - should get 1 (Orc destination)
        effects_at_10_10 = queue.get_effects_for_position(10, 10)
        assert len(effects_at_10_10) == 1
        
        # Get effects at (20, 20) - should get 1 (Player source)
        effects_at_20_20 = queue.get_effects_for_position(20, 20)
        assert len(effects_at_20_20) == 1
    
    def test_get_global_effect_queue(self):
        """Get global effect queue singleton."""
        queue1 = get_portal_effect_queue()
        queue2 = get_portal_effect_queue()
        
        # Should be same instance
        assert queue1 is queue2
    
    def test_global_queue_persists_effects(self):
        """Global queue maintains state across calls."""
        global_queue = get_portal_effect_queue()
        global_queue.clear()
        
        global_queue.add_teleportation((5, 5), (10, 10), "Orc", 'medium')
        
        # Get queue again
        queue_again = get_portal_effect_queue()
        assert len(queue_again.effects) == 1


class TestPortalVFXIntegration:
    """Integration tests for visual effects with portal system."""
    
    def test_player_teleportation_has_visual_effect(self):
        """Player teleportation creates appropriate visual effect."""
        from services.portal_visual_effects import PortalVFXSystem
        
        # Create player teleportation message
        msg = PortalVFXSystem.create_teleportation_message(
            "Player",
            is_player=True
        )
        
        # Should have visual feedback
        assert msg['effect_type'] == 'teleport_player'
        assert msg['intensity'] == 'high'
    
    def test_monster_teleportation_has_visual_effect(self):
        """Monster teleportation creates appropriate visual effect."""
        from services.portal_visual_effects import PortalVFXSystem
        
        # Create monster teleportation message
        msg = PortalVFXSystem.create_teleportation_message(
            "Orc",
            is_monster=True
        )
        
        # Should have visual feedback
        assert msg['effect_type'] == 'teleport_monster'
        assert msg['intensity'] == 'medium'


class TestEffectQueueBehavior:
    """Test effect queue behavior under various conditions."""
    
    def test_effects_track_source_and_destination(self):
        """Effects correctly track source and destination positions."""
        queue = PortalEffectQueue()
        
        queue.add_teleportation((5, 5), (15, 15), "Orc", 'medium')
        
        effect = queue.effects[0]
        
        # Can query by either position
        effects_from_source = queue.get_effects_for_position(5, 5)
        effects_from_dest = queue.get_effects_for_position(15, 15)
        
        assert len(effects_from_source) == 1
        assert len(effects_from_dest) == 1
        assert effects_from_source[0] is effects_from_dest[0]
    
    def test_effect_intensity_colors_gradient(self):
        """Effect intensities create color gradient."""
        low_effect = TeleportationEffect((0, 0), (1, 1), "Low", 'low')
        mid_effect = TeleportationEffect((0, 0), (1, 1), "Mid", 'medium')
        high_effect = TeleportationEffect((0, 0), (1, 1), "High", 'high')
        
        low_color = low_effect.get_flash_color()
        mid_color = mid_effect.get_flash_color()
        high_color = high_effect.get_flash_color()
        
        # Colors should increase in brightness
        low_brightness = sum(low_color) / 3
        mid_brightness = sum(mid_color) / 3
        high_brightness = sum(high_color) / 3
        
        assert low_brightness < mid_brightness < high_brightness

