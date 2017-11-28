# -*- mode: python -*-

block_cipher = None

a = Analysis(
    ['il2fb/ds/airbridge/main.py'],
    pathex=['.', ],
    binaries=[],
    datas=[],
    hiddenimports=[
        'il2fb.ds.airbridge.streaming.subscribers.file',
        'il2fb.ds.airbridge.streaming.subscribers.nats',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='airbridge',
    debug=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=True , icon='assets/control-tower.ico',
)
