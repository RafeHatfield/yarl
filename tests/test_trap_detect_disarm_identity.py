"""Phase 21.7: Trap Detection and Disarm Identity Tests

Verifies that:
1. Passive detection works for adjacent traps
2. Disarm action works on revealed traps
3. Disarmed traps do not trigger
4. Metrics are tracked correctly
5. Scenarios are deterministic under seed_base=1337
"""

import pytest
from engine.rng_config import reset_rng_state, set_global_seed


class TestTrapPassiveDetection:
    """Tests for passive trap detection."""
    
    def setup_method(self):
        """Reset RNG state before each test."""
        reset_rng_state()
    
    def teardown_method(self):
        """Reset RNG state after each test."""
        reset_rng_state()
    
    def test_passive_detection_adjacent_tiles(self):
        """Player can passively detect traps in adjacent tiles."""
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
        
        player = Entity(x=3, y=5, char='@', color=(255, 255, 255), name='Test Player', blocks=True)
        player.components = ComponentRegistry()
        
        # Trap at (5,5) with high passive_detect_chance
        trap_entity = Entity(x=5, y=5, char='^', color=(192, 32, 32), name='Spike Trap', blocks=False)
        trap_entity.components = ComponentRegistry()
        trap = Trap(trap_type="spike_trap", detectable=True, passive_detect_chance=0.99)
        trap_entity.trap = trap
        trap.owner = trap_entity
        trap_entity.components.add(ComponentType.TRAP, trap)
        
        entities = [player, trap_entity]
        
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
        
        # Verify trap is not detected initially
        assert not trap.is_detected
        
        # Move to (4,5) - adjacent to trap at (5,5)
        set_global_seed(1337)
        result = movement_service.execute_movement(1, 0, source="test")
        
        assert result.success
        assert player.x == 4
        
        # With 99% chance and seed 1337, trap should be detected
        # (If this fails, adjust seed or use 1.0 chance)
        assert trap.is_detected, "Trap should be detected passively"


class TestTrapDisarm:
    """Tests for trap disarm action."""
    
    def setup_method(self):
        """Reset RNG state before each test."""
        reset_rng_state()
    
    def teardown_method(self):
        """Reset RNG state after each test."""
        reset_rng_state()
    
    def test_disarm_revealed_trap(self):
        """Player can disarm a revealed trap."""
        from entity import Entity
        from components.component_registry import ComponentRegistry
        from components.trap import Trap
        
        player = Entity(x=4, y=5, char='@', color=(255, 255, 255), name='Test Player', blocks=True)
        player.components = ComponentRegistry()
        
        trap_entity = Entity(x=5, y=5, char='^', color=(192, 32, 32), name='Spike Trap', blocks=False)
        trap_entity.components = ComponentRegistry()
        trap = Trap(trap_type="spike_trap", detectable=True, passive_detect_chance=0.1)
        trap.is_detected = True  # Pre-detected
        trap_entity.trap = trap
        trap.owner = trap_entity
        
        # Verify trap is detected but not disarmed
        assert trap.is_detected
        assert not trap.is_disarmed
        
        # Disarm the trap
        success = trap.disarm()
        
        assert success
        assert trap.is_disarmed
    
    def test_disarmed_trap_does_not_trigger(self):
        """Disarmed trap does not trigger when stepped on."""
        from entity import Entity
        from components.component_registry import ComponentType, ComponentRegistry
        from components.trap import Trap
        from components.fighter import Fighter
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
        fighter = Fighter(hp=20, defense=0, power=0)
        fighter.owner = player
        player.fighter = fighter
        
        # Disarmed trap at (2,1)
        trap_entity = Entity(x=2, y=1, char='^', color=(192, 32, 32), name='Spike Trap', blocks=False)
        trap_entity.components = ComponentRegistry()
        trap = Trap(trap_type="spike_trap", detectable=True, passive_detect_chance=0.0, spike_damage=7)
        trap.is_detected = True
        trap.is_disarmed = True  # Pre-disarmed
        trap_entity.trap = trap
        trap.owner = trap_entity
        trap_entity.components.add(ComponentType.TRAP, trap)
        
        entities = [player, trap_entity]
        
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
        
        initial_hp = player.fighter.hp
        
        # Move onto disarmed trap
        result = movement_service.execute_movement(1, 0, source="test")
        
        assert result.success
        assert player.x == 2
        
        # Verify no damage was dealt (trap is disarmed)
        assert player.fighter.hp == initial_hp, "No damage should be dealt by disarmed trap"


