"""FAO-56 soil water balance between crops (fallow and other gaps) — physics.

Allen, R.G., Pereira, L.S., Raes, D., Smith, M. (1998). FAO Irrigation and
Drainage Paper 56. Equation numbers refer to that paper:

* ch. 7 (dual crop coefficient), topsoil evaporation layer Ze:
  Ke = min(Kr (Kc max - Kcb), few Kc max)            eq. 71
  Kc max                                              eq. 72
  TEW = 1000 (theta_FC - 0.5 theta_WP) Ze             eq. 73
  Kr = (TEW - De,i-1) / (TEW - REW), 1 while De <= REW eq. 74
  few = min(1 - fc, fw)                               eq. 75
  fc = ((Kcb - Kc min) / (Kc max - Kc min))^(1 + 0.5 h) eq. 76
  De,i = De,i-1 - (P - RO) - I/fw + E/few + Tew + DPe  eq. 77, 0 <= De <= TEW (eq. 78)
  DPe = (P - RO) + I/fw - De,i-1 >= 0                  eq. 79
* ch. 8, root zone:
  TAW = 1000 (theta_FC - theta_WP) Zr                 eq. 82 (app.sources.soilgrids)
  Ks = (TAW - Dr) / ((1 - p) TAW), 1 while Dr <= p TAW eq. 84
  Dr,i = Dr,i-1 - (P - RO) - I + ETc + DP              eq. 85, 0 <= Dr <= TAW (eq. 86)
  DP = (P - RO) + I - ETc - Dr,i-1 >= 0                eq. 88
* ch. 11 (non-growing periods, bare soil): Kcb = 0 and Kc min = 0, daily
  balance of topsoil and root zone. With h = 0 eq. 72 gives Kc max = 1.20.

Order within a day follows Example 35 (column 9): rain is assumed to fall
early in the day, so the topsoil depletion is reduced before Kr is computed.

Assumptions (labelled in docs/METHOD.md): runoff RO = 0; transpiration from
the evaporation layer Tew = 0 (FAO-56: small, "can generally be ignored");
no irrigation in the gap; frozen soil and snow are not treated separately.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

KC_MAX_BARE = 1.20   # eq. 72 with h = 0 (and Kcb = 0); also the value used in Example 31
ZE_M = 0.10          # depth of the evaporation layer (FAO-56: 0.10-0.15 m where unknown)


def kc_max(u2: float, rh_min: float, h: float, kcb: float) -> float:
    """FAO-56 eq. 72."""
    return max(1.2 + (0.04 * (u2 - 2) - 0.004 * (rh_min - 45)) * (h / 3) ** 0.3, kcb + 0.05)


def kr(de_prev, tew, rew):
    """FAO-56 eq. 74 (Kr = 1 in stage 1, De <= REW). Works on scalars and arrays."""
    de_prev, tew, rew = np.asarray(de_prev, float), np.asarray(tew, float), np.asarray(rew, float)
    stage2 = np.clip((tew - de_prev) / np.maximum(tew - rew, 1e-9), 0.0, 1.0)
    return np.where(de_prev <= rew, 1.0, stage2)


def fc_from_kcb(kcb, kc_min: float, kcmax: float, h: float):
    """FAO-56 eq. 76: fraction of ground covered by vegetation, from Kcb (0.01-1)."""
    ratio = np.clip((np.asarray(kcb, float) - kc_min) / (kcmax - kc_min), 0.0, 1.0)
    return np.clip(ratio ** (1 + 0.5 * h), 0.0, 0.99)


def ks(dr_prev, taw, p):
    """FAO-56 eq. 84 (Ks = 1 while Dr <= RAW = p TAW)."""
    dr_prev, taw = np.asarray(dr_prev, float), np.asarray(taw, float)
    raw = p * taw
    return np.where(dr_prev <= raw, 1.0, np.clip((taw - dr_prev) / np.maximum(taw - raw, 1e-9), 0.0, 1.0))


@dataclass
class TopsoilDay:
    de_start: float
    kr: float
    ke: float
    e: float        # Ke ETo, over the whole field (mm)
    dpe: float      # eq. 79
    de_end: float


def topsoil_day(de_prev: float, et0: float, tew: float, rew: float, p: float = 0.0, irr: float = 0.0,
                fw: float = 1.0, few: float = 1.0, kcb: float = 0.0, kcmax: float = KC_MAX_BARE) -> TopsoilDay:
    """One day of the FAO-56 topsoil balance (eq. 71, 74, 77-79), scalar reference version.

    `irr` is the irrigation depth (I), `fw` the fraction wetted by it; kept so that the
    FAO-56 worked examples can be reproduced in tests. The fallow model has irr = 0.
    """
    wet = p + (irr / fw if irr else 0.0)
    dpe = max(0.0, wet - de_prev)
    de_start = max(0.0, de_prev - wet)
    k_r = float(kr(de_start, tew, rew))
    ke = min(k_r * (kcmax - kcb), few * kcmax)
    e = ke * et0
    de_end = min(tew, max(0.0, de_start + e / few))
    return TopsoilDay(de_start, k_r, ke, e, dpe, de_end)


@dataclass
class GapResult:
    """Per run (one gap in one year): state at the end and fluxes over the gap (mm)."""
    dr_end: np.ndarray     # root-zone depletion at the end of the gap
    de_end: np.ndarray     # topsoil depletion at the end
    stored: np.ndarray     # TAW - dr_end: plant-available water at the next sowing
    precip: np.ndarray     # rain in the gap
    evaporation: np.ndarray
    transpiration: np.ndarray  # cover crop only (0 for bare soil)
    deep_percolation: np.ndarray


def gap_balance(precip: np.ndarray, et0: np.ndarray, starts: np.ndarray, lengths: np.ndarray,
                taw: np.ndarray, tew: np.ndarray, rew: np.ndarray, dr0: np.ndarray | None = None,
                de0: np.ndarray | None = None, kcb: np.ndarray | None = None, h_m: float = 0.0,
                p_dep: float = 0.55) -> GapResult:
    """Daily FAO-56 balance of topsoil and root zone over many gaps at once.

    precip, et0: daily series of the whole record (mm). Each run r covers days
    starts[r] .. starts[r] + lengths[r] - 1. taw, tew, rew: per run (or scalars).
    dr0, de0: depletion at the start (default: profile empty, Dr = TAW and De = TEW).
    kcb: optional (n_runs, max_len) basal crop coefficient of a cover crop; None = bare
    soil (Kcb = 0, FAO-56 ch. 11). With a cover crop, fc comes from eq. 76 with
    Kc min = 0 and Kc max from eq. 72 with h = h_m at u2 = 2 m/s, RHmin = 45 % (assumption).
    """
    starts = np.asarray(starts, int)
    lengths = np.asarray(lengths, int)
    n = len(starts)
    taw = np.broadcast_to(np.asarray(taw, float), (n,)).copy()
    tew = np.broadcast_to(np.asarray(tew, float), (n,)).copy()
    rew = np.minimum(np.broadcast_to(np.asarray(rew, float), (n,)), tew)  # REW <= TEW
    dr = taw.copy() if dr0 is None else np.broadcast_to(np.asarray(dr0, float), (n,)).copy()
    de = tew.copy() if de0 is None else np.broadcast_to(np.asarray(de0, float), (n,)).copy()
    p_all = np.nan_to_num(np.asarray(precip, float))
    e_all = np.maximum(np.nan_to_num(np.asarray(et0, float)), 0.0)
    if n and (starts.min() < 0 or (starts + lengths).max() > len(p_all)):
        raise ValueError("gap runs outside the climate record")

    tot_p, tot_e, tot_t, tot_dp = (np.zeros(n) for _ in range(4))
    max_len = int(lengths.max()) if n else 0
    kcmax_cover = kc_max(2.0, 45.0, h_m, 0.0)
    for t in range(max_len):
        active = t < lengths
        idx = np.where(active, starts + t, 0)
        p = np.where(active, p_all[idx], 0.0)
        e0 = np.where(active, e_all[idx], 0.0)
        if kcb is None:
            k_cb, kcmax, few = 0.0, KC_MAX_BARE, 1.0
        else:
            k_cb = np.where(active, kcb[:, t] if t < kcb.shape[1] else 0.0, 0.0)
            kcmax = np.maximum(kcmax_cover, k_cb + 0.05)
            few = np.maximum(1.0 - fc_from_kcb(k_cb, 0.0, kcmax, h_m), 0.01)  # eq. 75, fw = 1 (rain)
        # topsoil (eq. 71, 74, 77-79)
        de_start = np.maximum(0.0, de - p)
        ke = np.minimum(kr(de_start, tew, rew) * (kcmax - k_cb), few * kcmax)
        evap = ke * e0
        de = np.where(active, np.minimum(tew, de_start + evap / few), de)
        # root zone (eq. 84, 85, 88): ETc = (Ks Kcb + Ke) ETo
        transp = ks(dr, taw, p_dep) * k_cb * e0
        etc = evap + transp
        dp = np.maximum(0.0, p - etc - dr)
        dr = np.where(active, np.clip(dr - p + etc + dp, 0.0, taw), dr)
        tot_p += p
        tot_e += evap
        tot_t += transp
        tot_dp += dp
    return GapResult(dr, de, taw - dr, tot_p, tot_e, tot_t, tot_dp)


def deficit_with_store(etc: np.ndarray, precip: np.ndarray, store_mm: float, block: int = 10) -> float:
    """Rain deficit over 10-day blocks (as in the suitability engine), where water stored in
    the soil at sowing covers block deficits until it is used up.

    In-season storage of surplus rain is NOT modelled (decision K1-A, docs/METHOD.md):
    with store_mm = 0 this equals the existing 10-day block deficit exactly.
    """
    n = len(etc)
    if n == 0:
        return 0.0
    edges = np.arange(0, n, block)
    d = np.maximum(np.add.reduceat(np.nan_to_num(etc), edges) - np.add.reduceat(np.nan_to_num(precip), edges), 0.0)
    if store_mm <= 0:
        return float(d.sum())
    used = np.minimum(np.cumsum(d), store_mm)
    return float(d.sum() - used[-1])
