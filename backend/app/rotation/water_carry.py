"""Soil water carried from one crop to the next (fallow and other gaps) — physics + labelled assumptions.

For every pair (crop A, crop B) that follows in a rotation, and every year of
the climate record, the gap from A's harvest to B's sowing is simulated with
the FAO-56 bare-soil daily balance (app.water.fao56_soil, ch. 7/8/11):

* B's sowing is the first occurrence of B's sowing date after A's harvest,
  plus one year per fallow year in between (a fallow year is a long gap).
* The root zone is B's FAO-56 Table 22 root depth; TAW and TEW come from
  SoilGrids (eq. 82, 73).
* Assumptions (docs/METHOD.md): the profile is empty at A's harvest (Dr = TAW,
  De = TEW); REW = 9 mm (FAO-56 Table 19 has no clay-loam row; neighbours
  8-12 mm), capped at TEW; no runoff, weeds, residue cover, snow or frost effects.

The water stored at B's sowing covers B's 10-day rain deficits first
(decision K1-A). B's season score, bad-year score and failure rate are then
recomputed per year from the suitability rows. With no stored water every
number equals the suitability result.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from app.rotation.engine import Rotation, Slot
from app.sources.soilgrids import SoilWater
from app.suitability.engine import FAIL_SCORE, ClimateArrays, remaining_deficit, season_rows
from app.water.fao56_soil import gap_balance

REW_MM = 9.0          # assumption, see module docstring
MIN_PAIRED_YEARS = 5  # fewer paired years than this: no carry-over is applied (reported)


@dataclass
class Transition:
    """Gap from slot A to slot B, per paired year."""
    n_fallow: int
    years: list[int] = field(default_factory=list)        # B's sowing years
    stored: np.ndarray = field(default_factory=lambda: np.zeros(0))
    precip: np.ndarray = field(default_factory=lambda: np.zeros(0))
    evaporation: np.ndarray = field(default_factory=lambda: np.zeros(0))
    deep_percolation: np.ndarray = field(default_factory=lambda: np.zeros(0))
    gap_days: np.ndarray = field(default_factory=lambda: np.zeros(0))
    taw: float = 0.0

    @property
    def usable(self) -> bool:
        return len(self.years) >= MIN_PAIRED_YEARS


class WaterCarry:
    def __init__(self, clim: ClimateArrays, soil: SoilWater, irrigation: str,
                 light_refs: dict[str, dict]):
        self.clim, self.soil, self.irrigation = clim, soil, irrigation
        self.light_refs = light_refs      # crop id -> suitability result["light_ref"]
        self.tew = soil.tew_mm()
        self._rows: dict[int, dict[int, dict]] = {}       # id(slot) -> {sowing year: row}
        self._trans: dict[tuple[int, int, int], Transition] = {}
        self._slots: dict[int, Slot] = {}                 # keep slots alive while ids are cached

    @property
    def available(self) -> bool:
        return self.tew is not None

    # -- per-year rows of a slot ------------------------------------------------------
    def rows(self, s: Slot) -> dict[int, dict]:
        key = id(s)
        if key not in self._rows:
            m, d = map(int, s.window["sowing"].split("-"))
            ref = self.light_refs.get(s.crop.id)
            rows = season_rows(s.crop, self.clim, self.irrigation, [(m, d)], ref)
            self._rows[key] = {r["year"]: r for r in rows.get(s.window["sowing"], [])}
            self._slots[key] = s
        return self._rows[key]

    def _taw(self, s: Slot) -> float | None:
        return None if s.crop.root_depth_m is None else self.soil.taw_mm(s.crop.root_depth_m)

    # -- transitions --------------------------------------------------------------------
    def prepare(self, pairs: list[tuple[Slot, Slot, int]]) -> None:
        """Simulate many transitions in one vectorised pass (cached)."""
        todo = [(a, b, k) for a, b, k in pairs if (id(a), id(b), k) not in self._trans]
        if not todo or not self.available:
            return
        dates = self.clim.dates
        runs_start, runs_len, runs_taw, owner, b_year = [], [], [], [], []
        metas = []
        for a, b, k in todo:
            t = Transition(k)
            taw = self._taw(b)
            metas.append((a, b, k, t))
            if taw is None:
                continue
            t.taw = taw
            rows_a, rows_b = self.rows(a), self.rows(b)
            b_sowings = sorted((r["i0"], y) for y, r in rows_b.items())  # B's sowing day per year
            b_i0 = np.array([i for i, _ in b_sowings], dtype=int)
            for ra in rows_a.values():
                h = ra["i1"]  # first day after A's season
                pos = int(np.searchsorted(b_i0, h)) + k  # next B sowing after the harvest, + fallow years
                if pos >= len(b_sowings):
                    continue
                sb, yb = b_sowings[pos]
                if k and dates[sb].year - dates[b_i0[pos - k]].year != k:
                    continue  # a year is missing from B's rows: do not skip over it
                runs_start.append(h)
                runs_len.append(sb - h)
                runs_taw.append(taw)
                owner.append(len(metas) - 1)
                b_year.append(yb)
        if runs_start:
            res = gap_balance(self.clim.precip, self.clim.et0, np.array(runs_start), np.array(runs_len),
                              np.array(runs_taw), self.tew, min(REW_MM, self.tew))
            owner_a = np.array(owner)
            for j, (_, _, _, t) in enumerate(metas):
                sel = np.flatnonzero(owner_a == j)
                t.years = [b_year[i] for i in sel]
                t.stored, t.precip = res.stored[sel], res.precip[sel]
                t.evaporation, t.deep_percolation = res.evaporation[sel], res.deep_percolation[sel]
                t.gap_days = np.array(runs_len)[sel]
        for a, b, k, t in metas:
            self._trans[(id(a), id(b), k)] = t

    def transition(self, a: Slot, b: Slot, n_fallow: int) -> Transition:
        key = (id(a), id(b), n_fallow)
        if key not in self._trans:
            self.prepare([(a, b, n_fallow)])
        return self._trans.get(key, Transition(n_fallow))

    def prepare_rotations(self, rotations: list[Rotation]) -> None:
        """Exactly the transitions the given rotations use, in one vectorised pass."""
        pairs = {(id(prev), id(s), k): (prev, s, k)
                 for r in rotations for s, prev, k in predecessors(r) if prev is not None}
        self.prepare(list(pairs.values()))

    # -- effect on a slot ---------------------------------------------------------------
    def effective(self, b: Slot, t: Transition) -> dict:
        """B's window statistics with the stored water of transition t."""
        if not t.usable:
            return {}
        if float(np.max(t.stored)) < 0.5:
            return {}  # nothing stored: the suitability numbers stand unchanged
        rows = self.rows(b)
        by_year = dict(zip(t.years, t.stored))
        scores, deficits, etcs, matured = [], [], [], []
        for y, r in rows.items():
            stored = by_year.get(y, 0.0)  # years without a predecessor in the record: no stored water
            rem = remaining_deficit(r["deficit"], self.irrigation, stored)
            water = 1.0 - rem / r["etc"] if r["etc"] > 0 else 1.0
            scores.append(r["temp"] * water * r["duration"] * r["light"] if r["matured"] else 0.0)
            deficits.append(max(0.0, r["deficit"] - stored))
            etcs.append(r["etc"])
            matured.append(r["matured"])
        scores, matured = np.array(scores), np.array(matured)
        eff = float(np.median(t.precip)) or 0.0
        return {
            "score_median": round(float(np.median(scores)), 3),
            "score_p20": round(float(np.percentile(scores, 20)), 3),
            "fail_rate": round(float(((scores < FAIL_SCORE) | ~matured).mean()), 2),
            "rain_deficit_mm_median": round(float(np.median(deficits)), 0),
            "etc_mm_median": round(float(np.median(etcs)), 0),
            "carry": {
                "n_fallow_years": t.n_fallow,
                "n_years": len(t.years),
                "gap_days_median": int(np.median(t.gap_days)),
                "gap_rain_mm_median": round(eff),
                "stored_mm_median": round(float(np.median(t.stored))),
                "stored_mm_p20": round(float(np.percentile(t.stored, 20))),
                "stored_mm_p80": round(float(np.percentile(t.stored, 80))),
                "storage_efficiency_median": (round(float(np.median(t.stored / np.maximum(t.precip, 1e-9))), 2)
                                              if eff > 0 else None),
                "evaporation_mm_median": round(float(np.median(t.evaporation))),
                "deep_percolation_mm_median": round(float(np.median(t.deep_percolation))),
                "taw_mm": round(t.taw),
                "score_median_without": b.window["score_median"],
            },
        }


