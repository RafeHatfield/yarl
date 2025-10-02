"""Entity dialogue system for the bound soul narrative.

The Entity is a powerful being who owns the player's soul and forces them
to delve into the dungeon repeatedly. They are sarcastically overbearing,
overconfident in their supremacy, and extremely condescending.
"""

import random
from typing import Optional


class EntityDialogue:
    """Manages dialogue from the Entity that binds the player's soul."""
    
    # General death quotes (used when no specific context matches)
    GENERAL_DEATH_QUOTES = [
        "Oh. You're back. How... unsurprising.",
        "Well, that was... pathetic. Let's try that again, shall we?",
        "I'd say I'm disappointed, but that would imply I had expectations.",
        "Again already? I've barely had time to prepare the next vessel.",
        "Do try to make this one last more than a few moments, would you?",
        "Your enthusiasm for dying is noted. Perhaps try *not* dying?",
        "Remind me why I bound *your* soul specifically? Oh yes, you were convenient.",
        "I've seen snails with more survival instinct.",
        "Your struggles are... quaint. Like watching a child learn to walk. And fall. Repeatedly.",
    ]
    
    # Quotes for dying to weak enemies (levels 1-3)
    WEAK_ENEMY_QUOTES = [
        "A goblin? Really? How embarrassingly mortal of you.",
        "Killed by... that? I've reconsidered. Perhaps I should find a different soul.",
        "Do you need me to explain basic combat? Point sword at enemy. Swing.",
        "At this rate, you'll be defeated by a particularly aggressive mushroom.",
        "I'm starting to think binding your soul was a waste of perfectly good magic.",
    ]
    
    # Quotes for dying to strong enemies or deep in dungeon (level 4+)
    DEEP_DUNGEON_QUOTES = [
        "Ah yes, ambitious. Foolish, but ambitious.",
        "At least you aimed high before failing spectacularly.",
        "Impressive that you made it that far. Not impressive that you died, but still.",
        "Oh? You almost made it. Almost. But 'almost' doesn't retrieve artifacts, does it?",
        "Level {level}. Not terrible. For you, anyway.",
        "I suppose that was... adequate. By mortal standards.",
    ]
    
    # Quotes for quick deaths (< 10 turns)
    QUICK_DEATH_QUOTES = [
        "That was impressively brief. And by impressive, I mean pathetic.",
        "Blink and you'd have missed it. I wish I had.",
        "New record for futility. Congratulations, I suppose.",
        "Did you even try? No, don't answer. I can tell.",
    ]
    
    # Quotes for good runs (many kills, good stats)
    STRONG_PERFORMANCE_QUOTES = [
        "Finally showing some competence. Don't let it go to your head.",
        "Not entirely useless this time. How refreshing.",
        "I'm *almost* impressed. Almost. But not quite.",
        "Adequate. Though I could have done it in half the time, naturally.",
        "Yes, yes, you killed many things. Shall I throw you a parade?",
    ]
    
    # Quotes for collecting gold/treasure
    TREASURE_QUOTES = [
        "Yes, yes, bring that to me. It's the least you can do.",
        "Finally, something useful from your little expedition.",
        "Adequate compensation for the effort of resurrecting you. Barely.",
        "Add it to the pile. You have a long way to go before your debt is paid.",
    ]
    
    # Quotes for rare/unusual deaths
    SPECIAL_QUOTES = [
        "Now that was creative. Stupidly so, but creative nonetheless.",
        "I didn't know that could kill you. Well, now we both know.",
        "Fascinating. Let's never do that again.",
    ]
    
    @classmethod
    def get_death_quote(cls, 
                       player_level: int = 1,
                       dungeon_level: int = 1, 
                       turns_taken: int = 0,
                       total_kills: int = 0,
                       gold_collected: int = 0,
                       cause_of_death: Optional[str] = None) -> str:
        """Get a contextually appropriate death quote from the Entity.
        
        Args:
            player_level: Player's character level
            dungeon_level: How deep in dungeon player reached
            turns_taken: Number of turns survived
            total_kills: Number of enemies killed
            gold_collected: Amount of gold collected
            cause_of_death: What killed the player (if known)
            
        Returns:
            A quote from the Entity appropriate to the death context
        """
        # Determine context and pick appropriate quote pool
        quote_pools = []
        weights = []
        
        # Quick death (less than 10 turns)
        if turns_taken < 10:
            quote_pools.append(cls.QUICK_DEATH_QUOTES)
            weights.append(3)  # High weight for quick deaths
        
        # Deep dungeon (level 4+)
        if dungeon_level >= 4:
            quote_pools.append(cls.DEEP_DUNGEON_QUOTES)
            weights.append(3)
        
        # Weak enemy death (early levels)
        elif dungeon_level <= 3 and total_kills < 10:
            quote_pools.append(cls.WEAK_ENEMY_QUOTES)
            weights.append(2)
        
        # Strong performance (many kills)
        if total_kills >= 15:
            quote_pools.append(cls.STRONG_PERFORMANCE_QUOTES)
            weights.append(2)
        
        # Collected treasure
        if gold_collected >= 50:
            quote_pools.append(cls.TREASURE_QUOTES)
            weights.append(1)  # Lower weight, less common
        
        # Always include general quotes as fallback
        quote_pools.append(cls.GENERAL_DEATH_QUOTES)
        weights.append(1)
        
        # Pick a pool based on weights, then pick a quote from that pool
        chosen_pool = random.choices(quote_pools, weights=weights, k=1)[0]
        quote = random.choice(chosen_pool)
        
        # Format quotes that have variables
        if "{level}" in quote:
            quote = quote.format(level=dungeon_level)
        
        return quote
    
    @classmethod
    def get_restart_quote(cls) -> str:
        """Get a quote for when player quickly restarts (presses R).
        
        Returns:
            A quote about the player's eagerness to try again
        """
        quotes = [
            "Eager for another beating, are we? Admirable. Foolish, but admirable.",
            "Back so soon? I like your determination. Pity about your competence.",
            "Already? The vessel's still warm. Well, let's not waste it.",
            "Impatient to fail again? Very well, I won't keep you waiting.",
            "Such enthusiasm. If only you channeled it into not dying.",
        ]
        return random.choice(quotes)
    
    @classmethod
    def get_first_death_quote(cls) -> str:
        """Get a special quote for the very first death of a new player.
        
        Returns:
            An introductory quote establishing the Entity's personality
        """
        quotes = [
            "Ah. Dead already. How delightfully predictable. Let's try that again.",
            "Well, that didn't last long. No matter - your soul is mine, and we have all eternity.",
            "Dead. Naturally. Don't worry, you'll get used to it. I certainly have.",
            "How unfortunate. For you, anyway. For me, it's merely an inconvenience.",
        ]
        return random.choice(quotes)


def get_entity_quote_for_death(statistics, dungeon_level: int = 1) -> str:
    """Convenience function to get a death quote based on player statistics.
    
    Args:
        statistics: The player's Statistics component
        dungeon_level: Current dungeon level reached
        
    Returns:
        An appropriate Entity quote
    """
    return EntityDialogue.get_death_quote(
        player_level=1,  # We don't have player levels yet, default to 1
        dungeon_level=dungeon_level,
        turns_taken=statistics.turns_taken,
        total_kills=statistics.total_kills,
        gold_collected=statistics.gold_collected
    )

