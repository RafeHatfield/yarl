"""Monster Knowledge & Investigation System.

Phase 11: Tracks player knowledge about monster species and provides
tier-gated information for the targeting/inspect UI.

This system:
- Tracks encounters per monster species (seen, engaged, killed)
- Unlocks progressively more info as the player interacts with monsters
- Provides a MonsterInfoView for UI consumption

The knowledge system is READ-ONLY from a gameplay perspective - it observes
and describes but does not alter monster behavior.
"""

from dataclasses import dataclass, field
from typing import Optional, Set, Dict, Any, List, TYPE_CHECKING
from enum import IntEnum

from logger_config import get_logger

if TYPE_CHECKING:
    from entity import Entity

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# KNOWLEDGE TIER ENUM
# ═══════════════════════════════════════════════════════════════════════════════

class KnowledgeTier(IntEnum):
    """Knowledge tiers for monster information gating."""
    UNKNOWN = 0    # Never seen
    OBSERVED = 1   # Seen at least once
    BATTLED = 2    # Engaged in combat multiple times
    UNDERSTOOD = 3 # Killed several, or experienced special traits


# ═══════════════════════════════════════════════════════════════════════════════
# MONSTER KNOWLEDGE ENTRY
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class MonsterKnowledgeEntry:
    """Tracks player knowledge about a single monster species.
    
    Attributes:
        species_id: Unique identifier for the monster type (e.g., "orc", "zombie")
        seen_count: Times this type entered player LOS
        engaged_count: Times player engaged in combat (attacker or defender)
        killed_count: Times player (or allies) killed this type
        first_depth_seen: Earliest dungeon depth where this type was encountered
        traits_discovered: Set of trait names discovered (e.g., "plague_carrier")
    """
    species_id: str
    seen_count: int = 0
    engaged_count: int = 0
    killed_count: int = 0
    first_depth_seen: Optional[int] = None
    traits_discovered: Set[str] = field(default_factory=set)


# ═══════════════════════════════════════════════════════════════════════════════
# MONSTER INFO VIEW (UI DATA)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class MonsterInfoView:
    """UI-friendly struct for displaying monster information.
    
    This is the single source of truth for what the UI should display
    based on knowledge tier. Fields may be None/empty if not yet unlocked.
    
    Attributes:
        name: Monster name (always shown)
        glyph: Display character (always shown)
        faction_label: Faction name (Tier 1+)
        role_label: Monster role/archetype (Tier 1+)
        durability_label: Approx toughness (Tier 2+)
        damage_label: Approx damage output (Tier 2+)
        speed_label: Approx speed (Tier 1+ coarse, Tier 2+ detailed)
        accuracy_label: Approx hit chance (Tier 2+)
        evasion_label: Approx dodge ability (Tier 2+)
        special_warnings: List of warning strings (Tier 3+)
        behavior_labels: List of behavior traits (Tier 3+)
        advice_line: Short tactical advice (Tier 3+)
        knowledge_tier: The current knowledge tier (for debugging/display)
    """
    name: str
    glyph: str
    faction_label: Optional[str] = None
    role_label: Optional[str] = None
    durability_label: Optional[str] = None
    damage_label: Optional[str] = None
    speed_label: Optional[str] = None
    accuracy_label: Optional[str] = None
    evasion_label: Optional[str] = None
    special_warnings: List[str] = field(default_factory=list)
    behavior_labels: List[str] = field(default_factory=list)
    advice_line: Optional[str] = None
    knowledge_tier: KnowledgeTier = KnowledgeTier.UNKNOWN


# ═══════════════════════════════════════════════════════════════════════════════
# KNOWLEDGE TIER CALCULATION
# ═══════════════════════════════════════════════════════════════════════════════

