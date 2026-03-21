# Distribution Readiness Audit - Catacombs of YARL
**Date:** January 19, 2026  
**Purpose:** Investigation-only assessment for PyInstaller/distribution packaging  
**Scope:** Identify required changes before creating downloadable builds

---

## 1) Entry Point

### Canonical Executable Entry Point
**File:** `engine.py`  
**Function:** `main()` (line 266)  
**Invocation:** `python engine.py` or `python3 engine.py`

### Entry Point Analysis
- **Single clear startup path:** ✅ YES
  - `engine.py` line 622: `if __name__ == "__main__": main()`
  - No `__main__.py` or `-m` package entry point exists
  - `app.py` is a dummy "Hello World" file (not used)

### Command Line Modes
The entry point supports multiple operational modes via argparse:
- Normal gameplay: `python engine.py`
- Bot mode: `python engine.py --bot`
- Bot soak: `python engine.py --bot-soak`
- Headless: `python engine.py --headless`
- Testing: `python engine.py --testing`

### Game Loop Location
- **File:** `engine/game_engine.py` (via `play_game_with_engine()`)
- Main loop coordinator in `engine.py` line ~470-550

**Verdict:** Clean single entry point. No changes needed for packaging.

---

## 2) Windowing / Native Dependencies

### Primary Rendering Library
**Library:** `tcod` (python-tcod) v19.5.0  
**Purpose:** Terminal/console rendering via libtcod (native C library)

### Native Dependencies Breakdown
From `requirements.txt`:
```
tcod==19.5.0         # Requires native libtcod (SDL2-based)
cffi==2.0.0          # Foreign function interface for tcod
numpy==2.3.3         # Numerical operations
PyYAML==6.0.3        # Configuration parsing
psutil==6.1.0        # Process utilities
matplotlib==3.9.2    # Graphing (tools only, not runtime)
```

### Critical libtcod Details
**Key code locations:**
- `engine.py` line 425: `libtcod.console_set_custom_font("arial10x10.png", ...)`
- `engine.py` line 429: `libtcod.console_init_root(...)`
- `engine/soak_harness.py` line 606: Font loading for headless mode

### SDL2 Backend
- tcod uses SDL2 as rendering backend
- SDL2 shared libraries (.dylib/.so/.dll) are bundled with tcod wheel
- Headless mode: Uses SDL dummy driver (`SDL_VIDEODRIVER=dummy`)

### PyInstaller Compatibility
**Known tcod PyInstaller Issues:**
- **MEDIUM RISK:** tcod has native shared libraries that must be collected
- Font files (`.png`) must be bundled as data files
- SDL2 libs typically auto-collected by PyInstaller hooks, BUT:
  - Custom fonts like `arial10x10.png` require explicit `--add-data`
  - tcod's internal data files may need hooks

**Official tcod PyInstaller Support:** 
- tcod maintainer has provided PyInstaller hooks in past releases
- Hook file location: Typically in `tcod` package or custom hook needed
- **Action Required:** Test if current tcod==19.5.0 includes hooks

---

## 3) Asset & Data Loading

### Non-Code Assets Required at Runtime

#### Category 1: Fonts & Graphics
**Location:** Root directory
- `arial10x10.png` - Primary game font (REQUIRED)
- `menu_background1.png` - Menu background (REQUIRED)

**Loading Method:**
- Direct relative path from `cwd`: `"arial10x10.png"`
- **ASSUMES:** Current working directory is repo root
- **RISK:** Will break if executable is in different directory

