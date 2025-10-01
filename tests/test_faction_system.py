"""Tests for the faction system and monster-vs-monster combat."""

import pytest
from unittest.mock import Mock, patch

from components.faction import (
    Faction, 
    get_faction_from_string, 
    are_factions_hostile, 
    get_target_priority
)
from components.ai import SlimeAI
from components.status_effects import StatusEffectManager, InvisibilityEffect
from entity import Entity
from components.fighter import Fighter
from render_functions import RenderOrder


class TestFactionSystem:
    """Test the faction system functionality."""
    
    def test_faction_enum_values(self):
        """Test that faction enum has expected values."""
        assert Faction.PLAYER.value == "player"
        assert Faction.NEUTRAL.value == "neutral"
        assert Faction.HOSTILE_ALL.value == "hostile_all"
    
    def test_get_faction_from_string(self):
        """Test faction string conversion."""
        assert get_faction_from_string("player") == Faction.PLAYER
        assert get_faction_from_string("neutral") == Faction.NEUTRAL
        assert get_faction_from_string("hostile_all") == Faction.HOSTILE_ALL
        
        # Test invalid faction defaults to NEUTRAL
        assert get_faction_from_string("invalid") == Faction.NEUTRAL
        assert get_faction_from_string("") == Faction.NEUTRAL
    
    def test_faction_hostility_rules(self):
        """Test faction hostility relationships."""
        # Same faction entities don't attack each other
        assert not are_factions_hostile(Faction.PLAYER, Faction.PLAYER)
        assert not are_factions_hostile(Faction.NEUTRAL, Faction.NEUTRAL)
        assert not are_factions_hostile(Faction.HOSTILE_ALL, Faction.HOSTILE_ALL)
        
        # HOSTILE_ALL attacks everyone except other HOSTILE_ALL
        assert are_factions_hostile(Faction.HOSTILE_ALL, Faction.PLAYER)
        assert are_factions_hostile(Faction.HOSTILE_ALL, Faction.NEUTRAL)
        assert not are_factions_hostile(Faction.HOSTILE_ALL, Faction.HOSTILE_ALL)
        
        # NEUTRAL only attacks PLAYER
        assert are_factions_hostile(Faction.NEUTRAL, Faction.PLAYER)
        assert not are_factions_hostile(Faction.NEUTRAL, Faction.NEUTRAL)
        assert are_factions_hostile(Faction.NEUTRAL, Faction.HOSTILE_ALL)  # Slimes attack neutrals
        
        # PLAYER is hostile to all non-PLAYER factions
        assert are_factions_hostile(Faction.PLAYER, Faction.NEUTRAL)
        assert are_factions_hostile(Faction.PLAYER, Faction.HOSTILE_ALL)
        assert not are_factions_hostile(Faction.PLAYER, Faction.PLAYER)
    
    def test_target_priority(self):
        """Test targeting priority system."""
        # Player always gets highest priority
        assert get_target_priority(Faction.HOSTILE_ALL, Faction.PLAYER) == 10
        assert get_target_priority(Faction.NEUTRAL, Faction.PLAYER) == 10
        
        # Other hostile targets get lower priority
        assert get_target_priority(Faction.HOSTILE_ALL, Faction.NEUTRAL) == 5
        
        # Non-hostile targets get no priority
        assert get_target_priority(Faction.NEUTRAL, Faction.NEUTRAL) == 0
        assert get_target_priority(Faction.HOSTILE_ALL, Faction.HOSTILE_ALL) == 0