def get_knowledge_tier(entry: MonsterKnowledgeEntry) -> KnowledgeTier:
    """Calculate knowledge tier from entry data.
    
    This is a pure function that determines tier based on thresholds
    defined in balance/knowledge_config.py.
    
    Args:
        entry: The knowledge entry for a monster species
        
    Returns:
        KnowledgeTier: The calculated tier (0-3)
    """
    from balance.knowledge_config import (
        TIER_1_SEEN_COUNT,
        TIER_2_ENGAGED_COUNT,
        TIER_3_KILLED_COUNT,
        TIER_3_TRAIT_EXPERIENCE_UNLOCKS,
        MAJOR_TRAITS,
    )
    
    # Tier 0: Never seen
    if entry.seen_count < TIER_1_SEEN_COUNT:
        return KnowledgeTier.UNKNOWN
    
    # Check for Tier 3 first (highest priority)
    # Tier 3: Killed enough OR experienced major trait
    if entry.killed_count >= TIER_3_KILLED_COUNT:
        return KnowledgeTier.UNDERSTOOD
    
    if TIER_3_TRAIT_EXPERIENCE_UNLOCKS:
        if entry.traits_discovered & MAJOR_TRAITS:
            return KnowledgeTier.UNDERSTOOD
    
    # Tier 2: Engaged enough
    if entry.engaged_count >= TIER_2_ENGAGED_COUNT:
        return KnowledgeTier.BATTLED
    
    # Tier 1: Seen at least once
    return KnowledgeTier.OBSERVED


# ═══════════════════════════════════════════════════════════════════════════════
# MONSTER KNOWLEDGE SYSTEM (SINGLETON SERVICE)
# ═══════════════════════════════════════════════════════════════════════════════

