"""
Anomaly / event detector.
Flags abnormal conditions based on computed indices.
"""
from typing import Any


def detect_anomalies(analysis: dict[str, Any]) -> list[str]:
    """
    Return a list of plain-English anomaly strings for use in the brief prompt.

    Examples:
      ["Fire radiative power exceeds 1,000 MW — high-intensity burn",
       "Estimated affected area > 500 ha",
       "Confidence distribution skewed toward high-confidence detections"]
    """
    flags: list[str] = []

    frp = analysis.get("total_frp_mw", 0)
    area = analysis.get("estimated_area_ha", 0)
    risk = analysis.get("risk_level", "low")
    count = analysis.get("hotspot_count", 0)

    if risk in ("critical", "high"):
        flags.append(f"Fire radiative power {frp:,.0f} MW — {risk}-intensity burn detected.")

    if area > 500:
        flags.append(f"Estimated affected area ~{area:,.0f} ha — significant ground coverage.")

    if count > 100:
        flags.append(f"{count} active hotspot pixels detected in the scene.")

    conf = analysis.get("confidence_distribution", {})
    high_conf = conf.get("h", 0) + conf.get("high", 0)
    if high_conf > 0 and high_conf / max(count, 1) > 0.5:
        flags.append("Majority of detections are high-confidence — low false-positive likelihood.")

    if not flags:
        flags.append("No significant anomalies detected; situation appears contained or early-stage.")

    return flags
