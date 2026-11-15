"""Optional monthly rainfall sources (IMERG, CHIRPS) for the daily water balance.

The suitability engine needs daily rain; the IMERG product we use is monthly and
CHIRPS is summed to months. Rule (assumption, documented in docs/METHOD.md):
every month's daily POWER rain is multiplied by SOURCE_month / POWER_month, so
the monthly total equals the source while the day-to-day pattern stays POWER's.

Months are left as POWER, and counted, when
* the source has no value (e.g. the IMERG monthly product ends 2025-09), or
* POWER has no rain in that month but the source has some (no daily pattern to
  scale; that rain cannot be placed on a day).

Rain check (decision 2026-11-14, docs/drafts/plan_konya_yagis.md K1-a, K2):
POWER is flagged as possibly too wet where its mean annual rain exceeds CHIRPS
by more than WET_RATIO_LIMIT (assumption: the existing "large difference" limit).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

WET_RATIO_LIMIT = 1.3


def rescale_to_monthly(daily: pd.DataFrame, monthly_mm: pd.Series, source: str) -> tuple[pd.DataFrame, dict]:
    """Copy of the raw POWER daily frame with PRECTOTCORR rescaled to `monthly_mm`
    (PeriodIndex "M"), and diagnostics with source-neutral keys."""
    df = daily.copy()
    per = df.index.to_period("M")
    power_m = df["PRECTOTCORR"].groupby(per).sum(min_count=1)
    src_m = monthly_mm.reindex(power_m.index)

    has_src = src_m.notna()
    power_zero = power_m.fillna(0) <= 0
    scalable = has_src & ~power_zero
    both_zero = has_src & power_zero & (src_m <= 0)
    lost = has_src & power_zero & (src_m > 0)

    factor = pd.Series(1.0, index=power_m.index)
    factor[scalable] = src_m[scalable] / power_m[scalable]
    df["PRECTOTCORR"] = df["PRECTOTCORR"].to_numpy() * factor.reindex(per).to_numpy()

    years = df.index.year
    full_years = sorted(set(years))
    before = daily["PRECTOTCORR"].groupby(years).sum().mean()
    after = df["PRECTOTCORR"].groupby(years).sum().mean()
    no_src = power_m.index[~has_src]
    diag = {
        "source": source,
        "rule": f"daily POWER rain x ({source} month total / POWER month total)",
        "months_total": int(len(power_m)),
        "months_rescaled": int(scalable.sum() + both_zero.sum()),
        "months_without_source": int((~has_src).sum()),
        "months_without_source_range": None if len(no_src) == 0 else f"{no_src.min()}..{no_src.max()}",
        "months_source_rain_without_power_rain": int(lost.sum()),
        "source_rain_not_placed_mm": round(float(src_m[lost].sum()), 1),
        "factor_median": round(float(np.median(factor[scalable])), 3) if scalable.any() else None,
        "annual_mean_mm": {"power": round(float(before), 0), "used": round(float(after), 0)},
        "years": f"{full_years[0]}..{full_years[-1]}",
    }
    return df, diag


def rescale_to_imerg(daily: pd.DataFrame, imerg_mm: pd.Series) -> tuple[pd.DataFrame, dict]:
    """IMERG version with the original diagnostic keys (API field `imerg_rescale`)."""
    df, d = rescale_to_monthly(daily, imerg_mm, "IMERG")
    rename = {"months_without_source": "months_without_imerg",
              "months_without_source_range": "months_without_imerg_range",
              "months_source_rain_without_power_rain": "months_imerg_rain_without_power_rain",
              "source_rain_not_placed_mm": "imerg_rain_not_placed_mm"}
    d = {rename.get(k, k): v for k, v in d.items() if k != "source"}
    return df, d


def rain_check(daily: pd.DataFrame, chirps_mm: pd.Series) -> dict:
    """Mean annual POWER vs CHIRPS rain over the complete years present in both."""
    p = daily["PRECTOTCORR"]
    pm = p.groupby(p.index.to_period("M")).sum(min_count=1)
    both = pd.DataFrame({"power": pm, "chirps": chirps_mm.reindex(pm.index)}).dropna()
    counts = both.groupby(both.index.year).size()
    years = [int(y) for y, n in counts.items() if n == 12]
    if not years:
        return {"status": "missing"}
    ann = both[both.index.year.isin(years)].groupby(both[both.index.year.isin(years)].index.year).sum()
    pw, ch = float(ann["power"].mean()), float(ann["chirps"].mean())
    ratio = pw / ch if ch > 0 else None
    return {"status": "ok", "years": f"{years[0]}..{years[-1]}", "power_mm": round(pw), "chirps_mm": round(ch),
            "ratio": None if ratio is None else round(ratio, 2), "limit": WET_RATIO_LIMIT,
            "power_may_be_too_wet": bool(ratio is not None and ratio > WET_RATIO_LIMIT)}