class MonsterKnowledgeSystem:
    """Manages monster knowledge tracking for a game run.
    
    This is the central manager that tracks all monster encounters and
    provides knowledge data for the UI. It should be owned by the game
    engine/world state and persist for the duration of a run.
    
    Usage:
        knowledge = get_monster_knowledge_system()
        knowledge.register_seen(monster)
        knowledge.register_engaged(monster)
        knowledge.register_killed(monster)
        knowledge.register_trait(monster, "plague_carrier")
        
        entry = knowledge.get_entry("orc")
        tier = get_knowledge_tier(entry)
    """
    
    def __init__(self):
        """Initialize the knowledge system with empty tracking."""
        self._entries: Dict[str, MonsterKnowledgeEntry] = {}
        self._seen_this_update: Set[int] = set()  # Entity IDs seen this update cycle
    
    def reset(self) -> None:
        """Reset all knowledge (for new game)."""
        self._entries.clear()
        self._seen_this_update.clear()
        logger.debug("[KNOWLEDGE] System reset")
    
    def _get_species_id(self, monster: 'Entity') -> str:
        """Extract species ID from a monster entity.
        
        Uses the entity's species_id property if available,
        otherwise falls back to lowercase name.
        
        Args:
            monster: The monster entity
            
        Returns:
            str: Species identifier (e.g., "orc", "plague_zombie")
        """
        if hasattr(monster, 'species_id') and monster.species_id:
            return monster.species_id
        # Fallback: use name, normalized
        return monster.name.lower().replace(" ", "_")
    
    def _get_or_create_entry(self, species_id: str) -> MonsterKnowledgeEntry:
        """Get or create a knowledge entry for a species.
        
        Args:
            species_id: The monster species identifier
            
        Returns:
            MonsterKnowledgeEntry: The entry (existing or new)
        """
        if species_id not in self._entries:
            self._entries[species_id] = MonsterKnowledgeEntry(species_id=species_id)
        return self._entries[species_id]
    
    def get_entry(self, species_id: str) -> MonsterKnowledgeEntry:
        """Get knowledge entry for a species (or default empty entry).
        
        Args:
            species_id: The monster species identifier
            
        Returns:
            MonsterKnowledgeEntry: The entry or a default empty one
        """
        return self._entries.get(species_id, MonsterKnowledgeEntry(species_id=species_id))
    
    def begin_update_cycle(self) -> None:
        """Call at the start of each game update to reset per-update tracking."""
        self._seen_this_update.clear()
    
    def register_seen(self, monster: 'Entity', current_depth: Optional[int] = None) -> None:
        """Register that a monster type was seen (entered player LOS).
        
        Should be called when a monster enters the player's field of view.
        Only increments once per monster per update cycle to avoid spam.
        
        Args:
            monster: The monster entity that was seen
            current_depth: Current dungeon depth (for first_depth_seen tracking)
        """
        # Avoid counting the same monster multiple times per update
        monster_id = id(monster)
        if monster_id in self._seen_this_update:
            return
        self._seen_this_update.add(monster_id)
        
        species_id = self._get_species_id(monster)
        entry = self._get_or_create_entry(species_id)
        
        entry.seen_count += 1
        
        # Track first depth seen
        if current_depth is not None:
            if entry.first_depth_seen is None:
                entry.first_depth_seen = current_depth
            else:
                entry.first_depth_seen = min(entry.first_depth_seen, current_depth)
        
        logger.debug(f"[KNOWLEDGE] Registered seen: {species_id} (count: {entry.seen_count})")
    
    def register_engaged(self, monster: 'Entity') -> None:
        """Register that player engaged in combat with a monster type.
        
        Should be called when:
        - Player attacks this monster type, OR
        - Monster attacks the player
        
        Args:
            monster: The monster entity involved in combat
        """
        species_id = self._get_species_id(monster)
        entry = self._get_or_create_entry(species_id)
        
        entry.engaged_count += 1
        
        # Also count as seen if not already
        if entry.seen_count == 0:
            entry.seen_count = 1
        
        logger.debug(f"[KNOWLEDGE] Registered engaged: {species_id} (count: {entry.engaged_count})")
    
    def register_killed(self, monster: 'Entity') -> None:
        """Register that player killed a monster of this type.
        
        Should be called when player (or player-controlled allies) kills
        a monster.
        
        Args:
            monster: The monster entity that was killed
        """
        species_id = self._get_species_id(monster)
        entry = self._get_or_create_entry(species_id)
        
        entry.killed_count += 1
        
        # Also count as seen/engaged if not already
        if entry.seen_count == 0:
            entry.seen_count = 1
        if entry.engaged_count == 0:
            entry.engaged_count = 1
        
        logger.debug(f"[KNOWLEDGE] Registered killed: {species_id} (count: {entry.killed_count})")
    
    def register_trait(self, monster: 'Entity', trait: str) -> None:
        """Register that a monster trait was discovered/experienced.
        
        Should be called when the monster manifests a notable behavior:
        - Applies plague effect → "plague_carrier"
        - Triggers bonus attack → "fast_attacker"
        - Swarm retargeting → "swarm_ai"
        - Steps into portal → "portal_curious"
        
        Args:
            monster: The monster entity that exhibited the trait
            trait: The trait name (should match constants in knowledge_config.py)
        """
        species_id = self._get_species_id(monster)
        entry = self._get_or_create_entry(species_id)
        
        entry.traits_discovered.add(trait)
        
        logger.debug(f"[KNOWLEDGE] Registered trait: {species_id} -> {trait}")
    
    def get_all_entries(self) -> Dict[str, MonsterKnowledgeEntry]:
        """Get all knowledge entries (for bestiary display).
        
        Returns:
            Dict mapping species_id to MonsterKnowledgeEntry
        """
        return dict(self._entries)


# ═══════════════════════════════════════════════════════════════════════════════
# MONSTER INFO VIEW GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

def _get_faction_label(monster: 'Entity') -> Optional[str]:
    """Get human-readable faction label for a monster."""
    from components.faction import Faction, get_faction_display_name
    
    faction = getattr(monster, 'faction', None)
    if faction is None or faction == Faction.NEUTRAL:
        return None
    
    return get_faction_display_name(faction)


