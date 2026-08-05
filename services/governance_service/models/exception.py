from datetime import datetime
from typing import Optional
from beanie import Document


class PolicyException(Document):
    policy_id: str
    owner: str
    justification: str
    compensating_controls: str
    risk_rating: str  # LOW, MEDIUM, HIGH, CRITICAL
    expiry_date: datetime
    is_approved: bool = False
    approved_by: Optional[str] = None
    approval_signature: Optional[str] = None
    is_escalated: bool = False
    escalated_at: Optional[datetime] = None

    class Settings:
        name = "exceptions"
