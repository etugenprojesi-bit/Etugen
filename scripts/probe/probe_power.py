"""Probe: NASA POWER daily point API (no authentication).

Requests 2001-01-01 .. 2025-12-31 daily data for each demo point and checks
parameter coverage, fill values and response time.

Run: backend/.venv/Scripts/python scripts/probe/probe_power.py
"""

from __future__ import annotations

import httpx

from _common import DEMO_POINTS, Timer, report, save

URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
CLIMATE = ["T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR", "RH2M", "WS2M", "ALLSKY_SFC_SW_DWN"]
# Model-based soil wetness (MERRA-2 / GEOS), NOT SMAP observations.
SOIL_MODEL = ["GWETTOP", "GWETROOT"]
START, END = "20010101", "20251231"


def probe_point(client: httpx.Client, key: str, lat: float, lon: float) -> bool:
    params = {
        "parameters": ",".join(CLIMATE + SOIL_MODEL),
        "community": "AG",
        "latitude": lat,
        "longitude": lon,
        "start": START,
        "end": END,
        "format": "JSON",
    }
    with Timer() as t:
        r = client.get(URL, params=params)
    if r.status_code != 200:
        report(f"POWER {key}", False, {"status": r.status_code, "body": r.text[:300]})
        return False

    data = r.json()
    save(f"power_{key}.json", data)
    header = data.get("header", {})
    fill = header.get("fill_value")
    series = data["properties"]["parameter"]
    coverage = {}
    for p in CLIMATE + SOIL_MODEL:
        values = series.get(p, {})
        n = len(values)
        missing = sum(1 for v in values.values() if v == fill)
        dates = sorted(values)
        coverage[p] = f"{n} days, {missing} fill, {dates[0] if dates else '-'}..{dates[-1] if dates else '-'}"

    report(
        f"POWER {key}",
        True,
        {
            "seconds": f"{t.seconds:.1f}",
            "bytes": len(r.content),
            "api": header.get("api"),
            "sources": header.get("sources"),
            "fill_value": fill,
            "time_standard": header.get("time_standard"),
            "geometry": data.get("geometry"),
            **coverage,
        },
    )
    return True


def main() -> None:
    with httpx.Client(timeout=120) as client:
        results = [probe_point(client, k, p["lat"], p["lon"]) for k, p in DEMO_POINTS.items()]
        # Parameter metadata (units, definitions) for docs.
        meta = client.get(
            "https://power.larc.nasa.gov/api/system/manager/parameters",
            params={"community": "AG", "temporal": "daily", "parameters": ",".join(CLIMATE + SOIL_MODEL)},
        )
        if meta.status_code == 200:
            save("power_parameters_meta.json", meta.json())
            print("    parameter metadata saved")
        else:
            print(f"    parameter metadata request: HTTP {meta.status_code}")
    raise SystemExit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