class TestSlimeAI:
    """Test the SlimeAI behavior."""
    
    def setup_method(self):
        """Set up test entities."""
        # Create slime with HOSTILE_ALL faction
        self.slime = Entity(
            x=5, y=5, char='s', color=(0, 255, 0), name='Slime',
            blocks=True, render_order=RenderOrder.ACTOR, faction=Faction.HOSTILE_ALL,
            fighter=Fighter(hp=15, defense=0, power=0, xp=25, damage_min=1, damage_max=3)
        )
        self.slime_ai = SlimeAI()
        self.slime.ai = self.slime_ai
        self.slime_ai.owner = self.slime
        
        # Create player
        self.player = Entity(
            x=3, y=3, char='@', color=(255, 255, 255), name='Player',
            blocks=True, render_order=RenderOrder.ACTOR, faction=Faction.PLAYER,
            fighter=Fighter(hp=100, defense=1, power=0, xp=0, damage_min=3, damage_max=4)
        )
        
        # Create orc (neutral faction)
        self.orc = Entity(
            x=7, y=7, char='o', color=(63, 127, 63), name='Orc',
            blocks=True, render_order=RenderOrder.ACTOR, faction=Faction.NEUTRAL,
            fighter=Fighter(hp=20, defense=0, power=0, xp=35, damage_min=4, damage_max=6)
        )
        
        # Mock FOV map
        self.fov_map = Mock()
        self.game_map = Mock()
        self.entities = [self.slime, self.player, self.orc]
    
    def test_slime_can_see_visible_targets(self):
        """Test that slime AI can see visible targets."""
        # Mock FOV to return True for visible entities
        with patch('components.ai.map_is_in_fov', return_value=True):
            assert self.slime_ai._can_see_target(self.player, self.fov_map)
            assert self.slime_ai._can_see_target(self.orc, self.fov_map)
    
    def test_slime_cannot_see_invisible_targets(self):
        """Test that slime AI cannot see invisible targets."""
        # Make player invisible
        self.player.invisible = True
        
        with patch('components.ai.map_is_in_fov', return_value=True):
            assert not self.slime_ai._can_see_target(self.player, self.fov_map)
            # Orc should still be visible
            assert self.slime_ai._can_see_target(self.orc, self.fov_map)
    
    def test_slime_hostility_to_factions(self):
        """Test that slime is hostile to correct factions."""
        assert self.slime_ai._is_hostile_to(self.player)  # PLAYER
        assert self.slime_ai._is_hostile_to(self.orc)     # NEUTRAL
        
        # Create another slime - should not be hostile
        other_slime = Entity(
            x=1, y=1, char='s', color=(0, 255, 0), name='Other Slime',
            faction=Faction.HOSTILE_ALL
        )
        assert not self.slime_ai._is_hostile_to(other_slime)
    
    def test_slime_target_prioritization(self):
        """Test that slime prioritizes player over other monsters."""
        with patch('components.ai.map_is_in_fov', return_value=True):
            # Both player and orc are visible and at same distance
            self.player.x, self.player.y = 4, 5  # Distance 1 from slime
            self.orc.x, self.orc.y = 6, 5        # Distance 1 from slime
            
            best_target = self.slime_ai._find_best_target(self.entities, self.fov_map)
            
            # Should prioritize player due to higher priority
            assert best_target == self.player
    
    def test_slime_targets_closest_when_same_priority(self):
        """Test that slime targets closest entity when priorities are equal."""
        # Create two orcs at different distances
        orc1 = Entity(
            x=4, y=5, char='o', color=(63, 127, 63), name='Close Orc',
            faction=Faction.NEUTRAL, fighter=Fighter(hp=20, defense=0, power=0, xp=35)
        )
        orc2 = Entity(
            x=8, y=8, char='o', color=(63, 127, 63), name='Far Orc',
            faction=Faction.NEUTRAL, fighter=Fighter(hp=20, defense=0, power=0, xp=35)
        )
        
        # Remove player to test orc prioritization
        entities_no_player = [self.slime, orc1, orc2]
        
        with patch('components.ai.map_is_in_fov', return_value=True):
            best_target = self.slime_ai._find_best_target(entities_no_player, self.fov_map)
            
            # Should target closer orc
            assert best_target == orc1
    
    def test_slime_no_target_when_none_visible(self):
        """Test that slime finds no target when none are visible."""
        with patch('components.ai.map_is_in_fov', return_value=False):
            best_target = self.slime_ai._find_best_target(self.entities, self.fov_map)
            assert best_target is None
    
    def test_slime_take_turn_movement(self):
        """Test that slime moves towards distant targets."""
        # Place target far away
        self.player.x, self.player.y = 10, 10
        
        with patch('components.ai.map_is_in_fov', return_value=True):
            with patch.object(self.slime, 'move_astar') as mock_move:
                results = self.slime_ai.take_turn(self.player, self.fov_map, self.game_map, self.entities)
                
                # Should attempt to move towards player
                mock_move.assert_called_once_with(self.player, self.entities, self.game_map)
    
    def test_slime_take_turn_attack(self):
        """Test that slime attacks adjacent targets."""
        # Place target adjacent
        self.player.x, self.player.y = 6, 5  # Distance 1 from slime at (5,5)
        
        with patch('components.ai.map_is_in_fov', return_value=True):
            with patch.object(self.slime.fighter, 'attack') as mock_attack:
                mock_attack.return_value = [{'message': 'Attack!'}]
                
                results = self.slime_ai.take_turn(self.player, self.fov_map, self.game_map, self.entities)
                
                # Should attack the player
                mock_attack.assert_called_once_with(self.player)
                assert len(results) == 1


