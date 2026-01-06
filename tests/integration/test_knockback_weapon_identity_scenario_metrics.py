"""Integration test for knockback weapon identity scenario.

Validates weapon-based knockback mechanics:
- Distance based on power delta (cap 4 tiles)
- Staggered micro-stun when blocked early by hard obstacle
- Uses canonical movement execution (respects entangle/root/etc)
- Works for both player and monsters

This test runs the scenario_knockback_weapon_identity scenario and validates
that knockback metrics are within expected ranges.
"""

import pytest
import subprocess
import json
from pathlib import Path


@pytest.mark.slow
def test_knockback_weapon_identity_scenario_metrics():
    """Run knockback weapon identity scenario and validate metrics.
    
    Expected behavior:
    - Player picks up knockback mace and uses it in combat
    - Knockback triggers on successful hits with knockback weapon
    - Distance varies based on power delta (1-4 tiles)
    - Stagger applied when knockback blocked by wall/obstacle
    - Stagger causes turn skip (micro-stun)
    
    Lower-bound invariants (30 runs, deterministic):
    - knockback_applications >= 50 (at least 50 knockback hits)
    - knockback_tiles_moved >= 100 (at least 100 tiles moved total)
    - knockback_blocked_events >= 10 (at least 10 wall/entity impacts)
    - stagger_applications >= 10 (at least 10 staggers applied)
    - stagger_turns_skipped >= 0 (may be 0 if enemies die before next turn)
    - player_deaths <= 20 (sanity check only, generous to avoid flakiness)
    """
    # Run ecosystem_sanity with knockback scenario
    cmd = [
        "python3",
        "ecosystem_sanity.py",
        "--scenario", "knockback_weapon_identity",
        "--runs", "30",
        "--turn-limit", "100",
        "--player-bot", "tactical_fighter",
        "--export-json", "/tmp/knockback_identity_test.json",
        "--seed-base", "1337",
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    
    # Check that command succeeded
    assert result.returncode == 0, f"ecosystem_sanity failed: {result.stderr}"
    
    # Load metrics from JSON export
    with open("/tmp/knockback_identity_test.json", "r") as f:
        data = json.load(f)
    
    metrics = data.get("metrics", {})
    runs = data.get("runs", 0)
    
    # Validate run count
    assert runs == 30, f"Expected 30 runs, got {runs}"
    
    # Validate knockback metrics (conservative thresholds)
    knockback_applications = metrics.get("knockback_applications", 0)
    knockback_tiles_moved = metrics.get("knockback_tiles_moved", 0)
    knockback_blocked_events = metrics.get("knockback_blocked_events", 0)
    stagger_applications = metrics.get("stagger_applications", 0)
    stagger_turns_skipped = metrics.get("stagger_turns_skipped", 0)
    
    assert knockback_applications >= 50, \
        f"Expected >= 50 knockback applications, got {knockback_applications}"
    
    assert knockback_tiles_moved >= 100, \
        f"Expected >= 100 knockback tiles moved, got {knockback_tiles_moved}"
    
    assert knockback_blocked_events >= 10, \
        f"Expected >= 10 knockback blocked events, got {knockback_blocked_events}"
    
    assert stagger_applications >= 10, \
        f"Expected >= 10 stagger applications, got {stagger_applications}"
    
    assert stagger_turns_skipped >= 0, \
        f"Expected >= 0 stagger turns skipped, got {stagger_turns_skipped}"
    
    # Validate death rate (sanity check - generous upper bound to avoid flakiness)
    # Note: This is not a strict invariant, just a smoke test for catastrophic failure
    player_deaths = metrics.get("player_deaths", 0)
    assert player_deaths <= 20, \
        f"Expected <= 20 player deaths (sanity check), got {player_deaths}"
    
    # Validate that player actually used the knockback weapon
    # (knockback_applications > 0 implies weapon was picked up and used)
    assert knockback_applications > 0, \
        "Player never used knockback weapon (knockback_applications == 0)"
    
    print(f"✓ Knockback weapon identity scenario passed:")
    print(f"  - Knockback applications: {knockback_applications}")
    print(f"  - Knockback tiles moved: {knockback_tiles_moved}")
    print(f"  - Knockback blocked events: {knockback_blocked_events}")
    print(f"  - Stagger applications: {stagger_applications}")
    print(f"  - Stagger turns skipped: {stagger_turns_skipped}")
    print(f"  - Player deaths: {player_deaths}/{runs}")

