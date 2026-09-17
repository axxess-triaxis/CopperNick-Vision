"""NASA GIBS night-sky cross-referencing -- explicitly NOT vision-dependent.

Uses NASA's public GIBS WMTS API (no API key required) to fetch VIIRS Day/Night
Band imagery. Endpoint pattern and layer identifier verified directly against
the live service (checked 2026-09-17), not guessed:

- Endpoint: https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/{layer}/default/{date}/{tileMatrixSet}/{z}/{y}/{x}.{ext}
- Layer: VIIRS_NOAA21_DayNightBand (NOAA-21 is the current active satellite;
  the older VIIRS_SNPP_DayNightBand_ENCC layer's data stops at 2023-07-07 in
  the live capabilities document -- confirmed by direct request, not assumed)
- Tile matrix set: 1km (confirmed via GetCapabilities for this layer)

This module only resolves a tile URL and reports known limitations (cloud
cover, etc. are a real limitation of this product, not modeled numerically
here) -- it does not download/process pixel data itself, since that decision
belongs to whatever caller actually needs the image (display vs. further
analysis).
"""

from __future__ import annotations

from datetime import date, timedelta

from ..schema import NightSkyReference

GIBS_LAYER = "VIIRS_NOAA21_DayNightBand"
GIBS_TILE_MATRIX_SET = "1km"
GIBS_BASE_URL = "https://gibs.earthdata.nasa.gov/wmts/epsg4326/best"

# This product's imagery lags by roughly a day in typical NASA near-real-time
# processing; requesting "today" often 404s until processing catches up.
DEFAULT_LOOKBACK_DAYS = 1

# Real (MatrixWidth, MatrixHeight) per zoom level for the "1km" TileMatrixSet,
# read directly from GIBS's own GetCapabilities response (checked 2026-09-17)
# -- NOT a doubling formula. GIBS's EPSG:4326 grid is irregular at low zoom
# levels (2, 3, 5, then a clean doubling from z2 onward: 5, 10, 20, 40, 80),
# so deriving this mathematically produces wrong tile indices, as a live
# TileOutOfRange response confirmed during development.
_MATRIX_DIMENSIONS: dict[int, tuple[int, int]] = {
    0: (2, 1),
    1: (3, 2),
    2: (5, 3),
    3: (10, 5),
    4: (20, 10),
    5: (40, 20),
    6: (80, 40),
}
MAX_ZOOM = max(_MATRIX_DIMENSIONS)


def _lat_lon_to_tile(lat: float, lon: float, zoom: int) -> tuple[int, int]:
    """Convert lat/lon to a GIBS EPSG:4326 tile row/col at the given zoom,
    using this TileMatrixSet's real per-level grid dimensions.
    """

    if zoom not in _MATRIX_DIMENSIONS:
        raise ValueError(f"zoom must be one of {sorted(_MATRIX_DIMENSIONS)}, got {zoom}")
    matrix_width, matrix_height = _MATRIX_DIMENSIONS[zoom]
    col = min(int((lon + 180.0) / 360.0 * matrix_width), matrix_width - 1)
    row = min(int((90.0 - lat) / 180.0 * matrix_height), matrix_height - 1)
    return row, col


def build_tile_url(
    lat: float,
    lon: float,
    on_date: date | None = None,
    zoom: int = 4,
) -> NightSkyReference:
    """Build a GIBS night-sky tile URL for the given coordinate and date.

    `on_date` defaults to yesterday (UTC), since same-day imagery is often
    not yet processed -- see DEFAULT_LOOKBACK_DAYS.
    """

    target_date = on_date or (date.today() - timedelta(days=DEFAULT_LOOKBACK_DAYS))
    row, col = _lat_lon_to_tile(lat, lon, zoom)
    tile_url = (
        f"{GIBS_BASE_URL}/{GIBS_LAYER}/default/{target_date.isoformat()}/"
        f"{GIBS_TILE_MATRIX_SET}/{zoom}/{row}/{col}.png"
    )
    return NightSkyReference(
        date=target_date.isoformat(),
        layer=GIBS_LAYER,
        lat=lat,
        lon=lon,
        tile_url=tile_url,
        cloud_cover_note=(
            "VIIRS Day/Night Band is a passive optical sensor -- dense cloud cover "
            "obscures surface lights entirely for the affected tile/date; this "
            "module does not detect or quantify cloud cover itself."
        ),
    )
