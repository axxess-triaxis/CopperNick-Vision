"""NOAA IBTrACS North Indian Ocean basin (Bay of Bengal + Arabian Sea) loader.

URL and column names verified directly against the live file at NCEI (checked
2026-09-17): the North Indian ("NI") basin CSV is the one relevant to India.
Two real quirks of this dataset, both handled here:

- The CSV has TWO header rows -- row 1 is column names, row 2 is units
  (e.g. "degrees_north", "kts", "mb"). Row 2 must be skipped, not parsed as data.
- Missing values are blank cells, not a sentinel like -9999 (that convention
  is used by IBTrACS's other file formats, not CSV) -- but "blank" in
  practice includes cells containing whitespace-only strings (e.g. a single
  space), not just true empty cells. A real production `/assess` call
  surfaced this: `float(" ")` raises `ValueError`, and `pd.notna(" ")` is
  `True` since a non-empty string isn't NaN, so the naive notna-then-float
  check silently let through cells pandas parsed as `" "` rather than NaN.
  `_safe_float` below handles this explicitly.
"""

from __future__ import annotations

from pathlib import Path

import httpx
import pandas as pd

from ..schema import CycloneTrackPoint

IBTRACS_NI_URL = (
    "https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-"
    "stewardship-ibtracs/v04r01/access/csv/ibtracs.NI.list.v04r01.csv"
)

# A ~28MB file downloaded fresh from NOAA on every cold Cloud Run start added
# 10-24s to every first request after an idle period (measured directly, not
# assumed -- see git history). Real cyclone tracks don't change retroactively
# except for slow NOAA reprocessing, so a snapshot bundled into the deployment
# is both faster and removes a live external dependency during a demo.
#
# Deliberately placed next to this file (inside the `coppernick.data`
# package), not at the repo root -- `pip install .` (what the Dockerfile
# runs) copies the installed package into site-packages, and a repo-root-
# relative path would silently break once installed rather than in local
# dev, since `__file__` then points into site-packages, not the source tree.
# See pyproject.toml's `[tool.setuptools.package-data]` for why this .csv
# actually gets included in the installed package at all.
_BUNDLED_CACHE_PATH = Path(__file__).parent / "ibtracs_ni_cache.csv"


def load_ni_basin_tracks(source: str | Path | None = None) -> pd.DataFrame:
    """Load the North Indian basin IBTrACS CSV.

    Resolution order: an explicit `source` (tests use this), then the
    bundled snapshot at `data/ibtracs_ni_cache.csv` if present, then the live
    NOAA URL as the last resort. Call `refresh_bundled_cache()` to update the
    snapshot when new storm seasons need to be reflected.
    """

    if source is not None:
        return pd.read_csv(source, skiprows=[1], low_memory=False)
    if _BUNDLED_CACHE_PATH.exists():
        return pd.read_csv(_BUNDLED_CACHE_PATH, skiprows=[1], low_memory=False)
    return pd.read_csv(IBTRACS_NI_URL, skiprows=[1], low_memory=False)


def refresh_bundled_cache(dest: str | Path | None = None, timeout: float = 60.0) -> Path:
    """Re-download the live IBTrACS NI CSV to the bundled cache location.

    Not called automatically -- run this deliberately (and redeploy) when the
    cached snapshot needs to reflect a more recent storm season.
    """

    target = Path(dest) if dest else _BUNDLED_CACHE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    response = httpx.get(IBTRACS_NI_URL, timeout=timeout, follow_redirects=True)
    response.raise_for_status()
    target.write_bytes(response.content)
    return target


def _safe_float(value: object) -> float | None:
    """Parse a possibly-missing IBTrACS numeric cell.

    Handles both true NaN (a genuinely empty cell) and a whitespace-only
    string (e.g. `" "`), which pandas reads as a non-null string that
    `pd.notna()` alone would wrongly treat as present.
    """

    if pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    return float(text)


def get_storm_track(df: pd.DataFrame, name: str, season: int | None = None) -> list[CycloneTrackPoint]:
    """Extract one named storm's track as a list of CycloneTrackPoint, ordered by time."""

    mask = df["NAME"].str.upper() == name.upper()
    if season is not None:
        mask &= df["SEASON"] == season
    subset = df[mask].sort_values("ISO_TIME")

    points: list[CycloneTrackPoint] = []
    for _, row in subset.iterrows():
        points.append(
            CycloneTrackPoint(
                storm_id=row["SID"],
                name=row["NAME"],
                timestamp=row["ISO_TIME"],
                lat=_safe_float(row["LAT"]),
                lon=_safe_float(row["LON"]),
                wind_knots=_safe_float(row.get("USA_WIND")),
                pressure_mb=_safe_float(row.get("USA_PRES")),
            )
        )
    return points
