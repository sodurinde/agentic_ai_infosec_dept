from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from beanie import PydanticObjectId
from services.governance_service.models.exception import PolicyException
from services.governance_service.models.policy import Policy
from shared.logging import log_audit_event
from shared.database import db_manager


router = APIRouter(prefix="/exceptions", tags=["Exceptions"])


class ExceptionCreateRequest(BaseModel):
    policy_id: str
    owner: str
    justification: str
    compensating_controls: str
    risk_rating: str  # LOW, MEDIUM, HIGH, CRITICAL
    expiry_date: datetime
    approved_by: Optional[str] = None
    approval_signature: Optional[str] = None


@router.post("", response_model=PolicyException, status_code=201)
async def create_exception(
    payload: ExceptionCreateRequest, x_agent_id: Optional[str] = Header(None)
):
    # Validate risk rating
    valid_ratings = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    if payload.risk_rating.upper() not in valid_ratings:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid risk rating. Must be one of {valid_ratings}"
        )

    # Check if policy exists
    try:
        policy = await Policy.get(PydanticObjectId(payload.policy_id))
    except Exception:
        policy = None
    if not policy:
        raise HTTPException(status_code=404, detail="Target Policy not found.")

    # Check if this exception has risk acceptance signature
    is_approved = False
    if payload.approved_by or payload.approval_signature:
        if not payload.approved_by or not payload.approval_signature:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Partial approval signature. Risk acceptance "
                    "requires both approved_by and approval_signature."
                )
            )
        is_approved = True

    # Insert exception
    exc = PolicyException(
        policy_id=payload.policy_id,
        owner=payload.owner,
        justification=payload.justification,
        compensating_controls=payload.compensating_controls,
        risk_rating=payload.risk_rating.upper(),
        expiry_date=payload.expiry_date,
        is_approved=is_approved,
        approved_by=payload.approved_by,
        approval_signature=payload.approval_signature,
        is_escalated=False
    )
    await exc.insert()

    # Audit trail
    await log_audit_event(
        event_type="EXCEPTION_CREATED",
        agent_identity=x_agent_id or "UNKNOWN_AGENT",
        details={
            "exception_id": str(exc.id),
            "policy_id": payload.policy_id,
            "risk_rating": exc.risk_rating,
            "is_approved": is_approved
        },
        severity="WARNING" if is_approved else "INFO",
        db_collection=db_manager.db["raw_audit_logs"]
    )
    return exc


@router.get("/escalations", response_model=List[PolicyException])
async def get_escalations(x_agent_id: Optional[str] = Header(None)):
    escalated = await PolicyException.find(
        PolicyException.is_escalated == True  # noqa: E712
    ).to_list()
    # Audit trail
    await log_audit_event(
        event_type="ESCALATIONS_READ",
        agent_identity=x_agent_id or "UNKNOWN_AGENT",
        details={"records_retrieved": len(escalated)},
        db_collection=db_manager.db["raw_audit_logs"]
    )
    return escalated
