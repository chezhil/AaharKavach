"""Disk cache for anything that costs money or rate limit to fetch.

Three callers, three reasons:

* **Open Food Facts** rate-limits, and did so mid-testing.
* **Textract** is billed per page, and the same demo label gets scanned
  repeatedly during a rehearsal.
* **Bedrock** is billed per token, and re-asking the model about a product
  whose ingredients have not changed buys nothing.

Deterministic reasoning is *not* cached — it is already instant and free.

Entries live in ``.cache/`` at the repo root (gitignored) and survive a
restart, so a rehearsed demo makes no network calls at all after the first
run. Clear it with ``rm -rf .cache`` or ``AAHAR_CACHE=off``.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)

# parents: [0] shared, [1] src, [2] backend, [3] repo root — the docstring
# promises the repo root, and [2] put it under backend/ where `rm -rf .cache`
# from the root silently missed it.
CACHE_DIR = Path(
    os.environ.get("AAHAR_CACHE_DIR", Path(__file__).resolve().parents[3] / ".cache")
)
DEFAULT_TTL = 7 * 24 * 3600  # a week; product records barely move

_lock = threading.Lock()


def enabled() -> bool:
    """Off by default.

    Caching hides which path actually answered, and a real run should exercise
    the real provider chain. Turn it on (AAHAR_CACHE=on) for repeated testing,
    where re-billing Textract and Bedrock for identical inputs buys nothing.
    """
    return os.environ.get("AAHAR_CACHE", "off").strip().lower() in ("on", "1", "true")


def key_for(*parts: Any) -> str:
    """Stable key from anything JSON-serialisable."""
    blob = json.dumps(parts, sort_keys=True, default=str).encode()
    return hashlib.sha256(blob).hexdigest()[:32]


def _path(namespace: str, key: str) -> Path:
    return CACHE_DIR / namespace / f"{key}.json"


def get(namespace: str, key: str, ttl: int | None = DEFAULT_TTL) -> Any | None:
    """Fetch a stored value. ``ttl=None`` never expires; ``ttl=0`` always does."""
    if not enabled():
        return None
    path = _path(namespace, key)
    try:
        if not path.is_file():
            return None
        payload = json.loads(path.read_text())
    except (OSError, ValueError):
        return None
    # `if ttl` treated 0 as "no expiry", the opposite of what it reads like.
    if ttl is not None and time.time() - payload.get("stored_at", 0) > ttl:
        return None
    return payload.get("value")


def put(namespace: str, key: str, value: Any) -> None:
    if not enabled():
        return
    path = _path(namespace, key)
    try:
        with _lock:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps({"stored_at": time.time(), "value": value}, default=str)
            )
    except (OSError, TypeError) as exc:
        # A cache that cannot write is a slow cache, not a broken app.
        logger.debug("Could not cache %s/%s: %s", namespace, key, exc)


def memoise(
    namespace: str, key: str, produce: Callable[[], Any], ttl: int | None = DEFAULT_TTL
) -> Any:
    """Return the cached value, or produce and store it."""
    hit = get(namespace, key, ttl)
    if hit is not None:
        logger.info("cache hit %s/%s", namespace, key[:8])
        return hit
    value = produce()
    if value is not None:
        put(namespace, key, value)
    return value


def stats() -> dict[str, int]:
    if not CACHE_DIR.is_dir():
        return {}
    return {
        d.name: len(list(d.glob("*.json")))
        for d in sorted(CACHE_DIR.iterdir())
        if d.is_dir()
    }
