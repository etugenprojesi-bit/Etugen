"""Download the GGCMI Phase 3 crop calendar and store it as data/ggcmi_crop_calendar.npz.

Source: Ray, D., Jägermeyr, J., Minoli, S., Siebert, S., Müller, C. (2021).
GGCMI Phase 3 crop calendar. Zenodo, doi:10.5281/zenodo.5062513, CC BY 4.0.
Method: Jägermeyr et al. (2021), Nature Food 2:873-885. See docs/DATA_SOURCES.md §8.

The NetCDF-4/HDF5 files are read with h5py (requirements-probe.txt only); the
app reads the resulting .npz with numpy. Values are copied unchanged: planting
and maturity day of year (1-365) per 0.5° cell, 0 = no value. Only the crops
that the app models are kept (app.suitability.calendar.GGCMI_CODES).

Run: backend/.venv/Scripts/python scripts/build_crop_calendar.py
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import h5py
import httpx
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.suitability.calendar import DATA_FILE, GGCMI_CODES  # noqa: E402

URL = "https://zenodo.org/records/5062513/files/{code}_{system}_ggcmi_crop_calendar_phase3_v1.01.nc4?download=1"
FILL = 1e19


def main() -> None:
    arrays: dict[str, np.ndarray] = {}
    lat = lon = None
    with httpx.Client(timeout=120, follow_redirects=True) as client:
        for code in sorted(set(GGCMI_CODES.values())):
            for system in ("rf", "ir"):
                r = client.get(URL.format(code=code, system=system))
                r.raise_for_status()
                with h5py.File(io.BytesIO(r.content), "r") as h:
                    la, lo = h["lat"][:], h["lon"][:]
                    if lat is None:
                        lat, lon = la, lo
                    elif not (np.array_equal(la, lat) and np.array_equal(lo, lon)):
                        raise SystemExit(f"{code}_{system}: grid differs")
                    for var, short in (("planting_day", "plant"), ("maturity_day", "mature")):
                        a = h[var][:]
                        valid = a < FILL
                        if np.any(valid & ((a < 1) | (a > 366))):
                            raise SystemExit(f"{code}_{system} {var}: values outside 1-366")
                        arrays[f"{code}_{system}_{short}"] = np.where(valid, np.rint(a), 0).astype(np.uint16)
                    arrays[f"{code}_{system}_source"] = np.where(
                        h["data_source_used"][:] < FILL, h["data_source_used"][:], 0).astype(np.uint8)
                print(f"{code}_{system}: ok")
    out = ROOT / DATA_FILE
    np.savez_compressed(out, lat=lat.astype(np.float32), lon=lon.astype(np.float32), **arrays)
    print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KiB, {len(arrays)} grids)")


if __name__ == "__main__":
    main()
