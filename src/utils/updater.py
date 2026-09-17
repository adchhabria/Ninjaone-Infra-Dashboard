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
import threading
import time
import urllib.request
from typing import Callable, Optional
from packaging import version

CURRENT_VERSION = "1.0.13"
GITHUB_REPO = "adchhabria/Ninjaone-Infra-Dashboard"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
GITHUB_RAW_VERSION_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/version.json"

# Thread-safe global update state
_UPDATE_STATE = {
    "status": "idle",  # "idle" | "downloading" | "restarting" | "failed" | "completed"
    "progress": 0,  # 0 to 100
    "downloaded_mb": 0.0,
    "total_mb": 0.0,
    "error": None,
    "message": "",
}
_UPDATE_LOCK = threading.Lock()


def get_update_state() -> dict:
    """Return a thread-safe snapshot of the current update state."""
    with _UPDATE_LOCK:
        return dict(_UPDATE_STATE)


def reset_update_state() -> None:
    """Reset the update state back to idle."""
    with _UPDATE_LOCK:
        _UPDATE_STATE["status"] = "idle"
        _UPDATE_STATE["progress"] = 0
        _UPDATE_STATE["downloaded_mb"] = 0.0
        _UPDATE_STATE["total_mb"] = 0.0
        _UPDATE_STATE["error"] = None
        _UPDATE_STATE["message"] = ""


def _set_update_state(
    status: Optional[str] = None,
    progress: Optional[int] = None,
    downloaded_mb: Optional[float] = None,
    total_mb: Optional[float] = None,
    error: Optional[str] = None,
    message: Optional[str] = None,
) -> None:
    """Update internal state under mutex lock."""
    with _UPDATE_LOCK:
        if status is not None:
            _UPDATE_STATE["status"] = status
        if progress is not None:
            _UPDATE_STATE["progress"] = progress
        if downloaded_mb is not None:
            _UPDATE_STATE["downloaded_mb"] = downloaded_mb
        if total_mb is not None:
            _UPDATE_STATE["total_mb"] = total_mb
        if error is not None:
            _UPDATE_STATE["error"] = error
        if message is not None:
            _UPDATE_STATE["message"] = message


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
    with urllib.request.urlopen(req, timeout=300) as response, open(target_path, "wb") as out_file:
        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0
        block_size = 262144  # 256 KB chunk

        while True:
            buffer = response.read(block_size)
            if not buffer:
                break
            downloaded += len(buffer)
            out_file.write(buffer)
            if progress_callback and total_size > 0:
                progress_callback(downloaded, total_size)
    return True


def start_auto_update(download_url: str) -> tuple[bool, str]:
    """
    Launch asynchronous background update download and self-restart.
    Does not block the caller or UI thread.
    """
    if not download_url:
        return False, "No download URL provided."

    with _UPDATE_LOCK:
        if _UPDATE_STATE["status"] in ("downloading", "restarting"):
            return True, "Update already in progress."
        _UPDATE_STATE["status"] = "downloading"
        _UPDATE_STATE["progress"] = 2
        _UPDATE_STATE["downloaded_mb"] = 0.0
        _UPDATE_STATE["total_mb"] = 0.0
        _UPDATE_STATE["error"] = None
        _UPDATE_STATE["message"] = "Initializing update download..."

    t = threading.Thread(target=_run_update_download, args=(download_url,), daemon=True)
    t.start()
    return True, "Update download started in background."


def apply_update_and_restart(download_url: str) -> tuple[bool, str]:
    """Compatibility wrapper that initiates asynchronous auto-update."""
    return start_auto_update(download_url)


def _run_update_download(download_url: str) -> None:
    """Background worker that downloads the asset, writes batch launcher, and restarts."""
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

        target_dir = os.path.dirname(current_target)

        # 1. Download payload with progress tracking
        headers = {"User-Agent": "NinjaOne-Dashboard-Updater"}
        req = urllib.request.Request(download_url, headers=headers)
        with urllib.request.urlopen(req, timeout=300) as response, open(downloaded_file, "wb") as out_file:
            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0
            block_size = 262144  # 256 KB chunk
            tot_mb = round(total_size / (1024 * 1024), 1) if total_size > 0 else 0.0

            while True:
                buffer = response.read(block_size)
                if not buffer:
                    break
                downloaded += len(buffer)
                out_file.write(buffer)

                dl_mb = round(downloaded / (1024 * 1024), 1)
                pct = int((downloaded / total_size) * 100) if total_size > 0 else 50
                _set_update_state(
                    status="downloading",
                    progress=min(pct, 99),
                    downloaded_mb=dl_mb,
                    total_mb=tot_mb,
                    message=f"Downloading: {dl_mb:.1f} MB / {tot_mb:.1f} MB ({pct}%)",
                )

        _set_update_state(
            status="restarting",
            progress=100,
            downloaded_mb=tot_mb,
            total_mb=tot_mb,
            message="Download complete! Synchronizing files and restarting...",
        )

        # 2. Write self-updating Windows batch script
        batch_path = os.path.join(temp_dir, "ninjaone_updater.bat")
        current_pid = os.getpid()

        # Batch script: Wait for application to exit, move old binary to .old (Windows lock workaround),
        # copy new payload, sync git repository, relaunch, and clean up.
        batch_content = f"""@echo off
timeout /t 2 /nobreak > nul
if exist "{current_target}.old" del /F /Q "{current_target}.old" > nul 2>&1
if exist "{current_target}" move /Y "{current_target}" "{current_target}.old" > nul 2>&1
copy /Y "{downloaded_file}" "{current_target}" > nul 2>&1
cd /d "{target_dir}"
if exist ".git" (
    git pull origin main > nul 2>&1
)
start "" "{current_target}"
del /F /Q "{downloaded_file}" > nul 2>&1
del /F /Q "{current_target}.old" > nul 2>&1
"""

        with open(batch_path, "w", encoding="utf-8") as f:
            f.write(batch_content)

        # 3. Launch batch updater detached from this process
        creation_flags = 0
        if sys.platform == "win32":
            creation_flags = (
                subprocess.CREATE_NEW_PROCESS_GROUP
                | subprocess.DETACHED_PROCESS
                | getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            )
            subprocess.Popen(
                ["cmd.exe", "/c", batch_path],
                creationflags=creation_flags,
                close_fds=True,
                shell=False,
            )
        else:
            subprocess.Popen(["bash", batch_path], close_fds=True)

        # 4. Wait 2 seconds so Dash can send the 'restarting' state to the UI, then cleanly exit
        time.sleep(2.0)
        os._exit(0)

    except Exception as e:
        _set_update_state(
            status="failed",
            error=str(e),
            message=f"Update failed: {str(e)}",
        )
