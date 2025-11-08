"""
NPC Dialogue Component

Handles interactive dialogue trees with NPCs, including:
- Multiple choice dialogue branches
- Knowledge/flag tracking (e.g., learning Entity's true name)
- Achievement unlocking
- Dialogue state persistence

Phase 3: Guide system uses this for camp encounters
Future: Can be expanded for other NPCs, quests, etc.
"""

from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class DialogueOption:
    """A single dialogue option the player can choose."""
    id: str
    player_option: str  # What the player sees ("What happened to you?")
    npc_response: str   # NPC's response text
    leads_to: List[str] = field(default_factory=list)  # IDs of next options
    ends_conversation: bool = False
    unlocks_knowledge: Optional[List[str]] = None  # Knowledge flags to set
    grants_achievement: Optional[str] = None
    
    def __post_init__(self):
        """Ensure leads_to is a list and unlocks_knowledge is normalized."""
        if self.leads_to is None:
            self.leads_to = []

        # Normalize unlocks_knowledge to always be a list or None
        if isinstance(self.unlocks_knowledge, str):
            self.unlocks_knowledge = [self.unlocks_knowledge]
        elif self.unlocks_knowledge is None:
            self.unlocks_knowledge = None


@dataclass
class DialogueEncounter:
    """A complete dialogue encounter (e.g., Guide at level 5)."""
    level: int
    greeting: str
    introduction: str
    dialogue_tree: List[DialogueOption]
    farewell: str
    
    # Track which options have been seen
    seen_options: Set[str] = field(default_factory=set)
    current_options: List[str] = field(default_factory=list)
    
    def get_option(self, option_id: str) -> Optional[DialogueOption]:
        """Get a dialogue option by ID."""
        for option in self.dialogue_tree:
            if option.id == option_id:
                return option
        return None
    
    def get_available_options(self) -> List[DialogueOption]:
        """Get currently available dialogue options."""
        if not self.current_options:
            # If no current options, show all root options
            # (options not in any leads_to list)
            all_option_ids = {opt.id for opt in self.dialogue_tree}
            referenced_ids = set()
            for opt in self.dialogue_tree:
                referenced_ids.update(opt.leads_to)
            
            root_ids = all_option_ids - referenced_ids
            return [self.get_option(opt_id) for opt_id in root_ids if self.get_option(opt_id)]
        
        # Return options by current_options list
        return [self.get_option(opt_id) for opt_id in self.current_options if self.get_option(opt_id)]
    
    def select_option(self, option_id: str) -> Optional[DialogueOption]:
        """Select a dialogue option and update state."""
        option = self.get_option(option_id)
        if not option:
            return None
        
        # Mark as seen
        self.seen_options.add(option_id)
        
        # Update current options
        if option.ends_conversation:
            self.current_options = []
        else:
            self.current_options = option.leads_to
        
        return option


