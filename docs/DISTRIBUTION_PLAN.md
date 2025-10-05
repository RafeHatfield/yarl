# 📦 Yarl Distribution Plan

**Goal:** Create standalone executables for Windows and macOS for playtesting/distribution

**Current State:** Python application requiring Python 3.12 + virtual environment + dependencies

**Target State:** Double-click executable (.exe for Windows, .app for macOS) with no Python installation required

---

## 🎯 **Distribution Strategy**

### **Recommended Approach: PyInstaller**

PyInstaller is the standard tool for packaging Python games (including tcod/libtcod games). It bundles:
- Python interpreter
- All dependencies (tcod, PyYAML, etc.)
- Game assets (YAML configs, save files, etc.)
- Native libraries (SDL2, libtcod binaries)

**Pros:**
- ✅ Works for both Windows and macOS
- ✅ Well-documented for tcod games
- ✅ Active community support
- ✅ Handles complex dependencies automatically
- ✅ Creates standalone executables (no Python needed)

**Cons:**
- ⚠️ Large file size (50-100MB typical)
- ⚠️ macOS Gatekeeper warnings (requires signing or user bypass)
- ⚠️ Windows antivirus false positives (common with PyInstaller)
- ⚠️ Some manual configuration needed for tcod

---

## 📋 **Implementation Steps**

### **Phase 1: Setup PyInstaller** (1-2 hours)

**1. Install PyInstaller:**
```bash
pip install pyinstaller
```

**2. Create Basic Spec File:**
```bash
pyi-makespec --onefile --windowed engine.py
```

**3. Customize Spec File** (`yarl.spec`):
```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['engine.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config/*.yaml', 'config'),
        ('config/*.py', 'config'),
        ('docs/*.md', 'docs'),
        # Add all necessary data files
    ],
    hiddenimports=[
        'tcod',
        'tcod.libtcodpy',
        'yaml',
        # Add any dynamic imports
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Yarl',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress executable
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window (set True for debugging)
    disable_windowing_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',  # Optional: Add game icon
)

# macOS-specific .app bundle
app = BUNDLE(
    exe,
    name='Yarl.app',
    icon='assets/icon.icns',  # macOS icon format
    bundle_identifier='com.yarl.roguelike',
    info_plist={
        'NSHighResolutionCapable': 'True',
    },
)
```

**4. Build Executable:**
```bash
# Windows
pyinstaller yarl.spec

# macOS
pyinstaller yarl.spec --target-arch universal2  # For Intel + Apple Silicon
```

**Output:**
- Windows: `dist/Yarl.exe` (~70MB)
- macOS: `dist/Yarl.app` (~80MB)

---

### **Phase 2: Handle tcod/SDL Dependencies** (1-2 hours)

**Common Issues & Solutions:**

**Issue 1: Missing SDL2 Libraries**
```python
# Add to .spec file binaries section:
binaries=[
    ('/path/to/SDL2.dll', '.'),  # Windows
    ('/path/to/libSDL2.dylib', '.'),  # macOS
],
```

**Issue 2: tcod Data Files**
```python
# Add tcod data to datas:
import tcod
tcod_path = os.path.dirname(tcod.__file__)
datas=[
    (tcod_path, 'tcod'),
],
```

**Issue 3: Dynamic Imports**
```python
# Add to hiddenimports:
hiddenimports=[
    'tcod._internal',
    'tcod.libtcodpy',
    'tcod.constants',
],
```

---

### **Phase 3: macOS Code Signing** (Optional, 2-4 hours)

**Problem:** macOS Gatekeeper blocks unsigned apps with scary warnings.

**Solution 1: Ad-hoc Signing (Free, Good for Testing)**
```bash
# Sign the app
codesign --force --deep --sign - dist/Yarl.app

# Verify
codesign --verify --verbose dist/Yarl.app
```

**Users will still see:** "Yarl is from an unidentified developer"
**User workaround:** Right-click → Open → Allow

**Solution 2: Apple Developer Signing ($99/year)**
- Enroll in Apple Developer Program
- Create Developer ID certificate
- Sign with certificate
- Notarize with Apple (xcode-notarize)
- No warnings for users!

**Recommendation for Playtesting:** Use ad-hoc signing + provide instructions for users.

---

### **Phase 4: Windows Antivirus Handling** (1-2 hours)

**Problem:** Windows Defender often flags PyInstaller executables as malware.

