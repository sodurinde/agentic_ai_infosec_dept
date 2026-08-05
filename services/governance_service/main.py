import asyncio
from datetime import datetime, timezone
from typing import Any
import sys
import os

# Add path hacks in dev if importing shared directly
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
)

from fastapi import FastAPI, HTTPException  # noqa: E402
from contextlib import asynccontextmanager  # noqa: E402

from shared.database import db_manager  # noqa: E402
from shared.logging import (  # noqa: E402
    log_audit_event,
    start_periodic_parquet_archiver,
    flush_logs_to_parquet,
)
from shared.middleware import AgentSafetyMiddleware  # noqa: E402

from services.governance_service.models.policy import Policy  # noqa: E402
from services.governance_service.models.exception import (  # noqa: E402
    PolicyException,
)
from services.governance_service.models.report import (  # noqa: E402
    GovernanceReport,
)

from services.governance_service.routers.policies import (  # noqa: E402
    router as policies_router,
)
from services.governance_service.routers.exceptions import (  # noqa: E402
    router as exceptions_router,
)
from services.governance_service.routers.reports import (  # noqa: E402
    router as reports_router,
)

background_tasks: set[asyncio.Task[Any]] = set()


async def check_governance_escalations_loop(interval_seconds: float = 60.0):
    """
    Background loop that checks for overdue policies and expired exceptions.
    """
    while True:
        try:
            now = datetime.now(timezone.utc)

            # 1. Update overdue policies
            overdue_policies = await Policy.find(
                Policy.review_deadline < now,
                Policy.status != "OVERDUE"
            ).to_list()

            for policy in overdue_policies:
                policy.status = "OVERDUE"
                await policy.save()
                await log_audit_event(
                    event_type="POLICY_OVERDUE",
                    agent_identity="governance-scheduler",
                    details={
                        "policy_id": str(policy.id),
                        "title": policy.title
                    },
                    severity="WARNING",
                    db_collection=db_manager.db["raw_audit_logs"]
                )

            # 2. Update expired exceptions to escalated
            expired_exceptions = await PolicyException.find(
                PolicyException.expiry_date < now,
                PolicyException.is_escalated == False  # noqa: E712
            ).to_list()

            for exc in expired_exceptions:
                exc.is_escalated = True
                exc.escalated_at = now
                await exc.save()
                await log_audit_event(
                    event_type="EXCEPTION_ESCALATED",
                    agent_identity="governance-scheduler",
                    details={"exception_id": str(exc.id), "owner": exc.owner},
                    severity="ERROR",
                    db_collection=db_manager.db["raw_audit_logs"]
                )
        except Exception:
            # Prevent background loop from crashing due to unhandled exceptions
            pass
        await asyncio.sleep(interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB with Beanie models
    models = [Policy, PolicyException, GovernanceReport]
    await db_manager.initialize(document_models=models)

    # Start the periodic Parquet log archiver background task
    task_archiver = asyncio.create_task(start_periodic_parquet_archiver())
    background_tasks.add(task_archiver)
    task_archiver.add_done_callback(background_tasks.discard)

    # Start periodic governance scheduler task (runs every 60 seconds)
    task_scheduler = asyncio.create_task(
        check_governance_escalations_loop(60.0)
    )
    background_tasks.add(task_scheduler)
    task_scheduler.add_done_callback(background_tasks.discard)

    yield

    # Force flush remaining logs to Parquet before exiting
    await flush_logs_to_parquet()
    await db_manager.close()


app = FastAPI(
    title="InfoSec Governance Service",
    description=(
        "Microservice managing security policies, exceptions, "
        "approvals, and compliance KPIs."
    ),
    version="1.0.0",
    lifespan=lifespan
)

# Register Safety Middleware
app.add_middleware(AgentSafetyMiddleware)

# Register routers
app.include_router(policies_router)
app.include_router(exceptions_router)
app.include_router(reports_router)


# Standard Health Endpoints
@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "service": "governance_service"}


@app.get("/ready", tags=["Health"])
async def readiness_check():
    try:
        # Check database health
        await Policy.count()
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service not ready: Database unreachable - {e}",
        )