class NPCDialogue:
    """Component for entities that can have dialogue interactions.
    
    Attributes:
        encounters: Dict of level -> DialogueEncounter
        current_encounter: The active encounter (if any)
        knowledge_flags: Set of unlocked knowledge flags
        achievements: Set of earned achievements
        has_been_talked_to: Whether player has initiated dialogue
    """
    
    def __init__(self, encounters: Optional[Dict[int, DialogueEncounter]] = None):
        """Initialize NPC dialogue component.
        
        Args:
            encounters: Dict mapping dungeon level to DialogueEncounter
        """
        self.encounters = encounters or {}
        self.current_encounter: Optional[DialogueEncounter] = None
        self.knowledge_flags: Set[str] = set()
        self.achievements: Set[str] = set()
        self.has_been_talked_to = False
        
        # Track dialogue history
        self.dialogue_history: List[Dict[str, Any]] = []
        
    def get_encounter_for_level(self, level: int) -> Optional[DialogueEncounter]:
        """Get dialogue encounter for specific dungeon level."""
        return self.encounters.get(level)
    
    def start_encounter(self, level: int) -> bool:
        """Start a dialogue encounter for the given level.
        
        Args:
            level: Dungeon level
            
        Returns:
            bool: True if encounter started, False if no encounter for this level
        """
        encounter = self.get_encounter_for_level(level)
        if not encounter:
            logger.debug(f"No dialogue encounter for level {level}")
            return False
        
        self.current_encounter = encounter
        self.has_been_talked_to = True
        
        logger.info(f"Started dialogue encounter for level {level}")
        return True
    
    def get_greeting(self) -> Optional[str]:
        """Get greeting text for current encounter."""
        if not self.current_encounter:
            return None
        return self.current_encounter.greeting
    
    def get_introduction(self) -> Optional[str]:
        """Get introduction text for current encounter."""
        if not self.current_encounter:
            return None
        return self.current_encounter.introduction
    
    def get_available_options(self) -> List[DialogueOption]:
        """Get available dialogue options for current encounter."""
        if not self.current_encounter:
            return []
        return self.current_encounter.get_available_options()
    
    def select_option(self, option_id: str) -> Optional[DialogueOption]:
        """Select a dialogue option and process its effects.
        
        Args:
            option_id: ID of the dialogue option to select
            
        Returns:
            DialogueOption if successful, None otherwise
        """
        if not self.current_encounter:
            logger.warning("Tried to select option with no active encounter")
            return None
        
        option = self.current_encounter.select_option(option_id)
        if not option:
            logger.warning(f"Invalid dialogue option: {option_id}")
            return None
        
        # Process effects
        if option.unlocks_knowledge:
            if isinstance(option.unlocks_knowledge, list):
                for knowledge in option.unlocks_knowledge:
                    self.knowledge_flags.add(knowledge)
                    logger.info(f"Unlocked knowledge: {knowledge}")
            else:
                self.knowledge_flags.add(option.unlocks_knowledge)
                logger.info(f"Unlocked knowledge: {option.unlocks_knowledge}")
        
        if option.grants_achievement:
            self.achievements.add(option.grants_achievement)
            logger.info(f"Earned achievement: {option.grants_achievement}")
        
        # Record in history
        self.dialogue_history.append({
            'level': self.current_encounter.level,
            'option_id': option_id,
            'option_text': option.player_option,
            'knowledge': option.unlocks_knowledge,
            'achievement': option.grants_achievement
        })
        
        return option
    
    def end_encounter(self) -> Optional[str]:
        """End the current dialogue encounter.
        
        Returns:
            Farewell message if encounter exists, None otherwise
        """
        if not self.current_encounter:
            return None
        
        farewell = self.current_encounter.farewell
        self.current_encounter = None
        
        return farewell
    
    def has_knowledge(self, flag: str) -> bool:
        """Check if a knowledge flag is unlocked."""
        return flag in self.knowledge_flags
    
    def has_achievement(self, achievement: str) -> bool:
        """Check if an achievement is earned."""
        return achievement in self.achievements
    
    def has_learned_true_name(self) -> bool:
        """Check if player learned Entity's true name (Zhyraxion)."""
        return self.has_knowledge("entity_true_name_zhyraxion")
    
    def is_in_conversation(self) -> bool:
        """Check if currently in a dialogue encounter."""
        return self.current_encounter is not None
    
    def get_dialogue_summary(self) -> Dict[str, Any]:
        """Get summary of dialogue state for save/load.
        
        Returns:
            Dict with knowledge flags, achievements, history
        """
        return {
            'knowledge_flags': list(self.knowledge_flags),
            'achievements': list(self.achievements),
            'has_been_talked_to': self.has_been_talked_to,
            'dialogue_history': self.dialogue_history
        }
    
    def load_dialogue_state(self, state: Dict[str, Any]) -> None:
        """Load dialogue state from save data.
        
        Args:
            state: Dict from get_dialogue_summary()
        """
        self.knowledge_flags = set(state.get('knowledge_flags', []))
        self.achievements = set(state.get('achievements', []))
        self.has_been_talked_to = state.get('has_been_talked_to', False)
        self.dialogue_history = state.get('dialogue_history', [])
        
        logger.info(f"Loaded dialogue state: {len(self.knowledge_flags)} knowledge flags, "
                   f"{len(self.achievements)} achievements")


def create_dialogue_from_yaml(dialogue_data: Dict[str, Any]) -> NPCDialogue:
    """Create NPCDialogue component from YAML data structure.
    
    Args:
        dialogue_data: Dict loaded from guide_dialogue.yaml
        
    Returns:
        NPCDialogue component with encounters configured
    """
    encounters = {}
    
    encounters_data = dialogue_data.get('encounters', {})
    for level_str, encounter_data in encounters_data.items():
        level = int(level_str)
        
        # Parse dialogue tree
        dialogue_tree = []
        for option_data in encounter_data.get('dialogue_tree', []):
            dialogue_tree.append(DialogueOption(
                id=option_data['id'],
                player_option=option_data['player_option'],
                npc_response=option_data['npc_response'],
                leads_to=option_data.get('leads_to', []),
                ends_conversation=option_data.get('ends_conversation', False),
                unlocks_knowledge=option_data.get('unlocks_knowledge'),
                grants_achievement=option_data.get('grants_achievement')
            ))
        
        # Create encounter
        encounters[level] = DialogueEncounter(
            level=level,
            greeting=encounter_data['greeting'],
            introduction=encounter_data['introduction'],
            dialogue_tree=dialogue_tree,
            farewell=encounter_data['farewell']
        )
    
    return NPCDialogue(encounters)


if __name__ == "__main__":
    # Test the dialogue system
    
    logging.basicConfig(level=logging.DEBUG)
    
    # Load guide dialogue
    dialogue_file = Path("config/guide_dialogue.yaml")
    if dialogue_file.exists():
        with open(dialogue_file, 'r') as f:
            data = yaml.safe_load(f)
        
        npc_dialogue = create_dialogue_from_yaml(data)
        
        print(f"Loaded dialogue with {len(npc_dialogue.encounters)} encounters")
        print("\nTesting Level 5 encounter:\n")
        
        # Start encounter
        npc_dialogue.start_encounter(5)
        print(f"Greeting: {npc_dialogue.get_greeting()}")
        print(f"Intro: {npc_dialogue.get_introduction()}\n")
        
        # Show options
        options = npc_dialogue.get_available_options()
        print("Available options:")
        for i, opt in enumerate(options, 1):
            print(f"  {i}. {opt.player_option}")
        
        print("\nDialogue system test complete!")
    else:
        print(f"Could not find {dialogue_file}")

