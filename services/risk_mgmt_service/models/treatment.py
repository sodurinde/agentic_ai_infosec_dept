from datetime import datetime
from typing import Optional
from beanie import Document


class TreatmentPlan(Document):
    risk_id: str
    owner: str
    target_date: datetime
    mitigation_actions: str
    expected_control_effectiveness: float
    status: str = "PROPOSED"  # PROPOSED, IN_PROGRESS, COMPLETED
    actual_outcome: Optional[str] = None

    class Settings:
        name = "treatment_plans"
