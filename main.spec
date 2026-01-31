# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

rich_datas, rich_binaries, rich_hiddenimports = collect_all('rich')

a = Analysis(
    ['src/main.py'],
    pathex=['.', 'src'],  # Added 'src' to pathex to locate modules in src/ directory
    binaries=rich_binaries,
    datas=[('schema.sql', '.')] + rich_datas,
    hiddenimports=[
        'trade',
        'load_data',
        'utils',
        'migrate',
        'stocks_reader',
        'planner',
        'settings',
        'filter_trades',
        'menu',
        'calculator',
        'chart',
        'pandas',
        'openpyxl',
        'rich',
    ] + rich_hiddenimports,
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
    name='tradecli',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
