"""FAO-56 soil water balance (ch. 7, 8, 11) against the worked examples.

Reference numbers are printed in FAO-56 chapter 7
(https://www.fao.org/4/X0490E/x0490e0c.htm): Example 31 (bare soil after rain)
and Example 35 (dual Kc, irrigation then rain).
"""

import numpy as np
import pytest

from app.suitability.engine import dekad_deficit
from app.water import fao56_soil as w


def test_kc_max_eq72():
    assert w.kc_max(2.0, 45.0, 0.0, 0.0) == pytest.approx(1.20)       # bare soil (ch. 11)
    assert w.kc_max(1.6, 35.0, 0.3, 0.30) == pytest.approx(1.21, abs=0.005)  # Example 35


def test_example31_bare_loam():
    # Loam: TEW 20 mm, REW 9 mm; Kcb 0.15, Kc max 1.20, ETo 4.5 mm/d; topsoil wet at the start.
    expected_de_end = [4.73, 9.45, 13.98, 16.57, 18.04, 18.88, 19.36, 19.64, 19.79, 19.88]
    expected_kr = [1, 1, 0.96, 0.55, 0.31, 0.18, 0.10, 0.06, 0.03, 0.02]
    de = 0.0
    for day, (de_ref, kr_ref) in enumerate(zip(expected_de_end, expected_kr), start=1):
        d = w.topsoil_day(de, 4.5, tew=20, rew=9, kcb=0.15, kcmax=1.20)
        assert d.kr == pytest.approx(kr_ref, abs=0.006), day
        assert d.de_end == pytest.approx(de_ref, abs=0.02), day
        de = d.de_end
    assert w.topsoil_day(0.0, 4.5, 20, 9, kcb=0.15).e == pytest.approx(4.73, abs=0.01)


