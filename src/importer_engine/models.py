from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class DiscoveryRequest(BaseModel):
    product: str = Field(..., min_length=2, description="Product or HS niche")
    country: str = Field(..., min_length=2, description="Target market country")
    top_n: int = Field(8, ge=1, le=25, description="How many importers to return")
    exporter_context: Optional[str] = Field(
        None,
        description="Optional note about the Indian exporter (certs, capacity, city)",
    )


class RawCandidate(BaseModel):
    name: str
    website: Optional[str] = None
    snippet: str = ""
    source_url: str = ""
    source_label: str = "web_search"
    known_email: Optional[str] = None
    known_phone: Optional[str] = None
    known_linkedin: Optional[str] = None


class ContactInfo(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None


class RankedImporter(BaseModel):
    rank: int
    company_name: str
    website: Optional[str] = None
    relevance_score: float = Field(..., ge=0, le=100)
    match_reason: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_linkedin: Optional[str] = None
    sources_used: list[str] = Field(default_factory=list)
    score_breakdown: dict[str, float] = Field(default_factory=dict)
    confidence: str = "medium"


class DiscoveryResult(BaseModel):
    product: str
    country: str
    top_n: int
    generated_at: str
    mode: str
    queries_used: list[str] = Field(default_factory=list)
    importers: list[RankedImporter] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
