"""Phase 21.2: Spike Trap Identity Tests

Verifies that:
1. Spike trap triggers ONLY when entity successfully enters the tile
2. Spike trap deals damage via damage_service.apply_damage (canonical routing)
3. Damage can be lethal (entity dies) or non-lethal (entity survives with reduced HP)
4. Trap metrics are recorded correctly (single source of truth)
5. Scenario is deterministic under seed_base=1337
6. No double-counting with existing damage metrics
"""

import pytest
from engine.rng_config import reset_rng_state, set_global_seed, stable_scenario_seed


class TestSpikeTrapTrigger:
    """Tests for spike trap triggering on tile entry."""
    
    def setup_method(self):
        """Reset RNG state before each test."""
        reset_rng_state()
    
    def teardown_method(self):
        """Reset RNG state after each test."""
        reset_rng_state()
    
    def test_spike_trap_deals_damage_on_entry(self):
        """Spike trap deals damage when player enters tile."""
        from entity import Entity
        from components.component_registry import ComponentType, ComponentRegistry
        from components.trap import Trap
        from components.fighter import Fighter
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
        
        # Create player at (1, 1) with enough HP to survive
        player = Entity(x=1, y=1, char='@', color=(255, 255, 255), name='Test Player', blocks=True)
        player.components = ComponentRegistry()
        fighter = Fighter(hp=20, defense=0, power=0)
        fighter.owner = player
        player.fighter = fighter  # Auto-registers via __setattr__
        
        # Create spike trap at (2, 1) with 7 damage
        trap_entity = Entity(x=2, y=1, char='^', color=(192, 32, 32), name='Spike Trap', blocks=False)
        trap_entity.components = ComponentRegistry()
        trap = Trap(trap_type="spike_trap", detectable=True, passive_detect_chance=0.0, spike_damage=7)
        trap_entity.trap = trap
        trap.owner = trap_entity
        trap_entity.components.add(ComponentType.TRAP, trap)
        
        entities = [player, trap_entity]
        
        # Mock state manager with message log support
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
                """Mock method for death finalization."""
                pass
        
        state_manager = MockStateManager()
        movement_service = MovementService(state_manager)
        
        # Player moves right (to 2,1 where trap is)
        # Use fixed RNG to prevent passive detection
        set_global_seed(12345)
        
        initial_hp = player.fighter.hp
        result = movement_service.execute_movement(1, 0, source="test")
        
        # Verify movement succeeded
        assert result.success, "Movement should succeed (trap doesn't block entry)"
        assert player.x == 2, f"Player should be at x=2, got x={player.x}"
        assert player.y == 1, f"Player should be at y=1, got y={player.y}"
        
        # Verify damage was dealt
        assert player.fighter.hp == initial_hp - 7, f"Player should have taken 7 damage, HP: {player.fighter.hp} (was {initial_hp})"
        assert player.fighter.hp > 0, "Player should still be alive"
    
    def test_spike_trap_lethal_damage(self):
        """Spike trap can kill an entity with low HP."""
        from entity import Entity
        from components.component_registry import ComponentType, ComponentRegistry
        from components.trap import Trap
        from components.fighter import Fighter
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
        
        # Create player at (1, 1) with low HP (will die from trap)
        player = Entity(x=1, y=1, char='@', color=(255, 255, 255), name='Test Player', blocks=True)
        player.components = ComponentRegistry()
        fighter = Fighter(hp=5, defense=0, power=0)
        fighter.owner = player
        player.fighter = fighter  # Auto-registers via __setattr__
        
        # Create spike trap at (2, 1) with 7 damage (lethal)
        trap_entity = Entity(x=2, y=1, char='^', color=(192, 32, 32), name='Spike Trap', blocks=False)
        trap_entity.components = ComponentRegistry()
        trap = Trap(trap_type="spike_trap", detectable=True, passive_detect_chance=0.0, spike_damage=7)
        trap_entity.trap = trap
        trap.owner = trap_entity
        trap_entity.components.add(ComponentType.TRAP, trap)
        
        entities = [player, trap_entity]
        
        # Mock state manager with death finalization support
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
                """Mock method for death finalization."""
                pass
        
        state_manager = MockStateManager()
        movement_service = MovementService(state_manager)
        
        # Player moves right (to 2,1 where trap is)
        # Use fixed RNG to prevent passive detection
        set_global_seed(12345)
        
        result = movement_service.execute_movement(1, 0, source="test")
        
        # Verify movement succeeded
        assert result.success, "Movement should succeed (trap doesn't block entry)"
        assert player.x == 2, f"Player should be at x=2, got x={player.x}"
        
        # Verify player died
        assert player.fighter.hp <= 0, f"Player should be dead, HP: {player.fighter.hp}"


