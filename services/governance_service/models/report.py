from datetime import datetime
from beanie import Document


class GovernanceReport(Document):
    generated_at: datetime
    metrics: dict  # total_policies, approved_policies, active_exceptions, etc.
    compiled_by: str

    class Settings:
        name = "governance_reports"
