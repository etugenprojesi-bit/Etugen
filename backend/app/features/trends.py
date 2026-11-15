"""Mann-Kendall trend test and Sen's slope (classical statistics, not ML).

Mann (1945), Kendall (1975); variance with tie correction; Sen (1968).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Trend:
    slope_per_year: float | None
    s: int
    z: float
    p_value: float
    n: int

    @property
    def significant(self) -> bool:
        return self.p_value < 0.05


def sens_slope(t: np.ndarray, y: np.ndarray) -> float | None:
    i, j = np.triu_indices(len(y), k=1)
    dt = t[j] - t[i]
    ok = dt != 0
    return float(np.median((y[j] - y[i])[ok] / dt[ok])) if ok.any() else None


def mann_kendall(y, t=None) -> Trend:
    y = np.asarray(y, float)
    t = np.arange(len(y), dtype=float) if t is None else np.asarray(t, float)
    keep = ~np.isnan(y)
    y, t = y[keep], t[keep]
    n = len(y)
    if n < 4:
        return Trend(None, 0, 0.0, 1.0, n)
    i, j = np.triu_indices(n, k=1)
    s = int(np.sign(y[j] - y[i]).sum())
    _, counts = np.unique(y, return_counts=True)
    ties = counts[counts > 1]
    var_s = (n * (n - 1) * (2 * n + 5) - (ties * (ties - 1) * (2 * ties + 5)).sum()) / 18.0
    if var_s <= 0:
        z = 0.0
    elif s > 0:
        z = (s - 1) / math.sqrt(var_s)
    elif s < 0:
        z = (s + 1) / math.sqrt(var_s)
    else:
        z = 0.0
    p = math.erfc(abs(z) / math.sqrt(2))  # two-sided normal p-value
    return Trend(sens_slope(t, y), s, z, p, n)


@dataclass(frozen=True)
class ChangePoint:
    index: int | None      # last index of the first segment
    k: float               # Pettitt statistic K = max |U_t|
    p_value: float         # approximate, two-sided
    n: int

    @property
    def significant(self) -> bool:
        return self.p_value < 0.05


def pettitt(y) -> ChangePoint:
    """Pettitt (1979) non-parametric change-point test, Appl. Statist. 28(2):126-135.

    U_t = sum_{i<=t} sum_{j>t} sign(y_j - y_i);  K = max_t |U_t|;
    p ~= 2 exp(-6 K^2 / (n^3 + n^2)) (approximation, accurate for p < 0.5).
    """
    y = np.asarray(y, float)
    y = y[~np.isnan(y)]
    n = len(y)
    if n < 4:
        return ChangePoint(None, 0.0, 1.0, n)
    sign = np.sign(y[None, :] - y[:, None])  # sign[i, j] = sign(y_j - y_i)
    u = np.array([sign[: t + 1, t + 1:].sum() for t in range(n - 1)])
    t = int(np.argmax(np.abs(u)))
    k = float(abs(u[t]))
    p = min(1.0, 2.0 * math.exp(-6.0 * k * k / (n ** 3 + n ** 2)))
    return ChangePoint(t, k, p, n)
