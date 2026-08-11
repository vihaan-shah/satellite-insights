"""
Daily ingestion + analysis + brief generation job.
Run manually: python scripts/daily_job.py
Or schedule via cron: 0 6 * * * cd /app && python scripts/daily_job.py
"""
import sys
import os

# Make sure the app package is importable when run from backend/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.store.db import init_db, save_event, save_insight, get_insight_for_event
from app.store.vectorstore import init_vectorstore, store_brief
from app.ingest.eonet import fetch_events
from app.ingest.firms import fetch_fire_hotspots
from app.ingest.gibs import fetch_imagery_url
from app.analysis.indices import compute_indices
from app.analysis.event_detector import detect_anomalies
from app.ai.summarizer import generate_brief

CATEGORIES = ["wildfires", "floods", "severeStorms", "volcanoes"]


def run():
    print("=== Satellite Insights — Daily Job ===")
    init_db()
    init_vectorstore()

    for category in CATEGORIES:
        print(f"\n[+] Fetching {category} …")
        events = fetch_events(category=category, limit=10, days=7)
        print(f"    {len(events)} events received.")

        for event in events:
            save_event(event)
            event_id = event.get("id", "")

            # Skip if we already have a fresh insight
            if get_insight_for_event(event_id):
                print(f"    [skip] {event.get('title')} — insight already cached.")
                continue

            print(f"    [>>] Processing: {event.get('title')}")

            # Coordinates from last geometry point
            geom = event.get("geometry", [])
            coords = geom[-1].get("coordinates", [0, 0]) if geom else [0, 0]
            date = geom[-1].get("date", "") if geom else ""
            lat, lon = coords[1], coords[0]

            # Imagery URL
            imagery_url = fetch_imagery_url(lat=lat, lon=lon, date=date)

            # Fire hotspots (only for wildfires)
            hotspots = []
            if category == "wildfires":
                hotspots = fetch_fire_hotspots(lat=lat, lon=lon)

            # Analysis
            analysis = compute_indices(hotspots=hotspots)
            anomalies = detect_anomalies(analysis)

            # Brief
            brief = generate_brief(event=event, analysis=analysis, anomalies=anomalies)

            insight = {
                "event_id": event_id,
                "title": event.get("title", ""),
                "brief": brief,
                "imagery_url": imagery_url,
                "hotspot_count": len(hotspots),
                "analysis": analysis,
                "categories": [c.get("title", "") for c in event.get("categories", [])],
            }
            save_insight(insight)
            store_brief(event_id=event_id, brief=brief, metadata={"title": event.get("title", "")})

            print(f"    [ok] Brief stored for {event_id}")

    print("\n=== Daily Job Complete ===")


if __name__ == "__main__":
    run()
