# 🔧 Refactoring Guide - Quick Start

**Purpose:** Quick reference for executing the 3 critical refactors  
**Timeline:** 2 weeks total (3 days + 4 days + 5 days)  
**Status:** Ready to execute

---

## 📦 **What We're Refactoring**

### **Week 1: Foundation Refactors**
1. **Component Registry** (Days 1-3) - Type-safe component lookups
2. **Spell Registry** (Days 4-7) - Unified spell/item system

### **Week 2: Turn System**
3. **Turn Manager** (Days 8-12) - Unified turn processing

---

## 🚀 **Getting Started**

### **Before You Begin**
```bash
# Ensure you're on main with latest changes
git checkout main
git pull origin main

# Verify all tests pass
python -m pytest tests/ -q

# Check current metrics
grep -r "hasattr" --include="*.py" . | wc -l  # Should show ~121
wc -l item_functions.py  # Should show ~1242
```

### **Daily Workflow**
```bash
# 1. Start your workday
git checkout refactor/component-registry  # or current refactor branch
git pull origin main  # Keep up to date

# 2. Work on checklist items
# See docs/REFACTOR_[NAME].md for detailed plan

# 3. Test frequently
python -m pytest tests/test_[relevant].py -xvs  # Test specific file
python -m pytest tests/ -q  # Full test suite

# 4. Commit frequently
git add .
git commit -m "refactor: [what you did]"

# 5. End of day
git push origin refactor/component-registry
```

---

## 📋 **Refactor #1: Component Registry** (3 days)

### **Day 1: Foundation**
```bash
# Branch: refactor/component-registry (already created!)

# Tasks:
1. Create components/component_registry.py
2. Implement ComponentType enum
3. Implement ComponentRegistry class  
4. Update Entity class
5. Write tests

# Test command:
python -m pytest tests/test_component_registry.py -xvs
```

### **Day 2: Entity Migration**
```bash
# Tasks:
1. Update entity.py hasattr calls
2. Update components/*.py files
3. Test after each file

# Track progress:
grep -r "hasattr.*fighter\|hasattr.*ai\|hasattr.*inventory" --include="*.py" components/ | wc -l

# Test command:
python -m pytest tests/test_entity.py tests/test_fighter.py -xvs
```

### **Day 3: System-Wide Migration**
```bash
# Tasks:
1. Update game_actions.py
2. Update render_functions.py
3. Update all remaining files

# Track progress:
grep -r "hasattr" --include="*.py" . | wc -l  # Goal: <30

# Final test:
python -m pytest tests/ -q  # ALL tests must pass
```

### **Completion Checklist**
- [ ] All 1,855 tests passing
- [ ] hasattr() count <30
- [ ] PR created and reviewed
- [ ] Merged to main
- [ ] TECH_DEBT.md updated

---

## 📋 **Refactor #2: Spell Registry** (4 days)

### **Branch Setup**
```bash
git checkout main
git pull origin main
git checkout -b refactor/spell-registry
```

### **Day 4: Design**
```bash
# Tasks:
1. Create config/spell_registry.py
2. Design Spell dataclass
3. Design SpellRegistry class
4. Define all 20+ spells
5. Write tests
```

### **Day 5-6: Consolidation**
```bash
# Tasks:
1. Refactor item_functions.py
2. Update entity_factory.py
3. Update tooltips
4. Update monster AI

# Track progress:
wc -l item_functions.py  # Goal: <800 lines
```

### **Day 7: Testing & Polish**
```bash
# Tasks:
1. Full test suite
2. Add spell metadata
3. Documentation
4. PR and merge
```

---

## 📋 **Refactor #3: Turn Manager** (5 days)

### **Branch Setup**
```bash
git checkout main
git pull origin main
git checkout -b refactor/turn-manager
```

### **Day 8-9: Core System**
```bash
# Tasks:
1. Create engine/turn_manager.py
2. Design TurnManager class
3. Design TurnListener interface
4. Write core tests
```

