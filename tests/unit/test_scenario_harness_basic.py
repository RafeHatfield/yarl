import pytest

from config.level_template_registry import ScenarioDefinition
from services.scenario_harness import make_bot_policy, run_scenario_once
from services.scenario_invariants import ScenarioInvariantError


def _scenario_base(**kwargs):
    defaults = dict(
        scenario_id="scenario_harness_test",
        name="Harness Test",
        description=None,
        depth=None,
        defaults={},
        expected={},
        rooms=[],
        monsters=[],
        items=[],
        player=None,
        hazards=[],
        victory_conditions=[],
        defeat_conditions=[],
        source_file="",
    )
    defaults.update(kwargs)
    return ScenarioDefinition(**defaults)


def test_run_scenario_once_success():
    scenario = _scenario_base(
        monsters=[{"type": "orc", "count": 1, "position": [5, 5]}],
        items=[{"type": "healing_potion", "count": 1, "position": [3, 3]}],
        player={"position": [1, 1]},
    )
    policy = make_bot_policy("observe_only")
    metrics = run_scenario_once(scenario, policy, turn_limit=5)

    assert metrics.turns_taken >= 1
    assert metrics.player_died in (True, False)


def test_run_scenario_once_invariant_failure():
    scenario = _scenario_base(
        player={"position": [99, 99]},
    )
    policy = make_bot_policy("observe_only")

    with pytest.raises(ScenarioInvariantError):
        run_scenario_once(scenario, policy, turn_limit=3)
"""
Unit tests for Phase 12B: Scenario Harness & Basic Metrics

Tests the scenario harness infrastructure including:
- RunMetrics and AggregatedMetrics dataclasses
- BotPolicy implementations
- run_scenario_once and run_scenario_many functions
"""

import os
import pytest

# Force headless mode before any tcod imports
os.environ['SDL_VIDEODRIVER'] = 'dummy'

from services.scenario_harness import (
    RunMetrics,
    AggregatedMetrics,
    BotPolicy,
    ObserveOnlyPolicy,
    TacticalFighterPolicy,
    make_bot_policy,
    run_scenario_once,
    run_scenario_many,
    evaluate_expected_invariants,
    ExpectedCheckResult,
)
from config.level_template_registry import (
    ScenarioDefinition,
    get_scenario_registry,
)


class TestRunMetrics:
    """Tests for RunMetrics dataclass."""
    
    def test_default_values(self):
        """Test RunMetrics has correct default values."""
        metrics = RunMetrics()
        
        assert metrics.turns_taken == 0
        assert metrics.player_died is False
        assert metrics.kills_by_faction == {}
        assert metrics.kills_by_source == {}
        assert metrics.plague_infections == 0
        assert metrics.reanimations == 0
        assert metrics.surprise_attacks == 0
        assert metrics.bonus_attacks_triggered == 0
        assert metrics.player_attacks == 0
        assert metrics.player_hits == 0
        assert metrics.monster_attacks == 0
        assert metrics.monster_hits == 0
    
    def test_custom_values(self):
        """Test RunMetrics with custom values."""
        metrics = RunMetrics(
            turns_taken=150,
            player_died=True,
            kills_by_faction={'PLAYER': 5, 'ORC': 3}
        )
        
        assert metrics.turns_taken == 150
        assert metrics.player_died is True
        assert metrics.kills_by_faction == {'PLAYER': 5, 'ORC': 3}
    
    def test_to_dict(self):
        """Test RunMetrics.to_dict() serialization."""
        metrics = RunMetrics(
            turns_taken=100,
            player_died=False,
            kills_by_faction={'UNDEAD': 10}
        )
        
        result = metrics.to_dict()
        
        assert isinstance(result, dict)
        assert result['turns_taken'] == 100
        assert result['player_died'] is False
        assert result['kills_by_faction'] == {'UNDEAD': 10}


