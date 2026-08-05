import asyncio
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
    start_periodic_parquet_archiver,
    flush_logs_to_parquet,
)
from shared.middleware import AgentSafetyMiddleware  # noqa: E402

from services.risk_mgmt_service.models.methodology import (  # noqa: E402
    Methodology,
)
from services.risk_mgmt_service.models.risk import Risk  # noqa: E402
from services.risk_mgmt_service.models.treatment import (  # noqa: E402
    TreatmentPlan,
)

from services.risk_mgmt_service.routers.risks import (  # noqa: E402
    router as risks_router,
)

background_tasks: set[asyncio.Task[Any]] = set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    models = [Methodology, Risk, TreatmentPlan]
    await db_manager.initialize(document_models=models)

    task_archiver = asyncio.create_task(start_periodic_parquet_archiver())
    background_tasks.add(task_archiver)
    task_archiver.add_done_callback(background_tasks.discard)

    yield

    await flush_logs_to_parquet()
    await db_manager.close()


app = FastAPI(
    title="InfoSec Risk Management Service",
    description=(
        "Microservice for identifying, assessing, mitigating, "
        "and escalating cybersecurity risks."
    ),
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(AgentSafetyMiddleware)
app.include_router(risks_router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "service": "risk_management_service"}


@app.get("/ready", tags=["Health"])
async def readiness_check():
    try:
        await Risk.count()
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service not ready: Database unreachable - {e}",
        )
