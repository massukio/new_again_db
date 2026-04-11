# -*- mode: python ; coding: utf-8 -*-

import os

project_root = os.getcwd()

datas = [
    (os.path.join(project_root, 'core'), 'core'),
    (os.path.join(project_root, 'ui'), 'ui'),
    (os.path.join(project_root, 'database'), 'database'),
    (os.path.join(project_root, 'utils'), 'utils'),
    (os.path.join(project_root, 'config'), 'config'),
    (os.path.join(project_root, 'assets'), 'assets'),
]

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
        'ui.styles',
        'ui.font_size_dialog',
        'ui.wash_record_dialog',
        'ui.earnings_page',
        'ui.customer_dashboard',
        'database',
        'database.database',
        'database.initialize_db',
        'utils',
        'utils.helpers',
        'config',
        'config.constants',
        'config.config_manager',
        'config.brands',
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
