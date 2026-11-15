"""Tests never call Earth Engine: live extraction raises, so the API must use demo_cache/."""

import pytest

from app.sources import SourceError, gee


@pytest.fixture(autouse=True)
def no_earth_engine(monkeypatch):
    def offline(*args, **kwargs):
        raise SourceError("Earth Engine offline (test)")

    monkeypatch.setattr(gee, "fetch_raw", offline)


@pytest.fixture(autouse=True)
def no_soilgrids_network(monkeypatch):
    """SoilGrids is never called live in tests: the demo cache (or an error) is used."""
    from app.sources import soilgrids

    async def offline(*args, **kwargs):
        raise SourceError("SoilGrids offline (test)")

    monkeypatch.setattr(soilgrids, "fetch_raw", offline)
