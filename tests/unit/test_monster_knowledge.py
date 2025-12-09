"""Unit tests for Phase 11: Monster Knowledge & Investigation System.

Tests cover:
- MonsterKnowledgeEntry data structure
- MonsterKnowledgeSystem tracking methods
- Knowledge tier threshold calculations
- MonsterInfoView tier-gated info generation
- Integration with monster entities
"""

import pytest
from unittest.mock import Mock, MagicMock

from services.monster_knowledge import (
    MonsterKnowledgeEntry,
    MonsterKnowledgeSystem,
    MonsterInfoView,
    KnowledgeTier,
    get_knowledge_tier,
    get_monster_info_view,
    get_monster_knowledge_system,
    reset_monster_knowledge_system,
)
from balance.knowledge_config import (
    TIER_1_SEEN_COUNT,
    TIER_2_ENGAGED_COUNT,
    TIER_3_KILLED_COUNT,
    TRAIT_PLAGUE_CARRIER,
    TRAIT_SWARM_AI,
    TRAIT_FAST_ATTACKER,
    TRAIT_PORTAL_CURIOUS,
)
from components.component_registry import ComponentType
from components.faction import Faction


# ═══════════════════════════════════════════════════════════════════════════════
# TEST FIXTURES
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def knowledge_system():
    """Create a fresh MonsterKnowledgeSystem for testing."""
    system = MonsterKnowledgeSystem()
    return system


@pytest.fixture
def mock_orc():
    """Create a mock orc entity for testing."""
    monster = Mock()
    monster.name = "Orc"
    monster.char = 'o'
    monster.species_id = "orc"
    monster.faction = Faction.ORC_FACTION
    monster.tags = ["corporeal_flesh", "humanoid", "living"]
    monster.special_abilities = None
    monster.is_boss = False
    monster.speed_bonus = 1.0
    
    # Mock fighter component
    fighter = Mock()
    fighter.max_hp = 20
    fighter.base_defense = 0
    fighter.damage_min = 4
    fighter.damage_max = 6
    fighter.base_power = 0
    fighter.accuracy = 2
    fighter.evasion = 1
    monster.get_component_optional = Mock(return_value=fighter)
    
    return monster


@pytest.fixture
def mock_plague_zombie():
    """Create a mock plague zombie entity for testing."""
    monster = Mock()
    monster.name = "Plague Zombie"
    monster.char = 'Z'
    monster.species_id = "plague_zombie"
    monster.faction = Faction.UNDEAD
    monster.tags = ["corporeal_flesh", "undead", "mindless", "plague_carrier"]
    monster.special_abilities = ["swarm", "plague_attack"]
    monster.is_boss = False
    monster.speed_bonus = 0.5
    
    # Mock fighter component
    fighter = Mock()
    fighter.max_hp = 30
    fighter.base_defense = 0
    fighter.damage_min = 4
    fighter.damage_max = 7
    fighter.base_power = 0
    fighter.accuracy = 1
    fighter.evasion = 0
    monster.get_component_optional = Mock(return_value=fighter)
    
    return monster


@pytest.fixture
def mock_wraith():
    """Create a mock wraith entity (fast, evasive) for testing."""
    monster = Mock()
    monster.name = "Wraith"
    monster.char = 'W'
    monster.species_id = "wraith"
    monster.faction = Faction.UNDEAD
    monster.tags = ["incorporeal", "undead", "high_undead", "no_flesh"]
    monster.special_abilities = None
    monster.is_boss = False
    monster.speed_bonus = 2.0
    
    # Mock fighter component
    fighter = Mock()
    fighter.max_hp = 20
    fighter.base_defense = 4
    fighter.damage_min = 5
    fighter.damage_max = 9
    fighter.base_power = 3
    fighter.accuracy = 3
    fighter.evasion = 4
    monster.get_component_optional = Mock(return_value=fighter)
    
    return monster


