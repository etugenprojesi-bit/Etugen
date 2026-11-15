"""End-to-end /api/risk and the stage 5 options of /api/analyze and /api/rotations, offline."""

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
def test_risk_demo_point(client, name):
    lat, lon = DEMO[name]
    r = client.get("/api/risk", params={"lat": lat, "lon": lon})
    assert r.status_code == 200, r.text
    b = r.json()
    assert b["years"][0] == 2001 and b["years"][-1] == 2025
    ids = [lyr["id"] for lyr in b["layers"]]
    assert {"frost_days", "hot_days", "water_balance_mm", "smap_sm", "ndvi"} <= set(ids)
    assert b["missing_layers"] == []
    assert b["data_sources"][-1]["origin"] == "demo_cache"
    for lyr in b["layers"]:
        assert len(lyr["values"]) == len(b["years"]) and all(len(row) == 12 for row in lyr["values"])
    smap = next(lyr for lyr in b["layers"] if lyr["id"] == "smap_sm")
    assert smap["observation"] and not smap["scenario_applies"]
    assert smap["values"][0] == [None] * 12  # SMAP starts in 2015
    assert "generic_heat_threshold" in b["notes"]


def test_risk_crop_thresholds_and_scenario(client):
    lat, lon = DEMO["konya"]
    b = client.get("/api/risk", params={"lat": lat, "lon": lon, "crop": "winter_wheat",
                                        "delta_t": 2, "delta_p": -10, "precip_source": "imerg"}).json()
    lay = {lyr["id"]: lyr for lyr in b["layers"]}
    assert lay["hot_days"]["threshold"]["value"] == 34 and not lay["hot_days"]["assumption"]
    assert lay["lethal_cold_days"]["threshold"]["value"] == pytest.approx(-17.2)
    assert b["variant"]["scenario_active"] and b["variant"]["precip_source"] == "imerg"
    hot = lay["hot_days"]
    assert sum(hot["annual"]) / len(hot["annual"]) > hot["annual_baseline_mean"]
    assert "scenario_applies_to_climate_only" in b["notes"]


def test_risk_unknown_crop(client):
    r = client.get("/api/risk", params={"lat": 37.6, "lon": 32.75, "crop": "nope"})
    assert r.status_code == 422


def test_analyze_chirps_and_rain_check(client):
    lat, lon = DEMO["konya"]
    p = client.get("/api/analyze", params={"lat": lat, "lon": lon}).json()
    rc = p["climate"]["rain_check"]
    # Konya: POWER ~1.8 x CHIRPS -> flagged (plan_konya_yagis.md)
    assert rc["status"] == "ok" and rc["ratio"] > 1.3 and rc["power_may_be_too_wet"]
    c = client.get("/api/analyze", params={"lat": lat, "lon": lon, "precip_source": "chirps"}).json()
    resc = c["variant"]["chirps_rescale"]
    assert resc["annual_mean_mm"]["used"] < 0.7 * resc["annual_mean_mm"]["power"]
    assert any(s["id"] == "chirps_v2" for s in c["data_sources"])
    r = client.post("/api/rotations", json={"lat": lat, "lon": lon, "precip_source": "chirps"})
    assert r.status_code == 200
    lat, lon = DEMO["punjab"]
    assert not client.get("/api/analyze", params={"lat": lat, "lon": lon}).json()["climate"]["rain_check"][
        "power_may_be_too_wet"]


def test_analyze_imerg_and_scenario(client):
    lat, lon = DEMO["konya"]
    b = client.get("/api/analyze", params={"lat": lat, "lon": lon, "precip_source": "imerg"}).json()
    resc = b["variant"]["imerg_rescale"]
    # Konya: POWER ~24 % wetter than IMERG (stage 3).
    assert resc["annual_mean_mm"]["used"] < 0.9 * resc["annual_mean_mm"]["power"]
    assert any(s["id"] == "gpm_imerg_monthly" for s in b["data_sources"])
    assert "baseline" not in b["crops"][0]

    s = client.get("/api/analyze", params={"lat": lat, "lon": lon, "delta_t": 2}).json()
    assert s["variant"]["scenario_active"]
    assert s["climate"]["annual"]["tmean_c"] == pytest.approx(b["climate"]["annual"]["tmean_c"] + 2, abs=0.11)
    ev = [c for c in s["crops"] if c["status"] == "evaluated"]
    assert ev and all("baseline" in c for c in ev)

    r = client.get("/api/analyze", params={"lat": lat, "lon": lon, "delta_t": 9})
    assert r.status_code == 422


def test_rotations_with_scenario(client):
    lat, lon = DEMO["punjab"]
    r = client.post("/api/rotations", json={"lat": lat, "lon": lon, "delta_t": 1.5, "delta_p": -20,
                                            "precip_source": "imerg"})
    assert r.status_code == 200, r.text
    b = r.json()
    assert b["variant"]["scenario_active"] and b["cards"]
