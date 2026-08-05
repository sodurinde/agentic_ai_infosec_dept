from datetime import datetime, timezone
from beanie import Document
from pydantic import Field


class Risk(Document):
    title: str
    description: str
    methodology_id: str
    likelihood: int  # Scale 1-5
    impact: int  # Scale 1-5
    vulnerability_factor: float = Field(default=0.0, ge=0.0, le=1.0)
    control_effectiveness: float = Field(default=0.0, ge=0.0, le=1.0)
    inherent_score: int
    residual_score: float
    status: str = "IDENTIFIED"  # IDENTIFIED, ASSESSED, TREATED, ESCALATED
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    class Settings:
        name = "risks"
