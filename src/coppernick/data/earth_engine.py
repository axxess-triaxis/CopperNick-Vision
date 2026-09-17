"""Google Earth Engine wrapper for the satellite-imagery infrastructure layer.

API shape verified against developers.google.com/earth-engine (checked
2026-09-17). One-time setup this code does NOT do for you: run
`earthengine authenticate` once from a terminal (opens a browser consent
flow) before `ensure_initialized` will succeed.
"""

from __future__ import annotations

import ee


def ensure_initialized(project_id: str) -> None:
    """Initialize the Earth Engine client. Raises ee.EEException with a clear
    message if `earthengine authenticate` hasn't been run yet for this machine.
    """

    ee.Initialize(project=project_id)


def fetch_recent_imagery_count(
    lat: float,
    lon: float,
    start_date: str,
    end_date: str,
    buffer_km: float = 25.0,
    collection_id: str = "COPERNICUS/S2_SR_HARMONIZED",
) -> int:
    """Return how many Sentinel-2 images cover the given point and date range.

    Intentionally minimal -- a starting point for the infrastructure-exposure
    layer, not the layer itself. Turning this into an actual exposure map
    (roads/power grids/shelters within the storm's projected path) is not
    yet built; see README Status.
    """

    point = ee.Geometry.Point([lon, lat])
    region = point.buffer(buffer_km * 1000)
    collection = (
        ee.ImageCollection(collection_id)
        .filterDate(start_date, end_date)
        .filterBounds(region)
    )
    return collection.size().getInfo()
