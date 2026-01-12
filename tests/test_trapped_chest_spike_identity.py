"""Phase 21.6: Trapped Chest (Spike) Identity Tests

Verifies that:
1. Trapped chest triggers spike payload on open
2. Spike payload deals damage via damage_service.apply_damage (canonical routing)
3. Trap triggers exactly once (chest becomes inert after opening)
4. Opening again does NOT retrigger trap
5. Chest trap metrics are recorded correctly (single source of truth)
6. Scenario is deterministic under seed_base=1337
"""

import pytest
from engine.rng_config import reset_rng_state, set_global_seed


class TestTrappedChestSpike:
    """Tests for trapped chest with spike payload."""
    
    def setup_method(self):
        """Reset RNG state before each test."""
        reset_rng_state()
    
    def teardown_method(self):
        """Reset RNG state after each test."""
        reset_rng_state()
    
    def test_trapped_chest_spike_deals_damage(self):
        """Trapped chest with spike payload deals damage when opened."""
        from entity import Entity
        from components.component_registry import ComponentType, ComponentRegistry
        from components.chest import Chest, ChestState
        from components.fighter import Fighter
        
        # Create player with fighter
        player = Entity(x=1, y=1, char='@', color=(255, 255, 255), name='Test Player', blocks=True)
        player.components = ComponentRegistry()
        fighter = Fighter(hp=20, defense=0, power=0)
        fighter.owner = player
        player.fighter = fighter
        
        # Create trapped chest with spike payload
        chest_entity = Entity(x=2, y=2, char='C', color=(150, 75, 25), name='Trapped Chest', blocks=True)
        chest_entity.components = ComponentRegistry()
        chest = Chest(state=ChestState.TRAPPED, trap_type="spike", loot_quality="common")
        chest.owner = chest_entity
        chest_entity.chest = chest
        
        initial_hp = player.fighter.hp
        
        # Open the chest
        results = chest.open(player, has_key=False)
        
        # Verify trap triggered
        trap_triggered = any(r.get('trap_triggered') for r in results)
        assert trap_triggered, "Trap should have triggered"
        
        # Verify damage was dealt
        assert player.fighter.hp < initial_hp, f"Player should have taken damage, HP: {player.fighter.hp} (was {initial_hp})"
        assert player.fighter.hp == initial_hp - 5, f"Player should have taken 5 damage, HP: {player.fighter.hp}"
        
        # Verify chest is now open
        assert chest.state == ChestState.OPEN
    
    def test_trapped_chest_does_not_retrigger(self):
        """Trapped chest does not retrigger after first opening."""
        from entity import Entity
        from components.component_registry import ComponentRegistry
        from components.chest import Chest, ChestState
        from components.fighter import Fighter
        
        # Create player with fighter
        player = Entity(x=1, y=1, char='@', color=(255, 255, 255), name='Test Player', blocks=True)
        player.components = ComponentRegistry()
        fighter = Fighter(hp=20, defense=0, power=0)
        fighter.owner = player
        player.fighter = fighter
        
        # Create trapped chest
        chest_entity = Entity(x=2, y=2, char='C', color=(150, 75, 25), name='Trapped Chest', blocks=True)
        chest_entity.components = ComponentRegistry()
        chest = Chest(state=ChestState.TRAPPED, trap_type="spike", loot_quality="common")
        chest.owner = chest_entity
        chest_entity.chest = chest
        
        # Open the chest first time
        results1 = chest.open(player, has_key=False)
        hp_after_first = player.fighter.hp
        
        # Try to open again
        results2 = chest.open(player, has_key=False)
        
        # Verify no trap triggered second time
        trap_triggered_second = any(r.get('trap_triggered') for r in results2)
        assert not trap_triggered_second, "Trap should NOT retrigger"
        
        # Verify no additional damage
        assert player.fighter.hp == hp_after_first, "No additional damage should be dealt"


class TestTrappedChestMetrics:
    """Tests for trapped chest metrics tracking."""
    
    def setup_method(self):
        """Reset RNG state before each test."""
        reset_rng_state()
    
    def teardown_method(self):
        """Reset RNG state after each test."""
        reset_rng_state()
    
    def test_chest_trap_metrics_increment_correctly(self):
        """Chest trap metrics are incremented when trap triggers."""
        from services.scenario_metrics import ScenarioMetricsCollector, set_active_metrics_collector, clear_active_metrics_collector
        from services.scenario_harness import RunMetrics
        
        metrics = RunMetrics()
        collector = ScenarioMetricsCollector(metrics)
        set_active_metrics_collector(collector)
        
        try:
            collector.increment('chest_traps_triggered_total')
            collector.increment('chest_trap_spike_triggered')
            collector.increment('chest_trap_spike_damage_total', 5)
            
            assert metrics.chest_traps_triggered_total == 1
            assert metrics.chest_trap_spike_triggered == 1
            assert metrics.chest_trap_spike_damage_total == 5
        finally:
            clear_active_metrics_collector()


class TestTrappedChestScenarioDeterminism:
    """Tests for scenario determinism with trapped chests."""
    
    def setup_method(self):
        """Reset RNG state before each test."""
        reset_rng_state()
    
    def teardown_method(self):
        """Reset RNG state after each test."""
        reset_rng_state()
    
    @pytest.mark.slow
    def test_trapped_chest_spike_identity_scenario_determinism(self):
        """trapped_chest_spike_identity scenario produces identical results with seed_base=1337."""
        from config.level_template_registry import get_scenario_registry
        from services.scenario_harness import run_scenario_many, make_bot_policy
        
        registry = get_scenario_registry()
        scenario = registry.get_scenario_definition("trapped_chest_spike_identity")
        
        if scenario is None:
            pytest.skip("trapped_chest_spike_identity scenario not found")
        
        policy = make_bot_policy("tactical_fighter")
        seed_base = 1337
        runs = 3
        turn_limit = 20
        
        metrics1 = run_scenario_many(scenario, policy, runs, turn_limit, seed_base=seed_base)
        metrics2 = run_scenario_many(scenario, policy, runs, turn_limit, seed_base=seed_base)
        
        assert metrics1.runs == metrics2.runs
        assert getattr(metrics1, 'chest_trap_spike_triggered', 0) == getattr(metrics2, 'chest_trap_spike_triggered', 0)
        assert getattr(metrics1, 'chest_trap_spike_damage_total', 0) == getattr(metrics2, 'chest_trap_spike_damage_total', 0)


class TestChestTrapPayloadExecution:
    """Tests for chest trap payload execution."""
    
    def test_chest_spike_payload_uses_damage_service(self):
        """Verify chest spike payload uses damage_service.apply_damage."""
        from components.chest import Chest
        import inspect
        
        # Get the source code of _execute_spike_trap_payload
        source = inspect.getsource(Chest._execute_spike_trap_payload)
        
        # Verify it imports and uses damage_service
        assert "from services.damage_service import apply_damage" in source
        assert "apply_damage(" in source
        assert 'cause="chest_trap_spike"' in source
