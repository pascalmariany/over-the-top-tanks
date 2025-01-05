# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['Over The Top Tanks.py'],
    pathex=[],
    binaries=[],
    datas=[('gfx', 'gfx'), ('sounds', 'sounds'), ('music', 'music')],
    hiddenimports=[],
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
    name='Over The Top Tanks',
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
    icon=['D:\\OneDrive - Stichting Hogeschool Utrecht\\2024 - 2025\\HBO Open-ICT\\Gilde Game Development\\Game Jams\\Over The Top\\gfx\\tanks.ico'],
)