# ═══════════════════════════════════════════════════════════════════════════════
# KNOWLEDGE ENTRY TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestMonsterKnowledgeEntry:
    """Tests for MonsterKnowledgeEntry data structure."""
    
    def test_entry_creation_defaults(self):
        """Entry should be created with correct default values."""
        entry = MonsterKnowledgeEntry(species_id="orc")
        
        assert entry.species_id == "orc"
        assert entry.seen_count == 0
        assert entry.engaged_count == 0
        assert entry.killed_count == 0
        assert entry.first_depth_seen is None
        assert entry.traits_discovered == set()
    
    def test_entry_creation_with_values(self):
        """Entry should accept custom values."""
        entry = MonsterKnowledgeEntry(
            species_id="zombie",
            seen_count=5,
            engaged_count=3,
            killed_count=2,
            first_depth_seen=3,
            traits_discovered={"swarm_ai", "plague_carrier"}
        )
        
        assert entry.species_id == "zombie"
        assert entry.seen_count == 5
        assert entry.engaged_count == 3
        assert entry.killed_count == 2
        assert entry.first_depth_seen == 3
        assert entry.traits_discovered == {"swarm_ai", "plague_carrier"}


# ═══════════════════════════════════════════════════════════════════════════════
# KNOWLEDGE SYSTEM TRACKING TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestMonsterKnowledgeSystem:
    """Tests for MonsterKnowledgeSystem tracking methods."""
    
    def test_register_seen_increments_count(self, knowledge_system, mock_orc):
        """register_seen should increment seen_count."""
        knowledge_system.register_seen(mock_orc)
        
        entry = knowledge_system.get_entry("orc")
        assert entry.seen_count == 1
    
    def test_register_seen_tracks_depth(self, knowledge_system, mock_orc):
        """register_seen should track first_depth_seen."""
        knowledge_system.register_seen(mock_orc, current_depth=5)
        
        entry = knowledge_system.get_entry("orc")
        assert entry.first_depth_seen == 5
    
    def test_register_seen_keeps_minimum_depth(self, knowledge_system, mock_orc):
        """register_seen should keep the minimum depth seen."""
        knowledge_system.register_seen(mock_orc, current_depth=5)
        knowledge_system.begin_update_cycle()  # Reset per-update tracking
        knowledge_system.register_seen(mock_orc, current_depth=3)
        knowledge_system.begin_update_cycle()
        knowledge_system.register_seen(mock_orc, current_depth=7)
        
        entry = knowledge_system.get_entry("orc")
        assert entry.first_depth_seen == 3
    
    def test_register_seen_dedupes_per_update(self, knowledge_system, mock_orc):
        """register_seen should only count once per update cycle per monster."""
        # Same monster seen multiple times in one update
        knowledge_system.register_seen(mock_orc)
        knowledge_system.register_seen(mock_orc)
        knowledge_system.register_seen(mock_orc)
        
        entry = knowledge_system.get_entry("orc")
        assert entry.seen_count == 1
        
        # After new update cycle, can be counted again
        knowledge_system.begin_update_cycle()
        knowledge_system.register_seen(mock_orc)
        
        entry = knowledge_system.get_entry("orc")
        assert entry.seen_count == 2
    
    def test_register_engaged_increments_count(self, knowledge_system, mock_orc):
        """register_engaged should increment engaged_count."""
        knowledge_system.register_engaged(mock_orc)
        knowledge_system.register_engaged(mock_orc)
        knowledge_system.register_engaged(mock_orc)
        
        entry = knowledge_system.get_entry("orc")
        assert entry.engaged_count == 3
    
    def test_register_engaged_also_sets_seen(self, knowledge_system, mock_orc):
        """register_engaged should also count as seen if not already."""
        knowledge_system.register_engaged(mock_orc)
        
        entry = knowledge_system.get_entry("orc")
        assert entry.seen_count >= 1
    
    def test_register_killed_increments_count(self, knowledge_system, mock_orc):
        """register_killed should increment killed_count."""
        knowledge_system.register_killed(mock_orc)
        knowledge_system.register_killed(mock_orc)
        
        entry = knowledge_system.get_entry("orc")
        assert entry.killed_count == 2
    
    def test_register_killed_also_sets_seen_and_engaged(self, knowledge_system, mock_orc):
        """register_killed should also count as seen and engaged."""
        knowledge_system.register_killed(mock_orc)
        
        entry = knowledge_system.get_entry("orc")
        assert entry.seen_count >= 1
        assert entry.engaged_count >= 1
    
    def test_register_trait_adds_to_set(self, knowledge_system, mock_orc):
        """register_trait should add trait to traits_discovered."""
        knowledge_system.register_trait(mock_orc, TRAIT_FAST_ATTACKER)
        
        entry = knowledge_system.get_entry("orc")
        assert TRAIT_FAST_ATTACKER in entry.traits_discovered
    
    def test_register_trait_dedupes(self, knowledge_system, mock_orc):
        """register_trait should not duplicate traits."""
        knowledge_system.register_trait(mock_orc, TRAIT_PLAGUE_CARRIER)
        knowledge_system.register_trait(mock_orc, TRAIT_PLAGUE_CARRIER)
        
        entry = knowledge_system.get_entry("orc")
        assert len(entry.traits_discovered) == 1
    
    def test_get_entry_returns_default_for_unknown(self, knowledge_system):
        """get_entry should return default entry for unknown species."""
        entry = knowledge_system.get_entry("unknown_monster")
        
        assert entry.species_id == "unknown_monster"
        assert entry.seen_count == 0
        assert entry.engaged_count == 0
        assert entry.killed_count == 0
    
    def test_reset_clears_all_entries(self, knowledge_system, mock_orc):
        """reset should clear all tracked knowledge."""
        knowledge_system.register_seen(mock_orc)
        knowledge_system.register_killed(mock_orc)
        knowledge_system.register_trait(mock_orc, TRAIT_SWARM_AI)
        
        knowledge_system.reset()
        
        entry = knowledge_system.get_entry("orc")
        assert entry.seen_count == 0
        assert entry.killed_count == 0
        assert len(entry.traits_discovered) == 0


