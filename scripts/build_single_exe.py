"""
Build Script for Compiling a Single Standalone Executable (.exe) for NinjaOne Infra Dashboard.

Compiles the entire application and all dependencies into a single, self-contained
.exe file and copies it directly into the project root folder.

Usage:
    python scripts/build_single_exe.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def build_single_exe():
    root = Path(__file__).resolve().parent.parent
    dist_dir = root / "dist"
    build_dir = root / "build"

    print("=" * 60)
    print("[*] Compiling Single-File Standalone NinjaOne Dashboard Executable")
    print("=" * 60)
    print(f"Project root: {root}")

    # Check PyInstaller
    try:
        import PyInstaller
    except ImportError:
        print("[!] Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    pyinstaller_args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=Ninjaone-Infra-Dashboard",
        "--onefile",  # Single standalone .exe file
        "--noconsole",  # Run silently without CMD window in background
        "--clean",
        f"--add-data={root / 'config.yaml'}{os.pathsep}.",
        f"--add-data={root / '.env.example'}{os.pathsep}.",
        f"--add-data={root / 'src'}{os.pathsep}src",
        f"--add-data={root / 'scripts'}{os.pathsep}scripts",
        "--collect-all=dash",
        "--collect-all=dash_bootstrap_components",
        "--collect-all=openpyxl",
        "--collect-all=plotly",
        "--collect-all=reportlab",
        "--collect-all=kaleido",
        "--hidden-import=dash",
        "--hidden-import=dash_bootstrap_components",
        "--hidden-import=plotly",
        "--hidden-import=reportlab",
        "--hidden-import=kaleido",
        "--hidden-import=pydantic",
        "--hidden-import=pandas",
        "--hidden-import=numpy",
        "--hidden-import=requests_oauthlib",
        "--hidden-import=tenacity",
        "--hidden-import=yaml",
        "--hidden-import=cachetools",
        "--hidden-import=flask",
        "--hidden-import=openpyxl",
        "--noconfirm",
        str(root / "launcher.py"),
    ]

    print("\nRunning PyInstaller command (this may take 1-2 minutes)...")
    subprocess.check_call(pyinstaller_args, cwd=str(root))

    # The generated single .exe is located in dist/Ninjaone-Infra-Dashboard.exe
    generated_exe = dist_dir / "Ninjaone-Infra-Dashboard.exe"
    target_root_exe = root / "Ninjaone-Infra-Dashboard.exe"

    if generated_exe.exists():
        print(f"\n[*] Copying standalone executable to project root: {target_root_exe}")
        shutil.copy2(generated_exe, target_root_exe)

    if (root / ".env.example").exists() and not (root / ".env").exists():
        shutil.copy2(root / ".env.example", root / ".env")

    print("\n" + "=" * 60)
    print("[+] SUCCESS: Standalone Single Executable Ready!")
    print(f"Direct Executable in Root: {target_root_exe}")
    print(f"File Size: {round(os.path.getsize(target_root_exe) / (1024 * 1024), 2)} MB")
    print("=" * 60)


if __name__ == "__main__":
    build_single_exe()