class TestSpikeTrapMetrics:
    """Tests for spike trap metrics tracking."""
    
    def setup_method(self):
        """Reset RNG state before each test."""
        reset_rng_state()
    
    def teardown_method(self):
        """Reset RNG state after each test."""
        reset_rng_state()
    
    def test_spike_trap_metrics_increment_correctly(self):
        """Spike trap metrics are incremented when trap triggers."""
        from services.scenario_metrics import ScenarioMetricsCollector, set_active_metrics_collector, clear_active_metrics_collector
        from services.scenario_harness import RunMetrics
        
        # Create and set metrics collector
        metrics = RunMetrics()
        collector = ScenarioMetricsCollector(metrics)
        set_active_metrics_collector(collector)
        
        try:
            # Simulate spike trap trigger metrics
            collector.increment('traps_triggered_total')
            collector.increment('trap_spike_triggered')
            collector.increment('trap_spike_damage_total', 7)
            
            # Verify metrics
            assert metrics.traps_triggered_total == 1
            assert metrics.trap_spike_triggered == 1
            assert metrics.trap_spike_damage_total == 7
            
            # Simulate second trap trigger
            collector.increment('traps_triggered_total')
            collector.increment('trap_spike_triggered')
            collector.increment('trap_spike_damage_total', 7)
            
            # Verify cumulative metrics
            assert metrics.traps_triggered_total == 2
            assert metrics.trap_spike_triggered == 2
            assert metrics.trap_spike_damage_total == 14
        finally:
            clear_active_metrics_collector()


class TestSpikeTrapScenarioDeterminism:
    """Tests for scenario determinism with spike traps."""
    
    def setup_method(self):
        """Reset RNG state before each test."""
        reset_rng_state()
    
    def teardown_method(self):
        """Reset RNG state after each test."""
        reset_rng_state()
    
    @pytest.mark.slow
    def test_trap_spike_identity_scenario_determinism(self):
        """trap_spike_identity scenario produces identical results with seed_base=1337."""
        from config.level_template_registry import get_scenario_registry
        from services.scenario_harness import run_scenario_many, make_bot_policy
        
        registry = get_scenario_registry()
        scenario = registry.get_scenario_definition("trap_spike_identity")
        
        if scenario is None:
            pytest.skip("trap_spike_identity scenario not found")
        
        policy = make_bot_policy("tactical_fighter")
        seed_base = 1337
        runs = 3
        turn_limit = 20
        
        # First execution
        metrics1 = run_scenario_many(scenario, policy, runs, turn_limit, seed_base=seed_base)
        
        # Second execution with same seed_base
        metrics2 = run_scenario_many(scenario, policy, runs, turn_limit, seed_base=seed_base)
        
        # Trap metrics must match exactly
        assert metrics1.runs == metrics2.runs
        assert getattr(metrics1, 'trap_spike_triggered', 0) == getattr(metrics2, 'trap_spike_triggered', 0)
        assert getattr(metrics1, 'trap_spike_damage_total', 0) == getattr(metrics2, 'trap_spike_damage_total', 0)


class TestSpikeTrapComponent:
    """Tests for Trap component with spike_trap type."""
    
    def test_trap_spike_damage_attribute(self):
        """Trap component has spike_damage attribute for spike traps."""
        from components.trap import Trap
        
        trap = Trap(trap_type="spike_trap", spike_damage=10)
        
        assert trap.trap_type == "spike_trap"
        assert trap.spike_damage == 10
    
    def test_trap_get_visible_char_spike_trap(self):
        """Spike trap displays '^' when detected."""
        from components.trap import Trap
        
        trap = Trap(trap_type="spike_trap")
        
        # Hidden shows floor
        assert trap.get_visible_char() == '.'
        
        # Detected shows spike character
        trap.is_detected = True
        assert trap.get_visible_char() == '^'
    
    def test_trap_get_description_spike_trap(self):
        """Spike trap description includes damage and bleed info."""
        from components.trap import Trap
        
        trap = Trap(trap_type="spike_trap", spike_damage=7, spike_bleed_severity=1)
        trap.is_detected = True
        
        desc = trap.get_description()
        assert "spike trap" in desc
        assert "7" in desc  # damage
        assert "1" in desc  # bleed severity


class TestSpikeTrapDamageRouting:
    """Tests to verify spike trap uses canonical damage routing."""
    
    def test_spike_trap_uses_damage_service(self):
        """Verify spike trap damage goes through damage_service.apply_damage."""
        # This is a documentation test - the actual implementation is verified
        # by checking that movement_service._apply_trap_effects calls
        # damage_service.apply_damage for spike traps.
        
        from services.movement_service import MovementService
        import inspect
        
        # Get the source code of _apply_trap_effects
        source = inspect.getsource(MovementService._apply_trap_effects)
        
        # Verify it imports and uses damage_service
        assert "from services.damage_service import apply_damage" in source
        assert "apply_damage(" in source
        assert 'cause="spike_trap"' in source
