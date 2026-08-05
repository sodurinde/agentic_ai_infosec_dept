from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from beanie import PydanticObjectId
from services.governance_service.models.policy import Policy
from shared.logging import log_audit_event
from shared.database import db_manager


router = APIRouter(prefix="/policies", tags=["Policies"])


class PolicyCreateRequest(BaseModel):
    title: str
    content: str
    version: str
    owner: str
    review_deadline: datetime


class PolicyApprovalRequest(BaseModel):
    policy_id: str
    approved_by: str
    approval_signature: str


@router.get("", response_model=List[Policy])
async def get_policies(x_agent_id: Optional[str] = Header(None)):
    policies = await Policy.find_all().to_list()
    # Audit trail
    await log_audit_event(
        event_type="POLICY_READ",
        agent_identity=x_agent_id or "UNKNOWN_AGENT",
        details={"records_retrieved": len(policies)},
        db_collection=db_manager.db["raw_audit_logs"]
    )
    return policies


@router.post("", response_model=Policy, status_code=201)
async def create_policy(
    payload: PolicyCreateRequest, x_agent_id: Optional[str] = Header(None)
):
    policy = Policy(
        title=payload.title,
        content=payload.content,
        version=payload.version,
        owner=payload.owner,
        review_deadline=payload.review_deadline,
        status="DRAFT"
    )
    await policy.insert()
    # Audit trail
    await log_audit_event(
        event_type="POLICY_CREATED",
        agent_identity=x_agent_id or "UNKNOWN_AGENT",
        details={"policy_id": str(policy.id), "title": policy.title},
        db_collection=db_manager.db["raw_audit_logs"]
    )
    return policy


@router.post("/approve", response_model=Policy)
async def approve_policy(
    payload: PolicyApprovalRequest, x_agent_id: Optional[str] = Header(None)
):
    if (
        not payload.approved_by.strip()
        or not payload.approval_signature.strip()
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Signature validation failed. Human-in-the-loop approvals "
                "require an authorized name and signature."
            )
        )

    try:
        policy = await Policy.get(PydanticObjectId(payload.policy_id))
    except Exception:
        policy = None

    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found.")

    policy.status = "APPROVED"
    policy.approved_by = payload.approved_by
    policy.approval_signature = payload.approval_signature
    policy.last_reviewed = datetime.now(timezone.utc)
    await policy.save()

    # Audit trail
    await log_audit_event(
        event_type="POLICY_APPROVED",
        agent_identity=x_agent_id or "UNKNOWN_AGENT",
        details={
            "policy_id": str(policy.id),
            "approved_by": payload.approved_by,
            "signature": payload.approval_signature
        },
        severity="WARNING",
        db_collection=db_manager.db["raw_audit_logs"]
    )
    return policy
