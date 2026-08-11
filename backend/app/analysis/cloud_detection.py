"""
Cloud detection stub.
In production: use s2cloudless or Fmask on Sentinel-2 bands.
Here we return a simple cloud-cover flag based on FIRMS data absence.
"""
from typing import Any


def estimate_cloud_cover(hotspots: list[dict], imagery_date: str = "") -> dict[str, Any]:
    """
    Estimate whether cloud cover may be masking the scene.

    In a real implementation this would run a CNN cloud mask on the
    GIBS/Sentinel imagery. Here we use hotspot density as a proxy:
    low hotspot count + known event = possible cloud obstruction.

    Returns:
        cloud_cover_pct: estimated percentage (0–100)
        flagged: True if cloud cover may be obscuring the scene
    """
    if not hotspots:
        # No data could mean clouds — flag conservatively
        return {"cloud_cover_pct": 60.0, "flagged": True, "note": "No hotspot data; possible cloud cover."}

    # More hotspots → clearer sky (less cloud obstruction)
    cloud_pct = max(0.0, 60.0 - len(hotspots) * 2.0)
    return {
        "cloud_cover_pct": round(cloud_pct, 1),
        "flagged": cloud_pct > 50.0,
        "note": "",
    }
