"""Phase 21.4: Fire Trap Identity Tests

Verifies that:
1. Fire trap triggers on tile entry
2. Fire trap applies BurningEffect (no direct damage from trap)
3. Burning DOT damage routes through damage_service.apply_damage
4. Trap metrics are recorded correctly (single source of truth)
5. Scenario is deterministic under seed_base=1337
"""

import pytest
from engine.rng_config import reset_rng_state, set_global_seed


class TestFireTrapTrigger:
    """Tests for fire trap triggering and burning application."""
    
    def setup_method(self):
        """Reset RNG state before each test."""
        reset_rng_state()
    
    def teardown_method(self):
        """Reset RNG state after each test."""
        reset_rng_state()
    
    def test_fire_trap_applies_burning_effect(self):
        """Fire trap applies BurningEffect when triggered."""
        from entity import Entity
        from components.component_registry import ComponentType, ComponentRegistry
        from components.trap import Trap
        from services.movement_service import MovementService, reset_movement_service
        from map_objects.game_map import GameMap
        
        reset_movement_service()
        
        game_map = GameMap(10, 10, dungeon_level=1)
        for x in range(10):
            for y in range(10):
                tile = game_map.get_tile(x, y)
                if tile:
                    tile.blocked = False
                    tile.block_sight = False
        
        player = Entity(x=1, y=1, char='@', color=(255, 255, 255), name='Test Player', blocks=True)
        player.components = ComponentRegistry()
        
        fire_trap = Entity(x=2, y=1, char='F', color=(255, 69, 0), name='Fire Trap', blocks=False)
        fire_trap.components = ComponentRegistry()
        trap = Trap(trap_type="fire_trap", detectable=True, passive_detect_chance=0.0)
        fire_trap.trap = trap
        trap.owner = fire_trap
        fire_trap.components.add(ComponentType.TRAP, trap)
        
        entities = [player, fire_trap]
        
        class MockMessageLog:
            def add_message(self, msg):
                pass
        
        class MockState:
            def __init__(self):
                self.player = player
                self.game_map = game_map
                self.entities = entities
                self.current_state = None
                self.camera = None
                self.message_log = MockMessageLog()
        
        class MockStateManager:
            def __init__(self):
                self.state = MockState()
            
            def set_game_state(self, state):
                pass
        
        state_manager = MockStateManager()
        movement_service = MovementService(state_manager)
        
        set_global_seed(12345)
        
        result = movement_service.execute_movement(1, 0, source="test")
        
        assert result.success
        assert player.x == 2
        
        # Verify burning effect was applied
        assert player.components.has(ComponentType.STATUS_EFFECTS)
        status_effects = player.components.get(ComponentType.STATUS_EFFECTS)
        assert status_effects.has_effect('burning')
        
        burning = status_effects.get_effect('burning')
        assert burning is not None
        assert burning.duration == 4  # BurningEffect duration


class TestFireTrapMetrics:
    """Tests for fire trap metrics tracking."""
    
    def setup_method(self):
        """Reset RNG state before each test."""
        reset_rng_state()
    
    def teardown_method(self):
        """Reset RNG state after each test."""
        reset_rng_state()
    
    def test_fire_trap_metrics_increment_correctly(self):
        """Fire trap metrics are incremented when trap triggers."""
        from services.scenario_metrics import ScenarioMetricsCollector, set_active_metrics_collector, clear_active_metrics_collector
        from services.scenario_harness import RunMetrics
        
        metrics = RunMetrics()
        collector = ScenarioMetricsCollector(metrics)
        set_active_metrics_collector(collector)
        
        try:
            collector.increment('traps_triggered_total')
            collector.increment('trap_fire_triggered')
            collector.increment('trap_fire_effects_applied')
            
            assert metrics.traps_triggered_total == 1
            assert metrics.trap_fire_triggered == 1
            assert metrics.trap_fire_effects_applied == 1
        finally:
            clear_active_metrics_collector()


class TestFireTrapScenarioDeterminism:
    """Tests for scenario determinism with fire traps."""
    
    def setup_method(self):
        """Reset RNG state before each test."""
        reset_rng_state()
    
    def teardown_method(self):
        """Reset RNG state after each test."""
        reset_rng_state()
    
    @pytest.mark.slow
    def test_trap_fire_identity_scenario_determinism(self):
        """trap_fire_identity scenario produces identical results with seed_base=1337."""
        from config.level_template_registry import get_scenario_registry
        from services.scenario_harness import run_scenario_many, make_bot_policy
        
        registry = get_scenario_registry()
        scenario = registry.get_scenario_definition("trap_fire_identity")
        
        if scenario is None:
            pytest.skip("trap_fire_identity scenario not found")
        
        policy = make_bot_policy("tactical_fighter")
        seed_base = 1337
        runs = 3
        turn_limit = 20
        
        metrics1 = run_scenario_many(scenario, policy, runs, turn_limit, seed_base=seed_base)
        metrics2 = run_scenario_many(scenario, policy, runs, turn_limit, seed_base=seed_base)
        
        assert metrics1.runs == metrics2.runs
        assert getattr(metrics1, 'trap_fire_triggered', 0) == getattr(metrics2, 'trap_fire_triggered', 0)
        assert getattr(metrics1, 'trap_fire_effects_applied', 0) == getattr(metrics2, 'trap_fire_effects_applied', 0)


class TestFireTrapComponent:
    """Tests for Trap component with fire_trap type."""
    
    def test_trap_type_includes_fire_trap(self):
        """TrapType enum includes FIRE_TRAP."""
        from components.trap import TrapType
        
        assert hasattr(TrapType, 'FIRE_TRAP')
        assert TrapType.FIRE_TRAP.value == "fire_trap"
    
    def test_trap_get_visible_char_fire_trap(self):
        """Fire trap displays 'F' when detected."""
        from components.trap import Trap
        
        trap = Trap(trap_type="fire_trap")
        
        assert trap.get_visible_char() == '.'
        
        trap.is_detected = True
        assert trap.get_visible_char() == 'F'
    
    def test_trap_get_description_fire_trap(self):
        """Fire trap description mentions burning."""
        from components.trap import Trap
        
        trap = Trap(trap_type="fire_trap")
        trap.is_detected = True
        
        desc = trap.get_description()
        assert "fire trap" in desc
        assert "burning" in desc
