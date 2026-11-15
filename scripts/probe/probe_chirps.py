"""Probe: CHIRPS v2.0 daily precipitation (Earth Engine) at the demo points, monthly sums.

Dataset ID, band and terms from the official STAC entry
(https://storage.googleapis.com/earthengine-stac/catalog/UCSB-CHG/UCSB-CHG_CHIRPS_DAILY.json):
`UCSB-CHG/CHIRPS/DAILY`, band `precipitation` (mm/d), 0.05°, 50°S-50°N, 1981-;
"This dataset is in the public domain" (copyright waived by the CHC).
Monthly sums are computed on the Earth Engine servers at the 0.05° pixel of the
point; one request per point. Output: scripts/probe/out/chirps_monthly.json.

Run: backend/.venv/Scripts/python scripts/probe/probe_chirps.py
"""

from __future__ import annotations

import ee

from _common import DEMO_POINTS, Timer, report, save
from probe_gee import init

ID = "UCSB-CHG/CHIRPS/DAILY"
Y0, Y1 = 2001, 2024


def monthly(pt: ee.Geometry) -> list[dict]:
    col = ee.ImageCollection(ID).select("precipitation")
    months = ee.List([[y, m] for y in range(Y0, Y1 + 1) for m in range(1, 13)])

    def one(ym):
        ym = ee.List(ym)
        start = ee.Date.fromYMD(ee.Number(ym.get(0)), ee.Number(ym.get(1)), 1)
        img = col.filterDate(start, start.advance(1, "month")).sum()
        v = img.reduceRegion(ee.Reducer.first(), pt, scale=5566).get("precipitation")
        return ee.Feature(None, {"ym": start.format("YYYY-MM"), "mm": v})

    fc = ee.FeatureCollection(months.map(one))
    cols = ee.Dictionary({"ym": fc.aggregate_array("ym"), "mm": fc.aggregate_array("mm")}).getInfo()
    return [{"ym": a, "mm": b} for a, b in zip(cols["ym"], cols["mm"])]


def main() -> None:
    init()
    out = {}
    for name, p in DEMO_POINTS.items():
        with Timer() as t:
            rows = monthly(ee.Geometry.Point(p["lon"], p["lat"]))
        out[name] = rows
        annual = sum(r["mm"] for r in rows) / (Y1 - Y0 + 1) if rows else None
        report(f"{ID} {name}", len(rows) == 12 * (Y1 - Y0 + 1), {
            "months": len(rows), "time_s": round(t.seconds, 1),
            f"mean annual {Y0}-{Y1} mm": round(annual) if annual else None,
        })
    save("chirps_monthly.json", out)


if __name__ == "__main__":
    main()
