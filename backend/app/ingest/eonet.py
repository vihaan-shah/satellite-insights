"""
NASA EONET — Live natural events feed (no API key required).
https://eonet.gsfc.nasa.gov/docs/v3
"""
import httpx
from typing import Optional

EONET_BASE = "https://eonet.gsfc.nasa.gov/api/v3"


def fetch_events(category: Optional[str] = None, limit: int = 20, days: int = 30) -> list[dict]:
    """
    Fetch open natural events from EONET v3.

    Args:
        category: e.g. 'wildfires', 'floods', 'severeStorms', 'volcanoes'
        limit: max number of events
        days: look-back window

    Returns:
        List of event dicts (title, id, categories, geometry, status, …)
    """
    params: dict = {"limit": limit, "days": days, "status": "open"}

    if category:
        url = f"{EONET_BASE}/categories/{category}"
    else:
        url = f"{EONET_BASE}/events"

    with httpx.Client(timeout=15) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    return data.get("events", [])


def fetch_event_by_id(event_id: str) -> Optional[dict]:
    """Fetch a single event by its EONET ID."""
    url = f"{EONET_BASE}/events/{event_id}"
    with httpx.Client(timeout=15) as client:
        resp = client.get(url)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
