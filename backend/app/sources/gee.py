"""Google Earth Engine point time series (stage 3).

Dataset IDs, bands, units and QA meanings were verified in
scripts/probe/probe_gee.py (live) and against the official STAC catalog;
see docs/DATA_SOURCES.md §4. All reductions run on the Earth Engine
servers; only small lists of numbers come back.

Each layer is sampled at the *rounded* analysis point (0.05° grid, see
docs/PRIVACY.md). Footprints differ by source and are reported as such —
nothing is resampled to a finer grid than the source provides.

The raw result is a plain JSON dict so it can be stored in the SQLite cache
and in demo_cache/ (offline fallback) exactly like the POWER responses.
"""

from __future__ import annotations

import gzip
import json
import math
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app.config import demo_cache_first
from app.cache.store import ResponseCache, cache_key
from app.sources import SourceError

NDVI_ID = "MODIS/061/MOD13Q1"
SMAP_IDS = ("NASA/SMAP/SPL3SMP_E/005", "NASA/SMAP/SPL3SMP_E/006")
IMERG_MONTHLY_ID = "NASA/GPM_L3/IMERG_MONTHLY_V07"
DEM_ID = "NASA/NASADEM_HGT/001"
CHIRPS_ID = "UCSB-CHG/CHIRPS/DAILY"     # CHIRPS v2.0, public domain (STAC terms)
PHENOLOGY_ID = "MODIS/061/MCD12Q2"   # land surface phenology, doi:10.5067/MODIS/MCD12Q2.061
PHENOLOGY_BANDS = ["NumCycles",
                   "MidGreenup_1", "Peak_1", "MidGreendown_1", "EVI_Amplitude_1", "QA_Overall_1",
                   "MidGreenup_2", "Peak_2", "MidGreendown_2", "EVI_Amplitude_2", "QA_Overall_2"]

NDVI_BUFFER_M = 1000      # NDVI: mean of 250 m pixels within 1 km of the point
CELL_HALF_DEG = 0.025     # slope: the 0.05° analysis cell around the rounded point
SCHEMA = 4                # bump when the raw layout changes (invalidates cache keys); 3: + phenology, 4: + chirps
NDVI_MISSING = -9999      # sentinel for composites with no valid pixel

FOOTPRINTS = {
    "ndvi": "MODIS MOD13Q1 250 m pixels, mean within 1 km of the analysis point",
    "smap": "SMAP L3 enhanced 9 km grid cell containing the analysis point",
    "imerg": "GPM IMERG 0.1° (~11 km) grid cell containing the analysis point",
    "slope": "NASADEM 30 m slope over the 0.05° analysis cell",
    "phenology": "MODIS MCD12Q2 500 m pixel containing the analysis point",
    "chirps": "CHIRPS v2.0 0.05° (~5.5 km) pixel containing the analysis point",
}

# `earthengine authenticate` also requests Google Drive access. If the user
# leaves that box unticked, refreshing with the stored scope list fails with
# "invalid_scope". We only read Earth Engine data, so we ask for these two.
EE_SCOPES = [
    "https://www.googleapis.com/auth/earthengine.readonly",
    "https://www.googleapis.com/auth/cloud-platform.read-only",
]

_init_lock = threading.Lock()
_initialized = False


def _ee():
    import ee  # imported lazily: tests and the stage-1 API do not need it

    return ee


def initialize() -> None:
    """Initialise Earth Engine once; raise SourceError with the reason if impossible."""
    global _initialized
    with _init_lock:
        if _initialized:
            return
        ee = _ee()
        project = os.environ.get("EE_PROJECT")
        if not project:
            raise SourceError("Earth Engine: EE_PROJECT is not set in .env")
        key = os.environ.get("EE_SERVICE_ACCOUNT_KEY")
        key_json = os.environ.get("EE_SERVICE_ACCOUNT_JSON")  # deployment secret: the key file's content
        try:
            if key_json:
                creds = ee.ServiceAccountCredentials(None, key_data=key_json)
            elif key:
                creds = ee.ServiceAccountCredentials(None, key_file=key)
            else:
                import google.oauth2.credentials
                from ee import oauth

                args = oauth.get_credentials_arguments()
                args.pop("scopes", None)
                args.pop("quota_project_id", None)
                creds = google.oauth2.credentials.Credentials(None, scopes=EE_SCOPES, **args)
            ee.Initialize(creds, project=project)
        except Exception as e:  # noqa: BLE001 - any auth/setup problem is reported verbatim
            raise SourceError(f"Earth Engine initialisation failed: {e}") from e
        _initialized = True