# ═══════════════════════════════════════════════════════════════════════════════
# TIER THRESHOLD TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestKnowledgeTierThresholds:
    """Tests for knowledge tier threshold calculations."""
    
    def test_tier_0_when_never_seen(self):
        """Tier should be UNKNOWN when seen_count is 0."""
        entry = MonsterKnowledgeEntry(species_id="orc", seen_count=0)
        
        assert get_knowledge_tier(entry) == KnowledgeTier.UNKNOWN
    
    def test_tier_1_when_seen_once(self):
        """Tier should be OBSERVED when seen at least once."""
        entry = MonsterKnowledgeEntry(
            species_id="orc", 
            seen_count=TIER_1_SEEN_COUNT
        )
        
        assert get_knowledge_tier(entry) == KnowledgeTier.OBSERVED
    
    def test_tier_2_when_engaged_enough(self):
        """Tier should be BATTLED when engaged enough times."""
        entry = MonsterKnowledgeEntry(
            species_id="orc",
            seen_count=1,
            engaged_count=TIER_2_ENGAGED_COUNT
        )
        
        assert get_knowledge_tier(entry) == KnowledgeTier.BATTLED
    
    def test_tier_3_when_killed_enough(self):
        """Tier should be UNDERSTOOD when killed enough times."""
        entry = MonsterKnowledgeEntry(
            species_id="orc",
            seen_count=1,
            engaged_count=1,
            killed_count=TIER_3_KILLED_COUNT
        )
        
        assert get_knowledge_tier(entry) == KnowledgeTier.UNDERSTOOD
    
    def test_tier_3_when_major_trait_discovered(self):
        """Tier should be UNDERSTOOD when major trait is experienced."""
        entry = MonsterKnowledgeEntry(
            species_id="plague_zombie",
            seen_count=1,
            engaged_count=1,
            killed_count=0,
            traits_discovered={TRAIT_PLAGUE_CARRIER}
        )
        
        assert get_knowledge_tier(entry) == KnowledgeTier.UNDERSTOOD
    
    def test_tier_3_from_swarm_trait(self):
        """Tier should be UNDERSTOOD when swarm trait is experienced."""
        entry = MonsterKnowledgeEntry(
            species_id="zombie",
            seen_count=1,
            engaged_count=2,
            killed_count=2,
            traits_discovered={TRAIT_SWARM_AI}
        )
        
        assert get_knowledge_tier(entry) == KnowledgeTier.UNDERSTOOD


