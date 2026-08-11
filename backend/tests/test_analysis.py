"""Tests for analysis modules."""
import pytest
from app.analysis.indices import compute_indices, compute_ndvi_proxy
from app.analysis.event_detector import detect_anomalies
from app.analysis.cloud_detection import estimate_cloud_cover


# ── Fixtures ─────────────────────────────────────────────────────────────────

SAMPLE_HOTSPOTS = [
    {"latitude": 37.1, "longitude": -120.5, "brightness": 345.0, "frp": 120.0, "acq_date": "2024-07-01", "confidence": "h"},
    {"latitude": 37.2, "longitude": -120.6, "brightness": 360.0, "frp": 200.0, "acq_date": "2024-07-01", "confidence": "h"},
    {"latitude": 37.0, "longitude": -120.4, "brightness": 330.0, "frp": 80.0,  "acq_date": "2024-07-01", "confidence": "n"},
]

HIGH_FRP_HOTSPOTS = [
    {"latitude": 37.0, "longitude": -120.0, "brightness": 400.0, "frp": 2000.0, "acq_date": "2024-07-01", "confidence": "h"}
    for _ in range(20)
]


# ── compute_indices ───────────────────────────────────────────────────────────

def test_indices_empty():
    result = compute_indices([])
    assert result["hotspot_count"] == 0
    assert result["risk_level"] == "low"
    assert result["estimated_area_ha"] == 0.0


def test_indices_sample():
    result = compute_indices(SAMPLE_HOTSPOTS)
    assert result["hotspot_count"] == 3
    assert result["total_frp_mw"] == pytest.approx(400.0, abs=0.1)
    assert result["estimated_area_ha"] == pytest.approx(42.0, abs=0.1)
    assert result["risk_level"] == "medium"


def test_indices_high_frp():
    result = compute_indices(HIGH_FRP_HOTSPOTS)
    assert result["risk_level"] == "critical"
    assert result["estimated_area_ha"] == pytest.approx(280.0, abs=0.1)


# ── compute_ndvi_proxy ────────────────────────────────────────────────────────

def test_ndvi_no_fire():
    assert compute_ndvi_proxy([]) == 1.0


def test_ndvi_fire():
    val = compute_ndvi_proxy(SAMPLE_HOTSPOTS)
    assert 0.0 <= val <= 1.0
    assert val < 1.0  # fire should reduce vegetation proxy


# ── detect_anomalies ──────────────────────────────────────────────────────────

def test_anomalies_empty():
    analysis = compute_indices([])
    anomalies = detect_anomalies(analysis)
    assert len(anomalies) >= 1
    assert any("No significant" in a for a in anomalies)


def test_anomalies_high_frp():
    analysis = compute_indices(HIGH_FRP_HOTSPOTS)
    anomalies = detect_anomalies(analysis)
    assert any("critical" in a.lower() or "high" in a.lower() for a in anomalies)


# ── cloud_detection ───────────────────────────────────────────────────────────

def test_cloud_no_hotspots():
    result = estimate_cloud_cover([])
    assert result["flagged"] is True
    assert result["cloud_cover_pct"] > 50


def test_cloud_with_hotspots():
    result = estimate_cloud_cover(SAMPLE_HOTSPOTS)
    assert isinstance(result["cloud_cover_pct"], float)
