# Logging System Consolidation

**Status:** Phase 1-2 COMPLETE ✅  
**Scope:** Standardize logging across the project  
**Estimated Time:** 2-3 hours  

---

## Current State (Audit Results)

### Logging Usage Patterns
- **logging.getLogger():** 85 uses across 75 files
- **logger.debug():** 231 uses across 56 files
- **logger.info():** 243 uses across 53 files
- **logger.warning():** 160 uses across 40 files
- **logger.error():** 153 uses across 46 files
- **print():** 996 uses (mostly in demos)
- **MonsterActionLogger:** 37 uses (specialized)

### Log Files
- `combat_debug.log` - 1.9 MB
- `debug.log` - 531 KB
- `errors.log` - 244 KB
- `monster_actions.log` - **29 MB** (largest)
- `my_test_results.log` - 48 KB
- **Total:** ~33 MB of logs

### Specialized Logging
- `debug_logging.py` - Global debug utilities
- `components/monster_action_logger.py` - Monster-specific logging
- `examples/demos/` - Extensive debug output via print()

---

## Issues with Current System

1. **Scattered Configuration:** Each module calls `logging.getLogger()` independently
2. **Inconsistent Formatting:** No unified message format
3. **No Log Rotation:** Logs grow unbounded (~33 MB)
4. **Multiple Log Files:** Hard to correlate events across logs
5. **Print Statements:** 996 uses bypass logging system
6. **Duplicate Logic:** Monster logger separate from main logging

---

## Consolidation Plan

### Phase 1: Create Central Logger (30 min)

**File:** `logger_config.py`

```python
import logging
import logging.handlers
import os

def setup_logging(log_level=logging.WARNING):
    """Configure centralized logging for entire application."""
    
    # Create logs directory if needed
    os.makedirs('logs', exist_ok=True)
    
    # Main application logger
    app_logger = logging.getLogger('rlike')
    app_logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    app_logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '[%(levelname)s] %(message)s'
    )
    
    # File handler (rotating)
    file_handler = logging.handlers.RotatingFileHandler(
        'logs/rlike.log',
        maxBytes=10_000_000,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    app_logger.addHandler(file_handler)
    
    # Error file handler (separate)
    error_handler = logging.handlers.RotatingFileHandler(
        'logs/rlike_errors.log',
        maxBytes=5_000_000,  # 5 MB
        backupCount=3
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    app_logger.addHandler(error_handler)
    
    # Console handler (development only)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(simple_formatter)
    app_logger.addHandler(console_handler)
    
    return app_logger

def get_logger(name):
    """Get a logger for a specific module."""
    return logging.getLogger(f'rlike.{name}')
```

### Phase 2: Update All Modules (1.5 hours)

**Pattern:** Replace scattered `logging.getLogger()` calls with centralized function.

**Before:**
```python
import logging
logger = logging.getLogger(__name__)
```

**After:**
```python
from logger_config import get_logger
logger = get_logger(__name__)
```

**Apply to:**
- Top 10 files by logging usage (covers 60% of calls)
- Priority: game_actions.py, components/ai.py, services/movement_service.py, etc.

### Phase 3: Consolidate Specialized Loggers (30 min)

**Replace MonsterActionLogger with centralized logger:**
```python
# Before
from components.monster_action_logger import MonsterActionLogger
monster_logger = MonsterActionLogger()

# After
from logger_config import get_logger
logger = get_logger('monsters')
logger.debug(f"Monster action: {action}")
```

### Phase 4: Clean Up (30 min)

1. Remove `debug_logging.py` (no longer needed)
2. Archive existing log files to `logs/archived/`
3. Update `.gitignore` to ignore `logs/` directory

---

## Benefits

✅ **Centralized Configuration:** Single source of truth for logging  
✅ **Log Rotation:** Prevents disk space issues (max 10 MB per file)  
✅ **Unified Format:** All messages consistent  
✅ **Separate Error Log:** Easy error tracking  
✅ **Module Hierarchy:** `rlike.game_actions`, `rlike.ai`, etc.  
✅ **Easier Debugging:** Can adjust log levels globally or per-module  

---

## Implementation Order

1. Create `logger_config.py`
2. Update top 10 logging-heavy files
3. Consolidate MonsterActionLogger
4. Clean up old logging infrastructure
5. Test with actual gameplay

---

**Ready to implement? (Y/N)**

