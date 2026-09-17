"""Night-sky GIBS tile URL builder -- pure logic, no network call needed.

The tile-coordinate math and layer/tile-matrix-set choice were verified
against live GIBS requests during development (see night_sky.py's module
docstring); these tests lock in that verified behavior against regression.
"""

from __future__ import annotations

from datetime import date

import pytest

from coppernick.sky.night_sky import GIBS_LAYER, GIBS_TILE_MATRIX_SET, _lat_lon_to_tile, build_tile_url


def test_lat_lon_to_tile_chennai_zoom4_matches_verified_value():
    # Verified against a real 200 response from GIBS during development.
    row, col = _lat_lon_to_tile(13.08, 80.27, zoom=4)
    assert (row, col) == (4, 14)


def test_lat_lon_to_tile_rejects_unknown_zoom():
    with pytest.raises(ValueError):
        _lat_lon_to_tile(0, 0, zoom=99)


def test_lat_lon_to_tile_clamps_at_edges():
    row, col = _lat_lon_to_tile(-90, 180, zoom=4)
    assert row == 9  # matrix height 10, valid rows 0-9
    assert col == 19  # matrix width 20, valid cols 0-19


def test_build_tile_url_uses_given_date_and_correct_layer():
    ref = build_tile_url(13.08, 80.27, on_date=date(2026, 9, 16), zoom=4)
    assert ref.date == "2026-09-16"
    assert ref.layer == GIBS_LAYER
    assert GIBS_TILE_MATRIX_SET in ref.tile_url
    assert "/4/4/14.png" in ref.tile_url
    assert ref.cloud_cover_note is not None


def test_build_tile_url_defaults_to_yesterday():
    ref = build_tile_url(13.08, 80.27)
    assert ref.date != date.today().isoformat()
