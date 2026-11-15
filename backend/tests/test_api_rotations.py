"""POST /api/rotations end to end, offline (demo_cache), without LLM credentials."""

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import get_settings

KONYA = {"lat": 37.60, "lon": 32.75}
PUNJAB = {"lat": 30.80, "lon": 75.60}


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("CACHE_PATH", str(tmp_path / "cache.sqlite"))
    monkeypatch.setenv("LAST_FULL_YEAR", "2025")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
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


def test_unknown_current_rotation_gives_reference_and_rule_abiding_recommendations(client):
    r = client.post("/api/rotations", json={**KONYA, "irrigation": "full"})
    assert r.status_code == 200, r.text
    body = r.json()
    cards = body["cards"]
    assert cards[0]["kind"] == "reference"
    assert cards[0]["rule_violations"]  # monoculture breaks the family/repeat rules
    recs = [c for c in cards if c["kind"] == "recommended"]
    assert 1 <= len(recs) <= 3 and body["n_recommended"] == len(recs)
    for c in recs:
        assert not c["rule_violations"]
        assert c["questions"] and c["data_gaps"] and c["evidence"]
        assert c["confidence"]["level"] in ("low", "medium", "unknown")
        assert len(c["years"]) in (2, 3)
        assert "income" in c["unknown_subscores"]  # no market input given
    assert body["explanation"] is None
    # cut forage modelled to its first cut only: evaluated, listed, never in a card
    assert set(body["not_used_first_cut_only"]) <= {"sudan_grass", "berseem_clover"}
    assert not {"sudan_grass", "berseem_clover"} & set(body["usable_crops"])
    for c in recs:
        assert not {s["crop_id"] for y in c["years"] for s in y} & {"sudan_grass", "berseem_clover"}


def test_current_rotation_is_scored_and_flagged(client):
    r = client.post("/api/rotations", json={
        **KONYA, "current_rotation": [["winter_wheat"], ["winter_wheat"], ["rapeseed"]]})
    card = r.json()["cards"][0]
    assert card["kind"] == "current"
    codes = {v["code"] for v in card["rule_violations"]}
    assert "same_crop_consecutive_years" in codes
    assert card["missing_slots"] == [{"year": 3, "crop_id": "rapeseed", "status": "insufficient_data"}]
    assert card["confidence"]["needs_local_validation"]


def test_constraints_and_market_input(client):
    r = client.post("/api/rotations", json={
        **PUNJAB, "irrigation": "full",
        "constraints": {"excluded_crops": ["rice"], "equipment_limits": ["no_root_harvester"],
                        "market_crops": ["soybean", "spring_wheat"]},
        "priorities": {"income": 5, "water": 1},
    })
    body = r.json()
    assert "rice" in body["excluded_by_constraints"] and "potato" in body["excluded_by_constraints"]
    for c in body["cards"]:
        ids = {s["crop_id"] for y in c["years"] for s in y}
        assert not ids & {"rice", "potato", "sweet_potato", "cassava"}
        assert c["subscores"]["income"]["value"] is not None


def test_llm_requested_without_key_falls_back_to_template(client):
    body = client.post("/api/rotations", json={**KONYA, "explain": "llm"}).json()
    assert body["explanation"] == {"mode": "template", "reason": "no_api_key"}


def test_invalid_input_rejected(client):
    assert client.post("/api/rotations", json={**KONYA, "priorities": {"water": 7}}).status_code == 422
    assert client.post("/api/rotations", json={"lat": 0}).status_code == 422


@pytest.mark.parametrize("precip_source", ["power", "imerg"])
def test_wheat_fallow_reports_stored_soil_water(client, precip_source):
    r = client.post("/api/rotations", json={**KONYA, "precip_source": precip_source,
                                            "current_rotation": [["winter_wheat"], []]})
    body = r.json()
    assert body["soil_water"]["tew_mm"] == pytest.approx(20.3, abs=0.1)
    assert any(s["id"] == "soilgrids_water_retention" and s["origin"] == "demo_cache" for s in body["data_sources"])
    card = body["cards"][0]
    fallow = [b for b in card["benefits"] if b["code"] == "fallow_stores_water"]
    assert len(fallow) == 1
    p = fallow[0]["params"]
    assert 0.10 <= p["storage_efficiency_median"] <= 0.35   # Janssen (1972): 14-33 % in the Konya Basin
    assert p["score_median_with"] > p["score_median_without"]
    wheat = card["years"][0][0]
    assert wheat["stored_soil_water"]["n_fallow_years"] == 1
    assert wheat["score_median"] > wheat["score_median_without_stored_water"]
    codes = {g["code"] for g in card["data_gaps"]}
    assert "soil_water_model" in codes and "fallow_not_modelled" not in codes


def test_without_soil_data_fallow_stays_unmodelled(client, monkeypatch):
    from app.sources import SourceError, soilgrids

    async def unavailable(*a, **k):
        raise SourceError("SoilGrids unavailable (test)")

    monkeypatch.setattr(soilgrids, "load_point", unavailable)
    r = client.post("/api/rotations", json={**KONYA, "current_rotation": [["winter_wheat"], []]})
    body = r.json()
    assert body["soil_water"] is None
    assert any(s["id"] == "soilgrids_water_retention" and s["origin"] == "none" for s in body["data_sources"])
    card = body["cards"][0]
    assert card["years"][0][0]["stored_soil_water"] is None
    assert not any(b["code"] == "fallow_stores_water" for b in card["benefits"])


def test_unmodelled_crop_year_is_not_treated_as_fallow(client):
    r = client.post("/api/rotations", json={**KONYA, "current_rotation": [["winter_wheat"], ["rapeseed"]]})
    card = r.json()["cards"][0]
    assert card["missing_slots"] and card["years"][0][0]["stored_soil_water"] is None


def test_explore_sowing_switches_the_calendar_rule_off(client):
    on = client.post("/api/rotations", json={**PUNJAB}).json()
    off = client.post("/api/rotations", json={**PUNJAB, "explore_sowing": True}).json()
    assert any(s["id"] == "ggcmi_crop_calendar" for s in on["data_sources"])
    assert off["cards"] and on["cards"]

    def wheat_sowings(body):
        return {s["sowing"] for c in body["cards"] for y in c["years"] for s in y
                if s["crop_id"] in ("winter_wheat", "spring_wheat")}
    # with the local calendar, wheat is never sown in the monsoon months
    assert not any(m[:2] in ("06", "07", "08") for m in wheat_sowings(on))


def test_flat_terrain_drops_the_erosion_priority(client):
    body = client.post("/api/rotations", json={**PUNJAB, "priorities": {"erosion": 5}}).json()
    assert body["slope"]["flat_terrain"] and body["erosion_ignored_flat_terrain"]
    for c in body["cards"]:
        assert c["subscores"]["erosion"]["weight"] == 0
