# Balance Acceptance Contract

**Effective:** 2024-12-14 (Phase 18 QOL)  
**Authority:** This document governs all balance-related merge decisions.

---

## Purpose

The Balance Suite is the **authoritative balance gate** for Catacombs of YARL.

This contract defines what constitutes acceptable balance drift and when contributions may merge.

---

## Definitions

### PASS

All metrics are within acceptable drift from baseline.

- **Death rate:** < ±10%
- **Hit rates (player/monster):** < ±5%
- **Pressure index:** < ±5.0
- **Bonus attacks/run:** < ±2.0

**Merge status:** ✅ May merge immediately.

---

### WARN

One or more metrics show notable drift, but below failure threshold.

- **Death rate:** ±10% to ±20%
- **Hit rates:** ±5% to ±10%
- **Pressure index:** ±5.0 to ±10.0
- **Bonus attacks/run:** ±2.0 to ±4.0

**Merge status:** ✅ May merge after review.

**Requirements:**
- Contributor must acknowledge the drift
- Drift must be explainable (e.g., "tuned orc HP +10")
- No silent merges; reviewer must approve

**Action:**
- If drift is intentional: merge and optionally update baseline
- If drift is surprising: investigate before merge

---

### FAIL

One or more metrics exceed acceptable drift thresholds.

- **Death rate:** ≥ ±20%
- **Hit rates:** ≥ ±10%
- **Pressure index:** ≥ ±10.0
- **Bonus attacks/run:** ≥ ±4.0

**Merge status:** ❌ Blocked until resolved.

**Resolution paths:**
1. **Bug fix:** Change broke balance unintentionally → fix the bug
2. **Intentional rebalance:** Large deliberate changes → update baseline + justify in PR
3. **Threshold miscalibration:** Thresholds too strict → update contract (rare)

---

## Responsibilities

### Contributors

When submitting a PR:

1. Run `make balance-suite-fast` locally
2. If WARN or FAIL:
   - Note the verdict in PR description
   - Explain why drift occurred
   - Justify if baseline update is needed
3. Do NOT update baseline without approval

---

### Reviewers

Before approving a PR:

1. Check CI balance suite results
2. If WARN:
   - Verify contributor acknowledged drift
   - Confirm explanation is reasonable
   - Approve or request baseline update
3. If FAIL:
   - Block merge until resolved
   - Work with contributor to fix or justify

---

### Future Agents / Maintainers

When working on balance changes:

- **Never bypass this contract**
- **Never auto-update baselines**
- Treat WARN as "proceed with awareness"
- Treat FAIL as "stop and investigate"

If thresholds feel wrong, update this contract explicitly and justify the change.

---

## Baseline Updates

### When to Update

Baselines represent "this felt good" and should be updated when:

1. **Intentional rebalance:** You changed combat deliberately and results are desired
2. **New scenarios added:** Expanding the suite requires new baseline data
3. **Bug fixes validated:** Fixed a bug, new behavior is correct

### When NOT to Update

- To make CI pass
- Because drift is inconvenient
- Without review and justification

### Process

```bash
# Local validation
make balance-suite-fast

# Review results
cat reports/balance_suite/latest.txt
cat $(cat reports/balance_suite/latest.txt)/balance_report.md

# If results are desired, update the baseline
make balance-suite-update-baseline

# Commit the updated baseline
git add reports/baselines/balance_suite_baseline.json
git commit -m "Update balance baseline: <reason>"
```

**Baseline updates require explicit justification in commit message.**

---

## CI Enforcement

### GitHub Actions Behavior

On all PRs, the balance suite runs automatically:

- **PASS:** ✅ CI passes
- **WARN:** ⚠️ CI passes with warning (logged, not blocking)
- **FAIL:** ❌ CI fails

### Overriding CI Failures

FAIL states should not be overridden. If you believe a FAIL is incorrect:

1. Open an issue explaining why thresholds are wrong
2. Submit a separate PR updating this contract
3. Do not merge the balance-failing PR until contract is updated

---

## Contract Modifications

This contract may be modified when:

- Thresholds prove too strict or too loose
- New metrics are added to the suite
- Workflow changes require policy updates

**All modifications require:**
- Explicit PR updating this file
- Justification in PR description
- Review by maintainer

---

## Exit Codes

For automation and scripting:

```bash
make balance-suite-fast
echo $?
```

- **Exit 0:** PASS or WARN (safe to merge after review)
- **Exit 1:** FAIL (blocked)

---

## Non-Goals

This contract does **NOT** govern:

- Unit test failures (covered by separate CI)
- Linting or formatting (covered by separate CI)
- Worldgen or non-combat systems
- Subjective "feel" (this is objective metrics only)

---

## Summary

| Verdict | Exit Code | CI Status | Merge? | Action |
|---------|-----------|-----------|--------|--------|
| PASS    | 0         | ✅ Pass   | Yes    | Merge freely |
| WARN    | 0         | ⚠️ Pass   | Yes    | Review + acknowledge |
| FAIL    | 1         | ❌ Fail   | No     | Fix or justify |

---

## References

- Balance Suite: `docs/BALANCE_SUITE.md`
- Testing Harness: `docs/BALANCE_AND_TESTING_HARNESS.md`
- Thresholds: `tools/balance_suite.py` (THRESHOLDS dict)

