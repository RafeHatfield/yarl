# Testing Guide: Exploration & Discovery Features

This guide will help you test all the new exploration features (chests, signposts, secret doors, and vaults) using the testing configuration.

## 🧪 **Enable Testing Mode**

Testing mode activates special level configurations that make features easier to test.

### **Option 1: Environment Variable (Recommended)**
```bash
export YARL_TESTING_MODE=1
python3 engine.py
```

### **Option 2: One-liner**
```bash
YARL_TESTING_MODE=1 python3 engine.py
```

### **Option 3: Permanent (for testing session)**
Add to your `~/.bashrc` or `~/.zshrc`:
```bash
export YARL_TESTING_MODE=1
```
Then reload: `source ~/.bashrc`

---

## 📋 **Testing Checklist**

### **Level 1: Exploration & Discovery**

**What to test:**
- [ ] **Chests (4 types)**
  - [ ] Normal chest (brown 'C')
  - [ ] Golden chest (gold 'C')
  - [ ] Trapped chest (dark brown 'C') - triggers trap on open
  - [ ] Locked chest (grey 'C') - requires key
- [ ] **Signposts (4 types)**
  - [ ] Lore sign (brown '|')
  - [ ] Warning sign (red/orange '|')
  - [ ] Humor sign (cyan '|')
  - [ ] Hint sign (gold '|')
- [ ] **Vaults (2 guaranteed)**
  - [ ] Golden walls clearly visible
  - [ ] Elite monsters with "(Elite)" suffix
  - [ ] 2-3 chests per vault
  - [ ] Auto-explore stops on entry
- [ ] **Auto-Explore Stops**
  - [ ] Pauses on vaults
  - [ ] Pauses on chests
  - [ ] Pauses on signposts
  - [ ] Pauses on secret doors (if found)
- [ ] **Visual Distinction**
  - [ ] Chests visible outside FOV (after discovery)
  - [ ] Signposts visible outside FOV
  - [ ] Opened chests appear grey
  - [ ] Vault walls are golden (RGB 200, 150, 50)
- [ ] **Chest Loot**
  - [ ] Items drop on ground near chest
  - [ ] See what items were in chest (message)
  - [ ] Can pick up items normally

**Features Available:**
- 20 healing potions (easy survival)
- Good starting equipment (sword, shield, chain mail, helmet, boots)
- Lots of utility scrolls (teleport, invisibility, identify)
- Ring of Searching (100% secret door detection when worn)

---

### **Level 2: Multiple Vaults & Combat**

**What to test:**
- [ ] **3 Guaranteed Vaults**
  - [ ] All 3 have golden walls
  - [ ] All spawn elite monsters
  - [ ] Each has 2-3 chests
  - [ ] Auto-explore stops at each vault (first visit only)
- [ ] **Elite Monster Combat**
  - [ ] Elite monsters have "(Elite)" suffix
  - [ ] Noticeably tougher (2x HP, +2 damage, +1 AC)
  - [ ] Spawn from depth+2 (tougher variants)
  - [ ] Test combat with buff potions (speed, heroism, protection)
- [ ] **Multiple Chests**
  - [ ] 11 guaranteed chests on map (from level template)
  - [ ] 6-9 more chests from vaults (2-3 per vault)
  - [ ] Test various chest types (normal, golden, trapped, locked)
- [ ] **Loot Quality**
  - [ ] Vault chests have higher quality loot
  - [ ] Compare golden vs normal chests
  - [ ] Check bonus items on vault floors
- [ ] **Survival**
  - [ ] 30 healing potions available
  - [ ] Buff potions help in combat
  - [ ] Lots of escape options (teleport, invisibility)

**Features Available:**
- 30 healing potions (survive tough fights)
- Better equipment (plate armor, greatsword option)
- Buff potions (speed, heroism, protection, regeneration)
- Lots of scrolls (combat + utility)
- Multiple rings (protection, regeneration, might, searching)
- 2 wands (lightning, fireball)

---

### **Level 3+: Random Vaults (Testing Mode)**

**Random Vault Generation:**
- **Testing mode:** 50% spawn rate on level 3+
- **Normal mode:** 10-20% spawn rate on level 4+
- Level templates can override with `vault_count` parameter

