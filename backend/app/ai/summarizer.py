"""
Situation brief generator.
Builds a structured prompt and calls IBM Granite to produce a 3–5 sentence
plain-English mission brief for field personnel.
"""
from typing import Any
from app.ai.granite_client import generate_text


BRIEF_TEMPLATE = """You are a satellite intelligence analyst. Based on the data below, write a concise 3–5 sentence situation brief for field operations personnel. Be factual, specific, and clear. Include: what is happening, where, scale/severity, key risk factors, and recommended awareness.

Event: {title}
Category: {categories}
Location: {location}
Date: {date}

Satellite Analysis:
- Hotspots detected: {hotspot_count}
- Estimated affected area: {estimated_area_ha} hectares
- Fire Radiative Power (total): {total_frp_mw} MW
- Risk level: {risk_level}

Detected anomalies:
{anomalies}

Situation Brief:"""


def generate_brief(event: dict, analysis: dict[str, Any], anomalies: list[str]) -> str:
    """
    Generate an IBM Granite situation brief for the given event and analysis.

    Args:
        event: Raw EONET event dict
        analysis: Output of compute_indices()
        anomalies: Output of detect_anomalies()

    Returns:
        Plain-English brief string (3–5 sentences)
    """
    # Extract location string
    geom = event.get("geometry", [])
    if geom:
        last = geom[-1]
        coords = last.get("coordinates", [0, 0])
        location = f"Lat {coords[1]:.2f}, Lon {coords[0]:.2f}"
        date = last.get("date", "unknown")[:10]
    else:
        location = "Unknown"
        date = "Unknown"

    categories = ", ".join(c.get("title", "") for c in event.get("categories", []))
    anomaly_text = "\n".join(f"  • {a}" for a in anomalies)

    prompt = BRIEF_TEMPLATE.format(
        title=event.get("title", "Unknown Event"),
        categories=categories or "Natural event",
        location=location,
        date=date,
        hotspot_count=analysis.get("hotspot_count", 0),
        estimated_area_ha=analysis.get("estimated_area_ha", 0),
        total_frp_mw=analysis.get("total_frp_mw", 0),
        risk_level=analysis.get("risk_level", "unknown").upper(),
        anomalies=anomaly_text or "  • No significant anomalies.",
    )

    brief = generate_text(prompt=prompt, max_new_tokens=300, temperature=0.4)
    return brief
