from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from pydantic import BaseModel

from app.ingest.eonet import fetch_events
from app.ingest.firms import fetch_fire_hotspots
from app.ingest.gibs import fetch_imagery_url
from app.analysis.indices import compute_indices
from app.analysis.event_detector import detect_anomalies
from app.ai.summarizer import generate_brief
from app.ai.agent import run_agent
from app.store.db import get_event, save_event, list_events, save_insight, get_insight_for_event
from app.store.vectorstore import store_brief, search_briefs
from app.schemas.insight import Event, Insight, ChatRequest, ChatResponse

router = APIRouter()


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

@router.get("/events", response_model=list[Event])
def get_events(
    category: Optional[str] = Query(None, description="Filter by category: wildfires|floods|severeStorms|volcanoes"),
    limit: int = Query(20, le=100),
):
    """Return recent natural events from EONET (cached in local DB)."""
    events = list_events(category=category, limit=limit)
    if not events:
        # Live fetch if cache empty
        raw = fetch_events(category=category, limit=limit)
        for e in raw:
            save_event(e)
        events = raw
    return events


@router.get("/events/{event_id}", response_model=Event)
def get_event_detail(event_id: str):
    event = get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


# ---------------------------------------------------------------------------
# Insights
# ---------------------------------------------------------------------------

@router.get("/insights", response_model=list[Insight])
def get_insights(limit: int = Query(10, le=50)):
    """Return the latest generated situation briefs."""
    from app.store.db import list_insights
    return list_insights(limit=limit)


@router.post("/insights/{event_id}", response_model=Insight)
def generate_insight(event_id: str):
    """
    Full pipeline for a single event:
      1. Fetch GIBS imagery URL
      2. Pull FIRMS fire hotspots (if wildfire)
      3. Compute indices / anomaly detection
      4. Generate Granite brief
      5. Store in DB + vector store
    """
    event = get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Check for cached insight
    existing = get_insight_for_event(event_id)
    if existing:
        return existing

    # --- Imagery ---
    imagery_url = fetch_imagery_url(
        lat=event["geometry"][0]["coordinates"][1] if event.get("geometry") else 0,
        lon=event["geometry"][0]["coordinates"][0] if event.get("geometry") else 0,
        date=event.get("closed") or event.get("geometry", [{}])[-1].get("date", ""),
    )

    # --- Fire hotspots (only for wildfire category) ---
    hotspots = []
    if any(c.get("id") == "wildfires" for c in event.get("categories", [])):
        coords = event.get("geometry", [{}])[-1].get("coordinates", [0, 0])
        hotspots = fetch_fire_hotspots(lat=coords[1], lon=coords[0])

    # --- Analysis ---
    analysis = compute_indices(hotspots=hotspots)
    anomalies = detect_anomalies(analysis)

    # --- Brief generation ---
    brief_text = generate_brief(event=event, analysis=analysis, anomalies=anomalies)

    insight: Insight = {
        "event_id": event_id,
        "title": event.get("title", "Unknown Event"),
        "brief": brief_text,
        "imagery_url": imagery_url,
        "hotspot_count": len(hotspots),
        "analysis": analysis,
        "categories": [c.get("title", "") for c in event.get("categories", [])],
    }

    save_insight(insight)
    store_brief(event_id=event_id, brief=brief_text, metadata={"title": event.get("title", "")})

    return insight


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """LangChain agent with RAG-backed Q&A over satellite briefs."""
    # Search for relevant past briefs (RAG context)
    rag_docs = search_briefs(query=req.message, k=3)
    context_snippets = "\n\n".join([d.page_content for d in rag_docs])

    answer = run_agent(
        user_message=req.message,
        event_id=req.event_id,
        rag_context=context_snippets,
    )
    return {"answer": answer}