#### Category 2: YAML Configuration Files
**Location:** `config/` directory
- `config/game_constants.yaml` - Core game constants
- `config/entities.yaml` - Monster/item definitions  
- `config/level_templates.yaml` - Level generation templates
- `config/level_templates_testing.yaml` - Testing overrides
- `config/signpost_messages.yaml` - In-game text
- `config/murals_inscriptions.yaml` - Environmental lore
- `config/entity_dialogue.yaml` - NPC dialogue
- `config/endings.yaml` - Victory/defeat messages
- `config/guide_dialogue.yaml` - Tutorial text
- `config/vault_themes.yaml` - Vault styling
- `config/etp_config.yaml` - Encounter budgeting
- `config/loot_policy.yaml` - Loot generation
- `config/yo_mama_jokes.yaml` - Easter eggs
- `config/item_appearances.py` - (Python module, not data)

**Scenario Files:** `config/levels/` - 70 YAML scenario definitions

**Loading Method:**
```python
# config/game_constants.py line 881
_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'game_constants.yaml')
```
- Uses `os.path.dirname(__file__)` pattern
- **RISK LEVEL:** MEDIUM
  - Will work in PyInstaller onedir build (maintains relative structure)
  - **WILL BREAK** in PyInstaller onefile build (`__file__` points to temp directory)

#### Category 3: Data Files
**Location:** `data/` directory
- `data/hall_of_fame.yaml` - Player achievements (runtime read/write)

#### Category 4: Reports/Baselines (Optional)
**Location:** `reports/baselines/`
- `balance_suite_baseline.json` - Balance testing reference
- **Not required for gameplay** - Only for development/testing

**Loading Method:** Direct file paths, assumes repo structure

#### Category 5: Docs/Licenses
**Files that should be bundled:**
- `LICENSE` - Required for distribution
- `README.md` - User documentation (optional)
- `STORY_LORE_CANONICAL.md` - Game lore (optional)

**Not required at runtime** - These are informational only

### Path Resolution Patterns Found

#### Pattern 1: Relative to CWD (PROBLEMATIC)
```python
# engine.py line 425
"arial10x10.png"  # No path resolution, assumes cwd is repo root
```
**Files using this pattern:**
- `arial10x10.png`
- `menu_background1.png`
- Save files: `savegame.json`, `savegame.dat.db`

#### Pattern 2: Relative to Module (BETTER)
```python
# config/game_constants.py line 881
os.path.join(os.path.dirname(__file__), 'game_constants.yaml')
```
**Files using this pattern:**
- All YAML files in `config/`
- Works in onedir, breaks in onefile

#### Pattern 3: Asset Manager (EXPERIMENTAL)
```python
# assets/manager.py line 49
self.asset_paths = asset_paths or ['assets', 'data', 'resources']
```
**Status:** Asset management system exists but appears unused by main game  
**Location:** `assets/` package (experimental/demo)

### CWD Assumptions
**Critical assumption locations:**
- `engine.py` - Assumes `arial10x10.png` in cwd
- `loader_functions/data_loaders.py` line 67: `open("savegame.json")`
- `logger_config.py` line 27: `os.makedirs('logs', exist_ok=True)`
- All YAML loaders use `os.path.dirname(__file__)` (better, but not perfect)

---

## 4) File Writes / Runtime State

### Save Game Files
**Location:** Current working directory (cwd)
**Files:**
- `savegame.json` - Primary save format
- `savegame.dat.db` - Legacy shelve format (fallback)

**Write locations:**
- `loader_functions/data_loaders.py` line 67: `open("savegame.json", "w")`
- **ASSUMES:** Writable cwd
- **RISK:** Breaks if installed to Program Files (Windows) or /Applications (macOS)

### Log Files
**Location:** `logs/` directory (created if missing)
**Files:**
- `logs/rlike.log` - Main log (10MB rotating, 5 backups)
- `logs/rlike_errors.log` - Error log (5MB rotating, 3 backups)

**Write locations:**
- `logger_config.py` line 27: `os.makedirs('logs', exist_ok=True)`
- **ASSUMES:** Writable cwd

### Additional Runtime Writes
**Telemetry (bot mode):**
- `telemetry/*.jsonl` - Bot soak run metrics
- Written during `--bot-soak` mode

