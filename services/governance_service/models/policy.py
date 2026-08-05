from datetime import datetime
from typing import Optional
from beanie import Document


class Policy(Document):
    title: str
    content: str
    version: str
    owner: str
    review_deadline: datetime
    last_reviewed: Optional[datetime] = None
    approved_by: Optional[str] = None
    approval_signature: Optional[str] = None
    status: str = "DRAFT"  # DRAFT, APPROVED, OVERDUE

    class Settings:
        name = "policies"
