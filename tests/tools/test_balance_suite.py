"""Unit tests for balance_suite.py comparison and verdict logic.

Phase 18 QOL: Tests drift computation, threshold classification, and verdict logic.
"""

import pytest
from tools.balance_suite import (
    normalize_metrics,
    compute_deltas,
    classify_verdict,
    THRESHOLDS,
)


class TestNormalizeMetrics:
    """Test metric normalization from raw ecosystem_sanity JSON."""
    
    def test_normalize_basic(self):
        """Test basic metric normalization."""
        raw = {
            "scenario_id": "test_scenario",
            "runs": 50,
            "metrics": {
                "total_player_attacks": 1000,
                "total_monster_attacks": 500,
                "total_player_hits": 700,
                "total_monster_hits": 200,
                "total_bonus_attacks_triggered": 150,
                "player_deaths": 10,
            }
        }
        
        result = normalize_metrics(raw)
        
        assert result["scenario_id"] == "test_scenario"
        assert result["runs"] == 50
        assert result["deaths"] == 10
        assert result["death_rate"] == 0.2  # 10/50
        assert result["player_hit_rate"] == 0.7  # 700/1000
        assert result["monster_hit_rate"] == 0.4  # 200/500
        assert result["pressure_index"] == -10.0  # (500/50) - (1000/50)
        assert result["bonus_attacks_per_run"] == 3.0  # 150/50
    
    def test_normalize_zero_division(self):
        """Test safe division when denominators are zero."""
        raw = {
            "scenario_id": "test_scenario",
            "runs": 50,
            "metrics": {
                "total_player_attacks": 0,
                "total_monster_attacks": 0,
                "total_player_hits": 0,
                "total_monster_hits": 0,
                "total_bonus_attacks_triggered": 0,
                "player_deaths": 0,
            }
        }
        
        result = normalize_metrics(raw)
        
        # All rates should be 0.0, not raise exceptions
        assert result["death_rate"] == 0.0
        assert result["player_hit_rate"] == 0.0
        assert result["monster_hit_rate"] == 0.0
        assert result["pressure_index"] == 0.0
        assert result["bonus_attacks_per_run"] == 0.0


class TestComputeDeltas:
    """Test delta computation between current and baseline."""
    
    def test_compute_deltas_basic(self):
        """Test basic delta computation."""
        current = {
            "death_rate": 0.25,
            "player_hit_rate": 0.70,
            "monster_hit_rate": 0.40,
            "pressure_index": -10.0,
            "bonus_attacks_per_run": 3.0,
        }
        baseline = {
            "death_rate": 0.20,
            "player_hit_rate": 0.68,
            "monster_hit_rate": 0.38,
            "pressure_index": -12.0,
            "bonus_attacks_per_run": 2.5,
        }
        
        deltas = compute_deltas(current, baseline)
        
        assert deltas["death_rate"] == pytest.approx(0.05)
        assert deltas["player_hit_rate"] == pytest.approx(0.02)
        assert deltas["monster_hit_rate"] == pytest.approx(0.02)
        assert deltas["pressure_index"] == pytest.approx(2.0)
        assert deltas["bonus_attacks_per_run"] == pytest.approx(0.5)
    
    def test_compute_deltas_negative(self):
        """Test delta computation with negative changes."""
        current = {
            "death_rate": 0.15,
            "player_hit_rate": 0.65,
            "monster_hit_rate": 0.35,
            "pressure_index": -15.0,
            "bonus_attacks_per_run": 2.0,
        }
        baseline = {
            "death_rate": 0.20,
            "player_hit_rate": 0.70,
            "monster_hit_rate": 0.40,
            "pressure_index": -10.0,
            "bonus_attacks_per_run": 3.0,
        }
        
        deltas = compute_deltas(current, baseline)
        
        assert deltas["death_rate"] == pytest.approx(-0.05)
        assert deltas["player_hit_rate"] == pytest.approx(-0.05)
        assert deltas["monster_hit_rate"] == pytest.approx(-0.05)
        assert deltas["pressure_index"] == pytest.approx(-5.0)
        assert deltas["bonus_attacks_per_run"] == pytest.approx(-1.0)


