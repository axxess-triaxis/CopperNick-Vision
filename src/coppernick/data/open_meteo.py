"""Open-Meteo free forecast API -- no API key required.

Base URL and parameter names verified against open-meteo.com/en/docs
(checked 2026-09-17).
"""

from __future__ import annotations

import httpx

from ..schema import WeatherSnapshot

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_forecast(lat: float, lon: float, timeout: float = 10.0) -> WeatherSnapshot:
    """Fetch hourly precipitation and wind speed for one coordinate."""

    response = httpx.get(
        OPEN_METEO_URL,
        params={
            "latitude": lat,
            "longitude": lon,
            "hourly": "precipitation,wind_speed_10m",
        },
        timeout=timeout,
    )
    response.raise_for_status()
    data = response.json()
    hourly = data["hourly"]

    return WeatherSnapshot(
        lat=lat,
        lon=lon,
        hourly_precipitation_mm=hourly["precipitation"],
        hourly_wind_speed_kmh=hourly["wind_speed_10m"],
        hourly_times=hourly["time"],
    )
