"""Dual-Mode Consumable Effects Dispatcher (Phase 20D.1).

This module provides a minimal, reusable model for consumables that behave
differently when CONSUMED (drunk) vs THROWN at a target.

Design Goals:
- Single dispatcher for dual-mode consumables
- Support exactly ONE effect per mode for v1
- No scripting, no chaining
- Legacy consumables MUST continue to work unchanged

Supported effect kinds:
1. apply_status_effect - Instantiate and apply a StatusEffect

Usage:
    Apply an effect when a dual-mode consumable is used:
    
    from services.consumable_effects import apply_consumable_effect, EffectMode
    
    results = apply_consumable_effect(
        mode=EffectMode.THROWN,
        effect_spec={'type': 'status_effect', 'effect_class': 'EntangledEffect', 'duration': 3},
        user=player,
        target=enemy,
        state_manager=state_manager
    )
"""

import logging
from enum import Enum, auto
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from entity import Entity

logger = logging.getLogger(__name__)


class EffectMode(Enum):
    """Mode of consumable usage."""
    CONSUMED = auto()  # Drunk/used on self
    THROWN = auto()    # Thrown at a target


def apply_consumable_effect(
    mode: EffectMode,
    effect_spec: Dict[str, Any],
    user: 'Entity',
    target: Optional['Entity'],
    state_manager: Any = None,
    metrics_collector: Any = None
) -> List[Dict[str, Any]]:
    """Apply a consumable effect based on mode and specification.
    
    This is the main dispatcher for dual-mode consumables.
    
    Args:
        mode: EffectMode.CONSUMED or EffectMode.THROWN
        effect_spec: Effect specification dict with keys:
            - type: Effect type ('status_effect')
            - effect_class: Name of StatusEffect subclass to instantiate
            - duration: Optional duration override
            - Additional kwargs for the effect constructor
        user: Entity using/throwing the consumable
        target: Entity to apply effect to (target for THROWN, user for CONSUMED)
        state_manager: Optional state manager for complex effects
        metrics_collector: Optional metrics collector for tracking
    
    Returns:
        List of result dictionaries with messages and side effects
    """
    results = []
    
    if not effect_spec:
        logger.warning("apply_consumable_effect called with empty effect_spec")
        return results
    
    effect_type = effect_spec.get('type', 'status_effect')
    
    # Determine the actual target based on mode
    actual_target = target if mode == EffectMode.THROWN else user
    
    if not actual_target:
        from message_builder import MessageBuilder as MB
        results.append({'message': MB.warning("No target for effect!")})
        return results
    
    if effect_type == 'status_effect':
        results.extend(_apply_status_effect(
            effect_spec=effect_spec,
            target=actual_target,
            state_manager=state_manager
        ))
    else:
        logger.warning(f"Unknown effect type: {effect_type}")
    
    return results


def _apply_status_effect(
    effect_spec: Dict[str, Any],
    target: 'Entity',
    state_manager: Any = None
) -> List[Dict[str, Any]]:
    """Apply a status effect to an entity.
    
    Args:
        effect_spec: Effect specification with:
            - effect_class: Name of StatusEffect subclass
            - duration: Optional duration override
            - Additional kwargs for constructor
        target: Entity to apply effect to
        state_manager: Optional state manager
    
    Returns:
        List of result dictionaries
    """
    results = []
    
    effect_class_name = effect_spec.get('effect_class')
    if not effect_class_name:
        logger.error("effect_spec missing 'effect_class'")
        return results
    
    # Dynamically import the effect class
    try:
        from components import status_effects
        effect_class = getattr(status_effects, effect_class_name, None)
        
        if not effect_class:
            logger.error(f"Unknown status effect class: {effect_class_name}")
            return results
        
    except ImportError as e:
        logger.error(f"Failed to import status_effects: {e}")
        return results
    
    # Build constructor kwargs
    kwargs = {'owner': target}
    if 'duration' in effect_spec:
        kwargs['duration'] = effect_spec['duration']
    
    # Pass any additional kwargs
    for key, value in effect_spec.items():
        if key not in ('type', 'effect_class', 'duration'):
            kwargs[key] = value
    
    # Ensure target has status_effects component
    from components.component_registry import ComponentType
    from components.status_effects import StatusEffectManager
    
    if not target.components.has(ComponentType.STATUS_EFFECTS):
        target.status_effects = StatusEffectManager(target)
        target.components.add(ComponentType.STATUS_EFFECTS, target.status_effects)
    
    # Create and apply the effect
    try:
        effect = effect_class(**kwargs)
        effect_results = target.status_effects.add_effect(effect)
        results.extend(effect_results)
        
        logger.debug(f"Applied {effect_class_name} to {target.name} (duration={effect.duration})")
        
    except Exception as e:
        logger.error(f"Failed to apply {effect_class_name}: {e}")
        from message_builder import MessageBuilder as MB
        results.append({'message': MB.failure(f"Effect failed: {e}")})
    
    return results

