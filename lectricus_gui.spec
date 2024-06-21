"""
PyInstaller Configuration File - CLI
"""

import os
import sys
import time
import platform
import subprocess

from PyInstaller.building.api        import PYZ, EXE, COLLECT
from PyInstaller.building.osx        import BUNDLE
from PyInstaller.building.build_main import Analysis

sys.path.append(os.path.abspath(os.getcwd()))

from lectricus import __version__


FILENAME:   str = "Lectricus (GUI)"
RUNNING_OS: str = platform.system()

if RUNNING_OS == "Windows":
    FILENAME += ".exe"


a = Analysis(
    ['lectricus_gui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
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
    [],
    exclude_binaries=True,
    name='lectricus_gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch="universal2",
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='lectricus_gui',
)
app = BUNDLE(
    coll,
    name='Lectricus (GUI).app',
    icon=".resources/icons/AppIcon.icns",
    entitlements_file=".resources/signing/entitlements.plist",
    bundle_identifier="com.ripeda.lectricus-gui",
    info_plist={
        "CFBundleName": "Lectricus (GUI)",
        "CFBundleShortVersionString": __version__,
        "CFBundleVersion": __version__,
        "CFBundleExecutable": "lectricus_gui",
        "NSRequiresAquaSystemAppearance": False,
        "NSHighResolutionCapable": True,
        "Build Date": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "BuildMachineOSBuild": subprocess.run(["/usr/bin/sw_vers", "-buildVersion"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.decode().strip(),
    },
)