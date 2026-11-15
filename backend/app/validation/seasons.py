"""Validation of model seasons against satellite phenology (improvement step 5).

A diagnostic, not a calibration: nothing here changes a suitability score.
Plan and decisions: docs/drafts/plan_ndvi_dogrulama.md (K1-a, K2-a); method:
docs/METHOD.md "Season validation (MODIS)".

* Satellite seasons: MODIS MCD12Q2 v6.1 (doi:10.5067/MODIS/MCD12Q2.061), up to
  two vegetation cycles per year at the 500 m pixel; `MidGreenup`, `Peak` and
  `MidGreendown` are the product's own 50 % / maximum EVI2-amplitude dates.
* Cross-check: the same 50 % rule applied to MOD13Q1 NDVI (1 km mean).
* Model seasons: the suitability engine sown at the local GGCMI planting day,
  so season *length* is tested, not the choice of sowing window.
* Matching (assumption): the satellite cycle whose peak lies between sowing and
  maturity + MATCH_TAIL_DAYS; with two candidates the larger amplitude wins.
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

from app.suitability.crops import Crop
from app.suitability.engine import SOWING_DATES, ClimateArrays, season_rows

EPOCH = date(1970, 1, 1)
MATCH_TAIL_DAYS = 45   # assumption: the green-down may follow maturity by up to ~6 weeks
HALF = 0.5             # 50 % of the amplitude, as MCD12Q2 MidGreenup / MidGreendown
QA_MAX = 2             # QA_Overall classes (STAC): 0 Best, 1 Good, 2 Fair, 3 Poor; dropping Poor is our choice


def _day(v) -> date | None:
    return None if v is None else EPOCH + timedelta(days=int(v))


def parse_phenology(layer: dict) -> list[dict]:
    """MCD12Q2 rows -> list of cycles {year, cycle, greenup, peak, greendown, amplitude, qa}."""
    cols = layer["columns"]
    out = []
    for r in layer["rows"]:
        d = dict(zip(cols, r))
        year = pd.Timestamp(d["time_ms"], unit="ms").year
        for n in (1, 2):
            peak = _day(d.get(f"Peak_{n}"))
            qa = d.get(f"QA_Overall_{n}")
            if peak is None or (qa is not None and qa > QA_MAX):
                continue
            out.append({"year": year, "cycle": n, "greenup": _day(d.get(f"MidGreenup_{n}")), "peak": peak,
                        "greendown": _day(d.get(f"MidGreendown_{n}")),
                        "amplitude": d.get(f"EVI_Amplitude_{n}"), "qa": qa})
    return out


def match_cycle(cycles: list[dict], sowing: date, maturity: date) -> dict | None:
    end = maturity + timedelta(days=MATCH_TAIL_DAYS)
    cand = [c for c in cycles if sowing <= c["peak"] <= end]
    if not cand:
        return None
    return max(cand, key=lambda c: c["amplitude"] or 0.0)


def ndvi_half_amplitude(ndvi: pd.Series, start: date, end: date) -> dict | None:
    """50 % green-up / peak / green-down of a daily NDVI series inside [start, end]
    (cross-check with the MCD12Q2 definition, applied to MOD13Q1 NDVI)."""
    w = ndvi[pd.Timestamp(start): pd.Timestamp(end)].dropna()
    if len(w) < 30:
        return None
    t_peak = w.idxmax()
    pre, post = w[:t_peak], w[t_peak:]
    lo_pre, lo_post, top = pre.min(), post.min(), w.max()
    if top - max(lo_pre, lo_post) < 0.1:  # assumption: < 0.1 NDVI is no clear cycle
        return None
    rise = pre[pre.idxmin():]
    up = rise[rise >= lo_pre + HALF * (top - lo_pre)]
    down = post[post <= lo_post + HALF * (top - lo_post)]
    return {"greenup": up.index[0].date() if len(up) else None, "peak": t_peak.date(),
            "greendown": down.index[0].date() if len(down) else None}


def nearest_sowing_date(doy: int) -> tuple[int, int]:
    def dist(md):
        d = abs(pd.Timestamp(2001, *md).day_of_year - doy)
        return min(d, 365 - d)
    return min(SOWING_DATES, key=dist)


def _q(x: list[float], q: float) -> float | None:
    return None if not x else float(np.percentile(x, q))


def compare(crop: Crop, clim: ClimateArrays, planting_doy: int, irrigation: str,
            cycles: list[dict], ndvi: pd.Series | None = None) -> dict:
    """Per-year model vs satellite dates and a summary (days; positive = model later)."""
    m, d = nearest_sowing_date(planting_doy)
    key = f"{m:02d}-{d:02d}"
    rows = season_rows(crop, clim, irrigation, sowing_dates=[(m, d)]).get(key, [])
    f_ini, f_dev, f_mid, _ = crop.stages.fractions()
    years = []
    for r in rows:
        if not r["matured"]:
            continue
        sow = clim.dates[r["i0"]].date()
        mat = clim.dates[r["i1"] - 1].date()
        mid = sow + timedelta(days=round(r["days"] * (f_ini + f_dev + f_mid / 2)))
        c = match_cycle(cycles, sow, mat)
        row = {"year": sow.year, "sowing": sow, "maturity": mat, "mid_season": mid,
               "sat_peak": c["peak"] if c else None, "sat_greendown": c["greendown"] if c else None}
        if ndvi is not None:
            h = ndvi_half_amplitude(ndvi, sow - timedelta(days=15), mat + timedelta(days=MATCH_TAIL_DAYS))
            row["ndvi_greendown"] = h["greendown"] if h else None
        years.append(row)
    dm = [(y["maturity"] - y["sat_greendown"]).days for y in years if y["sat_greendown"]]
    dp = [(y["mid_season"] - y["sat_peak"]).days for y in years if y["sat_peak"]]
    dn = [(y["maturity"] - y["ndvi_greendown"]).days for y in years if y.get("ndvi_greendown")]
    pairs = [(y["maturity"].timetuple().tm_yday, y["sat_greendown"].timetuple().tm_yday)
             for y in years if y["sat_greendown"]]
    rho = (float(pd.Series([a for a, _ in pairs]).corr(pd.Series([b for _, b in pairs]), method="spearman"))
           if len(pairs) >= 8 else None)  # assumption: >= 8 matched years for a correlation
    return {
        "crop": crop.id, "irrigation": irrigation, "sowing": key,
        "n_seasons": len(years), "n_matched": len(dm),
        "maturity_minus_greendown_days": {"median": _q(dm, 50), "p25": _q(dm, 25), "p75": _q(dm, 75)},
        "midseason_minus_peak_days": {"median": _q(dp, 50), "p25": _q(dp, 25), "p75": _q(dp, 75)},
        "maturity_minus_ndvi_greendown_days": {"median": _q(dn, 50), "n": len(dn)},
        "interannual_spearman": None if rho is None or np.isnan(rho) else round(rho, 2),
        "years": years,
    }
