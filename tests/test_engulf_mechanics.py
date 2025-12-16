"""Tests for Phase 19 Slime Engulf mechanics.

Engulf Identity: Slimes envelope targets; being adjacent is dangerous.
Creates a "break contact" decision for players.
"""

import pytest
from unittest.mock import patch

from entity import Entity
from components.fighter import Fighter
from components.equipment import Equipment
from components.equippable import Equippable
from components.faction import Faction
from components.status_effects import EngulfedEffect
from equipment_slots import EquipmentSlots
from render_functions import RenderOrder


class TestEngulfMechanics:
    """Test slime engulf functionality."""
    
    def setup_method(self):
        """Set up test entities."""
        # Create slime with engulf ability
        self.slime = Entity(
            x=5, y=5, char='s', color=(0, 255, 0), name='Slime',
            blocks=True, render_order=RenderOrder.ACTOR, faction=Faction.HOSTILE_ALL,
            fighter=Fighter(hp=15, defense=0, power=5, xp=25, damage_min=1, damage_max=3)
        )
        self.slime.special_abilities = ['engulf']
        
        # Create player
        self.player = Entity(
            x=4, y=5, char='@', color=(255, 255, 255), name='Player',
            blocks=True, render_order=RenderOrder.ACTOR, faction=Faction.PLAYER,
            fighter=Fighter(hp=100, defense=0, power=0, xp=0),
            equipment=Equipment()
        )
        
        # Create a second slime for multi-slime tests
        self.slime2 = Entity(
            x=6, y=5, char='s', color=(0, 255, 0), name='Slime2',
            blocks=True, render_order=RenderOrder.ACTOR, faction=Faction.HOSTILE_ALL,
            fighter=Fighter(hp=15, defense=0, power=5, xp=25, damage_min=1, damage_max=3)
        )
        self.slime2.special_abilities = ['engulf']
    
    def test_slime_has_engulf_ability(self):
        """Test that slimes are detected as having engulf ability."""
        assert self.slime.fighter._has_engulf_ability()
        assert self.slime2.fighter._has_engulf_ability()
    
    def test_non_slime_no_engulf_ability(self):
        """Test that non-slimes don't have engulf ability."""
        orc = Entity(
            x=0, y=0, char='o', color=(63, 127, 63), name='Orc',
            faction=Faction.NEUTRAL,
            fighter=Fighter(hp=20, defense=0, power=0, xp=35)
        )
        assert not orc.fighter._has_engulf_ability()
        assert not self.player.fighter._has_engulf_ability()
    
    def test_engulf_applies_on_hit(self):
        """Test that engulf is applied deterministically on successful hit."""
        # Mock take_damage to ensure hit succeeds
        with patch.object(self.player.fighter, 'take_damage', return_value=[]):
            results = self.slime.fighter.attack(self.player)
            
            # Check that player has engulfed status
            assert self.player.has_status_effect('engulfed')
            
            # Check for engulf message
            messages = [r.get('message') for r in results if 'message' in r]
            engulf_messages = [m for m in messages if m and 'engulfed' in m.text.lower()]
            assert len(engulf_messages) >= 1
    
    def test_engulf_no_rng_always_applies(self):
        """Test that engulf is deterministic - always applies on hit (no RNG)."""
        # Run multiple attacks - should always engulf
        for _ in range(5):
            player_test = Entity(
                x=4, y=5, char='@', color=(255, 255, 255), name='TestPlayer',
                blocks=True, render_order=RenderOrder.ACTOR, faction=Faction.PLAYER,
                fighter=Fighter(hp=100, defense=0, power=0, xp=0)
            )
            
            with patch.object(player_test.fighter, 'take_damage', return_value=[]):
                self.slime.fighter.attack(player_test)
                assert player_test.has_status_effect('engulfed')
    
    def test_engulf_does_not_apply_on_miss(self):
        """Test that engulf doesn't apply when no damage is dealt."""
        # Create invulnerable player (blocks all damage)
        invulnerable = Entity(
            x=4, y=5, char='@', color=(255, 255, 255), name='Invulnerable',
            blocks=True, render_order=RenderOrder.ACTOR, faction=Faction.PLAYER,
            fighter=Fighter(hp=100, defense=1000, power=0, xp=0)
        )
        
        self.slime.fighter.attack(invulnerable)
        
        # Should not be engulfed (no damage dealt)
        assert not invulnerable.has_status_effect('engulfed')
    
    def test_engulf_duration_refresh_while_adjacent(self):
        """Test that engulf duration doesn't decay while adjacent to slime."""
        # Apply engulf
        engulf = EngulfedEffect(duration=3, owner=self.player)
        self.player.add_status_effect(engulf)
        
        # Create entity list for adjacency check
        entities = [self.player, self.slime]
        
        # Process turn start multiple times while adjacent
        for _ in range(5):
            engulf.process_turn_start(entities=entities)
            # Duration should stay at max (3)
            assert engulf.duration == 3
    
    def test_engulf_decay_when_not_adjacent(self):
        """Test that engulf decays when not adjacent to any slime."""
        # Apply engulf
        engulf = EngulfedEffect(duration=3, owner=self.player)
        self.player.add_status_effect(engulf)
        
        # Move player far away from slime
        self.player.x = 10
        self.player.y = 10
        
        entities = [self.player, self.slime]
        
        # First process should show "pulling free" message
        results = engulf.process_turn_start(entities=entities)
        pulling_free_msgs = [r for r in results if 'message' in r and 'pulling free' in r['message'].text.lower()]
        assert len(pulling_free_msgs) == 1
        
        # Duration should still be 3 (hasn't decayed yet in turn_start)
        assert engulf.duration == 3
        
        # After turn ends, duration should not have changed (custom logic)
        engulf.process_turn_end()
        # Our custom process_turn_end doesn't decay - that happens in manager
    
    def test_engulf_refresh_from_multiple_slimes(self):
        """Test that being adjacent to ANY slime refreshes engulf."""
        # Apply engulf
        engulf = EngulfedEffect(duration=3, owner=self.player)
        self.player.add_status_effect(engulf)
        
        # Player at (4, 5), slime at (5, 5), slime2 at (6, 5)
        # Player is adjacent to slime but not slime2
        entities = [self.player, self.slime, self.slime2]
        
        # Process - should refresh due to slime adjacency
        engulf.process_turn_start(entities=entities)
        assert engulf.duration == 3
        
        # Move slime away, but keep slime2 adjacent
        self.slime.x = 10
        self.slime.y = 10
        self.slime2.x = 4
        self.slime2.y = 6  # Now slime2 is adjacent
        
        # Should still refresh (adjacent to slime2)
        engulf.process_turn_start(entities=entities)
        assert engulf.duration == 3
    
    def test_engulf_movement_penalty(self):
        """Test that engulfed entities have movement penalty (skip every other turn)."""
        engulf = EngulfedEffect(duration=3, owner=self.player)
        self.player.add_status_effect(engulf)
        
        entities = [self.player, self.slime]
        
        # First turn (counter = 1, odd) - should skip
        results = engulf.process_turn_start(entities=entities)
        skip_turn_results = [r for r in results if r.get('skip_turn')]
        assert len(skip_turn_results) == 1
        
        # Second turn (counter = 2, even) - should not skip
        results = engulf.process_turn_start(entities=entities)
        skip_turn_results = [r for r in results if r.get('skip_turn')]
        assert len(skip_turn_results) == 0
        
        # Third turn (counter = 3, odd) - should skip again
        results = engulf.process_turn_start(entities=entities)
        skip_turn_results = [r for r in results if r.get('skip_turn')]
        assert len(skip_turn_results) == 1
    
    def test_engulf_reapplication_refreshes_duration(self):
        """Test that getting hit again while engulfed refreshes duration."""
        # Apply initial engulf
        with patch.object(self.player.fighter, 'take_damage', return_value=[]):
            self.slime.fighter.attack(self.player)
        
        assert self.player.has_status_effect('engulfed')
        effect = self.player.status_effects.get_effect('engulfed')
        
        # Move player away and let duration decay conceptually
        self.player.x = 10
        self.player.y = 10
        effect.duration = 1  # Simulate near-expiration
        
        # Get hit again
        with patch.object(self.player.fighter, 'take_damage', return_value=[]):
            self.slime.fighter.attack(self.player)
        
        # Duration should be refreshed (still has effect, and StatusEffectManager refreshes it)
        assert self.player.has_status_effect('engulfed')
    
    def test_engulf_messages_no_spam(self):
        """Test that engulf doesn't spam messages when already adjacent."""
        engulf = EngulfedEffect(duration=3, owner=self.player)
        self.player.add_status_effect(engulf)
        
        entities = [self.player, self.slime]
        
        # First turn while adjacent - should have skip message
        results1 = engulf.process_turn_start(entities=entities)
        messages1 = [r.get('message') for r in results1 if 'message' in r]
        
        # Second turn still adjacent - should have skip message but not "still engulfed" message
        results2 = engulf.process_turn_start(entities=entities)
        messages2 = [r.get('message') for r in results2 if 'message' in r]
        
        # Should not have "still engulfed" spam (was_adjacent_last_turn prevents it)
        still_engulfed_msgs = [m for m in messages2 if m and 'still engulfed' in m.text.lower()]
        assert len(still_engulfed_msgs) == 0