# --- server-side extraction (one getInfo per layer) -------------------------------


def _ndvi(ee, pt, start: str, end: str) -> dict:
    buf = pt.buffer(NDVI_BUFFER_M)

    def per_image(img):
        qa = img.select("SummaryQA")
        good = img.select("NDVI").updateMask(qa.lte(1))  # 0 good, 1 marginal (STAC bitmask)
        stats = good.reduceRegion(ee.Reducer.mean().combine(ee.Reducer.count(), sharedInputs=True),
                                  buf, scale=250, maxPixels=1e6)
        n = ee.Number(stats.get("NDVI_count"))
        # aggregate_array drops nulls, which would misalign the lists: use a sentinel.
        ndvi = ee.Algorithms.If(n.gt(0), stats.get("NDVI_mean"), NDVI_MISSING)
        return ee.Feature(None, {"t": img.date().format("YYYY-MM-dd"), "ndvi": ndvi, "n": n})

    fc = ee.FeatureCollection(ee.ImageCollection(NDVI_ID).filterDate(start, end).map(per_image))
    cols = ee.Dictionary({k: fc.aggregate_array(k) for k in ("t", "ndvi", "n")}).getInfo()
    if not len(cols["t"]) == len(cols["ndvi"]) == len(cols["n"]):
        raise SourceError("NDVI lists from Earth Engine have different lengths")
    return {"id": NDVI_ID, "scale_factor": 0.0001, "missing": NDVI_MISSING,
            "qa": "SummaryQA <= 1 (good or marginal)",
            "dates": cols["t"], "ndvi_raw": cols["ndvi"], "valid_pixels": cols["n"]}


def _region_rows(coll, pt, scale: float, bands: list[str]) -> list[list]:
    """getRegion rows [date_ms, *bands] (header removed); masked values are None."""
    try:
        rows = coll.select(bands).getRegion(pt, scale).getInfo()
    except Exception as e:  # noqa: BLE001
        if "No bands in collection" in str(e):  # empty collection for this period
            return []
        raise
    head = rows[0]
    idx = [head.index("time")] + [head.index(b) for b in bands]
    return [[r[i] for i in idx] for r in rows[1:]]


def _smap(ee, pt, start: str, end: str) -> dict:
    # One request per year: a single getRegion over the whole daily record
    # exceeds Earth Engine's user memory limit (observed 2026-11-11).
    # Requests run in parallel threads (the EE client only waits on HTTP).
    y0, y1 = int(start[:4]), int(end[:4])
    jobs = [(cid, y) for cid in SMAP_IDS for y in range(max(y0, 2015), y1)]

    def one(job):
        cid, y = job
        coll = ee.ImageCollection(cid).filterDate(max(start, f"{y}-01-01"), min(end, f"{y + 1}-01-01"))
        return _region_rows(coll, pt, 9000, ["soil_moisture_am", "retrieval_qual_flag_am"])

    with ThreadPoolExecutor(max_workers=8) as pool:
        parts = list(pool.map(one, jobs))
    out: dict[str, list] = {cid: [] for cid in SMAP_IDS}
    for (cid, _), rows in zip(jobs, parts):
        out[cid] += rows
    return {"ids": list(SMAP_IDS), "units": "m3/m3 (volume fraction)",
            "qa": "retrieval_qual_flag_am == 0 (Pass)", "columns": ["time_ms", "sm", "flag"],
            "versions": out}


def _imerg(ee, pt, start: str, end: str) -> dict:
    coll = ee.ImageCollection(IMERG_MONTHLY_ID).filterDate(start, end)
    rows = _region_rows(coll, pt, 11132, ["precipitation"])
    return {"id": IMERG_MONTHLY_ID, "units": "mm/h (monthly mean rate)",
            "columns": ["time_ms", "precip_mm_h"], "rows": rows}


