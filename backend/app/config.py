"""Runtime settings, read from environment variables and the repo-root .env file."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


@dataclass(frozen=True)
class Settings:
    cache_path: Path
    cache_grid_deg: float
    demo_cache_dir: Path
    data_dir: Path
    climate_years: int
    last_full_year: int

    @property
    def first_year(self) -> int:
        return self.last_full_year - self.climate_years + 1


@lru_cache
def get_settings() -> Settings:
    _load_dotenv(ROOT / ".env")
    cache_path = Path(os.environ.get("CACHE_PATH") or "backend/cache.sqlite")
    if not cache_path.is_absolute():
        cache_path = ROOT / cache_path
    return Settings(
        cache_path=cache_path,
        cache_grid_deg=float(os.environ.get("CACHE_GRID_DEG") or 0.05),
        demo_cache_dir=ROOT / "demo_cache",
        data_dir=ROOT / "data",
        climate_years=int(os.environ.get("CLIMATE_YEARS") or 25),
        # Only complete calendar years are analysed.
        last_full_year=int(os.environ.get("LAST_FULL_YEAR") or date.today().year - 1),
    )


def demo_cache_first() -> bool:
    """Hosted demo (deploy/huggingface/): for the three demo fields, use the saved real data in
    demo_cache/ before the network, so they answer in seconds. Off by default (local use and
    tests keep cache -> network -> demo cache)."""
    return os.environ.get("DEMO_CACHE_FIRST", "").lower() in ("1", "true", "yes")
