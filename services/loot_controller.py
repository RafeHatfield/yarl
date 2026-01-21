"""Loot controller for managing item distribution and pity mechanics.

This module implements a sophisticated loot system that:
- Tracks expected value (EV) targets for item categories across dungeon bands
- Maintains rolling windows to detect category droughts
- Applies soft pity (increased weights) when a category hasn't appeared
- Applies hard pity (guaranteed injection) if drought persists
- Provides telemetry for monitoring loot distribution trends

Key concepts:
- Band: Depth range (B1=1-5, B2=6-10, etc.)
- Category: Item type (healing, escape, identification, upgrade)
- EV: Expected value - target frequency per band
- Rolling window: Track last N floors for drought detection
- Pity: Soft (increase weight) → Hard (inject item)
"""

import yaml
import logging
import os
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict

from utils.resource_paths import get_resource_path

logger = logging.getLogger(__name__)


@dataclass
class BandEVTargets:
    """EV targets for a dungeon band."""
    healing_ev: float = 2.0
    escape_ev: float = 2.0
    identification_ev: float = 1.5
    upgrade_ev: float = 1.5
    
    def get_target(self, category: str) -> float:
        """Get EV target for a category.
        
        Args:
            category: Item category ('healing', 'escape', 'identification', 'upgrade')
            
        Returns:
            EV target value (0.0-5.0)
        """
        category_key = f"{category}_ev"
        return getattr(self, category_key, 1.0)
    
    def to_weights(self) -> Dict[str, float]:
        """Convert EV targets to relative weights for random selection.
        
        Returns:
            Dict mapping category to weight
        """
        total = self.healing_ev + self.escape_ev + self.identification_ev + self.upgrade_ev
        if total <= 0:
            return {}
        
        return {
            'healing': self.healing_ev / total,
            'escape': self.escape_ev / total,
            'identification': self.identification_ev / total,
            'upgrade': self.upgrade_ev / total,
        }


@dataclass
class PitySettings:
    """Configuration for pity mechanics."""
    window_floors: int = 3  # Floors to track in rolling window
    soft_bias_factor: float = 2.0  # Weight multiplier for soft pity
    hard_inject_at: int = 5  # Floors without item before hard injection


@dataclass
class CategoryWindow:
    """Rolling window tracking for a single category."""
    category: str
    window_floors: int
    window: List[int] = field(default_factory=list)  # Floor numbers where item appeared
    floors_since_last: int = 0  # Floors since last occurrence
    pity_triggered: bool = False  # Soft pity active
    hard_pity_queued: bool = False  # Hard inject queued
    
    def record_appearance(self, floor: int) -> None:
        """Record that item appeared on this floor.
        
        Args:
            floor: Current floor number
        """
        self.window.append(floor)
        # Keep only recent history
        if len(self.window) > self.window_floors:
            self.window.pop(0)
        
        self.floors_since_last = 0
        self.pity_triggered = False
        # Hard pity injection uses up the queue
        was_queued = self.hard_pity_queued
        self.hard_pity_queued = False
        
        if was_queued:
            logger.info(f"Hard pity injection satisfied for {self.category} on floor {floor}")
    
    def advance_floor(self, floor: int) -> None:
        """Advance to next floor without finding item.
        
        Args:
            floor: Current floor number
        """
        self.floors_since_last += 1
    
    def is_window_empty(self) -> bool:
        """Check if rolling window is empty (no items in recent floors).
        
        Returns:
            True if no items found in last window_floors
        """
        return len(self.window) == 0
    
    def get_floors_since_last(self) -> int:
        """Get floors since last appearance.
        
        Returns:
            Number of floors (0 if just appeared)
        """
        return self.floors_since_last


@dataclass
class BandLootState:
    """Loot state tracking for a dungeon band."""
    band_name: str
    floors_in_band: int  # e.g., 5 for B1 (levels 1-5)
    windows: Dict[str, CategoryWindow] = field(default_factory=dict)
    floor_counter: int = 0  # Floors elapsed in this band
    telemetry: List[Dict] = field(default_factory=list)  # Telemetry records
    
    def initialize_windows(self, window_floors: int) -> None:
        """Initialize rolling windows for all categories.
        
        Args:
            window_floors: Size of rolling window
        """
        for category in ['healing', 'escape', 'identification', 'upgrade']:
            self.windows[category] = CategoryWindow(category, window_floors)
    
    def get_window(self, category: str) -> Optional[CategoryWindow]:
        """Get window for a category.
        
        Args:
            category: Item category
            
        Returns:
            CategoryWindow or None if not found
        """
        return self.windows.get(category)


