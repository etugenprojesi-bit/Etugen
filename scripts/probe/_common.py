"""Shared helpers for data-source probe scripts.

Each probe hits a real endpoint, prints a short human-readable report and
saves the raw response under scripts/probe/out/ (git-ignored).
"""

from __future__ import annotations

import json
import time
from pathlib import Path

OUT_DIR = Path(__file__).parent / "out"
OUT_DIR.mkdir(exist_ok=True)

# Demo points on farmland. Each was checked against MODIS MCD12Q1 LC_Type1
# (2024): >= 22 of 25 pixels in the 1 km box are class 12 "Croplands".
# City-centre coordinates were rejected: SoilGrids masks urban pixels.
DEMO_POINTS = {
    "konya": {"lat": 37.60, "lon": 32.75, "label": "Çumra, Konya plain, Türkiye"},
    "punjab": {"lat": 30.80, "lon": 75.60, "label": "Ludhiana district, Punjab, India"},
    "nakuru": {"lat": -0.25, "lon": 36.15, "label": "Nakuru County, Kenya"},
}


def save(name: str, payload: object) -> Path:
    path = OUT_DIR / name
    if isinstance(payload, (bytes, bytearray)):
        path.write_bytes(payload)
    elif isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
    else:
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


class Timer:
    def __enter__(self) -> "Timer":
        self.t0 = time.perf_counter()
        return self

    def __exit__(self, *exc: object) -> None:
        self.seconds = time.perf_counter() - self.t0


def report(source: str, ok: bool, details: dict) -> None:
    status = "OK" if ok else "FAIL"
    print(f"[{status}] {source}")
    for k, v in details.items():
        print(f"    {k}: {v}")
