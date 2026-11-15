"""Model seasons vs MODIS MCD12Q2 phenology at the 3 demo points (offline, demo_cache).

Prints a Markdown table for docs/METHOD.md "Season validation (MODIS)" and,
with --json <file>, writes the per-year details. Sowing = local GGCMI planting
day (nearest 1st/16th); crops = every evaluable crop with a GGCMI calendar
at the point. Irrigation: rainfed, except crops whose GGCMI calendar exists
only for irrigation at the point (then `full`).

Run: backend/.venv/Scripts/python scripts/validate_seasons.py [--json out.json]
"""

from __future__ import annotations

import gzip
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
os.environ.setdefault("LAST_FULL_YEAR", "2025")

from app.config import get_settings  # noqa: E402
from app.features import climate  # noqa: E402
from app.harmonize.series import ndvi_series  # noqa: E402
from app.sources import gee, power  # noqa: E402
from app.suitability import calendar  # noqa: E402
from app.suitability.crops import load_crops, localize  # noqa: E402
from app.suitability.engine import ClimateArrays, evaluable  # noqa: E402
from app.validation.seasons import compare, parse_phenology  # noqa: E402

DEMO_POINTS = {"konya": (37.60, 32.75), "punjab": (30.80, 75.60), "nakuru": (-0.25, 36.15)}


def load(lat: float, lon: float):
    s = get_settings()
    f = power.demo_cache_file(s.demo_cache_dir, lat, lon)
    pdata = power.parse(json.loads(gzip.decompress(f.read_bytes())), "demo_cache")
    df = climate.add_derived(pdata.daily, pdata.elevation_m, lat)
    g = json.loads(gzip.decompress(gee.demo_cache_file(s.demo_cache_dir, lat, lon).read_bytes()))
    cycles = parse_phenology(g["layers"]["phenology"])
    ndvi = ndvi_series(g["layers"]["ndvi"]).resample("D").mean().interpolate(limit=40)
    return ClimateArrays.from_frame(df), cycles, ndvi


def fmt(d: dict) -> str:
    if d.get("median") is None:
        return "—"
    if "p25" in d:
        return f"{d['median']:+.0f} ({d['p25']:+.0f}…{d['p75']:+.0f})"
    return f"{d['median']:+.0f}"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # Windows console default is not UTF-8
    s = get_settings()
    crops = [c for c in load_crops(s.data_dir) if evaluable(c)[0]]
    out = {}
    print("| Point | Crop | Water | Sowing (GGCMI) | Matched years | Model maturity − MidGreendown, d (IQR) "
          "| Model mid-season − Peak, d | Same with MOD13Q1 NDVI, d | Spearman (years) |")
    print("|---|---|---|---|---|---|---|---|---|")
    for name, (lat, lon) in DEMO_POINTS.items():
        clim, cycles, ndvi = load(lat, lon)
        for c in localize(crops, lat, lon, s.data_dir):  # regional cultivar variants (Punjab wheat)
            irr = "none"
            cal = calendar.lookup(s.data_dir, c.id, lat, lon, "none")
            if cal is None:
                irr = "full"
                cal = calendar.lookup(s.data_dir, c.id, lat, lon, "full")
            if cal is None:
                continue
            r = compare(c, clim, cal["planting_doy"], irr, cycles, ndvi)
            out[f"{name}/{c.id}"] = r
            if r["n_seasons"] == 0:
                continue
            print(f"| {name} | {c.id} | {irr} | {r['sowing']} | {r['n_matched']}/{r['n_seasons']} "
                  f"| {fmt(r['maturity_minus_greendown_days'])} | {fmt(r['midseason_minus_peak_days'])} "
                  f"| {fmt(r['maturity_minus_ndvi_greendown_days'])} | {r['interannual_spearman'] or '—'} |")
    if "--json" in sys.argv:
        Path(sys.argv[sys.argv.index("--json") + 1]).write_text(json.dumps(out, default=str, indent=1),
                                                                 encoding="utf-8")


if __name__ == "__main__":
    main()