def _get_role_label(monster: 'Entity') -> Optional[str]:
    """Derive role label from monster tags or abilities.
    
    Returns labels like: "Brute", "Skirmisher", "Swarm", "Caster", etc.
    """
    tags = getattr(monster, 'tags', None) or []
    abilities = getattr(monster, 'special_abilities', None) or []
    name = monster.name.lower()
    
    # Check for specific roles based on tags/abilities
    if 'swarm' in abilities:
        return "Swarm"
    if 'boss' in tags or getattr(monster, 'is_boss', False):
        return "Boss"
    if 'mindless' in tags:
        return "Mindless"
    if 'venomous' in tags:
        return "Venomous"
    if 'regenerating' in tags:
        return "Regenerator"
    
    # Infer from name
    if 'brute' in name:
        return "Brute"
    if 'scout' in name:
        return "Scout"
    if 'blademaster' in name or 'veteran' in name:
        return "Elite"
    if 'chieftain' in name or 'ancient' in name:
        return "Leader"
    
    return None


def _get_durability_label(monster: 'Entity') -> Optional[str]:
    """Get durability label based on HP and defense."""
    from balance.knowledge_config import (
        DURABILITY_FRAGILE_MAX,
        DURABILITY_STURDY_MAX,
        DURABILITY_TOUGH_MAX,
    )
    from components.component_registry import ComponentType
    
    fighter = monster.get_component_optional(ComponentType.FIGHTER)
    if not fighter:
        return None
    
    # Effective durability = max_hp + (defense * 5)
    defense = getattr(fighter, 'base_defense', 0)
    durability = fighter.max_hp + (defense * 5)
    
    if durability <= DURABILITY_FRAGILE_MAX:
        return "fragile"
    elif durability <= DURABILITY_STURDY_MAX:
        return "sturdy"
    elif durability <= DURABILITY_TOUGH_MAX:
        return "very tough"
    else:
        return "monstrous"


def _get_damage_label(monster: 'Entity') -> Optional[str]:
    """Get damage label based on average damage output."""
    from balance.knowledge_config import (
        DAMAGE_LIGHT_MAX,
        DAMAGE_MODERATE_MAX,
        DAMAGE_HEAVY_MAX,
    )
    from components.component_registry import ComponentType
    
    fighter = monster.get_component_optional(ComponentType.FIGHTER)
    if not fighter:
        return None
    
    damage_min = getattr(fighter, 'damage_min', 0)
    damage_max = getattr(fighter, 'damage_max', 0)
    power = getattr(fighter, 'base_power', 0)
    
    avg_damage = ((damage_min + damage_max) / 2) + power
    
    if avg_damage <= DAMAGE_LIGHT_MAX:
        return "light"
    elif avg_damage <= DAMAGE_MODERATE_MAX:
        return "moderate"
    elif avg_damage <= DAMAGE_HEAVY_MAX:
        return "heavy"
    else:
        return "brutal"


def _get_speed_label(monster: 'Entity', detailed: bool = False) -> Optional[str]:
    """Get speed label based on speed_bonus ratio.
    
    Args:
        monster: The monster entity
        detailed: If True, return more detailed label (Tier 2+)
    """
    from balance.knowledge_config import (
        SPEED_SLUGGISH_MAX,
        SPEED_NORMAL_MAX,
        SPEED_FAST_MAX,
    )
    
    # Check for speed_bonus on entity or speed_bonus_tracker
    speed_bonus = getattr(monster, 'speed_bonus', None)
    if speed_bonus is None:
        from components.component_registry import ComponentType
        tracker = monster.get_component_optional(ComponentType.SPEED_BONUS_TRACKER)
        if tracker:
            speed_bonus = tracker.speed_bonus_ratio
    
    if speed_bonus is None:
        speed_bonus = 1.0  # Default
    
    if speed_bonus <= SPEED_SLUGGISH_MAX:
        return "sluggish"
    elif speed_bonus <= SPEED_NORMAL_MAX:
        return "normal" if detailed else None
    elif speed_bonus <= SPEED_FAST_MAX:
        return "fast"
    else:
        return "lightning fast" if detailed else "fast"


