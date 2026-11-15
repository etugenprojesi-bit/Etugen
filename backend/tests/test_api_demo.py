"""End-to-end /api/analyze for the 3 demo points, offline.

The network is replaced by a transport that always fails, so the API must fall
back to the real POWER responses stored in demo_cache/ and say so.
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
def test_demo_point_from_demo_cache(client, name):
    lat, lon = DEMO[name]
    r = client.get("/api/analyze", params={"lat": lat, "lon": lon})
    assert r.status_code == 200, r.text
    body = r.json()
    src = body["data_sources"][0]
    assert src["origin"] == "demo_cache" and src["is_demo_cache"] is True
    assert body["climate"]["monthly"]["years"] == 25
    assert len(body["climate"]["monthly"]["months"]) == 12
    evaluated = [c for c in body["crops"] if c["status"] == "evaluated"]
    modelled = [c for c in body["crops"] if c["status"] in ("evaluated", "not_suitable_by_model")]
    assert len(modelled) >= 10 and len(evaluated) >= 4
    scores = [c["best_window"]["score_median"] for c in evaluated]
    assert scores == sorted(scores, reverse=True)
    for c in body["crops"]:
        assert c["confidence"]["level"] in ("low", "medium", "unknown")  # never "high" in stage 1
        assert c["confidence"]["questions"]
    assert "does not replace" in body["disclaimer"]


def test_climate_profiles_differ_as_expected(client):
    out = {k: client.get("/api/analyze", params={"lat": a, "lon": b}).json() for k, (a, b) in DEMO.items()}
    annual = {k: v["climate"]["annual"] for k, v in out.items()}
    # Konya: cold winters with frost; Nakuru (equator, ~2000 m): little frost; Punjab: many hot days.
    assert annual["konya"]["frost_days"] > 30
    assert annual["punjab"]["hot_days"] > annual["konya"]["hot_days"]
    assert annual["punjab"]["tmean_c"] > annual["konya"]["tmean_c"]
    # Konya is semi-arid: P well below ET0
    assert annual["konya"]["aridity_index_p_over_et0"] < 0.65


def test_irrigation_raises_water_scores(client):
    lat, lon = DEMO["konya"]
    rain = client.get("/api/analyze", params={"lat": lat, "lon": lon}).json()
    irr = client.get("/api/analyze", params={"lat": lat, "lon": lon, "irrigation": "full"}).json()
    w_rain = {c["id"]: c["best_window"]["water_score_median"] for c in rain["crops"] if c["status"] == "evaluated"}
    w_irr = {c["id"]: c["best_window"]["water_score_median"] for c in irr["crops"] if c["status"] == "evaluated"}
    assert all(w_irr[k] >= w_rain[k] for k in w_rain)
    assert w_irr["maize_grain"] == 1.0


def test_bad_input_is_rejected(client):
    assert client.get("/api/analyze", params={"lat": 95, "lon": 0}).status_code == 422
    assert client.get("/api/analyze", params={"lat": 0, "lon": 0, "irrigation": "lots"}).status_code == 422


def test_unknown_point_offline_reports_source_error(client):
    r = client.get("/api/analyze", params={"lat": 10.0, "lon": 10.0})
    assert r.status_code == 502
    assert r.json()["detail"]["source"] == "nasa_power"