**Reports (dev tools):**
- `reports/balance_suite/*` - Generated by balance suite
- `reports/hazards_suite/*` - Generated by hazards suite
- `reports/metrics/*` - Performance metrics
- **Not needed for gameplay**

### Hall of Fame
**File:** `data/hall_of_fame.yaml`
**Usage:** Read/write player achievements
**Location:** `systems/hall_of_fame.py`

### Writable Directory Abstraction Needed?
**YES** - Required for:
1. Save games
2. Log files
3. Hall of Fame updates
4. Telemetry (if bot mode used)

**Strategy:**
- Use platform-specific user data directory:
  - Windows: `%APPDATA%/CatacombsOfYARL/`
  - macOS: `~/Library/Application Support/CatacombsOfYARL/`
  - Linux: `~/.local/share/catacombs-of-yarl/`
- Or fallback to `cwd` if writable

---

## 5) Platform Assumptions

### OS-Specific Code Paths
**None found** - No `sys.platform` or `platform.system()` checks in core code

### Environment Variables
**SDL_VIDEODRIVER:**
- `engine.py` line 45: `os.environ['SDL_VIDEODRIVER'] = 'dummy'`
- **Purpose:** Headless mode for bot/testing
- **Platform:** Cross-platform (SDL2 feature)

### Shell Calls / Subprocesses
**Found in dev tools only:**
- `tools/balance_suite.py` - Uses `subprocess.run()` to call `ecosystem_sanity.py`
- `tools/hazards_suite.py` - Uses `subprocess.run()` to call `ecosystem_sanity.py`
- **Impact:** Dev tools, not runtime gameplay
- **Risk:** None for packaged gameplay executable

### Platform-Specific Paths
**None found** - All file operations use `os.path.join()` (cross-platform)

**Verdict:** Excellent cross-platform compatibility. No platform-specific refactoring needed.

---

## 6) Test / Dev Artifacts

### Directories to EXCLUDE from Distribution

#### Test Code
- `tests/` - 249 test files, 68,878 lines
- Root-level test files:
  - `test_*.py` (9 files)
  - `run_critical_tests.py`
  - `run_golden_path_tests.py`

#### Dev Tools
- `tools/` - Balance suite, hazards suite, difficulty visualizer
- `scripts/` - CI scripts (bash)
- `batch_fix_tests.sh`

#### Development Documentation
- `docs/` - 121 markdown files (keep README.md, LICENSE only)
- `archive/` - Old documentation
- `examples/` - Demo code

#### Generated Artifacts
- `reports/` (except `reports/baselines/balance_suite_baseline.json` if needed)
- `logs/` - Runtime logs (ignored, created at runtime)
- `telemetry/` - Bot soak output
- `my_custom_saves/` - Dev save directory
- Output JSON files in root:
  - `*_runs.json` (40+ files)
  - `output.json`

#### Build/Cache
- `__pycache__/`
- `.pytest_cache/`
- `.mypy_cache/`
- `.vscode/`
- `venv/`, `source/`

#### Development Config
- `pytest.ini`
- `requirements-dev.txt`
- `Makefile`
- `.gitignore`

### Test-Only Imports in Runtime Paths
**None found** - Test imports (pytest, unittest) are properly isolated in `tests/`

**Notable:**
- `config/testing_config.py` - Testing mode flags (KEEP - used by `--testing` flag)
- All test files properly scoped to `tests/` directory

### Recommended Exclusions for PyInstaller
```python
# Add to spec file excludes
excludes = [
    'tests',
    'tools',
    'scripts',
    'docs',
    'archive',
    'examples',
    'pytest',
    'pytest_cov',
    'pytest_mock',
    'unittest',
    'coverage',
    'black',
    'flake8',
    'mypy',
    'matplotlib',  # Only used in tools, not gameplay
]
```

---

## 7) Packaging Risk Assessment

### PyInstaller Folder Build (--onedir)
**RISK LEVEL:** LOW-MEDIUM

