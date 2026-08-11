"""
NASA GIBS — Global Imagery Browse Services (no API key required).
Returns WMTS tile URLs for MODIS/VIIRS layers around a given coordinate/date.
https://wiki.earthdata.nasa.gov/display/GIBS
"""
from datetime import datetime, timedelta, timezone

GIBS_BASE = "https://gibs.earthdata.nasa.gov/wmts/epsg4326/best"

# Available layers
LAYERS = {
    "true_color": "MODIS_Terra_CorrectedReflectance_TrueColor",
    "fire": "MODIS_Terra_Thermal_Anomalies_All",
    "ndvi": "MODIS_Terra_NDVI_8Day",
    "floods": "MODIS_Aqua_CorrectedReflectance_TrueColor",
}


def _tile_coords(lat: float, lon: float, zoom: int = 6) -> tuple[int, int]:
    """Convert lat/lon to WMTS tile row/col at a given zoom."""
    import math
    n = 2**zoom
    col = int((lon + 180.0) / 360.0 * n)
    lat_rad = math.radians(lat)
    row = int((1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
    return row, col


def fetch_imagery_url(
    lat: float,
    lon: float,
    date: str = "",
    layer: str = "true_color",
    zoom: int = 6,
) -> str:
    """
    Build a GIBS WMTS tile URL for the given coordinate and date.

    Args:
        lat, lon: centre coordinate
        date: ISO date string (YYYY-MM-DD). Defaults to yesterday.
        layer: one of true_color | fire | ndvi | floods
        zoom: tile zoom level (5–8 recommended)

    Returns:
        Tile image URL string
    """
    if not date or date.startswith("0001"):
        date = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        # Normalise ISO datetime → date only
        date = date[:10]

    layer_id = LAYERS.get(layer, LAYERS["true_color"])
    row, col = _tile_coords(lat, lon, zoom)

    url = (
        f"{GIBS_BASE}/{layer_id}/default/{date}/250m/{zoom}/{row}/{col}.jpg"
    )
    return url


def fetch_thumbnail_url(lat: float, lon: float, date: str = "", layer: str = "true_color") -> str:
    """Return a thumbnail URL suitable for display cards (zoom=5)."""
    return fetch_imagery_url(lat=lat, lon=lon, date=date, layer=layer, zoom=5)