def _slope(ee, lat: float, lon: float) -> dict:
    cell = ee.Geometry.Rectangle([lon - CELL_HALF_DEG, lat - CELL_HALF_DEG,
                                  lon + CELL_HALF_DEG, lat + CELL_HALF_DEG])
    dem = ee.Image(DEM_ID).select("elevation")
    img = ee.Terrain.slope(dem).rename("slope_deg").addBands(dem)
    pct = ee.Reducer.percentile([10, 50, 90])
    stats = img.reduceRegion(ee.Reducer.mean().combine(pct, sharedInputs=True),
                             cell, scale=30, maxPixels=1e8, bestEffort=True).getInfo()
    # Plane z = c0 + cx * east_m + cy * north_m fitted to the cell (least squares): the main
    # fall direction of the cell, for contour (across-slope) rows (docs/METHOD.md).
    ll = ee.Image.pixelLonLat()
    east = ll.select("longitude").subtract(lon).multiply(111320 * math.cos(math.radians(lat)))
    north = ll.select("latitude").subtract(lat).multiply(111320)
    design = ee.Image.constant(1).addBands(east).addBands(north).addBands(dem.toFloat())
    fit = design.reduceRegion(ee.Reducer.linearRegression(numX=3, numY=1), cell, scale=30,
                              maxPixels=1e8, bestEffort=True).getInfo()
    coef = (fit or {}).get("coefficients")
    plane = {"dz_de": coef[1][0], "dz_dn": coef[2][0]} if coef else None
    return {"id": DEM_ID, "units": "degrees", "elevation_units": "m (EGM96)", "stats": stats, "plane": plane}


def _phenology(ee, pt, start: str, end: str) -> dict:
    """MCD12Q2 yearly phenology at the 500 m pixel (band meanings: STAC entry, DATA_SOURCES §4)."""
    coll = ee.ImageCollection(PHENOLOGY_ID).filterDate(start, end)
    rows = _region_rows(coll, pt, 500, PHENOLOGY_BANDS)
    return {"id": PHENOLOGY_ID, "doi": "10.5067/MODIS/MCD12Q2.061",
            "units": "dates as days since 1970-01-01; EVI2 amplitude unitless",
            "columns": ["time_ms", *PHENOLOGY_BANDS], "rows": rows}


def _chirps(ee, pt, start: str, end: str) -> dict:
    """CHIRPS daily rain summed to calendar months on the server (one request)."""
    col = ee.ImageCollection(CHIRPS_ID).select("precipitation")
    y0, y1 = int(start[:4]), int(end[:4]) - 1
    months = ee.List([[y, m] for y in range(y0, y1 + 1) for m in range(1, 13)])

    def one(ym):
        ym = ee.List(ym)
        t0 = ee.Date.fromYMD(ee.Number(ym.get(0)), ee.Number(ym.get(1)), 1)
        coll = col.filterDate(t0, t0.advance(1, "month"))
        v = ee.Algorithms.If(coll.size().gt(0),
                             coll.sum().reduceRegion(ee.Reducer.first(), pt, scale=5566).get("precipitation"),
                             None)
        return ee.Feature(None, {"ym": t0.format("YYYY-MM"), "mm": v, "n": coll.size()})

    fc = ee.FeatureCollection(months.map(one))
    cols = ee.Dictionary({k: fc.aggregate_array(k) for k in ("ym", "n")}).getInfo()
    mm = fc.toList(fc.size()).map(lambda f: ee.Feature(f).get("mm")).getInfo()
    rows = [[ym, v] for ym, v, n in zip(cols["ym"], mm, cols["n"]) if n and v is not None]
    return {"id": CHIRPS_ID, "units": "mm/month (sum of daily mm)", "columns": ["month", "precip_mm"],
            "rows": rows}


LAYERS = ("ndvi", "smap", "imerg", "slope", "phenology", "chirps")


def fetch_raw(lat: float, lon: float, first_year: int, last_year: int,
              layers: tuple[str, ...] = LAYERS) -> dict:
    """Live extraction. Per-layer errors are recorded, not raised."""
    initialize()
    ee = _ee()
    pt = ee.Geometry.Point([lon, lat])
    start, end = f"{first_year}-01-01", f"{last_year + 1}-01-01"
    fns = {"ndvi": lambda: _ndvi(ee, pt, start, end),
           "smap": lambda: _smap(ee, pt, start, end),
           "imerg": lambda: _imerg(ee, pt, start, end),
           "slope": lambda: _slope(ee, lat, lon),
           "phenology": lambda: _phenology(ee, pt, start, end),
           "chirps": lambda: _chirps(ee, pt, start, end)}
    raw: dict = {"schema": SCHEMA, "lat": lat, "lon": lon, "period": [start, end], "layers": {}, "errors": {}}

    def run(name):
        try:
            return name, fns[name](), None
        except Exception as e:  # noqa: BLE001 - EE raises many exception types
            return name, None, str(e)[:500]

    with ThreadPoolExecutor(max_workers=len(layers)) as pool:
        for name, value, err in pool.map(run, layers):
            if err is None:
                raw["layers"][name] = value
            else:
                raw["errors"][name] = err
    return raw


