"""Probe: ISRIC SoilGrids v2.0 REST point query (no authentication).

Run: backend/.venv/Scripts/python scripts/probe/probe_soilgrids.py
"""

from __future__ import annotations

import httpx

from _common import DEMO_POINTS, Timer, report, save

URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"
PROPERTIES = ["clay", "sand", "silt", "phh2o", "soc", "bdod", "cec"]
DEPTHS = ["0-5cm", "5-15cm", "15-30cm"]
VALUES = ["mean", "Q0.05", "Q0.95", "uncertainty"]


def main() -> None:
    ok_all = True
    with httpx.Client(timeout=60) as client:
        for key, p in DEMO_POINTS.items():
            params = [("lon", p["lon"]), ("lat", p["lat"])]
            params += [("property", x) for x in PROPERTIES]
            params += [("depth", x) for x in DEPTHS]
            params += [("value", x) for x in VALUES]
            try:
                with Timer() as t:
                    r = client.get(URL, params=params)
                r.raise_for_status()
            except httpx.HTTPError as e:
                ok_all = False
                report(f"SoilGrids {key}", False, {"error": repr(e)})
                continue
            data = r.json()
            save(f"soilgrids_{key}.json", data)
            summary = {}
            for layer in data["properties"]["layers"]:
                um = layer["unit_measure"]
                top = layer["depths"][0]
                summary[layer["name"]] = (
                    f"{top['label']} mean={top['values'].get('mean')} "
                    f"(d_factor={um.get('d_factor')}, {um.get('target_units')})"
                )
            report(f"SoilGrids {key}", True, {
                "seconds": f"{t.seconds:.1f}",
                "coordinates": data.get("geometry", {}).get("coordinates"),
                **summary,
            })
    raise SystemExit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
