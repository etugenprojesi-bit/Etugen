"""Load crop parameters from data/crops.yaml, data/crop_phenology.yaml and
data/fao56_table11.yaml into one structure per crop.

Ranges in the YAML ([low, high]) are reduced to their midpoint for the
calculation; the range itself is kept for display.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from functools import lru_cache
from pathlib import Path

import numpy as np
import yaml


def mid(v):
    if v is None:
        return None
    if isinstance(v, list):
        return sum(v) / len(v)
    return float(v)


@dataclass(frozen=True)
class Temperature:
    t_base: float
    t_opt: float | None  # optional: only needed when t_sum is unknown (growth ramp)
    t_heat: float | None
    t_ext: float | None
    t_sum: float | None
    source: str
    verified: bool
    note: str | None = None
    # Optional WOFOST-style development (docs/METHOD.md "Thermal time"): daily thermal-time
    # increment as a piecewise-linear function of Tmean ([[T, dT], ...], clamped at the ends)
    # instead of max(0, Tmean - t_base); t_sum is then counted from emergence.
    dev_rate_table: tuple[tuple[float, float], ...] | None = None
    emergence: Emergence | None = None
    # FAO ECOCROP general ranges (docs/METHOD.md "ECOCROP crops"); only set when the crop has
    # no evaluable literature block. The engine then scores temperature with the trapezoid.
    ecocrop: Ecocrop | None = None


@dataclass(frozen=True)
class Ecocrop:
    """ECOCROP data sheet values: temperature [TMIN, TOPMN, TOPMX, TMAX] °C, crop cycle days."""
    id: int
    temp: tuple[float, float, float, float]
    cycle: tuple[float, float] | None

    @property
    def url(self) -> str:
        return f"https://ecocrop.apps.fao.org/ecocrop/srv/en/dataSheet?id={self.id}"


@dataclass(frozen=True)
class Emergence:
    """Sowing -> emergence phase with its own base (WOFOST TBASEM / TEFFMX / TSUMEM)."""
    t_base: float
    t_sum: float
    t_eff_max: float | None = None  # daily increment capped at t_eff_max - t_base

    def rate(self, tmean: np.ndarray) -> np.ndarray:
        hi = np.inf if self.t_eff_max is None else self.t_eff_max - self.t_base
        return np.clip(tmean - self.t_base, 0.0, hi)


@dataclass(frozen=True)
class Stages:
    init: float
    dev: float
    mid: float
    late: float
    total: float
    row: str  # FAO-56 Table 11 row used
    max_total: float | None = None  # longest season among the crop's Table 11 rows
    min_total: float | None = None  # shortest season among the crop's Table 11 rows

    def fractions(self) -> tuple[float, float, float, float]:
        s = self.init + self.dev + self.mid + self.late
        return self.init / s, self.dev / s, self.mid / s, self.late / s


@dataclass(frozen=True)
class Crop:
    id: str
    name: dict
    scientific: str
    family: str
    group: str
    nitrogen_fixing: bool
    perennial: bool
    kc_ini: float | None
    kc_mid: float | None
    kc_end: float | None
    root_depth_m: float | None
    temperature: Temperature | None
    stages: Stages | None
    lethal_min: dict | None = None
    max_height_m: float | None = None  # FAO-56 Table 12 (eq. 62 / 65 crop height h)
    missing: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)  # labelled analogies (e.g. Kc from a similar crop)
    # Cut forage whose season is only the first cutting cycle (regrowth cuts not modelled):
    # evaluated, but not used in recommended rotations (plan_veri_eksik_urunler.md, K3)
    first_cut_only: bool = False
    depletion_p: float | None = None  # FAO-56 Table 22 p (ETc ~5 mm/day); irrigation interval
    regional: tuple = ()          # raw `regional` blocks of crop_phenology.yaml (see localize)
    variant: dict | None = None   # the regional variant applied at this point, if any


def _pick_stages(rows: list[dict], names: list[str]) -> Stages | None:
    """Median-length FAO-56 Table 11 row among the named rows (documented choice)."""
    cands = []
    for r in rows:
        if r["crop"] in names and all(mid(r[k]) is not None for k in ("init", "dev", "mid", "late")):
            vals = [mid(r[k]) for k in ("init", "dev", "mid", "late")]
            cands.append((sum(vals), vals, f"{r['crop']} | {r.get('planting')} | {r.get('region')}"))
    if not cands:
        return None
    cands.sort(key=lambda c: c[0])
    total, vals, label = cands[(len(cands) - 1) // 2]
    return Stages(*vals, total=total, row=label, max_total=cands[-1][0], min_total=cands[0][0])


@lru_cache
def load_crops(data_dir: Path) -> list[Crop]:
    base = yaml.safe_load((data_dir / "crops.yaml").read_text(encoding="utf-8"))
    phen = yaml.safe_load((data_dir / "crop_phenology.yaml").read_text(encoding="utf-8"))
    t11 = yaml.safe_load((data_dir / "fao56_table11.yaml").read_text(encoding="utf-8"))["rows"]
    sources = phen["sources"]
    by_id = {c["id"]: c for c in base["crops"]}
    crops = []
    for c in base["crops"]:
        f = c.get("fao56") or {}
        p = phen["crops"].get(c["id"], {})
        assumptions = []
        if not f and (an := c.get("fao56_analog")):
            f = by_id[an["crop"]].get("fao56") or {}
            assumptions.append(" ".join(an["assumption"].split()))
        if (sa := p.get("season", {}).get("assumption")):
            assumptions.append(" ".join(sa.split()))
        temp = None
        if t := p.get("temperature"):
            src = sources[t["source"]]
            table = t.get("dev_rate_table")
            em = t.get("emergence")
            temp = Temperature(
                t_base=float(t["t_base"]), t_opt=mid(t.get("t_opt")),
                t_heat=mid(t.get("t_heat")), t_ext=mid(t.get("t_ext")), t_sum=mid(t.get("t_sum")),
                source=t["source"], verified=bool(src.get("verified_against_original")),
                note=t.get("note"),
                dev_rate_table=tuple((float(x), float(y)) for x, y in table) if table else None,
                emergence=Emergence(float(em["t_base"]), float(em["t_sum"]),
                                    None if em.get("t_eff_max") is None else float(em["t_eff_max"]))
                if em else None,
            )
        eco = p.get("ecocrop")
        if eco and (temp is None or (temp.t_sum is None and temp.t_opt is None)):
            # Decision 2026-11-12 (plan_ecocrop_urun_artirma.md): general ECOCROP ranges replace a
            # missing / partial literature block. t_base / t_opt are TMIN / TOPMN for display only.
            tmin, topmn, topmx, tmax = (float(v) for v in eco["temp"])
            temp = Temperature(
                t_base=tmin, t_opt=topmn, t_heat=None, t_ext=None, t_sum=None,
                source="ecocrop", verified=bool(sources["ecocrop"].get("verified_against_original")),
                note=f"FAO ECOCROP general ranges, data sheet id {eco['id']} (no licence stated)",
                ecocrop=Ecocrop(int(eco["id"]), (tmin, topmn, topmx, tmax),
                                tuple(float(v) for v in eco["cycle"]) if eco.get("cycle") else None),
            )
        stages = _pick_stages(t11, p.get("season", {}).get("fao56_table11", []))
        missing = []
        if not f:
            missing.append("fao56_kc")
        if temp is None or (temp.t_sum is None and temp.t_opt is None):
            missing.append("temperature_limits")
        elif temp.t_heat is None:
            missing.append("heat_thresholds")
        if stages is None:
            missing.append("season_stages")
        crops.append(Crop(
            id=c["id"], name=c["name"], scientific=c["scientific"], family=c["family"],
            group=c["group"], nitrogen_fixing=bool(c.get("nitrogen_fixing")),
            perennial=bool(c.get("perennial")),
            kc_ini=mid(f.get("kc_ini")), kc_mid=mid(f.get("kc_mid")), kc_end=mid(f.get("kc_end")),
            root_depth_m=mid(f.get("root_depth_m")), temperature=temp, stages=stages,
            lethal_min=p.get("lethal_min"), max_height_m=mid(f.get("max_height_m")), missing=missing,
            assumptions=assumptions, first_cut_only=bool(p.get("season", {}).get("first_cut_only")),
            regional=tuple(p.get("regional") or ()), depletion_p=mid(f.get("depletion_p")),
        ))
    return crops


def source_citations(data_dir: Path) -> dict:
    phen = yaml.safe_load((data_dir / "crop_phenology.yaml").read_text(encoding="utf-8"))
    base = yaml.safe_load((data_dir / "crops.yaml").read_text(encoding="utf-8"))
    t11 = yaml.safe_load((data_dir / "fao56_table11.yaml").read_text(encoding="utf-8"))
    return {
        "fao56_t12": base["sources"]["fao56_t12"]["citation"].strip(),
        "fao56_t22": base["sources"]["fao56_t22"]["citation"].strip(),
        "fao56_t11": t11["source"]["citation"].strip(),
        **{k: v["citation"].strip() + (f" doi:{v['doi']}" if v.get("doi") else f" {v['url']}")
           for k, v in phen["sources"].items()},
    }


def _in_region(region: dict, crop_id: str, lat: float, lon: float, data_dir: Path) -> bool:
    (la0, la1), (lo0, lo1) = region["lat"], region["lon"]
    if not (la0 <= lat <= la1 and lo0 <= lon <= lo1):
        return False
    if (src := region.get("ggcmi_source")) is not None:
        from app.suitability import calendar  # local import: calendar does not need crops
        cal = calendar.lookup(data_dir, crop_id, lat, lon)
        return cal is not None and cal["data_source"] == src
    return True


def localize(crops: list[Crop], lat: float, lon: float, data_dir: Path) -> list[Crop]:
    """Crops with their regional variant applied at this point (decision 2026-11-14,
    docs/drafts/plan_punjab_bugday_sicak_esik.md). A variant replaces t_sum (and t_base if
    given); `variant` carries its label and assumption (confidence reason regional_variant)."""
    out = []
    for c in crops:
        v = next((r for r in c.regional if _in_region(r["region"], c.id, lat, lon, data_dir)), None)
        if v is None or c.temperature is None:
            out.append(c)
            continue
        t = replace(c.temperature, t_sum=mid(v["t_sum"]),
                    t_base=float(v.get("t_base", c.temperature.t_base)))
        out.append(replace(c, temperature=t, variant={
            "id": v["id"], "name": v["name"], "source": v["source"], "t_sum": v["t_sum"],
            "assumption": " ".join(v["assumption"].split())}))
    return out
