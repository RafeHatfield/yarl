# Headless Mode for Soak Testing

**Date**: November 25, 2025  
**Status**: ✅ Complete

---

## Overview

Added configurable **headless mode** for bot/soak testing via `--headless` flag.

---

## Usage

### **With Window (Default)**
```bash
make soak
# or
python engine.py --bot-soak --runs 10
```

- ✅ Game window visible
- ✅ Can watch bot play in real-time
- ✅ Good for debugging/demo

### **Headless (No Window)**
```bash
make soak-headless
# or  
python engine.py --bot-soak --headless --runs 10
```

- ✅ No window created
- ✅ Faster execution
- ✅ Perfect for CI/automated testing
- ✅ Lower resource usage

---

## Implementation

### **engine.py** - Added `--headless` argument
```python
parser.add_argument(
    '--headless',
    action='store_true',
    help='Run in headless mode (no window, for CI/automated testing)'
)
```

### **engine.py** - Set SDL environment variable when headless
```python
if args.headless:
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    print("🔇 Headless mode enabled (no window)")
else:
    print("🖥️  Window mode enabled (game visible)")
```

### **Makefile** - Two targets
```makefile
soak: clean
    # With window (default)
    $(PYTHON) engine.py --bot-soak --runs 200 ...

soak-headless: clean
    # No window (headless)
    $(PYTHON) engine.py --bot-soak --headless --runs 200 ...
```

---

## Benefits

### **With Window (`make soak`)**
- See the game running
- Watch bot behavior
- Visual feedback
- Good for development/debugging

### **Headless (`make soak-headless`)**
- No window overhead
- Faster execution
- CI/server-friendly
- Can run in background
- Lower CPU/GPU usage

---

## Examples

```bash
# Quick soak test with window (10 runs)
python engine.py --bot-soak --runs 10

# Long soak test headless (1000 runs, fast)
python engine.py --bot-soak --headless --runs 1000

# Overnight soak headless with metrics
python engine.py --bot-soak --headless --runs 10000 \
    --max-turns 5000 --metrics-log logs/overnight.jsonl

# Debug mode with window (watch it play)
python engine.py --bot-soak --runs 1 --max-turns 100
```

---

## Files Modified

- `engine.py` - Added `--headless` argument, conditional SDL_VIDEODRIVER
- `Makefile` - Added `soak-headless` target

**Total**: 2 files, ~10 lines added

---

## Result

**Flexible soak testing:**
- ✅ `make soak` - with window (default)
- ✅ `make soak-headless` - no window (fast)
- ✅ `--headless` flag for manual control
- ✅ Backward compatible (default is with window)

**Best of both worlds** ✅


