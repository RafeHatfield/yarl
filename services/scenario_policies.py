"""Scenario-specific bot policies for automated testing.

Phase 12B: Bot policies for scenario harness
Phase 20C.1: Reflex potion user policy

This module contains bot policy implementations used exclusively in
scenario-based testing. These are NOT used in production gameplay.

Bot policies control the player during automated scenario runs,
implementing different behaviors for different test scenarios.

WARNING: Do not use these policies in production code. They are
designed for deterministic testing scenarios only.
"""

from typing import Any, Dict, Optional

from components.component_registry import ComponentType


# =============================================================================
# Scenario-Only Bot Policies
# =============================================================================

class ObserveOnlyPolicy:
    """Bot policy that always waits/does nothing.
    
    This policy is useful for testing game mechanics where we want to
    observe AI/environment behavior without player intervention.
    
    Usage: Passive observation scenarios (monster AI, environmental effects)
    """
    
    def choose_action(self, game_state: Any) -> Optional[Dict[str, Any]]:
        """Always return a wait action.
        
        Args:
            game_state: Current game state (unused)
            
        Returns:
            Wait action dict
        """
        return {'wait': True}


class TacticalFighterPolicy:
    """Simple deterministic melee fighter bot for combat scenarios.
    
    This bot:
    - Finds the nearest enemy (manhattan distance)
    - Moves toward it
    - Attacks when adjacent
    - Waits if no enemies or path blocked
    
    Usage: Basic combat scenarios, identity tests
    """
    
    def choose_action(self, game_state: Any) -> Optional[Dict[str, Any]]:
        player = game_state.player
        entities = game_state.entities or []
        game_map = game_state.game_map
        
        # Identify enemies (any living fighter with AI, not the player)
        enemies = [
            e for e in entities
            if e != player
            and getattr(e, 'fighter', None)
            and getattr(e.fighter, 'hp', 0) > 0
            and getattr(e, 'ai', None) is not None
        ]
        if not enemies:
            return {'wait': True}
        
        # Find nearest enemy by manhattan distance
        def manhattan(e):
            return abs(e.x - player.x) + abs(e.y - player.y)
        enemies.sort(key=manhattan)
        target = enemies[0]
        
        dx = target.x - player.x
        dy = target.y - player.y
        if abs(dx) <= 1 and abs(dy) <= 1:
            return {'attack': target}
        
        # Move one step toward target if not blocked
        step_x = 0 if dx == 0 else (1 if dx > 0 else -1)
        step_y = 0 if dy == 0 else (1 if dy > 0 else -1)

        dest_x, dest_y = player.x + step_x, player.y + step_y
        if (0 <= dest_x < game_map.width and 0 <= dest_y < game_map.height
            and not game_map.is_blocked(dest_x, dest_y)):
            blocking = next((e for e in entities if e.blocks and e.x == dest_x and e.y == dest_y), None)
            if blocking is None:
                return {'move': (step_x, step_y)}
        
        return {'wait': True}


class ReflexPotionUserPolicy:
    """Specialized bot for adrenaline potion reflex scenario.
    
    Phase 20C.1 Cleanup: This bot is used exclusively for the
    player_reflex_potion_identity scenario to ensure deterministic
    potion usage and bonus attack metrics.
    
    Behavior:
    - Uses adrenaline potion from inventory when available
    - Only uses if lightning_reflexes effect not already active
    - Delegates to TacticalFighterPolicy for combat after potion use
    
    Usage: player_reflex_potion_identity scenario ONLY
    """
    
    def choose_action(self, game_state: Any) -> Optional[Dict[str, Any]]:
        player = game_state.player
        
        # Check inventory for adrenaline potion and use it if found
        inventory = player.get_component_optional(ComponentType.INVENTORY)
        if inventory:
            for i, item in enumerate(inventory.items):
                if 'adrenaline' in item.name.lower():
                    # Only use if not already active
                    status_effects = player.get_component_optional(ComponentType.STATUS_EFFECTS)
                    if not status_effects or not status_effects.has_effect('lightning_reflexes'):
                        return {'use_item': i}
        
        # Fight
        return TacticalFighterPolicy().choose_action(game_state)


class RootPotionThrowerPolicy:
    """Specialized bot for root potion entangle scenario.
    
    Phase 20D.1: This bot throws root potions at approaching enemies
    to test the entangle mechanic, then fights in melee.
    
    Behavior:
    - If enemy is at distance 3-6 tiles and we have root potion: throw at enemy
    - Otherwise: delegate to TacticalFighterPolicy for melee combat
    
    Usage: root_potion_entangle_identity scenario
    """
    
    def choose_action(self, game_state: Any) -> Optional[Dict[str, Any]]:
        player = game_state.player
        entities = game_state.entities or []
        
        # Check inventory for root potion
        inventory = player.get_component_optional(ComponentType.INVENTORY)
        root_potion_index = None
        if inventory:
            for i, item in enumerate(inventory.items):
                if 'root' in item.name.lower() and 'potion' in item.name.lower():
                    root_potion_index = i
                    break
        
        # If we have a root potion, look for a target at throw range (3-6 tiles)
        if root_potion_index is not None:
            enemies = [
                e for e in entities
                if e != player
                and getattr(e, 'fighter', None)
                and getattr(e.fighter, 'hp', 0) > 0
                and getattr(e, 'ai', None) is not None
            ]
            
            for enemy in enemies:
                dist = abs(enemy.x - player.x) + abs(enemy.y - player.y)
                # Throw at enemies 3-6 tiles away (good throw range)
                if 3 <= dist <= 6:
                    return {'throw_item': root_potion_index, 'target': enemy}
        
        # No potion or no good target - fight normally
        return TacticalFighterPolicy().choose_action(game_state)


# =============================================================================
# Policy Factory
# =============================================================================

def make_scenario_bot_policy(name: str):
    """Factory function to create scenario bot policies by name.
    
    WARNING: These policies are for scenario testing only, not production.
    
    Args:
        name: Policy name. Supported:
            - "observe_only": Passive policy that always waits
            - "tactical_fighter": Simple melee fighter
            - "reflex_potion_user": Uses adrenaline potion turn 1, then fights
            - "root_potion_thrower": Throws root potions at enemies
            
    Returns:
        Bot policy instance
        
    Raises:
        ValueError: If policy name is not recognized
    """
    name_lower = name.lower().replace("-", "_").replace(" ", "_")
    
    if name_lower == "observe_only":
        return ObserveOnlyPolicy()
    if name_lower == "tactical_fighter":
        return TacticalFighterPolicy()
    if name_lower == "reflex_potion_user":
        return ReflexPotionUserPolicy()
    if name_lower == "root_potion_thrower":
        return RootPotionThrowerPolicy()
    
    raise ValueError(f"Unknown scenario bot policy: {name}")


__all__ = [
    'ObserveOnlyPolicy',
    'TacticalFighterPolicy',
    'ReflexPotionUserPolicy',
    'RootPotionThrowerPolicy',
    'make_scenario_bot_policy',
]

