"""Probe: NASA POWER humidity parameters for the FAO-56 Kc climate adjustment.

FAO-56 eq. 62 / 65 need the mean daily minimum relative humidity (RHmin) of the
mid- and late-season stages. POWER gives the daily mean RH (RH2M), not RHmin.
This probe checks which humidity parameters the daily AG API offers and compares
three RHmin estimates at the demo points:

  A  ea from RH2M (FAO-56 eq. 19, as in our ET0), RHmin = 100 ea / e°(Tmax)
     (eq. 63 with e°(Tdew) = ea, eq. 14)
  B  dew point T2MDEW from POWER, RHmin = 100 e°(Tdew) / e°(Tmax)    (eq. 63)
  C  Tdew ~ Tmin, RHmin = 100 e°(Tmin) / e°(Tmax)                    (eq. 64)

Run: backend/.venv/Scripts/python scripts/probe/probe_power_humidity.py
"""

from __future__ import annotations

import httpx
import numpy as np

from _common import DEMO_POINTS, Timer, report, save

URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
META_URL = "https://power.larc.nasa.gov/api/system/manager/parameters"
PARAMS = ["T2M_MAX", "T2M_MIN", "RH2M", "T2MDEW", "QV2M", "WS2M"]
# Candidate names checked one by one in the parameter manager (exist or not).
CANDIDATES = ["RH2M", "T2MDEW", "QV2M", "WS2M", "WS2M_MAX", "WS2M_MIN", "RH2M_MIN", "RH2M_MAX"]
START, END = "20010101", "20251231"


def es(t):
    """FAO-56 eq. 11, kPa."""
    return 0.6108 * np.exp(17.27 * t / (t + 237.3))


def probe_meta(client: httpx.Client) -> dict:
    found = {}
    for p in CANDIDATES:
        r = client.get(META_URL, params={"community": "AG", "temporal": "daily", "parameters": p})
        if r.status_code == 200 and p in (body := r.json()):
            found[p] = {k: body[p].get(k) for k in ("name", "units", "definition") if k in body[p]}
        else:
            found[p] = f"not offered (HTTP {r.status_code})"
    save("power_humidity_meta.json", found)
    return found


def probe_point(client: httpx.Client, key: str, lat: float, lon: float) -> bool:
    params = {"parameters": ",".join(PARAMS), "community": "AG", "latitude": lat,
              "longitude": lon, "start": START, "end": END, "format": "JSON"}
    with Timer() as t:
        r = client.get(URL, params=params)
    if r.status_code != 200:
        report(f"POWER humidity {key}", False, {"status": r.status_code, "body": r.text[:300]})
        return False
    data = r.json()
    save(f"power_humidity_{key}.json", data)
    fill = data["header"].get("fill_value")
    s = data["properties"]["parameter"]
    days = sorted(s["T2M_MAX"])
    arr = {p: np.array([s[p][d] for d in days], float) for p in PARAMS}
    n_fill = {p: int((a == fill).sum()) for p, a in arr.items()}
    for a in arr.values():
        a[a == fill] = np.nan
    tx, tn = arr["T2M_MAX"], arr["T2M_MIN"]
    ea_rh = arr["RH2M"] / 100 * (es(tx) + es(tn)) / 2           # eq. 19
    rh_a = np.minimum(100 * ea_rh / es(tx), 100)
    rh_b = np.minimum(100 * es(arr["T2MDEW"]) / es(tx), 100)
    rh_c = np.minimum(100 * es(tn) / es(tx), 100)
    months = np.array([int(d[4:6]) for d in days])
    by_month = {}
    for m in range(1, 13):
        k = months == m
        by_month[m] = (f"A {np.nanmean(rh_a[k]):4.1f}  B {np.nanmean(rh_b[k]):4.1f}  "
                       f"C {np.nanmean(rh_c[k]):4.1f}  u2 {np.nanmean(arr['WS2M'][k]):.2f}")
    report(f"POWER humidity {key}", True, {
        "seconds": f"{t.seconds:.1f}",
        "api": data["header"].get("api"),
        "days": len(days),
        "fill values": n_fill,
        "mean RHmin %  A (RH2M)": f"{np.nanmean(rh_a):.1f}",
        "mean RHmin %  B (T2MDEW)": f"{np.nanmean(rh_b):.1f}",
        "mean RHmin %  C (Tmin)": f"{np.nanmean(rh_c):.1f}",
        "mean |A - B| (daily)": f"{np.nanmean(np.abs(rh_a - rh_b)):.1f}",
        "mean u2 m/s": f"{np.nanmean(arr['WS2M']):.2f}",
        **{f"month {m:02d}": v for m, v in by_month.items()},
    })
    return True


def main() -> None:
    with httpx.Client(timeout=120) as client:
        for p, v in probe_meta(client).items():
            print(f"    meta {p}: {v}")
        results = [probe_point(client, k, p["lat"], p["lon"]) for k, p in DEMO_POINTS.items()]
    raise SystemExit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
