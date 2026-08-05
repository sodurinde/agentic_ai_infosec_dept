from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Header
from services.governance_service.models.policy import Policy
from services.governance_service.models.exception import PolicyException
from services.governance_service.models.report import GovernanceReport
from shared.logging import log_audit_event
from shared.database import db_manager


router = APIRouter(prefix="/governance", tags=["Governance Reports"])


@router.get("/report", response_model=GovernanceReport)
async def generate_report(x_agent_id: Optional[str] = Header(None)):
    total_policies = await Policy.count()
    approved_policies = await Policy.find(Policy.status == "APPROVED").count()

    # Calculate percentage
    pct_approved = 0.0
    if total_policies > 0:
        pct_approved = round((approved_policies / total_policies) * 100.0, 2)

    active_exceptions = await PolicyException.find(
        PolicyException.is_approved == True  # noqa: E712
    ).count()
    escalated_exceptions = await PolicyException.find(
        PolicyException.is_escalated == True  # noqa: E712
    ).count()

    metrics = {
        "total_policies": total_policies,
        "approved_policies": approved_policies,
        "percentage_approved": pct_approved,
        "active_exceptions": active_exceptions,
        "escalated_exceptions": escalated_exceptions
    }

    report = GovernanceReport(
        generated_at=datetime.now(timezone.utc),
        metrics=metrics,
        compiled_by=x_agent_id or "SYSTEM"
    )
    await report.insert()

    # Audit trail
    await log_audit_event(
        event_type="GOVERNANCE_REPORT_GENERATED",
        agent_identity=x_agent_id or "UNKNOWN_AGENT",
        details={"report_id": str(report.id), "metrics": metrics},
        db_collection=db_manager.db["raw_audit_logs"]
    )
    return report
