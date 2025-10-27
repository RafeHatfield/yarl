"""Victory component for tracking player's progress toward victory condition.

This component tracks the state of the player's quest to obtain Aurelyn's Ruby Heart
and confront Zhyraxion. It manages the victory sequence and determines which ending
the player achieves.
"""

from typing import Optional


class Victory:
    """Component for tracking victory condition progress.
    
    Attributes:
        has_ruby_heart: Whether player has picked up Aurelyn's Ruby Heart
        portal_appeared: Whether the portal to confrontation has manifested
        portal_location: (x, y) coordinates of the portal
        entity_anxiety_level: 0-3, increases as player delays confrontation
        turns_since_ruby_heart: Number of turns since picking up Ruby Heart
        confrontation_started: Whether player has entered the portal
        ending_achieved: Which ending the player got (e.g., '1a', '1b', '2', '3', '4', '5')
        confrontation_chamber_entered: Whether player is in Zhyraxion's Chamber
    """
    
    def __init__(self):
        """Initialize victory tracking component."""
        self.has_ruby_heart = False
        self.portal_appeared = False
        self.portal_location: Optional[tuple] = None
        self.entity_anxiety_level = 0  # 0=calm, 1=impatient, 2=anxious, 3=desperate
        self.turns_since_ruby_heart = 0
        self.confrontation_started = False
        self.ending_achieved: Optional[str] = None
        self.confrontation_chamber_entered = False
        
        # Phase 5: Knowledge tracking (from Guide dialogue + secret room)
        self.knows_entity_true_name = False  # Learned "Zhyraxion" from Guide at Level 15
        self.knows_crimson_ritual = False     # Found Crimson Ritual Codex in secret room
        self.knowledge_unlocked = set()       # Set of knowledge IDs from dialogue
        
        # Owner reference (will be set to player entity)
        self.owner: Optional[object] = None
    
    def obtain_ruby_heart(self, portal_x: int, portal_y: int):
        """Mark that player has obtained Aurelyn's Ruby Heart.
        
        Args:
            portal_x: X coordinate where portal should appear
            portal_y: Y coordinate where portal should appear
        """
        self.has_ruby_heart = True
        self.portal_appeared = True
        self.portal_location = (portal_x, portal_y)
        self.turns_since_ruby_heart = 0
    
    def advance_turn(self):
        """Advance turn counter and update Zhyraxion's anxiety level."""
        if self.has_ruby_heart and not self.confrontation_started:
            self.turns_since_ruby_heart += 1
            
            # Update anxiety level based on delay
            if self.turns_since_ruby_heart > 100:
                self.entity_anxiety_level = 3  # Desperate
            elif self.turns_since_ruby_heart > 50:
                self.entity_anxiety_level = 2  # Anxious
            elif self.turns_since_ruby_heart > 10:
                self.entity_anxiety_level = 1  # Impatient
    
    def start_confrontation(self):
        """Mark that player has entered the portal for confrontation."""
        self.confrontation_started = True
        self.confrontation_chamber_entered = True
    
    def achieve_ending(self, ending_type: str):
        """Record which ending the player achieved.
        
        Args:
            ending_type: '1a', '1b', '2', '3', '4', or '5' (see STORY_LORE_CANONICAL.md)
        """
        self.ending_achieved = ending_type
    
    def unlock_knowledge(self, knowledge_id: str):
        """Unlock a piece of knowledge from Guide dialogue or items.
        
        Args:
            knowledge_id: ID of the knowledge (e.g., "entity_true_name_zhyraxion", "crimson_ritual_knowledge")
        """
        self.knowledge_unlocked.add(knowledge_id)
        
        # Special handling for true name
        if knowledge_id == "entity_true_name_zhyraxion":
            self.knows_entity_true_name = True
        
        # Special handling for crimson ritual knowledge
        if knowledge_id == "crimson_ritual_knowledge":
            self.knows_crimson_ritual = True
    
    def has_knowledge(self, knowledge_id: str) -> bool:
        """Check if player has unlocked specific knowledge.
        
        Args:
            knowledge_id: ID of the knowledge to check
            
        Returns:
            True if knowledge is unlocked
        """
        return knowledge_id in self.knowledge_unlocked

