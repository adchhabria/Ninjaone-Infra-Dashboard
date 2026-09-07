"""
Automatic Software Update Engine for NinjaOne Infra Dashboard.

Queries GitHub Releases API, checks for newer versions, downloads the latest
standalone executable or release bundle, and executes a detached self-updating
batch launcher on Windows to replace the running binary and relaunch.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
from typing import Callable, Optional
from packaging import version

CURRENT_VERSION = "1.0.11"
GITHUB_REPO = "adchhabria/Ninjaone-Infra-Dashboard"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
GITHUB_RAW_VERSION_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/version.json"


def normalize_version(v_str: str) -> str:
    """Strip 'v' prefix and whitespace from version string."""
    if not v_str:
        return "0.0.0"
    v = v_str.strip().lstrip("v").lstrip("V")
    # Clean any suffixes like -alpha, -beta, etc. if needed
    match = re.match(r"^(\d+\.\d+(\.\d+)?)", v)
    return match.group(1) if match else v


def is_newer_version(latest_str: str, current_str: str = CURRENT_VERSION) -> bool:
    """Return True if latest_str is strictly newer than current_str."""
    try:
        v_latest = version.parse(normalize_version(latest_str))
        v_current = version.parse(normalize_version(current_str))
        return v_latest > v_current
    except Exception:
        return False


def check_for_updates() -> dict:
    """
    Check GitHub Releases for newer version of the toolkit.

    Returns dict with keys:
        - success: bool
        - update_available: bool
        - current_version: str
        - latest_version: str
        - release_name: str
        - release_notes: str
        - published_at: str
        - download_url: str
        - html_url: str
        - message: str
    """
    current_v = f"v{CURRENT_VERSION}"
    headers = {
        "User-Agent": "NinjaOne-Dashboard-Updater",
        "Accept": "application/vnd.github.v3+json",
    }

    req = urllib.request.Request(GITHUB_API_URL, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                tag_name = data.get("tag_name", "")
                latest_v = tag_name if tag_name.startswith("v") else f"v{tag_name}"
                body = data.get("body", "No release notes provided.")
                name = data.get("name") or f"Release {latest_v}"
                published = data.get("published_at", "")[:10]
                html_url = data.get("html_url", f"https://github.com/{GITHUB_REPO}/releases")

                # Find .exe asset if available, else zipball
                download_url = ""
                for asset in data.get("assets", []):
                    if asset.get("name", "").lower().endswith(".exe"):
                        download_url = asset.get("browser_download_url", "")
                        break
                if not download_url:
                    download_url = data.get("zipball_url", html_url)

                newer = is_newer_version(latest_v, CURRENT_VERSION)

                return {
                    "success": True,
                    "update_available": newer,
                    "current_version": current_v,
                    "latest_version": latest_v,
                    "release_name": name,
                    "release_notes": body,
                    "published_at": published,
                    "download_url": download_url,
                    "html_url": html_url,
                    "message": "Update available!" if newer else "You are running the latest version.",
                }
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # No releases published yet on GitHub repo
            return {
                "success": True,
                "update_available": False,
                "current_version": current_v,
                "latest_version": current_v,
                "release_name": "Latest Build",
                "release_notes": "All features and security definitions are up-to-date.",
                "published_at": time.strftime("%Y-%m-%d"),
                "download_url": "",
                "html_url": f"https://github.com/{GITHUB_REPO}",
                "message": "You are running the latest version.",
            }
        return {
            "success": False,
            "update_available": False,
            "current_version": current_v,
            "latest_version": "Unknown",
            "release_name": "",
            "release_notes": "",
            "published_at": "",
            "download_url": "",
            "html_url": "",
            "message": f"GitHub API error (HTTP {e.code})",
        }
    except Exception as e:
        return {
            "success": False,
            "update_available": False,
            "current_version": current_v,
            "latest_version": "Unknown",
            "release_name": "",
            "release_notes": "",
            "published_at": "",
            "download_url": "",
            "html_url": "",
            "message": f"Could not check for updates: {str(e)}",
        }


def download_file(url: str, target_path: str, progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
    """Download a remote file with progress tracking."""
    headers = {"User-Agent": "NinjaOne-Dashboard-Updater"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as response, open(target_path, "wb") as out_file:
        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0
        block_size = 65536

        while True:
            buffer = response.read(block_size)
            if not buffer:
                break
            downloaded += len(buffer)
            out_file.write(buffer)
            if progress_callback and total_size > 0:
                progress_callback(downloaded, total_size)
    return True


def apply_update_and_restart(download_url: str) -> tuple[bool, str]:
    """
    Download the update and execute detached Windows batch script to replace
    the running executable/program and restart the dashboard.
    """
    if not download_url:
        return False, "No download URL provided for update."

    try:
        temp_dir = tempfile.gettempdir()
        downloaded_file = os.path.join(temp_dir, "Ninjaone_Update_Payload.exe")

        # Determine current running binary location
        if getattr(sys, "frozen", False):
            current_target = os.path.abspath(sys.executable)
        else:
            # Running from source, target the project root exe
            current_target = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "Ninjaone-Infra-Dashboard.exe")
            )

        # 1. Download payload
        download_file(download_url, downloaded_file)

        # 2. Write self-updating Windows batch script
        batch_path = os.path.join(temp_dir, "ninjaone_updater.bat")
        current_pid = os.getpid()

        target_dir = os.path.dirname(current_target)

        # Batch script: Wait for current process to exit, copy new file over old file, sync git repo, launch new file, clean up
        batch_content = f"""@echo off
chcp 65001 > nul
echo ========================================================
echo   NinjaOne Infra Dashboard - Auto Updater
echo ========================================================
echo Waiting for application (PID: {current_pid}) to close...

:: Wait up to 5 seconds for current process to exit
timeout /t 2 /nobreak > nul

:: Overwrite target executable
echo Installing new version...
copy /Y "{downloaded_file}" "{current_target}" > nul

if %ERRORLEVEL% NEQ 0 (
    echo Update failed to overwrite file. Retrying in 2 seconds...
    timeout /t 2 /nobreak > nul
    copy /Y "{downloaded_file}" "{current_target}" > nul
)

:: Sync local repository files if running in git folder
cd /d "{target_dir}"
if exist ".git" (
    echo Syncing local files from GitHub...
    git pull origin main > nul 2>&1
)

echo Starting updated NinjaOne Dashboard...
start "" "{current_target}"

:: Cleanup temporary downloaded payload
del /F /Q "{downloaded_file}" > nul 2>&1

:: Self-destruct batch script
(goto) 2>nul & del "%~f0"
"""

        with open(batch_path, "w", encoding="utf-8") as f:
            f.write(batch_content)

        # 3. Launch batch updater detached from this process
        if sys.platform == "win32":
            subprocess.Popen(
                ["cmd.exe", "/c", batch_path],
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
                close_fds=True,
                shell=False,
            )
        else:
            subprocess.Popen(["bash", batch_path], close_fds=True)

        return True, "Update applied! Restarting application..."

    except Exception as e:
        return False, f"Failed to apply update: {str(e)}"