def demo_cache_file(demo_dir: Path, lat: float, lon: float) -> Path:
    return demo_dir / f"gee_{lat:.2f}_{lon:.2f}.json.gz"


def load_point(lat: float, lon: float, first_year: int, last_year: int,
               cache: ResponseCache | None = None, demo_dir: Path | None = None) -> tuple[dict, str]:
    """Raw layers for a rounded point. Order: SQLite cache, Earth Engine, demo cache.

    Returns (raw, origin). Results with layer errors are not cached.
    """
    key = cache_key("gee_point", lat, lon, start=first_year, end=last_year, schema=SCHEMA)
    if cache is not None and (hit := cache.get(key)) is not None:
        return hit, "cache"
    if demo_cache_first() and demo_dir is not None and (f := demo_cache_file(demo_dir, lat, lon)).exists():
        return json.loads(gzip.decompress(f.read_bytes())), "demo_cache"
    try:
        raw = fetch_raw(lat, lon, first_year, last_year)
    except SourceError as live_error:
        if demo_dir is not None and (f := demo_cache_file(demo_dir, lat, lon)).exists():
            return json.loads(gzip.decompress(f.read_bytes())), "demo_cache"
        raise live_error
    if raw["errors"] and demo_dir is not None and (f := demo_cache_file(demo_dir, lat, lon)).exists():
        return json.loads(gzip.decompress(f.read_bytes())), "demo_cache"
    if cache is not None and not raw["errors"]:
        cache.put(key, raw)
    return raw, "earth_engine"


def load_layer(lat: float, lon: float, layer: str, first_year: int, last_year: int,
               cache: ResponseCache | None = None, demo_dir: Path | None = None) -> tuple[dict, str]:
    """One layer only (fast; e.g. CHIRPS for the rain check). Order: SQLite cache, Earth Engine,
    demo cache. Returns (layer, origin); raises SourceError with the reason if unavailable."""
    key = cache_key(f"gee_{layer}", lat, lon, start=first_year, end=last_year, schema=SCHEMA)
    if cache is not None and (hit := cache.get(key)) is not None:
        return hit, "cache"
    demo = None
    if demo_dir is not None and (f := demo_cache_file(demo_dir, lat, lon)).exists():
        demo = json.loads(gzip.decompress(f.read_bytes()))["layers"].get(layer)
    if demo_cache_first() and demo is not None:
        return demo, "demo_cache"
    try:
        raw = fetch_raw(lat, lon, first_year, last_year, layers=(layer,))
        if layer in raw["errors"]:
            raise SourceError(raw["errors"][layer])
    except SourceError as e:
        if demo is not None:
            return demo, "demo_cache"
        raise e
    out = raw["layers"][layer]
    if cache is not None:
        cache.put(key, out)
    return out, "earth_engine"


def load_slope(lat: float, lon: float, cache: ResponseCache | None = None,
               demo_dir: Path | None = None) -> tuple[dict | None, str, str | None]:
    """Slope layer only (fast, for the rotation engine). Returns (layer, origin, error)."""
    key = cache_key("gee_slope_v2", lat, lon, schema=SCHEMA)  # v2: with the plane fit (2026-11-14)
    if cache is not None and (hit := cache.get(key)) is not None:
        return hit, "cache", None
    if demo_dir is not None and (f := demo_cache_file(demo_dir, lat, lon)).exists():
        demo = json.loads(gzip.decompress(f.read_bytes()))["layers"].get("slope")
    else:
        demo = None
    if demo_cache_first() and demo is not None:
        return demo, "demo_cache", None
    try:
        raw = fetch_raw(lat, lon, 2000, 2000, layers=("slope",))
        if "slope" in raw["errors"]:
            raise SourceError(raw["errors"]["slope"])
    except SourceError as e:
        return (demo, "demo_cache", str(e)) if demo else (None, "none", str(e))
    layer = raw["layers"]["slope"]
    if cache is not None:
        cache.put(key, layer)
    return layer, "earth_engine", None
