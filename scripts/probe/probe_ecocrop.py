"""Probe: FAO ECOCROP data sheets (https://ecocrop.apps.fao.org/ecocrop/srv/en/cropSearchForm).

Licence: none stated on the site (checked 2026-11-03 and 2026-11-12); used by
user decision with a label, see docs/DATA_SOURCES.md §5. Only the values we
use are copied by hand into data/crop_phenology.yaml; no bulk data is stored.

For each species: name search (`cropListDetails`, exact match), then the data
sheet (`dataSheet?id=`). Prints the temperature ranges (optimal min/max,
absolute min/max), crop cycle (days), killing temperatures and the sheet URL.
One request per second. Raw HTML goes to scripts/probe/out/ (git-ignored).

Run: backend/.venv/Scripts/python scripts/probe/probe_ecocrop.py [crop_id ...]
"""

from __future__ import annotations

import re
import sys
import time
import urllib.parse
import urllib.request

from _common import report, save

BASE = "https://ecocrop.apps.fao.org/ecocrop/srv/en"
SPECIES = {
    "oats": "Avena sativa", "faba_bean": "Vicia faba", "dry_pea": "Pisum sativum",
    "cowpea": "Vigna unguiculata", "safflower": "Carthamus tinctorius", "sesame": "Sesamum indicum",
    "flax": "Linum usitatissimum", "sweet_potato": "Ipomoea batatas", "sugar_beet": "Beta vulgaris",
    "chickpea": "Cicer arietinum", "cereal_rye": "Secale cereale",
    # new crops (2026-11-13)
    "tomato": "Lycopersicon esculentum", "onion": "Allium cepa",
    "cabbage": "Brassica oleracea var. capitata", "carrot": "Daucus carota",
    "cucumber": "Cucumis sativus", "watermelon": "Citrullus lanatus", "melon": "Cucumis melo",
    "sweet_pepper": "Capsicum annuum", "eggplant": "Solanum melongena",
    "lettuce": "Lactuca sativa var. capitata", "spinach": "Spinacia oleracea",
    "pumpkin": "Cucurbita maxima", "radish": "Raphanus sativus", "green_bean": "Phaseolus vulgaris",
    "mung_bean": "Vigna radiata",
    # still insufficient_data (search 2026-11-14)
    "rapeseed": "Brassica napus", "mustard": "Sinapis alba", "buckwheat": "Fagopyrum esculentum",
    "ryegrass": "Lolium multiflorum", "berseem_clover": "Trifolium alexandrinum",
    "vetch": "Vicia sativa", "phacelia": "Phacelia tanacetifolia", "sudan_grass": "Sorghum sudanense",
    "sudan_grass_x": "Sorghum x drummondii", "brown_mustard": "Brassica juncea",
    "hairy_vetch": "Vicia villosa", "rapeseed_campestris": "Brassica rapa",
}


def get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "etugen-probe"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def plain(html: str) -> str:
    t = re.sub(r"<script.*?</script>", " ", html, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    for a, b in (("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">")):
        t = t.replace(a, b)
    return re.sub(r"\s+", " ", t)


def numbers(t: str, label: str, n: int) -> list[float | None] | None:
    m = re.search(re.escape(label) + r"((?:\s+(?:-?\d+(?:\.\d+)?|NaN|---|-)){%d})" % n, t)
    if not m:
        return None
    return [None if v in ("NaN", "---", "-") else float(v) for v in m.group(1).split()]


def main() -> None:
    wanted = sys.argv[1:] or list(SPECIES)
    for cid in wanted:
        sp = SPECIES[cid]
        q = urllib.parse.urlencode({"code": "", "relation": "matches", "name": sp, "quantity": "25"})
        hits = re.findall(r"cropView\?id=(\d+)%22\)\" class=\"serviceLink\">([^<]+)",
                          get(f"{BASE}/cropListDetails?{q}"))
        ids = [i for i, name in hits if name.strip().lower() == sp.lower()]
        if not ids:
            report(f"ECOCROP {cid}", False, {"species": sp, "error": "no exact match"})
            continue
        url = f"{BASE}/dataSheet?id={ids[0]}"
        html = get(url)
        save(f"ecocrop_{cid}.html", html)
        t = plain(html)
        temp = numbers(t, "Temperat. requir.", 4)  # optimal min, optimal max, absolute min, absolute max
        report(f"ECOCROP {cid}", temp is not None and None not in temp, {
            "species": sp, "url": url,
            "temp [opt min, opt max, abs min, abs max] C": temp,
            "crop cycle [min, max] days": numbers(t, "Crop cycle", 2),
            "killing temp during rest / early growth C": (numbers(t, "Killing temp. during rest", 1),
                                                          numbers(t, "Killing temp. early growth", 1)),
        })
        time.sleep(1.0)


if __name__ == "__main__":
    main()
