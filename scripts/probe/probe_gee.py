"""Probe: Google Earth Engine live access (requires credentials).

Dataset IDs and band names come from probe_gee_catalog.py (official STAC
catalog), not from memory. For each dataset we run one small server-side
reduction in a 1 km buffer around the Konya demo point and time it; only
summary numbers come back to the client.

Setup (once):
    backend/.venv/Scripts/earthengine authenticate
    set EE_PROJECT=<your-cloud-project> in .env
Run: backend/.venv/Scripts/python scripts/probe/probe_gee.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import ee

from _common import DEMO_POINTS, Timer, report, save

ROOT = Path(__file__).resolve().parents[2]


def load_env() -> None:
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


# Read-only scopes we actually need. `earthengine authenticate` also asks for
# Drive; if the user leaves that box unticked, refreshing with the stored
# scope list fails with "invalid_scope". We never touch Drive, so we refresh
# with these two scopes only.
EE_SCOPES = [
    "https://www.googleapis.com/auth/earthengine.readonly",
    "https://www.googleapis.com/auth/cloud-platform.read-only",
]


def user_credentials():
    """Credentials from `earthengine authenticate`, limited to EE_SCOPES."""
    from ee import oauth
    import google.oauth2.credentials

    args = oauth.get_credentials_arguments()
    args.pop("scopes", None)
    args.pop("quota_project_id", None)
    return google.oauth2.credentials.Credentials(None, scopes=EE_SCOPES, **args)


def init() -> None:
    load_env()
    project = os.environ.get("EE_PROJECT")
    key = os.environ.get("EE_SERVICE_ACCOUNT_KEY")
    if not project:
        print("[WAIT] Earth Engine: EE_PROJECT is not set in .env")
        sys.exit(2)
    try:
        if key:
            creds = ee.ServiceAccountCredentials(None, key_file=key)
            ee.Initialize(creds, project=project)
        else:
            ee.Initialize(user_credentials(), project=project)
    except Exception as e:  # noqa: BLE001 - surface any auth/setup problem verbatim
        print(f"[WAIT] Earth Engine: initialisation failed: {e}")
        sys.exit(2)


def region_mean(img: ee.Image, geom: ee.Geometry, scale: float) -> ee.Dictionary:
    return img.reduceRegion(ee.Reducer.mean(), geom, scale=scale, bestEffort=True, maxPixels=1e8)


def checks(pt: ee.Geometry, buf: ee.Geometry) -> dict[str, callable]:
    year = ee.Filter.date("2024-01-01", "2025-01-01")
    return {
        "MODIS/061/MOD13Q1 NDVI (2024 count, mean)": lambda: ee.Dictionary({
            "n": ee.ImageCollection("MODIS/061/MOD13Q1").filter(year).size(),
            "mean": region_mean(ee.ImageCollection("MODIS/061/MOD13Q1").filter(year)
                                .select("NDVI").mean().multiply(0.0001), buf, 250),
        }),
        "NASA/HLS/HLSL30/v002 + HLSS30 (2024 scenes)": lambda: ee.Dictionary({
            "L30": ee.ImageCollection("NASA/HLS/HLSL30/v002").filter(year).filterBounds(pt).size(),
            "S30": ee.ImageCollection("NASA/HLS/HLSS30/v002").filter(year).filterBounds(pt).size(),
        }),
        "NASA/SMAP/SPL3SMP_E/006 soil_moisture_am (2024)": lambda: region_mean(
            ee.ImageCollection("NASA/SMAP/SPL3SMP_E/006").filter(year)
            .select(["soil_moisture_am", "soil_moisture_am_anomaly"]).mean(), pt.buffer(9000), 9000),
        "NASA/GPM_L3/IMERG_MONTHLY_V07 precipitation (2024 mean mm/h)": lambda: region_mean(
            ee.ImageCollection("NASA/GPM_L3/IMERG_MONTHLY_V07").filter(year)
            .select("precipitation").mean(), pt.buffer(11000), 11132),
        "NASA/GRACE/MASS_GRIDS_V04/MASCON_CRI lwe_thickness (latest)": lambda: ee.Dictionary({
            "n": ee.ImageCollection("NASA/GRACE/MASS_GRIDS_V04/MASCON_CRI").size(),
            "last": region_mean(ee.ImageCollection("NASA/GRACE/MASS_GRIDS_V04/MASCON_CRI")
                                .sort("system:time_start", False).first(), pt.buffer(30000), 55660),
        }),
        "NASA/NASADEM_HGT/001 slope (deg)": lambda: region_mean(
            ee.Terrain.slope(ee.Image("NASA/NASADEM_HGT/001").select("elevation")), buf, 30),
        "NASA/ECOSTRESS/L2T_LSTE/V2 LST (2024 scenes)": lambda: ee.Dictionary({
            "n": ee.ImageCollection("NASA/ECOSTRESS/L2T_LSTE/V2").filter(year).filterBounds(pt).size(),
        }),
        "LARSE/GEDI/GEDI04_B_002 MU (agbd Mg/ha)": lambda: region_mean(
            ee.Image("LARSE/GEDI/GEDI04_B_002").select("MU"), pt.buffer(1000), 1000),
        "MODIS/061/MOD11A2 LST_Day_1km (2024 mean K)": lambda: region_mean(
            ee.ImageCollection("MODIS/061/MOD11A2").filter(year).select("LST_Day_1km")
            .mean().multiply(0.02), buf, 1000),
        "ISRIC/SoilGrids250m/v2_0 (first image, 0-5cm mean)": lambda: ee.Dictionary({
            "n_images": ee.ImageCollection("ISRIC/SoilGrids250m/v2_0").size(),
            "first_id": ee.ImageCollection("ISRIC/SoilGrids250m/v2_0").first().get("system:index"),
            "val": region_mean(ee.ImageCollection("ISRIC/SoilGrids250m/v2_0").first()
                               .select("val_0_5cm_mean"), buf, 250),
        }),
    }


def main() -> None:
    init()
    p = DEMO_POINTS["konya"]
    pt = ee.Geometry.Point([p["lon"], p["lat"]])
    buf = pt.buffer(1000)
    results, ok_all = {}, True
    for name, fn in checks(pt, buf).items():
        try:
            with Timer() as t:
                value = fn().getInfo()
            results[name] = value
            report(f"EE {name}", True, {"seconds": f"{t.seconds:.1f}", "value": value})
        except Exception as e:  # noqa: BLE001
            ok_all = False
            results[name] = {"error": str(e)}
            report(f"EE {name}", False, {"error": str(e)[:300]})
    save("gee_live_konya.json", results)
    raise SystemExit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
