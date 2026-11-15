"""Rotation engine (stage 4): rule-based generation and scoring of 3-year rotations.

Inputs are the per-crop suitability results (sowing windows over 25 years),
the monthly climate profile and the user's priorities and constraints.

* A *slot* is one crop grown in one season (a sowing window).
* A *year plan* is one slot, or two slots whose season months do not overlap
  (double cropping, e.g. rice then wheat).
* A *rotation* is a cycle of YEARS year plans.

Hard rules (a rotation that breaks one is never recommended; the user's
current rotation is scored anyway and the broken rules are reported):
  - no two consecutive slots of the same botanical family (also across the
    cycle boundary), which also breaks pest/disease cycles;
  - the same crop is not grown in consecutive years;
  - crops the user excluded, or that need equipment the user lacks, are not used.

Everything here is rules and arithmetic, not ML. Sub-scores are documented in
SUBSCORES and docs/METHOD.md; proxies are labelled as such.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field

from app.suitability.crops import Crop

YEARS = 3                   # reference / default cycle length
CYCLE_LENGTHS = (2, 3)      # recommended rotations may be 2- or 3-year cycles
MIN_SLOT_SCORE = 0.2        # crops/windows scoring below this are never used in recommendations ...
RELATIVE_SLOT_SCORE = 0.5   # ... nor below half of the best crop's score at this point
MAX_FALLOW_YEARS = 1        # a fallow year (no crop) may appear at most once per cycle
ALT_WINDOW_SHARE = 0.8      # alternative sowing windows must reach 80 % of the crop's best
MAX_ALT_WINDOWS = 4
PLAN_POOL = 30              # year plans searched exhaustively when no screen is given (tests)
N_RECOMMENDED = 3
MIN_DISTANCE = 0.5          # Jaccard distance between crop sets of recommended rotations
ROOT_DEPTH_REF_M = 1.5      # root depth giving full credit in the soil-structure proxy

PRIORITIES = ("water", "soil", "erosion", "nitrogen", "income", "forage")
# Always included, not user-weighted: risk in bad years, and family diversity.
FIXED_WEIGHTS = {"climate_risk": 3.0, "diversity": 1.0}

EQUIPMENT_EXCLUSIONS = {
    "no_root_harvester": lambda c: c.group == "root_tuber",
    "no_paddy": lambda c: c.id == "rice",
}


@dataclass(frozen=True)
class Slot:
    crop: Crop
    window: dict  # one entry of evaluate_crop(...)["windows"]
    months: frozenset[int]

    @property
    def score(self) -> float:
        return self.window["score_median"]


@dataclass
class Rotation:
    kind: str                     # "recommended" | "current" | "reference"
    years: list[tuple[Slot, ...]]
    missing_slots: list[dict] = field(default_factory=list)  # current-rotation crops we cannot model

    @property
    def slots(self) -> list[Slot]:
        return [s for y in self.years for s in y]

    def crop_ids(self) -> list[str]:
        return [s.crop.id for s in self.slots] + [m["crop_id"] for m in self.missing_slots]


def season_months(window: dict) -> frozenset[int]:
    return frozenset(window["season_months"])


def slot_threshold(results: dict[str, dict]) -> float:
    best = max((r["best_window"]["score_median"] for r in results.values() if r.get("status") == "evaluated"),
               default=0.0)
    return max(MIN_SLOT_SCORE, RELATIVE_SLOT_SCORE * best)


def make_slots(crop: Crop, result: dict, threshold: float = MIN_SLOT_SCORE) -> list[Slot]:
    """Best window plus up to MAX_ALT_WINDOWS alternatives that score >= 80 % of it.

    Cut forage modelled only to its first cut (crop.first_cut_only) gets no slots: its
    real field occupancy (several cuts) is unknown, so it would look like a cheap short crop."""
    if result.get("status") != "evaluated" or crop.first_cut_only:
        return []
    best = result["best_window"]
    if best["score_median"] < threshold:
        return []
    in_cal = (lambda w: w.get("in_local_calendar") is not False) if result.get("calendar_rule") else (lambda w: True)
    alts = [w for w in result["windows"]
            if w is not best and in_cal(w)
            and w["score_median"] >= max(threshold, ALT_WINDOW_SHARE * best["score_median"])]
    alts.sort(key=lambda w: -w["score_median"])
    return [Slot(crop, w, season_months(w)) for w in [best, *alts[:MAX_ALT_WINDOWS]]]


def allowed(crop: Crop, constraints: dict) -> bool:
    if crop.id in set(constraints.get("excluded_crops") or []):
        return False
    for eq in constraints.get("equipment_limits") or []:
        rule = EQUIPMENT_EXCLUSIONS.get(eq)
        if rule and rule(crop):
            return False
    return True


def year_plans(slots_by_crop: dict[str, list[Slot]]) -> list[tuple[Slot, ...]]:
    """Single-crop years (best window) and compatible double-crop years."""
    plans: list[tuple[Slot, ...]] = [(slots[0],) for slots in slots_by_crop.values()]
    ids = list(slots_by_crop)
    for a, b in itertools.combinations(ids, 2):
        best_pair, best_val = None, -1.0
        for sa in slots_by_crop[a]:
            for sb in slots_by_crop[b]:
                if sa.crop.family == sb.crop.family or sa.months & sb.months:
                    continue
                if len(sa.months) + len(sb.months) > 12:
                    continue
                val = sa.score + sb.score
                if val > best_val:
                    best_pair, best_val = (sa, sb), val
        if best_pair:
            # order by sowing month within the calendar year
            plans.append(tuple(sorted(best_pair, key=lambda s: s.window["sowing"])))
    return plans


def rule_violations(rotation: Rotation) -> list[dict]:
    """Broken rules. A fallow year (empty year) breaks both the family and the repeat sequence."""
    out = []
    seq: list[Slot | None] = [s for y in rotation.years for s in (y or (None,))]
    n = len(seq)
    for i in range(n):
        a, b = seq[i], seq[(i + 1) % n]
        if n > 1 and a is not None and b is not None and a.crop.family == b.crop.family:
            out.append({"code": "same_family_consecutive", "crops": [a.crop.id, b.crop.id], "family": a.crop.family})
    ys = rotation.years
    for i in range(len(ys)):
        prev = {s.crop.id for s in ys[i - 1]} if len(ys) > 1 else set()
        repeated = prev & {s.crop.id for s in ys[i]}
        for cid in sorted(repeated):
            out.append({"code": "same_crop_consecutive_years", "crops": [cid]})
    for y in ys:  # two crops in one year must not overlap in time
        if len(y) == 2 and y[0].months & y[1].months:
            out.append({"code": "seasons_overlap", "crops": [y[0].crop.id, y[1].crop.id]})
    unique, seen = [], set()
    for v in out:
        key = (v["code"], tuple(sorted(v["crops"])))
        if key not in seen:
            seen.add(key)
            unique.append(v)
    return unique


def _jaccard_distance(a: set[str], b: set[str]) -> float:
    return 1 - len(a & b) / len(a | b) if a | b else 0.0


def candidate_cycles(plans: list[tuple[Slot, ...]]) -> list[Rotation]:
    """Every rule-abiding 2- and 3-year cycle over `plans` (+ fallow years), once per cycle.
    Exhaustive: only for small plan lists (tests, no screen)."""
    pool = plans + [()]  # () = fallow year
    out, seen = [], set()
    for length in CYCLE_LENGTHS:
        for combo in itertools.product(pool, repeat=length):
            if sum(1 for y in combo if not y) > MAX_FALLOW_YEARS or all(not y for y in combo):
                continue
            # a cycle is the same rotation whichever year it starts in
            ids = tuple(tuple(id(s) for s in y) for y in combo)
            key = min(ids[i:] + ids[:i] for i in range(length))
            if key in seen:
                continue
            seen.add(key)
            rot = Rotation("recommended", list(combo))
            if not rule_violations(rot):
                out.append(rot)
    return out


def recommend(slots_by_crop: dict[str, list[Slot]], score_fn, n: int = N_RECOMMENDED,
              on_candidates=None, screen=None) -> list[Rotation]:
    """Search 2- and 3-year cycles of year plans; return n diverse, rule-abiding rotations.

    With a `screen` (app.rotation.search.Screen) every rule-abiding cycle over *all* year
    plans is ranked by the rotation score without carried soil water, and only the best
    search.N_CANDIDATES are scored with score_fn. Without one, cycles over the PLAN_POOL
    best plans (by crop score) are all scored with score_fn (small inputs, tests).

    on_candidates(rotations) is called once before exact scoring (e.g. to simulate the soil
    water carried between crops in one vectorised pass)."""
    plans = year_plans(slots_by_crop)
    plans.sort(key=lambda p: -sum(s.score for s in p) / len(p) - 0.05 * (len(p) - 1))
    if screen is None:
        candidates = candidate_cycles(plans[:PLAN_POOL])
    else:
        candidates = [Rotation("recommended", [plans[i] if i >= 0 else () for i in cyc])
                      for _, cyc in screen.top_cycles(plans, max_fallow=MAX_FALLOW_YEARS)]
    if on_candidates is not None:
        on_candidates(candidates)
    scored = [(score_fn(rot)["total"], rot) for rot in candidates]
    scored.sort(key=lambda x: -x[0])
    chosen: list[Rotation] = []
    for _, rot in scored:
        crops = set(rot.crop_ids())
        if all(_jaccard_distance(crops, set(c.crop_ids())) >= MIN_DISTANCE for c in chosen):
            chosen.append(rot)
        if len(chosen) == n:
            break
    return chosen


def current_rotation(crop_ids_by_year: list[list[str]], crops: dict[str, Crop], results: dict[str, dict]) -> Rotation:
    """The user's rotation, scored as-is with each crop's best window (even if poorly suited)."""
    years, missing = [], []
    for y, ids in enumerate(crop_ids_by_year):
        options: list[list[Slot]] = []
        for cid in ids:
            crop, res = crops.get(cid), results.get(cid, {})
            if crop is None or not res.get("windows"):
                missing.append({"year": y + 1, "crop_id": cid, "status": res.get("status", "unknown_crop")})
                continue
            # local-calendar windows first (when the rule is on), then by score
            ws = sorted(res["windows"], key=lambda w: (res.get("calendar_rule") and w.get("in_local_calendar") is False,
                                                        -w["score_median"]))
            options.append([Slot(crop, w, season_months(w)) for w in ws])
        years.append(tuple(sorted(_fit_year(options), key=lambda s: s.window["sowing"])))
    return Rotation("current", years, missing)


def _fit_year(options: list[list[Slot]]) -> list[Slot]:
    """Best window per crop; for two crops in one year, the best pair whose seasons do not overlap."""
    if len(options) != 2:
        return [o[0] for o in options]
    pairs = [(a, b) for a in options[0] for b in options[1]
             if not a.months & b.months and len(a.months) + len(b.months) <= 12]
    if not pairs:
        return [options[0][0], options[1][0]]  # cannot fit: keep best windows, overlap shows as a risk
    return list(max(pairs, key=lambda p: p[0].score + p[1].score))


def monoculture_reference(slots_by_crop: dict[str, list[Slot]]) -> Rotation | None:
    """Reference when the current rotation is unknown: the single best crop every year."""
    if not slots_by_crop:
        return None
    best = max(slots_by_crop.values(), key=lambda s: s[0].score)[0]
    return Rotation("reference", [(best,)] * YEARS)
