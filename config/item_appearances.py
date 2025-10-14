"""Item Appearance Generation for Identification System.

This module handles the randomization of unidentified item appearances.
Each game session gets a new randomized mapping of item types to appearances.

Features:
- Scroll titles: Random phrases like "KIRJE XIXAXA", "ZELGO MER"
- Potion colors: Descriptions like "cyan potion", "bubbling green potion"
- Per-session randomization: Consistent within a game, different each run
- NetHack-inspired scroll names
"""

import random
from typing import Dict, List, Optional


# Scroll titles inspired by NetHack and traditional roguelikes
SCROLL_TITLES = [
    "KIRJE XIXAXA",      # Classic NetHack
    "ZELGO MER",
    "JUYED AWK YACC",    # "JUYED AWK" + "YACC" (Unix parser generator)
    "NR 9",
    "XIXAXA XOXAXA XUXAXA",
    "PRATYAVAYAH",
    "DAIYEN FOOELS",
    "LEP GEX VEN ZEA",
    "PRIRUTSENIE",
    "ELBIB YLOH",        # "HOLY BIBLE" reversed
    "VERR YED HORRE",
    "VENZAR BORGAVVE",
    "THARR",
    "YUM YUM",
    "KERNOD WEL",
    "ELAM EBOW",         # "WOMB MALE" reversed
    "DUAM XNAHT",        # "THANX MAUD" reversed
    "ANDOVA BEGARIN",
    "KIRJE",
    "VE FORBRYDERNE",
    "HACKEM MUCHE",
    "VELOX NEB",
    "FOOBIE BLETCH",
    "TEMOV",
    "GARVEN DEH",
    "READ ME",
    "ETAOIN SHRDLU",     # Most common letters in English
    "LOREM IPSUM",
    "FNORD",             # Discordianism reference
    "ZLORFIK",
    "GNIK SISI VLE",
    "HAPAX LEGOMENON",   # Linguistic term
    "EIRIS SAZUN",
    "GHOTI",             # George Bernard Shaw's phonetic spelling of "fish"
]

# Potion appearances: color + optional adjective + "potion"
POTION_COLORS = [
    "red",
    "blue",
    "green",
    "cyan",
    "magenta",
    "yellow",
    "amber",
    "golden",
    "silver",
    "black",
    "white",
    "purple",
    "orange",
    "brown",
    "gray",
    "pink",
    "violet",
    "indigo",
    "crimson",
    "emerald",
]

POTION_ADJECTIVES = [
    "",  # No adjective (most common)
    "",
    "",
    "bubbling",
    "fizzy",
    "cloudy",
    "clear",
    "dark",
    "bright",
    "murky",
    "sparkling",
    "glowing",
    "smoky",
    "viscous",
    "milky",
]


class AppearanceGenerator:
    """Generates and manages unidentified item appearances for a game session.
    
    This class handles:
    - Random assignment of appearances to item types
    - Consistent appearance mapping within a session
    - Support for scrolls, potions, rings, and wands
    """
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize the appearance generator.
        
        Args:
            seed: Optional random seed for deterministic generation (e.g., for testing)
        """
        self.seed = seed
        self._scroll_appearances: Dict[str, str] = {}
        self._potion_appearances: Dict[str, str] = {}
        self._ring_appearances: Dict[str, str] = {}
        self._wand_appearances: Dict[str, str] = {}
        self._initialized = False
    
    def initialize(self, item_types: Dict[str, List[str]]) -> None:
        """Initialize appearances for all item types.
        
        Args:
            item_types: Dictionary mapping category to list of item type names
                       Example: {"scroll": ["lightning_scroll", "fireball_scroll"],
                                "potion": ["healing_potion", "mana_potion"]}
        """
        if self._initialized:
            return
        
        # Set seed for reproducibility
        rng = random.Random(self.seed)
        
        # Generate scroll appearances
        if "scroll" in item_types:
            scroll_types = item_types["scroll"]
            scroll_titles = rng.sample(SCROLL_TITLES, min(len(scroll_types), len(SCROLL_TITLES)))
            self._scroll_appearances = {
                item_type: f"scroll labeled {title}"
                for item_type, title in zip(scroll_types, scroll_titles)
            }
        
        # Generate potion appearances
        if "potion" in item_types:
            potion_types = item_types["potion"]
            # Generate unique color + adjective combinations
            appearances = []
            colors = POTION_COLORS.copy()
            rng.shuffle(colors)
            
            for i, color in enumerate(colors[:len(potion_types)]):
                adjective = rng.choice(POTION_ADJECTIVES)
                if adjective:
                    appearances.append(f"{adjective} {color} potion")
                else:
                    appearances.append(f"{color} potion")
            
            self._potion_appearances = {
                item_type: appearance
                for item_type, appearance in zip(potion_types, appearances)
            }
        
        # TODO: Add ring and wand appearances when those systems are implemented
        # Rings: "wooden ring", "iron ring", "copper ring", etc.
        # Wands: "oak wand", "pine wand", "balsa wand", etc.
        
        self._initialized = True
    
    def get_appearance(self, item_type: str, category: str) -> Optional[str]:
        """Get the appearance for a specific item type.
        
        Args:
            item_type: The internal item type name (e.g., "healing_potion")
            category: The item category ("scroll", "potion", "ring", "wand")
        
        Returns:
            The unidentified appearance string, or None if not found
        """
        if category == "scroll":
            return self._scroll_appearances.get(item_type)
        elif category == "potion":
            return self._potion_appearances.get(item_type)
        elif category == "ring":
            return self._ring_appearances.get(item_type)
        elif category == "wand":
            return self._wand_appearances.get(item_type)
        
        return None
    
    def get_all_appearances(self) -> Dict[str, Dict[str, str]]:
        """Get all appearance mappings for serialization/saving.
        
        Returns:
            Dictionary of category -> (item_type -> appearance) mappings
        """
        return {
            "scroll": self._scroll_appearances.copy(),
            "potion": self._potion_appearances.copy(),
            "ring": self._ring_appearances.copy(),
            "wand": self._wand_appearances.copy(),
        }
    
    def set_appearances(self, appearances: Dict[str, Dict[str, str]]) -> None:
        """Set appearance mappings from loaded data.
        
        Used when loading a saved game to restore the appearance mappings.
        
        Args:
            appearances: Dictionary of category -> (item_type -> appearance) mappings
        """
        self._scroll_appearances = appearances.get("scroll", {}).copy()
        self._potion_appearances = appearances.get("potion", {}).copy()
        self._ring_appearances = appearances.get("ring", {}).copy()
        self._wand_appearances = appearances.get("wand", {}).copy()
        self._initialized = True


# Global singleton instance
_appearance_generator: Optional[AppearanceGenerator] = None


def get_appearance_generator() -> AppearanceGenerator:
    """Get the global appearance generator singleton.
    
    Returns:
        The global AppearanceGenerator instance
    """
    global _appearance_generator
    if _appearance_generator is None:
        _appearance_generator = AppearanceGenerator()
    return _appearance_generator


def reset_appearance_generator(seed: Optional[int] = None) -> AppearanceGenerator:
    """Reset the global appearance generator with a new seed.
    
    Used when starting a new game.
    
    Args:
        seed: Optional random seed for deterministic generation
        
    Returns:
        The newly created AppearanceGenerator instance
    """
    global _appearance_generator
    _appearance_generator = AppearanceGenerator(seed=seed)
    return _appearance_generator