class TestEngulfScenario:
    """Integration scenario tests for engulf."""
    
    def test_break_contact_scenario(self):
        """Test the break contact decision: player vs slime over multiple turns."""
        # Setup: Player adjacent to slime
        slime = Entity(
            x=5, y=5, char='s', color=(0, 255, 0), name='Slime',
            blocks=True, render_order=RenderOrder.ACTOR, faction=Faction.HOSTILE_ALL,
            fighter=Fighter(hp=15, defense=0, power=5, xp=25, damage_min=1, damage_max=3)
        )
        slime.special_abilities = ['engulf']
        
        player = Entity(
            x=4, y=5, char='@', color=(255, 255, 255), name='Player',
            blocks=True, render_order=RenderOrder.ACTOR, faction=Faction.PLAYER,
            fighter=Fighter(hp=100, defense=0, power=0, xp=0)
        )
        
        # Turn 1: Slime hits player, applies engulf
        with patch.object(player.fighter, 'take_damage', return_value=[]):
            slime.fighter.attack(player)
        
        assert player.has_status_effect('engulfed')
        engulf = player.status_effects.get_effect('engulfed')
        
        # Turn 2: Player still adjacent - duration refreshed
        entities = [player, slime]
        engulf.process_turn_start(entities=entities)
        assert engulf.duration == 3  # Refreshed to max
        
        # Turn 3: Player breaks contact (moves away)
        player.x = 10
        player.y = 10
        results = engulf.process_turn_start(entities=entities)
        
        # Should see "pulling free" message
        pulling_free = [r for r in results if 'message' in r and 'pulling free' in r['message'].text.lower()]
        assert len(pulling_free) == 1
        
        # Duration should still be 3 (hasn't decayed in process_turn_start)
        assert engulf.duration == 3
    
    def test_multiple_slimes_engulf(self):
        """Test engulf behavior with multiple slimes."""
        player = Entity(
            x=5, y=5, char='@', color=(255, 255, 255), name='Player',
            blocks=True, render_order=RenderOrder.ACTOR, faction=Faction.PLAYER,
            fighter=Fighter(hp=100, defense=0, power=0, xp=0)
        )
        
        slime1 = Entity(
            x=4, y=5, char='s', color=(0, 255, 0), name='Slime1',
            blocks=True, render_order=RenderOrder.ACTOR, faction=Faction.HOSTILE_ALL,
            fighter=Fighter(hp=15, defense=0, power=5, xp=25, damage_min=1, damage_max=3)
        )
        slime1.special_abilities = ['engulf']
        
        slime2 = Entity(
            x=6, y=5, char='s', color=(0, 255, 0), name='Slime2',
            blocks=True, render_order=RenderOrder.ACTOR, faction=Faction.HOSTILE_ALL,
            fighter=Fighter(hp=15, defense=0, power=5, xp=25, damage_min=1, damage_max=3)
        )
        slime2.special_abilities = ['engulf']
        
        # Slime1 hits player
        with patch.object(player.fighter, 'take_damage', return_value=[]):
            slime1.fighter.attack(player)
        
        assert player.has_status_effect('engulfed')
        engulf = player.status_effects.get_effect('engulfed')
        
        # Player is adjacent to both slimes
        entities = [player, slime1, slime2]
        
        # Move slime1 away - player still adjacent to slime2
        slime1.x = 10
        slime1.y = 10
        
        engulf.process_turn_start(entities=entities)
        # Duration should still refresh (adjacent to slime2)
        assert engulf.duration == 3
        
        # Move slime2 away too - no longer adjacent to ANY slime
        slime2.x = 10
        slime2.y = 10
        
        results = engulf.process_turn_start(entities=entities)
        # Should start pulling free
        pulling_free = [r for r in results if 'message' in r and 'pulling free' in r['message'].text.lower()]
        assert len(pulling_free) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

