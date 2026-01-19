# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# Determine if running on macOS
block_cipher = None

# Collect icon files
icon_files = [
    ('icons/icon-22.png', 'icons'),
    ('icons/icon-44.png', 'icons'),
    ('icons/icon-128.png', 'icons'),
    ('icons/icon-256.png', 'icons'),
    ('icons/icon-512.png', 'icons'),
]

# Collect data files
datas = icon_files

# Hidden imports required for the application
hiddenimports = [
    'rumps',
    'sounddevice',
    'numpy',
    'PIL',
    'Quartz',
    'Vision',
    'AppKit',
    'Foundation',
    'objc',
]

a = Analysis(
    ['espresso_gui_wrapper.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='espresso-gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity='Apple Development: Simon Lauger (SCUHYFZ5Q3)',
    entitlements_file='entitlements.plist',
    icon='icons/icon-512.png',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='espresso-gui',
)

app = BUNDLE(
    coll,
    name='Espresso.app',
    icon='icons/icon-512.png',
    bundle_identifier='com.simonlauger.espresso',
    info_plist={
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'NSHighResolutionCapable': True,
        'LSUIElement': True,  # Run as menu bar app (no dock icon)
        'NSMicrophoneUsageDescription': 'Espresso needs microphone access to monitor audio for Teams notifications.',
        'NSAppleEventsUsageDescription': 'Espresso needs to control other apps to simulate keyboard activity.',
    },
)
