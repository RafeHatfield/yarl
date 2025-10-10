"""Tests for Boss component."""

import pytest
from components.boss import Boss, create_dragon_lord_boss, create_demon_king_boss


class TestBossComponent:
    """Tests for basic Boss component functionality."""
    
    def test_boss_creation(self):
        """Test creating a boss component."""
        boss = Boss(boss_name="Test Boss")
        assert boss.boss_name == "Test Boss"
        assert boss.phase == 0
        assert boss.max_phases == 1
        assert boss.enrage_threshold == 0.5
        assert not boss.is_enraged
        assert not boss.defeated
    
    def test_boss_with_custom_values(self):
        """Test boss with custom configuration."""
        boss = Boss(
            boss_name="Custom Boss",
            boss_type="undead",
            max_phases=3,
            enrage_threshold=0.3,
            enrage_damage_multiplier=2.0
        )
        assert boss.boss_name == "Custom Boss"
        assert boss.boss_type == "undead"
        assert boss.max_phases == 3
        assert boss.enrage_threshold == 0.3
        assert boss.enrage_damage_multiplier == 2.0
    
    def test_enrage_trigger(self):
        """Test enrage mechanic triggers correctly."""
        boss = Boss(boss_name="Test", enrage_threshold=0.5)
        
        # Should not enrage at 60% HP
        just_enraged = boss.check_enrage(60, 100)
        assert not just_enraged
        assert not boss.is_enraged
        
        # Should enrage at 50% HP
        just_enraged = boss.check_enrage(50, 100)
        assert just_enraged
        assert boss.is_enraged
        
        # Should not trigger again
        just_enraged = boss.check_enrage(40, 100)
        assert not just_enraged
        assert boss.is_enraged
    
    def test_damage_multiplier(self):
        """Test damage multiplier changes with enrage."""
        boss = Boss(boss_name="Test", enrage_damage_multiplier=1.5)
        
        # Normal damage multiplier
        assert boss.get_damage_multiplier() == 1.0
        
        # Enrage
        boss.check_enrage(40, 100)
        assert boss.is_enraged
        assert boss.get_damage_multiplier() == 1.5
    
    def test_phase_advancement(self):
        """Test advancing combat phases."""
        boss = Boss(boss_name="Test", max_phases=3)
        
        assert boss.phase == 0
        
        # Advance to phase 1
        advanced = boss.advance_phase()
        assert advanced
        assert boss.phase == 1
        
        # Advance to phase 2
        advanced = boss.advance_phase()
        assert advanced
        assert boss.phase == 2
        
        # Cannot advance beyond max
        advanced = boss.advance_phase()
        assert not advanced
        assert boss.phase == 2


class TestBossDialogue:
    """Tests for boss dialogue system."""
    
    def test_default_dialogue(self):
        """Test boss has default dialogue."""
        boss = Boss(boss_name="Test Boss")
        
        spawn_line = boss.get_dialogue("spawn")
        assert spawn_line is not None
        assert "Test Boss" in spawn_line
    
    def test_custom_dialogue(self):
        """Test boss with custom dialogue."""
        boss = Boss(
            boss_name="Test",
            dialogue={
                "spawn": ["Hello!", "Greetings!"],
                "hit": ["Ouch!"],
                "death": ["Farewell..."]
            }
        )
        
        # Should return one of spawn lines
        spawn = boss.get_dialogue("spawn")
        assert spawn in ["Hello!", "Greetings!"]
        
        # Specific line
        hit = boss.get_dialogue("hit", use_random=False)
        assert hit == "Ouch!"
    
    def test_dialogue_tracking(self):
        """Test tracking used dialogue."""
        boss = Boss(boss_name="Test")
        
        assert not boss.has_used_dialogue("spawn")
        
        boss.mark_dialogue_used("spawn")
        assert boss.has_used_dialogue("spawn")
        
        # Other dialogue not marked
        assert not boss.has_used_dialogue("hit")
    
    def test_missing_dialogue(self):
        """Test getting dialogue for nonexistent trigger."""
        boss = Boss(boss_name="Test")
        
        result = boss.get_dialogue("nonexistent")
        assert result is None


class TestBossStatusImmunities:
    """Tests for boss status effect immunity."""
    
    def test_default_immunities(self):
        """Test bosses have default immunities."""
        boss = Boss(boss_name="Test")
        
        # Default immunities
        assert boss.is_immune_to("confusion")
        assert boss.is_immune_to("slow")
        
        # Not immune to everything
        assert not boss.is_immune_to("fire")
    
    def test_custom_immunities(self):
        """Test boss with custom immunities."""
        boss = Boss(
            boss_name="Fire Dragon",
            status_immunities=["fire", "burn", "confusion"]
        )
        
        assert boss.is_immune_to("fire")
        assert boss.is_immune_to("burn")
        assert boss.is_immune_to("confusion")
        assert not boss.is_immune_to("poison")
    
    def test_immunity_case_insensitive(self):
        """Test immunity checks are case-insensitive."""
        boss = Boss(boss_name="Test", status_immunities=["Fire", "POISON"])
        
        assert boss.is_immune_to("fire")
        assert boss.is_immune_to("FIRE")
        assert boss.is_immune_to("poison")
        assert boss.is_immune_to("Poison")


class TestBossPrefabs:
    """Tests for prefabricated boss configurations."""
    
    def test_dragon_lord_creation(self):
        """Test Dragon Lord boss configuration."""
        dragon = create_dragon_lord_boss()
        
        assert dragon.boss_name == "Dragon Lord"
        assert dragon.boss_type == "dragon"
        assert dragon.enrage_threshold == 0.5
        assert dragon.is_immune_to("fire")
        assert dragon.is_immune_to("confusion")
        
        # Check dialogue exists
        assert "spawn" in dragon.dialogue
        assert "enrage" in dragon.dialogue
        assert "death" in dragon.dialogue
        assert len(dragon.dialogue["spawn"]) > 0
    
    def test_demon_king_creation(self):
        """Test Demon King boss configuration."""
        demon = create_demon_king_boss()
        
        assert demon.boss_name == "Demon King"
        assert demon.boss_type == "demon"
        assert demon.enrage_threshold == 0.4  # Enrages earlier
        assert demon.enrage_damage_multiplier == 1.75  # More aggressive
        assert demon.is_immune_to("curse")
        assert demon.is_immune_to("poison")
        
        # Check dialogue exists
        assert "spawn" in demon.dialogue
        assert len(demon.dialogue["death"]) > 0


class TestBossDefeat:
    """Tests for boss defeat tracking."""
    
    def test_mark_defeated(self):
        """Test marking boss as defeated."""
        boss = Boss(boss_name="Test")
        
        assert not boss.defeated
        
        boss.mark_defeated()
        assert boss.defeated


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