**Solutions:**

**1. Add Exception for Your App:**
- Include instructions for users to add exception
- Temporary solution for playtesting

**2. Submit to Microsoft:**
- Upload false positive report to Microsoft
- Takes 2-3 days for review
- Permanent solution

**3. Code Signing Certificate ($50-$300/year):**
- Buy certificate from trusted CA (DigiCert, Sectigo, etc.)
- Sign your .exe
- Builds trust with Windows Defender
- Reduces false positives significantly

**Recommendation for Playtesting:** Provide clear instructions for adding exceptions.

---

### **Phase 5: Distribution Packaging** (1-2 hours)

**Windows Distribution:**

**Option A: ZIP Archive (Simplest)**
```
Yarl_v1.0.0_Windows.zip
├── Yarl.exe
├── README.txt
├── LICENSE.txt
└── CHANGELOG.txt
```

**Option B: Installer (More Professional)**
- Use NSIS or Inno Setup
- Creates proper installer/uninstaller
- Adds Start Menu shortcuts
- Registers uninstaller in Control Panel
- ~2-3 hours additional work

**macOS Distribution:**

**Option A: ZIP Archive**
```
Yarl_v1.0.0_macOS.zip
└── Yarl.app (just the app bundle)
```

**Option B: DMG Image (More Professional)**
- Create .dmg with background image
- Drag-to-Applications folder UI
- Looks professional and polished
- ~1-2 hours additional work

**Tools for DMG:**
- `create-dmg` (open source)
- `appdmg` (node package)

---

### **Phase 6: Testing & Validation** (2-4 hours)

**Critical Testing:**

**1. Clean Machine Testing:**
- Test on Windows PC with NO Python installed
- Test on macOS with NO Python installed
- Verify all features work
- Check save/load functionality
- Test all YAML configs load correctly

**2. Different OS Versions:**
- Windows 10, Windows 11
- macOS Monterey, Ventura, Sonoma
- Both Intel and Apple Silicon Macs

**3. Common Issues Checklist:**
- [ ] Game launches without errors
- [ ] All assets load (YAML files)
- [ ] Save files work correctly
- [ ] Visual effects render properly
- [ ] Keyboard/mouse input works
- [ ] Game quits cleanly
- [ ] No console errors/warnings

---

## ⏱️ **Time Estimates**

### **First-Time Setup (Total: 8-16 hours)**

| Task | Time | Notes |
|------|------|-------|
| PyInstaller setup & learning | 2-3 hours | Initial learning curve |
| Creating .spec file | 1-2 hours | Trial and error with tcod |
| Fixing dependency issues | 2-4 hours | SDL2, tcod binaries, etc. |
| Testing on clean machines | 2-4 hours | Finding missing files |
| Documentation for users | 1-2 hours | Installation instructions |
| macOS signing (ad-hoc) | 30 min | Quick and easy |
| Windows false positive handling | 1-2 hours | Writing instructions |

### **Subsequent Releases (Total: 30 min - 1 hour)**

Once set up, building new releases is fast:
```bash
# Update version number
# Run build
pyinstaller yarl.spec
# Create archives
# Upload to GitHub releases
```

---

## 🚀 **Quick Start Guide**

### **Minimal Viable Distribution (2-4 hours)**

For playtesting, you can skip the fancy stuff and just do:

1. **Install PyInstaller** (5 min)
2. **Create basic .spec file** (30 min)
3. **Build executables** (15 min)
4. **Test on clean VM** (1-2 hours)
5. **Create ZIP archives** (15 min)
6. **Write simple README** (30 min)
7. **Upload to GitHub releases** (15 min)

**README for playtesters:**
```markdown
# Yarl Playtest Build

## Windows
1. Download Yarl_Windows.zip
2. Extract to folder
3. Run Yarl.exe
4. If Windows Defender blocks it:
   - Click "More info" → "Run anyway"
   - Or: Add exception in Windows Security

## macOS
1. Download Yarl_macOS.zip
2. Extract Yarl.app
3. Right-click Yarl.app → Open (first time only)
4. Click "Open" on the security warning
5. Subsequent launches: double-click normally

## Controls
- Arrow keys: Move
- i: Inventory
- g: Get item
- ... etc
```

---

## 🎯 **Recommended Approach**

### **For Your First Playtest Build:**

