"""
Build Script for Compiling Standalone NinjaOne Dashboard Executable.

Uses PyInstaller to bundle the application into a single portable directory / executable
with all assets, config, and dependencies included.

Usage:
    python scripts/build_exe.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def build():
    root = Path(__file__).resolve().parent.parent
    dist_dir = root / "dist"
    build_dir = root / "build"

    print("=" * 60)
    print("📦 Building Standalone NinjaOne Dashboard Executable")
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
        "--name=NinjaOne-Compliance-Dashboard",
        "--onedir",  # onedir launches faster than onefile
        "--clean",
        f"--add-data={root / 'config.yaml'}{os.pathsep}.",
        f"--add-data={root / '.env.example'}{os.pathsep}.",
        "--hidden-import=dash",
        "--hidden-import=dash_bootstrap_components",
        "--hidden-import=plotly",
        "--hidden-import=pydantic",
        "--hidden-import=pandas",
        "--hidden-import=numpy",
        "--hidden-import=requests_oauthlib",
        "--hidden-import=tenacity",
        "--hidden-import=yaml",
        "--hidden-import=cachetools",
        "--hidden-import=flask",
        "--noconfirm",
        str(root / "launcher.py"),
    ]

    print("\nRunning PyInstaller command...")
    subprocess.check_call(pyinstaller_args, cwd=str(root))

    out_folder = dist_dir / "NinjaOne-Compliance-Dashboard"
    if (root / ".env.example").exists() and not (out_folder / ".env").exists():
        shutil.copy(root / ".env.example", out_folder / ".env")

    print("\n" + "=" * 60)
    print("✅ Build Completed Successfully!")
    print(f"Executable folder: {out_folder}")
    print(f"Main Executable: {out_folder / 'NinjaOne-Compliance-Dashboard.exe'}")
    print("=" * 60)


if __name__ == "__main__":
    build()
