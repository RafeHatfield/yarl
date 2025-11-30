"""Pity system for guaranteed loot drops.

This module implements a "pity" mechanic that ensures players don't go too long
without receiving critical items like healing potions, panic items, or upgrades.
When a pity counter exceeds a band-based threshold, the next loot generation
will guarantee that item type.

Pity Mechanics:
    - Each tracked category has a counter (rooms since last drop)
    - Counter increments when a room is generated without that category
    - Counter resets when an item of that category drops
    - When counter exceeds threshold, pity triggers → guaranteed drop
    - Only triggers in normal rooms (not boss/treasure/etc.)
    - At most one pity item per room (priority: healing > panic > weapon > armor)

Band Thresholds:
    Healing:  B1=6, B2=5, B3+=4 rooms
    Panic:    B1=7, B2=6, B3+=5 rooms
    Weapon:   B1=8, B2=7, B3+=6 rooms
    Armor:    B1=8, B2=7, B3+=6 rooms

This creates a safety net that prevents extremely unlucky streaks while
allowing normal RNG-driven loot the rest of the time.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Callable, List

from balance.loot_tags import get_band_for_depth, get_loot_tags

logger = logging.getLogger(__name__)

# Debug flag for pity logging
PITY_DEBUG = True


# ═══════════════════════════════════════════════════════════════════════════════
# PITY THRESHOLDS - All tuning values in one place
# ═══════════════════════════════════════════════════════════════════════════════

# Healing pity thresholds (rooms without healing before trigger)
HEALING_PITY_THRESHOLDS: Dict[int, int] = {
    1: 6,   # B1: more forgiving
    2: 5,   # B2: slightly stricter
    3: 4,   # B3+: tighter healing requirements
    4: 4,
    5: 4,
}

# Panic item pity thresholds (teleports, haste, etc.)
PANIC_PITY_THRESHOLDS: Dict[int, int] = {
    1: 7,   # B1: generous - less panic needed early
    2: 6,   # B2: start needing escape options
    3: 5,   # B3+: panic items become critical
    4: 5,
    5: 5,
}

# Weapon upgrade pity thresholds
WEAPON_PITY_THRESHOLDS: Dict[int, int] = {
    1: 8,   # B1: weapons less critical early
    2: 7,   # B2: upgrades start mattering
    3: 6,   # B3+: need to keep up with monsters
    4: 6,
    5: 6,
}

# Armor upgrade pity thresholds (same as weapon for now)
ARMOR_PITY_THRESHOLDS: Dict[int, int] = {
    1: 8,   # B1: armor less critical early
    2: 7,   # B2: defense starts mattering
    3: 6,   # B3+: need to keep up with damage
    4: 6,
    5: 6,
}

# Special room roles that skip pity (swingy/spiky rooms)
PITY_EXEMPT_ROLES = {"boss", "miniboss", "end_boss", "treasure"}


# ═══════════════════════════════════════════════════════════════════════════════
# THRESHOLD ACCESSORS - Clean API for getting thresholds
# ═══════════════════════════════════════════════════════════════════════════════

def get_healing_pity_threshold(band: int) -> int:
    """Get the healing pity threshold for a band.
    
    Args:
        band: Band number (1-5)
        
    Returns:
        Number of rooms without healing before pity triggers
    """
    return HEALING_PITY_THRESHOLDS.get(band, HEALING_PITY_THRESHOLDS.get(5, 4))


def get_panic_pity_threshold(band: int) -> int:
    """Get the panic item pity threshold for a band.
    
    Args:
        band: Band number (1-5)
        
    Returns:
        Number of rooms without panic items before pity triggers
    """
    return PANIC_PITY_THRESHOLDS.get(band, PANIC_PITY_THRESHOLDS.get(5, 5))


def get_weapon_pity_threshold(band: int) -> int:
    """Get the weapon upgrade pity threshold for a band.
    
    Args:
        band: Band number (1-5)
        
    Returns:
        Number of rooms without weapon upgrades before pity triggers
    """
    return WEAPON_PITY_THRESHOLDS.get(band, WEAPON_PITY_THRESHOLDS.get(5, 6))


def get_armor_pity_threshold(band: int) -> int:
    """Get the armor upgrade pity threshold for a band.
    
    Args:
        band: Band number (1-5)
        
    Returns:
        Number of rooms without armor upgrades before pity triggers
    """
    return ARMOR_PITY_THRESHOLDS.get(band, ARMOR_PITY_THRESHOLDS.get(5, 6))


# ═══════════════════════════════════════════════════════════════════════════════
# PITY STATE
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class PityState:
    """Tracks pity counters for various loot categories.
    
    Pity counters increment when a room is generated without the tracked
    item type. When a counter exceeds the threshold, pity triggers and
    guarantees that item in the next applicable room.
    
    Attributes:
        rooms_since_healing_drop: Counter for rooms without healing items
        rooms_since_panic_item: Counter for rooms without panic/escape items
        rooms_since_weapon_upgrade: Counter for rooms without weapon upgrades
        rooms_since_armor_upgrade: Counter for rooms without armor upgrades
    """
    rooms_since_healing_drop: int = 0
    rooms_since_panic_item: int = 0
    rooms_since_weapon_upgrade: int = 0
    rooms_since_armor_upgrade: int = 0
    
    # ─────────────────────────────────────────────────────────────────────────
    # HEALING PITY
    # ─────────────────────────────────────────────────────────────────────────
    
    def reset_healing_counter(self) -> None:
        """Reset the healing pity counter (called when healing drops)."""
        if PITY_DEBUG and self.rooms_since_healing_drop > 0:
            logger.debug(
                f"[PITY] Healing counter reset (was {self.rooms_since_healing_drop})"
            )
        self.rooms_since_healing_drop = 0
    
    def increment_healing_counter(self) -> None:
        """Increment the healing pity counter."""
        self.rooms_since_healing_drop += 1
    
    def should_trigger_healing_pity(self, band: int) -> bool:
        """Check if healing pity should trigger.
        
        Args:
            band: Current band (1-5)
            
        Returns:
            True if pity should trigger
        """
        threshold = get_healing_pity_threshold(band)
        return self.rooms_since_healing_drop >= threshold
    
    # ─────────────────────────────────────────────────────────────────────────
    # PANIC ITEM PITY
    # ─────────────────────────────────────────────────────────────────────────
    
    def reset_panic_counter(self) -> None:
        """Reset the panic item pity counter."""
        if PITY_DEBUG and self.rooms_since_panic_item > 0:
            logger.debug(
                f"[PITY] Panic counter reset (was {self.rooms_since_panic_item})"
            )
        self.rooms_since_panic_item = 0
    
    def increment_panic_counter(self) -> None:
        """Increment the panic item pity counter."""
        self.rooms_since_panic_item += 1
    
    def should_trigger_panic_pity(self, band: int) -> bool:
        """Check if panic item pity should trigger.
        
        Args:
            band: Current band (1-5)
            
        Returns:
            True if pity should trigger
        """
        threshold = get_panic_pity_threshold(band)
        return self.rooms_since_panic_item >= threshold
    
    # ─────────────────────────────────────────────────────────────────────────
    # WEAPON UPGRADE PITY
    # ─────────────────────────────────────────────────────────────────────────
    
    def reset_weapon_upgrade_counter(self) -> None:
        """Reset the weapon upgrade pity counter."""
        if PITY_DEBUG and self.rooms_since_weapon_upgrade > 0:
            logger.debug(
                f"[PITY] Weapon upgrade counter reset (was {self.rooms_since_weapon_upgrade})"
            )
        self.rooms_since_weapon_upgrade = 0
    
    def increment_weapon_upgrade_counter(self) -> None:
        """Increment the weapon upgrade pity counter."""
        self.rooms_since_weapon_upgrade += 1
    
    def should_trigger_weapon_upgrade_pity(self, band: int) -> bool:
        """Check if weapon upgrade pity should trigger.
        
        Args:
            band: Current band (1-5)
            
        Returns:
            True if pity should trigger
        """
        threshold = get_weapon_pity_threshold(band)
        return self.rooms_since_weapon_upgrade >= threshold
    
    # ─────────────────────────────────────────────────────────────────────────
    # ARMOR UPGRADE PITY
    # ─────────────────────────────────────────────────────────────────────────
    
    def reset_armor_upgrade_counter(self) -> None:
        """Reset the armor upgrade pity counter."""
        if PITY_DEBUG and self.rooms_since_armor_upgrade > 0:
            logger.debug(
                f"[PITY] Armor upgrade counter reset (was {self.rooms_since_armor_upgrade})"
            )
        self.rooms_since_armor_upgrade = 0
    
    def increment_armor_upgrade_counter(self) -> None:
        """Increment the armor upgrade pity counter."""
        self.rooms_since_armor_upgrade += 1
    
    def should_trigger_armor_upgrade_pity(self, band: int) -> bool:
        """Check if armor upgrade pity should trigger.
        
        Args:
            band: Current band (1-5)
            
        Returns:
            True if pity should trigger
        """
        threshold = get_armor_pity_threshold(band)
        return self.rooms_since_armor_upgrade >= threshold
    
    # ─────────────────────────────────────────────────────────────────────────
    # STATE MANAGEMENT
    # ─────────────────────────────────────────────────────────────────────────
    
    def to_dict(self) -> Dict[str, int]:
        """Serialize pity state to a dictionary.
        
        Returns:
            Dictionary with pity counters
        """
        return {
            "rooms_since_healing_drop": self.rooms_since_healing_drop,
            "rooms_since_panic_item": self.rooms_since_panic_item,
            "rooms_since_weapon_upgrade": self.rooms_since_weapon_upgrade,
            "rooms_since_armor_upgrade": self.rooms_since_armor_upgrade,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> "PityState":
        """Deserialize pity state from a dictionary.
        
        Args:
            data: Dictionary with pity counters
            
        Returns:
            PityState instance
        """
        return cls(
            rooms_since_healing_drop=data.get("rooms_since_healing_drop", 0),
            rooms_since_panic_item=data.get("rooms_since_panic_item", 0),
            rooms_since_weapon_upgrade=data.get("rooms_since_weapon_upgrade", 0),
            rooms_since_armor_upgrade=data.get("rooms_since_armor_upgrade", 0),
        )


# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL STATE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════
# The pity state persists across rooms within a single run.
# It resets when a new game is started.

_pity_state: Optional[PityState] = None


# ═══════════════════════════════════════════════════════════════════════════════
# PITY TRIGGER TRACKING (for sanity harness reporting)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class PityTriggerStats:
    """Tracks how many times each pity type triggered."""
    healing_triggers: int = 0
    panic_triggers: int = 0
    weapon_triggers: int = 0
    armor_triggers: int = 0
    normal_rooms_processed: int = 0  # Rooms where pity was checked (not skipped)
    skipped_rooms: int = 0  # Rooms where pity was skipped (special rooms)
    
    def reset(self) -> None:
        """Reset all counters."""
        self.healing_triggers = 0
        self.panic_triggers = 0
        self.weapon_triggers = 0
        self.armor_triggers = 0
        self.normal_rooms_processed = 0
        self.skipped_rooms = 0
    
    def record_result(self, result: 'PityResult') -> None:
        """Record a pity check result.
        
        Args:
            result: Result from check_and_apply_pity()
        """
        if result.skipped_reason:
            self.skipped_rooms += 1
        else:
            self.normal_rooms_processed += 1
            if result.healing:
                self.healing_triggers += 1
            if result.panic:
                self.panic_triggers += 1
            if result.weapon_upgrade:
                self.weapon_triggers += 1
            if result.armor_upgrade:
                self.armor_triggers += 1
    
    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary for reporting."""
        return {
            "healing_triggers": self.healing_triggers,
            "panic_triggers": self.panic_triggers,
            "weapon_triggers": self.weapon_triggers,
            "armor_triggers": self.armor_triggers,
            "normal_rooms_processed": self.normal_rooms_processed,
            "skipped_rooms": self.skipped_rooms,
        }


