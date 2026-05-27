# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all CustomTkinter assets (themes, images, etc.)
ctk_datas = collect_data_files('customtkinter')

a = Analysis(
    ['gui.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('fonts',    'fonts'),
        ('assets',   'assets'),
        ('rarities', 'rarities'),
        ('cache',    'cache'),
        ('icons',    'icons'),
        ('merged',   'merged'),
        ('json',     'json'),          # ← was 'settings.json' and 'shop_history.json' separately
        *ctk_datas,
    ],
    hiddenimports=[
        'PIL._tkinter_finder',
        'PIL.ImageTk',
        'tweepy',
        'colorama',
        'requests',
        'customtkinter',
        'ALmodules.shop',
        'ALmodules.stats_gen',
        'ALmodules.image_gen',
        'ALmodules.merger',
        'ALmodules.setup',
        'ALmodules.monitors',
        'ALmodules.compressor',
        'ALmodules.twitter_client',
        'ALmodules.loot_sim',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['bot', 'publish_to_github'],
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
    name='FNLeak',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,   # no terminal window
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FNLeak',
)

app = BUNDLE(
    coll,
    name='FNLeak.app',
    icon='assets/FNLeak.icns',
    bundle_identifier='com.fnleak.app',
    info_plist={
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.13.0',
        'CFBundleShortVersionString': '1.2.0',
        'NSRequiresAquaSystemAppearance': False,  # allow dark mode
    },
)
