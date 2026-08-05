from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from beanie import PydanticObjectId
from services.risk_mgmt_service.models.risk import Risk
from services.risk_mgmt_service.models.methodology import Methodology
from services.risk_mgmt_service.models.treatment import TreatmentPlan
from shared.logging import log_audit_event
from shared.database import db_manager

router = APIRouter(prefix="/risks", tags=["Risks"])


class MethodologyCreateRequest(BaseModel):
    name: str
    description: str


class RiskAssessRequest(BaseModel):
    title: str
    description: str
    methodology_id: str
    likelihood: int = Field(..., ge=1, le=5)
    impact: int = Field(..., ge=1, le=5)
    vulnerability_factor: float = Field(0.0, ge=0.0, le=1.0)
    control_effectiveness: float = Field(0.0, ge=0.0, le=1.0)


class TreatmentPlanRequest(BaseModel):
    risk_id: str
    owner: str
    target_date: datetime
    mitigation_actions: str
    expected_control_effectiveness: float = Field(..., ge=0.0, le=1.0)


class EscalateRequest(BaseModel):
    risk_id: str


class IncidentTriggerRequest(BaseModel):
    risk_id: str
    incident_id: str
    description: str
    severity: str  # LOW, MEDIUM, HIGH


@router.post("/methodologies", response_model=Methodology, status_code=201)
async def create_methodology(
    payload: MethodologyCreateRequest, x_agent_id: Optional[str] = Header(None)
):
    methodology = Methodology(
        name=payload.name,
        description=payload.description
    )
    await methodology.insert()
    await log_audit_event(
        event_type="METHODOLOGY_CREATED",
        agent_identity=x_agent_id or "UNKNOWN_AGENT",
        details={
            "methodology_id": str(methodology.id),
            "name": methodology.name
        },
        db_collection=db_manager.db["raw_audit_logs"]
    )
    return methodology


@router.post("/assess", response_model=Risk, status_code=201)
async def assess_risk(
    payload: RiskAssessRequest, x_agent_id: Optional[str] = Header(None)
):
    try:
        methodology = await Methodology.get(
            PydanticObjectId(payload.methodology_id)
        )
    except Exception:
        methodology = None

    if not methodology:
        raise HTTPException(
            status_code=404, detail="Risk Methodology not found."
        )

    inherent_score = payload.likelihood * payload.impact
    residual_score = round(
        inherent_score * (1.0 - payload.control_effectiveness), 2
    )

    risk = Risk(
        title=payload.title,
        description=payload.description,
        methodology_id=payload.methodology_id,
        likelihood=payload.likelihood,
        impact=payload.impact,
        vulnerability_factor=payload.vulnerability_factor,
        control_effectiveness=payload.control_effectiveness,
        inherent_score=inherent_score,
        residual_score=residual_score,
        status="ASSESSED"
    )
    await risk.insert()

    await log_audit_event(
        event_type="RISK_ASSESSED",
        agent_identity=x_agent_id or "UNKNOWN_AGENT",
        details={
            "risk_id": str(risk.id),
            "title": risk.title,
            "inherent_score": inherent_score,
            "residual_score": residual_score
        },
        db_collection=db_manager.db["raw_audit_logs"]
    )
    return risk


@router.get("/register", response_model=List[Risk])
async def get_risk_register(x_agent_id: Optional[str] = Header(None)):
    risks = await Risk.find_all().to_list()
    await log_audit_event(
        event_type="RISK_REGISTER_READ",
        agent_identity=x_agent_id or "UNKNOWN_AGENT",
        details={"records_retrieved": len(risks)},
        db_collection=db_manager.db["raw_audit_logs"]
    )
    return risks


@router.post("/treatment", response_model=TreatmentPlan, status_code=201)
async def define_treatment(
    payload: TreatmentPlanRequest, x_agent_id: Optional[str] = Header(None)
):
    try:
        risk = await Risk.get(PydanticObjectId(payload.risk_id))
    except Exception:
        risk = None

    if not risk:
        raise HTTPException(status_code=404, detail="Risk record not found.")

    plan = TreatmentPlan(
        risk_id=payload.risk_id,
        owner=payload.owner,
        target_date=payload.target_date,
        mitigation_actions=payload.mitigation_actions,
        expected_control_effectiveness=payload.expected_control_effectiveness,
        status="IN_PROGRESS"
    )
    await plan.insert()

    risk.status = "TREATED"
    risk.control_effectiveness = payload.expected_control_effectiveness
    risk.residual_score = round(
        risk.inherent_score * (1.0 - risk.control_effectiveness), 2
    )
    risk.updated_at = datetime.now(timezone.utc)
    await risk.save()

    await log_audit_event(
        event_type="RISK_TREATMENT_PLAN_DEFINED",
        agent_identity=x_agent_id or "UNKNOWN_AGENT",
        details={
            "treatment_id": str(plan.id),
            "risk_id": payload.risk_id,
            "new_residual_score": risk.residual_score
        },
        severity="WARNING",
        db_collection=db_manager.db["raw_audit_logs"]
    )
    return plan


@router.post("/escalate", response_model=Risk)
async def escalate_risk(
    payload: EscalateRequest, x_agent_id: Optional[str] = Header(None)
):
    try:
        risk = await Risk.get(PydanticObjectId(payload.risk_id))
    except Exception:
        risk = None

    if not risk:
        raise HTTPException(status_code=404, detail="Risk record not found.")

    if risk.residual_score < 12.0:
        raise HTTPException(
            status_code=400,
            detail=(
                "Risk does not exceed the appetite tolerance "
                "threshold (residual score >= 12.0) for escalation."
            )
        )

    risk.status = "ESCALATED"
    risk.updated_at = datetime.now(timezone.utc)
    await risk.save()

    await log_audit_event(
        event_type="RISK_ESCALATED",
        agent_identity=x_agent_id or "UNKNOWN_AGENT",
        details={
            "risk_id": str(risk.id),
            "residual_score": risk.residual_score
        },
        severity="ERROR",
        db_collection=db_manager.db["raw_audit_logs"]
    )
    return risk


@router.post("/incident-trigger", response_model=Risk)
async def trigger_incident(
    payload: IncidentTriggerRequest, x_agent_id: Optional[str] = Header(None)
):
    try:
        risk = await Risk.get(PydanticObjectId(payload.risk_id))
    except Exception:
        risk = None

    if not risk:
        raise HTTPException(status_code=404, detail="Risk record not found.")

    old_likelihood = risk.likelihood
    if payload.severity.upper() == "HIGH":
        if risk.likelihood < 5:
            risk.likelihood += 1

    risk.inherent_score = risk.likelihood * risk.impact
    risk.residual_score = round(
        risk.inherent_score * (1.0 - risk.control_effectiveness), 2
    )
    risk.updated_at = datetime.now(timezone.utc)
    await risk.save()

    await log_audit_event(
        event_type="RISK_INCIDENT_TRIGGERED",
        agent_identity=x_agent_id or "UNKNOWN_AGENT",
        details={
            "risk_id": str(risk.id),
            "incident_id": payload.incident_id,
            "incident_severity": payload.severity,
            "old_likelihood": old_likelihood,
            "new_likelihood": risk.likelihood,
            "new_residual_score": risk.residual_score
        },
        severity="ERROR" if payload.severity.upper() == "HIGH" else "WARNING",
        db_collection=db_manager.db["raw_audit_logs"]
    )
    return risk
