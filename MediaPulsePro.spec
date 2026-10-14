# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect package data
datas = [
    ('web/static', 'web/static'),
    ('assets', 'assets'),
    ('locales', 'locales'),
]
datas += collect_data_files('yt_dlp')

# Hidden imports for dynamic frameworks
hiddenimports = [
    'clr',
    'pythonnet',
    'webview',
    'webview.platforms.winforms',
    'webview.platforms.edgechromium',
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'fastapi',
    'fastapi.staticfiles',
    'fastapi.middleware.cors',
    'fastapi.responses',
    'starlette',
    'starlette.staticfiles',
    'pydantic',
    'PIL',
    'PIL.Image',
    'PIL.IcoImagePlugin',
    'yt_dlp',
    'bs4',
    'beautifulsoup4',
]

hiddenimports += collect_submodules('uvicorn')
hiddenimports += collect_submodules('starlette')
hiddenimports += collect_submodules('fastapi')
hiddenimports += collect_submodules('webview')

# Explicit exclusions to prune unnecessary heavy libraries
excludes = [
    'pytest',
    '_pytest',
    'unittest',
    'numpy',
    'matplotlib',
    'scipy',
    'pandas',
    'IPython',
    'jedi',
    'zmq',
    'contourpy',
    'fontTools',
    'tornado',
    'jupyter',
    'pygments',
    'notebook',
    'tkinter',
    '_tkinter',
    'tcl',
    'tk',
    'customtkinter',
    'imageio_ffmpeg'
]

a = Analysis(
    ['desktop_app.py'],
    pathex=['.'],
    binaries=[('bin/ffmpeg.exe', 'bin')],
    datas=datas,
    hiddenimports=list(set(hiddenimports)),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Standalone Onedir distribution
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MediaPulsePro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
    version='version_info.txt',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='MediaPulsePro',
)
