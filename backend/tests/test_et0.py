"""FAO-56 ET0 against FAO-56 Example 18 (Uccle, Brussels, 6 July).

Reference numbers are printed in FAO-56 chapter 4, Example 18
(https://www.fao.org/4/X0490E/x0490e08.htm).
"""

import numpy as np
import pytest

from app.features import et0 as e


def test_example18_parameters():
    p = e.atmospheric_pressure(100)
    assert p == pytest.approx(100.1, abs=0.05)
    assert e.psychrometric_constant(p) == pytest.approx(0.0666, abs=5e-5)
    assert e.svp_slope(16.9) == pytest.approx(0.122, abs=5e-4)
    assert e.sat_vapour_pressure(21.5) == pytest.approx(2.564, abs=5e-4)
    assert e.sat_vapour_pressure(12.3) == pytest.approx(1.431, abs=5e-4)


def test_example18_radiation():
    ra = e.extraterrestrial_radiation(50.80, 187)
    assert ra == pytest.approx(41.09, abs=0.02)
    rso = e.clear_sky_radiation(ra, 100)
    assert rso == pytest.approx(30.90, abs=0.02)
    ea = (1.431 * 0.84 + 2.564 * 0.63) / 2  # eq. 17 as in the example
    assert ea == pytest.approx(1.409, abs=5e-4)
    rnl = e.net_longwave_radiation(21.5, 12.3, ea, 22.07, rso)
    assert rnl == pytest.approx(3.71, abs=0.01)


def test_example18_et0():
    ea = 1.409
    rn = 17.00 - 3.71
    et0 = e.et0_from_components(
        t_mean=16.9, u2=2.078, es=1.997, ea=ea,
        delta=e.svp_slope(16.9), gamma=e.psychrometric_constant(e.atmospheric_pressure(100)), rn=rn,
    )
    assert et0 == pytest.approx(3.88, abs=0.02)


def test_et0_daily_vectorised_and_non_negative():
    out = e.et0_daily(
        tmax_c=np.array([21.5, -5.0]), tmin_c=np.array([12.3, -15.0]),
        rh_mean_pct=np.array([73.5, 95.0]), u2_ms=np.array([2.078, 0.5]),
        rs_mj=np.array([22.07, 2.0]), elevation_m=100, lat_deg=50.8, doy=np.array([187, 15]),
    )
    assert out.shape == (2,)
    assert (out >= 0).all()
    # RHmean path (eq. 19) is close to, not equal to, the RHmax/RHmin example result.
    assert out[0] == pytest.approx(3.9, abs=0.3)


def test_polar_night_radiation_is_zero_not_nan():
    assert e.extraterrestrial_radiation(80.0, 355) == pytest.approx(0.0, abs=1e-6)
