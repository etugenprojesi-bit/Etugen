"""POWER vs GPM IMERG precipitation comparison (classical statistics).

Both series are monthly totals at the same analysis point (different
footprints: POWER ~0.5° MERRA-2 bias-corrected, IMERG 0.1° satellite-gauge
merge). Only complete years present in both are compared.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.features.trends import mann_kendall, pettitt

# Assumption (reporting rule, not a physical constant): sources "agree" on the
# annual mean when they differ by less than 15 %; above 30 % the difference is
# flagged as large and the UI must show both values.
AGREE_REL = 0.15
LARGE_REL = 0.30


def _trend(values: pd.Series) -> dict:
    tr = mann_kendall(values.to_numpy(float), values.index.to_numpy(float))
    return {"slope_mm_per_decade": None if tr.slope_per_year is None else round(tr.slope_per_year * 10, 1),
            "p_value": round(tr.p_value, 4), "significant_5pct": tr.significant, "n_years": tr.n}


def compare_precip(table: pd.DataFrame) -> dict:
    t = table[["power_precip_mm", "imerg_precip_mm"]]
    both = t.dropna()
    counts = both.groupby(both.index.year).size()
    years = counts[counts == 12].index
    if len(years) < 5:
        return {"status": "insufficient_overlap", "common_full_years": int(len(years))}
    sub = both[both.index.year.isin(years)]
    ann = sub.groupby(sub.index.year).sum()
    p_mean, i_mean = float(ann["power_precip_mm"].mean()), float(ann["imerg_precip_mm"].mean())
    rel = (p_mean - i_mean) / i_mean if i_mean > 0 else None
    if rel is None:
        verdict = "imerg_zero"
    elif abs(rel) < AGREE_REL:
        verdict = "agree"
    elif abs(rel) < LARGE_REL:
        verdict = "moderate_difference"
    else:
        verdict = "large_difference"

    m = sub.index.month
    by_month = []
    for k in range(1, 13):
        s = sub[m == k]
        by_month.append({"month": k, "power_mm": round(float(s["power_precip_mm"].mean()), 1),
                         "imerg_mm": round(float(s["imerg_precip_mm"].mean()), 1)})

    # Year-to-year agreement: do both sources rank wet and dry years the same way?
    r_annual = float(np.corrcoef(ann["power_precip_mm"], ann["imerg_precip_mm"])[0, 1])
    r_monthly = float(np.corrcoef(sub["power_precip_mm"], sub["imerg_precip_mm"])[0, 1])
    trend_p, trend_i = _trend(ann["power_precip_mm"]), _trend(ann["imerg_precip_mm"])
    sp, si = trend_p["slope_mm_per_decade"], trend_i["slope_mm_per_decade"]
    trend_agree = (sp is not None and si is not None and np.sign(sp) == np.sign(si)
                   and trend_p["significant_5pct"] == trend_i["significant_5pct"])
    # Homogeneity: if the POWER - IMERG difference has a trend or a step, a trend
    # seen in only one source may come from that source's processing, not climate.
    yrs = ann.index.to_numpy()
    diff = (ann["power_precip_mm"] - ann["imerg_precip_mm"]).to_numpy(float)
    cp = pettitt(diff)
    diff_trend = _trend(pd.Series(diff, index=yrs))
    step = None
    if cp.significant:
        before, after = diff[: cp.index + 1], diff[cp.index + 1:]
        step = {"last_year_before": int(yrs[cp.index]), "mean_diff_before_mm": round(float(before.mean())),
                "mean_diff_after_mm": round(float(after.mean())),
                "ratio_before": round(float(ann["power_precip_mm"].iloc[: cp.index + 1].sum()
                                            / ann["imerg_precip_mm"].iloc[: cp.index + 1].sum()), 2),
                "ratio_after": round(float(ann["power_precip_mm"].iloc[cp.index + 1:].sum()
                                           / ann["imerg_precip_mm"].iloc[cp.index + 1:].sum()), 2)}
    homogeneous = not cp.significant and not diff_trend["significant_5pct"]
    power_trend_confirmed = bool(trend_agree and homogeneous) if trend_p["significant_5pct"] else None
    return {
        "status": "ok",
        "period": f"{int(years.min())}-{int(years.max())}",
        "common_full_years": int(len(years)),
        "annual_mean_mm": {"power": round(p_mean), "imerg": round(i_mean)},
        "power_minus_imerg_mm": round(p_mean - i_mean),
        "power_relative_difference": None if rel is None else round(rel, 3),
        "verdict": verdict,
        "correlation": {"annual": round(r_annual, 3), "monthly": round(r_monthly, 3)},
        "trend": {"power": trend_p, "imerg": trend_i, "same_direction_and_significance": bool(trend_agree)},
        "difference_series": {
            "trend": diff_trend,
            "change_point": {"p_value": round(cp.p_value, 4), "significant_5pct": cp.significant, "step": step},
            "homogeneous": homogeneous,
        },
        # True/False only when POWER reports a significant trend; None = nothing to confirm.
        "power_trend_confirmed_by_imerg": power_trend_confirmed,
        "by_month": by_month,
        "annual": [{"year": int(y), "power_mm": round(float(r.power_precip_mm)),
                    "imerg_mm": round(float(r.imerg_precip_mm))} for y, r in ann.iterrows()],
        "thresholds": {"agree_below": AGREE_REL, "large_above": LARGE_REL, "kind": "assumption"},
        "method": ["stat:pearson_r", "stat:mann_kendall+sens_slope", "stat:pettitt_change_point"],
    }
