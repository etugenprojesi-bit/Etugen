"""SQLite cache for public-data API responses.

Keys contain only the source name, coordinates rounded to the cache grid
(default 0.05°) and request parameters — no user identifiers, IP addresses
or request times (see docs/PRIVACY.md).
"""

from __future__ import annotations

import gzip
import json
import sqlite3
import time
from pathlib import Path


def round_coord(value: float, grid_deg: float) -> float:
    """Snap a coordinate to the cache grid, e.g. 37.612 -> 37.60 for 0.05°."""
    snapped = round(value / grid_deg) * grid_deg
    return round(snapped, 6) + 0.0  # + 0.0 turns -0.0 into 0.0


def cache_key(source: str, lat: float, lon: float, **params: object) -> str:
    extra = ";".join(f"{k}={params[k]}" for k in sorted(params))
    return f"{source}:{lat:.4f}:{lon:.4f}:{extra}"


class ResponseCache:
    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as con:
            con.execute(
                "CREATE TABLE IF NOT EXISTS responses ("
                "key TEXT PRIMARY KEY, stored_unix INTEGER NOT NULL, payload BLOB NOT NULL)"
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def get(self, key: str) -> object | None:
        with self._connect() as con:
            row = con.execute("SELECT payload FROM responses WHERE key = ?", (key,)).fetchone()
        return json.loads(gzip.decompress(row[0])) if row else None

    def put(self, key: str, payload: object) -> None:
        blob = gzip.compress(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        with self._connect() as con:
            con.execute(
                "INSERT OR REPLACE INTO responses (key, stored_unix, payload) VALUES (?, ?, ?)",
                (key, int(time.time()), blob),
            )
