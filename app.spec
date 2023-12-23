# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('/Users/redstar/Documents/criss/seat-tool/data/readme.html', './data'), ('/Users/redstar/Documents/criss/seat-tool/data/shot-1.png', './data'), ('/Users/redstar/Documents/criss/seat-tool/data/shot-2.png', './data'), ('/Users/redstar/Documents/criss/seat-tool/data/shot-3.png', './data'), ('/Users/redstar/Documents/criss/seat-tool/data/shot-4.png', './data'), ('/Users/redstar/Documents/criss/seat-tool/data/shot-5.png', './data'), ('/Users/redstar/Documents/criss/seat-tool/data/shot-6.png', './data'), ('/Users/redstar/Documents/criss/seat-tool/data/shot-7.png', './data'), ('/Users/redstar/Documents/criss/seat-tool/data/shot-8.png', './data'), ('/Users/redstar/Documents/criss/seat-tool/data/shot-9.png', './data'), ('/Users/redstar/Documents/criss/seat-tool/data/shot-10.png', './data'), ('/Users/redstar/Documents/criss/seat-tool/data/shot-11.png', './data'), ('/Users/redstar/Documents/criss/seat-tool/data/shot-12.png', './data'), ('/Users/redstar/Documents/criss/seat-tool/data/shot-13.png', './data'), ('/Users/redstar/Documents/criss/seat-tool/data/shot-14.png', './data'), ('/Users/redstar/Documents/criss/seat-tool/data/shot-15.png', './data'), ('/Users/redstar/Documents/criss/seat-tool/data/shot-16.png', './data'), ('/Users/redstar/Documents/criss/seat-tool/data/shot-17.png', './data'), ('/Users/redstar/Documents/criss/seat-tool/data/shot-18.png', './data')]
binaries = []
hiddenimports = []
tmp_ret = collect_all('tkinterweb')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='app',
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
app = BUNDLE(
    exe,
    name='app.app',
    icon=None,
    bundle_identifier=None,
)