_pity_trigger_stats: Optional[PityTriggerStats] = None


def get_pity_trigger_stats() -> PityTriggerStats:
    """Get the global pity trigger stats.
    
    Creates a new instance if none exists.
    
    Returns:
        PityTriggerStats instance
    """
    global _pity_trigger_stats
    if _pity_trigger_stats is None:
        _pity_trigger_stats = PityTriggerStats()
    return _pity_trigger_stats


def reset_pity_trigger_stats() -> None:
    """Reset pity trigger statistics (e.g., for new sanity test run)."""
    global _pity_trigger_stats
    _pity_trigger_stats = PityTriggerStats()


def get_pity_state() -> PityState:
    """Get the global pity state instance.
    
    Creates a new instance if none exists.
    
    Returns:
        PityState instance
    """
    global _pity_state
    if _pity_state is None:
        _pity_state = PityState()
    return _pity_state


def reset_pity_state() -> None:
    """Reset the global pity state (e.g., on new game).
    
    Resets all four counters: healing, panic, weapon_upgrade, armor_upgrade.
    """
    global _pity_state
    _pity_state = PityState()
    if PITY_DEBUG:
        logger.debug("[PITY] Pity state reset for new game (all 4 counters)")


def set_pity_state(state: PityState) -> None:
    """Set the global pity state (e.g., when loading a save).
    
    Args:
        state: PityState to use
    """
    global _pity_state
    _pity_state = state


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORY DETECTION HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _check_items_have_category(spawned_item_ids: List[str], category: str) -> bool:
    """Check if any spawned item has a specific category tag.
    
    Args:
        spawned_item_ids: List of item IDs spawned in the room
        category: Category to check for (e.g., "healing", "panic")
        
    Returns:
        True if at least one item has the category
    """
    for item_id in spawned_item_ids:
        tags = get_loot_tags(item_id)
        if tags and tags.has_category(category):
            return True
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# UNIFIED PITY CHECK & APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class PityResult:
    """Result of pity check for a room.
    
    Attributes:
        healing: True if healing pity triggered
        panic: True if panic pity triggered
        weapon_upgrade: True if weapon upgrade pity triggered
        armor_upgrade: True if armor upgrade pity triggered
        skipped_reason: If pity was skipped entirely, why (e.g., "special_room")
    """
    healing: bool = False
    panic: bool = False
    weapon_upgrade: bool = False
    armor_upgrade: bool = False
    skipped_reason: Optional[str] = None
    
    def any_triggered(self) -> bool:
        """Check if any pity type triggered."""
        return self.healing or self.panic or self.weapon_upgrade or self.armor_upgrade
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting."""
        return {
            "healing": self.healing,
            "panic": self.panic,
            "weapon_upgrade": self.weapon_upgrade,
            "armor_upgrade": self.armor_upgrade,
            "skipped_reason": self.skipped_reason,
        }


def check_and_apply_pity(
    depth: int,
    band: int,
    room_role: str,
    room_etp_exempt: bool,
    spawned_item_ids: List[str],
    spawn_healing_item_fn: Optional[Callable[[], bool]] = None,
    spawn_panic_item_fn: Optional[Callable[[], bool]] = None,
    spawn_upgrade_weapon_fn: Optional[Callable[[], bool]] = None,
    spawn_upgrade_armor_fn: Optional[Callable[[], bool]] = None,
    room_id: str = "unknown",
) -> PityResult:
    """Check pity state and apply at most one pity item to the room.
    
    Called once per room after normal item spawning is done.
    
    Behavior:
    - If room_role is special (boss, miniboss, end_boss, treasure): skip pity
    - If room_etp_exempt is True: skip pity
    - For normal rooms:
        - Update counters based on what items spawned naturally
        - Check each pity type in priority order: healing → panic → weapon → armor
        - Fire at most ONE pity type per room
        - Call the corresponding spawn function when pity triggers
    
    Args:
        depth: Current dungeon depth
        band: Current band (1-5)
        room_role: Room role ("normal", "boss", "treasure", etc.)
        room_etp_exempt: Whether room is ETP exempt
        spawned_item_ids: List of item IDs that naturally spawned in this room
        spawn_healing_item_fn: Function to spawn a healing item (returns True if success)
        spawn_panic_item_fn: Function to spawn a panic item (returns True if success)
        spawn_upgrade_weapon_fn: Function to spawn a weapon upgrade (returns True if success)
        spawn_upgrade_armor_fn: Function to spawn an armor upgrade (returns True if success)
        room_id: Room identifier for logging
        
    Returns:
        PityResult indicating which pity types triggered
    """
    result = PityResult()
    pity_state = get_pity_state()
    
    # ─────────────────────────────────────────────────────────────────────────
    # Skip pity for special rooms (boss/treasure/etc.)
    # ─────────────────────────────────────────────────────────────────────────
    if room_role in PITY_EXEMPT_ROLES:
        result.skipped_reason = f"special_room_{room_role}"
        if PITY_DEBUG:
            logger.debug(f"[PITY] Skipping pity for {room_role} room {room_id}")
        get_pity_trigger_stats().record_result(result)
        return result
    
    if room_etp_exempt:
        result.skipped_reason = "etp_exempt"
        if PITY_DEBUG:
            logger.debug(f"[PITY] Skipping pity for ETP-exempt room {room_id}")
        get_pity_trigger_stats().record_result(result)
        return result
    
    # ─────────────────────────────────────────────────────────────────────────
    # Determine what categories the room naturally had
    # ─────────────────────────────────────────────────────────────────────────
    had_healing = _check_items_have_category(spawned_item_ids, "healing")
    had_panic = _check_items_have_category(spawned_item_ids, "panic")
    had_weapon_upgrade = _check_items_have_category(spawned_item_ids, "upgrade_weapon")
    had_armor_upgrade = _check_items_have_category(spawned_item_ids, "upgrade_armor")
    
    # ─────────────────────────────────────────────────────────────────────────
    # Update counters based on what the room had
    # ─────────────────────────────────────────────────────────────────────────
    if had_healing:
        pity_state.reset_healing_counter()
    else:
        pity_state.increment_healing_counter()
    
    if had_panic:
        pity_state.reset_panic_counter()
    else:
        pity_state.increment_panic_counter()
    
    if had_weapon_upgrade:
        pity_state.reset_weapon_upgrade_counter()
    else:
        pity_state.increment_weapon_upgrade_counter()
    
    if had_armor_upgrade:
        pity_state.reset_armor_upgrade_counter()
    else:
        pity_state.increment_armor_upgrade_counter()
    
    # ─────────────────────────────────────────────────────────────────────────
    # Check and fire pity in priority order (at most one per room)
    # Priority: healing > panic > weapon > armor
    # ─────────────────────────────────────────────────────────────────────────
    
    # 1. Healing pity (highest priority - survival)
    if pity_state.should_trigger_healing_pity(band):
        if spawn_healing_item_fn and spawn_healing_item_fn():
            result.healing = True
            pity_state.reset_healing_counter()
            if PITY_DEBUG:
                logger.info(
                    f"[PITY] depth={depth} band=B{band} room={room_id} -> "
                    f"triggered healing pity (rooms_since_healing_drop={pity_state.rooms_since_healing_drop})"
                )
            # Record for stats before returning
            get_pity_trigger_stats().record_result(result)
            return result  # Only one pity per room
    
    # 2. Panic pity (escape options)
    if pity_state.should_trigger_panic_pity(band):
        if spawn_panic_item_fn and spawn_panic_item_fn():
            result.panic = True
            pity_state.reset_panic_counter()
            if PITY_DEBUG:
                logger.info(
                    f"[PITY] depth={depth} band=B{band} room={room_id} -> "
                    f"triggered panic pity (rooms_since_panic_item={pity_state.rooms_since_panic_item})"
                )
            # Record for stats before returning
            get_pity_trigger_stats().record_result(result)
            return result  # Only one pity per room
    
    # 3. Weapon upgrade pity
    if pity_state.should_trigger_weapon_upgrade_pity(band):
        if spawn_upgrade_weapon_fn and spawn_upgrade_weapon_fn():
            result.weapon_upgrade = True
            pity_state.reset_weapon_upgrade_counter()
            if PITY_DEBUG:
                logger.info(
                    f"[PITY] depth={depth} band=B{band} room={room_id} -> "
                    f"triggered weapon pity (rooms_since_weapon_upgrade={pity_state.rooms_since_weapon_upgrade})"
                )
            # Record for stats before returning
            get_pity_trigger_stats().record_result(result)
            return result  # Only one pity per room
    
    # 4. Armor upgrade pity (lowest priority)
    if pity_state.should_trigger_armor_upgrade_pity(band):
        if spawn_upgrade_armor_fn and spawn_upgrade_armor_fn():
            result.armor_upgrade = True
            pity_state.reset_armor_upgrade_counter()
            if PITY_DEBUG:
                logger.info(
                    f"[PITY] depth={depth} band=B{band} room={room_id} -> "
                    f"triggered armor pity (rooms_since_armor_upgrade={pity_state.rooms_since_armor_upgrade})"
                )
            # Record for stats before returning
            get_pity_trigger_stats().record_result(result)
            return result  # Only one pity per room
    
    # Record result (even if no pity triggered)
    get_pity_trigger_stats().record_result(result)
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# LEGACY API (kept for backward compatibility)
# ═══════════════════════════════════════════════════════════════════════════════

def check_and_apply_healing_pity(
    depth: int,
    room_had_healing: bool,
) -> bool:
    """Check pity state and determine if healing should be forced.
    
    LEGACY: Prefer using check_and_apply_pity() for new code.
    
    Call this after determining room loot but before finalizing.
    
    Args:
        depth: Current dungeon depth
        room_had_healing: Whether the room's loot includes healing
        
    Returns:
        True if healing pity should force a healing potion spawn
    """
    pity_state = get_pity_state()
    band = get_band_for_depth(depth)
    
    if room_had_healing:
        # Healing was present, reset counter
        pity_state.reset_healing_counter()
        return False
    else:
        # No healing, increment counter
        pity_state.increment_healing_counter()
        
        # Check if pity should trigger
        if pity_state.should_trigger_healing_pity(band):
            if PITY_DEBUG:
                logger.info(
                    f"[PITY] Healing pity triggered at depth {depth} (band B{band}), "
                    f"forcing healing_potion spawn"
                )
            # Don't reset here - let the caller spawn the item and then reset
            return True
        
        return False


def on_healing_pity_applied() -> None:
    """Call this after successfully spawning a pity healing item.
    
    LEGACY: When using check_and_apply_pity(), this is handled automatically.
    
    This resets the healing counter.
    """
    pity_state = get_pity_state()
    pity_state.reset_healing_counter()
    if PITY_DEBUG:
        logger.debug("[PITY] Healing counter reset after pity application")


def log_pity_status(depth: int) -> None:
    """Log current pity state for debugging.
    
    Args:
        depth: Current dungeon depth
    """
    if not PITY_DEBUG:
        return
    
    pity_state = get_pity_state()
    band = get_band_for_depth(depth)
    
    logger.debug(
        f"[PITY STATUS] Depth {depth} (Band B{band}): "
        f"healing={pity_state.rooms_since_healing_drop}/{get_healing_pity_threshold(band)}, "
        f"panic={pity_state.rooms_since_panic_item}/{get_panic_pity_threshold(band)}, "
        f"weapon={pity_state.rooms_since_weapon_upgrade}/{get_weapon_pity_threshold(band)}, "
        f"armor={pity_state.rooms_since_armor_upgrade}/{get_armor_pity_threshold(band)}"
    )
