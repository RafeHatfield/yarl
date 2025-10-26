"""Victory component for tracking player's progress toward victory condition.

This component tracks the state of the player's quest to obtain the Amulet of
Yendor and confront the Entity. It manages the victory sequence and determines
which ending the player achieves.
"""

from typing import Optional


class Victory:
    """Component for tracking victory condition progress.
    
    Attributes:
        has_amulet: Whether player has picked up the Amulet of Yendor
        portal_appeared: Whether the Entity's portal has manifested
        portal_location: (x, y) coordinates of the portal
        entity_anxiety_level: 0-3, increases as player delays confrontation
        turns_since_amulet: Number of turns since picking up amulet
        confrontation_started: Whether player has entered the portal
        ending_achieved: Which ending the player got ('good', 'bad', 'sacrifice', 'betrayal', None)
        throne_room_entered: Whether player is in Entity's Throne Room
    """
    
    def __init__(self):
        """Initialize victory tracking component."""
        self.has_amulet = False
        self.portal_appeared = False
        self.portal_location: Optional[tuple] = None
        self.entity_anxiety_level = 0  # 0=calm, 1=impatient, 2=anxious, 3=desperate
        self.turns_since_amulet = 0
        self.confrontation_started = False
        self.ending_achieved: Optional[str] = None
        self.throne_room_entered = False
        
        # Phase 3: Knowledge tracking (from Guide dialogue)
        self.knows_entity_true_name = False  # Learned "Zhyraxion"
        self.knowledge_unlocked = set()  # Set of knowledge IDs from dialogue
        
        # Owner reference (will be set to player entity)
        self.owner: Optional[object] = None
    
    def obtain_amulet(self, portal_x: int, portal_y: int):
        """Mark that player has obtained the Amulet of Yendor.
        
        Args:
            portal_x: X coordinate where portal should appear
            portal_y: Y coordinate where portal should appear
        """
        self.has_amulet = True
        self.portal_appeared = True
        self.portal_location = (portal_x, portal_y)
        self.turns_since_amulet = 0
    
    def advance_turn(self):
        """Advance turn counter and update Entity anxiety level."""
        if self.has_amulet and not self.confrontation_started:
            self.turns_since_amulet += 1
            
            # Update anxiety level based on delay
            if self.turns_since_amulet > 100:
                self.entity_anxiety_level = 3  # Desperate
            elif self.turns_since_amulet > 50:
                self.entity_anxiety_level = 2  # Anxious
            elif self.turns_since_amulet > 10:
                self.entity_anxiety_level = 1  # Impatient
    
    def start_confrontation(self):
        """Mark that player has entered the portal for confrontation."""
        self.confrontation_started = True
        self.throne_room_entered = True
    
    def achieve_ending(self, ending_type: str):
        """Record which ending the player achieved.
        
        Args:
            ending_type: 'good', 'bad', 'sacrifice', or 'betrayal'
        """
        self.ending_achieved = ending_type
    
    def unlock_knowledge(self, knowledge_id: str):
        """Unlock a piece of knowledge from Guide dialogue.
        
        Args:
            knowledge_id: ID of the knowledge (e.g., "entity_true_name_zhyraxion")
        """
        self.knowledge_unlocked.add(knowledge_id)
        
        # Special handling for true name
        if knowledge_id == "entity_true_name_zhyraxion":
            self.knows_entity_true_name = True
    
    def has_knowledge(self, knowledge_id: str) -> bool:
        """Check if player has unlocked specific knowledge.
        
        Args:
            knowledge_id: ID of the knowledge to check
            
        Returns:
            True if knowledge is unlocked
        """
        return knowledge_id in self.knowledge_unlocked

