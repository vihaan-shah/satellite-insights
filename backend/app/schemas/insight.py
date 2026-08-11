"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, Field
from typing import Optional, Any


class Event(BaseModel):
    id: str
    title: str
    categories: list[dict] = []
    geometry: list[dict] = []
    status: str = "open"
    closed: Optional[str] = None

    class Config:
        extra = "allow"


class Insight(BaseModel):
    event_id: str
    title: str
    brief: str
    imagery_url: str = ""
    hotspot_count: int = 0
    analysis: dict[str, Any] = {}
    categories: list[str] = []

    class Config:
        extra = "allow"


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    event_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
