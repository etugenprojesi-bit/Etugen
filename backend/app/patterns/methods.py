"""Three pattern-finding approaches on the same year table (stage 3).

A. Classical statistics: z-scores with a fixed threshold.        [stat]
B. Machine learning: k-means clustering of NDVI curves and        [ml]
   Isolation Forest anomaly detection (scikit-learn).
C. Analog years: nearest neighbours in standardised climate       [stat]
   space, with a leave-one-out skill test.

All thresholds are assumptions stated here and in docs/METHOD.md. With ~25
years per point the samples are small; results describe this record, they
are not general rules.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.features.trends import pettitt
from app.patterns.features import CLIMATE_COLS, NDVI_COLS, zscores

Z_THRESHOLD = 1.5             # assumption: |z| >= 1.5 marks an unusual year (~13 % of a normal sample)
K_RANGE = (2, 3, 4)
MIN_SILHOUETTE = 0.25         # assumption: below this, clusters are reported as "no clear structure"
IF_TREES = 500
ANALOG_K = 3
RANDOM_STATE = 0


# --- A. z-score / threshold --------------------------------------------------------------


def zscore_anomalies(t: pd.DataFrame) -> dict:
    z = zscores(t[["ndvi_integral", "ndvi_peak", "precip_mm", "tmean_c"]])
    flagged = []
    for year, r in z.iterrows():
        hits = [c for c in ("ndvi_integral", "ndvi_peak") if abs(r[c]) >= Z_THRESHOLD]
        if hits:
            flagged.append({
                "year": int(year),
                "direction": "low" if r[hits[0]] < 0 else "high",
                "z": {c: round(float(r[c]), 2) for c in z.columns},
                "triggered_by": hits,
            })
    return {"threshold": Z_THRESHOLD, "years": flagged,
            "anomalous_years": [f["year"] for f in flagged], "method": "stat:zscore_threshold"}


# --- B. k-means + Isolation Forest -----------------------------------------------------


def kmeans_curves(t: pd.DataFrame) -> dict:
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score

    x = t[NDVI_COLS].to_numpy()
    best = None
    tried = []
    for k in K_RANGE:
        if len(x) <= k + 1:
            continue
        km = KMeans(n_clusters=k, n_init=20, random_state=RANDOM_STATE).fit(x)
        if len(set(km.labels_)) < 2:
            continue
        s = float(silhouette_score(x, km.labels_))
        tried.append({"k": k, "silhouette": round(s, 3)})
        if best is None or s > best[0]:
            best = (s, k, km)
    if best is None:
        return {"status": "too_few_years", "tried": tried, "method": "ml:kmeans"}
    s, k, km = best
    clusters = []
    for c in range(k):
        mask = km.labels_ == c
        curve = km.cluster_centers_[c]
        clusters.append({"cluster": c, "years": [int(y) for y in t.index[mask]],
                         "mean_curve": [round(float(v), 3) for v in curve],
                         "peak_month": int(curve.argmax() + 1),
                         "n_peaks": _n_peaks(curve)})
    clusters.sort(key=lambda c: -len(c["years"]))
    # With two clusters: are they ordered in time (a regime shift, e.g. a change of
    # crops or irrigation) rather than mixed? Pettitt test on the label sequence.
    shift = None
    if k == 2:
        cp = pettitt(km.labels_.astype(float))
        if cp.significant:
            shift = {"last_year_before": int(t.index[cp.index]), "p_value": round(cp.p_value, 4)}
    return {"status": "ok" if s >= MIN_SILHOUETTE else "no_clear_structure", "k": k,
            "silhouette": round(s, 3), "min_silhouette": MIN_SILHOUETTE, "tried": tried,
            "clusters": clusters, "regime_shift": shift, "method": "ml:kmeans"}


def _n_peaks(curve: np.ndarray, min_rise: float = 0.05) -> int:
    """Seasonal NDVI peaks on the circular curve; a peak must rise >= min_rise (assumption) above
    the lowest value on each side before the next peak."""
    c = np.asarray(curve)
    n = len(c)
    peaks = [i for i in range(n) if c[i] > c[i - 1] and c[i] >= c[(i + 1) % n]]
    keep = []
    for i in peaks:
        left = min(c[(i - d) % n] for d in range(1, n // 2 + 1))
        right = min(c[(i + d) % n] for d in range(1, n // 2 + 1))
        if c[i] - max(left, right) >= min_rise:
            keep.append(i)
    return len(keep)


def isolation_forest(t: pd.DataFrame) -> dict:
    from sklearn.ensemble import IsolationForest

    cols = NDVI_COLS + CLIMATE_COLS
    x = zscores(t[cols]).fillna(0.0).to_numpy()
    model = IsolationForest(n_estimators=IF_TREES, contamination="auto",
                            random_state=RANDOM_STATE).fit(x)
    score = model.decision_function(x)  # < 0 = more isolated than expected
    flagged = [int(y) for y, s in zip(t.index, score) if s < 0]
    return {"anomalous_years": flagged,
            "scores": {int(y): round(float(s), 3) for y, s in zip(t.index, score)},
            "features": cols, "trees": IF_TREES, "contamination": "auto",
            "method": "ml:isolation_forest"}


# --- C. analog years ----------------------------------------------------------------------


def analog_years(t: pd.DataFrame, target_year: int | None = None) -> dict:
    """For each year, the ANALOG_K most similar other years by climate (Euclidean on z-scores).

    Skill test (leave-one-out): predict each year's NDVI integral as the mean of its
    analogs and compare the mean absolute error with the climatology forecast
    (mean of all other years). skill = 1 - MAE_analog / MAE_climatology.
    """
    z = zscores(t[CLIMATE_COLS]).fillna(0.0)
    zx = z.to_numpy()
    years = t.index.to_numpy()
    y = t["ndvi_integral"].to_numpy()
    n = len(years)
    if n < ANALOG_K + 2:
        return {"status": "too_few_years"}
    d = np.sqrt(((zx[:, None, :] - zx[None, :, :]) ** 2).sum(-1))
    np.fill_diagonal(d, np.inf)
    nn = np.argsort(d, axis=1)[:, :ANALOG_K]
    pred_analog = y[nn].mean(axis=1)
    pred_clim = (y.sum() - y) / (n - 1)
    mae_a = float(np.abs(pred_analog - y).mean())
    mae_c = float(np.abs(pred_clim - y).mean())
    target = int(years.max()) if target_year is None else int(target_year)
    i = int(np.where(years == target)[0][0]) if target in years else n - 1
    return {
        "status": "ok",
        "k": ANALOG_K,
        "features": CLIMATE_COLS,
        "target_year": int(years[i]),
        "target_analogs": [{"year": int(years[j]), "distance": round(float(d[i, j]), 2),
                            "ndvi_integral": round(float(y[j]), 2)} for j in nn[i]],
        "target_ndvi_integral": round(float(y[i]), 2),
        "loo": {"mae_analog": round(mae_a, 3), "mae_climatology": round(mae_c, 3),
                "skill": None if mae_c == 0 else round(1 - mae_a / mae_c, 3)},
        "method": "stat:analog_nearest_neighbours",
    }


# --- comparison --------------------------------------------------------------------------


def compare(t: pd.DataFrame) -> dict:
    a = zscore_anomalies(t)
    km = kmeans_curves(t)
    iso = isolation_forest(t)
    an = analog_years(t)
    sa, sb = set(a["anomalous_years"]), set(iso["anomalous_years"])
    union = sa | sb
    z = zscores(t[["ndvi_integral", "precip_mm", "tmean_c"]])

    def context(year: int) -> dict:
        r = z.loc[year]
        return {"year": year, "found_by": sorted(({"zscore"} if year in sa else set())
                                                 | ({"isolation_forest"} if year in sb else set())),
                "z_ndvi_integral": round(float(r["ndvi_integral"]), 2),
                "z_precip": round(float(r["precip_mm"]), 2), "z_tmean": round(float(r["tmean_c"]), 2)}

    return {
        "years": [int(y) for y in t.index],
        "n_years": int(len(t)),
        "zscore": a,
        "kmeans": km,
        "isolation_forest": iso,
        "analogs": an,
        "agreement": {
            "both": sorted(sa & sb), "only_zscore": sorted(sa - sb), "only_isolation_forest": sorted(sb - sa),
            "jaccard": None if not union else round(len(sa & sb) / len(union), 3),
        },
        "flagged_year_context": [context(y) for y in sorted(union)],
        "notes": [
            "z-score looks only at NDVI level (integral, peak); Isolation Forest also uses the curve shape "
            "and climate, so it can flag years with a normal NDVI total but an unusual season.",
            f"Small sample ({len(t)} years): treat flagged years as questions, not facts.",
        ],
    }