class TestAggregatedMetrics:
    """Tests for AggregatedMetrics dataclass."""
    
    def test_default_values(self):
        """Test AggregatedMetrics has correct default values."""
        metrics = AggregatedMetrics()
        
        assert metrics.runs == 0
        assert metrics.average_turns == 0.0
        assert metrics.player_deaths == 0
        assert metrics.depth is None
        assert metrics.total_kills_by_faction == {}
        assert metrics.total_kills_by_source == {}
        assert metrics.total_plague_infections == 0
        assert metrics.total_reanimations == 0
        assert metrics.total_surprise_attacks == 0
        assert metrics.total_bonus_attacks_triggered == 0
        assert metrics.total_player_attacks == 0
        assert metrics.total_player_hits == 0
        assert metrics.total_monster_attacks == 0
        assert metrics.total_monster_hits == 0
    
    def test_custom_values(self):
        """Test AggregatedMetrics with custom values."""
        metrics = AggregatedMetrics(
            runs=10,
            average_turns=145.5,
            player_deaths=3,
            total_kills_by_faction={'PLAYER': 50, 'ENEMY': 20},
            total_kills_by_source={'PLAYER': 30},
            total_plague_infections=4,
            total_reanimations=2,
            total_surprise_attacks=5,
            total_bonus_attacks_triggered=3,
            total_player_attacks=100,
            total_player_hits=60,
            total_monster_attacks=80,
            total_monster_hits=40,
            depth=5,
        )
        
        assert metrics.runs == 10
        assert metrics.average_turns == 145.5
        assert metrics.player_deaths == 3
        assert metrics.depth == 5
        assert metrics.total_kills_by_faction == {'PLAYER': 50, 'ENEMY': 20}
        assert metrics.total_kills_by_source == {'PLAYER': 30}
        assert metrics.total_plague_infections == 4
        assert metrics.total_reanimations == 2
        assert metrics.total_surprise_attacks == 5
        assert metrics.total_bonus_attacks_triggered == 3
        assert metrics.total_player_attacks == 100
        assert metrics.total_player_hits == 60
        assert metrics.total_monster_attacks == 80
        assert metrics.total_monster_hits == 40
    
    def test_to_dict(self):
        """Test AggregatedMetrics.to_dict() serialization."""
        metrics = AggregatedMetrics(
            runs=5,
            average_turns=100.333,
            player_deaths=1,
            total_kills_by_faction={'ZOMBIE': 15},
            total_kills_by_source={'PLAYER': 5},
            total_plague_infections=2,
            total_reanimations=1,
            total_surprise_attacks=3,
            total_bonus_attacks_triggered=2,
            total_player_attacks=50,
            total_player_hits=30,
            total_monster_attacks=40,
            total_monster_hits=20,
            depth=7,
        )
        
        result = metrics.to_dict()
        
        assert isinstance(result, dict)
        assert result['runs'] == 5
        assert result['average_turns'] == 100.33  # Rounded to 2 decimal places
        assert result['player_deaths'] == 1
        assert result['depth'] == 7
        assert result['total_kills_by_faction'] == {'ZOMBIE': 15}
        assert result['total_kills_by_source'] == {'PLAYER': 5}
        assert result['total_plague_infections'] == 2
        assert result['total_reanimations'] == 1
        assert result['total_surprise_attacks'] == 3
        assert result['total_bonus_attacks_triggered'] == 2
        assert result['total_player_attacks'] == 50
        assert result['total_player_hits'] == 30
        assert result['total_monster_attacks'] == 40
        assert result['total_monster_hits'] == 20


class TestBotPolicy:
    """Tests for BotPolicy implementations."""
    
    def test_observe_only_policy_returns_wait(self):
        """Test ObserveOnlyPolicy always returns wait action."""
        policy = ObserveOnlyPolicy()
        
        # Test with None game_state
        action = policy.choose_action(None)
        assert action == {'wait': True}
        
        # Test with mock game_state
        class MockGameState:
            pass
        
        action = policy.choose_action(MockGameState())
        assert action == {'wait': True}
    
    def test_make_bot_policy_observe_only(self):
        """Test make_bot_policy creates ObserveOnlyPolicy."""
        policy = make_bot_policy("observe_only")
        
        assert isinstance(policy, ObserveOnlyPolicy)
        assert hasattr(policy, 'choose_action')
    
    def test_make_bot_policy_case_insensitive(self):
        """Test make_bot_policy is case-insensitive."""
        policy1 = make_bot_policy("observe_only")
        policy2 = make_bot_policy("OBSERVE_ONLY")
        policy3 = make_bot_policy("Observe_Only")
        
        assert all(isinstance(p, ObserveOnlyPolicy) for p in [policy1, policy2, policy3])
    
    def test_make_bot_policy_allows_dashes(self):
        """Test make_bot_policy accepts dashes as separators."""
        policy = make_bot_policy("observe-only")
        
        assert isinstance(policy, ObserveOnlyPolicy)
    
    def test_make_bot_policy_tactical(self):
        """Test make_bot_policy creates TacticalFighterPolicy."""
        policy = make_bot_policy("tactical_fighter")
        assert isinstance(policy, TacticalFighterPolicy)
    
    def test_make_bot_policy_unknown_raises_error(self):
        """Test make_bot_policy raises ValueError for unknown policy."""
        with pytest.raises(ValueError) as exc_info:
            make_bot_policy("nonexistent_policy")
        
        assert "Unknown bot policy" in str(exc_info.value)