class TestClassifyVerdict:
    """Test verdict classification based on thresholds."""
    
    def test_classify_pass(self):
        """Test PASS verdict with small deltas."""
        deltas = {
            "death_rate": 0.05,  # Below warn threshold (0.10)
            "player_hit_rate": 0.02,  # Below warn threshold (0.05)
            "monster_hit_rate": 0.03,  # Below warn threshold (0.05)
            "pressure_index": 2.0,  # Below warn threshold (5.0)
            "bonus_attacks_per_run": 1.0,  # Below warn threshold (2.0)
        }
        
        assert classify_verdict(deltas) == "PASS"
    
    def test_classify_warn(self):
        """Test WARN verdict with moderate deltas."""
        deltas = {
            "death_rate": 0.12,  # Above warn (0.10), below fail (0.20)
            "player_hit_rate": 0.02,
            "monster_hit_rate": 0.03,
            "pressure_index": 2.0,
            "bonus_attacks_per_run": 1.0,
        }
        
        assert classify_verdict(deltas) == "WARN"
    
    def test_classify_fail(self):
        """Test FAIL verdict with large deltas."""
        deltas = {
            "death_rate": 0.25,  # Above fail threshold (0.20)
            "player_hit_rate": 0.02,
            "monster_hit_rate": 0.03,
            "pressure_index": 2.0,
            "bonus_attacks_per_run": 1.0,
        }
        
        assert classify_verdict(deltas) == "FAIL"
    
    def test_classify_multiple_warns(self):
        """Test WARN verdict with multiple metrics at warn level."""
        deltas = {
            "death_rate": 0.12,  # Above warn
            "player_hit_rate": 0.07,  # Above warn
            "monster_hit_rate": 0.06,  # Above warn
            "pressure_index": 6.0,  # Above warn
            "bonus_attacks_per_run": 1.0,
        }
        
        assert classify_verdict(deltas) == "WARN"
    
    def test_classify_fail_trumps_warn(self):
        """Test that FAIL takes precedence over WARN."""
        deltas = {
            "death_rate": 0.12,  # WARN level
            "player_hit_rate": 0.15,  # FAIL level (> 0.10)
            "monster_hit_rate": 0.03,
            "pressure_index": 2.0,
            "bonus_attacks_per_run": 1.0,
        }
        
        assert classify_verdict(deltas) == "FAIL"
    
    def test_classify_negative_deltas(self):
        """Test that negative deltas (improvements) are treated as abs values."""
        deltas = {
            "death_rate": -0.12,  # Improvement, but abs > warn threshold
            "player_hit_rate": 0.02,
            "monster_hit_rate": 0.03,
            "pressure_index": 2.0,
            "bonus_attacks_per_run": 1.0,
        }
        
        assert classify_verdict(deltas) == "WARN"
    
    def test_classify_at_warn_boundary(self):
        """Test behavior exactly at warn threshold."""
        deltas = {
            "death_rate": 0.10,  # Exactly at warn threshold
            "player_hit_rate": 0.02,
            "monster_hit_rate": 0.03,
            "pressure_index": 2.0,
            "bonus_attacks_per_run": 1.0,
        }
        
        # At threshold should trigger warn
        assert classify_verdict(deltas) == "WARN"
    
    def test_classify_at_fail_boundary(self):
        """Test behavior exactly at fail threshold."""
        deltas = {
            "death_rate": 0.20,  # Exactly at fail threshold
            "player_hit_rate": 0.02,
            "monster_hit_rate": 0.03,
            "pressure_index": 2.0,
            "bonus_attacks_per_run": 1.0,
        }
        
        # At threshold should trigger fail
        assert classify_verdict(deltas) == "FAIL"


class TestThresholds:
    """Test that threshold configuration is valid."""
    
    def test_thresholds_exist(self):
        """Test that all expected metrics have thresholds."""
        expected_keys = [
            "death_rate",
            "player_hit_rate",
            "monster_hit_rate",
            "pressure_index",
            "bonus_attacks_per_run",
        ]
        
        for key in expected_keys:
            assert key in THRESHOLDS, f"Missing threshold for {key}"
            assert "warn" in THRESHOLDS[key], f"Missing warn threshold for {key}"
            assert "fail" in THRESHOLDS[key], f"Missing fail threshold for {key}"
    
    def test_threshold_ordering(self):
        """Test that fail thresholds are >= warn thresholds."""
        for key, thresholds in THRESHOLDS.items():
            assert thresholds["fail"] >= thresholds["warn"], \
                f"Fail threshold must be >= warn threshold for {key}"
