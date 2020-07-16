# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(
    ['citrine_ui\\__main__.py'],
    pathex=['C:\\Users\\build\\citrine\\citrine-ui'],
    binaries=[],
    datas=[
        ('citrine_ui/res', 'citrine_ui/res'),
        ('citrine_ui/js_bridge/client.js', 'citrine_ui/js_bridge/'),
    ],
    hiddenimports=[
        'pkg_resources.py2_warn',
        'citrine_client',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='citrine-ui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='citrine-ui',
)
