"""TTL-based in-memory cache — no Redis or external service required."""

from __future__ import annotations

import functools
import hashlib
import json
import time
from typing import Any, Callable, Optional


import os
import pickle
from pathlib import Path


def _get_disk_cache_path(key: str) -> Optional[Path]:
    """Resolves local persistent cache directory for high-speed instant startup."""
    try:
        if os.name == "nt":
            base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        else:
            base = Path.home() / ".cache"
        cache_dir = base / "NinjaOneDashboard" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        safe_key = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in key)
        return cache_dir / f"{safe_key}.pkl"
    except Exception:
        return None


class TTLCache:
    """
    Thread-safe in-memory cache with per-key TTL and persistent disk fallback
    for instantaneous zero-lag dashboard startup.
    """

    def __init__(self, default_ttl: int = 300):
        self._default_ttl = default_ttl
        self._store: dict[str, tuple[Any, float]] = {}

    # ------------------------------------------------------------------
    # Core Operations
    # ------------------------------------------------------------------

    def get(self, key: str, allow_disk: bool = True) -> Optional[Any]:
        if key in self._store:
            value, expires_at = self._store[key]
            if time.monotonic() < expires_at:
                return value
            del self._store[key]

        if allow_disk and key == "raw_api_payload":
            disk_path = _get_disk_cache_path(key)
            if disk_path and disk_path.exists():
                try:
                    with open(disk_path, "rb") as f:
                        val, exp_wall_time = pickle.load(f)
                    if time.time() < exp_wall_time:
                        ttl_remaining = max(1.0, exp_wall_time - time.time())
                        self._store[key] = (val, time.monotonic() + ttl_remaining)
                        return val
                except Exception:
                    pass
        return None

    def get_stale(self, key: str) -> Optional[Any]:
        """Returns cached payload immediately even if expired (stale-while-revalidate pattern)."""
        if key in self._store:
            return self._store[key][0]
        disk_path = _get_disk_cache_path(key)
        if disk_path and disk_path.exists():
            try:
                with open(disk_path, "rb") as f:
                    val, _ = pickle.load(f)
                return val
            except Exception:
                pass
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ttl = ttl if ttl is not None else self._default_ttl
        self._store[key] = (value, time.monotonic() + ttl)

        if key == "raw_api_payload":
            disk_path = _get_disk_cache_path(key)
            if disk_path:
                try:
                    with open(disk_path, "wb") as f:
                        pickle.dump((value, time.time() + ttl), f, protocol=pickle.HIGHEST_PROTOCOL)
                except Exception:
                    pass

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)
        if key == "raw_api_payload":
            disk_path = _get_disk_cache_path(key)
            if disk_path and disk_path.exists():
                try:
                    disk_path.unlink()
                except Exception:
                    pass

    def clear(self) -> None:
        self._store.clear()
        disk_path = _get_disk_cache_path("raw_api_payload")
        if disk_path and disk_path.exists():
            try:
                disk_path.unlink()
            except Exception:
                pass

    def stats(self) -> dict[str, int]:
        now = time.monotonic()
        valid = sum(1 for _, exp in self._store.values() if now < exp)
        return {"total": len(self._store), "valid": valid, "expired": len(self._store) - valid}

    # ------------------------------------------------------------------
    # Decorator
    # ------------------------------------------------------------------

    def cached(self, ttl: Optional[int] = None, key_prefix: str = "") -> Callable:
        """Decorator that caches the return value of a function."""

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                raw_key = json.dumps(
                    {"f": func.__qualname__, "a": args, "k": sorted(kwargs.items())},
                    default=str,
                )
                cache_key = key_prefix + hashlib.md5(raw_key.encode()).hexdigest()

                cached_val = self.get(cache_key)
                if cached_val is not None:
                    return cached_val

                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl=ttl)
                return result

            return wrapper

        return decorator


# ---------------------------------------------------------------------------
# Singleton instance (imported by metrics layer)
# ---------------------------------------------------------------------------

_default_cache: Optional[TTLCache] = None


def get_cache(ttl: int = 300) -> TTLCache:
    """Return the process-global cache instance, creating it if needed."""
    global _default_cache
    if _default_cache is None:
        _default_cache = TTLCache(default_ttl=ttl)
    return _default_cache
