"""
Entity Dialogue Loader

Loads and manages progressive Entity dialogue from entity_dialogue.yaml.
The Entity's voice becomes more anxious and desperate as player descends.

Phase 2 implementation - simple depth-based triggers.
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EntityDialogue:
    """Container for Entity dialogue at a specific depth."""
    level: int
    message: str
    color: str
    style: str


class EntityDialogueLoader:
    """Loads and provides Entity dialogue based on dungeon depth."""
    
    def __init__(self, dialogue_file: str = "config/entity_dialogue.yaml"):
        """Initialize the dialogue loader.
        
        Args:
            dialogue_file: Path to dialogue YAML file
        """
        self.dialogue_file = dialogue_file
        self.depth_dialogue: Dict[int, EntityDialogue] = {}
        self.config: Dict[str, Any] = {}
        self.last_triggered_level: Optional[int] = None
        self.turns_since_last: int = 0
        
        self._load_dialogue()
        
    def _load_dialogue(self) -> None:
        """Load dialogue from YAML file."""
        try:
            path = Path(self.dialogue_file)
            if not path.exists():
                logger.warning(f"Entity dialogue file not found: {self.dialogue_file}")
                return
                
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
                
            if not data:
                logger.warning(f"Empty dialogue file: {self.dialogue_file}")
                return
                
            # Load depth-based dialogue
            depth_data = data.get('depth_dialogue', {})
            for level_str, dialogue_data in depth_data.items():
                level = int(level_str)
                self.depth_dialogue[level] = EntityDialogue(
                    level=level,
                    message=dialogue_data['message'],
                    color=dialogue_data.get('color', 'light_purple'),
                    style=dialogue_data.get('style', 'dramatic')
                )
                
            # Load config
            self.config = data.get('config', {
                'show_in_log': True,
                'interrupt_gameplay': False,
                'track_in_save': False,
                'cooldown_turns': 50
            })
            
            logger.info(f"Loaded {len(self.depth_dialogue)} Entity dialogue entries")
            
        except Exception as e:
            logger.error(f"Failed to load Entity dialogue: {e}", exc_info=True)
            
    def get_dialogue_for_level(self, level: int, force: bool = False) -> Optional[EntityDialogue]:
        """Get Entity dialogue for a specific dungeon level.
        
        Args:
            level: Dungeon level (1-25)
            force: Ignore cooldown and return dialogue anyway
            
        Returns:
            EntityDialogue if available for this level, None otherwise
        """
        # Check if dialogue exists for this level
        if level not in self.depth_dialogue:
            return None
            
        # Cooldown check (prevent spam if player goes up/down repeatedly)
        cooldown = self.config.get('cooldown_turns', 50)
        if not force and self.last_triggered_level == level and self.turns_since_last < cooldown:
            logger.debug(f"Entity dialogue cooldown active (level {level})")
            return None
            
        # Reset cooldown tracking
        self.last_triggered_level = level
        self.turns_since_last = 0
        
        return self.depth_dialogue[level]
        
    def increment_turn_counter(self) -> None:
        """Increment turn counter for cooldown tracking."""
        self.turns_since_last += 1
        
    def should_show_in_log(self) -> bool:
        """Should dialogue appear in message log?"""
        return self.config.get('show_in_log', True)
        
    def should_interrupt(self) -> bool:
        """Should dialogue interrupt gameplay with dialog box?"""
        return self.config.get('interrupt_gameplay', False)
        
    def reset(self) -> None:
        """Reset dialogue state (for new game)."""
        self.last_triggered_level = None
        self.turns_since_last = 0
        logger.debug("Entity dialogue state reset")


# Global singleton instance
_dialogue_loader_instance: Optional[EntityDialogueLoader] = None


def get_entity_dialogue_loader() -> EntityDialogueLoader:
    """Get the global Entity dialogue loader instance.
    
    Returns:
        EntityDialogueLoader singleton
    """
    global _dialogue_loader_instance
    
    if _dialogue_loader_instance is None:
        _dialogue_loader_instance = EntityDialogueLoader()
        
    return _dialogue_loader_instance


def reset_entity_dialogue() -> None:
    """Reset Entity dialogue state (call on new game)."""
    loader = get_entity_dialogue_loader()
    loader.reset()


if __name__ == "__main__":
    # Test the loader
    import sys
    logging.basicConfig(level=logging.DEBUG)
    
    loader = EntityDialogueLoader()
    
    print(f"Loaded {len(loader.depth_dialogue)} dialogue entries\n")
    print("Testing dialogue retrieval:\n")
    
    test_levels = [1, 5, 10, 15, 20, 25, 13]  # 13 has no dialogue
    for level in test_levels:
        dialogue = loader.get_dialogue_for_level(level, force=True)
        if dialogue:
            print(f"Level {level}: {dialogue.message}")
            print(f"  Color: {dialogue.color}, Style: {dialogue.style}\n")
        else:
            print(f"Level {level}: (no dialogue)\n")

