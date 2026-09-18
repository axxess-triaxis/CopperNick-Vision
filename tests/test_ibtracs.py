"""IBTrACS loader, tested against a small fixture matching the real CSV's
two-header-row shape (column names, then units) -- no live network call."""

from __future__ import annotations

import io

from coppernick.data.ibtracs import _BUNDLED_CACHE_PATH, _safe_float, get_storm_track, load_ni_basin_tracks

SAMPLE_CSV = """SID,SEASON,NAME,ISO_TIME,LAT,LON,USA_WIND,USA_PRES
 ,Year, , ,degrees_north,degrees_east,kts,mb
2026123N10080,2026,AMPHAN,2026-05-16 00:00:00,10.5,80.1,35,1005
2026123N10080,2026,AMPHAN,2026-05-16 06:00:00,11.2,79.8,45,998
2026123N10080,2026,AMPHAN,2026-05-16 12:00:00,12.0,79.5,60,985
2026456N15085,2026,OTHERSTORM,2026-06-01 00:00:00,15.0,85.0,30,1008
"""

# Regression fixture for a real production bug: IBTrACS uses a whitespace-only
# string (a single space) as a missing-value marker in some cells, which
# pandas reads as a non-null string -- pd.notna() alone doesn't catch it.
SAMPLE_CSV_WITH_WHITESPACE_MISSING = """SID,SEASON,NAME,ISO_TIME,LAT,LON,USA_WIND,USA_PRES
 ,Year, , ,degrees_north,degrees_east,kts,mb
2020123N10080,2020,GAPWIND,2020-05-16 00:00:00,10.5,80.1, ,1005
"""


def test_load_ni_basin_tracks_skips_unit_row():
    df = load_ni_basin_tracks(io.StringIO(SAMPLE_CSV))
    assert len(df) == 4
    assert df.iloc[0]["NAME"] == "AMPHAN"


def test_get_storm_track_filters_and_orders_by_time():
    df = load_ni_basin_tracks(io.StringIO(SAMPLE_CSV))
    track = get_storm_track(df, "amphan", season=2026)
    assert len(track) == 3
    assert track[0].wind_knots == 35
    assert track[-1].wind_knots == 60
    assert track[0].timestamp < track[-1].timestamp


def test_get_storm_track_excludes_other_storms():
    df = load_ni_basin_tracks(io.StringIO(SAMPLE_CSV))
    track = get_storm_track(df, "amphan", season=2026)
    assert all(p.name == "AMPHAN" for p in track)


def test_get_storm_track_handles_whitespace_only_missing_value():
    """Regression test: a real /assess call in production hit ValueError:
    could not convert string to float: ' ' before this fix."""
    df = load_ni_basin_tracks(io.StringIO(SAMPLE_CSV_WITH_WHITESPACE_MISSING))
    track = get_storm_track(df, "GAPWIND", season=2020)
    assert len(track) == 1
    assert track[0].wind_knots is None
    assert track[0].pressure_mb == 1005


def test_safe_float_handles_nan_whitespace_and_real_values():
    import pandas as pd

    assert _safe_float(float("nan")) is None
    assert _safe_float(" ") is None
    assert _safe_float("") is None
    assert _safe_float("45.5") == 45.5
    assert _safe_float(pd.NA) is None


def test_bundled_cache_file_exists_and_is_a_real_ibtracs_csv():
    """The whole point of bundling this file is that it's actually there and
    loadable in the deployed package -- not just referenced in code. This
    guards against the exact bug this fix could otherwise reintroduce: the
    file existing in the source tree but silently missing from what
    `pip install .` actually packages (see pyproject.toml package-data)."""

    assert _BUNDLED_CACHE_PATH.exists(), (
        f"{_BUNDLED_CACHE_PATH} is missing -- load_ni_basin_tracks() would silently "
        "fall through to the live NOAA URL, defeating the point of bundling it"
    )
    df = load_ni_basin_tracks(_BUNDLED_CACHE_PATH)
    assert len(df) > 1000  # sanity: this is the real ~63k-row file, not a stub
    assert "AMPHAN" in df["NAME"].str.upper().values


def test_load_ni_basin_tracks_prefers_bundled_cache_over_live_url(monkeypatch):
    """With no explicit source given, the bundled cache must be used --
    never a silent network call to NOAA on every request."""

    calls = []
    monkeypatch.setattr(
        "coppernick.data.ibtracs.pd.read_csv",
        lambda source, **kwargs: calls.append(source) or __import__("pandas").DataFrame({"NAME": ["X"]}),
    )
    load_ni_basin_tracks()
    assert calls == [_BUNDLED_CACHE_PATH]
