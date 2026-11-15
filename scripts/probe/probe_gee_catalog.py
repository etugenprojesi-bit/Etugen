"""Probe: verify Earth Engine dataset IDs against the public EE STAC catalog.

No authentication is needed for the catalog itself. For each topic we list
every catalog collection whose id matches, with version, temporal extent,
resolution, license and deprecation flag, so IDs are never taken from memory.

Run: backend/.venv/Scripts/python scripts/probe/probe_gee_catalog.py
"""

from __future__ import annotations

import asyncio
import re

import httpx

from _common import report, save

ROOT = "https://storage.googleapis.com/earthengine-stac/catalog/catalog.json"
PROVIDERS = {"NASA", "MODIS", "LANDSAT", "USGS", "LARSE", "NASA_USDA", "ISRIC",
             "OpenLandMap", "JAXA", "CGIAR", "ECMWF"}
TOPICS = {
    "MODIS NDVI": r"^MODIS/06\d/M[OY]D13Q1$",
    "MODIS LST": r"^MODIS/06\d/M[OY]D11A[12]$",
    "MODIS ET": r"^MODIS/06\d/MOD16A2",
    "HLS": r"^NASA/HLS/",
    "Landsat C2 L2": r"^LANDSAT/L[CE]0[789]/C02/T1_L2$",
    "SMAP": r"SMAP",
    "GPM IMERG": r"GPM_L3/IMERG",
    "GRACE": r"GRACE",
    "SRTM / NASADEM": r"SRTM|NASADEM",
    "ECOSTRESS": r"ECOSTRESS|ECO",
    "GEDI": r"GEDI",
    "SoilGrids / soil": r"SoilGrids|isric|OpenLandMap/SOL",
}
PREFILTER = (r"MOD13Q1|MYD13Q1|MOD11A|MYD11A|MOD16A2|HLS|LC08_C02_T1_L2|LC09_C02_T1_L2|"
             r"LE07_C02_T1_L2|SMAP|GPM|IMERG|GRACE|SRTM|NASADEM|ECOSTRESS|GEDI|SoilGrids|SOL_")


async def fetch(client: httpx.AsyncClient, url: str) -> dict:
    r = await client.get(url)
    r.raise_for_status()
    return r.json()


def summarise(c: dict) -> dict:
    ext = c.get("extent", {}).get("temporal", {}).get("interval", [[None, None]])[0]
    summ = c.get("summaries", {})
    gsd = summ.get("gsd")
    if gsd is None:
        gsd = sorted({b.get("gsd") for b in summ.get("eo:bands", []) if b.get("gsd")})
    return {
        "id": c["id"],
        "title": c.get("title"),
        "version": c.get("version"),
        "deprecated": c.get("deprecated", False),
        "start": ext[0],
        "end": ext[1],
        "gsd_m": gsd,
        "license": c.get("license"),
        "ee_type": c.get("gee:type"),
        "interval": c.get("gee:interval"),
        "terms": (c.get("gee:terms_of_use") or "")[:300],
        "bands": [b.get("name") for b in summ.get("eo:bands", [])][:25],
    }


async def main() -> None:
    async with httpx.AsyncClient(timeout=60, limits=httpx.Limits(max_connections=16)) as client:
        root = await fetch(client, ROOT)
        children = [l["href"] for l in root["links"]
                    if l["rel"] == "child" and l.get("title") in PROVIDERS]
        catalogs = await asyncio.gather(*(fetch(client, h) for h in children))
        links = [l for cat in catalogs for l in cat["links"] if l["rel"] == "child"]
        # Hrefs only loosely encode the id (.../NASA/NASA_GPM_L3_IMERG_V07.json), so
        # pre-filter on keywords and match TOPICS against the real "id" field below.
        wanted = [l["href"] for l in links if re.search(PREFILTER, l["href"], re.IGNORECASE)]
        collections = await asyncio.gather(*(fetch(client, h) for h in sorted(set(wanted))),
                                           return_exceptions=True)

    found: dict[str, list[dict]] = {t: [] for t in TOPICS}
    for c in collections:
        if isinstance(c, Exception):
            continue
        s = summarise(c)
        for topic, rx in TOPICS.items():
            if re.search(rx, s["id"], re.IGNORECASE if topic.startswith("Soil") else 0):
                found[topic].append(s)
                break
    save("gee_catalog.json", found)
    for topic, items in found.items():
        report(f"EE catalog: {topic}", bool(items), {
            s["id"]: f"v={s['version']} {s['start']}..{s['end']} gsd={s['gsd_m']} "
                     f"interval={s['interval']} deprecated={s['deprecated']} license={s['license']}"
            for s in items
        } or {"note": "no matching collection in the official catalog"})


if __name__ == "__main__":
    asyncio.run(main())
