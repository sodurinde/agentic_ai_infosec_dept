import asyncio
from datetime import datetime, timezone
from typing import Optional, List, Any
import sys
import os

# Add path hacks in dev if importing shared directly
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
)

from fastapi import FastAPI, Header, HTTPException  # noqa: E402
from beanie import Document  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402
from contextlib import asynccontextmanager  # noqa: E402

from shared.database import db_manager  # noqa: E402
from shared.logging import (  # noqa: E402
    log_audit_event,
    start_periodic_parquet_archiver,
    flush_logs_to_parquet,
)
from shared.middleware import AgentSafetyMiddleware  # noqa: E402

background_tasks: set[asyncio.Task[Any]] = set()


# 1. Define Beanie Document Model for this service
class ServiceMetadata(Document):
    name: str
    status: str
    last_updated: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    class Settings:
        name = "base_service_metadata"  # Collection name in MongoDB


# 2. Define API Schemas
class StatusUpdateRequest(BaseModel):
    status: str


# 3. Lifespan Context Manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB with Beanie models
    await db_manager.initialize(document_models=[ServiceMetadata])

    # Start the periodic Parquet log archiver background task
    # and keep a reference to prevent garbage collection
    task = asyncio.create_task(start_periodic_parquet_archiver())
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)

    # Pre-populate data if collection is empty
    count = await ServiceMetadata.count()
    if count == 0:
        initial_meta = ServiceMetadata(
            name="Base Template Service", status="ONLINE"
        )
        await initial_meta.insert()

    yield

    # Force flush remaining logs to Parquet before exiting
    await flush_logs_to_parquet()
    await db_manager.close()


app = FastAPI(
    title="InfoSec Base Service Template",
    description=(
        "Starter microservice boilerplate demonstrating shared DB, "
        "custom logging, and middleware usage."
    ),
    version="1.0.0",
    lifespan=lifespan
)

# Register Safety Middleware
app.add_middleware(AgentSafetyMiddleware)


# 4. Standard Health Endpoints
@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "service": "base_service"}


@app.get("/ready", tags=["Health"])
async def readiness_check():
    try:
        # Check database health
        await ServiceMetadata.count()
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service not ready: Database unreachable - {e}",
        )


# 5. Business Logic Endpoints
@app.get("/metadata", response_model=List[ServiceMetadata], tags=["Metadata"])
async def get_metadata(x_agent_id: Optional[str] = Header(None)):
    # Retrieve from MongoDB
    records = await ServiceMetadata.find_all().to_list()

    # Audit log this lookup
    await log_audit_event(
        event_type="METADATA_READ",
        agent_identity=x_agent_id or "UNKNOWN_AGENT",
        details={"records_retrieved": len(records)},
        db_collection=db_manager.db["raw_audit_logs"]
    )
    return records


@app.post(
    "/metadata/status",
    response_model=ServiceMetadata,
    tags=["Metadata"]
)
async def update_status(
    payload: StatusUpdateRequest, x_agent_id: Optional[str] = Header(None)
):
    meta = await ServiceMetadata.find_one(
        ServiceMetadata.name == "Base Template Service"
    )
    if not meta:
        raise HTTPException(
            status_code=404, detail="Service metadata record not found."
        )

    old_status = meta.status
    meta.status = payload.status
    meta.last_updated = datetime.now(timezone.utc)
    await meta.save()

    # Audit log the modification
    await log_audit_event(
        event_type="STATUS_CHANGED",
        agent_identity=x_agent_id or "UNKNOWN_AGENT",
        details={
            "old_status": old_status,
            "new_status": payload.status
        },
        severity="WARNING",
        db_collection=db_manager.db["raw_audit_logs"]
    )

    return meta
