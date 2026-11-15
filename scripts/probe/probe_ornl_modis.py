"""Probe: ORNL DAAC MODIS/VIIRS Land Product Subsets REST API (no authentication).

Fallback for NDVI (and possibly SMAP / LST / GEDI) when Earth Engine is not
available. Checks bands, date coverage, a 1 km buffer subset and timing.

Run: backend/.venv/Scripts/python scripts/probe/probe_ornl_modis.py
"""

from __future__ import annotations

import httpx

from _common import DEMO_POINTS, Timer, report, save

BASE = "https://modis.ornl.gov/rst/api/v1"
# product -> bands to request in the subset test
PRODUCTS = {
    "MOD13Q1": ["250m_16_days_NDVI", "250m_16_days_pixel_reliability"],
    "MOD11A2": ["LST_Day_1km"],
    "SPL3SMP_E": None,  # bands discovered at runtime
    "GEDI03": None,
}
CHUNK = 10  # the API limits a subset request to 10 dates


def bands(client: httpx.Client, product: str) -> list[dict]:
    r = client.get(f"{BASE}/{product}/bands")
    r.raise_for_status()
    return r.json()["bands"]


def dates(client: httpx.Client, product: str, lat: float, lon: float) -> list[dict]:
    r = client.get(f"{BASE}/{product}/dates", params={"latitude": lat, "longitude": lon})
    r.raise_for_status()
    return r.json()["dates"]


def subset(client: httpx.Client, product: str, band: str, lat: float, lon: float,
           start: str, end: str, km: int = 1) -> dict:
    r = client.get(
        f"{BASE}/{product}/subset",
        params={"latitude": lat, "longitude": lon, "band": band, "startDate": start,
                "endDate": end, "kmAboveBelow": km, "kmLeftRight": km},
        headers={"Accept": "application/json"},
    )
    r.raise_for_status()
    return r.json()


def main() -> None:
    p = DEMO_POINTS["konya"]
    ok_all = True
    with httpx.Client(timeout=120) as client:
        for product, wanted in PRODUCTS.items():
            try:
                band_meta = bands(client, product)
                band_names = [b["band"] for b in band_meta]
                d = dates(client, product, p["lat"], p["lon"])
                test_bands = wanted or band_names[:1]
                first, last = d[0], d[-1]
                # One chunk of (up to) 10 most recent dates
                chunk = d[-CHUNK:]
                with Timer() as t:
                    res = subset(client, product, test_bands[0], p["lat"], p["lon"],
                                 chunk[0]["modis_date"], chunk[-1]["modis_date"])
                save(f"ornl_{product}_konya.json", {"bands": band_meta, "subset": res})
                sub = res.get("subset", [])
                n_pix = len(sub[0]["data"]) if sub else 0
                report(f"ORNL {product}", True, {
                    "bands": band_names,
                    "dates": f"{len(d)} ({first['calendar_date']} .. {last['calendar_date']})",
                    "subset_band": test_bands[0],
                    "subset_dates_returned": len(sub),
                    "pixels_per_date (1 km buffer)": n_pix,
                    "grid": f"{res.get('nrows')}x{res.get('ncols')} cellsize={res.get('cellsize')}",
                    "seconds_for_10_dates": f"{t.seconds:.1f}",
                    "sample_values": sub[0]["data"][:6] if sub else None,
                })
            except httpx.HTTPError as e:
                ok_all = False
                report(f"ORNL {product}", False, {"error": repr(e)})
    raise SystemExit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
