"""End-to-end /api/satellite and slope in /api/rotations, offline.

POWER network calls fail (MockTransport) and Earth Engine is disabled by
conftest.py, so both must come from the real responses in demo_cache/.
"""

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import get_settings

DEMO = {"konya": (37.60, 32.75), "punjab": (30.80, 75.60), "nakuru": (-0.25, 36.15)}


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("CACHE_PATH", str(tmp_path / "cache.sqlite"))
    monkeypatch.setenv("LAST_FULL_YEAR", "2025")
    get_settings.cache_clear()

    def offline(request):
        raise httpx.ConnectError("offline (test)", request=request)

    real_client = httpx.AsyncClient
    import app.api.analyze as analyze
    monkeypatch.setattr(analyze.httpx, "AsyncClient",
                        lambda *a, **k: real_client(transport=httpx.MockTransport(offline)))
    from app.main import app
    yield TestClient(app)
    get_settings.cache_clear()


@pytest.mark.parametrize("name", DEMO)
def test_satellite_demo_point(client, name):
    lat, lon = DEMO[name]
    r = client.get("/api/satellite", params={"lat": lat, "lon": lon})
    assert r.status_code == 200, r.text
    b = r.json()
    ee_src = b["data_sources"][1]
    assert ee_src["origin"] == "demo_cache" and ee_src["is_demo_cache"]
    assert all(layer["available"] for layer in ee_src["layers"].values())
    assert b["slope"]["status"] == "ok" and 0 < b["slope"]["slope_deg_median"] < 10
    assert len(b["monthly_climatology"]) == 12
    p = b["precipitation_comparison"]
    assert p["status"] == "ok" and p["common_full_years"] >= 20
    sm = b["soil_moisture"]
    assert sm["status"] == "ok" and sm["merge"]["overlap_days"] > 100
    pt = b["patterns"]
    assert pt["status"] == "ok" and pt["n_years"] >= 20
    assert {"zscore", "kmeans", "isolation_forest", "analogs", "agreement"} <= set(pt)
    assert "not SMAP" in b["labels"]["power_gwetroot_model"]


def test_nakuru_power_trend_not_confirmed(client):
    b = client.get("/api/satellite", params={"lat": -0.25, "lon": 36.15}).json()
    p = b["precipitation_comparison"]
    assert p["trend"]["power"]["significant_5pct"]
    assert p["difference_series"]["homogeneous"] is False
    assert p["power_trend_confirmed_by_imerg"] is False
    assert any("not homogeneous" in n for n in b["patterns"]["notes"])


def test_konya_power_wetter_than_imerg_but_homogeneous(client):
    p = client.get("/api/satellite", params={"lat": 37.60, "lon": 32.75}).json()["precipitation_comparison"]
    assert p["annual_mean_mm"]["power"] > p["annual_mean_mm"]["imerg"]
    assert p["difference_series"]["homogeneous"] is True


def test_rotations_use_slope(client):
    r = client.post("/api/rotations", json={"lat": 37.60, "lon": 32.75})
    b = r.json()
    assert b["slope"]["status"] == "ok"
    for c in b["cards"]:
        ero = c["subscores"]["erosion"]
        assert ero["relative_slope_factor"] == b["slope"]["relative_s"]
        codes = {g["code"] for g in c["data_gaps"]}
        assert "slope_is_area" in codes and "no_slope" not in codes


def test_rotations_without_slope_data(client, monkeypatch):
    from app.sources import gee
    monkeypatch.setattr(gee, "load_slope", lambda *a, **k: (None, "none", "Earth Engine offline (test)"))
    b = client.post("/api/rotations", json={"lat": 37.60, "lon": 32.75}).json()
    assert b["slope"]["status"] == "missing" and "offline" in b["slope"]["error"]
    assert b["data_sources"][1]["errors"]
    ero = b["cards"][0]["subscores"]["erosion"]
    assert ero["relative_slope_factor"] is None
    assert "no_slope" in {g["code"] for g in b["cards"][0]["data_gaps"]}
