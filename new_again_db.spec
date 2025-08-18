# -*- mode: python ; coding: utf-8 -*-

import os

# Get the project root directory (current working directory)
project_root = os.getcwd()

# Collect all Python files and modules
datas = [
    # Include all Python modules
    (os.path.join(project_root, 'core'), 'core'),
    (os.path.join(project_root, 'ui'), 'ui'),
    (os.path.join(project_root, 'database'), 'database'),
    (os.path.join(project_root, 'utils'), 'utils'),
    (os.path.join(project_root, 'config'), 'config'),
]

# Add any additional data files if needed
# datas += [(os.path.join(project_root, 'designer'), 'designer')]

a = Analysis(
    ['start.py'],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'core',
        'core.application',
        'core.logger',
        'ui',
        'ui.main_ui',
        'ui.add_plate_dialog',
        'ui.table_view_handler',
        'database',
        'database.database',
        'database.initialize_db',
        'utils',
        'utils.helpers',
        'config',
        'config.constants',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='new_again_db',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)