class TestScenarioDefinitionForHarness:
    """Tests for ScenarioDefinition usage in harness context."""
    
    def test_create_test_scenario(self):
        """Test creating a minimal test scenario."""
        scenario = ScenarioDefinition(
            scenario_id="test_harness",
            name="Harness Test Scenario",
            description="For testing the harness",
            depth=1,
            defaults={
                'turn_limit': 50,
                'player_bot': 'observe_only',
                'runs': 3,
            }
        )
        
        assert scenario.scenario_id == "test_harness"
        assert scenario.get_default('turn_limit') == 50
        assert scenario.get_default('player_bot') == 'observe_only'
        assert scenario.get_default('runs') == 3


class TestRunScenarioOnce:
    """Tests for run_scenario_once function."""
    
    @pytest.fixture
    def simple_scenario(self):
        """Create a simple test scenario."""
        return ScenarioDefinition(
            scenario_id="test_simple",
            name="Simple Test",
            description="Minimal scenario for testing",
            depth=1,
        )
    
    def test_run_scenario_once_smoke(self, simple_scenario):
        """Smoke test: run_scenario_once completes without error."""
        policy = ObserveOnlyPolicy()
        
        # Run with very small turn limit
        metrics = run_scenario_once(simple_scenario, policy, turn_limit=5)
        
        # Basic assertions
        assert isinstance(metrics, RunMetrics)
        assert metrics.turns_taken <= 5
        assert isinstance(metrics.player_died, bool)
        assert isinstance(metrics.kills_by_faction, dict)
    
    def test_run_scenario_once_respects_turn_limit(self, simple_scenario):
        """Test that turn limit is respected."""
        policy = ObserveOnlyPolicy()
        
        metrics = run_scenario_once(simple_scenario, policy, turn_limit=3)
        
        assert metrics.turns_taken <= 3
    
    def test_run_scenario_once_with_larger_turn_limit(self, simple_scenario):
        """Test with a larger turn limit."""
        policy = ObserveOnlyPolicy()
        
        metrics = run_scenario_once(simple_scenario, policy, turn_limit=10)
        
        assert metrics.turns_taken <= 10
        assert isinstance(metrics.player_died, bool)


class TestRunScenarioMany:
    """Tests for run_scenario_many function."""
    
    @pytest.fixture
    def simple_scenario(self):
        """Create a simple test scenario."""
        return ScenarioDefinition(
            scenario_id="test_multi",
            name="Multi-Run Test",
            description="Scenario for testing multiple runs",
            depth=1,
        )
    
    def test_run_scenario_many_aggregates(self, simple_scenario):
        """Test run_scenario_many aggregates correctly."""
        policy = ObserveOnlyPolicy()
        
        # Run 3 times with small turn limit
        metrics = run_scenario_many(simple_scenario, policy, runs=3, turn_limit=3)
        
        # Check aggregation
        assert isinstance(metrics, AggregatedMetrics)
        assert metrics.runs == 3
        assert metrics.average_turns > 0
        assert isinstance(metrics.player_deaths, int)
        assert isinstance(metrics.total_kills_by_faction, dict)
    
    def test_run_scenario_many_run_count(self, simple_scenario):
        """Test that run count is correct."""
        policy = ObserveOnlyPolicy()
        
        for expected_runs in [1, 2, 5]:
            metrics = run_scenario_many(simple_scenario, policy, runs=expected_runs, turn_limit=2)
            assert metrics.runs == expected_runs
    
    def test_run_scenario_many_average_calculation(self, simple_scenario):
        """Test that average turns is calculated correctly."""
        policy = ObserveOnlyPolicy()
        
        metrics = run_scenario_many(simple_scenario, policy, runs=3, turn_limit=5)
        
        # Average should be <= turn_limit
        assert metrics.average_turns <= 5
        assert metrics.average_turns > 0


