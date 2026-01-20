# Building Catacombs of YARL for Distribution

This guide covers building a distributable version of Catacombs of YARL using PyInstaller.

## Prerequisites

1. **Python 3.9+** with the game's dependencies installed:
   ```bash
   pip install -r requirements.txt
   ```

2. **PyInstaller** (not included in requirements.txt):
   ```bash
   pip install pyinstaller
   ```

## Quick Build

From the repository root:

```bash
# Build for your current platform
pyinstaller build/pyinstaller/CatacombsOfYARL.spec
```

The output will be in `dist/CatacombsOfYARL/`.

## Platform-Specific Instructions

### macOS

```bash
# From repo root
pyinstaller build/pyinstaller/CatacombsOfYARL.spec

# Test the build
cd dist
./CatacombsOfYARL/CatacombsOfYARL

# Package for distribution
zip -r CatacombsOfYARL-macOS.zip CatacombsOfYARL/
```

**Note:** The build is not signed/notarized. Users may need to right-click and select "Open" the first time, or adjust Gatekeeper settings.

### Windows

```powershell
# From repo root
pyinstaller build\pyinstaller\CatacombsOfYARL.spec

# Test the build
cd dist
.\CatacombsOfYARL\CatacombsOfYARL.exe

# Package for distribution
Compress-Archive -Path CatacombsOfYARL -DestinationPath CatacombsOfYARL-Windows.zip
```

### Linux

```bash
# From repo root
pyinstaller build/pyinstaller/CatacombsOfYARL.spec

# Test the build
cd dist
./CatacombsOfYARL/CatacombsOfYARL

# Package for distribution
tar -czvf CatacombsOfYARL-Linux.tar.gz CatacombsOfYARL/
```

## What's Included

The build bundles:
- Game executable
- Font: `arial10x10.png`
- Menu background: `menu_background1.png`
- Config files: `config/*.yaml`
- Data files: `data/*.yaml`
- All Python dependencies (tcod, numpy, pyyaml, etc.)

## Runtime File Locations

When the game runs, it writes user data to platform-appropriate locations:

| Platform | User Data Location |
|----------|-------------------|
| **Windows** | `%APPDATA%\CatacombsOfYARL\` |
| **macOS** | `~/Library/Application Support/CatacombsOfYARL/` |
| **Linux** | `~/.local/share/catacombs-of-yarl/` |

Within the user data directory:
- `saves/savegame.json` - Save game file
- `logs/rlike.log` - Main log file
- `logs/rlike_errors.log` - Error log
- `data/hall_of_fame.yaml` - Hall of Fame records

## Legacy Save Migration

If the player has save files from an older version (stored in the game directory), they will be automatically migrated to the user data directory on first launch.

## Testing the Build

After building, test from **outside** the repository:

```bash
# Copy to a different location
cp -r dist/CatacombsOfYARL /tmp/

# Run from there
cd /tmp/CatacombsOfYARL
./CatacombsOfYARL  # or CatacombsOfYARL.exe on Windows

# Verify:
# 1. Game launches and shows main menu
# 2. Font displays correctly
# 3. Menu background image loads
# 4. Start a new game, play a few turns
# 5. Save the game (main menu -> Quit -> Yes to save)
# 6. Check that save appeared in user data directory:
#    - macOS: ls ~/Library/Application\ Support/CatacombsOfYARL/saves/
#    - Linux: ls ~/.local/share/catacombs-of-yarl/saves/
#    - Windows: dir %APPDATA%\CatacombsOfYARL\saves\
```

## Troubleshooting

### "Font file not found"
The font PNG wasn't bundled. Check that `arial10x10.png` exists in the repo root and is listed in the spec file's `datas`.

### "No module named X"
Add the missing module to `hiddenimports` in the spec file.

### Game runs but can't save
Check that the user data directory is writable. The game should create it automatically.

### macOS: "damaged and can't be opened"
The app is not signed. Users should:
1. Right-click the app and select "Open"
2. Click "Open" in the dialog that appears

Or clear the quarantine attribute:
```bash
xattr -cr CatacombsOfYARL
```

## Not Covered (Future Work)

- **Code signing/notarization** (macOS/Windows)
- **Installer creation** (Windows MSI, macOS DMG)
- **--onefile builds** (single executable, slower startup)
- **Auto-update mechanism**
