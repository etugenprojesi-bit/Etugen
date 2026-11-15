"""Irrigation interval in the mid-season — FAO-56 chapter 8 (physics, labelled assumptions).

Allen, R.G., Pereira, L.S., Raes, D., Smith, M. (1998). FAO Irrigation and Drainage Paper 56.

* TAW = 1000 (θFC − θWP) Zr                              (eq. 82; SoilGrids, crop root depth Zr)
* p   = p_table + 0.04 (5 − ETc), limited to 0.1 … 0.8   (Table 22 footnote; p_table from Table 22)
* RAW = p TAW                                            (eq. 83) — water the crop can use without stress
* ETc = Kc_mid × ET0 in the mid-season                   (eq. 56; Kc_mid adjusted to the local climate)

Interval = RAW / ETc (days), depth per irrigation = RAW (net mm): irrigate when the root zone
has lost RAW (start of water stress, FAO-56 ch. 8), refilling it to field capacity.

Assumptions (docs/METHOD.md "Irrigation interval"): mid-season ET0 is the multi-year monthly
mean from NASA POWER (no rain, i.e. a dry spell — rain lengthens the interval, its mean is
reported); root depth is the Table 22 value (mid of the range), fully reached in the
mid-season; net depth (no field application losses).
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta

P_MIN, P_MAX = 0.1, 0.8


def schedule(crop, window: dict, months_climate: list[dict], soil) -> dict | None:
    """Mid-season interval and depth for one crop window, or None if an input is unknown."""
    if soil is None or crop.root_depth_m is None or crop.depletion_p is None or crop.stages is None:
        return None
    taw = soil.taw_mm(crop.root_depth_m)
    taw = None if taw is None else float(taw)
    if not taw:
        return None
    by_month = {m["month"]: m for m in months_climate}
    m0, d0 = map(int, window["sowing"].split("-"))
    days = int(window["season_days_median"])
    f_ini, f_dev, f_mid, _ = crop.stages.fractions()
    sow = date(2001, m0, d0)
    start = sow + timedelta(days=round((f_ini + f_dev) * days))
    length = max(1, round(f_mid * days))
    et0, rain = [], []
    for k in range(length):
        d = start + timedelta(days=k)
        mc = by_month.get(d.month)
        if mc is None or mc.get("et0_mm") is None:
            return None
        n = calendar.monthrange(2001, d.month)[1]
        et0.append(mc["et0_mm"] / n)
        rain.append((mc.get("precip_mm") or 0.0) / n)
    kc = window.get("kc_mid_median") or crop.kc_mid
    kc = None if kc is None else float(kc)
    if kc is None:
        return None
    etc = float(kc * sum(et0) / len(et0))
    if etc <= 0:
        return None
    p = min(P_MAX, max(P_MIN, crop.depletion_p + 0.04 * (5.0 - etc)))
    raw = p * taw
    end = start + timedelta(days=length - 1)
    return {
        "mid_season_start": f"{start.month:02d}-{start.day:02d}",
        "mid_season_end": f"{end.month:02d}-{end.day:02d}",
        "mid_season_days": length,
        "etc_mm_per_day": round(etc, 1),
        "rain_mm_per_day": round(float(sum(rain) / len(rain)), 1),
        "taw_mm": round(taw),
        "p": round(p, 2),
        "depth_mm": round(raw),
        "interval_days": max(1, int(raw // etc)),
        "method": "FAO-56 eq. 82-83, Table 22 p adjusted for ETc; RAW / ETc in the mid-season, no rain",
    }