class LootController:
    """Controller for loot distribution with EV targeting and pity mechanics."""
    
    def __init__(self, policy_path: str = "config/loot_policy.yaml"):
        """Initialize loot controller.
        
        Args:
            policy_path: Relative path to loot policy YAML file (resolved via get_resource_path)
        """
        self.policy_path = get_resource_path(policy_path)
        self.bands: Dict[str, BandEVTargets] = {}
        self.pity_settings: PitySettings = PitySettings()
        self.band_states: Dict[str, BandLootState] = {}
        self.current_band: Optional[str] = None
        self.current_floor: int = 1
        
        self.load_policy()
    
    def load_policy(self) -> None:
        """Load loot policy from YAML file."""
        if not os.path.exists(self.policy_path):
            logger.warning(f"Loot policy not found at {self.policy_path}, using defaults")
            self._create_default_policy()
            return
        
        try:
            with open(self.policy_path, 'r') as f:
                data = yaml.safe_load(f)
            
            if not data or 'loot_policy' not in data:
                logger.warning("Invalid loot policy format, using defaults")
                self._create_default_policy()
                return
            
            policy = data['loot_policy']
            
            # Load bands
            if 'bands' in policy:
                for band_name, targets in policy['bands'].items():
                    self.bands[band_name] = BandEVTargets(**targets)
            
            # Load pity settings
            if 'pity' in policy:
                pity_data = policy['pity']
                self.pity_settings = PitySettings(
                    window_floors=pity_data.get('window_floors', 3),
                    soft_bias_factor=pity_data.get('soft_bias_factor', 2.0),
                    hard_inject_at=pity_data.get('hard_inject_at', 5)
                )
            
            logger.info(f"Loaded loot policy with {len(self.bands)} bands")
        
        except Exception as e:
            logger.error(f"Error loading loot policy: {e}")
            self._create_default_policy()
    
    def _create_default_policy(self) -> None:
        """Create default policy if loading fails."""
        self.bands = {
            'B1': BandEVTargets(2.5, 1.5, 1.0, 0.5),
            'B2': BandEVTargets(2.0, 2.0, 1.5, 1.0),
            'B3': BandEVTargets(1.5, 2.5, 2.0, 1.5),
            'B4': BandEVTargets(1.0, 2.0, 2.5, 2.0),
            'B5': BandEVTargets(0.5, 1.5, 2.0, 3.0),
        }
        self.pity_settings = PitySettings()
    
    def get_band_for_floor(self, floor: int) -> str:
        """Get band for a given floor.
        
        Args:
            floor: Dungeon level (1-25)
            
        Returns:
            Band name (B1-B5)
        """
        if floor <= 5:
            return 'B1'
        elif floor <= 10:
            return 'B2'
        elif floor <= 15:
            return 'B3'
        elif floor <= 20:
            return 'B4'
        else:
            return 'B5'
    
    def enter_floor(self, floor: int) -> None:
        """Called when entering a new floor.
        
        Args:
            floor: Floor number (1-25)
        """
        self.current_floor = floor
        band = self.get_band_for_floor(floor)
        
        if band != self.current_band:
            # Entering new band
            self.current_band = band
            if band not in self.band_states:
                self.band_states[band] = BandLootState(
                    band_name=band,
                    floors_in_band=5
                )
                self.band_states[band].initialize_windows(self.pity_settings.window_floors)
            
            logger.info(f"Entered band {band} at floor {floor}")
        
        state = self.band_states[self.current_band]
        state.floor_counter += 1
        
        # Advance all windows (no item found yet on this floor)
        for window in state.windows.values():
            window.advance_floor(floor)
    
    def record_item_found(self, floor: int, category: str) -> None:
        """Record that an item was found on this floor.
        
        Args:
            floor: Floor number
            category: Item category
        """
        if not self.current_band:
            logger.warning("No current band set, cannot record item")
            return
        
        state = self.band_states[self.current_band]
        window = state.windows.get(category)
        
        if window:
            window.record_appearance(floor)
            logger.debug(f"Recorded {category} item on floor {floor} ({self.current_band})")
    
    def end_floor(self) -> None:
        """Called at end of floor to update windows and check pity.
        
        Should be called after level completion/transition.
        """
        if not self.current_band:
            return
        
        state = self.band_states[self.current_band]
        
        # Check for soft pity triggers
        for category, window in state.windows.items():
            if window.is_window_empty() and not window.pity_triggered:
                window.pity_triggered = True
                telemetry = {
                    'event': 'soft_pity_triggered',
                    'band': self.current_band,
                    'category': category,
                    'floor': self.current_floor,
                    'windows_empty': True,
                }
                state.telemetry.append(telemetry)
                logger.warning(f"Soft pity triggered for {category} in {self.current_band} "
                             f"(floor {self.current_floor})")
            
            # Check for hard pity injection
            if window.floors_since_last >= self.pity_settings.hard_inject_at:
                if not window.hard_pity_queued:
                    window.hard_pity_queued = True
                    telemetry = {
                        'event': 'hard_pity_injected',
                        'band': self.current_band,
                        'category': category,
                        'floor': self.current_floor,
                        'floors_since_last': window.floors_since_last,
                    }
                    state.telemetry.append(telemetry)
                    logger.error(f"Hard pity injection queued for {category} in {self.current_band} "
                               f"(floor {self.current_floor}, {window.floors_since_last} floors dry)")
    
    def get_category_weights(self, category_bias: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        """Get current category weights, applying pity adjustments.
        
        Args:
            category_bias: Optional pre-existing bias adjustments
            
        Returns:
            Dict of category -> weight for random selection
        """
        if not self.current_band:
            return {}
        
        band_targets = self.bands.get(self.current_band)
        if not band_targets:
            return {}
        
        # Start with base weights
        weights = band_targets.to_weights()
        
        # Apply soft pity multiplier
        state = self.band_states[self.current_band]
        for category, window in state.windows.items():
            if window.pity_triggered:
                weights[category] *= self.pity_settings.soft_bias_factor
        
        # Apply user-provided bias if any
        if category_bias:
            for category, bias in category_bias.items():
                if category in weights:
                    weights[category] *= bias
        
        # Normalize weights
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}
        
        return weights
    
    def should_hard_inject(self, category: str) -> bool:
        """Check if hard pity injection is queued for a category.
        
        Args:
            category: Item category
            
        Returns:
            True if hard inject is queued
        """
        if not self.current_band:
            return False
        
        state = self.band_states[self.current_band]
        window = state.windows.get(category)
        
        return window.hard_pity_queued if window else False
    
    def consume_hard_inject(self, category: str) -> bool:
        """Consume a hard inject (mark as used).
        
        Call this after injecting an item to mark the pity as satisfied.
        
        Args:
            category: Item category
            
        Returns:
            True if injection was consumed
        """
        if not self.current_band:
            return False
        
        state = self.band_states[self.current_band]
        window = state.windows.get(category)
        
        if window and window.hard_pity_queued:
            # Record that injection occurred
            telemetry = {
                'event': 'hard_pity_satisfied',
                'band': self.current_band,
                'category': category,
                'floor': self.current_floor,
            }
            state.telemetry.append(telemetry)
            return True
        
        return False
    
    def get_telemetry(self, band: Optional[str] = None) -> List[Dict]:
        """Get telemetry events for monitoring loot distribution.
        
        Args:
            band: Specific band to get telemetry for, or None for all
            
        Returns:
            List of telemetry events
        """
        if band:
            return self.band_states.get(band, BandLootState('', 0)).telemetry
        
        all_telemetry = []
        for state in self.band_states.values():
            all_telemetry.extend(state.telemetry)
        return all_telemetry
    
    def get_ev_stats(self, band: str) -> Dict[str, Dict]:
        """Get EV statistics for a band (for trend analysis).
        
        Args:
            band: Band name
            
        Returns:
            Dict with category -> {target, found, floors}
        """
        if band not in self.bands:
            return {}
        
        band_targets = self.bands[band]
        state = self.band_states.get(band)
        
        stats = {}
        for category in ['healing', 'escape', 'identification', 'upgrade']:
            window = state.windows.get(category) if state else None
            found_count = len(window.window) if window else 0
            
            stats[category] = {
                'target_ev': band_targets.get_target(category),
                'found': found_count,
                'floors_elapsed': state.floor_counter if state else 0,
                'floors_since_last': window.floors_since_last if window else 0,
                'pity_active': window.pity_triggered if window else False,
            }
        
        return stats


# Global singleton
_loot_controller: Optional[LootController] = None


def get_loot_controller() -> LootController:
    """Get the global loot controller instance.
    
    Returns:
        LootController singleton
    """
    global _loot_controller
    if _loot_controller is None:
        _loot_controller = LootController()
    return _loot_controller


def reset_loot_controller() -> None:
    """Reset the global loot controller (for testing)."""
    global _loot_controller
    _loot_controller = None

