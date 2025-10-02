"""Tests for the Entity dialogue system."""

import pytest
from entity_dialogue import EntityDialogue, get_entity_quote_for_death
from components.statistics import Statistics


class TestEntityDialogue:
    """Test the Entity's condescending, sarcastic dialogue system."""
    
    def test_get_death_quote_returns_string(self):
        """Test that get_death_quote returns a non-empty string."""
        quote = EntityDialogue.get_death_quote()
        assert isinstance(quote, str)
        assert len(quote) > 0
    
    def test_quick_death_triggers_quick_death_quotes(self):
        """Test that very short runs trigger quick death quotes."""
        # Run multiple times to check we get contextual quotes
        quotes = set()
        for _ in range(20):
            quote = EntityDialogue.get_death_quote(turns_taken=5, total_kills=0)
            quotes.add(quote)
        
        # Should get at least some variety
        assert len(quotes) > 1
    
    def test_deep_dungeon_triggers_appropriate_quotes(self):
        """Test that deep dungeon runs trigger different quotes."""
        quotes = set()
        for _ in range(20):
            quote = EntityDialogue.get_death_quote(dungeon_level=6, total_kills=20, turns_taken=100)
            quotes.add(quote)
        
        # Should get variety
        assert len(quotes) > 1
    
    def test_weak_enemy_death_triggers_condescending_quotes(self):
        """Test that early death triggers weak enemy quotes."""
        quotes = set()
        for _ in range(20):
            quote = EntityDialogue.get_death_quote(dungeon_level=2, total_kills=3, turns_taken=50)
            quotes.add(quote)
        
        # Should get variety
        assert len(quotes) > 1
    
    def test_strong_performance_recognized(self):
        """Test that strong performances trigger appropriate quotes."""
        quotes = set()
        for _ in range(20):
            quote = EntityDialogue.get_death_quote(
                dungeon_level=5,
                total_kills=25,
                turns_taken=200,
                gold_collected=100
            )
            quotes.add(quote)
        
        # Should get variety including performance-based quotes
        assert len(quotes) > 1
    
    def test_quote_formatting_with_variables(self):
        """Test that quotes with variables are properly formatted."""
        quote = EntityDialogue.get_death_quote(dungeon_level=7)
        
        # Quote shouldn't have unformatted placeholders
        assert "{level}" not in quote
    
    def test_restart_quote_returns_string(self):
        """Test that restart quotes work."""
        quote = EntityDialogue.get_restart_quote()
        assert isinstance(quote, str)
        assert len(quote) > 0
    
    def test_first_death_quote_returns_string(self):
        """Test that first death quote works."""
        quote = EntityDialogue.get_first_death_quote()
        assert isinstance(quote, str)
        assert len(quote) > 0
    
    def test_convenience_function_with_statistics(self):
        """Test the convenience function works with Statistics component."""
        stats = Statistics()
        stats.total_kills = 10
        stats.turns_taken = 100
        stats.gold_collected = 50
        stats.deepest_level = 4
        
        quote = get_entity_quote_for_death(stats, dungeon_level=4)
        assert isinstance(quote, str)
        assert len(quote) > 0
    
    def test_all_quote_pools_accessible(self):
        """Test that all quote pools have content."""
        assert len(EntityDialogue.GENERAL_DEATH_QUOTES) > 0
        assert len(EntityDialogue.WEAK_ENEMY_QUOTES) > 0
        assert len(EntityDialogue.DEEP_DUNGEON_QUOTES) > 0
        assert len(EntityDialogue.QUICK_DEATH_QUOTES) > 0
        assert len(EntityDialogue.STRONG_PERFORMANCE_QUOTES) > 0
        assert len(EntityDialogue.TREASURE_QUOTES) > 0
        assert len(EntityDialogue.SPECIAL_QUOTES) > 0
    
    def test_quotes_match_personality(self):
        """Test that quotes have the right condescending tone."""
        all_quotes = (
            EntityDialogue.GENERAL_DEATH_QUOTES +
            EntityDialogue.WEAK_ENEMY_QUOTES +
            EntityDialogue.DEEP_DUNGEON_QUOTES
        )
        
        # Check for condescending markers (not a perfect test, but reasonable)
        condescending_words = ['pathetic', 'unsurprising', 'disappointing', 
                               'foolish', 'mortal', 'adequate', 'almost']
        
        # At least some quotes should have condescending language
        condescending_count = sum(
            1 for quote in all_quotes 
            if any(word in quote.lower() for word in condescending_words)
        )
        assert condescending_count > 0