# ═══════════════════════════════════════════════════════════════════════════════
# MONSTER INFO VIEW TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestMonsterInfoView:
    """Tests for MonsterInfoView tier-gated info generation."""
    
    def test_tier_0_shows_only_name_and_glyph(self, knowledge_system, mock_orc):
        """Tier 0 should show only name and glyph."""
        # Don't register anything - monster is unknown
        info = get_monster_info_view(mock_orc, knowledge_system)
        
        assert info.name == "Orc"
        assert info.glyph == 'o'
        assert info.knowledge_tier == KnowledgeTier.UNKNOWN
        assert info.faction_label is None
        assert info.role_label is None
        assert info.durability_label is None
        assert info.damage_label is None
        assert len(info.special_warnings) == 0
        assert info.advice_line is None
    
    def test_tier_1_shows_faction_and_role(self, knowledge_system, mock_orc):
        """Tier 1 should show faction and role."""
        knowledge_system.register_seen(mock_orc)
        
        info = get_monster_info_view(mock_orc, knowledge_system)
        
        assert info.knowledge_tier == KnowledgeTier.OBSERVED
        assert info.faction_label is not None  # "Orc" faction
        # role_label may or may not be set depending on tags
    
    def test_tier_2_shows_combat_stats(self, knowledge_system, mock_orc):
        """Tier 2 should show durability, damage, accuracy, evasion labels."""
        # Register enough engagement for Tier 2
        for _ in range(TIER_2_ENGAGED_COUNT):
            knowledge_system.register_engaged(mock_orc)
        
        info = get_monster_info_view(mock_orc, knowledge_system)
        
        assert info.knowledge_tier == KnowledgeTier.BATTLED
        assert info.durability_label is not None
        assert info.damage_label is not None
        # accuracy/evasion labels may be None if average
    
    def test_tier_3_shows_warnings_and_advice(self, knowledge_system, mock_plague_zombie):
        """Tier 3 should show special warnings and advice."""
        # Register enough kills for Tier 3
        for _ in range(TIER_3_KILLED_COUNT):
            knowledge_system.register_killed(mock_plague_zombie)
        # Also register the plague trait
        knowledge_system.register_trait(mock_plague_zombie, TRAIT_PLAGUE_CARRIER)
        
        info = get_monster_info_view(mock_plague_zombie, knowledge_system)
        
        assert info.knowledge_tier == KnowledgeTier.UNDERSTOOD
        assert len(info.special_warnings) > 0
        # Should have plague warning
        plague_warnings = [w for w in info.special_warnings if "Plague" in w]
        assert len(plague_warnings) > 0
    
    def test_wraith_shows_speed_label(self, knowledge_system, mock_wraith):
        """Fast monster should show speed label at Tier 1+."""
        knowledge_system.register_seen(mock_wraith)
        
        info = get_monster_info_view(mock_wraith, knowledge_system)
        
        assert info.speed_label is not None
        # Wraith has speed_bonus 2.0, should be "fast" or "lightning fast"
        assert "fast" in info.speed_label.lower()
    
    def test_tier_3_advice_for_plague_carrier(self, knowledge_system, mock_plague_zombie):
        """Tier 3 should generate tactical advice for plague carriers."""
        knowledge_system.register_seen(mock_plague_zombie)
        knowledge_system.register_trait(mock_plague_zombie, TRAIT_PLAGUE_CARRIER)
        
        info = get_monster_info_view(mock_plague_zombie, knowledge_system)
        
        assert info.advice_line is not None
        # Advice should mention plague or cure
        assert "plague" in info.advice_line.lower() or "antidote" in info.advice_line.lower()


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestIntegration:
    """Integration-style tests for the knowledge system."""
    
    def test_full_progression_orc(self, knowledge_system, mock_orc):
        """Test full tier progression for an orc."""
        # Tier 0: Unknown
        info0 = get_monster_info_view(mock_orc, knowledge_system)
        assert info0.knowledge_tier == KnowledgeTier.UNKNOWN
        
        # Tier 1: See it
        knowledge_system.register_seen(mock_orc)
        info1 = get_monster_info_view(mock_orc, knowledge_system)
        assert info1.knowledge_tier == KnowledgeTier.OBSERVED
        assert info1.faction_label is not None
        
        # Tier 2: Fight it
        for _ in range(TIER_2_ENGAGED_COUNT):
            knowledge_system.register_engaged(mock_orc)
        info2 = get_monster_info_view(mock_orc, knowledge_system)
        assert info2.knowledge_tier == KnowledgeTier.BATTLED
        assert info2.durability_label is not None
        
        # Tier 3: Kill enough
        for _ in range(TIER_3_KILLED_COUNT):
            knowledge_system.register_killed(mock_orc)
        info3 = get_monster_info_view(mock_orc, knowledge_system)
        assert info3.knowledge_tier == KnowledgeTier.UNDERSTOOD
    
    def test_plague_zombie_with_all_traits(self, knowledge_system, mock_plague_zombie):
        """Test plague zombie with discovered plague and swarm traits."""
        # Get to Tier 3 via traits
        knowledge_system.register_seen(mock_plague_zombie)
        knowledge_system.register_engaged(mock_plague_zombie)
        knowledge_system.register_trait(mock_plague_zombie, TRAIT_PLAGUE_CARRIER)
        knowledge_system.register_trait(mock_plague_zombie, TRAIT_SWARM_AI)
        
        info = get_monster_info_view(mock_plague_zombie, knowledge_system)
        
        # Should be Tier 3 due to major trait
        assert info.knowledge_tier == KnowledgeTier.UNDERSTOOD
        
        # Should have faction label (Undead)
        assert info.faction_label is not None
        assert "undead" in info.faction_label.lower()
        
        # Should have warnings for both traits
        warning_text = " ".join(info.special_warnings).lower()
        assert "plague" in warning_text
        assert "swarm" in warning_text
        
        # Should have advice line
        assert info.advice_line is not None
    
    def test_singleton_access(self):
        """Test singleton accessor functions."""
        reset_monster_knowledge_system()
        
        system1 = get_monster_knowledge_system()
        system2 = get_monster_knowledge_system()
        
        assert system1 is system2
        
        # Register something and verify it persists
        monster = Mock()
        monster.name = "Test Monster"
        monster.species_id = "test_monster"
        
        system1.register_seen(monster)
        
        entry = system2.get_entry("test_monster")
        assert entry.seen_count == 1


# ═══════════════════════════════════════════════════════════════════════════════
# SPECIES ID TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestSpeciesIdExtraction:
    """Tests for species ID extraction from entities."""
    
    def test_uses_species_id_property(self, knowledge_system):
        """Should use entity's species_id if available."""
        monster = Mock()
        monster.name = "Orc Chieftain"
        monster.species_id = "orc_chieftain"
        
        knowledge_system.register_seen(monster)
        
        # Should use species_id, not name
        assert knowledge_system.get_entry("orc_chieftain").seen_count == 1
        assert knowledge_system.get_entry("orc chieftain").seen_count == 0
    
    def test_falls_back_to_name(self, knowledge_system):
        """Should fall back to normalized name if no species_id."""
        monster = Mock()
        monster.name = "Giant Spider"
        monster.species_id = None
        
        knowledge_system.register_seen(monster)
        
        # Should normalize name: lowercase, spaces to underscores
        assert knowledge_system.get_entry("giant_spider").seen_count == 1
