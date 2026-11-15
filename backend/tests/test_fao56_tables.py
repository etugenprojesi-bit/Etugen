"""data/crops.yaml FAO-56 blocks agree with the extracted Tables 12 and 22
(data/fao56_table12_22.yaml, scripts/extract_fao56_table12_22.py)."""

import yaml
import pytest

from app.config import ROOT

T = yaml.safe_load((ROOT / "data" / "fao56_table12_22.yaml").read_text(encoding="utf-8"))
R12 = {r["crop"]: r for r in T["table12"]}
R22 = {r["crop"]: r for r in T["table22"]}
CROPS = yaml.safe_load((ROOT / "data" / "crops.yaml").read_text(encoding="utf-8"))["crops"]
T22_NAME = {"Radish": "Radishes"}  # same crop, different spelling in Table 22
NEW = ["tomato", "onion", "cabbage", "carrot", "cucumber", "watermelon", "melon", "sweet_pepper",
       "eggplant", "lettuce", "spinach", "pumpkin", "radish", "green_bean", "mung_bean"]


def by_row():
    return [c for c in CROPS if (c.get("fao56") or {}).get("row") in R12]


def test_every_new_crop_has_an_extracted_row():
    ids = {c["id"] for c in by_row()}
    assert set(NEW) <= ids
    assert len(ids) >= 29 + len(NEW)


@pytest.mark.parametrize("c", by_row(), ids=lambda c: c["id"])
def test_table12_values_match(c):
    f, r = c["fao56"], R12[c["fao56"]["row"]]
    for k in ("kc_ini", "kc_mid", "kc_end", "max_height_m"):
        assert f.get(k) == r[k], k
    assert bool(f.get("kc_ini_from_group")) == r["kc_ini_from_group"]


@pytest.mark.parametrize("cid", NEW)
def test_table22_values_match_for_new_crops(cid):
    f = next(c for c in CROPS if c["id"] == cid)["fao56"]
    r = R22[T22_NAME.get(f["row"], f["row"])]
    assert (f["root_depth_m"], f["depletion_p"]) == (r["root_depth_m"], r["depletion_p"])