**Pros:**
- Maintains directory structure (relative imports work)
- `__file__` paths mostly work correctly
- Easier debugging (can inspect files)
- Faster rebuild times during development

**Cons:**
- Larger distribution (folder of ~50-100MB)
- More files to manage

**Specific Risks:**
1. **MEDIUM:** Font file (`arial10x10.png`) needs `--add-data`
2. **MEDIUM:** Config YAML files need `--add-data` for entire `config/` tree
3. **LOW:** tcod native libraries (likely auto-collected by hooks)
4. **LOW:** Save file directory creation (just needs mkdir)

**Mitigation:**
```bash
--add-data "arial10x10.png:."
--add-data "menu_background1.png:."
--add-data "config:config"
--add-data "data:data"
```

---

### PyInstaller Onefile Build (--onefile)
**RISK LEVEL:** HIGH

**Pros:**
- Single executable file
- Easier distribution (drag & drop)
- Smaller apparent footprint

**Cons:**
- Slower startup (extract to temp dir each run)
- `__file__` points to temp directory (breaks YAML loading)
- Harder debugging
- Must handle writable directories differently

**Specific Risks:**
1. **HIGH:** All `os.path.dirname(__file__)` patterns break
   - Affects all YAML config loading
   - Requires `sys._MEIPASS` abstraction
2. **HIGH:** Save files can't write to temp directory (gets deleted)
3. **MEDIUM:** Font path resolution needs update
4. **LOW:** Startup time penalty (decompress/extract)

**Required Code Changes:**
- Add resource path helper:
```python
def resource_path(relative_path):
    """Get absolute path to resource (works for dev and PyInstaller)"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)
```
- Update all asset loading to use `resource_path()`
- Add user data directory logic for saves/logs

---

### Briefcase App Bundle
**RISK LEVEL:** MEDIUM

**Platform:** macOS .app, Windows MSIX, Linux AppImage

**Pros:**
- Platform-native installers
- Code signing support (macOS/Windows)
- Better integration (file associations, etc.)

**Cons:**
- More complex build process
- Platform-specific configurations
- Requires separate builds per platform

**Specific Risks:**
1. **MEDIUM:** Same `__file__` issues as PyInstaller onefile
2. **MEDIUM:** Sandboxing restrictions (especially macOS)
3. **LOW:** tcod compatibility (generally good with Briefcase)

**Mitigation:** Same as PyInstaller onefile (resource path helper)

---

### Nuitka
**RISK LEVEL:** MEDIUM-HIGH

**Pros:**
- Compiles to native code (faster execution)
- Better startup time than PyInstaller onefile
- Good Python compatibility

**Cons:**
- Longer compilation time
- More complex debugging
- Less mature for complex dependencies
- Module discovery can be finicky

**Specific Risks:**
1. **HIGH:** Dynamic imports may need explicit inclusion
2. **MEDIUM:** YAML loading via `yaml.safe_load` (generally works)
3. **MEDIUM:** tcod compatibility (native libs need care)
4. **LOW:** NumPy compatibility (generally good)

**Mitigation:**
- Use Nuitka standalone mode
- Explicit `--include-package=config`
- Same resource path helper as PyInstaller

---

## 8) Recommendation

### Initial Distribution Approach
**RECOMMENDED:** PyInstaller folder build (`--onedir`)

**Rationale:**
1. **Lowest risk** - Directory structure preserved
2. **Minimal code changes** - Only need to add `--add-data` flags
3. **Debugging friendly** - Can inspect extracted files
4. **tcod compatible** - Well-tested with PyInstaller
5. **Quick iteration** - Faster builds during testing

### Top 3 Changes BEFORE Packaging

#### Change 1: Create Asset Path Helper (CRITICAL)
**Why:** Prepare for both onedir and future onefile builds  
**Where:** Create new file `utils/resource_paths.py`

