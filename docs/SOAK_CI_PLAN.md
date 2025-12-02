# Soak CI Plan

> **STATUS**: TODO - Not yet implemented  
> **PRIORITY**: Medium  
> **ESTIMATED EFFORT**: 1-2 hours

## Overview

This document outlines the plan for adding a CI soak job to GitHub Actions that runs
automated bot games to detect regressions and stability issues.

## Proposed Implementation

### GitHub Actions Workflow

Create `.github/workflows/soak-ci.yml`:

```yaml
name: Bot Soak CI

on:
  # Run on merge to main
  push:
    branches: [main]
  # Run nightly
  schedule:
    - cron: "0 4 * * *"  # 04:00 UTC daily
  # Manual trigger
  workflow_dispatch:
    inputs:
      runs:
        description: "Number of bot runs"
        default: "30"
      seed:
        description: "Base RNG seed (optional)"
        required: false

jobs:
  soak-test:
    runs-on: ubuntu-latest
    
    env:
      SDL_VIDEODRIVER: dummy
      PYTHONUNBUFFERED: "1"
    
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt || true
      
      - name: Run bot soak
        run: |
          python engine.py --bot-soak --headless \
            --runs ${RUNS:-30} \
            --max-turns 5000 \
            --metrics-log logs/soak/ \
            ${SEED:+--seed $SEED}
        env:
          RUNS: ${{ github.event.inputs.runs || '30' }}
          SEED: ${{ github.event.inputs.seed }}
      
      - name: Upload soak results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: soak-results-${{ github.run_number }}
          path: |
            logs/soak_*/metrics.csv
            logs/replays/*.jsonl
          retention-days: 30
      
      - name: Check for failures
        run: |
          # Parse CSV and fail if crash rate > 10%
          python -c "
          import csv
          import sys
          from pathlib import Path
          
          csv_files = list(Path('logs').rglob('metrics.csv'))
          if not csv_files:
              print('No CSV found, skipping check')
              sys.exit(0)
          
          with open(csv_files[0]) as f:
              rows = list(csv.DictReader(f))
          
          total = len(rows)
          errors = sum(1 for r in rows if r['failure_type'] == 'error')
          crash_rate = errors / total if total > 0 else 0
          
          print(f'Crash rate: {errors}/{total} = {crash_rate:.1%}')
          if crash_rate > 0.1:
              print('FAIL: Crash rate exceeds 10%')
              sys.exit(1)
          "
```

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `--runs` | 30 | Number of bot runs per CI job |
| `--max-turns` | 5000 | Max turns before forced termination |
| `--seed` | (random) | Base seed for reproducibility |
| `--metrics-log` | logs/soak/ | Output directory for CSV |

### Artifacts

The workflow uploads:
- `metrics.csv` - Per-run metrics with failure classification
- `*.jsonl` - Replay files for failed runs (if `--replay-log` enabled)

### Success Criteria

The job passes if:
1. At least 90% of runs complete without crash (`failure_type != 'error'`)
2. No unhandled exceptions cause the harness itself to fail

### Integration with Existing CI

This can be integrated into the existing `ci.yml` workflow as a separate job,
or kept as a standalone `soak-ci.yml` for independent scheduling.

## Next Steps

1. [ ] Create `.github/workflows/soak-ci.yml`
2. [ ] Test locally with `act` or similar
3. [ ] Tune run count and turn limits based on CI time budget
4. [ ] Consider adding replay logging for failed runs
5. [ ] Add failure trend tracking over time

## Related Files

- `engine/soak_harness.py` - Soak harness implementation
- `engine/rng_config.py` - RNG seed configuration
- `engine/replay.py` - Action replay system
- `.github/workflows/ci.yml` - Main CI workflow