def _get_accuracy_label(monster: 'Entity') -> Optional[str]:
    """Get accuracy label."""
    from balance.knowledge_config import (
        ACCURACY_OFTEN_MISSES_MAX,
        ACCURACY_USUALLY_HITS_MAX,
    )
    from components.component_registry import ComponentType
    
    fighter = monster.get_component_optional(ComponentType.FIGHTER)
    if not fighter:
        return None
    
    accuracy = getattr(fighter, 'accuracy', 2)
    
    if accuracy <= ACCURACY_OFTEN_MISSES_MAX:
        return "often misses"
    elif accuracy <= ACCURACY_USUALLY_HITS_MAX:
        return "usually hits"
    else:
        return "rarely misses"


def _get_evasion_label(monster: 'Entity') -> Optional[str]:
    """Get evasion label."""
    from balance.knowledge_config import (
        EVASION_EASY_TO_HIT_MAX,
        EVASION_AVERAGE_MAX,
    )
    from components.component_registry import ComponentType
    
    fighter = monster.get_component_optional(ComponentType.FIGHTER)
    if not fighter:
        return None
    
    evasion = getattr(fighter, 'evasion', 1)
    
    if evasion <= EVASION_EASY_TO_HIT_MAX:
        return "easy to hit"
    elif evasion <= EVASION_AVERAGE_MAX:
        return None  # Average, don't display
    else:
        return "hard to hit"


def _get_special_warnings(monster: 'Entity', entry: MonsterKnowledgeEntry) -> List[str]:
    """Get special warning strings based on discovered traits and monster type."""
    from balance.knowledge_config import (
        TRAIT_PLAGUE_CARRIER,
        TRAIT_SWARM_AI,
        TRAIT_PORTAL_CURIOUS,
        TRAIT_FAST_ATTACKER,
    )
    
    warnings = []
    
    # Check discovered traits
    if TRAIT_PLAGUE_CARRIER in entry.traits_discovered:
        warnings.append("⚠ Carries the Plague of Restless Death")
    
    if TRAIT_SWARM_AI in entry.traits_discovered:
        warnings.append("⚠ Swarm behavior: retargets when adjacent to multiple foes")
    
    if TRAIT_FAST_ATTACKER in entry.traits_discovered:
        warnings.append("⚠ Fast attacker: can strike multiple times")
    
    if TRAIT_PORTAL_CURIOUS in entry.traits_discovered:
        warnings.append("Often steps into portals")
    
    # Also check monster tags/abilities directly for always-visible warnings
    tags = getattr(monster, 'tags', None) or []
    abilities = getattr(monster, 'special_abilities', None) or []
    
    if 'plague_carrier' in tags and TRAIT_PLAGUE_CARRIER not in entry.traits_discovered:
        warnings.append("⚠ Suspected plague carrier")
    
    if 'corrosion' in abilities:
        warnings.append("⚠ Acid: corrodes equipment")
    
    return warnings


def _get_behavior_labels(monster: 'Entity', entry: MonsterKnowledgeEntry) -> List[str]:
    """Get behavior labels based on traits and monster properties."""
    labels = []
    
    abilities = getattr(monster, 'special_abilities', None) or []
    tags = getattr(monster, 'tags', None) or []
    
    if 'swarm' in abilities:
        labels.append("Swarm")
    if 'mindless' in tags:
        labels.append("Mindless")
    if 'regenerating' in tags:
        labels.append("Regenerating")
    
    return labels