def predecessors(rot: Rotation) -> list[tuple[Slot, Slot | None, int]]:
    """(slot, previous slot in the cycle or None, fallow years in between), in slot order.

    An empty year is a fallow year, unless it is empty because the user's crop could not be
    modelled (rot.missing_slots): then the previous crop is unknown and nothing is carried.
    """
    unknown_years = {m["year"] for m in rot.missing_slots}
    seq: list = []
    for yi, y in enumerate(rot.years, start=1):
        seq += list(y) if y else (["unknown"] if yi in unknown_years else [None])
    out = []
    for i, s in enumerate(seq):
        if s is None or s == "unknown":
            continue
        j, n_fallow, prev = i, 0, None
        for _ in range(len(seq)):
            j = (j - 1) % len(seq)
            if seq[j] is None:
                n_fallow += 1
                continue
            prev = None if seq[j] == "unknown" else seq[j]
            break
        out.append((s, prev, n_fallow))
    return out


def effective_windows(rot: Rotation, carry: WaterCarry | None) -> list[dict]:
    """Per slot (in rot.slots order): its window, updated by the carried-over soil water."""
    out = []
    for s, prev, k in predecessors(rot):
        w = dict(s.window)
        if carry is not None and carry.available and prev is not None:
            w.update(carry.effective(s, carry.transition(prev, s, k)))
        out.append(w)
    return out