**Phase 1: Minimal Distribution** (4-6 hours)
- ✅ Basic PyInstaller setup
- ✅ ZIP archives for both platforms
- ✅ Simple README with workarounds
- ✅ Ad-hoc signing for macOS
- ✅ Test on clean machines

**Results:** Functional but not polished. Good enough for trusted playtesters.

### **For Public Release (Future):**

**Phase 2: Professional Distribution** (+8-12 hours)
- ✅ Apple Developer signing ($99/year)
- ✅ Code signing certificate for Windows ($50-300/year)
- ✅ DMG installer for macOS
- ✅ NSIS installer for Windows
- ✅ Automated build scripts
- ✅ CI/CD for releases (GitHub Actions)

**Results:** Professional, no warnings, easy installation.

---

## 🤖 **Automation (Future Enhancement)**

### **GitHub Actions CI/CD** (2-4 hours setup)

Create `.github/workflows/release.yml`:
```yaml
name: Build Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: pip install pyinstaller
      - run: pyinstaller yarl.spec
      - uses: actions/upload-artifact@v3
        with:
          name: Yarl-Windows
          path: dist/Yarl.exe

  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: pip install pyinstaller
      - run: pyinstaller yarl.spec
      - run: codesign --force --deep --sign - dist/Yarl.app
      - uses: actions/upload-artifact@v3
        with:
          name: Yarl-macOS
          path: dist/Yarl.app
```

**Benefits:**
- Automatic builds on version tag
- Consistent build environment
- Both platforms built simultaneously
- Artifacts ready for release

---

## 📊 **Comparison: Distribution Methods**

| Method | Setup Time | User Experience | File Size | Cost |
|--------|-----------|-----------------|-----------|------|
| **Source + Python** | 0 hours | Poor (install Python) | ~1MB | Free |
| **PyInstaller Basic** | 4-6 hours | Good (some warnings) | 70-100MB | Free |
| **PyInstaller + Signing** | 8-12 hours | Excellent (no warnings) | 70-100MB | $100-400/year |
| **Installers (DMG/NSIS)** | 12-16 hours | Professional | 70-100MB | $100-400/year |
| **CI/CD Automated** | 16-20 hours | Professional + Fast | 70-100MB | $100-400/year |

---

## 🎯 **Recommendation**

### **For Your First Playtesting Round:**

**Go with "PyInstaller Basic" (~4-6 hours)**

**Why:**
- Quick to set up
- Good enough for trusted playtesters
- Learn the process without heavy investment
- Can upgrade to signed versions later
- Free (no signing certificates needed)

**Action Items:**
1. Finish your desired features first
2. Set aside half a day for PyInstaller setup
3. Test on friend's clean machine
4. Create GitHub release with zips
5. Send to playtesters with clear instructions
6. Gather feedback
7. If feedback is good → invest in signing

### **Sample Timeline:**

**Week 1-2:** Finish features (camera system ✅, ranged weapons ✅, etc.)
**Week 3:** Set up PyInstaller, create first builds
**Week 4:** Playtesting round 1
**Week 5-6:** Fixes based on feedback
**Week 7:** Second playtest with signed builds (if positive feedback)

---

## 📝 **Next Steps**

When you're ready to start distribution:

1. **Create requirements.txt** (if not already)
   ```bash
   pip freeze > requirements.txt
   ```

2. **Add game icon** (optional but nice)
   - Create 256x256 PNG icon
   - Convert to .ico (Windows) and .icns (macOS)
   - Tools: ImageMagick, online converters

3. **Test current game thoroughly**
   - Make sure everything works via `python engine.py`
   - Fix any hardcoded paths
   - Ensure all YAML configs load dynamically

4. **Set up PyInstaller**
   - Follow Phase 1 above
   - Test, test, test!

5. **Create GitHub release**
   - Tag version (e.g., v0.1.0-playtest)
   - Upload builds
   - Add release notes

---

## 🔗 **Useful Resources**

- **PyInstaller Docs:** https://pyinstaller.org/en/stable/
- **PyInstaller + tcod:** https://python-tcod.readthedocs.io/en/latest/distribution.html
- **macOS Code Signing:** https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution
- **GitHub Actions for Game Dev:** https://github.com/abarichello/godot-ci (similar concepts)

---

**TL;DR:** Budget 4-6 hours for first-time setup with PyInstaller. After that, creating builds takes ~30 minutes. For playtesting, basic builds are fine. For public release, invest in code signing (~$100-400/year + 4 hours setup).

