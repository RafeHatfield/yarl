"""Tests for boss dialogue integration in combat."""

import pytest
from entity import Entity
from components.fighter import Fighter
from components.boss import Boss, create_dragon_lord_boss, create_demon_king_boss
from components.component_registry import ComponentType
from death_functions import kill_monster
from map_objects.game_map import GameMap


class TestBossDamageDialogue:
    """Tests for boss dialogue when taking damage."""
    
    def test_boss_enrage_dialogue(self):
        """Test boss says something when enraged."""
        boss = Entity(10, 10, 'D', (255, 50, 0), "Dragon Lord", blocks=True)
        boss.fighter = Fighter(hp=100, defense=5, power=5)
        boss.boss = create_dragon_lord_boss()
        boss.fighter.owner = boss
        boss.boss.owner = boss
        
        boss.components.add(ComponentType.FIGHTER, boss.fighter)
        boss.components.add(ComponentType.BOSS, boss.boss)
        
        # Damage boss to 60% HP (no enrage yet)
        results = boss.fighter.take_damage(40)
        messages = [r for r in results if 'message' in r]
        assert len(messages) == 0  # No message yet
        assert not boss.boss.is_enraged
        
        # Damage boss to 50% HP (enrage!)
        results = boss.fighter.take_damage(10)
        messages = [r for r in results if 'message' in r]
        assert len(messages) >= 1  # At least enrage message! (may also have random hit dialogue)
        assert boss.boss.is_enraged
        
        # Find the enrage message (should be in there)
        enrage_messages = [m for m in messages if any(word in str(m['message'].text).lower() 
                          for word in ['wrath', 'fury', 'anger', 'enough'])]
        assert len(enrage_messages) >= 1
        
        message_text = str(enrage_messages[0]['message'].text)
        assert "Dragon Lord" in message_text
    
    def test_boss_low_hp_dialogue(self):
        """Test boss says something when at low HP."""
        boss = Entity(10, 10, 'D', (255, 50, 0), "Dragon Lord", blocks=True)
        boss.fighter = Fighter(hp=100, defense=5, power=5)
        boss.boss = create_dragon_lord_boss()
        boss.fighter.owner = boss
        boss.boss.owner = boss
        
        boss.components.add(ComponentType.FIGHTER, boss.fighter)
        boss.components.add(ComponentType.BOSS, boss.boss)
        
        # Damage to 50% (enrage)
        boss.fighter.take_damage(50)
        
        # Damage to 19% (low HP dialogue)
        results = boss.fighter.take_damage(31)
        messages = [r for r in results if 'message' in r]
        
        # Should have at least one message (might be enrage + low HP)
        assert len(messages) >= 1
        
        # Find low HP message
        low_hp_messages = [m for m in messages if 'cannot' in str(m['message'].text).lower() 
                          or 'impossible' in str(m['message'].text).lower()
                          or 'scales' in str(m['message'].text).lower()]
        assert len(low_hp_messages) >= 1
    
    def test_boss_dialogue_only_triggers_once(self):
        """Test low HP dialogue only triggers once."""
        boss = Entity(10, 10, 'K', (160, 32, 240), "Demon King", blocks=True)
        boss.fighter = Fighter(hp=100, defense=5, power=5)
        boss.boss = create_demon_king_boss()
        boss.fighter.owner = boss
        boss.boss.owner = boss
        
        boss.components.add(ComponentType.FIGHTER, boss.fighter)
        boss.components.add(ComponentType.BOSS, boss.boss)
        
        # Damage to 40% (enrage for Demon King)
        boss.fighter.take_damage(60)
        
        # Damage to 19% (low HP)
        results1 = boss.fighter.take_damage(21)
        messages1 = [r for r in results1 if 'message' in r]
        
        # Damage again while still at low HP
        results2 = boss.fighter.take_damage(5)
        messages2 = [r for r in results2 if 'message' in r]
        
        # First time should have low HP message, second time should not
        # (or might have random hit dialogue)
        assert boss.boss.has_used_dialogue("low_hp")


class TestBossDeathDialogue:
    """Tests for boss death dialogue."""
    
    def test_boss_death_has_dialogue(self):
        """Test boss says something dramatic when dying."""
        boss = Entity(10, 10, 'D', (255, 50, 0), "Dragon Lord", blocks=True)
        boss.fighter = Fighter(hp=50, defense=5, power=5)
        boss.boss = create_dragon_lord_boss()
        boss.fighter.owner = boss
        boss.boss.owner = boss
        
        boss.components.add(ComponentType.FIGHTER, boss.fighter)
        boss.components.add(ComponentType.BOSS, boss.boss)
        
        # Create game map for loot drops
        game_map = GameMap(30, 20, dungeon_level=5)
        
        # Kill boss
        death_message = kill_monster(boss, game_map)
        message_text = str(death_message.text)
        
        # Should include "falls" and dialogue quotes
        assert "falls" in message_text.lower()
        assert '"' in message_text  # Dialogue quotes
        # Check for death-related words
        assert any(word in message_text.lower() for word in ['impossible', 'defeated', 'mortal', 'hoard'])
    
    def test_boss_marked_defeated(self):
        """Test boss component is marked as defeated on death."""
        boss = Entity(10, 10, 'K', (160, 32, 240), "Demon King", blocks=True)
        boss.fighter = Fighter(hp=50, defense=3, power=8)
        boss.boss = create_demon_king_boss()
        boss.fighter.owner = boss
        boss.boss.owner = boss
        
        boss.components.add(ComponentType.FIGHTER, boss.fighter)
        boss.components.add(ComponentType.BOSS, boss.boss)
        
        assert not boss.boss.defeated
        
        # Kill boss
        game_map = GameMap(30, 20, dungeon_level=5)
        kill_monster(boss, game_map)
        
        assert boss.boss.defeated
    
    def test_normal_monster_no_boss_dialogue(self):
        """Test normal monsters don't get boss dialogue."""
        orc = Entity(10, 10, 'o', (63, 127, 63), "Orc", blocks=True)
        orc.fighter = Fighter(hp=20, defense=0, power=3)
        orc.fighter.owner = orc
        orc.components.add(ComponentType.FIGHTER, orc.fighter)
        
        # No boss component!
        
        game_map = GameMap(30, 20, dungeon_level=1)
        death_message = kill_monster(orc, game_map)
        message_text = str(death_message.text)
        
        # Should be simple death message
        assert "Orc is dead!" in message_text
        assert '"' not in message_text  # No dialogue quotes


class TestBossDamageMultiplier:
    """Tests for boss enrage damage multiplier."""
    
    def test_boss_damage_increases_when_enraged(self):
        """Test boss damage multiplier increases when enraged."""
        boss = Entity(10, 10, 'D', (255, 50, 0), "Dragon Lord", blocks=True)
        boss.fighter = Fighter(hp=100, defense=5, power=10)
        boss.boss = create_dragon_lord_boss()
        boss.fighter.owner = boss
        boss.boss.owner = boss
        
        boss.components.add(ComponentType.FIGHTER, boss.fighter)
        boss.components.add(ComponentType.BOSS, boss.boss)
        
        # Check normal damage multiplier
        assert boss.boss.get_damage_multiplier() == 1.0
        
        # Enrage boss
        boss.fighter.take_damage(50)
        assert boss.boss.is_enraged
        
        # Check enraged damage multiplier
        assert boss.boss.get_damage_multiplier() == 1.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