def _get_advice_line(monster: 'Entity', entry: MonsterKnowledgeEntry) -> Optional[str]:
    """Generate tactical advice based on monster type and discovered traits."""
    from balance.knowledge_config import TRAIT_SWARM_AI, TRAIT_PLAGUE_CARRIER, TRAIT_PORTAL_CURIOUS
    
    abilities = getattr(monster, 'special_abilities', None) or []
    tags = getattr(monster, 'tags', None) or []
    name = monster.name.lower()
    
    # Prioritize advice based on most dangerous traits
    if TRAIT_PLAGUE_CARRIER in entry.traits_discovered or 'plague_carrier' in tags:
        return "Avoid getting hit. Cure plague immediately with antidotes."
    
    if TRAIT_SWARM_AI in entry.traits_discovered or 'swarm' in abilities:
        return "Avoid being adjacent alongside other enemies; retargets chaotically."
    
    if 'corrosion' in abilities:
        return "Keep distance if possible. Each hit risks corroding your equipment."
    
    if TRAIT_PORTAL_CURIOUS in entry.traits_discovered:
        return "Use portals to redirect them away from you."
    
    # Speed-based advice
    speed_label = _get_speed_label(monster, detailed=True)
    if speed_label == "lightning fast":
        return "Very fast enemy. Build momentum slowly or use crowd control."
    
    if 'regenerating' in tags:
        return "Kill quickly before it regenerates. Focus fire is effective."
    
    return None


def get_monster_info_view(monster: 'Entity', knowledge_system: MonsterKnowledgeSystem) -> MonsterInfoView:
    """Generate a MonsterInfoView for a monster, gated by knowledge tier.
    
    This is the ONLY function that should determine what info is shown
    based on knowledge tier. All UI code should consume MonsterInfoView.
    
    Args:
        monster: The monster entity to generate info for
        knowledge_system: The knowledge system with player's knowledge
        
    Returns:
        MonsterInfoView: Tier-gated information for UI display
    """
    species_id = knowledge_system._get_species_id(monster)
    entry = knowledge_system.get_entry(species_id)
    tier = get_knowledge_tier(entry)
    
    # Basic info - always shown
    view = MonsterInfoView(
        name=monster.name,
        glyph=monster.char,
        knowledge_tier=tier,
    )
    
    # Tier 0 - Unknown: Only name and glyph
    if tier == KnowledgeTier.UNKNOWN:
        return view
    
    # Tier 1 - Observed: Add faction, role, coarse speed
    if tier >= KnowledgeTier.OBSERVED:
        view.faction_label = _get_faction_label(monster)
        view.role_label = _get_role_label(monster)
        view.speed_label = _get_speed_label(monster, detailed=False)
    
    # Tier 2 - Battled: Add combat stats
    if tier >= KnowledgeTier.BATTLED:
        view.durability_label = _get_durability_label(monster)
        view.damage_label = _get_damage_label(monster)
        view.speed_label = _get_speed_label(monster, detailed=True)
        view.accuracy_label = _get_accuracy_label(monster)
        view.evasion_label = _get_evasion_label(monster)
    
    # Tier 3 - Understood: Add warnings, behaviors, and advice
    if tier >= KnowledgeTier.UNDERSTOOD:
        view.special_warnings = _get_special_warnings(monster, entry)
        view.behavior_labels = _get_behavior_labels(monster, entry)
        view.advice_line = _get_advice_line(monster, entry)
    
    return view


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_knowledge_system_instance: Optional[MonsterKnowledgeSystem] = None


def get_monster_knowledge_system() -> MonsterKnowledgeSystem:
    """Get the singleton MonsterKnowledgeSystem instance.
    
    Creates the instance if it doesn't exist yet.
    
    Returns:
        MonsterKnowledgeSystem: The singleton instance
    """
    global _knowledge_system_instance
    if _knowledge_system_instance is None:
        _knowledge_system_instance = MonsterKnowledgeSystem()
    return _knowledge_system_instance


def reset_monster_knowledge_system() -> None:
    """Reset the knowledge system (call on new game start).
    
    This clears all knowledge and prepares for a fresh run.
    """
    global _knowledge_system_instance
    if _knowledge_system_instance is not None:
        _knowledge_system_instance.reset()
    else:
        _knowledge_system_instance = MonsterKnowledgeSystem()