class TestStatusEffects:
    """Test the status effect system."""
    
    def setup_method(self):
        """Set up test entity."""
        self.entity = Entity(
            x=5, y=5, char='@', color=(255, 255, 255), name='Test Entity',
            faction=Faction.PLAYER
        )
    
    def test_status_effect_manager_creation(self):
        """Test that status effect manager is created on demand."""
        assert self.entity.status_effects is None
        
        manager = self.entity.get_status_effect_manager()
        assert manager is not None
        assert isinstance(manager, StatusEffectManager)
        assert self.entity.status_effects == manager
    
    def test_invisibility_effect_application(self):
        """Test applying invisibility effect."""
        invisibility = InvisibilityEffect(duration=5, owner=self.entity)
        
        results = self.entity.add_status_effect(invisibility)
        
        assert self.entity.invisible is True
        assert self.entity.has_status_effect("invisibility")
        assert len(results) == 1  # Should have application message
        assert "becomes invisible" in results[0]['message'].text
    
    def test_invisibility_effect_removal(self):
        """Test removing invisibility effect."""
        invisibility = InvisibilityEffect(duration=1, owner=self.entity)
        self.entity.add_status_effect(invisibility)
        
        # Process turn end to expire effect
        results = self.entity.process_status_effects_turn_end()
        
        assert self.entity.invisible is False
        assert not self.entity.has_status_effect("invisibility")
        assert len(results) == 1  # Should have removal message
        assert "no longer invisible" in results[0]['message'].text
    
    def test_invisibility_effect_breaking(self):
        """Test breaking invisibility early."""
        invisibility = InvisibilityEffect(duration=10, owner=self.entity)
        self.entity.add_status_effect(invisibility)
        
        # Break invisibility
        results = invisibility.break_invisibility()
        
        assert len(results) == 1
        assert "no longer invisible" in results[0]['message'].text
        assert invisibility.duration == 0  # Should be expired
    
    def test_status_effect_replacement(self):
        """Test that adding same effect type replaces existing."""
        invisibility1 = InvisibilityEffect(duration=5, owner=self.entity)
        invisibility2 = InvisibilityEffect(duration=10, owner=self.entity)
        
        self.entity.add_status_effect(invisibility1)
        self.entity.add_status_effect(invisibility2)
        
        # Should only have one invisibility effect
        manager = self.entity.get_status_effect_manager()
        invisibility_effects = [e for e in manager.active_effects.values() if e.name == "invisibility"]
        assert len(invisibility_effects) == 1
        assert invisibility_effects[0].duration == 10  # Should be the newer one


class TestEntityFactionIntegration:
    """Test faction integration with Entity class."""
    
    def test_entity_default_faction(self):
        """Test that entities get default NEUTRAL faction."""
        entity = Entity(x=0, y=0, char='x', color=(255, 255, 255), name='Test')
        assert entity.faction == Faction.NEUTRAL
    
    def test_entity_explicit_faction(self):
        """Test setting explicit faction on entity."""
        entity = Entity(
            x=0, y=0, char='x', color=(255, 255, 255), name='Test',
            faction=Faction.PLAYER
        )
        assert entity.faction == Faction.PLAYER
    
    def test_player_creation_has_player_faction(self):
        """Test that player creation sets PLAYER faction."""
        from components.inventory import Inventory
        from components.equipment import Equipment
        from components.level import Level
        
        fighter = Fighter(hp=100, defense=1, power=0, xp=0)
        inventory = Inventory(capacity=26)
        equipment = Equipment()
        level = Level()
        
        player = Entity.create_player(0, 0, fighter, inventory, level, equipment)
        assert player.faction == Faction.PLAYER
        assert player.name == "Player"
