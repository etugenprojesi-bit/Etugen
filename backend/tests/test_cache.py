import pytest

from app.cache.store import ResponseCache, cache_key, round_coord


@pytest.mark.parametrize("value,expected", [
    (37.612, 37.60), (37.626, 37.65), (-0.249, -0.25), (0.01, 0.0), (-0.01, 0.0), (179.99, 180.0),
])
def test_round_coord(value, expected):
    assert round_coord(value, 0.05) == pytest.approx(expected)
    assert str(round_coord(-0.01, 0.05)) == "0.0"  # no "-0.0" keys


def test_roundtrip(tmp_path):
    cache = ResponseCache(tmp_path / "c.sqlite")
    key = cache_key("power_daily", 37.6, 32.75, start="20010101")
    assert cache.get(key) is None
    cache.put(key, {"a": [1, 2, 3]})
    assert cache.get(key) == {"a": [1, 2, 3]}


def test_key_contains_no_identity():
    key = cache_key("power_daily", 37.6, 32.75, start="20010101", end="20251231")
    assert key == "power_daily:37.6000:32.7500:end=20251231;start=20010101"
