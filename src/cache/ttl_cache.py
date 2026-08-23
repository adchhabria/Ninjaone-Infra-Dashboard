"""TTL-based in-memory cache — no Redis or external service required."""

from __future__ import annotations

import functools
import hashlib
import json
import time
from typing import Any, Callable, Optional


class TTLCache:
    """
    Simple thread-safe in-memory cache with per-key TTL.

    Usage::

        cache = TTLCache(default_ttl=300)

        @cache.cached(ttl=60)
        def expensive_call():
            ...
    """

    def __init__(self, default_ttl: int = 300):
        self._default_ttl = default_ttl
        self._store: dict[str, tuple[Any, float]] = {}

    # ------------------------------------------------------------------
    # Core Operations
    # ------------------------------------------------------------------

    def get(self, key: str) -> Optional[Any]:
        if key in self._store:
            value, expires_at = self._store[key]
            if time.monotonic() < expires_at:
                return value
            del self._store[key]
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ttl = ttl if ttl is not None else self._default_ttl
        self._store[key] = (value, time.monotonic() + ttl)

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()

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
