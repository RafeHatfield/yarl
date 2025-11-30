# YARL Balance Tuning Cheat Sheet

## A. Rooms feel too spiky in early game

1. Lower ETP for the main offenders in `balance/etp.py`.
2. Reduce their spawn chance or delay them to a later band in `map_objects/game_map.py`.
3. Optionally tighten B1/B2 budgets in `config/etp_config.yaml`.
4. Run:

       python3 etp_sanity.py --strict

Aim for:

- Normal rooms: mostly OK.
- Only a few UNDER per band.
- No OVER in normal rooms.

---

## B. Mid/late game feels too flat

1. Slightly increase ETP values for mid-tier monsters.
2. Widen upper budgets for B3–B5 in `config/etp_config.yaml`.
3. Consider increasing elite-spawn chance in appropriate bands.

Run:

       python3 etp_sanity.py --strict

---

## C. Loot feels too dense

Lower the per-band density multiplier in `balance/loot_tags.py`:

       BAND_ITEM_DENSITY_MULTIPLIER = {
           1: 0.35,
           2: 0.45,
           3: 1.0,
           4: 1.0,
           5: 1.0,
       }

Re-run:

       python3 loot_sanity.py --bands --runs 5 --normal

Look at:

- Items per room by band.
- Target range: ~0.5–1.5 items/room.

---

## D. Too many / too few healing items

Adjust the `HEALING_BAND_MULTIPLIER` in `balance/loot_tags.py`.

- Early bands: use low multipliers to prevent floods.  
- Late bands: increase slightly to avoid starvation.

---

## E. Rings appear too early

Shift ring `band_min` upward in `balance/loot_tags.py`.

Recommended:

- Common rings → B2–B3  
- Uncommon rings → B3  
- Exotic rings → B4–B5  

---

## F. Pity firing too often

1. Increase pity thresholds in `balance/pity.py`.
2. Or increase natural drop rates for categories that fire too often.

Use the pity summary in `loot_sanity.py` to verify.

Healthy target: **5–15%** pity triggers per category.

---

## G. Removing overpowered drops in early bands

1. Raise `band_min` for those items in `balance/loot_tags.py`.
2. Reduce their base weights.

---

## H. Adding more guaranteed spawns

Use templates in `config/level_templates.yaml`:

- Add carefully to avoid distorting early-game difficulty.
- Mark rooms as `allow_spike: true` or `role: treasure/miniboss/boss` when appropriate.
- Avoid guaranteed spawns in B1 unless intentional.

---

## I. CI Integration

Add a GitHub Actions workflow to run:

       python3 etp_sanity.py --strict
       python3 loot_sanity.py --bands --runs 5 --normal

Treat failures as:

- **Hard errors** for ETP OVER in normal rooms.
- **Warnings** for loot drift.

This prevents silent balance regression.

---

## J. When in doubt

Re-run both harnesses:

### ETP Sanity
- Verifies encounter difficulty curve.
- Flags spikes, invalid rooms, band errors.

### Loot Sanity
- Verifies item pacing.
- Checks pity frequency.
- Finds category droughts or floods.

Together, these harnesses catch 90% of issues before playtesting.
