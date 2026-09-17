"""IBTrACS loader, tested against a small fixture matching the real CSV's
two-header-row shape (column names, then units) -- no live network call."""

from __future__ import annotations

import io

from coppernick.data.ibtracs import get_storm_track, load_ni_basin_tracks

SAMPLE_CSV = """SID,SEASON,NAME,ISO_TIME,LAT,LON,USA_WIND,USA_PRES
 ,Year, , ,degrees_north,degrees_east,kts,mb
2026123N10080,2026,AMPHAN,2026-05-16 00:00:00,10.5,80.1,35,1005
2026123N10080,2026,AMPHAN,2026-05-16 06:00:00,11.2,79.8,45,998
2026123N10080,2026,AMPHAN,2026-05-16 12:00:00,12.0,79.5,60,985
2026456N15085,2026,OTHERSTORM,2026-06-01 00:00:00,15.0,85.0,30,1008
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