def test_example35_dual_kc():
    # Sandy loam TEW 18, REW 8, Kc max 1.21; De = TEW at the start; I = 40 mm (fw 0.8) on day 1,
    # rain 6 mm on day 6. Columns 2, 7, 8 (ETo, few, Kcb) are given in the example.
    et0 = [4.5, 5.0, 3.9, 4.2, 4.8, 2.7, 5.8, 5.1, 4.7, 5.2]
    few = [0.80, 0.80, 0.80, 0.80, 0.80, 0.89, 0.88, 0.87, 0.87, 0.86]
    kcb = [0.30, 0.31, 0.32, 0.33, 0.34, 0.36, 0.37, 0.38, 0.39, 0.40]
    rain = [0, 0, 0, 0, 0, 6, 0, 0, 0, 0]
    irr = [40, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    de_end = [5, 11, 14, 16, 17, 13, 16, 17, 18, 18]       # column 14 (rounded to mm)
    ke = [0.91, 0.90, 0.62, 0.35, 0.18, 0.64, 0.45, 0.17, 0.08, 0.04]  # column 11
    # The example carries De rounded to whole mm (e.g. 11 instead of 10.7 at the start of day 3),
    # so Kr/Ke differ by up to ~0.04 from an unrounded calculation. Column 15 prints E = 2.8 on
    # day 3, which contradicts its own Ke x ETo = 0.62 x 3.9 = 2.4; E is checked as Ke x ETo.
    de = 18.0
    for i in range(10):
        d = w.topsoil_day(de, et0[i], 18, 8, p=rain[i], irr=irr[i], fw=0.8, few=few[i], kcb=kcb[i], kcmax=1.21)
        if i == 0:
            assert d.dpe == pytest.approx(32, abs=0.5)
        assert d.de_end == pytest.approx(de_end[i], abs=0.7), i + 1  # rounding carried over days
        assert d.ke == pytest.approx(ke[i], abs=0.045), i + 1
        assert d.e == pytest.approx(ke[i] * et0[i], abs=0.2), i + 1
        de = d.de_end


def _scalar_bare(p, et0, taw, tew, rew):
    """Bare soil, one gap, written plainly from eq. 74/77/79/85/88 (reference for the batch kernel)."""
    dr, de, tot_e, tot_dp = taw, tew, 0.0, 0.0
    for pi, ei in zip(p, et0):
        d = w.topsoil_day(de, ei, tew, rew, p=pi)
        de = d.de_end
        dp = max(0.0, pi - d.e - dr)
        dr = min(taw, max(0.0, dr - pi + d.e + dp))
        tot_e += d.e
        tot_dp += dp
    return dr, de, tot_e, tot_dp


def test_batch_kernel_matches_scalar_reference():
    rng = np.random.default_rng(1)
    p = np.where(rng.random(800) < 0.25, rng.gamma(1.2, 8, 800), 0.0)
    et0 = rng.uniform(0.3, 7, 800)
    starts, lengths = np.array([0, 100, 350]), np.array([450, 120, 400])
    taw, tew, rew = np.array([138.0, 92.0, 165.0]), 20.3, 9.0
    res = w.gap_balance(p, et0, starts, lengths, taw, tew, rew)
    for r in range(3):
        s, n = starts[r], lengths[r]
        dr, de, e, dp = _scalar_bare(p[s:s + n], et0[s:s + n], taw[r], tew, rew)
        assert res.dr_end[r] == pytest.approx(dr)
        assert res.de_end[r] == pytest.approx(de)
        assert res.evaporation[r] == pytest.approx(e)
        assert res.deep_percolation[r] == pytest.approx(dp)


@pytest.mark.parametrize("cover", [False, True])
def test_mass_balance_and_bounds(cover):
    rng = np.random.default_rng(7)
    p = np.where(rng.random(500) < 0.3, rng.gamma(1.5, 10, 500), 0.0)
    et0 = rng.uniform(0.5, 6, 500)
    kcb = np.tile(np.linspace(0.15, 0.95, 500), (2, 1)) if cover else None
    res = w.gap_balance(p, et0, [0, 20], [480, 300], taw=[140.0, 90.0], tew=20.0, rew=9.0,
                        kcb=kcb, h_m=0.9)
    # rain = evaporation + transpiration + drainage + storage change (Dr0 = TAW: empty profile)
    stored_change = res.stored - 0.0
    assert res.precip == pytest.approx(res.evaporation + res.transpiration + res.deep_percolation
                                       + stored_change, abs=1e-6)
    assert np.all((res.stored >= 0) & (res.stored <= np.array([140.0, 90.0])))
    assert np.all((res.de_end >= 0) & (res.de_end <= 20.0))
    assert (res.transpiration > 0).all() == cover


def test_no_rain_bare_soil_stays_empty():
    res = w.gap_balance(np.zeros(100), np.full(100, 5.0), [0], [100], taw=120.0, tew=20.0, rew=9.0)
    assert res.stored[0] == 0 and res.evaporation[0] == 0 and res.deep_percolation[0] == 0


def test_evaporation_only_from_topsoil():
    # Profile full, then 60 dry days: bare soil can lose at most TEW (two-layer model, ch. 7 / ch. 11).
    res = w.gap_balance(np.zeros(60), np.full(60, 6.0), [0], [60], taw=140.0, tew=20.0, rew=9.0,
                        dr0=0.0, de0=0.0)
    assert res.evaporation[0] == pytest.approx(20.0, abs=0.5)
    assert res.stored[0] == pytest.approx(120.0, abs=0.5)


def test_deficit_with_store():
    rng = np.random.default_rng(3)
    etc, p = rng.uniform(0, 6, 200), np.where(rng.random(200) < 0.2, rng.gamma(1, 10, 200), 0.0)
    base = dekad_deficit(etc, p)
    assert w.deficit_with_store(etc, p, 0.0) == pytest.approx(base)   # unchanged without storage
    assert w.deficit_with_store(etc, p, 50.0) == pytest.approx(max(0.0, base - 50.0))
    assert w.deficit_with_store(etc, p, 1e6) == 0.0
