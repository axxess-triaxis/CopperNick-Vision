"""Hardware-agnostic camera/stream ingestion: ONVIF discovery + universal RTSP fallback.

Deliberately restricted to two open, cross-vendor standards rather than any
per-brand SDK, so this works "across specs and brands" by construction:

- **ONVIF** (`onvif-zeep-async`) -- the industry interoperability standard
  most IP cameras and NVRs implement, for discovery and resolving a stream
  URI from a device's media profiles.
- **RTSP** -- the universal streaming protocol every IP camera speaks, used
  directly as a fallback when a camera's RTSP URL is already known (common
  for consumer cameras that don't fully implement ONVIF media services).

API shapes below (constructor signature, `create_media_service`/
`create_devicemgmt_service` being async, `ThreadedWSDiscovery.searchServices`
signature) were confirmed by directly introspecting the installed
`onvif-zeep-async` 4.2.1 and `wsdiscovery` 2.1.2 packages (checked
2026-09-17) -- not guessed from memory.

**Hardware-unverified**: no physical ONVIF camera exists in this development
environment. The class structure and method signatures below are verified
against the real library; the actual network round-trip to a device (SOAP
auth, GetProfiles, GetStreamUri) has not been exercised against real
hardware. Treat this as correct-by-construction, not field-tested.
"""

from __future__ import annotations

from onvif import ONVIFCamera

from ..schema import CameraSource


class OnvifDiscoveryError(RuntimeError):
    pass


def discover_onvif_devices(timeout: float = 3.0) -> list[str]:
    """WS-Discovery multicast scan for ONVIF devices on the local network.

    Returns each responding device's XAddrs (service address) list. Requires
    the caller's network to allow multicast (many cloud/container
    environments block this -- expect an empty list there, not an error).
    """

    from wsdiscovery.discovery import ThreadedWSDiscovery

    wsd = ThreadedWSDiscovery()
    wsd.start()
    try:
        services = wsd.searchServices(timeout=timeout)
        return [addr for svc in services for addr in svc.getXAddrs()]
    finally:
        wsd.stop()


async def connect_onvif_camera(host: str, port: int, username: str, password: str) -> ONVIFCamera:
    """Connect to an ONVIF device. Caller must `await camera.close()` when done."""

    camera = ONVIFCamera(host, port, username, password)
    await camera.update_xaddrs()
    return camera


async def resolve_stream_source(camera: ONVIFCamera, source_id: str, label: str) -> CameraSource:
    """Resolve an ONVIF camera's first media profile to an RTSP stream URL.

    Uses the ONVIF Media service's GetProfiles + GetStreamUri operations --
    the standard, vendor-neutral way to get a playable stream URL regardless
    of camera brand.
    """

    media_service = await camera.create_media_service()
    profiles = await media_service.GetProfiles()
    if not profiles:
        raise OnvifDiscoveryError(f"ONVIF device at {source_id} reported no media profiles")

    stream_setup = {
        "Stream": "RTP-Unicast",
        "Transport": {"Protocol": "RTSP"},
    }
    uri_response = await media_service.GetStreamUri(
        {"StreamSetup": stream_setup, "ProfileToken": profiles[0].token}
    )

    return CameraSource(
        source_id=source_id,
        protocol="onvif",
        stream_url=uri_response.Uri,
        onvif_device_url=camera.xaddrs.get("device", "") if hasattr(camera, "xaddrs") else None,
        label=label,
    )


def from_rtsp_url(source_id: str, rtsp_url: str, label: str) -> CameraSource:
    """Universal fallback: use a known RTSP URL directly, no ONVIF handshake.

    Every IP camera speaks RTSP even when ONVIF media services aren't fully
    implemented -- this is the guaranteed-to-work path across brands.
    """

    if not rtsp_url.startswith("rtsp://"):
        raise ValueError(f"Expected an rtsp:// URL, got: {rtsp_url!r}")
    return CameraSource(source_id=source_id, protocol="rtsp", stream_url=rtsp_url, label=label)
