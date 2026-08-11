"""
Analysis: spectral indices (NDVI, NBR, burn-area estimate) derived from FIRMS hotspot data.
For a full implementation, replace with rasterio/rioxarray over Sentinel-2 or MODIS GeoTIFF.
This version uses FIRMS frp/brightness as proxies when raw rasters are unavailable.
"""
import math
from typing import Any


def compute_indices(hotspots: list[dict]) -> dict[str, Any]:
    """
    Compute summary statistics from FIRMS hotspot records.

    In a production build this function would ingest a multispectral GeoTIFF
    (bands NIR, Red, SWIR) and compute per-pixel NDVI / NBR. Here we derive
    proxy metrics from FIRMS fire radiative power (FRP) values.

    Returns a dict with:
        hotspot_count, total_frp_mw, mean_brightness_k,
        estimated_area_ha, risk_level, confidence_distribution
    """
    if not hotspots:
        return {
            "hotspot_count": 0,
            "total_frp_mw": 0.0,
            "mean_brightness_k": 0.0,
            "estimated_area_ha": 0.0,
            "risk_level": "low",
            "confidence_distribution": {},
        }

    total_frp = sum(h.get("frp", 0) for h in hotspots)
    mean_brightness = sum(h.get("brightness", 0) for h in hotspots) / len(hotspots)

    # Rough burn-area proxy: each VIIRS pixel ≈ 375 m × 375 m = ~14 ha
    estimated_area_ha = len(hotspots) * 14.0

    # Risk level based on FRP
    if total_frp > 5000:
        risk_level = "critical"
    elif total_frp > 1000:
        risk_level = "high"
    elif total_frp > 200:
        risk_level = "medium"
    else:
        risk_level = "low"

    # Confidence distribution
    conf_dist: dict[str, int] = {}
    for h in hotspots:
        conf = str(h.get("confidence", "n")).lower()
        conf_dist[conf] = conf_dist.get(conf, 0) + 1

    return {
        "hotspot_count": len(hotspots),
        "total_frp_mw": round(total_frp, 1),
        "mean_brightness_k": round(mean_brightness, 1),
        "estimated_area_ha": round(estimated_area_ha, 1),
        "risk_level": risk_level,
        "confidence_distribution": conf_dist,
    }


def compute_ndvi_proxy(hotspots: list[dict]) -> float:
    """
    Return a synthetic NDVI-proxy (0–1 scale, inverted so fire = low vegetation).
    0.0 = fully burned / bare, 1.0 = dense healthy vegetation.
    """
    if not hotspots:
        return 1.0  # no fire detected → assume healthy vegetation
    mean_brightness = sum(h.get("brightness", 300) for h in hotspots) / len(hotspots)
    # VIIRS brightness > 340 K strongly correlated with active fire
    ndvi_proxy = max(0.0, 1.0 - (mean_brightness - 300) / 100.0)
    return round(min(ndvi_proxy, 1.0), 3)
