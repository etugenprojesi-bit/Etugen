"""Probe: GGCMI Phase 3 crop calendar (Zenodo 10.5281/zenodo.5062513, CC BY 4.0).

Planting and maturity day of year for 18 crops, rainfed and irrigated, on a
0.5° grid (multi-year average, gap-filled and extrapolated outside cropland).
Reference: Jägermeyr et al. (2021), Nature Food 2:873-885,
doi:10.1038/s43016-021-00400-y.

The files are NetCDF-4 (HDF5). Reading them needs `h5py`, which is NOT a
project dependency (pending decision, docs/drafts/plan_ekim_takvimi.md).
Without h5py the probe still checks the record, licence and file list.

Run: backend/.venv/Scripts/python scripts/probe/probe_ggcmi_calendar.py
"""

from __future__ import annotations

import datetime as dt
import importlib.util
import io

import httpx

from _common import DEMO_POINTS, Timer, report, save

RECORD = "https://zenodo.org/api/records/5062513"
FILE_URL = "https://zenodo.org/records/5062513/files/{name}?download=1"
CROPS = ["wwh", "swh", "bar", "mai", "sor", "mil", "ri1", "soy", "bea", "nut", "sun", "rap", "pot", "cas",
         "cot", "sgb", "pea", "rye"]
SHOW = ["wwh", "swh", "bar", "mai"]


def mmdd(doy: float) -> str:
    return (dt.date(2001, 1, 1) + dt.timedelta(days=int(doy) - 1)).strftime("%m-%d")


def main() -> None:
    with httpx.Client(timeout=60, follow_redirects=True) as client:
        with Timer() as t:
            meta = client.get(RECORD).json()
        m = meta["metadata"]
        files = {f["key"]: f["size"] for f in meta.get("files", [])}
        expected = {f"{c}_{s}_ggcmi_crop_calendar_phase3_v1.01.nc4" for c in CROPS for s in ("rf", "ir")}
        ok = m.get("license", {}).get("id") == "cc-by-4.0" and expected <= set(files)
        details = {"title": m.get("title"), "licence": m.get("license"), "published": m.get("publication_date"),
                   "files": len(files), "total_kib": sum(files.values()) // 1024,
                   "all 36 expected files": expected <= set(files), "seconds": f"{t.seconds:.1f}"}
        values = {}
        if importlib.util.find_spec("h5py") is None:
            details["values"] = "h5py not installed: values not read (see module docstring)"
        else:
            import h5py
            import numpy as np

            for c in SHOW:
                name = f"{c}_rf_ggcmi_crop_calendar_phase3_v1.01.nc4"
                with h5py.File(io.BytesIO(client.get(FILE_URL.format(name=name)).content), "r") as h:
                    lat, lon = h["lat"][:], h["lon"][:]
                    for key, p in DEMO_POINTS.items():
                        i, j = int(np.argmin(abs(lat - p["lat"]))), int(np.argmin(abs(lon - p["lon"])))
                        pd_, md_ = float(h["planting_day"][i, j]), float(h["maturity_day"][i, j])
                        values[f"{c}_rf {key}"] = (None if pd_ > 1e19 else
                                                   f"{mmdd(pd_)} -> {mmdd(md_)} (cell {lat[i]}, {lon[j]}, "
                                                   f"source {int(h['data_source_used'][i, j])})")
            details.update(values)
    save("ggcmi_calendar.json", {"metadata": m, "files": files, "values": values})
    report("GGCMI Phase 3 crop calendar (Zenodo)", ok, details)
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
