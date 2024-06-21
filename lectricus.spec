"""
PyInstaller Configuration File - CLI
"""

import platform

from PyInstaller.building.api        import PYZ, EXE
from PyInstaller.building.build_main import Analysis


FILENAME:   str = "lectricus"
RUNNING_OS: str = platform.system()

if RUNNING_OS == "Windows":
    FILENAME += ".exe"


a = Analysis(["lectricus.py"],
    pathex=[],
    binaries=[],
    datas=[("lectricus", ".")],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=FILENAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    target_arch="universal2",
    icon=f".resources/icons/AppIcon.{'ico' if RUNNING_OS == 'Windows' else 'icns'}",
    entitlements_file=".resources/signing/entitlements.plist",
    console=True)