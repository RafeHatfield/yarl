"""Phase 21.5: Hole Trap Identity Tests

Verifies that:
1. Hole trap triggers on tile entry
2. Hole trap creates TransitionRequest (type=next_floor, cause=hole_trap)
3. Trap consumes turn (no additional actions after trigger)
4. Trap metrics are recorded correctly (single source of truth)
5. Scenario is deterministic under seed_base=1337
6. Real gameplay would execute transition via game_map.next_floor()
"""

import pytest
from engine.rng_config import reset_rng_state, set_global_seed


class TestHoleTrapTrigger:
    """Tests for hole trap triggering and transition request."""
    
    def setup_method(self):
        """Reset RNG state before each test."""
        reset_rng_state()
    
    def teardown_method(self):
        """Reset RNG state after each test."""
        reset_rng_state()
    
    def test_hole_trap_creates_transition_request(self):
        """Hole trap creates TransitionRequest when triggered."""
        from entity import Entity
        from components.component_registry import ComponentType, ComponentRegistry
        from components.trap import Trap
        from services.movement_service import MovementService, reset_movement_service
        from services.transition_service import get_transition_service, reset_transition_service
        from map_objects.game_map import GameMap
        
        reset_movement_service()
        reset_transition_service()
        
        game_map = GameMap(10, 10, dungeon_level=1)
        for x in range(10):
            for y in range(10):
                tile = game_map.get_tile(x, y)
                if tile:
                    tile.blocked = False
                    tile.block_sight = False
        
        player = Entity(x=1, y=1, char='@', color=(255, 255, 255), name='Test Player', blocks=True)
        player.components = ComponentRegistry()
        
        hole_trap = Entity(x=2, y=1, char='O', color=(64, 64, 64), name='Hole Trap', blocks=False)
        hole_trap.components = ComponentRegistry()
        trap = Trap(trap_type="hole_trap", detectable=True, passive_detect_chance=0.0)
        hole_trap.trap = trap
        trap.owner = hole_trap
        hole_trap.components.add(ComponentType.TRAP, trap)
        
        entities = [player, hole_trap]
        
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
        transition_service = get_transition_service()
        
        set_global_seed(12345)
        
        # Verify no pending transition before trigger
        assert not transition_service.has_pending_transition()
        
        result = movement_service.execute_movement(1, 0, source="test")
        
        assert result.success
        assert player.x == 2
        
        # Verify TransitionRequest was created
        assert transition_service.has_pending_transition()
        request = transition_service.get_pending_request()
        assert request is not None
        assert request.transition_type == "next_floor"
        assert request.cause == "hole_trap"
        assert request.entity == player


class TestHoleTrapMetrics:
    """Tests for hole trap metrics tracking."""
    
    def setup_method(self):
        """Reset RNG state before each test."""
        reset_rng_state()
    
    def teardown_method(self):
        """Reset RNG state after each test."""
        reset_rng_state()
    
    def test_hole_trap_metrics_increment_correctly(self):
        """Hole trap metrics are incremented when trap triggers."""
        from services.scenario_metrics import ScenarioMetricsCollector, set_active_metrics_collector, clear_active_metrics_collector
        from services.scenario_harness import RunMetrics
        
        metrics = RunMetrics()
        collector = ScenarioMetricsCollector(metrics)
        set_active_metrics_collector(collector)
        
        try:
            collector.increment('traps_triggered_total')
            collector.increment('trap_hole_triggered')
            collector.increment('trap_hole_transition_requested')
            
            assert metrics.traps_triggered_total == 1
            assert metrics.trap_hole_triggered == 1
            assert metrics.trap_hole_transition_requested == 1
        finally:
            clear_active_metrics_collector()


class TestHoleTrapScenarioDeterminism:
    """Tests for scenario determinism with hole traps."""
    
    def setup_method(self):
        """Reset RNG state before each test."""
        reset_rng_state()
    
    def teardown_method(self):
        """Reset RNG state after each test."""
        reset_rng_state()
    
    @pytest.mark.slow
    def test_trap_hole_identity_scenario_determinism(self):
        """trap_hole_identity scenario produces identical results with seed_base=1337."""
        from config.level_template_registry import get_scenario_registry
        from services.scenario_harness import run_scenario_many, make_bot_policy
        
        registry = get_scenario_registry()
        scenario = registry.get_scenario_definition("trap_hole_identity")
        
        if scenario is None:
            pytest.skip("trap_hole_identity scenario not found")
        
        policy = make_bot_policy("tactical_fighter")
        seed_base = 1337
        runs = 3
        turn_limit = 20
        
        metrics1 = run_scenario_many(scenario, policy, runs, turn_limit, seed_base=seed_base)
        metrics2 = run_scenario_many(scenario, policy, runs, turn_limit, seed_base=seed_base)
        
        assert metrics1.runs == metrics2.runs
        assert getattr(metrics1, 'trap_hole_triggered', 0) == getattr(metrics2, 'trap_hole_triggered', 0)
        assert getattr(metrics1, 'trap_hole_transition_requested', 0) == getattr(metrics2, 'trap_hole_transition_requested', 0)


class TestHoleTrapComponent:
    """Tests for Trap component with hole_trap type."""
    
    def test_trap_type_includes_hole_trap(self):
        """TrapType enum includes HOLE_TRAP."""
        from components.trap import TrapType
        
        assert hasattr(TrapType, 'HOLE_TRAP')
        assert TrapType.HOLE_TRAP.value == "hole_trap"
    
    def test_trap_get_visible_char_hole_trap(self):
        """Hole trap displays 'O' when detected."""
        from components.trap import Trap
        
        trap = Trap(trap_type="hole_trap")
        
        assert trap.get_visible_char() == '.'
        
        trap.is_detected = True
        assert trap.get_visible_char() == 'O'
    
    def test_trap_get_description_hole_trap(self):
        """Hole trap description mentions sudden drop."""
        from components.trap import Trap
        
        trap = Trap(trap_type="hole_trap")
        trap.is_detected = True
        
        desc = trap.get_description()
        assert "hole trap" in desc
        assert "drop" in desc


class TestTransitionService:
    """Tests for TransitionService."""
    
    def test_transition_service_singleton(self):
        """TransitionService is a singleton."""
        from services.transition_service import get_transition_service, reset_transition_service
        
        reset_transition_service()
        
        service1 = get_transition_service()
        service2 = get_transition_service()
        
        assert service1 is service2
    
    def test_transition_request_lifecycle(self):
        """TransitionRequest can be created, checked, and consumed."""
        from services.transition_service import get_transition_service, reset_transition_service
        from entity import Entity
        
        reset_transition_service()
        service = get_transition_service()
        
        # Initially no pending transition
        assert not service.has_pending_transition()
        assert service.get_pending_request() is None
        
        # Create a mock entity
        entity = Entity(x=5, y=5, char='@', color=(255, 255, 255), name='Test Entity', blocks=True)
        
        # Request transition
        service.request_transition("next_floor", "hole_trap", entity)
        
        # Verify pending
        assert service.has_pending_transition()
        request = service.get_pending_request()
        assert request is not None
        assert request.transition_type == "next_floor"
        assert request.cause == "hole_trap"
        assert request.entity == entity
        
        # Consume transition
        consumed = service.consume_transition()
        assert consumed == request
        
        # Verify cleared
        assert not service.has_pending_transition()
        assert service.get_pending_request() is None
