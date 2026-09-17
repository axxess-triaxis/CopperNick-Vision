"""Camera ingestion, tested with ONVIF/WS-Discovery mocked -- no real camera
hardware exists to test against (see camera_ingest.py's module docstring)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from coppernick.sky.camera_ingest import (
    OnvifDiscoveryError,
    discover_onvif_devices,
    from_rtsp_url,
    resolve_stream_source,
)


def test_from_rtsp_url_accepts_valid_url():
    source = from_rtsp_url("cam-1", "rtsp://192.0.2.10:554/stream1", "Test camera")
    assert source.protocol == "rtsp"
    assert source.stream_url == "rtsp://192.0.2.10:554/stream1"
    assert source.onvif_device_url is None


def test_from_rtsp_url_rejects_non_rtsp_url():
    with pytest.raises(ValueError):
        from_rtsp_url("cam-1", "http://192.0.2.10/stream1", "Test camera")


def test_discover_onvif_devices_returns_xaddrs():
    mock_service = MagicMock()
    mock_service.getXAddrs.return_value = ["http://192.0.2.10/onvif/device_service"]
    with patch("wsdiscovery.discovery.ThreadedWSDiscovery") as MockWSD:
        instance = MockWSD.return_value
        instance.searchServices.return_value = [mock_service]
        result = discover_onvif_devices(timeout=1.0)
    assert result == ["http://192.0.2.10/onvif/device_service"]
    instance.start.assert_called_once()
    instance.stop.assert_called_once()


@pytest.mark.asyncio
async def test_resolve_stream_source_returns_camera_source():
    mock_profile = MagicMock()
    mock_profile.token = "profile-1"
    mock_media_service = AsyncMock()
    mock_media_service.GetProfiles.return_value = [mock_profile]
    mock_media_service.GetStreamUri.return_value = MagicMock(Uri="rtsp://192.0.2.10:554/profile1")

    mock_camera = MagicMock()
    mock_camera.create_media_service = AsyncMock(return_value=mock_media_service)
    mock_camera.xaddrs = {"device": "http://192.0.2.10/onvif/device_service"}

    result = await resolve_stream_source(mock_camera, "cam-1", "Rooftop north")

    assert result.protocol == "onvif"
    assert result.stream_url == "rtsp://192.0.2.10:554/profile1"
    mock_media_service.GetStreamUri.assert_called_once()


@pytest.mark.asyncio
async def test_resolve_stream_source_raises_on_no_profiles():
    mock_media_service = AsyncMock()
    mock_media_service.GetProfiles.return_value = []
    mock_camera = MagicMock()
    mock_camera.create_media_service = AsyncMock(return_value=mock_media_service)

    with pytest.raises(OnvifDiscoveryError):
        await resolve_stream_source(mock_camera, "cam-1", "Rooftop north")
