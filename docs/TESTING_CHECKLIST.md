# Distribution Testing Checklist

Quick smoke-test for packaged builds. Run through this before sending to friends
or uploading a release. Takes ~5 minutes.

---

## ✅ Core Functionality

- [ ] **Launch game** — Main menu appears, no crash or error dialog
- [ ] **Font renders** — Text is readable, not garbled/missing
- [ ] **Menu background** — Image loads (not black/blank screen)
- [ ] **Start new game** — Level generates, player visible on map
- [ ] **Move around** — Arrow keys / numpad work
- [ ] **Pick up item** — Walk over item, press `g` or `,` — item appears in inventory
- [ ] **Open a chest** — Right-click or bump a chest, loot drops
- [ ] **Descend stairs** — Find `>`, press `>` to go down — level 2 generates
- [ ] **Quit game** — Press `Esc`, confirm quit, game closes cleanly

---

## ✅ Save/Load

- [ ] **Save on quit** — When prompted "Save before quitting?", select Yes
- [ ] **Relaunch game** — Start the game again
- [ ] **Load save** — Select "Continue" from main menu — returns to saved state
- [ ] **Save file exists** — Check the user data directory:
  - macOS: `~/Library/Application Support/CatacombsOfYARL/saves/savegame.json`
  - Windows: `%APPDATA%\CatacombsOfYARL\saves\savegame.json`
  - Linux: `~/.local/share/catacombs-of-yarl/saves/savegame.json`

---

## ✅ Logs Created

- [ ] **Log directory exists** — Check user data folder has `logs/` subdirectory
- [ ] **rlike.log present** — Main log file created with recent timestamps

---

## 🤖 Optional: Bot Mode (if shipping)

```bash
./CatacombsOfYARL --bot-soak --runs 1 --headless --max-turns 50
```

- [ ] **Completes without crash** — Session summary prints
- [ ] **No "file not found" errors** — All configs load correctly

---

## 📋 Platform-Specific

### macOS
- [ ] First launch: Right-click → Open (bypasses Gatekeeper)
- [ ] Or run: `xattr -cr CatacombsOfYARL` to clear quarantine

### Windows
- [ ] SmartScreen warning: Click "More info" → "Run anyway"

### Linux
- [ ] Executable permission: `chmod +x CatacombsOfYARL` if needed

---

## 🐛 Common Issues

| Symptom | Likely Cause |
|---------|--------------|
| Black screen on launch | Font file missing from bundle |
| "Configuration file not found" | Config YAML not bundled correctly |
| Can't save game | User data directory not writable |
| Crash on new game | Entity/level config YAML missing |

---

**If all boxes are checked, the build is ready to ship! 🎉**
