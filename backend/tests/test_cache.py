"""The cache exists to keep billed calls and rate limits off the demo path."""

import pytest

from shared import cache


@pytest.fixture
def temp_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("AAHAR_CACHE", "on")
    monkeypatch.setattr(cache, "CACHE_DIR", tmp_path)
    return tmp_path


def test_a_value_survives_a_round_trip(temp_cache):
    key = cache.key_for("product", "5000159461122")
    assert cache.get("product", key) is None
    cache.put("product", key, {"name": "Snickers"})
    assert cache.get("product", key) == {"name": "Snickers"}


def test_memoise_calls_the_producer_once(temp_cache):
    calls = []

    def produce():
        calls.append(1)
        return {"blocks": 3}

    key = cache.key_for("ocr", "abc")
    first = cache.memoise("ocr", key, produce)
    second = cache.memoise("ocr", key, produce)

    assert first == second == {"blocks": 3}
    assert len(calls) == 1, "second call should have been served from disk"


def test_keys_distinguish_different_inputs(temp_cache):
    assert cache.key_for("a", 1) != cache.key_for("a", 2)
    assert cache.key_for("a", 1) == cache.key_for("a", 1)


def test_expired_entries_are_ignored(temp_cache):
    key = cache.key_for("x")
    cache.put("x", key, "old")
    assert cache.get("x", key, ttl=0) is None      # ttl=0 → always stale
    assert cache.get("x", key, ttl=3600) == "old"


def test_disabling_the_cache_is_respected(tmp_path, monkeypatch):
    monkeypatch.setenv("AAHAR_CACHE", "off")
    monkeypatch.setattr(cache, "CACHE_DIR", tmp_path)
    key = cache.key_for("y")
    cache.put("y", key, "value")
    assert cache.get("y", key) is None


def test_an_unwritable_cache_does_not_break_the_caller(temp_cache, monkeypatch):
    """A cache that cannot write is a slow app, not a broken one."""
    def explode(*a, **k):
        raise OSError("read-only filesystem")

    monkeypatch.setattr("pathlib.Path.write_text", explode)
    cache.put("z", cache.key_for("z"), {"any": "thing"})  # must not raise
