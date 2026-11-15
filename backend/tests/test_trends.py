import numpy as np
import pytest

from app.features.trends import mann_kendall, sens_slope


def test_linear_series_slope_and_significance():
    t = np.arange(2001, 2026, dtype=float)
    y = 0.03 * (t - 2001) + 10
    tr = mann_kendall(y, t)
    assert tr.slope_per_year == pytest.approx(0.03)
    assert tr.s == len(y) * (len(y) - 1) // 2
    assert tr.significant


def test_constant_series_has_no_trend():
    tr = mann_kendall(np.full(20, 5.0))
    assert tr.slope_per_year == 0
    assert tr.s == 0
    assert tr.p_value == pytest.approx(1.0)


def test_sen_slope_is_robust_to_outlier():
    t = np.arange(10, dtype=float)
    y = t.copy()
    y[9] = 1000
    assert sens_slope(t, y) == pytest.approx(1.0)


def test_nan_values_are_dropped_and_short_series_is_not_tested():
    tr = mann_kendall([1.0, np.nan, 2.0])
    assert tr.n == 2 and tr.slope_per_year is None and tr.p_value == 1.0


def test_decreasing_noisy_series():
    rng = np.random.default_rng(0)
    y = -0.5 * np.arange(30) + rng.normal(0, 1, 30)
    tr = mann_kendall(y)
    assert tr.s < 0 and tr.significant and tr.slope_per_year < 0