### **Day 10-11: Migration**
```bash
# Tasks:
1. Refactor AISystem
2. Move hazard processing
3. Update pathfinding logic
4. Update action processing
```

### **Day 12: Integration**
```bash
# Tasks:
1. End-to-end testing
2. Performance verification
3. Documentation
4. PR and merge
```

---

## ✅ **Testing Checklist**

### **After Every File Change**
```bash
# Quick smoke test
python -m pytest tests/test_[file].py -x

# If that passes, run relevant systems
python -m pytest tests/test_entity.py tests/test_fighter.py -x
```

### **After Every Day**
```bash
# Full test suite
python -m pytest tests/ -q --tb=short

# Should see: "1855 passed in ~20s"
```

### **Before PR**
```bash
# Clean test run
python -m pytest tests/ -xvs

# Check coverage (optional)
python -m pytest tests/ --cov=. --cov-report=html

# Verify no new warnings
python -m pytest tests/ --tb=short 2>&1 | grep -i warning
```

---

## 🐛 **Common Issues & Solutions**

### **Issue: Tests failing after change**
```bash
# Identify the exact test
python -m pytest tests/ -x  # Stops at first failure

# Run just that test with verbose output
python -m pytest tests/test_X.py::test_Y -xvs

# Check if you need to update mocks
grep -n "Mock\|patch" tests/test_X.py
```

### **Issue: Import errors**
```bash
# Check circular imports
python -c "import entity"

# Check if you need __init__.py updates
find . -name "__init__.py" -type f
```

### **Issue: hasattr() not decreasing**
```bash
# Find remaining hasattr calls
grep -rn "hasattr" --include="*.py" . | grep -v test | grep -v ".pyc"

# Focus on specific components
grep -rn "hasattr.*fighter" --include="*.py" .
```

---

## 📊 **Progress Tracking**

### **Metrics to Check Daily**
```bash
# hasattr count (Refactor #1)
grep -r "hasattr" --include="*.py" . | wc -l

# item_functions.py size (Refactor #2)
wc -l item_functions.py

# Test count
python -m pytest tests/ --collect-only | grep "test session starts" -A 1

# Test runtime
time python -m pytest tests/ -q
```

### **Update TECH_DEBT.md**
```bash
# Mark progress in TECH_DEBT.md
# Update checkboxes: - [ ] → - [x]
# Commit daily: git commit -am "docs: Update refactor progress"
```

---

## 🎉 **Completion Ceremony**

### **After Each Refactor**
1. ✅ Merge PR to main
2. ✅ Tag release: `git tag v3.7.0-refactor-[name]`
3. ✅ Update TECH_DEBT.md (move to COMPLETED)
4. ✅ Celebrate! 🎊
5. ✅ Take a break before next refactor

### **After All 3 Refactors**
1. ✅ Create summary document
2. ✅ Update ROADMAP.md
3. ✅ Blog post about the refactoring journey
4. ✅ Start Phase 3 features with clean architecture!

---

## 💡 **Pro Tips**

1. **Commit Often** - Small commits are easier to review and revert
2. **Test After Each File** - Catch breaks immediately
3. **Keep Notes** - Document surprises and decisions
4. **Ask Questions** - Unclear about design? Stop and discuss
5. **Take Breaks** - Refactoring is mentally intensive
6. **Celebrate Wins** - Each checklist item is progress!

---

## 📞 **Need Help?**

- **Design Questions:** Review `TECH_DEBT_ANALYSIS.md`
- **Implementation Details:** Check `docs/REFACTOR_[NAME].md`
- **Test Issues:** Check test file history: `git log tests/test_X.py`
- **Stuck:** Commit current work, create WIP PR, ask for feedback

---

**Ready to start? Let's do this! 🚀**

```bash
git checkout refactor/component-registry
code docs/REFACTOR_COMPONENT_REGISTRY.md  # Read the plan
code components/component_registry.py      # Create the file
# ... and you're off!
```
