"""Two-stage rotation search: a vectorised screen of every rule-abiding cycle, then exact scoring.

Stage 1 (screen): the rotation score of app.rotation.scoring *without* the soil water
carried between crops. Without carry-over every sub-score is a ratio of per-plan sums
(plus one pairwise term for "cereal after legume" and the union of families), so many
cycles are scored at once with numpy. Year plans are first ranked by their own screen
total and the best MAX_PLANS are combined into every 2- and 3-year cycle that keeps the
hard rules (app.rotation.engine; one fallow year at most).

Stage 2 (engine.recommend): the best N_CANDIDATES cycles of the screen are scored
exactly (with the carried soil water) and the diverse top rotations are chosen.

Both cuts are heuristics, checked at the demo points (docs/METHOD.md, "Rotation engine", Search):
carried soil water only lowers rain deficits, so the screen total is close to (and not
above) the exact total, but a cycle far down the screen list could still win with a
large carry-over; and a plan that is weak on its own could still fit a cycle well.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.rotation.engine import FIXED_WEIGHTS, PRIORITIES, ROOT_DEPTH_REF_M, Slot
from app.rotation.scoring import CEREAL_GROUPS, SUITABILITY_WEIGHT

N_CANDIDATES = 300   # screened cycles scored exactly
MAX_PER_CROP_SET = 3  # at most this many candidates with the same set of crops (order / windows differ)
MAX_PLANS = 150       # year plans combined, the best by their own screen total (see METHOD)
PER_START_KEEP = 1000  # best cycles kept per first plan / cycle type while screening (memory bound)

Plan = tuple[Slot, ...]


def plan_compat(plans: list[Plan]) -> np.ndarray:
    """compat[i, j]: plan j may follow plan i in the next year (engine.rule_violations):
    no shared crop, and the last crop of i and the first of j are of different families.
    Plans are non-empty; a fallow year is compatible with everything."""
    n = len(plans)
    crop_ids = sorted({s.crop.id for p in plans for s in p})
    fams = sorted({s.crop.family for p in plans for s in p})
    col, fam_i = {c: k for k, c in enumerate(crop_ids)}, {f: k for k, f in enumerate(fams)}
    inc = np.zeros((n, len(crop_ids)), dtype=np.int32)
    for i, p in enumerate(plans):
        for s in p:
            inc[i, col[s.crop.id]] = 1
    shared = (inc @ inc.T) > 0                                    # includes i == j
    first = np.array([fam_i[p[0].crop.family] for p in plans])
    last = np.array([fam_i[p[-1].crop.family] for p in plans])
    return ~shared & (last[:, None] != first[None, :])


@dataclass
class Screen:
    """Rotation score without carried soil water, for many cycles at once.

    Same arguments and the same sub-score definitions as scoring.score(..., carry=None);
    sub-scores are not rounded to 3 decimals here (ranking only)."""
    months_climate: list[dict]
    weights: dict[str, float]
    market_crops: set[str]
    slope: dict | None = None

    def _features(self, plans: list[Plan]) -> dict[str, np.ndarray]:
        wm = {m["month"]: (m.get("heavy_rain_days") or 0.0) + 0.1 for m in self.months_climate} or \
            {m: 1.0 for m in range(1, 13)}
        self._w_year = sum(wm.values())
        fams = sorted({s.crop.family for p in plans for s in p})
        bit = {f: 1 << k for k, f in enumerate(fams)}
        if len(fams) > 63:
            raise ValueError("more than 63 families")
        f: dict[str, list] = {k: [] for k in ("S", "P", "D", "E", "R", "NS", "M", "W", "LEG", "CER", "CIN",
                                               "FC", "LL", "INC", "FOR", "FAM")}
        for p in plans:
            cov = set().union(*(s.months for s in p))
            f["S"].append(sum(s.window["score_median"] for s in p))
            f["P"].append(sum(s.window["score_p20"] for s in p))
            f["D"].append(sum(s.window["rain_deficit_mm_median"] for s in p))
            f["E"].append(sum(s.window["etc_mm_median"] for s in p))
            f["R"].append(sum(min(1.0, (s.crop.root_depth_m or 0) / ROOT_DEPTH_REF_M) for s in p))
            f["NS"].append(len(p))
            f["M"].append(len(cov))
            f["W"].append(sum(wm.get(m, 1.0) for m in cov))
            f["LEG"].append(float(any(s.crop.nitrogen_fixing for s in p)))
            f["CER"].append(sum(s.crop.group in CEREAL_GROUPS for s in p))
            f["CIN"].append(sum(p[k].crop.group in CEREAL_GROUPS and p[k - 1].crop.nitrogen_fixing
                                for k in range(1, len(p))))
            f["FC"].append(float(p[0].crop.group in CEREAL_GROUPS))
            f["LL"].append(float(p[-1].crop.nitrogen_fixing))
            f["INC"].append(sum(s.crop.id in self.market_crops for s in p))
            f["FOR"].append(sum(s.crop.group == "forage" for s in p))
            fam = 0
            for s in p:
                fam |= bit[s.crop.family]
            f["FAM"].append(fam)
        out = {k: np.array(v, dtype=np.uint64 if k == "FAM" else float) for k, v in f.items()}
        out["X"] = np.outer(out["LL"], out["FC"])  # X[i, j]: cereal first in j after legume last in i
        return out

    def totals(self, sums: dict[str, np.ndarray], fam: np.ndarray, cross: np.ndarray,
               n_years: np.ndarray | int) -> np.ndarray:
        """Total score from the summed plan features of cycles (1-D arrays)."""
        w = {k: float(self.weights.get(k, 3.0)) for k in PRIORITIES} | FIXED_WEIGHTS |             {"suitability": SUITABILITY_WEIGHT}
        ns = sums["NS"]
        with np.errstate(divide="ignore", invalid="ignore"):
            sub = {
                "suitability": sums["S"] / n_years,
                "climate_risk": sums["P"] / ns,
                "water": 1 - sums["D"] / sums["E"],          # nan / -inf when no crop water use: unknown
                "soil": 0.5 * sums["R"] / ns + 0.5 * sums["M"] / (12 * n_years),
                "nitrogen": 0.6 * sums["LEG"] / n_years
                            + 0.4 * np.where(sums["CER"] > 0, (sums["CIN"] + cross) / sums["CER"], 0.0),
                "forage": sums["FOR"] / ns,
                "diversity": np.bitwise_count(fam) / ns,
            }
            covered = sums["W"] / (self._w_year * n_years)
            if self.slope and self.slope.get("status") == "ok":
                sub["erosion"] = 1 - (1 - covered) * self.slope["relative_s"]
            else:
                sub["erosion"] = covered
            if self.market_crops:
                sub["income"] = sums["INC"] / ns
        num = np.zeros(len(ns))
        den = np.zeros(len(ns))
        for k, v in sub.items():
            if w[k] <= 0:
                continue
            if k == "water":
                known = sums["E"] > 0
                num += np.where(known, w[k] * np.clip(np.nan_to_num(v), 0.0, 1.0), 0.0)
                den += np.where(known, w[k], 0.0)
            else:
                num += w[k] * np.clip(v, 0.0, 1.0)
                den += w[k]
        return np.where(den > 0, num / np.where(den > 0, den, 1), 0.0)

    def cycles(self, plans: list[Plan], max_fallow: int = 1) -> tuple[np.ndarray, np.ndarray]:
        """Screen totals of every rule-abiding 2- and 3-year cycle of `plans` (+ one fallow year).

        Returns (totals, cycles): cycles is an (n, 3) int array of plan indices per year,
        -1 = fallow year, -2 = no third year (2-year cycle). Each cycle appears once
        (not once per starting year)."""
        n = len(plans)
        if n == 0:
            return np.zeros(0), np.zeros((0, 3), dtype=int)
        f = self._features(plans)
        c = plan_compat(plans)
        X = f["X"]
        keys = [k for k in f if k not in ("X", "FAM")]
        # features of a fallow / missing year are 0: extra zero rows at index n (-1) and n + 1 (-2)
        F = np.vstack([np.stack([f[k] for k in keys], axis=1), np.zeros((2, len(keys)))])
        fam = np.concatenate([f["FAM"], np.zeros(2, dtype=np.uint64)])
        tots: list[np.ndarray] = []
        cycs: list[np.ndarray] = []

        def add(A, B, C, cross, keep: int | None = None):
            if not len(cross):
                return
            A, B, C = (np.broadcast_to(np.asarray(x, dtype=int), cross.shape) for x in (A, B, C))
            ia, ib, ic = (np.where(x < 0, n - 1 - x, x) for x in (A, B, C))   # -1 -> n, -2 -> n + 1
            m = F[ia] + F[ib] + F[ic]
            tot = self.totals({k: m[:, i] for i, k in enumerate(keys)}, fam[ia] | fam[ib] | fam[ic], cross,
                              np.where(C == -2, 2, 3))
            if keep is not None and len(tot) > keep:
                sel = np.sort(np.argpartition(-tot, keep)[:keep])
                tot, A, B, C = tot[sel], A[sel], B[sel], C[sel]
            tots.append(tot)
            cycs.append(np.stack([A, B, C], axis=1))

        # 2-year cycles: (a, b) with a < b, compatible both ways
        ia, ib = np.nonzero(np.triu(c & c.T, 1))
        add(ia, ib, -2, X[ia, ib] + X[ib, ia])
        if max_fallow >= 1:
            ia = np.arange(n)                      # (a, fallow)
            add(ia, -1, -2, X[ia, ia])
            ia, ib = np.nonzero(c)                 # (a, b, fallow): a -> b; both orders are cycles
            add(ia, ib, -1, X[ia, ib] + X[ib, ia])
        # 3-year cycles without fallow: a is the smallest index (one entry per cycle). Up to ~10
        # million cycles with ~400 plans: only the PER_START_KEEP best per a are kept.
        for a in range(n):
            bs = np.flatnonzero(c[a, a + 1:]) + a + 1          # a -> b
            cs = np.flatnonzero(c[a + 1:, a]) + a + 1          # c -> a
            if not len(bs) or not len(cs):
                continue
            bi, ci = np.nonzero(c[np.ix_(bs, cs)])             # b -> c (also excludes b == c)
            b_, c_ = bs[bi], cs[ci]
            add(a, b_, c_, X[a, b_] + X[b_, c_] + X[c_, a], PER_START_KEEP)
        if not tots:
            return np.zeros(0), np.zeros((0, 3), dtype=int)
        return np.concatenate(tots), np.concatenate(cycs)

    def plan_totals(self, plans: list[Plan]) -> np.ndarray:
        """Screen total of each year plan on its own (a 1-year "cycle"; rules not applied)."""
        if not plans:
            return np.zeros(0)
        f = self._features(plans)
        return self.totals({k: f[k] for k in f if k not in ("X", "FAM")}, f["FAM"], np.diag(f["X"]), 1)

    def top_cycles(self, plans: list[Plan], k: int = N_CANDIDATES, max_fallow: int = 1,
                   per_crop_set: int = MAX_PER_CROP_SET,
                   max_plans: int | None = MAX_PLANS) -> list[tuple[float, tuple[int, ...]]]:
        """The k best screened cycles (indices into `plans`, -1 = fallow), at most per_crop_set
        with the same set of crops. Only the max_plans best plans by plan_totals are combined."""
        keep = np.arange(len(plans))
        if max_plans is not None and len(plans) > max_plans:
            keep = np.sort(np.argsort(-self.plan_totals(plans), kind="stable")[:max_plans])
        tot, cyc = self.cycles([plans[i] for i in keep], max_fallow)
        cyc = np.where(cyc >= 0, keep[np.clip(cyc, 0, None)], cyc)   # back to indices into `plans`
        order = np.lexsort((np.arange(len(tot)), -tot))  # stable: ties keep enumeration order
        crop_sets = [frozenset(s.crop.id for s in p) for p in plans]
        seen: dict[frozenset, int] = {}
        out = []
        for i in order:
            years = tuple(int(j) for j in cyc[i] if j != -2)
            key = frozenset().union(*(crop_sets[j] for j in years if j >= 0))
            if seen.get(key, 0) >= per_crop_set:
                continue
            seen[key] = seen.get(key, 0) + 1
            out.append((float(tot[i]), years))
            if len(out) == k:
                break
        return out
