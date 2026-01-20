# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Catacombs of YARL.

This creates a --onedir build: a folder containing the game executable
plus bundled assets, suitable for zipping and distributing.

Usage:
    cd /path/to/rlike
    pyinstaller build/pyinstaller/CatacombsOfYARL.spec

Output:
    dist/CatacombsOfYARL/
        CatacombsOfYARL (or CatacombsOfYARL.exe on Windows)
        arial10x10.png
        menu_background1.png
        config/
        data/
        ...
"""

import sys
from pathlib import Path

# Get the repo root (parent of build/pyinstaller/)
spec_dir = Path(SPECPATH).resolve()
repo_root = spec_dir.parent.parent

block_cipher = None

# Main analysis
a = Analysis(
    [str(repo_root / 'engine.py')],
    pathex=[str(repo_root)],
    binaries=[],
    datas=[
        # Font and images
        (str(repo_root / 'arial10x10.png'), '.'),
        (str(repo_root / 'menu_background1.png'), '.'),
        # Config YAML files
        (str(repo_root / 'config'), 'config'),
        # Data files (entity definitions, etc.)
        (str(repo_root / 'data'), 'data'),
    ],
    hiddenimports=[
        # Ensure all game modules are included
        'tcod',
        'tcod.libtcodpy',
        'yaml',
        'numpy',
        # Our modules
        'utils.resource_paths',
        'components',
        'systems',
        'services',
        'engine',
        'io_layer',
        'rendering',
        'map_objects',
        'loader_functions',
        'state_machine',
        'state_management',
        'spells',
        'events',
        'ui',
        'screens',
        'balance',
        'input',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude dev-only packages
        'pytest',
        'pytest_cov',
        'coverage',
        'matplotlib',
        'matplotlib.pyplot',
        'IPython',
        'jupyter',
        'notebook',
        'sphinx',
        'pylint',
        'flake8',
        'black',
        'mypy',
        # Exclude test modules
        'tests',
        'test_*',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CatacombsOfYARL',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Keep console for error messages; set False for release
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # macOS/Windows icon (optional - create these files if desired)
    # icon=str(repo_root / 'assets' / 'icon.ico'),  # Windows
    # icon=str(repo_root / 'assets' / 'icon.icns'),  # macOS
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CatacombsOfYARL',
)
