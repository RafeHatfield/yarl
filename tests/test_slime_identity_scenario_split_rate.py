"""Phase 19: Test that slime identity scenario achieves target split rate.

This test validates that the slime identity scenario exercises the split mechanic
at a meaningful rate (>= 33% of eligible slimes should split).
"""

import pytest
import json
import subprocess
from pathlib import Path


class TestSlimeIdentityScenarioSplitRate:
    """Test that slime identity scenario achieves target split rate."""
    
    def test_split_rate_meets_minimum_threshold(self):
        """Test that at least 33% of eligible slimes split in scenario runs."""
        # Run the scenario
        result = subprocess.run(
            [
                "python3", "ecosystem_sanity.py",
                "--scenario", "monster_slime_identity",
                "--runs", "30",
                "--turn-limit", "200",
                "--player-bot", "tactical_fighter",
                "--export-json", "/tmp/slime_identity_split_test.json"
            ],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        assert result.returncode == 0, f"Scenario run failed: {result.stderr}"
        
        # Load the JSON output
        json_path = Path("/tmp/slime_identity_split_test.json")
        assert json_path.exists(), "JSON export not found"
        
        with open(json_path) as f:
            data = json.load(f)
        
        metrics = data['metrics']
        runs = data['runs']
        
        # Calculate eligible slimes per run
        # Scenario has: 1 minor (no split) + 2 large (can split) + 1 greater (can split) = 3 eligible per run
        eligible_per_run = 3
        total_eligible = eligible_per_run * runs
        
        # Get split events
        total_splits = metrics['total_split_events']
        
        # Calculate split rate
        split_rate = total_splits / total_eligible if total_eligible > 0 else 0
        
        # Assert minimum split rate of 33%
        min_split_rate = 0.33
        assert split_rate >= min_split_rate, \
            f"Split rate {split_rate:.1%} is below minimum {min_split_rate:.1%} " \
            f"(splits={total_splits}, eligible={total_eligible})"
        
        # Additional validation: ensure children were spawned
        children_spawned = metrics['total_split_children_spawned']
        assert children_spawned > 0, "No children spawned despite split events"
        
        # Verify splits by type
        splits_by_type = metrics['total_split_events_by_type']
        assert 'Large_Slime' in splits_by_type, "No large slime splits recorded"
        assert 'Greater_Slime' in splits_by_type, "No greater slime splits recorded"
        
        print(f"\n✅ Split rate validation passed:")
        print(f"   Split rate: {split_rate:.1%} (target: >= {min_split_rate:.1%})")
        print(f"   Total splits: {total_splits} / {total_eligible} eligible")
        print(f"   Children spawned: {children_spawned}")
        print(f"   Splits by type: {splits_by_type}")


if __name__ == '__main__':
    pytest.main([__file__, "-v", "-s"])


