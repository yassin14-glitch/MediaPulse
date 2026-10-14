# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect package data
datas = [
    ('web/static', 'web/static'),
    ('assets', 'assets'),
    ('bin/ffmpeg.exe', 'bin'),
]
datas += collect_data_files('customtkinter')
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
    'PIL._tkinter_finder',
    'customtkinter',
    'yt_dlp',
    'imageio_ffmpeg',
    'bs4',
    'beautifulsoup4',
]

hiddenimports += collect_submodules('uvicorn')
hiddenimports += collect_submodules('starlette')
hiddenimports += collect_submodules('fastapi')
hiddenimports += collect_submodules('webview')

a = Analysis(
    ['desktop_app.py'],
    pathex=['.'],
    binaries=[('bin/ffmpeg.exe', 'bin')],
    datas=datas,
    hiddenimports=list(set(hiddenimports)),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest', '_pytest', 'unittest'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Single-file standalone executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MediaPulsePro_Portable',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
    version='version_info.txt',
)
