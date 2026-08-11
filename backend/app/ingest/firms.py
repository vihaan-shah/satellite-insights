"""
NASA FIRMS — Active fire hotspot data.
Requires a free MAP_KEY from https://firms.modaps.eosdis.nasa.gov/api/area/
Set FIRMS_MAP_KEY in your .env file.
"""
import os
import csv
import io
import httpx

FIRMS_BASE = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
MAP_KEY = os.getenv("FIRMS_MAP_KEY", "")


def fetch_fire_hotspots(
    lat: float,
    lon: float,
    radius_deg: float = 1.0,
    days: int = 1,
    source: str = "VIIRS_SNPP_NRT",
) -> list[dict]:
    """
    Fetch FIRMS active fire hotspots around a coordinate.

    Returns a list of dicts with keys: latitude, longitude, brightness, frp, acq_date, confidence
    """
    if not MAP_KEY:
        print("[FIRMS] No MAP_KEY set — returning empty hotspot list.")
        return []

    # Bounding box: lon_min,lat_min,lon_max,lat_max
    bbox = f"{lon - radius_deg},{lat - radius_deg},{lon + radius_deg},{lat + radius_deg}"
    url = f"{FIRMS_BASE}/{MAP_KEY}/{source}/{bbox}/{days}"

    with httpx.Client(timeout=20) as client:
        resp = client.get(url)
        if resp.status_code != 200:
            print(f"[FIRMS] HTTP {resp.status_code} — {resp.text[:200]}")
            return []

    reader = csv.DictReader(io.StringIO(resp.text))
    hotspots = []
    for row in reader:
        hotspots.append(
            {
                "latitude": float(row.get("latitude", 0)),
                "longitude": float(row.get("longitude", 0)),
                "brightness": float(row.get("brightness", 0) or 0),
                "frp": float(row.get("frp", 0) or 0),
                "acq_date": row.get("acq_date", ""),
                "confidence": row.get("confidence", ""),
            }
        )
    return hotspots
