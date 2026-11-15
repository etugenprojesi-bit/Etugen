"""FAO-56 irrigation interval and the contour (across-slope) row direction."""

import pytest

from app.features.terrain import fall_direction, slope_summary
from app.suitability.crops import Stages
from app.water.irrigation import schedule
from tests.test_rotation import crop


class Soil:
    def __init__(self, taw_per_m):
        self.taw_per_m = taw_per_m

    def taw_mm(self, root_depth_m):
        return self.taw_per_m * root_depth_m


DAYS = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
MONTHS = [{"month": m, "et0_mm": DAYS[m] * (5.0 if m in (6, 7) else 1.0), "precip_mm": float(DAYS[m])}
          for m in range(1, 13)]


def test_interval_is_raw_over_etc_with_fao56_p_adjustment():
    c = crop("maize", "Poaceae", root=1.0)
    c = c.__class__(**{**c.__dict__, "depletion_p": 0.55, "stages": Stages(20, 20, 40, 20, total=100,
                                                                             row="x", max_total=100, min_total=100)})
    w = {"sowing": "05-01", "season_days_median": 100, "kc_mid_median": 1.2}
    out = schedule(c, w, MONTHS, Soil(150))
    # mid-season: day 40-79 after 1 May = 10 Jun - 19 Jul, ET0 5 mm/d -> ETc 6 mm/d
    assert out["mid_season_start"] == "06-10" and out["etc_mm_per_day"] == 6.0
    p = 0.55 + 0.04 * (5 - 6.0)                      # FAO-56 Table 22 footnote
    assert out["p"] == pytest.approx(p) and out["taw_mm"] == 150
    assert out["depth_mm"] == round(p * 150) and out["interval_days"] == int(p * 150 // 6.0)
    assert out["rain_mm_per_day"] == 1.0


def test_unknown_inputs_give_no_schedule():
    c = crop("x", "Poaceae")  # no depletion_p, no stages
    assert schedule(c, {"sowing": "05-01", "season_days_median": 100}, MONTHS, Soil(150)) is None


def test_fall_direction_and_contour_rows():
    # ground rises to the north-east -> water runs south-west (225 deg), rows NW-SE (135 deg)
    f = fall_direction({"dz_de": 0.01, "dz_dn": 0.01})
    assert f["downhill_azimuth_deg"] == 225 and f["contour_rows_azimuth_deg"] == 135
    assert f["plane_slope_pct"] == pytest.approx(1.41, abs=0.01)
    assert fall_direction({"dz_de": 0.0, "dz_dn": -0.02})["downhill_azimuth_deg"] == 0  # falls north
    assert fall_direction(None) is None
    # no row advice on flat terrain
    flat = slope_summary({"slope_deg_p50": 1.85, "elevation_p10": 235, "elevation_p90": 240},
                         {"dz_de": 0.001, "dz_dn": 0.0})
    assert flat["flat_terrain"] and flat["fall"] is None
    hill = slope_summary({"slope_deg_p50": 2.62, "elevation_p10": 1899, "elevation_p90": 1985},
                         {"dz_de": 0.015, "dz_dn": 0.013})
    assert hill["fall"]["downhill_azimuth_deg"] == 229