**What to test (if vaults spawn):**
- [ ] **Visual Distinction**
  - [ ] Golden walls (RGB 200, 150, 50)
  - [ ] Clearly distinguishable from normal brown walls
  - [ ] Visible in both lit and dark areas
- [ ] **Elite Monsters**
  - [ ] Monsters have "(Elite)" suffix
  - [ ] Noticeably tougher (2x HP)
  - [ ] Hit harder (+2 damage)
  - [ ] Better defense (+1 AC)
- [ ] **Guaranteed Loot**
  - [ ] 2-3 chests spawn in vault
  - [ ] Mostly golden/rare chests
  - [ ] 1-2 bonus items on floor
- [ ] **Auto-Explore**
  - [ ] Stops with "Discovered treasure vault!" message
  - [ ] Only triggers once per vault
- [ ] **Risk/Reward Balance**
  - [ ] Vaults feel appropriately challenging
  - [ ] Loot feels rewarding for the risk
  - [ ] Can choose to skip vault if too dangerous

---

### **Custom Vault Configuration (YAML)**

**For level designers:**
You can now specify exact vault counts in `level_templates.yaml`:

```yaml
level_overrides:
  5:
    parameters:
      vault_count: 1  # Force 1 vault on level 5
  
  10:
    parameters:
      vault_count: 3  # Epic level with 3 vaults!
  
  15:
    parameters:
      vault_count: 0  # Disable vaults on level 15
```

**Benefits:**
- ✅ Works on any level (ignores depth restrictions)
- ✅ Exact control over vault count (0 to N)
- ✅ No code changes needed
- ✅ Consistent with other level template features

---

## 🎮 **Testing Tips**

### **Quick Tests:**
1. **Chest Interaction:**
   - Click on chest to open
   - If not adjacent, auto-pathfinds to it
   - Items drop on ground for pickup

2. **Signpost Reading:**
   - Click on signpost to read
   - If not adjacent, auto-pathfinds to it
   - Different colors for different types

3. **Secret Doors:**
   - Wear Ring of Searching for 100% detection
   - Or use 'S' key to search (10-tile radius)
   - Secret doors appear as cyan '+' when found
   - Remain visible outside FOV

4. **Auto-Explore:**
   - Press 'O' to start auto-explore
   - Should stop for: monsters, vaults, chests, signposts, secret doors, loot
   - Check console logs for stop reasons

### **Debug Logging:**
Check the console for messages like:
```
Level 1: Designated vault at room center (25, 15)
Spawning 4 elite monsters in vault
Spawning 3 chests in vault
Placed chest at (24, 14) in vault
Entered new treasure vault at grid (2, 1)
```

---

## 🐛 **Known Issues / Expected Behavior**

### **Normal Behavior:**
- Vaults don't spawn on levels 1-3 in normal mode (only testing mode)
- Secret doors are rare (15% chance per level)
- Not every room will have chests/signposts (30% and 20% spawn rates)

### **Testing Mode Changes:**
- ✅ Vaults spawn on any level (80% on 1-2, 50% on 3+)
- ✅ Normal chest/signpost spawn rates still apply
- ✅ Secret door spawn rate unchanged (15%)

---

## 📝 **Bug Reporting Template**

If you find issues, please report with:

```
**Feature:** (e.g., "Chest Opening")
**Level:** (e.g., "Level 1")
**Expected:** (e.g., "Items should drop on ground")
**Actual:** (e.g., "Items added to inventory instead")
**Steps to Reproduce:**
1. Start game with YARL_TESTING_MODE=1
2. Go to level 1
3. Click on chest
4. ...
**Console Output:** (copy any error messages)
```

---

## 🎯 **Success Criteria**

Before considering features complete, verify:
- [ ] All chest types spawn and open correctly
- [ ] All signpost types spawn and read correctly
- [ ] Secret doors are findable (passive + active search)
- [ ] Vaults spawn with golden walls at depth 3+ (testing mode: any level)
- [ ] Elite monsters spawn in vaults and are tougher
- [ ] Auto-explore stops for all new features
- [ ] Visual distinction is clear for all features
- [ ] No crashes or errors
- [ ] Performance is acceptable (no lag)

---

## 🚀 **After Testing**

When done testing:
```bash
unset YARL_TESTING_MODE
```

Or close the terminal to end the testing session.

---

**Happy Testing! 🎮**

