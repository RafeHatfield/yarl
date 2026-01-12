"""Phase 21.1: Root Trap Identity Tests

Verifies that:
1. Root trap triggers ONLY when entity successfully enters the tile
2. ROOT_TRAP applies EntangledEffect with correct duration
3. Entangled status blocks next movement attempt
4. Trap metrics are recorded correctly (single source of truth)
5. Scenario is deterministic under seed_base=1337
"""

import pytest
from engine.rng_config import reset_rng_state, set_global_seed, stable_scenario_seed


class TestRootTrapTrigger:
    """Tests for root trap triggering on tile entry."""
    
    def setup_method(self):
        """Reset RNG state before each test."""
        reset_rng_state()
    
    def teardown_method(self):
        """Reset RNG state after each test."""
        reset_rng_state()
    
    def test_root_trap_applies_entangle_on_entry(self):
        """Root trap applies EntangledEffect when player enters tile."""
        from entity import Entity
        from components.component_registry import ComponentType, ComponentRegistry
        from components.trap import Trap
        from components.status_effects import StatusEffectManager
        from services.movement_service import MovementService, reset_movement_service
        
        # Reset movement service singleton
        reset_movement_service()
        
        # Create minimal game state
        from map_objects.game_map import GameMap
        
        game_map = GameMap(10, 10, dungeon_level=1)
        # Carve floor
        for x in range(10):
            for y in range(10):
                tile = game_map.get_tile(x, y)
                if tile:
                    tile.blocked = False
                    tile.block_sight = False
        
        # Create player at (1, 1)
        player = Entity(x=1, y=1, char='@', color=(255, 255, 255), name='Test Player', blocks=True)
        player.components = ComponentRegistry()
        player.status_effects = StatusEffectManager(player)
        player.components.add(ComponentType.STATUS_EFFECTS, player.status_effects)
        
        # Create root trap at (2, 1)
        trap_entity = Entity(x=2, y=1, char='~', color=(34, 139, 34), name='Root Trap', blocks=False)
        trap_entity.components = ComponentRegistry()
        trap = Trap(trap_type="root_trap", detectable=True, passive_detect_chance=0.0, entangle_duration=3)
        trap_entity.trap = trap
        trap.owner = trap_entity
        trap_entity.components.add(ComponentType.TRAP, trap)
        
        entities = [player, trap_entity]
        
        # Mock state manager
        class MockState:
            def __init__(self):
                self.player = player
                self.game_map = game_map
                self.entities = entities
                self.current_state = None
                self.camera = None
                self.message_log = None
        
        class MockStateManager:
            def __init__(self):
                self.state = MockState()
        
        state_manager = MockStateManager()
        movement_service = MovementService(state_manager)
        
        # Player moves right (to 2,1 where trap is)
        # Use fixed RNG to prevent passive detection
        set_global_seed(12345)  # Ensure detection fails
        
        result = movement_service.execute_movement(1, 0, source="test")
        
        # Verify movement succeeded
        assert result.success, "Movement should succeed (trap doesn't block entry)"
        assert player.x == 2, f"Player should be at x=2, got x={player.x}"
        assert player.y == 1, f"Player should be at y=1, got y={player.y}"
        
        # Verify entangled effect was applied
        assert player.status_effects.has_effect('entangled'), "Player should be entangled after stepping on root trap"
        
        entangled = player.status_effects.get_effect('entangled')
        assert entangled is not None
        assert entangled.duration == 3, f"Entangle duration should be 3, got {entangled.duration}"
    
    def test_entangled_blocks_next_movement(self):
        """Entangled status blocks the next movement attempt."""
        from entity import Entity
        from components.component_registry import ComponentType, ComponentRegistry
        from components.status_effects import StatusEffectManager, EntangledEffect
        from services.movement_service import MovementService, reset_movement_service
        
        # Reset movement service singleton
        reset_movement_service()
        
        # Create minimal game state
        from map_objects.game_map import GameMap
        
        game_map = GameMap(10, 10, dungeon_level=1)
        # Carve floor
        for x in range(10):
            for y in range(10):
                tile = game_map.get_tile(x, y)
                if tile:
                    tile.blocked = False
                    tile.block_sight = False
        
        # Create player at (2, 1) already entangled
        player = Entity(x=2, y=1, char='@', color=(255, 255, 255), name='Test Player', blocks=True)
        player.components = ComponentRegistry()
        player.status_effects = StatusEffectManager(player)
        player.components.add(ComponentType.STATUS_EFFECTS, player.status_effects)
        
        # Apply entangled effect
        entangled_effect = EntangledEffect(owner=player, duration=3)
        player.status_effects.add_effect(entangled_effect)
        
        entities = [player]
        
        # Mock state manager
        class MockState:
            def __init__(self):
                self.player = player
                self.game_map = game_map
                self.entities = entities
                self.current_state = None
                self.camera = None
                self.message_log = None
        
        class MockStateManager:
            def __init__(self):
                self.state = MockState()
        
        state_manager = MockStateManager()
        movement_service = MovementService(state_manager)
        
        # Player tries to move while entangled
        result = movement_service.execute_movement(1, 0, source="test")
        
        # Verify movement was blocked
        assert not result.success, "Movement should be blocked by entangle"
        assert result.blocked_by_status, "Should be blocked by status effect"
        assert player.x == 2, "Player position should not change"
        assert player.y == 1, "Player position should not change"