```python
import os
import sys

def get_resource_path(relative_path):
    """Get absolute path to resource (works for dev and PyInstaller)."""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # PyInstaller onefile mode
        base_path = sys._MEIPASS
    else:
        # Development mode or PyInstaller onedir
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def get_user_data_dir():
    """Get platform-specific user data directory for saves/logs."""
    import platform
    app_name = "CatacombsOfYARL"
    
    system = platform.system()
    if system == "Windows":
        base = os.environ.get('APPDATA', os.path.expanduser('~'))
        return os.path.join(base, app_name)
    elif system == "Darwin":  # macOS
        return os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', app_name)
    else:  # Linux/Unix
        return os.path.join(os.path.expanduser('~'), '.local', 'share', app_name.lower())
```

**Impact:** 1 new file, ~30 lines

#### Change 2: Update Font Loading in engine.py (CRITICAL)
**Why:** Font must load from bundled location, not cwd assumption  
**Where:** `engine.py` line 425, `engine/soak_harness.py` line 606

```python
# OLD:
libtcod.console_set_custom_font("arial10x10.png", ...)

# NEW:
from utils.resource_paths import get_resource_path
font_path = get_resource_path("arial10x10.png")
libtcod.console_set_custom_font(font_path, ...)
```

**Impact:** 2 files, 4 lines changed

#### Change 3: Update Save/Log Paths (IMPORTANT)
**Why:** Writes must go to user data directory, not install location  
**Where:** 
- `loader_functions/data_loaders.py` line 67, 96
- `logger_config.py` line 27, 44, 54

```python
# loader_functions/data_loaders.py
from utils.resource_paths import get_user_data_dir
save_dir = get_user_data_dir()
os.makedirs(save_dir, exist_ok=True)
save_path = os.path.join(save_dir, "savegame.json")

# logger_config.py
from utils.resource_paths import get_user_data_dir
log_dir = os.path.join(get_user_data_dir(), 'logs')
os.makedirs(log_dir, exist_ok=True)
```

**Impact:** 2 files, ~10 lines changed

### Optional (Medium Priority)

#### Change 4: Verify tcod PyInstaller Hooks
**Action:** Test build, check if tcod hook collects SDL2 libs correctly  
**Fallback:** Manual `--hidden-import=tcod` if needed

#### Change 5: Create PyInstaller spec file template
**Action:** Generate initial spec with proper excludes and data files  
**Benefit:** Reproducible builds, easier testing

### NOT Recommended Before First Build
- ❌ Switching to asset manager system (too large a refactor)
- ❌ Onefile builds (wait until onedir proven)
- ❌ Code signing (do after successful builds)
- ❌ Platform-specific installers (test portable builds first)

---

## Summary Matrix

| Concern | Status | Action Required |
|---------|--------|----------------|
| Entry point | ✅ Clean | None |
| Platform compatibility | ✅ Excellent | None |
| Native dependencies | ⚠️ tcod | Test PyInstaller hooks |
| Font loading | ❌ CWD assumption | Add resource_path() |
| Config YAML loading | ⚠️ __file__ pattern | Works for onedir, fix for onefile later |
| Save/log writes | ❌ CWD assumption | Add user_data_dir() |
| Test exclusions | ✅ Well-isolated | Standard excludes list |
| Subprocess calls | ✅ Dev tools only | None |

**Overall Readiness:** 75% - Good foundation, needs 3 targeted fixes before packaging

**Estimated Work:** 4-6 hours to implement changes + initial build testing

---

## Next Steps (Out of Scope - Not Implemented)

1. Implement `utils/resource_paths.py` module
2. Update `engine.py` and `engine/soak_harness.py` font loading
3. Update save/log path resolution
4. Create PyInstaller spec file
5. Test onedir build on development machine
6. Test onedir build on clean VM (no Python installed)
7. Document build process
8. (Future) Test onefile build after onedir proven stable

**End of Audit**
