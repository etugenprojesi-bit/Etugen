"""Crop suitability and planting windows from daily climate (stage 1).

For every crop, every candidate sowing date (1st and 16th of each month) and
every year of the record, one season is simulated:

* Season length: thermal time (SIMPLE, Zhao et al. 2019) — the season ends when
  the sum of max(0, Tmean - t_base) reaches t_sum; if t_sum is unknown, the
  FAO-56 Table 11 length is used. Crops sourced from WOFOST (Boons-Prins et al.
  1993) use their daily thermal-time table (DTSMTB) instead of max(0, Tmean -
  t_base) and a separate sowing -> emergence sum with its own base. A season fails if it does not mature within
  SEASON_LENGTH_TOLERANCE x the longest FAO-56 Table 11 season for the crop
  (e.g. a summer crop that would have to overwinter), and never exceeds 365 days.
* Temperature score: season mean of [Tmean > t_base] x the SIMPLE heat factor
  ramp_down(Tmax; t_heat -> t_ext). Days below t_base (no development in
  SIMPLE) count as lost days, so sowing into cold soil is penalised; slower
  development above t_base is already captured by the thermal-time season
  length. For crops without t_sum (fixed season length) the SIMPLE growth
  factor ramp_up(Tmean; t_base -> t_opt) is used instead of [Tmean > t_base].
* ECOCROP crops (no literature parameters; FAO ECOCROP general ranges): fixed
  FAO-56 season length; temperature score = worst ~30-day block of
  trapezoid(TMIN, TOPMN, TOPMX, TMAX) on the block mean temperature (dismo
  ECOCROP method). Water, duration and light factors as for every crop.
* Water score: FAO-56 crop water use ETc = Kc(t) x ET0 with the FAO-56 Kc curve;
  Kc_mid and Kc_end are adjusted per season to the mean daily wind (u2) and RHmin
  of the mid / late season (FAO-56 eq. 62 / 65, app.features.kc_climate);
  rainfed deficit = sum over 10-day blocks of max(0, ETc - P);
  score = 1 - deficit / ETc. Irrigation relaxes the deficit.
* Duration factor: min(1, days / (SHORT_SEASON_FRACTION x shortest FAO-56 season)).
  Heat-accelerated, very short seasons intercept less light and yield less
  (the SIMPLE yield logic); without this a cool-season crop would rank well
  in a hot season simply because it "matures" quickly.
* Light factor (stage 5): min(1, R / R_ref), R = sum of daily solar radiation
  over the season, R_ref = median R of the matured seasons for the same sowing
  date in the reference (baseline, no scenario) climate. Crop growth is
  proportional to intercepted solar radiation (Monteith 1977, the basis of
  SIMPLE); without this factor a warmer climate that shortens the season
  would look better (less water deficit) without losing anything.
* Season score = temperature score x water score x duration factor x light factor.
* If every sowing date scores 0, the crop is "not_suitable_by_model" with the
  dominant reason — a model result to be checked locally, not a verdict.

Per sowing date the results over years give a median, a bad-year (20th
percentile) value and a failure rate. All rule/physics based, not ML.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd

from app.features.kc_climate import season_kc
from app.suitability.calendar import WINDOW_DAYS as calendar_window_days
from app.suitability.calendar import days_apart
from app.suitability.crops import Crop, Temperature
from app.suitability.membership import ramp_down, ramp_up, trapezoid

SOWING_DATES = [(m, d) for m in range(1, 13) for d in (1, 16)]
MAX_SEASON_DAYS = 365
SEASON_LENGTH_TOLERANCE = 1.25  # assumption: allow 25 % longer than the longest FAO-56 season
SHORT_SEASON_FRACTION = 0.75    # assumption: no penalty down to 75 % of the shortest FAO-56 season
DEKAD = 10
FAIL_SCORE = 0.4            # season score below this counts as a failed season
GOOD_WINDOW_MARGIN = 0.05   # sowing dates within this of the best median are "good" too ...
GOOD_WINDOW_SHARE = 0.9     # ... and at least 90 % of the best median
LIMITED_IRRIGATION_SHARE = 0.5  # assumption: "limited" irrigation covers half the deficit
IRRIGATION_MODES = ("none", "limited", "full")


@dataclass
class ClimateArrays:
    dates: pd.DatetimeIndex
    tmean: np.ndarray
    tmax: np.ndarray
    tmin: np.ndarray
    precip: np.ndarray
    et0: np.ndarray
    rad: np.ndarray | None = None  # daily solar radiation, MJ/m2/day (light factor)
    u2: np.ndarray | None = None      # daily wind speed at 2 m, m/s (Kc adjustment)
    rh_min: np.ndarray | None = None  # daily RHmin, % (FAO-56 eq. 63; Kc adjustment)

    @classmethod
    def from_frame(cls, df: pd.DataFrame) -> "ClimateArrays":
        col = (lambda c: df[c].to_numpy() if c in df else None)
        return cls(df.index, df["TMEAN"].to_numpy(), df["T2M_MAX"].to_numpy(),
                   df["T2M_MIN"].to_numpy(), df["PRECTOTCORR"].to_numpy(), df["ET0"].to_numpy(),
                   col("ALLSKY_SFC_SW_DWN"), col("WS2M"), col("RHMIN"))


def kc_curve(n_days: int, fractions: tuple[float, float, float, float],
             kc_ini: float, kc_mid: float, kc_end: float) -> np.ndarray:
    """FAO-56 single crop coefficient curve (chapter 6, Fig. 25 construction)."""
    f_ini, f_dev, f_mid, _ = fractions
    x = (np.arange(n_days) + 0.5) / n_days
    b1, b2, b3 = f_ini, f_ini + f_dev, f_ini + f_dev + f_mid
    return np.interp(x, [0.0, b1, b2, b3, 1.0], [kc_ini, kc_ini, kc_mid, kc_mid, kc_end])


def dekad_deficit(etc: np.ndarray, precip: np.ndarray) -> float:
    n = len(etc)
    edges = np.arange(0, n, DEKAD)
    etc_b = np.add.reduceat(etc, edges)
    p_b = np.add.reduceat(precip, edges)
    return float(np.maximum(etc_b - p_b, 0.0).sum())


def max_season_days(crop: Crop) -> int:
    if crop.stages is None or crop.stages.max_total is None:
        return MAX_SEASON_DAYS
    return min(MAX_SEASON_DAYS, int(round(SEASON_LENGTH_TOLERANCE * crop.stages.max_total)))


ECOCROP_BLOCK_DAYS = 30  # "monthly" mean temperature of the ECOCROP model, as 30-day blocks from sowing


def ecocrop_temperature_score(tmean_season: np.ndarray, temp: tuple[float, float, float, float]) -> float:
    """ECOCROP temperature suitability of one season (method of dismo::ecocrop, Hijmans):
    trapezoid(TMIN, TOPMN, TOPMX, TMAX) of each ~30-day mean temperature, season = worst block."""
    n_blocks = max(1, int(round(len(tmean_season) / ECOCROP_BLOCK_DAYS)))
    means = np.array([np.nanmean(b) for b in np.array_split(tmean_season, n_blocks)])
    return float(np.nanmin(trapezoid(means, *temp)))


def daily_thermal_time(t: Temperature, tmean: np.ndarray) -> np.ndarray:
    """Daily development increment (°C·d): max(0, Tmean - t_base) (SIMPLE), or the crop's
    piecewise-linear WOFOST DTSMTB table (clamped at its ends, like WOFOST's AFGEN)."""
    if t.dev_rate_table:
        xs, ys = zip(*t.dev_rate_table)
        return np.interp(tmean, xs, ys)
    return np.maximum(tmean - t.t_base, 0.0)


def _season_end(crop: Crop, gdd_cum: np.ndarray, i0: int, n_total: int, limit: int,
                em_cum: np.ndarray | None = None) -> tuple[int, bool]:
    """Index one past the last season day, and whether the crop matured within `limit` days.

    With an emergence phase (`em_cum`), t_sum is counted from the day after emergence.
    """
    t = crop.temperature
    if t is not None and t.t_sum is not None:
        start = i0
        if em_cum is not None and t.emergence is not None:
            em_base = em_cum[i0 - 1] if i0 > 0 else 0.0
            je = int(np.searchsorted(em_cum, em_base + t.emergence.t_sum, side="left"))
            if je >= n_total or je - i0 + 1 > limit:
                return min(i0 + limit, n_total), False
            start = je + 1
        base = gdd_cum[start - 1] if start > 0 else 0.0
        target = base + t.t_sum
        j = int(np.searchsorted(gdd_cum, target, side="left"))
        if j >= n_total or j - i0 + 1 > limit:
            return min(i0 + limit, n_total), False
        return j + 1, True
    return i0 + int(round(crop.stages.total)), True


def evaluable(crop: Crop) -> tuple[bool, str | None]:
    if crop.perennial:
        return False, "perennial_not_evaluated"
    if crop.kc_ini is None or crop.temperature is None:
        return False, "insufficient_data"
    if crop.temperature.t_sum is None and crop.temperature.t_opt is None:
        return False, "insufficient_data"  # neither thermal time nor growth optimum known
    if crop.stages is None:
        return False, "insufficient_data"
    return True, None


def remaining_deficit(deficit: float, irrigation: str, stored_mm: float = 0.0) -> float:
    """Rain deficit left after soil water stored at sowing (fallow/gap, docs/METHOD.md) and irrigation.

    Stored water covers 10-day block deficits first (decision K1-A); irrigation then covers
    all (`full`) or half (`limited`, assumption) of what is left.
    """
    left = max(0.0, deficit - max(0.0, stored_mm))
    if irrigation == "full":
        return 0.0
    if irrigation == "limited":
        return left * (1 - LIMITED_IRRIGATION_SHARE)
    return left


def season_rows(crop: Crop, clim: ClimateArrays, irrigation: str = "none",
                sowing_dates: list[tuple[int, int]] | None = None,
                light_ref: dict[str, float] | None = None) -> dict[str, list[dict]]:
    """Per sowing date ("MM-DD") the per-year season rows (crop must be evaluable).

    Each row has the year, the season's first index i0 and end index i1 (one past the last
    day) in the climate record, the factor scores and the final season `score`.
    """
    t = crop.temperature
    n = len(clim.dates)
    limit = max_season_days(crop)
    short_limit = (SHORT_SEASON_FRACTION * crop.stages.min_total
                   if crop.stages.min_total and t.t_sum is not None else None)
    if t.t_sum is None:
        f_temp = ramp_up(clim.tmean, t.t_base, t.t_opt)
    else:
        f_temp = (clim.tmean > t.t_base).astype(float)
    if t.t_heat is not None and t.t_ext is not None:
        f_temp = f_temp * ramp_down(clim.tmax, t.t_heat, t.t_ext)
    gdd_cum = np.cumsum(daily_thermal_time(t, clim.tmean))
    em_cum = np.cumsum(t.emergence.rate(clim.tmean)) if t.emergence is not None else None
    adjust_kc = clim.u2 is not None and clim.rh_min is not None and crop.max_height_m is not None
    lethal = crop.lethal_min["value"] if crop.lethal_min else None
    lethal = None if lethal is None else (max(lethal) if isinstance(lethal, list) else lethal)

    years = sorted(set(clim.dates.year))
    index_of = {d: i for i, d in enumerate(clim.dates.date)}
    out: dict[str, list[dict]] = {}
    for m, d in sowing_dates or SOWING_DATES:
        rows = []
        for y in years:
            i0 = index_of.get(date(y, m, d))
            if i0 is None:
                continue
            i1, matured = _season_end(crop, gdd_cum, i0, n, limit, em_cum)
            if matured and i1 > n:
                continue  # season runs past the end of the record
            if not matured and i1 >= n and i1 - i0 < limit:
                continue  # record ended before we could decide
            s = slice(i0, i1)
            length = i1 - i0
            if not matured:
                temp_score = 0.0
            elif t.ecocrop is not None:
                temp_score = ecocrop_temperature_score(clim.tmean[s], t.ecocrop.temp)
            else:
                temp_score = float(np.nanmean(f_temp[s]))
            kc_mid, kc_end = crop.kc_mid, crop.kc_end
            if adjust_kc:  # FAO-56 eq. 62 / 65 with this season's mid / late-season means
                kc_mid, kc_end, _ = season_kc(crop.stages.fractions(), kc_mid, kc_end,
                                              crop.max_height_m, clim.u2[s], clim.rh_min[s])
            kc = kc_curve(length, crop.stages.fractions(), crop.kc_ini, kc_mid, kc_end)
            etc = kc * clim.et0[s]
            etc_total = float(np.nansum(etc))
            deficit = dekad_deficit(np.nan_to_num(etc), np.nan_to_num(clim.precip[s]))
            remaining = remaining_deficit(deficit, irrigation)
            water_score = 1.0 - remaining / etc_total if etc_total > 0 else 1.0
            duration = min(1.0, length / short_limit) if short_limit else 1.0
            radiation = float(np.nansum(clim.rad[s])) if clim.rad is not None else None
            rows.append({
                "year": y, "i0": i0, "i1": i1,
                "temp": temp_score, "water": water_score, "duration": duration, "radiation": radiation,
                "matured": matured,
                "days": length, "etc": etc_total, "deficit": deficit,
                "kc_mid": kc_mid, "kc_end": kc_end,
                "precip": float(np.nansum(clim.precip[s])),
                "frost_days": int((clim.tmin[s] < 0).sum()),
                "lethal_days": int((clim.tmin[s] < lethal).sum()) if lethal is not None else None,
                "heat_days": int((clim.tmax[s] > t.t_heat).sum()) if t.t_heat is not None else None,
            })
        if rows:
            key = f"{m:02d}-{d:02d}"
            own = [r["radiation"] for r in rows if r["matured"] and r["radiation"] is not None]
            ref = (light_ref or {}).get(key) if light_ref is not None else (float(np.median(own)) if own else None)
            for r in rows:
                r["light_ref"] = ref
                r["light"] = (min(1.0, r["radiation"] / ref) if ref and r["radiation"] is not None else 1.0)
                r["score"] = r["temp"] * r["water"] * r["duration"] * r["light"] if r["matured"] else 0.0
            out[key] = rows
    return out


def evaluate_crop(crop: Crop, clim: ClimateArrays, irrigation: str = "none",
                  light_ref: dict[str, float] | None = None, local_calendar: dict | None = None,
                  use_calendar: bool = True) -> dict:
    """light_ref: per sowing date ("MM-DD") the reference season radiation from the
    baseline climate (result["light_ref"] of the baseline run). None = use this climate.

    local_calendar: the crop's observed regional calendar (app.suitability.calendar.lookup).
    With use_calendar the best window is chosen among windows within WINDOW_DAYS of the
    local planting day (decision K1-a); every window is labelled in_local_calendar."""
    if irrigation not in IRRIGATION_MODES:
        raise ValueError(f"irrigation must be one of {IRRIGATION_MODES}")
    ok, status = evaluable(crop)
    if not ok:
        return {"status": status, "missing": crop.missing}

    windows = []
    refs: dict[str, float] = {}
    for key, rows in season_rows(crop, clim, irrigation, light_ref=light_ref).items():
        if rows[0]["light_ref"] is not None:
            refs[key] = rows[0]["light_ref"]
        m, d = map(int, key.split("-"))
        windows.append(_aggregate(m, d, rows))

    if not windows:
        return {"status": "insufficient_data", "missing": ["climate_record_too_short"]}
    for w in windows:
        if local_calendar is None:
            w["in_local_calendar"] = None
        else:
            w["days_from_local_planting"] = days_apart(w["sowing"], local_calendar["planting_doy"])
            w["in_local_calendar"] = w["days_from_local_planting"] <= calendar_window_days
    rank = (lambda w: (w["score_median"], w["score_p20"]))
    best_any = max(windows, key=rank)
    # Conflict rule (decision K2, plan_ggcmi_takvim.md): when the model cannot grow the crop in
    # any window of the local calendar (every in-calendar median score is 0), the calendar is
    # not applied for this crop and the conflict is reported.
    in_cal = [w for w in windows if w["in_local_calendar"]]
    calendar_conflict = bool(local_calendar is not None and in_cal and all(w["score_median"] == 0 for w in in_cal)
                             and any(w["score_median"] > 0 for w in windows))
    calendar_rule = bool(local_calendar is not None and use_calendar and in_cal and not calendar_conflict)
    candidates = [w for w in windows if w["in_local_calendar"]] if calendar_rule else windows
    best = max(candidates, key=rank)
    common = {"windows": windows, "light_ref": refs, "local_calendar": local_calendar,
              "calendar_rule": calendar_rule, "calendar_conflict": calendar_conflict}
    if best_any["score_median"] == 0 and best_any["score_p20"] == 0:
        return {"status": "not_suitable_by_model", "reason": _failure_reason(windows), **common}
    # Within GOOD_WINDOW_MARGIN of the best AND at least GOOD_WINDOW_SHARE of it, so that
    # uniformly poor results do not mark every month as "good".
    threshold = max(best["score_median"] - GOOD_WINDOW_MARGIN, best["score_median"] * GOOD_WINDOW_SHARE)
    good = [w["sowing"] for w in candidates if w["score_median"] >= threshold]
    return {"status": "evaluated", "best_window": best, "good_sowing_dates": good,
            "best_window_outside_calendar": best_any if best_any is not best else None, **common}


def _failure_reason(windows: list[dict]) -> dict:
    """Why no sowing date works: the most common limiting factor over all windows."""
    not_matured = float(np.mean([1 - w["matured_share"] for w in windows]))
    if not_matured > 0.5:
        return {"code": "does_not_mature", "share_of_seasons": round(not_matured, 2),
                "text": "The crop does not complete its season within the typical length "
                        "(too cool, or the thermal-time value does not fit local varieties)."}
    temp = float(np.median([w["temperature_score_median"] for w in windows]))
    water = float(np.median([w["water_score_median"] for w in windows]))
    if temp <= water:
        return {"code": "temperature", "text": "Temperatures limit the crop in every sowing window."}
    return {"code": "water", "text": "Rainfall cannot meet crop water use in any sowing window."}


def _aggregate(m: int, d: int, rows: list[dict]) -> dict:
    a = {k: np.array([r[k] for r in rows], dtype=float) for k in
         ("score", "temp", "water", "duration", "light", "days", "etc", "deficit", "precip", "frost_days",
          "kc_mid", "kc_end")}
    matured = np.array([r["matured"] for r in rows])
    sow = date(2001, m, d)
    days_med = float(np.median(a["days"]))
    harvest = sow + timedelta(days=int(round(days_med)) - 1)
    out = {
        "sowing": f"{m:02d}-{d:02d}",
        "harvest_median": f"{harvest.month:02d}-{harvest.day:02d}",
        "season_days_median": int(round(days_med)),
        "season_months": _months_between(sow, harvest),
        "n_seasons": len(rows),
        "matured_share": round(float(matured.mean()), 2),
        "score_median": round(float(np.median(a["score"])), 3),
        "score_p20": round(float(np.percentile(a["score"], 20)), 3),
        "fail_rate": round(float(((a["score"] < FAIL_SCORE) | ~matured).mean()), 2),
        "temperature_score_median": round(float(np.median(a["temp"])), 3),
        "water_score_median": round(float(np.median(a["water"])), 3),
        "duration_factor_median": round(float(np.median(a["duration"])), 3),
        "light_factor_median": round(float(np.median(a["light"])), 3),
        "etc_mm_median": round(float(np.median(a["etc"])), 0),
        "kc_mid_median": round(float(np.median(a["kc_mid"])), 3),
        "kc_end_median": round(float(np.median(a["kc_end"])), 3),
        "precip_mm_median": round(float(np.median(a["precip"])), 0),
        "rain_deficit_mm_median": round(float(np.median(a["deficit"])), 0),
        "frost_days_median": float(np.median(a["frost_days"])),
    }
    for k in ("lethal_days", "heat_days"):
        vals = [r[k] for r in rows if r[k] is not None]
        out[f"{k}_median"] = float(np.median(vals)) if vals else None
    return out


def _months_between(start: date, end: date) -> list[int]:
    months, cur = [], date(start.year, start.month, 1)
    while (cur.year, cur.month) <= (end.year, end.month) and len(months) < 12:
        months.append(cur.month)
        cur = date(cur.year + (cur.month == 12), cur.month % 12 + 1, 1)
    return months
