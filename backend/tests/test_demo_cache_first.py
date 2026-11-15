"""DEMO_CACHE_FIRST (hosted demo): the demo fields use demo_cache/ before the network."""

import asyncio

import httpx

from app.config import ROOT
from app.sources import power

KONYA = (37.60, 32.75)


def _client(calls: list):
    def handler(request):
        calls.append(request.url)
        return httpx.Response(500)
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def _fetch(calls):
    async def run():
        async with _client(calls) as c:
            return await power.fetch_daily(c, *KONYA, 2001, 2025, cache=None, demo_dir=ROOT / "demo_cache")
    return asyncio.run(run())


def test_demo_first_skips_the_network(monkeypatch):
    monkeypatch.setenv("DEMO_CACHE_FIRST", "1")
    calls: list = []
    data = _fetch(calls)
    assert data.origin == "demo_cache" and not calls


def test_default_order_tries_the_network_first(monkeypatch):
    monkeypatch.delenv("DEMO_CACHE_FIRST", raising=False)
    calls: list = []
    data = _fetch(calls)
    assert calls and data.origin == "demo_cache"  # network failed (500) -> demo cache fallback
