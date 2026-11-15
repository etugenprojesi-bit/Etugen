"""Observed regional crop calendar (GGCMI Phase 3) — the local sowing practice.

Ray, D., Jägermeyr, J., Minoli, S., Siebert, S., Müller, C. (2021). GGCMI Phase 3
crop calendar. Zenodo, doi:10.5281/zenodo.5062513, CC BY 4.0; method in
Jägermeyr et al. (2021), Nature Food 2:873-885. Built into
data/ggcmi_crop_calendar.npz by scripts/build_crop_calendar.py.

Static multi-year planting and maturity day of year per 0.5° cell, rainfed and
irrigated; merged from national statistics, SAGE, MIRCA2000 and others, and
extrapolated outside cropland (docs/DATA_SOURCES.md §8).

Rule (decision K1-a, docs/METHOD.md "Local sowing calendar"): when a crop has a
calendar here, its best sowing window is chosen among windows within
WINDOW_DAYS of the local planting day; other windows stay visible and are
labelled. The user can switch the rule off ("explore sowing dates").
"""

from __future__ import annotations

from datetime import date
from functools import lru_cache
from pathlib import Path

import numpy as np

DATA_FILE = Path("data") / "ggcmi_crop_calendar.npz"
WINDOW_DAYS = 45  # assumption: GGCMI is a multi-year average; real sowing shifts between years

# crops.yaml id -> GGCMI crop code (file names of the Zenodo record)
GGCMI_CODES = {
    "winter_wheat": "wwh", "spring_wheat": "swh", "barley": "bar", "maize_grain": "mai",
    "sorghum_grain": "sor", "millet": "mil", "rice": "ri1", "soybean": "soy", "dry_bean": "bea",
    "groundnut": "nut", "sunflower": "sun", "rapeseed": "rap", "potato": "pot", "cassava": "cas",
    "cotton": "cot", "sugar_beet": "sgb", "dry_pea": "pea",
}
SOURCES = {1: "MIRCA2000", 2: "SAGE", 3: "Iizumi et al. 2019", 4: "RiceAtlas", 5: "Dimou et al. 2018",
           6: "ChinaCropPhen", 7: "India agricultural statistics", 8: "Brazil CONAB", 9: "Australia ABARES"}
ATTRIBUTION = "GGCMI Phase 3 crop calendar (Ray, Jägermeyr et al. 2021, CC BY 4.0)"


@lru_cache
def _load(path: str) -> dict[str, np.ndarray] | None:
    p = Path(path)
    if not p.exists():
        return None
    with np.load(p) as z:
        return {k: z[k] for k in z.files}


def system_for(irrigation: str) -> str:
    """Irrigated calendar only with full irrigation (assumption: "limited" farms follow the rainfed calendar)."""
    return "ir" if irrigation == "full" else "rf"


def lookup(data_dir: Path, crop_id: str, lat: float, lon: float, irrigation: str = "none") -> dict | None:
    """Local calendar of a crop at the nearest 0.5° cell, or None (no data / crop not covered).

    Source rule (decision K1, docs/drafts/plan_ggcmi_takvim.md): GGCMI marks the data source
    of every cell (`data_source_used`); 0 = no named source, i.e. gap-filled or extrapolated.
    When the requested system (rainfed / irrigated) is gap-filled at this cell but the other
    system has a named source, the other system's calendar is used (labelled `fallback_from`).
    Otherwise the value is used as it is and labelled `gap_filled`."""
    code = GGCMI_CODES.get(crop_id)
    grids = _load(str(data_dir / DATA_FILE.name)) if code else None
    if grids is None:
        return None
    lat_a, lon_a = grids["lat"], grids["lon"]
    lon = ((lon + 180.0) % 360.0) - 180.0
    i = int(np.argmin(np.abs(lat_a - lat)))
    j = int(np.argmin(np.abs(lon_a - lon)))
    wanted = system_for(irrigation)

    def cell(system: str) -> tuple[int, int, int]:
        return tuple(int(grids[f"{code}_{system}_{k}"][i, j]) for k in ("plant", "mature", "source"))

    system = wanted
    plant, mature, source = cell(system)
    other = "rf" if wanted == "ir" else "ir"
    o_plant, o_mature, o_source = cell(other)
    fallback = False
    if (plant == 0 or mature == 0 or source == 0) and o_plant and o_mature and o_source:
        system, plant, mature, source, fallback = other, o_plant, o_mature, o_source, True
    if plant == 0 or mature == 0:
        return None
    return {
        "ggcmi_crop": code, "system": "irrigated" if system == "ir" else "rainfed",
        "fallback_from": ("irrigated" if wanted == "ir" else "rainfed") if fallback else None,
        "gap_filled": source == 0,
        "planting_doy": plant, "maturity_doy": mature,
        "planting": _mmdd(plant), "maturity": _mmdd(mature),
        "cell": {"lat": round(float(lat_a[i]), 2), "lon": round(float(lon_a[j]), 2)},
        "data_source": SOURCES.get(source, "unknown"), "window_days": WINDOW_DAYS,
        "attribution": ATTRIBUTION,
    }


def _mmdd(doy: int) -> str:
    d = date.fromordinal(date(2001, 1, 1).toordinal() + doy - 1)
    return f"{d.month:02d}-{d.day:02d}"


def days_apart(sowing_mmdd: str, doy: int) -> int:
    """Circular distance in days between a sowing date "MM-DD" and a day of year."""
    m, d = map(int, sowing_mmdd.split("-"))
    s = date(2001, m, d).timetuple().tm_yday
    diff = abs(s - doy) % 365
    return min(diff, 365 - diff)
