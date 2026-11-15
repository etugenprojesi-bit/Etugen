"""Benchmark POST /api/rotations offline (demo_cache): best totals and timing.

Runs the 3 demo points x rainfed / full irrigation through the real API with
network access blocked (like backend/tests/test_api_rotations.py) and prints
a Markdown table: total and crops of each recommended rotation, request time.

Run: backend/.venv/Scripts/python scripts/bench_rotations.py [--profile] [--json out.json]
"""

from __future__ import annotations

import argparse
import asyncio
import cProfile
import json
import os
import pstats
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
os.environ.setdefault("LAST_FULL_YEAR", "2025")
os.environ["CACHE_PATH"] = str(Path(tempfile.mkdtemp()) / "bench_cache.sqlite")
os.environ.pop("ANTHROPIC_API_KEY", None)
os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)

import httpx  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import app.api.analyze as analyze  # noqa: E402
from app.config import get_settings  # noqa: E402

DEMO_POINTS = {"konya": (37.60, 32.75), "punjab": (30.80, 75.60), "nakuru": (-0.25, 36.15)}
IRRIGATION = ("none", "full")


def offline_client() -> TestClient:
    def offline(request):
        raise httpx.ConnectError("offline (benchmark)", request=request)

    real = httpx.AsyncClient
    analyze.httpx.AsyncClient = lambda *a, **k: real(transport=httpx.MockTransport(offline))
    get_settings.cache_clear()
    from app.main import app
    return TestClient(app)


SEARCH_S: list[float] = []


def timed_recommend():
    """Wrap engine.recommend (as used by the API) to time the rotation search alone."""
    import app.api.rotations as api
    real = api.rot.recommend

    def wrapped(*a, **k):
        t = time.perf_counter()
        try:
            return real(*a, **k)
        finally:
            SEARCH_S.append(time.perf_counter() - t)
    api.rot.recommend = wrapped


def run(client: TestClient, lat: float, lon: float, irrigation: str) -> dict:
    """Calls the endpoint coroutine in this thread (so cProfile sees it); same code path as HTTP."""
    from app.api.rotations import RotationRequest, rotations
    t0 = time.perf_counter()
    SEARCH_S.clear()
    body = asyncio.run(rotations(RotationRequest(lat=lat, lon=lon, irrigation=irrigation)))
    recs = [c for c in body["cards"] if c["kind"] == "recommended"]
    return {
        "wall_s": round(time.perf_counter() - t0, 2),
        "timing_s": body["timing_s"],
        "search_s": round(sum(SEARCH_S), 2),
        "recommended": [{"total": c["total"],
                         "years": [[s["crop_id"] for s in y] for y in c["years"]]} for c in recs],
    }


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", action="store_true", help="cProfile the requests, print the top functions")
    ap.add_argument("--json", help="write the results to this file")
    ap.add_argument("--points", default=",".join(DEMO_POINTS))
    ap.add_argument("--repeat", type=int, default=2, help="runs per case; the fastest is reported")
    args = ap.parse_args()
    client = offline_client()
    timed_recommend()
    run(client, *DEMO_POINTS["konya"], "none")  # warm-up: imports, data files
    prof = cProfile.Profile() if args.profile else None
    out = {}
    print("| Point | Water | Request, s | Search, s | #1 total | #2 | #3 | #1 rotation |")
    print("|---|---|---|---|---|---|---|---|")
    for name in args.points.split(","):
        for irr in IRRIGATION:
            if prof:
                prof.enable()
            runs = [run(client, *DEMO_POINTS[name], irr) for _ in range(args.repeat)]
            res = min(runs, key=lambda r: r["timing_s"])  # least disturbed by other load
            res["search_s"] = min(r["search_s"] for r in runs)
            if prof:
                prof.disable()
            out[f"{name}/{irr}"] = res
            tot = [f"{r['total']:.3f}" for r in res["recommended"]] + ["—"] * 3
            best = " → ".join("+".join(y) or "fallow" for y in res["recommended"][0]["years"]) \
                if res["recommended"] else "—"
            print(f"| {name} | {irr} | {res['timing_s']} | {res['search_s']} | {tot[0]} | {tot[1]} | {tot[2]} | {best} |", flush=True)
    if args.json:
        Path(args.json).write_text(json.dumps(out, indent=1), encoding="utf-8")
    if prof:
        st = pstats.Stats(prof)
        st.sort_stats("cumulative").print_stats(r"[\/]app[\/]", 30)
        st.sort_stats("tottime").print_stats(20)


if __name__ == "__main__":
    main()