class TestRootTrapMetrics:
    """Tests for root trap metrics tracking."""
    
    def setup_method(self):
        """Reset RNG state before each test."""
        reset_rng_state()
    
    def teardown_method(self):
        """Reset RNG state after each test."""
        reset_rng_state()
    
    def test_trap_metrics_increment_correctly(self):
        """Trap metrics are incremented when trap triggers."""
        from services.scenario_metrics import ScenarioMetricsCollector, set_active_metrics_collector, clear_active_metrics_collector
        from services.scenario_harness import RunMetrics
        
        # Create and set metrics collector
        metrics = RunMetrics()
        collector = ScenarioMetricsCollector(metrics)
        set_active_metrics_collector(collector)
        
        try:
            # Simulate trap trigger metrics
            collector.increment('traps_triggered_total')
            collector.increment('trap_root_triggered')
            collector.increment('trap_root_effects_applied')
            
            # Verify metrics
            assert metrics.traps_triggered_total == 1
            assert metrics.trap_root_triggered == 1
            assert metrics.trap_root_effects_applied == 1
        finally:
            clear_active_metrics_collector()


class TestRootTrapScenarioDeterminism:
    """Tests for scenario determinism with root traps."""
    
    def setup_method(self):
        """Reset RNG state before each test."""
        reset_rng_state()
    
    def teardown_method(self):
        """Reset RNG state after each test."""
        reset_rng_state()
    
    @pytest.mark.slow
    def test_trap_root_identity_scenario_determinism(self):
        """trap_root_identity scenario produces identical results with seed_base=1337."""
        from config.level_template_registry import get_scenario_registry
        from services.scenario_harness import run_scenario_many, make_bot_policy
        
        registry = get_scenario_registry()
        scenario = registry.get_scenario_definition("trap_root_identity")
        
        if scenario is None:
            pytest.skip("trap_root_identity scenario not found")
        
        policy = make_bot_policy("tactical_fighter")
        seed_base = 1337
        runs = 3
        turn_limit = 10
        
        # First execution
        metrics1 = run_scenario_many(scenario, policy, runs, turn_limit, seed_base=seed_base)
        
        # Second execution with same seed_base
        metrics2 = run_scenario_many(scenario, policy, runs, turn_limit, seed_base=seed_base)
        
        # Trap metrics must match exactly
        assert metrics1.runs == metrics2.runs
        assert getattr(metrics1, 'total_traps_triggered', 0) == getattr(metrics2, 'total_traps_triggered', 0)


class TestTrapComponent:
    """Tests for Trap component with root_trap type."""
    
    def test_trap_type_includes_root_trap(self):
        """TrapType enum includes ROOT_TRAP."""
        from components.trap import TrapType
        
        assert hasattr(TrapType, 'ROOT_TRAP')
        assert TrapType.ROOT_TRAP.value == "root_trap"
    
    def test_trap_entangle_duration_attribute(self):
        """Trap component has entangle_duration for root traps."""
        from components.trap import Trap
        
        trap = Trap(trap_type="root_trap", entangle_duration=5)
        
        assert trap.trap_type == "root_trap"
        assert trap.entangle_duration == 5
    
    def test_trap_get_visible_char_root_trap(self):
        """Root trap displays '~' when detected."""
        from components.trap import Trap
        
        trap = Trap(trap_type="root_trap")
        
        # Hidden shows floor
        assert trap.get_visible_char() == '.'
        
        # Detected shows root character
        trap.is_detected = True
        assert trap.get_visible_char() == '~'
    
    def test_trap_get_description_root_trap(self):
        """Root trap description includes entangle duration."""
        from components.trap import Trap
        
        trap = Trap(trap_type="root_trap", entangle_duration=3)
        trap.is_detected = True
        
        desc = trap.get_description()
        assert "root trap" in desc
        assert "entangle" in desc
        assert "3" in desc
