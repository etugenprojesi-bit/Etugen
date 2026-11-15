import numpy as np
import pytest

from app.suitability.membership import ramp_down, ramp_up, trapezoid


def test_trapezoid_shape():
    x = np.array([0, 5, 10, 15, 20, 25, 30, 35])
    y = trapezoid(x, 5, 15, 25, 35)
    np.testing.assert_allclose(y, [0, 0, 0.5, 1, 1, 1, 0.5, 0])


def test_open_sides():
    np.testing.assert_allclose(ramp_up([0, 4, 8, 100], 0, 8), [0, 0.5, 1, 1])
    np.testing.assert_allclose(ramp_down([-10, 34, 39.5, 45, 50], 34, 45), [1, 1, 0.5, 0, 0])


def test_degenerate_edges_are_steps():
    np.testing.assert_allclose(trapezoid([4, 5, 6], 5, 5, 10, 10), [0, 1, 1])


def test_nan_passes_through():
    assert np.isnan(trapezoid([np.nan], 0, 1, 2, 3)[0])


def test_invalid_order_raises():
    with pytest.raises(ValueError):
        trapezoid([1], 3, 2, 4, 5)
