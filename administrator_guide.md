# Administrator's Guide: Modular Agentic Banking Security Microservices (Phase 0)

This guide provides system administrators, operations engineers, and developers with complete documentation for configuring, executing, verifying, and troubleshooting the baseline environment (Phase 0) of the Information Security microservices framework.

---

## 1. System Overview

The InfoSec Agentic Microservices architecture is built on a modular design utilizing the following baseline technology stack:
*   **API Framework**: FastAPI (v0.110+)
*   **Database ODM**: Beanie ODM (v2.1.0) / PyMongo (v4.17.0)
*   **Logging Engine**: Pandas / PyArrow (Parquet buffer & Snappy compression)
*   **Cloud Storage**: Google Cloud Storage (GCS)
*   **Runtime Environment**: Python 3.11+ / Docker Containerization

---

## 2. Configuration & Environment Variables

The microservice framework relies on environment variables for database connections, logging destinations, and deployment specifics. A local `.env` file must be maintained in the project root:

```env
ENVIRONMENT=development
PORT=8000
MONGO_URI=mongodb://localhost:27017
DB_NAME=bank_infosec
LOCAL_LOG_DIR=C:/Users/HP/.gemini/antigravity/scratch/bank_infosec_agent_stories/logs
GCP_PROJECT=bank-infosec-dev
GCS_BUCKET=bank-audit-logs-dev
PARQUET_LOG_BUFFER_SIZE=5
PARQUET_ARCHIVE_INTERVAL_SECONDS=10
```

### Key Parameter Definitions:
*   `MONGO_URI`: The connection string for the MongoDB instance.
*   `LOCAL_LOG_DIR`: Target directory for storing Snappy-compressed Parquet logs locally (used as a fallback if GCP is unreachable).
*   `PARQUET_LOG_BUFFER_SIZE`: The threshold count of raw audit logs in memory before an automatic write-to-disk and GCS upload is triggered.
*   `PARQUET_ARCHIVE_INTERVAL_SECONDS`: The periodic backup flush interval for the background log archiver.

---

## 3. Shared Library Architecture

The core framework logic resides under the `shared/` package:

### 3.1 Configurations (`shared/config.py`)
Loads settings from the `.env` file using Pydantic's `BaseSettings` utility. Any missing required environment variable or type mismatch will raise an validation error on startup.

### 3.2 Database Connection & Hotfix (`shared/database.py`)
Manages connection lifecycle with MongoDB. 
> [!IMPORTANT]
> **Motor Compatibility Hotfix**: Newer versions of the `motor` asynchronous driver (v3.4.0+) deprecate and remove the `append_metadata` client method, which Beanie (v2.1.0) requires during initialization. To prevent startup crashes, the database manager injects a runtime hotfix that patches `AsyncIOMotorClient` dynamically if the method is missing.

### 3.3 Audit Logging & Parquet Archive (`shared/logging.py`)
Provides a two-tier auditing structure:
1.  **Hot Storage (MongoDB)**: Real-time queries write directly to the `raw_audit_logs` collection.
2.  **Cold Storage (Parquet & GCS)**: Events are buffered in memory. When the buffer size reaches `PARQUET_LOG_BUFFER_SIZE` or `PARQUET_ARCHIVE_INTERVAL_SECONDS` expires:
    *   Logs are formatted into a PyArrow Table with the schema: `(timestamp, event_id, event_type, agent_identity, details_json, severity)`.
    *   Written to local disk with **Snappy Compression** under `LOCAL_LOG_DIR`.
    *   Uploaded asynchronously to the GCS bucket under `logs/YYYY/MM/DD/audit_logs_*.parquet`.

### 3.4 Safety Middleware (`shared/middleware.py`)
Intercepts all incoming HTTP requests to verify agent security:
*   Enforces the presence of the `X-Agent-ID` header. Requests lacking this header are rejected with a `401 Unauthorized` response.
*   Provides a bypass list for public endpoints (such as `/health`, `/ready`, `/docs`, `/openapi.json`).
*   Injects a response execution timing header (`X-Process-Time`).
*   Gracefully traps unhandled exceptions and wraps them into standard `500 Internal Server Error` JSON responses to prevent data or stack trace leaks.

---

## 4. Base Template Service (`services/base_service/main.py`)

The boilerplate service serves as the template for building all 38 security microservices:
*   **Lifespan Management**: Initializes the Beanie ODM model mapping on startup, starts the background log archiver task, and ensures a clean connection closure and log flush on shutdown.
*   **Task Reference Protection**: Maintains a strong reference to the background archiver task using a module-level `background_tasks` set, preventing premature garbage collection by the event loop.

---

## 5. Operations & Administration

### 5.1 Local Service Execution
Start the service locally using Uvicorn in your virtual environment:
```powershell
C:\Users\HP\.venv_infosec\Scripts\uvicorn.exe services.base_service.main:app --host 127.0.0.1 --port 8000
```

### 5.2 Containerized Local Execution
Launch the database infrastructure and the template container together using Docker Compose:
```powershell
# Build and run containers in background
docker-compose up -d --build

# Inspect container status
docker-compose ps
```

### 5.3 Storing Parquet Log Backups (WORM Compliance)
For banking compliance (e.g., PCI-DSS, SOC2), the target GCS bucket should be configured with a WORM (Write Once Read Many) policy:
```powershell
# Create standard bucket
gcloud storage buckets create gs://bank-audit-logs-prod --project=bank-infosec-prod --location=us-central1 --uniform-bucket-level-access

# Enable retention policy for 7 years (220,752,000 seconds)
gcloud storage buckets update gs://bank-audit-logs-prod --retention-period=220752000s
```

---

## 6. Troubleshooting Common Issues

### 6.1 Windows Path Length Limit (260 characters)
*   **Symptom**: Virtualenv setups (`ensurepip`) or Git checkouts fail with "No such file or directory" errors.
*   **Resolution**: 
    1. Create the virtual environment in a shorter path (e.g., `C:\Users\HP\.venv_infosec`).
    2. Configure Git to support long paths:
       ```bash
       git config core.longpaths true
       ```

### 6.2 MotorDatabase "Object is not callable" during Beanie init
*   **Symptom**: App startup crashes with a `TypeError` complaining about calling a `MotorDatabase` object.
*   **Resolution**: Ensure that the hotfix script in `shared/database.py` is imported. This dynamically patches `AsyncIOMotorClient` with `append_metadata` before Beanie initialization is triggered.

### 6.3 Missing X-Agent-ID warnings
*   **Symptom**: Log reports `Rejected request to /metadata - Missing X-Agent-ID header`.
*   **Resolution**: Clients calling protected endpoints must pass the header:
    `X-Agent-ID: <your-agent-identifier>`
