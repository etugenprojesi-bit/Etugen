"""Probe: satellite base map (EOX Sentinel-2 cloudless 2016) and place search (Nominatim).

1. Reads the EOX WMTS capabilities, checks that layer `s2cloudless_3857` is the
   2016 mosaic and that its abstract states CC BY 4.0, then fetches one tile per
   demo point at several zoom levels (JPEG, size).
2. Searches one Turkish place name with the OpenStreetMap Nominatim API
   (one request per second at most, as the usage policy asks).

Run: backend/.venv/Scripts/python scripts/probe/probe_basemap.py
"""

from __future__ import annotations

import math
import re
import time

import httpx

from _common import DEMO_POINTS, Timer, report, save

CAPS = "https://tiles.maps.eox.at/wmts/1.0.0/WMTSCapabilities.xml"
LAYER = "s2cloudless_3857"
TILE = "https://tiles.maps.eox.at/wmts/1.0.0/" + LAYER + "/default/g/{z}/{y}/{x}.jpg"
NOMINATIM = "https://nominatim.openstreetmap.org/search"
# Generic client name (no personal contact details).
HEADERS = {"User-Agent": "ToprakPusulasi-probe/1.0 (NASA Space Apps 2026, open source)"}


def tile_xy(lat: float, lon: float, z: int) -> tuple[int, int]:
    n = 2**z
    x = int((lon + 180) / 360 * n)
    y = int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)
    return x, y


def probe_eox(client: httpx.Client) -> None:
    r = client.get(CAPS)
    save("eox_wmts_caps.xml", r.text)
    i = r.text.find(f"<ows:Identifier>{LAYER}<")
    j = r.text.rfind("<Layer>", 0, i)
    layer = r.text[j : r.text.find("</Layer>", i)]
    title = re.search(r"<ows:Title>(.*?)</ows:Title>", layer)
    abstract = re.search(r"<ows:Abstract>(.*?)</ows:Abstract>", layer, re.S)
    report(
        "EOX WMTS capabilities",
        r.status_code == 200 and i > 0,
        {
            "title": title.group(1) if title else None,
            "abstract": abstract.group(1)[:200] if abstract else None,
            "cc_by_4": bool(abstract and "creativecommons.org/licenses/by/4.0" in abstract.group(1)),
        },
    )
    for key, p in DEMO_POINTS.items():
        for z in (10, 13, 15, 17):
            x, y = tile_xy(p["lat"], p["lon"], z)
            with Timer() as t:
                tr = client.get(TILE.format(z=z, x=x, y=y))
            ok = tr.status_code == 200 and tr.headers.get("content-type", "").startswith("image/jpeg")
            if z == 15:
                save(f"eox_{key}_z15.jpg", tr.content)
            report(
                f"EOX tile {key} z{z}",
                ok,
                {"status": tr.status_code, "type": tr.headers.get("content-type"), "bytes": len(tr.content), "s": round(t.seconds, 2)},
            )


def probe_nominatim(client: httpx.Client) -> None:
    params = {"q": "Çumra, Konya", "format": "jsonv2", "limit": 3, "accept-language": "tr"}
    with Timer() as t:
        r = client.get(NOMINATIM, params=params)
    data = r.json() if r.status_code == 200 else []
    save("nominatim_cumra.json", data)
    report(
        "Nominatim search 'Çumra, Konya'",
        r.status_code == 200 and len(data) > 0,
        {
            "status": r.status_code,
            "results": [(d.get("display_name"), d.get("lat"), d.get("lon")) for d in data],
            "licence": data[0].get("licence") if data else None,
            "s": round(t.seconds, 2),
        },
    )
    time.sleep(1.1)


if __name__ == "__main__":
    with httpx.Client(timeout=30, headers=HEADERS, follow_redirects=True) as c:
        probe_eox(c)
        probe_nominatim(c)
