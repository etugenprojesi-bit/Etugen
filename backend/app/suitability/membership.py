"""Trapezoidal membership functions (ECOCROP-style fuzzy suitability).

    1 |      b________c
      |     /          \\
    0 |____/            \\____
          a              d

Use a = b = -inf for an open left side and c = d = +inf for an open right side.
"""

from __future__ import annotations

import numpy as np


def trapezoid(x, a: float, b: float, c: float, d: float) -> np.ndarray:
    if not (a <= b <= c <= d):
        raise ValueError(f"trapezoid needs a <= b <= c <= d, got {a}, {b}, {c}, {d}")
    x = np.asarray(x, float)
    y = np.ones_like(x)
    if np.isfinite(a) or np.isfinite(b):
        rise = (x - a) / (b - a) if b > a else (x >= b).astype(float)
        y = np.where(x < b, np.clip(rise, 0.0, 1.0), y)
    if np.isfinite(c) or np.isfinite(d):
        fall = (d - x) / (d - c) if d > c else (x <= c).astype(float)
        y = np.where(x > c, np.clip(fall, 0.0, 1.0), y)
    return np.where(np.isnan(x), np.nan, y)


def ramp_up(x, lo: float, hi: float) -> np.ndarray:
    """0 below lo, linear to 1 at hi, 1 above."""
    return trapezoid(x, lo, hi, np.inf, np.inf)


def ramp_down(x, lo: float, hi: float) -> np.ndarray:
    """1 below lo, linear to 0 at hi, 0 above."""
    return trapezoid(x, -np.inf, -np.inf, lo, hi)
