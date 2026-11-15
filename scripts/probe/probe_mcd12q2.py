"""Probe: MODIS MCD12Q2 v6.1 Land Cover Dynamics (phenology) at the demo points.

Dataset ID and band names from the official Earth Engine STAC entry
(https://storage.googleapis.com/earthengine-stac/catalog/MODIS/MODIS_061_MCD12Q2.json,
DOI 10.5067/MODIS/MCD12Q2.061). One `getRegion` call per point returns every
product year at the 500 m pixel containing the point. Dates are days since
1970-01-01; they are converted to calendar dates here.

Run: backend/.venv/Scripts/python scripts/probe/probe_mcd12q2.py
"""

from __future__ import annotations

import datetime as dt
import statistics

import ee

from _common import DEMO_POINTS, Timer, report, save
from probe_gee import init

ID = "MODIS/061/MCD12Q2"
BANDS = ["NumCycles", "MidGreenup_1", "Peak_1", "MidGreendown_1", "EVI_Amplitude_1", "QA_Overall_1",
         "MidGreenup_2", "Peak_2", "MidGreendown_2", "EVI_Amplitude_2", "QA_Overall_2"]
DATE_BANDS = {"MidGreenup_1", "Peak_1", "MidGreendown_1", "MidGreenup_2", "Peak_2", "MidGreendown_2"}


def as_date(v):
    return None if v is None else (dt.date(1970, 1, 1) + dt.timedelta(days=int(v)))


def main() -> None:
    init()
    col = ee.ImageCollection(ID).select(BANDS)
    out = {}
    for name, p in DEMO_POINTS.items():
        pt = ee.Geometry.Point(p["lon"], p["lat"])
        with Timer() as t:
            rows = col.getRegion(pt, 500).getInfo()
        head, data = rows[0], rows[1:]
        recs = []
        for r in data:
            d = dict(zip(head, r))
            rec = {"year": int(d["id"][:4]), **{b: d.get(b) for b in BANDS}}
            for b in DATE_BANDS:
                rec[b] = as_date(rec[b]).isoformat() if rec[b] is not None else None
            recs.append(rec)
        out[name] = recs
        peaks1 = [dt.date.fromisoformat(r["Peak_1"]).timetuple().tm_yday for r in recs if r["Peak_1"]]
        peaks2 = [dt.date.fromisoformat(r["Peak_2"]).timetuple().tm_yday for r in recs if r["Peak_2"]]
        report(f"{ID} {name}", bool(recs), {
            "years": f"{recs[0]['year']}-{recs[-1]['year']} ({len(recs)})" if recs else 0,
            "time_s": round(t.seconds, 1),
            "NumCycles median": statistics.median([r["NumCycles"] or 0 for r in recs]) if recs else None,
            "Peak_1 doy median": statistics.median(peaks1) if peaks1 else None,
            "Peak_2 doy median (n)": (statistics.median(peaks2), len(peaks2)) if peaks2 else None,
        })
    save("mcd12q2_demo_points.json", out)


if __name__ == "__main__":
    main()
