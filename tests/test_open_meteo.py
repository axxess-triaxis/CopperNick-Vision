"""Open-Meteo client, tested with the HTTP call mocked via respx -- no live
network call, no API key needed either way."""

from __future__ import annotations

import httpx
import respx

from coppernick.data.open_meteo import OPEN_METEO_URL, fetch_forecast


@respx.mock
def test_fetch_forecast_parses_hourly_arrays():
    respx.get(OPEN_METEO_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "hourly": {
                    "time": ["2026-09-17T00:00", "2026-09-17T01:00"],
                    "precipitation": [0.0, 2.5],
                    "wind_speed_10m": [10.1, 14.3],
                }
            },
        )
    )

    snapshot = fetch_forecast(lat=13.08, lon=80.27)

    assert snapshot.lat == 13.08
    assert snapshot.hourly_precipitation_mm == [0.0, 2.5]
    assert snapshot.hourly_wind_speed_kmh == [10.1, 14.3]
    assert len(snapshot.hourly_times) == 2


@respx.mock
def test_fetch_forecast_raises_on_http_error():
    respx.get(OPEN_METEO_URL).mock(return_value=httpx.Response(400))
    try:
        fetch_forecast(lat=0, lon=0)
        assert False, "expected HTTPStatusError"
    except httpx.HTTPStatusError:
        pass
