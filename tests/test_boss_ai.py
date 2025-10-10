"""Tests for boss AI behavior and combat enhancements."""

import pytest
from entity import Entity
from components.fighter import Fighter
from components.boss import Boss, create_dragon_lord_boss, create_demon_king_boss
from components.ai import BossAI
from components.component_registry import ComponentType
from spells.spell_executor import SpellExecutor
from spells.spell_catalog import CONFUSION, SLOW
from spells.spell_types import EffectType


class TestBossStatusImmunity:
    """Tests for boss immunity to status effects."""
    
    def test_boss_resists_confusion(self):
        """Test that bosses resist confusion spell."""
        # Create boss
        boss = Entity(10, 10, 'D', (255, 50, 0), "Dragon Lord", blocks=True)
        boss.fighter = Fighter(hp=100, defense=5, power=10)
        boss.boss = create_dragon_lord_boss()
        boss.ai = BossAI()
        
        boss.fighter.owner = boss
        boss.boss.owner = boss
        boss.ai.owner = boss
        
        boss.components.add(ComponentType.FIGHTER, boss.fighter)
        boss.components.add(ComponentType.BOSS, boss.boss)
        boss.components.add(ComponentType.AI, boss.ai)
        
        # Create player
        player = Entity(5, 5, '@', (255, 255, 255), "Player", blocks=True)
        
        # Try to confuse boss
        executor = SpellExecutor()
        results = executor._cast_confusion_spell(
            CONFUSION,
            player,
            [boss, player],
            boss.x,
            boss.y
        )
        
        # Should be consumed (spell cast) but boss resists
        assert any(r.get('consumed') for r in results)
        
        # Find resist message
        messages = [r for r in results if 'message' in r]
        assert len(messages) > 0
        assert 'resist' in str(messages[0]['message'].text).lower()
        
        # Boss AI should NOT be ConfusedMonster
        assert type(boss.ai).__name__ == 'BossAI'
    
    def test_dragon_lord_immune_to_fire(self):
        """Test Dragon Lord is immune to fire damage."""
        boss = create_dragon_lord_boss()
        
        # Dragon Lord should be immune to fire
        assert boss.is_immune_to("fire")
        assert boss.is_immune_to("Fire")  # Case insensitive
        assert boss.is_immune_to("FIRE")
        
        # Still immune to confusion and slow (default)
        assert boss.is_immune_to("confusion")
        assert boss.is_immune_to("slow")
    
    def test_demon_king_immune_to_curse(self):
        """Test Demon King is immune to curse and poison."""
        boss = create_demon_king_boss()
        
        # Demon King has expanded immunities
        assert boss.is_immune_to("curse")
        assert boss.is_immune_to("poison")
        assert boss.is_immune_to("confusion")
        assert boss.is_immune_to("slow")
    
    def test_normal_monster_affected_by_confusion(self):
        """Test that normal monsters can be confused (not immune)."""
        # Create normal orc
        orc = Entity(10, 10, 'o', (63, 127, 63), "Orc", blocks=True)
        orc.fighter = Fighter(hp=20, defense=0, power=3)
        from components.ai import BasicMonster
        orc.ai = BasicMonster()
        
        orc.fighter.owner = orc
        orc.ai.owner = orc
        
        orc.components.add(ComponentType.FIGHTER, orc.fighter)
        orc.components.add(ComponentType.AI, orc.ai)
        
        # NO boss component!
        
        # Create player
        player = Entity(5, 5, '@', (255, 255, 255), "Player", blocks=True)
        
        # Confuse orc
        executor = SpellExecutor()
        results = executor._cast_confusion_spell(
            CONFUSION,
            player,
            [orc, player],
            orc.x,
            orc.y
        )
        
        # Should be consumed and orc confused
        assert any(r.get('consumed') for r in results)
        
        # Orc AI should now be ConfusedMonster
        assert type(orc.ai).__name__ == 'ConfusedMonster'


class TestBossDamageMultiplier:
    """Tests for boss damage multiplier when enraged."""
    
    def test_enraged_boss_deals_more_damage(self):
        """Test enraged boss deals 1.5x damage."""
        # Create boss
        boss = Entity(10, 10, 'D', (255, 50, 0), "Dragon Lord", blocks=True)
        boss.fighter = Fighter(hp=100, defense=5, power=10, damage_min=5, damage_max=5)
        boss.boss = create_dragon_lord_boss()
        boss.ai = BossAI()
        
        boss.fighter.owner = boss
        boss.boss.owner = boss
        boss.ai.owner = boss
        
        boss.components.add(ComponentType.FIGHTER, boss.fighter)
        boss.components.add(ComponentType.BOSS, boss.boss)
        boss.components.add(ComponentType.AI, boss.ai)
        
        # Create target with no defense
        target = Entity(9, 10, '@', (255, 255, 255), "Player", blocks=True)
        target.fighter = Fighter(hp=100, defense=0, power=5)
        target.fighter.owner = target
        target.components.add(ComponentType.FIGHTER, target.fighter)
        
        # Attack while NOT enraged
        target.fighter.hp = 100  # Reset HP
        boss.fighter.attack(target)
        normal_damage = 100 - target.fighter.hp
        
        # Enrage boss
        boss.boss.check_enrage(40, 100)
        assert boss.boss.is_enraged
        
        # Attack while enraged
        target.fighter.hp = 100  # Reset HP
        boss.fighter.attack(target)
        enraged_damage = 100 - target.fighter.hp
        
        # Enraged damage should be significantly higher (1.5x)
        assert enraged_damage > normal_damage
        # Should be approximately 1.5x (allowing for variance)
        assert enraged_damage >= int(normal_damage * 1.4)


class TestBossAI:
    """Tests for BossAI behavior."""
    
    def test_boss_ai_creation(self):
        """Test creating a boss with BossAI."""
        boss = Entity(10, 10, 'D', (255, 50, 0), "Dragon Lord", blocks=True)
        boss.fighter = Fighter(hp=100, defense=5, power=10)
        boss.boss = create_dragon_lord_boss()
        boss.ai = BossAI()
        
        boss.fighter.owner = boss
        boss.boss.owner = boss
        boss.ai.owner = boss
        
        boss.components.add(ComponentType.FIGHTER, boss.fighter)
        boss.components.add(ComponentType.BOSS, boss.boss)
        boss.components.add(ComponentType.AI, boss.ai)
        
        assert boss.ai is not None
        assert type(boss.ai).__name__ == 'BossAI'
        assert boss.ai.owner == boss
    
    def test_boss_ai_has_in_combat_flag(self):
        """Test BossAI has in_combat flag for consistency."""
        boss_ai = BossAI()
        assert hasattr(boss_ai, 'in_combat')
        assert boss_ai.in_combat == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

