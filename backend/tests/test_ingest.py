"""Tests for ingest modules (uses live HTTP — mark as integration tests)."""
import pytest
from unittest.mock import patch, MagicMock
from app.ingest.eonet import fetch_events
from app.ingest.gibs import fetch_imagery_url, _tile_coords


# ── GIBS ─────────────────────────────────────────────────────────────────────

def test_tile_coords_known():
    """WMTS tile for (0,0) at zoom 0 is always (0,0)."""
    row, col = _tile_coords(lat=0, lon=0, zoom=0)
    assert row == 0
    assert col == 0


def test_gibs_url_format():
    url = fetch_imagery_url(lat=37.5, lon=-120.0, date="2024-07-01", layer="fire", zoom=6)
    assert url.startswith("https://gibs.earthdata.nasa.gov")
    assert "2024-07-01" in url
    assert url.endswith(".jpg")


def test_gibs_default_date():
    url = fetch_imagery_url(lat=37.5, lon=-120.0, date="")
    # Should default to yesterday — just check it's a valid URL
    assert "gibs.earthdata.nasa.gov" in url


# ── EONET (mocked) ────────────────────────────────────────────────────────────

MOCK_EONET_RESPONSE = {
    "events": [
        {
            "id": "EONET_6789",
            "title": "Wildfire, California",
            "status": "open",
            "categories": [{"id": "wildfires", "title": "Wildfires"}],
            "geometry": [{"date": "2024-07-01T00:00:00Z", "type": "Point", "coordinates": [-120.5, 37.1]}],
            "closed": None,
        }
    ]
}


def test_fetch_events_returns_list():
    with patch("app.ingest.eonet.httpx.Client") as mock_client:
        mock_resp = MagicMock()
        mock_resp.json.return_value = MOCK_EONET_RESPONSE
        mock_resp.raise_for_status.return_value = None
        mock_client.return_value.__enter__.return_value.get.return_value = mock_resp

        events = fetch_events(limit=5)
        assert isinstance(events, list)
        assert len(events) == 1
        assert events[0]["id"] == "EONET_6789"