class TestInstalledScenarios:
    """Tests using actual installed scenarios from Phase 12A."""
    
    def test_run_backstab_scenario_if_available(self):
        """Test running backstab scenario if installed."""
        registry = get_scenario_registry()
        scenario = registry.get_scenario_definition("backstab_training")
        
        if scenario is None:
            pytest.skip("backstab_training scenario not installed")
        
        policy = make_bot_policy("observe_only")
        metrics = run_scenario_once(scenario, policy, turn_limit=5)
        
        assert isinstance(metrics, RunMetrics)
        assert metrics.turns_taken <= 5
    
    def test_run_plague_arena_scenario_if_available(self):
        """Test running plague arena scenario if installed."""
        registry = get_scenario_registry()
        scenario = registry.get_scenario_definition("plague_arena")
        
        if scenario is None:
            pytest.skip("plague_arena scenario not installed")
        
        policy = make_bot_policy("observe_only")
        metrics = run_scenario_once(scenario, policy, turn_limit=5)
        
        assert isinstance(metrics, RunMetrics)
        assert metrics.turns_taken <= 5


class TestMakeBotPolicyInterface:
    """Tests for the bot policy factory interface."""
    
    def test_observe_only_implements_protocol(self):
        """Verify ObserveOnlyPolicy implements BotPolicy protocol."""
        policy = make_bot_policy("observe_only")
        
        # Check that choose_action is callable
        assert callable(getattr(policy, 'choose_action', None))
        
        # Check that it returns expected type
        result = policy.choose_action(None)
        assert result is None or isinstance(result, dict)
    
    def test_policy_returns_action_dict(self):
        """Verify policies return valid action dicts."""
        policy = make_bot_policy("observe_only")
        action = policy.choose_action(None)
        
        # Should be dict with recognized action keys
        assert isinstance(action, dict)
        # ObserveOnly should return wait
        assert 'wait' in action


class TestTacticalFighterPolicy:
    """Tests for TacticalFighterPolicy behavior."""
    
    def test_adjacent_enemy_attack(self):
        class Dummy:
            def __init__(self, x, y, fighter=True, ai=True):
                self.x = x
                self.y = y
                self.fighter = type("F", (), {"hp": 10})() if fighter else None
                self.ai = object() if ai else None
                self.blocks = True
        player = Dummy(0, 0)
        enemy = Dummy(1, 0)
        game_state = type("GS", (), {
            "player": player,
            "entities": [player, enemy],
            "game_map": type("GM", (), {"width": 10, "height": 10, "is_blocked": lambda self,x,y: False})()
        })()
        
        policy = TacticalFighterPolicy()
        action = policy.choose_action(game_state)
        
        assert action.get('attack') is enemy


class TestExpectedEvaluation:
    """Tests for evaluate_expected_invariants."""
    
    def test_expected_passes(self):
        scenario = _scenario_base(expected={"min_player_kills": 2, "max_player_deaths": 0})
        metrics = AggregatedMetrics(
            runs=3,
            average_turns=5,
            player_deaths=0,
            total_kills_by_faction={},
            total_kills_by_source={"PLAYER": 3},
        )
        result = evaluate_expected_invariants(scenario, metrics)
        assert result.passed is True
        assert result.failures == []
    
    def test_expected_failures(self):
        scenario = _scenario_base(expected={
            "min_player_kills": 2,
            "max_player_deaths": 0,
            "bonus_attacks_min": 1,
        })
        metrics = AggregatedMetrics(
            runs=2,
            average_turns=4,
            player_deaths=1,
            total_kills_by_source={"PLAYER": 1},
            total_bonus_attacks_triggered=0,
        )
        result = evaluate_expected_invariants(scenario, metrics)
        assert result.passed is False
        assert len(result.failures) == 3
