"""Hall of Fame system for tracking player victories.

This module manages the Hall of Fame, which records all successful
game completions with relevant statistics and endings achieved.
"""

import os
import yaml
from datetime import datetime
from typing import List, Dict, Any


HALL_OF_FAME_FILE = "data/hall_of_fame.yaml"


class HallOfFame:
    """Manages the Hall of Fame for victorious runs."""
    
    def __init__(self):
        """Initialize Hall of Fame manager."""
        self.entries: List[Dict[str, Any]] = []
        self.load()
    
    def load(self):
        """Load Hall of Fame from file."""
        if not os.path.exists(HALL_OF_FAME_FILE):
            self.entries = []
            return
        
        try:
            with open(HALL_OF_FAME_FILE, 'r') as f:
                data = yaml.safe_load(f)
                self.entries = data.get('victories', []) if data else []
        except Exception as e:
            print(f"Warning: Could not load Hall of Fame: {e}")
            self.entries = []
    
    def save(self):
        """Save Hall of Fame to file."""
        # Ensure data directory exists
        os.makedirs(os.path.dirname(HALL_OF_FAME_FILE), exist_ok=True)
        
        try:
            with open(HALL_OF_FAME_FILE, 'w') as f:
                yaml.dump({'victories': self.entries}, f, default_flow_style=False)
        except Exception as e:
            print(f"Warning: Could not save Hall of Fame: {e}")
    
    def add_victory(self, player_name: str, ending_type: str, stats: Dict[str, Any]):
        """Add a new victory to the Hall of Fame.
        
        Args:
            player_name: Name of the victorious character
            ending_type: Type of ending achieved ('good', 'bad', etc.)
            stats: Dictionary of player statistics
        """
        entry = {
            'character_name': player_name,
            'ending': ending_type,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'turns': stats.get('turns', 0),
            'deaths': stats.get('deaths', 0),
            'kills': stats.get('kills', 0),
            'final_level': stats.get('final_level', 0),
            'deepest_level': stats.get('deepest_level', 0)
        }
        
        self.entries.append(entry)
        
        # Keep only the most recent 50 entries to prevent file bloat
        if len(self.entries) > 50:
            self.entries = self.entries[-50:]
        
        self.save()
    
    def get_recent_victories(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get the most recent victories.
        
        Args:
            count: Number of recent victories to return
            
        Returns:
            List of victory entries
        """
        return self.entries[-count:][::-1]  # Reverse to show newest first
    
    def get_by_ending(self, ending_type: str) -> List[Dict[str, Any]]:
        """Get all victories with a specific ending type.
        
        Args:
            ending_type: Type of ending to filter by
            
        Returns:
            List of matching victory entries
        """
        return [e for e in self.entries if e.get('ending') == ending_type]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall Hall of Fame statistics.
        
        Returns:
            Dictionary of aggregate statistics
        """
        if not self.entries:
            return {
                'total_victories': 0,
                'good_endings': 0,
                'bad_endings': 0,
                'fastest_victory': None,
                'fewest_deaths': None
            }
        
        good_count = len([e for e in self.entries if e.get('ending') == 'good'])
        bad_count = len([e for e in self.entries if e.get('ending') == 'bad'])
        
        # Find fastest victory (fewest turns)
        fastest = min(self.entries, key=lambda e: e.get('turns', float('inf')))
        
        # Find victory with fewest deaths
        fewest_deaths_entry = min(self.entries, key=lambda e: e.get('deaths', float('inf')))
        
        return {
            'total_victories': len(self.entries),
            'good_endings': good_count,
            'bad_endings': bad_count,
            'fastest_victory': {
                'character': fastest.get('character_name', 'Unknown'),
                'turns': fastest.get('turns', 0),
                'date': fastest.get('date', 'Unknown')
            },
            'fewest_deaths': {
                'character': fewest_deaths_entry.get('character_name', 'Unknown'),
                'deaths': fewest_deaths_entry.get('deaths', 0),
                'date': fewest_deaths_entry.get('date', 'Unknown')
            }
        }


# Global instance
_hall_of_fame = None


def get_hall_of_fame() -> HallOfFame:
    """Get the global Hall of Fame instance.
    
    Returns:
        HallOfFame instance
    """
    global _hall_of_fame
    if _hall_of_fame is None:
        _hall_of_fame = HallOfFame()
    return _hall_of_fame

