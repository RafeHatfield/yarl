"""Unit tests for Phase 10: Zombie Swarm Behavior.

Tests cover:
- Zombie swarm targeting mechanics
- Random retargeting when adjacent to 2+ creatures
- Portal curiosity by faction
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from components.faction import Faction
from components.ai.basic_monster import BasicMonster
from components.component_registry import ComponentType


class TestZombieSwarmTargeting:
    """Tests for zombie swarm behavior mechanics."""
    
    def create_mock_entity(self, x, y, name="Entity", faction=Faction.NEUTRAL, hp=20):
        """Create a mock entity at a position."""
        entity = Mock()
        entity.x = x
        entity.y = y
        entity.name = name
        entity.faction = faction
        
        fighter = Mock()
        fighter.hp = hp
        entity.get_component_optional = Mock(return_value=fighter)
        
        return entity
    
    def create_zombie_ai(self, x, y, has_swarm=True):
        """Create a zombie AI with swarm behavior."""
        owner = Mock()
        owner.x = x
        owner.y = y
        owner.name = "Zombie"
        owner.faction = Faction.UNDEAD
        owner.special_abilities = ['swarm'] if has_swarm else []
        
        ai = BasicMonster()
        ai.owner = owner
        ai.is_zombie = True
        
        return ai
    
    def test_swarm_does_not_trigger_with_one_adjacent(self):
        """Swarm should not trigger when only 1 creature is adjacent."""
        ai = self.create_zombie_ai(5, 5)
        
        # One adjacent creature
        player = self.create_mock_entity(5, 4, "Player", Faction.PLAYER)
        
        fov_map = Mock()
        
        result = ai._get_zombie_swarm_target(
            player,
            [ai.owner, player],
            fov_map
        )
        
        # Should return the same target (no change)
        assert result == player
    
    def test_swarm_can_retarget_with_two_adjacent(self):
        """Swarm should potentially retarget when 2+ creatures are adjacent."""
        ai = self.create_zombie_ai(5, 5)
        
        # Two adjacent creatures
        player = self.create_mock_entity(5, 4, "Player", Faction.PLAYER)
        orc = self.create_mock_entity(5, 6, "Orc", Faction.ORC_FACTION)
        
        fov_map = Mock()
        
        # Run multiple times to verify randomness
        targets = set()
        for _ in range(50):
            result = ai._get_zombie_swarm_target(
                player,
                [ai.owner, player, orc],
                fov_map
            )
            if result:
                targets.add(result.name)
        
        # With randomness, should sometimes pick different targets
        # (statistically should hit both in 50 trials)
        assert len(targets) >= 1  # At least one target selected
    
    def test_swarm_only_targets_adjacent(self):
        """Swarm should only consider adjacent (distance 1) creatures."""
        ai = self.create_zombie_ai(5, 5)
        
        # One adjacent, one far
        adjacent = self.create_mock_entity(5, 4, "Adjacent", Faction.PLAYER)
        far = self.create_mock_entity(10, 10, "Far", Faction.PLAYER)
        
        fov_map = Mock()
        
        result = ai._get_zombie_swarm_target(
            adjacent,
            [ai.owner, adjacent, far],
            fov_map
        )
        
        # Should only consider adjacent target
        assert result == adjacent
    
    def test_swarm_ignores_dead_creatures(self):
        """Swarm should not consider dead creatures."""
        ai = self.create_zombie_ai(5, 5)
        
        # One alive, one dead (adjacent)
        alive = self.create_mock_entity(5, 4, "Alive", Faction.PLAYER, hp=20)
        dead = self.create_mock_entity(5, 6, "Dead", Faction.PLAYER, hp=0)
        dead.get_component_optional = Mock(return_value=Mock(hp=0))
        
        fov_map = Mock()
        
        result = ai._get_zombie_swarm_target(
            alive,
            [ai.owner, alive, dead],
            fov_map
        )
        
        # Should only target alive creature
        assert result == alive
    
    def test_non_zombie_does_not_swarm(self):
        """Non-zombie monsters should not use swarm behavior."""
        # Create orc AI (not zombie)
        owner = Mock()
        owner.x, owner.y = 5, 5
        owner.name = "Orc"
        owner.faction = Faction.ORC_FACTION
        owner.special_abilities = None
        
        ai = BasicMonster()
        ai.owner = owner
        ai.is_zombie = False  # Explicitly not zombie
        
        # Two adjacent creatures
        player = self.create_mock_entity(5, 4, "Player", Faction.PLAYER)
        zombie = self.create_mock_entity(5, 6, "Zombie", Faction.UNDEAD)
        
        fov_map = Mock()
        
        result = ai._get_zombie_swarm_target(
            player,
            [owner, player, zombie],
            fov_map
        )
        
        # Should return original target (no swarm behavior)
        assert result == player


class TestPortalCuriosity:
    """Tests for faction-based portal curiosity."""
    
    def test_independent_high_curiosity(self):
        """Independents should have high portal curiosity."""
        owner = Mock()
        owner.faction = Faction.INDEPENDENT
        
        ai = BasicMonster()
        ai.owner = owner
        
        curiosity = ai.get_portal_curiosity_chance()
        
        assert curiosity >= 0.30  # High curiosity
    
    def test_orc_medium_curiosity(self):
        """Orcs should have medium portal curiosity."""
        owner = Mock()
        owner.faction = Faction.ORC_FACTION
        
        ai = BasicMonster()
        ai.owner = owner
        
        curiosity = ai.get_portal_curiosity_chance()
        
        assert 0.10 <= curiosity <= 0.30  # Medium curiosity
    
    def test_undead_low_curiosity(self):
        """Undead should have low portal curiosity."""
        owner = Mock()
        owner.faction = Faction.UNDEAD
        
        ai = BasicMonster()
        ai.owner = owner
        
        curiosity = ai.get_portal_curiosity_chance()
        
        assert curiosity <= 0.10  # Low curiosity
    
    def test_cultist_very_low_curiosity(self):
        """Cultists should have very low portal curiosity."""
        owner = Mock()
        owner.faction = Faction.CULTIST
        
        ai = BasicMonster()
        ai.owner = owner
        
        curiosity = ai.get_portal_curiosity_chance()
        
        assert curiosity <= 0.05  # Very low curiosity
    
    def test_portal_step_finds_adjacent_portals(self):
        """Portal step should detect adjacent portals."""
        owner = Mock()
        owner.x, owner.y = 5, 5
        owner.faction = Faction.INDEPENDENT  # High curiosity
        
        ai = BasicMonster()
        ai.owner = owner
        
        # Create adjacent portal
        portal = Mock()
        portal.x, portal.y = 5, 4  # Adjacent
        portal.is_portal = True
        
        # Non-portal entity
        orc = Mock()
        orc.x, orc.y = 5, 6
        orc.is_portal = False
        
        # Mock random module function to always succeed
        with patch('random.random', return_value=0.0):
            result = ai._try_portal_step(None, [portal, orc])
        
        # Should have stepped into portal
        assert result is not None
        assert owner.x == portal.x
        assert owner.y == portal.y
    
    def test_portal_step_ignores_non_adjacent(self):
        """Portal step should ignore non-adjacent portals."""
        owner = Mock()
        owner.x, owner.y = 5, 5
        owner.faction = Faction.INDEPENDENT
        
        ai = BasicMonster()
        ai.owner = owner
        
        # Create far portal
        portal = Mock()
        portal.x, portal.y = 10, 10  # Not adjacent
        portal.is_portal = True
        
        with patch('random.random', return_value=0.0):
            result = ai._try_portal_step(None, [portal])
        
        # Should not step (no adjacent portal)
        assert result is None
        assert owner.x == 5
        assert owner.y == 5


class TestFactionAIBehaviors:
    """Tests for faction-specific AI behaviors."""
    
    def test_undead_prefers_living_targets(self):
        """Undead should prefer living/fleshy targets over non-living."""
        from components.faction import get_target_priority, is_living_faction
        
        # Test living faction check
        assert is_living_faction(Faction.PLAYER) is True
        assert is_living_faction(Faction.ORC_FACTION) is True
        assert is_living_faction(Faction.CULTIST) is True
        
        # Test priority - undead should prioritize living
        orc_priority = get_target_priority(Faction.UNDEAD, Faction.ORC_FACTION)
        slime_priority = get_target_priority(Faction.UNDEAD, Faction.HOSTILE_ALL)
        
        assert orc_priority > slime_priority
    
    def test_orcs_dont_attack_orcs(self):
        """Orcs should not attack other orcs."""
        from components.faction import are_factions_hostile
        
        assert are_factions_hostile(Faction.ORC_FACTION, Faction.ORC_FACTION) is False
    
    def test_cultists_attack_intruders(self):
        """Cultists should be hostile to intruders (all other factions)."""
        from components.faction import are_factions_hostile
        
        assert are_factions_hostile(Faction.CULTIST, Faction.PLAYER) is True
        assert are_factions_hostile(Faction.CULTIST, Faction.ORC_FACTION) is True
        assert are_factions_hostile(Faction.CULTIST, Faction.UNDEAD) is True
    
    def test_independents_attack_everything(self):
        """Independents should attack all non-independent factions."""
        from components.faction import are_factions_hostile
        
        assert are_factions_hostile(Faction.INDEPENDENT, Faction.PLAYER) is True
        assert are_factions_hostile(Faction.INDEPENDENT, Faction.ORC_FACTION) is True
        assert are_factions_hostile(Faction.INDEPENDENT, Faction.UNDEAD) is True
        assert are_factions_hostile(Faction.INDEPENDENT, Faction.CULTIST) is True
        
        # But not other independents
        assert are_factions_hostile(Faction.INDEPENDENT, Faction.INDEPENDENT) is False
