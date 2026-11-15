"""Save real NASA POWER, Earth Engine and SoilGrids responses for the 3 demo points into demo_cache/.

The API falls back to these files when the network (or Earth Engine) is
unavailable and labels the result `origin: demo_cache`. Files are
gzip-compressed raw responses.

Run: backend/.venv/Scripts/python scripts/build_demo_cache.py [power|gee|gee:<layer>|soilgrids]
     (no argument = all; gee needs EE_PROJECT in .env and `earthengine authenticate`;
     gee:<layer>, e.g. gee:phenology, adds one layer to the existing gee files)
"""

from __future__ import annotations

import asyncio
import gzip
import json
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.config import get_settings  # noqa: E402
from app.sources import gee, power, soilgrids  # noqa: E402

DEMO_POINTS = {"konya": (37.60, 32.75), "punjab": (30.80, 75.60), "nakuru": (-0.25, 36.15)}


def build_gee() -> None:
    s = get_settings()
    for name, (lat, lon) in DEMO_POINTS.items():
        raw = gee.fetch_raw(lat, lon, s.first_year, s.last_full_year)
        if raw["errors"]:
            raise SystemExit(f"{name}: Earth Engine layer errors, nothing saved: {raw['errors']}")
        out = gee.demo_cache_file(s.demo_cache_dir, lat, lon)
        out.write_bytes(gzip.compress(json.dumps(raw, separators=(",", ":")).encode()))
        print(f"{name}: {out.name} {out.stat().st_size // 1024} KiB")


def add_gee_layer(layer: str) -> None:
    """Fetch one Earth Engine layer and add it to the existing demo files (others unchanged)."""
    s = get_settings()
    for name, (lat, lon) in DEMO_POINTS.items():
        f = gee.demo_cache_file(s.demo_cache_dir, lat, lon)
        raw = json.loads(gzip.decompress(f.read_bytes()))
        new = gee.fetch_raw(lat, lon, s.first_year, s.last_full_year, layers=(layer,))
        if new["errors"]:
            raise SystemExit(f"{name}: Earth Engine error, nothing saved: {new['errors']}")
        raw["layers"][layer] = new["layers"][layer]
        raw["schema"] = gee.SCHEMA
        f.write_bytes(gzip.compress(json.dumps(raw, separators=(",", ":")).encode()))
        print(f"{name}: {f.name} + {layer}, {f.stat().st_size // 1024} KiB")


def build_soilgrids() -> None:
    s = get_settings()
    for name, (lat, lon) in DEMO_POINTS.items():
        raw = asyncio.run(soilgrids.fetch_raw(lat, lon))
        if raw["errors"]:
            raise SystemExit(f"{name}: SoilGrids errors, nothing saved: {raw['errors']}")
        out = soilgrids.demo_cache_file(s.demo_cache_dir, lat, lon)
        out.write_bytes(gzip.compress(json.dumps(raw, separators=(",", ":")).encode()))
        print(f"{name}: {out.name} {out.stat().st_size} B")


def main() -> None:
    s = get_settings()
    s.demo_cache_dir.mkdir(exist_ok=True)
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what.startswith("gee:"):  # e.g. gee:phenology — add one layer to the existing files
        add_gee_layer(what.split(":", 1)[1])
        return
    if what in ("gee", "all"):
        build_gee()
    if what in ("soilgrids", "all"):
        build_soilgrids()
    if what in ("gee", "soilgrids"):
        return
    with httpx.Client(timeout=120) as client:
        for name, (lat, lon) in DEMO_POINTS.items():
            r = client.get(power.URL, params={
                "parameters": ",".join(power.PARAMETERS), "community": "AG", "latitude": lat,
                "longitude": lon, "start": f"{s.first_year}0101", "end": f"{s.last_full_year}1231",
                "format": "JSON"})
            r.raise_for_status()
            raw = r.json()
            power.parse(raw, "network")  # validate before saving
            out = power.demo_cache_file(s.demo_cache_dir, lat, lon)
            out.write_bytes(gzip.compress(json.dumps(raw, separators=(",", ":")).encode()))
            print(f"{name}: {out.name} {out.stat().st_size // 1024} KiB")


if __name__ == "__main__":
    main()