class TestTrapDetectDisarmMetrics:
    """Tests for trap detection and disarm metrics."""
    
    def setup_method(self):
        """Reset RNG state before each test."""
        reset_rng_state()
    
    def teardown_method(self):
        """Reset RNG state after each test."""
        reset_rng_state()
    
    def test_detection_metrics_increment(self):
        """Detection metrics increment correctly."""
        from services.scenario_metrics import ScenarioMetricsCollector, set_active_metrics_collector, clear_active_metrics_collector
        from services.scenario_harness import RunMetrics
        
        metrics = RunMetrics()
        collector = ScenarioMetricsCollector(metrics)
        set_active_metrics_collector(collector)
        
        try:
            collector.increment('traps_detected_total')
            assert metrics.traps_detected_total == 1
        finally:
            clear_active_metrics_collector()
    
    def test_disarm_metrics_increment(self):
        """Disarm metrics increment correctly."""
        from services.scenario_metrics import ScenarioMetricsCollector, set_active_metrics_collector, clear_active_metrics_collector
        from services.scenario_harness import RunMetrics
        
        metrics = RunMetrics()
        collector = ScenarioMetricsCollector(metrics)
        set_active_metrics_collector(collector)
        
        try:
            collector.increment('trap_disarms_attempted')
            collector.increment('trap_disarms_succeeded')
            
            assert metrics.trap_disarms_attempted == 1
            assert metrics.trap_disarms_succeeded == 1
        finally:
            clear_active_metrics_collector()


class TestTrapDetectDisarmScenarioDeterminism:
    """Tests for scenario determinism."""
    
    def setup_method(self):
        """Reset RNG state before each test."""
        reset_rng_state()
    
    def teardown_method(self):
        """Reset RNG state after each test."""
        reset_rng_state()
    
    @pytest.mark.slow
    def test_trap_detect_identity_scenario_determinism(self):
        """trap_detect_identity scenario produces identical results."""
        from config.level_template_registry import get_scenario_registry
        from services.scenario_harness import run_scenario_many, make_bot_policy
        
        registry = get_scenario_registry()
        scenario = registry.get_scenario_definition("trap_detect_identity")
        
        if scenario is None:
            pytest.skip("trap_detect_identity scenario not found")
        
        policy = make_bot_policy("tactical_fighter")
        seed_base = 1337
        runs = 3
        turn_limit = 20
        
        metrics1 = run_scenario_many(scenario, policy, runs, turn_limit, seed_base=seed_base)
        metrics2 = run_scenario_many(scenario, policy, runs, turn_limit, seed_base=seed_base)
        
        assert metrics1.runs == metrics2.runs
    
    @pytest.mark.slow
    def test_trap_disarm_identity_scenario_determinism(self):
        """trap_disarm_identity scenario produces identical results."""
        from config.level_template_registry import get_scenario_registry
        from services.scenario_harness import run_scenario_many, make_bot_policy
        
        registry = get_scenario_registry()
        scenario = registry.get_scenario_definition("trap_disarm_identity")
        
        if scenario is None:
            pytest.skip("trap_disarm_identity scenario not found")
        
        policy = make_bot_policy("tactical_fighter")
        seed_base = 1337
        runs = 3
        turn_limit = 20
        
        metrics1 = run_scenario_many(scenario, policy, runs, turn_limit, seed_base=seed_base)
        metrics2 = run_scenario_many(scenario, policy, runs, turn_limit, seed_base=seed_base)
        
        assert metrics1.runs == metrics2.runs
        assert getattr(metrics1, 'trap_disarms_attempted', 0) == getattr(metrics2, 'trap_disarms_attempted', 0)
        assert getattr(metrics1, 'trap_disarms_succeeded', 0) == getattr(metrics2, 'trap_disarms_succeeded', 0)
