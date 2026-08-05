# Agentic Banking Systems: InfoSec Department Agent Prompts

This document contains summaries and copy-paste ready Antigravity IDE (or Claude Code) prompts for all 38 Information Security agents. Each set of prompts explicitly leverages the specified technology stack:
- **Language**: Python
- **Architecture**: Modular Microservices
- **API Layer**: FastAPI
- **Database**: MongoDB
- **Log Storage**: Parquet (buffered locally, archived to Google Cloud Storage or Proxmox local volumes)
- **Cloud Deployment**: Google Cloud Platform (Cloud Run/GCS)
- **On-Premise/Prod Deployment**: Proxmox VE (LXC Containers or Virtual Machines)

---

## User Story 1: Information Security Governance Agent

**Summary**:
The goal of the Information Security Governance Agent is to fulfill the story requirements: \"As a proactive Information Security Governance Agent, I want to continuously maintain the bank’s security strategy, policies, control framework, exceptions, and governance reporting so that security obligations remain current, measurable, and aligned with business and regulatory requirements.\". To achieve this, the microservice `governance-service` will expose several API endpoints using FastAPI, managing data across MongoDB collections like `policies`, `regulatory_mappings`, `exceptions`, `governance_reports`. Key functionality includes enforcing specific business constraints such as: Implement scheduler check for policy review deadlines and auto-escalation of overdue exceptions. Ensure that policy changes and risk acceptances require authorized human signatures. To ensure audit compliance and regulatory alignment, the microservice captures all decisions in high-performance local MongoDB collections and archives long-term logs to compressed Parquet files, which are securely uploaded to Google Cloud Storage. The microservice is designed for containerized deployment, running on GCP Cloud Run for cloud workflows or within Proxmox LXC containers for localized, secure production environments. Acceptance criteria dictate strict validation, verification checkpoints, and human-in-the-loop approvals for any critical or material actions.

### Implementation Prompt
```markdown
Task: Implement the `governance-service` microservice for the 'Information Security Governance Agent'.

Technology Stack:
- Python
- Modular Microservices Architecture
- FastAPI for the API layer
- MongoDB for the database layer (use PyMongo or Beanie ODM)
- Parquet for long-term log storage (using PyArrow/Pandas)
- Google Cloud (GCS/Cloud Run) for cloud deployment
- Proxmox VE for local virtualization/production deployment

Requirements:
1. Create a structured Python project with FastAPI for the `governance-service`:
   - `main.py` - FastAPI app initialization, routes registration, and exception handlers.
   - `config.py` - Pydantic settings loading MongoDB URI, GCP project details, Proxmox configs, and log paths.
   - `models/` - MongoDB schemas mapping the collections: `policies`, `regulatory_mappings`, `exceptions`, `governance_reports`.
   - `routers/` - Clean FastAPI router modules implementing:
          - GET /policies - Retrieve policies with review schedules
     - POST /exceptions - Create a policy exception (requires owner, justification, compensating controls, risk rating, expiry date)
     - GET /exceptions/escalations - Retrieve exceptions nearing expiry for escalation
     - GET /governance/report - Generate compliance and KPI dashboard data
     - POST /policies/approve - Human-in-the-loop approval endpoint for final policy and risk acceptance
   - `services/` - Business logic implementation.
   - `utils/logging.py` - Custom logger logging events to MongoDB for active querying and periodically buffering/writing log events to local Parquet files, with automated upload to Google Cloud Storage.

2. Specific Business Logic:
   - Story: As a proactive Information Security Governance Agent, I want to continuously maintain the bank’s security strategy, policies, control framework, exceptions, and governance reporting so that security obligations remain current, measurable, and aligned with business and regulatory requirements.
   - Custom implementation details: Implement scheduler check for policy review deadlines and auto-escalation of overdue exceptions. Ensure that policy changes and risk acceptances require authorized human signatures.

3. Parquet Logging Pipeline:
   - Configure a background task or worker that runs every hour or when logs reach 1000 records.
   - Buffer raw logs as standard dicts. Format into a Pandas DataFrame or PyArrow Table using a schema representing (timestamp, event_id, event_type, agent_identity, details_json, severity).
   - Write logs locally to a Parquet file (using Snappy compression).
   - Upload the resulting Parquet file to a Google Cloud Storage bucket (e.g., `gs://bank-audit-logs/governance-service/YYYY/MM/DD/`) using `google-cloud-storage`.
   - Setup fallback local directory in Proxmox VM storage if GCP is unreachable.

4. Deployment Configuration:
   - Write a `Dockerfile` multi-stage build optimizing dependency size and security (running as non-root user).
   - Write a Google Cloud Build configuration `cloudbuild.yaml` to build the container and deploy to Google Cloud Run with minimum/maximum instances.
   - Write a Proxmox deployment configuration template (e.g., an Ansible playbook or shell script using pct/qm commands) to deploy this microservice as an LXC container or VM.

Ensure the code is modular, fully typed with Python type hints, incorporates proper error handling with FastAPI HTTPExceptions, and includes clear docstrings. Do not use placeholders.
```

### Testing Prompt
```markdown
Task: Write automated tests (unit, integration, and end-to-end) for the `governance-service` microservice.

Technology Stack:
- Python (pytest, pytest-asyncio)
- FastAPI (TestClient, httpx.AsyncClient)
- MongoDB (using mongomock or testcontainers-mongodb)
- Parquet & GCS Mocking (using pandas, pyarrow, and mock/unittest.mock)

Testing Requirements:
1. Setup Unit Tests under `tests/unit/`:
   - Mock MongoDB connections and database calls using a fixture.
   - Mock Google Cloud Storage client library to verify GCS uploads.
   - Write unit tests for core helper functions, custom formulas, and validation logic: Implement scheduler check for policy review deadlines and auto-escalation of overdue exceptions. Ensure that policy changes and risk acceptances require authorized human signatures.
   - Verify that log archiving buffers logs correctly and generates a valid Parquet file (read the written file back using pyarrow/pandas and check the schemas match).

2. Setup Integration Tests under `tests/integration/`:
   - Use FastAPI `TestClient` or `httpx.AsyncClient` to call endpoints.
   - Test key routes:
          - GET /policies - Retrieve policies with review schedules
     - POST /exceptions - Create a policy exception (requires owner, justification, compensating controls, risk rating, expiry date)
     - GET /exceptions/escalations - Retrieve exceptions nearing expiry for escalation
     - GET /governance/report - Generate compliance and KPI dashboard data
     - POST /policies/approve - Human-in-the-loop approval endpoint for final policy and risk acceptance
   - Verify the request validation (e.g. invalid schemas return 422 Unprocessable Entity).
   - Assert correct database records are inserted/updated in the mock MongoDB.
   - Test failure modes: database timeout, GCS upload failure (check that fallback local storage works).

3. Setup End-to-End Tests under `tests/e2e/`:
   - Test full workflows (e.g., trigger an action, verify the database state, trigger the log archiver, and check the generated parquet payload).
   - Ensure authentication and role-based access checks (if applicable) are tested.

Write clean, highly structured pytest code utilizing fixtures. Include clean tear-downs to reset the database states and local temp files.
```

### Optimization Prompt
```markdown
Task: Optimize the performance, maintainability, and scalability of the `governance-service` microservice.

Areas of Optimization:
1. Database (MongoDB) Performance:
   - Review and implement the index design: Compound index on exceptions for (expiry_date, status) and policies for (next_review_date).
   - Optimize queries using project filters and pagination to minimize memory usage on large collections.
   - Enforce connection pooling configurations with PyMongo/Beanie, tuning `maxPoolSize`, `minPoolSize`, and `maxIdleTimeMS`.

2. Logging (Parquet Archiving) Pipeline:
   - Optimize memory consumption during the Parquet conversion. Instead of loading all buffered logs into memory at once, stream logs in chunks using `pyarrow.parquet.ParquetWriter`.
   - Implement snappy or zstd compression on the Parquet file to optimize GCS storage fees and network transfer times.
   - Use async background tasks (e.g., FastAPI's `BackgroundTasks` or Celery) so that log writing and GCS uploads do not block the active API request-response cycle.

3. Deployment & Cloud Resource Optimization:
   - GCP (Cloud Run): Configure CPU and memory limits. Setup concurrency settings to handle multiple simultaneous requests per container instance, minimizing cold starts.
   - Proxmox (LXC/VM): Design container configuration profiles with appropriate swap space limits, IO limits, and CPU weight parameters.
   - Implement health check endpoints (`/health` and `/ready`) that verify MongoDB and disk storage health for liveness/readiness probes in Proxmox / Google Cloud.

Analyze the microservice code to refactor any synchronous blocking calls to asynchronous alternatives (`async`/`await`). Provide clean, optimized refactoring blocks for index creation, background task logic, and async query executions.
```

---

## User Story 2: Cybersecurity Risk Management Agent

**Summary**:
The goal of the Cybersecurity Risk Management Agent is to fulfill the story requirements: \"As a proactive Cybersecurity Risk Management Agent, I want to identify, quantify, prioritise, and track cyber risks continuously so that decision-makers can reduce exposure within the bank’s approved risk appetite.\". To achieve this, the microservice `risk-management-service` will expose several API endpoints using FastAPI, managing data across MongoDB collections like `risks`, `treatment_plans`, `methodologies`. Key functionality includes enforcing specific business constraints such as: Implement formulaic scoring of inherent and residual risk based on likelihood, impact, vulnerability, and control effectiveness. Integrate automated incident-driven risk update logic. To ensure audit compliance and regulatory alignment, the microservice captures all decisions in high-performance local MongoDB collections and archives long-term logs to compressed Parquet files, which are securely uploaded to Google Cloud Storage. The microservice is designed for containerized deployment, running on GCP Cloud Run for cloud workflows or within Proxmox LXC containers for localized, secure production environments. Acceptance criteria dictate strict validation, verification checkpoints, and human-in-the-loop approvals for any critical or material actions.

### Implementation Prompt
```markdown
Task: Implement the `risk-management-service` microservice for the 'Cybersecurity Risk Management Agent'.

Technology Stack:
- Python
- Modular Microservices Architecture
- FastAPI for the API layer
- MongoDB for the database layer (use PyMongo or Beanie ODM)
- Parquet for long-term log storage (using PyArrow/Pandas)
- Google Cloud (GCS/Cloud Run) for cloud deployment
- Proxmox VE for local virtualization/production deployment

Requirements:
1. Create a structured Python project with FastAPI for the `risk-management-service`:
   - `main.py` - FastAPI app initialization, routes registration, and exception handlers.
   - `config.py` - Pydantic settings loading MongoDB URI, GCP project details, Proxmox configs, and log paths.
   - `models/` - MongoDB schemas mapping the collections: `risks`, `treatment_plans`, `methodologies`.
   - `routers/` - Clean FastAPI router modules implementing:
          - POST /risks/assess - Assess a new risk using approved methodology
     - GET /risks/register - View the complete risk register with inherent and residual risk scores
     - POST /risks/treatment - Define treatment plans with owners, target dates, and outcomes
     - POST /risks/escalate - Escalate risks exceeding appetite tolerance based on SLAs
     - POST /risks/incident-trigger - Trigger updates in risk register when incidents or control failures occur
   - `services/` - Business logic implementation.
   - `utils/logging.py` - Custom logger logging events to MongoDB for active querying and periodically buffering/writing log events to local Parquet files, with automated upload to Google Cloud Storage.

2. Specific Business Logic:
   - Story: As a proactive Cybersecurity Risk Management Agent, I want to identify, quantify, prioritise, and track cyber risks continuously so that decision-makers can reduce exposure within the bank’s approved risk appetite.
   - Custom implementation details: Implement formulaic scoring of inherent and residual risk based on likelihood, impact, vulnerability, and control effectiveness. Integrate automated incident-driven risk update logic.

3. Parquet Logging Pipeline:
   - Configure a background task or worker that runs every hour or when logs reach 1000 records.
   - Buffer raw logs as standard dicts. Format into a Pandas DataFrame or PyArrow Table using a schema representing (timestamp, event_id, event_type, agent_identity, details_json, severity).
   - Write logs locally to a Parquet file (using Snappy compression).
   - Upload the resulting Parquet file to a Google Cloud Storage bucket (e.g., `gs://bank-audit-logs/risk-management-service/YYYY/MM/DD/`) using `google-cloud-storage`.
   - Setup fallback local directory in Proxmox VM storage if GCP is unreachable.

4. Deployment Configuration:
   - Write a `Dockerfile` multi-stage build optimizing dependency size and security (running as non-root user).
   - Write a Google Cloud Build configuration `cloudbuild.yaml` to build the container and deploy to Google Cloud Run with minimum/maximum instances.
   - Write a Proxmox deployment configuration template (e.g., an Ansible playbook or shell script using pct/qm commands) to deploy this microservice as an LXC container or VM.

Ensure the code is modular, fully typed with Python type hints, incorporates proper error handling with FastAPI HTTPExceptions, and includes clear docstrings. Do not use placeholders.
```

### Testing Prompt
```markdown
Task: Write automated tests (unit, integration, and end-to-end) for the `risk-management-service` microservice.

Technology Stack:
- Python (pytest, pytest-asyncio)
- FastAPI (TestClient, httpx.AsyncClient)
- MongoDB (using mongomock or testcontainers-mongodb)
- Parquet & GCS Mocking (using pandas, pyarrow, and mock/unittest.mock)

Testing Requirements:
1. Setup Unit Tests under `tests/unit/`:
   - Mock MongoDB connections and database calls using a fixture.
   - Mock Google Cloud Storage client library to verify GCS uploads.
   - Write unit tests for core helper functions, custom formulas, and validation logic: Implement formulaic scoring of inherent and residual risk based on likelihood, impact, vulnerability, and control effectiveness. Integrate automated incident-driven risk update logic.
   - Verify that log archiving buffers logs correctly and generates a valid Parquet file (read the written file back using pyarrow/pandas and check the schemas match).

2. Setup Integration Tests under `tests/integration/`:
   - Use FastAPI `TestClient` or `httpx.AsyncClient` to call endpoints.
   - Test key routes:
          - POST /risks/assess - Assess a new risk using approved methodology
     - GET /risks/register - View the complete risk register with inherent and residual risk scores
     - POST /risks/treatment - Define treatment plans with owners, target dates, and outcomes
     - POST /risks/escalate - Escalate risks exceeding appetite tolerance based on SLAs
     - POST /risks/incident-trigger - Trigger updates in risk register when incidents or control failures occur
   - Verify the request validation (e.g. invalid schemas return 422 Unprocessable Entity).
   - Assert correct database records are inserted/updated in the mock MongoDB.
   - Test failure modes: database timeout, GCS upload failure (check that fallback local storage works).

3. Setup End-to-End Tests under `tests/e2e/`:
   - Test full workflows (e.g., trigger an action, verify the database state, trigger the log archiver, and check the generated parquet payload).
   - Ensure authentication and role-based access checks (if applicable) are tested.

Write clean, highly structured pytest code utilizing fixtures. Include clean tear-downs to reset the database states and local temp files.
```

### Optimization Prompt
```markdown
Task: Optimize the performance, maintainability, and scalability of the `risk-management-service` microservice.

Areas of Optimization:
1. Database (MongoDB) Performance:
   - Review and implement the index design: Compound index on risks for (severity_score, status) and (assets.id, status).
   - Optimize queries using project filters and pagination to minimize memory usage on large collections.
   - Enforce connection pooling configurations with PyMongo/Beanie, tuning `maxPoolSize`, `minPoolSize`, and `maxIdleTimeMS`.

2. Logging (Parquet Archiving) Pipeline:
   - Optimize memory consumption during the Parquet conversion. Instead of loading all buffered logs into memory at once, stream logs in chunks using `pyarrow.parquet.ParquetWriter`.
   - Implement snappy or zstd compression on the Parquet file to optimize GCS storage fees and network transfer times.
   - Use async background tasks (e.g., FastAPI's `BackgroundTasks` or Celery) so that log writing and GCS uploads do not block the active API request-response cycle.

3. Deployment & Cloud Resource Optimization:
   - GCP (Cloud Run): Configure CPU and memory limits. Setup concurrency settings to handle multiple simultaneous requests per container instance, minimizing cold starts.
   - Proxmox (LXC/VM): Design container configuration profiles with appropriate swap space limits, IO limits, and CPU weight parameters.
   - Implement health check endpoints (`/health` and `/ready`) that verify MongoDB and disk storage health for liveness/readiness probes in Proxmox / Google Cloud.

Analyze the microservice code to refactor any synchronous blocking calls to asynchronous alternatives (`async`/`await`). Provide clean, optimized refactoring blocks for index creation, background task logic, and async query executions.
```

---

## User Story 3: Security Architecture Agent

**Summary**:
The goal of the Security Architecture Agent is to fulfill the story requirements: \"As a proactive Security Architecture Agent, I want to assess proposed systems and changes and recommend secure design patterns so that security weaknesses are addressed before implementation.\". To achieve this, the microservice `security-architecture-service` will expose several API endpoints using FastAPI, managing data across MongoDB collections like `design_assessments`, `patterns`, `findings`, `decision_logs`. Key functionality includes enforcing specific business constraints such as: Implement structured evaluation of trust boundaries, sensitive data flow, threats, and required controls. Enforce blocking status on critical architectural findings. To ensure audit compliance and regulatory alignment, the microservice captures all decisions in high-performance local MongoDB collections and archives long-term logs to compressed Parquet files, which are securely uploaded to Google Cloud Storage. The microservice is designed for containerized deployment, running on GCP Cloud Run for cloud workflows or within Proxmox LXC containers for localized, secure production environments. Acceptance criteria dictate strict validation, verification checkpoints, and human-in-the-loop approvals for any critical or material actions.

### Implementation Prompt
```markdown
Task: Implement the `security-architecture-service` microservice for the 'Security Architecture Agent'.

Technology Stack:
- Python
- Modular Microservices Architecture
- FastAPI for the API layer
- MongoDB for the database layer (use PyMongo or Beanie ODM)
- Parquet for long-term log storage (using PyArrow/Pandas)
- Google Cloud (GCS/Cloud Run) for cloud deployment
- Proxmox VE for local virtualization/production deployment

Requirements:
1. Create a structured Python project with FastAPI for the `security-architecture-service`:
   - `main.py` - FastAPI app initialization, routes registration, and exception handlers.
   - `config.py` - Pydantic settings loading MongoDB URI, GCP project details, Proxmox configs, and log paths.
   - `models/` - MongoDB schemas mapping the collections: `design_assessments`, `patterns`, `findings`, `decision_logs`.
   - `routers/` - Clean FastAPI router modules implementing:
          - POST /assessments/design - Submit and review proposed system design documents
     - GET /patterns - Retrieve approved secure design patterns and standards
     - POST /assessments/deviations - Document architectural deviations and route through the exception process
     - POST /assessments/findings/block - Flag critical design findings that block progression until resolution
     - GET /assessments/audit-trail - Retrieve retained decisions and supporting evidence for audits
   - `services/` - Business logic implementation.
   - `utils/logging.py` - Custom logger logging events to MongoDB for active querying and periodically buffering/writing log events to local Parquet files, with automated upload to Google Cloud Storage.

2. Specific Business Logic:
   - Story: As a proactive Security Architecture Agent, I want to assess proposed systems and changes and recommend secure design patterns so that security weaknesses are addressed before implementation.
   - Custom implementation details: Implement structured evaluation of trust boundaries, sensitive data flow, threats, and required controls. Enforce blocking status on critical architectural findings.

3. Parquet Logging Pipeline:
   - Configure a background task or worker that runs every hour or when logs reach 1000 records.
   - Buffer raw logs as standard dicts. Format into a Pandas DataFrame or PyArrow Table using a schema representing (timestamp, event_id, event_type, agent_identity, details_json, severity).
   - Write logs locally to a Parquet file (using Snappy compression).
   - Upload the resulting Parquet file to a Google Cloud Storage bucket (e.g., `gs://bank-audit-logs/security-architecture-service/YYYY/MM/DD/`) using `google-cloud-storage`.
   - Setup fallback local directory in Proxmox VM storage if GCP is unreachable.

4. Deployment Configuration:
   - Write a `Dockerfile` multi-stage build optimizing dependency size and security (running as non-root user).
   - Write a Google Cloud Build configuration `cloudbuild.yaml` to build the container and deploy to Google Cloud Run with minimum/maximum instances.
   - Write a Proxmox deployment configuration template (e.g., an Ansible playbook or shell script using pct/qm commands) to deploy this microservice as an LXC container or VM.

Ensure the code is modular, fully typed with Python type hints, incorporates proper error handling with FastAPI HTTPExceptions, and includes clear docstrings. Do not use placeholders.
```

### Testing Prompt
```markdown
Task: Write automated tests (unit, integration, and end-to-end) for the `security-architecture-service` microservice.

Technology Stack:
- Python (pytest, pytest-asyncio)
- FastAPI (TestClient, httpx.AsyncClient)
- MongoDB (using mongomock or testcontainers-mongodb)
- Parquet & GCS Mocking (using pandas, pyarrow, and mock/unittest.mock)

Testing Requirements:
1. Setup Unit Tests under `tests/unit/`:
   - Mock MongoDB connections and database calls using a fixture.
   - Mock Google Cloud Storage client library to verify GCS uploads.
   - Write unit tests for core helper functions, custom formulas, and validation logic: Implement structured evaluation of trust boundaries, sensitive data flow, threats, and required controls. Enforce blocking status on critical architectural findings.
   - Verify that log archiving buffers logs correctly and generates a valid Parquet file (read the written file back using pyarrow/pandas and check the schemas match).

2. Setup Integration Tests under `tests/integration/`:
   - Use FastAPI `TestClient` or `httpx.AsyncClient` to call endpoints.
   - Test key routes:
          - POST /assessments/design - Submit and review proposed system design documents
     - GET /patterns - Retrieve approved secure design patterns and standards
     - POST /assessments/deviations - Document architectural deviations and route through the exception process
     - POST /assessments/findings/block - Flag critical design findings that block progression until resolution
     - GET /assessments/audit-trail - Retrieve retained decisions and supporting evidence for audits
   - Verify the request validation (e.g. invalid schemas return 422 Unprocessable Entity).
   - Assert correct database records are inserted/updated in the mock MongoDB.
   - Test failure modes: database timeout, GCS upload failure (check that fallback local storage works).

3. Setup End-to-End Tests under `tests/e2e/`:
   - Test full workflows (e.g., trigger an action, verify the database state, trigger the log archiver, and check the generated parquet payload).
   - Ensure authentication and role-based access checks (if applicable) are tested.

Write clean, highly structured pytest code utilizing fixtures. Include clean tear-downs to reset the database states and local temp files.
```

### Optimization Prompt
```markdown
Task: Optimize the performance, maintainability, and scalability of the `security-architecture-service` microservice.

Areas of Optimization:
1. Database (MongoDB) Performance:
   - Review and implement the index design: Index on design_assessments (status, submission_date) and findings (design_id, severity).
   - Optimize queries using project filters and pagination to minimize memory usage on large collections.
   - Enforce connection pooling configurations with PyMongo/Beanie, tuning `maxPoolSize`, `minPoolSize`, and `maxIdleTimeMS`.

2. Logging (Parquet Archiving) Pipeline:
   - Optimize memory consumption during the Parquet conversion. Instead of loading all buffered logs into memory at once, stream logs in chunks using `pyarrow.parquet.ParquetWriter`.
   - Implement snappy or zstd compression on the Parquet file to optimize GCS storage fees and network transfer times.
   - Use async background tasks (e.g., FastAPI's `BackgroundTasks` or Celery) so that log writing and GCS uploads do not block the active API request-response cycle.

3. Deployment & Cloud Resource Optimization:
   - GCP (Cloud Run): Configure CPU and memory limits. Setup concurrency settings to handle multiple simultaneous requests per container instance, minimizing cold starts.
   - Proxmox (LXC/VM): Design container configuration profiles with appropriate swap space limits, IO limits, and CPU weight parameters.
   - Implement health check endpoints (`/health` and `/ready`) that verify MongoDB and disk storage health for liveness/readiness probes in Proxmox / Google Cloud.

Analyze the microservice code to refactor any synchronous blocking calls to asynchronous alternatives (`async`/`await`). Provide clean, optimized refactoring blocks for index creation, background task logic, and async query executions.
```

---

## User Story 4: Security Engineering Agent

**Summary**:
The goal of the Security Engineering Agent is to fulfill the story requirements: \"As a proactive Security Engineering Agent, I want to deploy, configure, integrate, and optimise security controls so that the bank’s technology environment remains consistently protected.\". To achieve this, the microservice `security-engineering-service` will expose several API endpoints using FastAPI, managing data across MongoDB collections like `control_baselines`, `drift_logs`, `change_records`, `platform_metrics`. Key functionality includes enforcing specific business constraints such as: Implement config parsing and baseline validation logic. Write automatic testing execution routines for low-risk changes and automatic rollback procedures for failed deployments. To ensure audit compliance and regulatory alignment, the microservice captures all decisions in high-performance local MongoDB collections and archives long-term logs to compressed Parquet files, which are securely uploaded to Google Cloud Storage. The microservice is designed for containerized deployment, running on GCP Cloud Run for cloud workflows or within Proxmox LXC containers for localized, secure production environments. Acceptance criteria dictate strict validation, verification checkpoints, and human-in-the-loop approvals for any critical or material actions.

### Implementation Prompt
```markdown
Task: Implement the `security-engineering-service` microservice for the 'Security Engineering Agent'.

Technology Stack:
- Python
- Modular Microservices Architecture
- FastAPI for the API layer
- MongoDB for the database layer (use PyMongo or Beanie ODM)
- Parquet for long-term log storage (using PyArrow/Pandas)
- Google Cloud (GCS/Cloud Run) for cloud deployment
- Proxmox VE for local virtualization/production deployment

Requirements:
1. Create a structured Python project with FastAPI for the `security-engineering-service`:
   - `main.py` - FastAPI app initialization, routes registration, and exception handlers.
   - `config.py` - Pydantic settings loading MongoDB URI, GCP project details, Proxmox configs, and log paths.
   - `models/` - MongoDB schemas mapping the collections: `control_baselines`, `drift_logs`, `change_records`, `platform_metrics`.
   - `routers/` - Clean FastAPI router modules implementing:
          - POST /controls/deploy - Deploy a security platform configuration
     - GET /controls/drift - Detect configuration drift and integration failures against baselines
     - POST /changes/low-risk - Auto-test and implement low-risk changes under delegated authority
     - POST /changes/material - Submit material changes requiring approval and rollback plans
     - GET /metrics/platform - Retrieve health, coverage, capacity, and effectiveness metrics
     - POST /changes/rollback - Rollback failed changes automatically or trigger human escalation
   - `services/` - Business logic implementation.
   - `utils/logging.py` - Custom logger logging events to MongoDB for active querying and periodically buffering/writing log events to local Parquet files, with automated upload to Google Cloud Storage.

2. Specific Business Logic:
   - Story: As a proactive Security Engineering Agent, I want to deploy, configure, integrate, and optimise security controls so that the bank’s technology environment remains consistently protected.
   - Custom implementation details: Implement config parsing and baseline validation logic. Write automatic testing execution routines for low-risk changes and automatic rollback procedures for failed deployments.

3. Parquet Logging Pipeline:
   - Configure a background task or worker that runs every hour or when logs reach 1000 records.
   - Buffer raw logs as standard dicts. Format into a Pandas DataFrame or PyArrow Table using a schema representing (timestamp, event_id, event_type, agent_identity, details_json, severity).
   - Write logs locally to a Parquet file (using Snappy compression).
   - Upload the resulting Parquet file to a Google Cloud Storage bucket (e.g., `gs://bank-audit-logs/security-engineering-service/YYYY/MM/DD/`) using `google-cloud-storage`.
   - Setup fallback local directory in Proxmox VM storage if GCP is unreachable.

4. Deployment Configuration:
   - Write a `Dockerfile` multi-stage build optimizing dependency size and security (running as non-root user).
   - Write a Google Cloud Build configuration `cloudbuild.yaml` to build the container and deploy to Google Cloud Run with minimum/maximum instances.
   - Write a Proxmox deployment configuration template (e.g., an Ansible playbook or shell script using pct/qm commands) to deploy this microservice as an LXC container or VM.

Ensure the code is modular, fully typed with Python type hints, incorporates proper error handling with FastAPI HTTPExceptions, and includes clear docstrings. Do not use placeholders.
```

### Testing Prompt
```markdown
Task: Write automated tests (unit, integration, and end-to-end) for the `security-engineering-service` microservice.

Technology Stack:
- Python (pytest, pytest-asyncio)
- FastAPI (TestClient, httpx.AsyncClient)
- MongoDB (using mongomock or testcontainers-mongodb)
- Parquet & GCS Mocking (using pandas, pyarrow, and mock/unittest.mock)

Testing Requirements:
1. Setup Unit Tests under `tests/unit/`:
   - Mock MongoDB connections and database calls using a fixture.
   - Mock Google Cloud Storage client library to verify GCS uploads.
   - Write unit tests for core helper functions, custom formulas, and validation logic: Implement config parsing and baseline validation logic. Write automatic testing execution routines for low-risk changes and automatic rollback procedures for failed deployments.
   - Verify that log archiving buffers logs correctly and generates a valid Parquet file (read the written file back using pyarrow/pandas and check the schemas match).

2. Setup Integration Tests under `tests/integration/`:
   - Use FastAPI `TestClient` or `httpx.AsyncClient` to call endpoints.
   - Test key routes:
          - POST /controls/deploy - Deploy a security platform configuration
     - GET /controls/drift - Detect configuration drift and integration failures against baselines
     - POST /changes/low-risk - Auto-test and implement low-risk changes under delegated authority
     - POST /changes/material - Submit material changes requiring approval and rollback plans
     - GET /metrics/platform - Retrieve health, coverage, capacity, and effectiveness metrics
     - POST /changes/rollback - Rollback failed changes automatically or trigger human escalation
   - Verify the request validation (e.g. invalid schemas return 422 Unprocessable Entity).
   - Assert correct database records are inserted/updated in the mock MongoDB.
   - Test failure modes: database timeout, GCS upload failure (check that fallback local storage works).

3. Setup End-to-End Tests under `tests/e2e/`:
   - Test full workflows (e.g., trigger an action, verify the database state, trigger the log archiver, and check the generated parquet payload).
   - Ensure authentication and role-based access checks (if applicable) are tested.

Write clean, highly structured pytest code utilizing fixtures. Include clean tear-downs to reset the database states and local temp files.
```

### Optimization Prompt
```markdown
Task: Optimize the performance, maintainability, and scalability of the `security-engineering-service` microservice.

Areas of Optimization:
1. Database (MongoDB) Performance:
   - Review and implement the index design: Index on drift_logs (platform_id, detected_at) and change_records (type, status).
   - Optimize queries using project filters and pagination to minimize memory usage on large collections.
   - Enforce connection pooling configurations with PyMongo/Beanie, tuning `maxPoolSize`, `minPoolSize`, and `maxIdleTimeMS`.

2. Logging (Parquet Archiving) Pipeline:
   - Optimize memory consumption during the Parquet conversion. Instead of loading all buffered logs into memory at once, stream logs in chunks using `pyarrow.parquet.ParquetWriter`.
   - Implement snappy or zstd compression on the Parquet file to optimize GCS storage fees and network transfer times.
   - Use async background tasks (e.g., FastAPI's `BackgroundTasks` or Celery) so that log writing and GCS uploads do not block the active API request-response cycle.

3. Deployment & Cloud Resource Optimization:
   - GCP (Cloud Run): Configure CPU and memory limits. Setup concurrency settings to handle multiple simultaneous requests per container instance, minimizing cold starts.
   - Proxmox (LXC/VM): Design container configuration profiles with appropriate swap space limits, IO limits, and CPU weight parameters.
   - Implement health check endpoints (`/health` and `/ready`) that verify MongoDB and disk storage health for liveness/readiness probes in Proxmox / Google Cloud.

Analyze the microservice code to refactor any synchronous blocking calls to asynchronous alternatives (`async`/`await`). Provide clean, optimized refactoring blocks for index creation, background task logic, and async query executions.
```

---

## User Story 5: Security Operations Centre Agent

**Summary**:
The goal of the Security Operations Centre Agent is to fulfill the story requirements: \"As a proactive Security Operations Centre Agent, I want to monitor and correlate security telemetry continuously and initiate approved response playbooks so that credible threats are detected and contained within agreed service levels.\". To achieve this, the microservice `soc-service` will expose several API endpoints using FastAPI, managing data across MongoDB collections like `telemetry_sources`, `alerts`, `enrichment_context`, `playbook_runs`. Key functionality includes enforcing specific business constraints such as: Implement event correlation logic and a rules engine to classify alert severity. Build automated playbook execution handlers for containment (e.g., calling APIs to isolate VMs or block IPs). To ensure audit compliance and regulatory alignment, the microservice captures all decisions in high-performance local MongoDB collections and archives long-term logs to compressed Parquet files, which are securely uploaded to Google Cloud Storage. The microservice is designed for containerized deployment, running on GCP Cloud Run for cloud workflows or within Proxmox LXC containers for localized, secure production environments. Acceptance criteria dictate strict validation, verification checkpoints, and human-in-the-loop approvals for any critical or material actions.

### Implementation Prompt
```markdown
Task: Implement the `soc-service` microservice for the 'Security Operations Centre Agent'.

Technology Stack:
- Python
- Modular Microservices Architecture
- FastAPI for the API layer
- MongoDB for the database layer (use PyMongo or Beanie ODM)
- Parquet for long-term log storage (using PyArrow/Pandas)
- Google Cloud (GCS/Cloud Run) for cloud deployment
- Proxmox VE for local virtualization/production deployment

Requirements:
1. Create a structured Python project with FastAPI for the `soc-service`:
   - `main.py` - FastAPI app initialization, routes registration, and exception handlers.
   - `config.py` - Pydantic settings loading MongoDB URI, GCP project details, Proxmox configs, and log paths.
   - `models/` - MongoDB schemas mapping the collections: `telemetry_sources`, `alerts`, `enrichment_context`, `playbook_runs`.
   - `routers/` - Clean FastAPI router modules implementing:
          - POST /telemetry/ingest - Ingest and check freshness of security telemetry sources
     - POST /alerts/correlate - Correlate incoming events and enrich alerts with asset, identity, threat, and business context
     - POST /alerts/classify - Prioritize alerts using approved severity rules
     - POST /playbooks/execute - Run containment playbooks when evidence and confidence thresholds are met
     - GET /incidents/performance - Retrieve detection and response metrics (coverage, accuracy, response time)
   - `services/` - Business logic implementation.
   - `utils/logging.py` - Custom logger logging events to MongoDB for active querying and periodically buffering/writing log events to local Parquet files, with automated upload to Google Cloud Storage.

2. Specific Business Logic:
   - Story: As a proactive Security Operations Centre Agent, I want to monitor and correlate security telemetry continuously and initiate approved response playbooks so that credible threats are detected and contained within agreed service levels.
   - Custom implementation details: Implement event correlation logic and a rules engine to classify alert severity. Build automated playbook execution handlers for containment (e.g., calling APIs to isolate VMs or block IPs).

3. Parquet Logging Pipeline:
   - Configure a background task or worker that runs every hour or when logs reach 1000 records.
   - Buffer raw logs as standard dicts. Format into a Pandas DataFrame or PyArrow Table using a schema representing (timestamp, event_id, event_type, agent_identity, details_json, severity).
   - Write logs locally to a Parquet file (using Snappy compression).
   - Upload the resulting Parquet file to a Google Cloud Storage bucket (e.g., `gs://bank-audit-logs/soc-service/YYYY/MM/DD/`) using `google-cloud-storage`.
   - Setup fallback local directory in Proxmox VM storage if GCP is unreachable.

4. Deployment Configuration:
   - Write a `Dockerfile` multi-stage build optimizing dependency size and security (running as non-root user).
   - Write a Google Cloud Build configuration `cloudbuild.yaml` to build the container and deploy to Google Cloud Run with minimum/maximum instances.
   - Write a Proxmox deployment configuration template (e.g., an Ansible playbook or shell script using pct/qm commands) to deploy this microservice as an LXC container or VM.

Ensure the code is modular, fully typed with Python type hints, incorporates proper error handling with FastAPI HTTPExceptions, and includes clear docstrings. Do not use placeholders.
```

### Testing Prompt
```markdown
Task: Write automated tests (unit, integration, and end-to-end) for the `soc-service` microservice.

Technology Stack:
- Python (pytest, pytest-asyncio)
- FastAPI (TestClient, httpx.AsyncClient)
- MongoDB (using mongomock or testcontainers-mongodb)
- Parquet & GCS Mocking (using pandas, pyarrow, and mock/unittest.mock)

Testing Requirements:
1. Setup Unit Tests under `tests/unit/`:
   - Mock MongoDB connections and database calls using a fixture.
   - Mock Google Cloud Storage client library to verify GCS uploads.
   - Write unit tests for core helper functions, custom formulas, and validation logic: Implement event correlation logic and a rules engine to classify alert severity. Build automated playbook execution handlers for containment (e.g., calling APIs to isolate VMs or block IPs).
   - Verify that log archiving buffers logs correctly and generates a valid Parquet file (read the written file back using pyarrow/pandas and check the schemas match).

2. Setup Integration Tests under `tests/integration/`:
   - Use FastAPI `TestClient` or `httpx.AsyncClient` to call endpoints.
   - Test key routes:
          - POST /telemetry/ingest - Ingest and check freshness of security telemetry sources
     - POST /alerts/correlate - Correlate incoming events and enrich alerts with asset, identity, threat, and business context
     - POST /alerts/classify - Prioritize alerts using approved severity rules
     - POST /playbooks/execute - Run containment playbooks when evidence and confidence thresholds are met
     - GET /incidents/performance - Retrieve detection and response metrics (coverage, accuracy, response time)
   - Verify the request validation (e.g. invalid schemas return 422 Unprocessable Entity).
   - Assert correct database records are inserted/updated in the mock MongoDB.
   - Test failure modes: database timeout, GCS upload failure (check that fallback local storage works).

3. Setup End-to-End Tests under `tests/e2e/`:
   - Test full workflows (e.g., trigger an action, verify the database state, trigger the log archiver, and check the generated parquet payload).
   - Ensure authentication and role-based access checks (if applicable) are tested.

Write clean, highly structured pytest code utilizing fixtures. Include clean tear-downs to reset the database states and local temp files.
```

### Optimization Prompt
```markdown
Task: Optimize the performance, maintainability, and scalability of the `soc-service` microservice.

Areas of Optimization:
1. Database (MongoDB) Performance:
   - Review and implement the index design: Compound index on alerts for (severity, status) and (timestamp, status).
   - Optimize queries using project filters and pagination to minimize memory usage on large collections.
   - Enforce connection pooling configurations with PyMongo/Beanie, tuning `maxPoolSize`, `minPoolSize`, and `maxIdleTimeMS`.

2. Logging (Parquet Archiving) Pipeline:
   - Optimize memory consumption during the Parquet conversion. Instead of loading all buffered logs into memory at once, stream logs in chunks using `pyarrow.parquet.ParquetWriter`.
   - Implement snappy or zstd compression on the Parquet file to optimize GCS storage fees and network transfer times.
   - Use async background tasks (e.g., FastAPI's `BackgroundTasks` or Celery) so that log writing and GCS uploads do not block the active API request-response cycle.

3. Deployment & Cloud Resource Optimization:
   - GCP (Cloud Run): Configure CPU and memory limits. Setup concurrency settings to handle multiple simultaneous requests per container instance, minimizing cold starts.
   - Proxmox (LXC/VM): Design container configuration profiles with appropriate swap space limits, IO limits, and CPU weight parameters.
   - Implement health check endpoints (`/health` and `/ready`) that verify MongoDB and disk storage health for liveness/readiness probes in Proxmox / Google Cloud.

Analyze the microservice code to refactor any synchronous blocking calls to asynchronous alternatives (`async`/`await`). Provide clean, optimized refactoring blocks for index creation, background task logic, and async query executions.
```

---

## User Story 6: Cyber Incident Response Agent

**Summary**:
The goal of the Cyber Incident Response Agent is to fulfill the story requirements: \"As a proactive Cyber Incident Response Agent, I want to coordinate investigation, containment, eradication, and recovery activities so that security incidents are resolved quickly with minimal business impact.\". To achieve this, the microservice `incident-response-service` will expose several API endpoints using FastAPI, managing data across MongoDB collections like `incidents`, `forensic_logs`, `containment_actions`, `post_incident_reports`. Key functionality includes enforcing specific business constraints such as: Implement state machine for incident lifecycles (Declaration, Containment, Eradication, Recovery, Closed). Ensure forensic metadata has SHA256 file hashes to guarantee integrity. To ensure audit compliance and regulatory alignment, the microservice captures all decisions in high-performance local MongoDB collections and archives long-term logs to compressed Parquet files, which are securely uploaded to Google Cloud Storage. The microservice is designed for containerized deployment, running on GCP Cloud Run for cloud workflows or within Proxmox LXC containers for localized, secure production environments. Acceptance criteria dictate strict validation, verification checkpoints, and human-in-the-loop approvals for any critical or material actions.

### Implementation Prompt
```markdown
Task: Implement the `incident-response-service` microservice for the 'Cyber Incident Response Agent'.

Technology Stack:
- Python
- Modular Microservices Architecture
- FastAPI for the API layer
- MongoDB for the database layer (use PyMongo or Beanie ODM)
- Parquet for long-term log storage (using PyArrow/Pandas)
- Google Cloud (GCS/Cloud Run) for cloud deployment
- Proxmox VE for local virtualization/production deployment

Requirements:
1. Create a structured Python project with FastAPI for the `incident-response-service`:
   - `main.py` - FastAPI app initialization, routes registration, and exception handlers.
   - `config.py` - Pydantic settings loading MongoDB URI, GCP project details, Proxmox configs, and log paths.
   - `models/` - MongoDB schemas mapping the collections: `incidents`, `forensic_logs`, `containment_actions`, `post_incident_reports`.
   - `routers/` - Clean FastAPI router modules implementing:
          - POST /incidents/declare - Declare a confirmed incident and assign owner, severity, timeline, and response plan
     - POST /incidents/forensics - Log evidence collection and preservation metadata following forensic procedures
     - POST /incidents/containment - Propose containment recommendations (requires impact, confidence, and rollback options)
     - POST /incidents/containment/approve - Approve critical containment actions requiring human-in-the-loop validation
     - POST /incidents/recovery - Validate recovery status against technical and business criteria
     - POST /incidents/post-incident - Generate post-incident reports documenting cause, impact, lessons, and improvements
   - `services/` - Business logic implementation.
   - `utils/logging.py` - Custom logger logging events to MongoDB for active querying and periodically buffering/writing log events to local Parquet files, with automated upload to Google Cloud Storage.

2. Specific Business Logic:
   - Story: As a proactive Cyber Incident Response Agent, I want to coordinate investigation, containment, eradication, and recovery activities so that security incidents are resolved quickly with minimal business impact.
   - Custom implementation details: Implement state machine for incident lifecycles (Declaration, Containment, Eradication, Recovery, Closed). Ensure forensic metadata has SHA256 file hashes to guarantee integrity.

3. Parquet Logging Pipeline:
   - Configure a background task or worker that runs every hour or when logs reach 1000 records.
   - Buffer raw logs as standard dicts. Format into a Pandas DataFrame or PyArrow Table using a schema representing (timestamp, event_id, event_type, agent_identity, details_json, severity).
   - Write logs locally to a Parquet file (using Snappy compression).
   - Upload the resulting Parquet file to a Google Cloud Storage bucket (e.g., `gs://bank-audit-logs/incident-response-service/YYYY/MM/DD/`) using `google-cloud-storage`.
   - Setup fallback local directory in Proxmox VM storage if GCP is unreachable.

4. Deployment Configuration:
   - Write a `Dockerfile` multi-stage build optimizing dependency size and security (running as non-root user).
   - Write a Google Cloud Build configuration `cloudbuild.yaml` to build the container and deploy to Google Cloud Run with minimum/maximum instances.
   - Write a Proxmox deployment configuration template (e.g., an Ansible playbook or shell script using pct/qm commands) to deploy this microservice as an LXC container or VM.

Ensure the code is modular, fully typed with Python type hints, incorporates proper error handling with FastAPI HTTPExceptions, and includes clear docstrings. Do not use placeholders.
```

### Testing Prompt
```markdown
Task: Write automated tests (unit, integration, and end-to-end) for the `incident-response-service` microservice.

Technology Stack:
- Python (pytest, pytest-asyncio)
- FastAPI (TestClient, httpx.AsyncClient)
- MongoDB (using mongomock or testcontainers-mongodb)
- Parquet & GCS Mocking (using pandas, pyarrow, and mock/unittest.mock)

Testing Requirements:
1. Setup Unit Tests under `tests/unit/`:
   - Mock MongoDB connections and database calls using a fixture.
   - Mock Google Cloud Storage client library to verify GCS uploads.
   - Write unit tests for core helper functions, custom formulas, and validation logic: Implement state machine for incident lifecycles (Declaration, Containment, Eradication, Recovery, Closed). Ensure forensic metadata has SHA256 file hashes to guarantee integrity.
   - Verify that log archiving buffers logs correctly and generates a valid Parquet file (read the written file back using pyarrow/pandas and check the schemas match).

2. Setup Integration Tests under `tests/integration/`:
   - Use FastAPI `TestClient` or `httpx.AsyncClient` to call endpoints.
   - Test key routes:
          - POST /incidents/declare - Declare a confirmed incident and assign owner, severity, timeline, and response plan
     - POST /incidents/forensics - Log evidence collection and preservation metadata following forensic procedures
     - POST /incidents/containment - Propose containment recommendations (requires impact, confidence, and rollback options)
     - POST /incidents/containment/approve - Approve critical containment actions requiring human-in-the-loop validation
     - POST /incidents/recovery - Validate recovery status against technical and business criteria
     - POST /incidents/post-incident - Generate post-incident reports documenting cause, impact, lessons, and improvements
   - Verify the request validation (e.g. invalid schemas return 422 Unprocessable Entity).
   - Assert correct database records are inserted/updated in the mock MongoDB.
   - Test failure modes: database timeout, GCS upload failure (check that fallback local storage works).

3. Setup End-to-End Tests under `tests/e2e/`:
   - Test full workflows (e.g., trigger an action, verify the database state, trigger the log archiver, and check the generated parquet payload).
   - Ensure authentication and role-based access checks (if applicable) are tested.

Write clean, highly structured pytest code utilizing fixtures. Include clean tear-downs to reset the database states and local temp files.
```

### Optimization Prompt
```markdown
Task: Optimize the performance, maintainability, and scalability of the `incident-response-service` microservice.

Areas of Optimization:
1. Database (MongoDB) Performance:
   - Review and implement the index design: Index on incidents (severity, status, declared_at) and forensic_logs (incident_id, hash).
   - Optimize queries using project filters and pagination to minimize memory usage on large collections.
   - Enforce connection pooling configurations with PyMongo/Beanie, tuning `maxPoolSize`, `minPoolSize`, and `maxIdleTimeMS`.

2. Logging (Parquet Archiving) Pipeline:
   - Optimize memory consumption during the Parquet conversion. Instead of loading all buffered logs into memory at once, stream logs in chunks using `pyarrow.parquet.ParquetWriter`.
   - Implement snappy or zstd compression on the Parquet file to optimize GCS storage fees and network transfer times.
   - Use async background tasks (e.g., FastAPI's `BackgroundTasks` or Celery) so that log writing and GCS uploads do not block the active API request-response cycle.

3. Deployment & Cloud Resource Optimization:
   - GCP (Cloud Run): Configure CPU and memory limits. Setup concurrency settings to handle multiple simultaneous requests per container instance, minimizing cold starts.
   - Proxmox (LXC/VM): Design container configuration profiles with appropriate swap space limits, IO limits, and CPU weight parameters.
   - Implement health check endpoints (`/health` and `/ready`) that verify MongoDB and disk storage health for liveness/readiness probes in Proxmox / Google Cloud.

Analyze the microservice code to refactor any synchronous blocking calls to asynchronous alternatives (`async`/`await`). Provide clean, optimized refactoring blocks for index creation, background task logic, and async query executions.
```

---

## User Story 7: Cyber Threat Intelligence Agent

**Summary**:
The goal of the Cyber Threat Intelligence Agent is to fulfill the story requirements: \"As a proactive Cyber Threat Intelligence Agent, I want to collect, validate, analyse, and distribute relevant threat intelligence so that defensive controls anticipate threats targeting the bank.\". To achieve this, the microservice `threat-intelligence-service` will expose several API endpoints using FastAPI, managing data across MongoDB collections like `threat_feeds`, `indicators`, `mappings`, `distribution_logs`. Key functionality includes enforcing specific business constraints such as: Implement parser for STIX/TAXII. Build an indicators evaluation scoring model based on reliability and timelines. Enforce automatic expiry of IoCs. To ensure audit compliance and regulatory alignment, the microservice captures all decisions in high-performance local MongoDB collections and archives long-term logs to compressed Parquet files, which are securely uploaded to Google Cloud Storage. The microservice is designed for containerized deployment, running on GCP Cloud Run for cloud workflows or within Proxmox LXC containers for localized, secure production environments. Acceptance criteria dictate strict validation, verification checkpoints, and human-in-the-loop approvals for any critical or material actions.

### Implementation Prompt
```markdown
Task: Implement the `threat-intelligence-service` microservice for the 'Cyber Threat Intelligence Agent'.

Technology Stack:
- Python
- Modular Microservices Architecture
- FastAPI for the API layer
- MongoDB for the database layer (use PyMongo or Beanie ODM)
- Parquet for long-term log storage (using PyArrow/Pandas)
- Google Cloud (GCS/Cloud Run) for cloud deployment
- Proxmox VE for local virtualization/production deployment

Requirements:
1. Create a structured Python project with FastAPI for the `threat-intelligence-service`:
   - `main.py` - FastAPI app initialization, routes registration, and exception handlers.
   - `config.py` - Pydantic settings loading MongoDB URI, GCP project details, Proxmox configs, and log paths.
   - `models/` - MongoDB schemas mapping the collections: `threat_feeds`, `indicators`, `mappings`, `distribution_logs`.
   - `routers/` - Clean FastAPI router modules implementing:
          - POST /threat-intel/collect - Ingest cyber threat intelligence feeds (STIX/TAXII format)
     - POST /threat-intel/validate - Evaluate intelligence relevance, reliability, confidence, and timeliness
     - POST /threat-intel/map - Map validated threats to bank assets, vulnerabilities, and controls
     - POST /threat-intel/distribute - Distribute actionable Indicators of Compromise (IoCs) to detection platforms
     - DELETE /threat-intel/expire - Remove expired or disproven indicators within defined periods
     - GET /threat-intel/trace - Trace downstream actions back to their intelligence source
   - `services/` - Business logic implementation.
   - `utils/logging.py` - Custom logger logging events to MongoDB for active querying and periodically buffering/writing log events to local Parquet files, with automated upload to Google Cloud Storage.

2. Specific Business Logic:
   - Story: As a proactive Cyber Threat Intelligence Agent, I want to collect, validate, analyse, and distribute relevant threat intelligence so that defensive controls anticipate threats targeting the bank.
   - Custom implementation details: Implement parser for STIX/TAXII. Build an indicators evaluation scoring model based on reliability and timelines. Enforce automatic expiry of IoCs.

3. Parquet Logging Pipeline:
   - Configure a background task or worker that runs every hour or when logs reach 1000 records.
   - Buffer raw logs as standard dicts. Format into a Pandas DataFrame or PyArrow Table using a schema representing (timestamp, event_id, event_type, agent_identity, details_json, severity).
   - Write logs locally to a Parquet file (using Snappy compression).
   - Upload the resulting Parquet file to a Google Cloud Storage bucket (e.g., `gs://bank-audit-logs/threat-intelligence-service/YYYY/MM/DD/`) using `google-cloud-storage`.
   - Setup fallback local directory in Proxmox VM storage if GCP is unreachable.

4. Deployment Configuration:
   - Write a `Dockerfile` multi-stage build optimizing dependency size and security (running as non-root user).
   - Write a Google Cloud Build configuration `cloudbuild.yaml` to build the container and deploy to Google Cloud Run with minimum/maximum instances.
   - Write a Proxmox deployment configuration template (e.g., an Ansible playbook or shell script using pct/qm commands) to deploy this microservice as an LXC container or VM.

Ensure the code is modular, fully typed with Python type hints, incorporates proper error handling with FastAPI HTTPExceptions, and includes clear docstrings. Do not use placeholders.
```

### Testing Prompt
```markdown
Task: Write automated tests (unit, integration, and end-to-end) for the `threat-intelligence-service` microservice.

Technology Stack:
- Python (pytest, pytest-asyncio)
- FastAPI (TestClient, httpx.AsyncClient)
- MongoDB (using mongomock or testcontainers-mongodb)
- Parquet & GCS Mocking (using pandas, pyarrow, and mock/unittest.mock)

Testing Requirements:
1. Setup Unit Tests under `tests/unit/`:
   - Mock MongoDB connections and database calls using a fixture.
   - Mock Google Cloud Storage client library to verify GCS uploads.
   - Write unit tests for core helper functions, custom formulas, and validation logic: Implement parser for STIX/TAXII. Build an indicators evaluation scoring model based on reliability and timelines. Enforce automatic expiry of IoCs.
   - Verify that log archiving buffers logs correctly and generates a valid Parquet file (read the written file back using pyarrow/pandas and check the schemas match).

2. Setup Integration Tests under `tests/integration/`:
   - Use FastAPI `TestClient` or `httpx.AsyncClient` to call endpoints.
   - Test key routes:
          - POST /threat-intel/collect - Ingest cyber threat intelligence feeds (STIX/TAXII format)
     - POST /threat-intel/validate - Evaluate intelligence relevance, reliability, confidence, and timeliness
     - POST /threat-intel/map - Map validated threats to bank assets, vulnerabilities, and controls
     - POST /threat-intel/distribute - Distribute actionable Indicators of Compromise (IoCs) to detection platforms
     - DELETE /threat-intel/expire - Remove expired or disproven indicators within defined periods
     - GET /threat-intel/trace - Trace downstream actions back to their intelligence source
   - Verify the request validation (e.g. invalid schemas return 422 Unprocessable Entity).
   - Assert correct database records are inserted/updated in the mock MongoDB.
   - Test failure modes: database timeout, GCS upload failure (check that fallback local storage works).

3. Setup End-to-End Tests under `tests/e2e/`:
   - Test full workflows (e.g., trigger an action, verify the database state, trigger the log archiver, and check the generated parquet payload).
   - Ensure authentication and role-based access checks (if applicable) are tested.

Write clean, highly structured pytest code utilizing fixtures. Include clean tear-downs to reset the database states and local temp files.
```

### Optimization Prompt
```markdown
Task: Optimize the performance, maintainability, and scalability of the `threat-intelligence-service` microservice.

Areas of Optimization:
1. Database (MongoDB) Performance:
   - Review and implement the index design: Index on indicators (value, type) and (expiry_date, active).
   - Optimize queries using project filters and pagination to minimize memory usage on large collections.
   - Enforce connection pooling configurations with PyMongo/Beanie, tuning `maxPoolSize`, `minPoolSize`, and `maxIdleTimeMS`.

2. Logging (Parquet Archiving) Pipeline:
   - Optimize memory consumption during the Parquet conversion. Instead of loading all buffered logs into memory at once, stream logs in chunks using `pyarrow.parquet.ParquetWriter`.
   - Implement snappy or zstd compression on the Parquet file to optimize GCS storage fees and network transfer times.
   - Use async background tasks (e.g., FastAPI's `BackgroundTasks` or Celery) so that log writing and GCS uploads do not block the active API request-response cycle.

3. Deployment & Cloud Resource Optimization:
   - GCP (Cloud Run): Configure CPU and memory limits. Setup concurrency settings to handle multiple simultaneous requests per container instance, minimizing cold starts.
   - Proxmox (LXC/VM): Design container configuration profiles with appropriate swap space limits, IO limits, and CPU weight parameters.
   - Implement health check endpoints (`/health` and `/ready`) that verify MongoDB and disk storage health for liveness/readiness probes in Proxmox / Google Cloud.

Analyze the microservice code to refactor any synchronous blocking calls to asynchronous alternatives (`async`/`await`). Provide clean, optimized refactoring blocks for index creation, background task logic, and async query executions.
```

---

## User Story 8: Vulnerability and Exposure Management Agent

**Summary**:
The goal of the Vulnerability and Exposure Management Agent is to fulfill the story requirements: \"As a proactive Vulnerability and Exposure Management Agent, I want to discover, prioritise, assign, and validate security exposures so that exploitable weaknesses are remediated according to business risk.\". To achieve this, the microservice `vulnerability-management-service` will expose several API endpoints using FastAPI, managing data across MongoDB collections like `scans`, `findings`, `remediation_tasks`, `assets`. Key functionality includes enforcing specific business constraints such as: Implement deduplication algorithm (hashing vulnerability type + asset IP/ID). Calculate risk-based remediation deadlines (e.g., Critical = 14 days, High = 30 days) and trigger auto-escalation. To ensure audit compliance and regulatory alignment, the microservice captures all decisions in high-performance local MongoDB collections and archives long-term logs to compressed Parquet files, which are securely uploaded to Google Cloud Storage. The microservice is designed for containerized deployment, running on GCP Cloud Run for cloud workflows or within Proxmox LXC containers for localized, secure production environments. Acceptance criteria dictate strict validation, verification checkpoints, and human-in-the-loop approvals for any critical or material actions.

### Implementation Prompt
```markdown
Task: Implement the `vulnerability-management-service` microservice for the 'Vulnerability and Exposure Management Agent'.

Technology Stack:
- Python
- Modular Microservices Architecture
- FastAPI for the API layer
- MongoDB for the database layer (use PyMongo or Beanie ODM)
- Parquet for long-term log storage (using PyArrow/Pandas)
- Google Cloud (GCS/Cloud Run) for cloud deployment
- Proxmox VE for local virtualization/production deployment

Requirements:
1. Create a structured Python project with FastAPI for the `vulnerability-management-service`:
   - `main.py` - FastAPI app initialization, routes registration, and exception handlers.
   - `config.py` - Pydantic settings loading MongoDB URI, GCP project details, Proxmox configs, and log paths.
   - `models/` - MongoDB schemas mapping the collections: `scans`, `findings`, `remediation_tasks`, `assets`.
   - `routers/` - Clean FastAPI router modules implementing:
          - POST /assets/scan - Ingest scan results from asset scanners
     - POST /findings/deduplicate - Deduplicate findings and map to asset owners
     - POST /findings/prioritize - Score and prioritize findings based on severity, exploitability, threat activity, and business impact
     - POST /tasks/remediate - Create remediation tasks with owners and risk-based deadlines
     - POST /findings/validate - Validate closure of findings technically or log risk acceptance
   - `services/` - Business logic implementation.
   - `utils/logging.py` - Custom logger logging events to MongoDB for active querying and periodically buffering/writing log events to local Parquet files, with automated upload to Google Cloud Storage.

2. Specific Business Logic:
   - Story: As a proactive Vulnerability and Exposure Management Agent, I want to discover, prioritise, assign, and validate security exposures so that exploitable weaknesses are remediated according to business risk.
   - Custom implementation details: Implement deduplication algorithm (hashing vulnerability type + asset IP/ID). Calculate risk-based remediation deadlines (e.g., Critical = 14 days, High = 30 days) and trigger auto-escalation.

3. Parquet Logging Pipeline:
   - Configure a background task or worker that runs every hour or when logs reach 1000 records.
   - Buffer raw logs as standard dicts. Format into a Pandas DataFrame or PyArrow Table using a schema representing (timestamp, event_id, event_type, agent_identity, details_json, severity).
   - Write logs locally to a Parquet file (using Snappy compression).
   - Upload the resulting Parquet file to a Google Cloud Storage bucket (e.g., `gs://bank-audit-logs/vulnerability-management-service/YYYY/MM/DD/`) using `google-cloud-storage`.
   - Setup fallback local directory in Proxmox VM storage if GCP is unreachable.

4. Deployment Configuration:
   - Write a `Dockerfile` multi-stage build optimizing dependency size and security (running as non-root user).
   - Write a Google Cloud Build configuration `cloudbuild.yaml` to build the container and deploy to Google Cloud Run with minimum/maximum instances.
   - Write a Proxmox deployment configuration template (e.g., an Ansible playbook or shell script using pct/qm commands) to deploy this microservice as an LXC container or VM.

Ensure the code is modular, fully typed with Python type hints, incorporates proper error handling with FastAPI HTTPExceptions, and includes clear docstrings. Do not use placeholders.
```

### Testing Prompt
```markdown
Task: Write automated tests (unit, integration, and end-to-end) for the `vulnerability-management-service` microservice.

Technology Stack:
- Python (pytest, pytest-asyncio)
- FastAPI (TestClient, httpx.AsyncClient)
- MongoDB (using mongomock or testcontainers-mongodb)
- Parquet & GCS Mocking (using pandas, pyarrow, and mock/unittest.mock)

Testing Requirements:
1. Setup Unit Tests under `tests/unit/`:
   - Mock MongoDB connections and database calls using a fixture.
   - Mock Google Cloud Storage client library to verify GCS uploads.
   - Write unit tests for core helper functions, custom formulas, and validation logic: Implement deduplication algorithm (hashing vulnerability type + asset IP/ID). Calculate risk-based remediation deadlines (e.g., Critical = 14 days, High = 30 days) and trigger auto-escalation.
   - Verify that log archiving buffers logs correctly and generates a valid Parquet file (read the written file back using pyarrow/pandas and check the schemas match).

2. Setup Integration Tests under `tests/integration/`:
   - Use FastAPI `TestClient` or `httpx.AsyncClient` to call endpoints.
   - Test key routes:
          - POST /assets/scan - Ingest scan results from asset scanners
     - POST /findings/deduplicate - Deduplicate findings and map to asset owners
     - POST /findings/prioritize - Score and prioritize findings based on severity, exploitability, threat activity, and business impact
     - POST /tasks/remediate - Create remediation tasks with owners and risk-based deadlines
     - POST /findings/validate - Validate closure of findings technically or log risk acceptance
   - Verify the request validation (e.g. invalid schemas return 422 Unprocessable Entity).
   - Assert correct database records are inserted/updated in the mock MongoDB.
   - Test failure modes: database timeout, GCS upload failure (check that fallback local storage works).

3. Setup End-to-End Tests under `tests/e2e/`:
   - Test full workflows (e.g., trigger an action, verify the database state, trigger the log archiver, and check the generated parquet payload).
   - Ensure authentication and role-based access checks (if applicable) are tested.

Write clean, highly structured pytest code utilizing fixtures. Include clean tear-downs to reset the database states and local temp files.
```

### Optimization Prompt
```markdown
Task: Optimize the performance, maintainability, and scalability of the `vulnerability-management-service` microservice.

Areas of Optimization:
1. Database (MongoDB) Performance:
   - Review and implement the index design: Compound index on findings for (status, severity) and (asset_id, vulnerability_id).
   - Optimize queries using project filters and pagination to minimize memory usage on large collections.
   - Enforce connection pooling configurations with PyMongo/Beanie, tuning `maxPoolSize`, `minPoolSize`, and `maxIdleTimeMS`.

2. Logging (Parquet Archiving) Pipeline:
   - Optimize memory consumption during the Parquet conversion. Instead of loading all buffered logs into memory at once, stream logs in chunks using `pyarrow.parquet.ParquetWriter`.
   - Implement snappy or zstd compression on the Parquet file to optimize GCS storage fees and network transfer times.
   - Use async background tasks (e.g., FastAPI's `BackgroundTasks` or Celery) so that log writing and GCS uploads do not block the active API request-response cycle.

3. Deployment & Cloud Resource Optimization:
   - GCP (Cloud Run): Configure CPU and memory limits. Setup concurrency settings to handle multiple simultaneous requests per container instance, minimizing cold starts.
   - Proxmox (LXC/VM): Design container configuration profiles with appropriate swap space limits, IO limits, and CPU weight parameters.
   - Implement health check endpoints (`/health` and `/ready`) that verify MongoDB and disk storage health for liveness/readiness probes in Proxmox / Google Cloud.

Analyze the microservice code to refactor any synchronous blocking calls to asynchronous alternatives (`async`/`await`). Provide clean, optimized refactoring blocks for index creation, background task logic, and async query executions.
```

---

## User Story 9: Offensive Security and Security Testing Agent

**Summary**:
The goal of the Offensive Security and Security Testing Agent is to fulfill the story requirements: \"As a proactive Offensive Security and Security Testing Agent, I want to conduct authorised adversarial testing and control validation so that exploitable weaknesses are discovered before malicious actors can use them.\". To achieve this, the microservice `offensive-security-service` will expose several API endpoints using FastAPI, managing data across MongoDB collections like `test_schedules`, `adversarial_findings`, `test_reports`. Key functionality includes enforcing specific business constraints such as: Validate scope constraints against target environments before running any test. Implement safety stop-conditions monitoring that pauses tests if system performance degrades. To ensure audit compliance and regulatory alignment, the microservice captures all decisions in high-performance local MongoDB collections and archives long-term logs to compressed Parquet files, which are securely uploaded to Google Cloud Storage. The microservice is designed for containerized deployment, running on GCP Cloud Run for cloud workflows or within Proxmox LXC containers for localized, secure production environments. Acceptance criteria dictate strict validation, verification checkpoints, and human-in-the-loop approvals for any critical or material actions.

### Implementation Prompt
```markdown
Task: Implement the `offensive-security-service` microservice for the 'Offensive Security and Security Testing Agent'.

Technology Stack:
- Python
- Modular Microservices Architecture
- FastAPI for the API layer
- MongoDB for the database layer (use PyMongo or Beanie ODM)
- Parquet for long-term log storage (using PyArrow/Pandas)
- Google Cloud (GCS/Cloud Run) for cloud deployment
- Proxmox VE for local virtualization/production deployment

Requirements:
1. Create a structured Python project with FastAPI for the `offensive-security-service`:
   - `main.py` - FastAPI app initialization, routes registration, and exception handlers.
   - `config.py` - Pydantic settings loading MongoDB URI, GCP project details, Proxmox configs, and log paths.
   - `models/` - MongoDB schemas mapping the collections: `test_schedules`, `adversarial_findings`, `test_reports`.
   - `routers/` - Clean FastAPI router modules implementing:
          - POST /tests/schedule - Schedule adversarial test (requires scope, rules of engagement, timing, and stop conditions)
     - POST /tests/findings - Log high-risk findings immediately through secure channels
     - POST /tests/reports - Generate test reports with reproducible evidence, impact, likelihood, and remediation guidance
     - POST /tests/retest - Retest remediated findings to validate closure
   - `services/` - Business logic implementation.
   - `utils/logging.py` - Custom logger logging events to MongoDB for active querying and periodically buffering/writing log events to local Parquet files, with automated upload to Google Cloud Storage.

2. Specific Business Logic:
   - Story: As a proactive Offensive Security and Security Testing Agent, I want to conduct authorised adversarial testing and control validation so that exploitable weaknesses are discovered before malicious actors can use them.
   - Custom implementation details: Validate scope constraints against target environments before running any test. Implement safety stop-conditions monitoring that pauses tests if system performance degrades.

3. Parquet Logging Pipeline:
   - Configure a background task or worker that runs every hour or when logs reach 1000 records.
   - Buffer raw logs as standard dicts. Format into a Pandas DataFrame or PyArrow Table using a schema representing (timestamp, event_id, event_type, agent_identity, details_json, severity).
   - Write logs locally to a Parquet file (using Snappy compression).
   - Upload the resulting Parquet file to a Google Cloud Storage bucket (e.g., `gs://bank-audit-logs/offensive-security-service/YYYY/MM/DD/`) using `google-cloud-storage`.
   - Setup fallback local directory in Proxmox VM storage if GCP is unreachable.

4. Deployment Configuration:
   - Write a `Dockerfile` multi-stage build optimizing dependency size and security (running as non-root user).
   - Write a Google Cloud Build configuration `cloudbuild.yaml` to build the container and deploy to Google Cloud Run with minimum/maximum instances.
   - Write a Proxmox deployment configuration template (e.g., an Ansible playbook or shell script using pct/qm commands) to deploy this microservice as an LXC container or VM.

Ensure the code is modular, fully typed with Python type hints, incorporates proper error handling with FastAPI HTTPExceptions, and includes clear docstrings. Do not use placeholders.
```

### Testing Prompt
```markdown
Task: Write automated tests (unit, integration, and end-to-end) for the `offensive-security-service` microservice.

Technology Stack:
- Python (pytest, pytest-asyncio)
- FastAPI (TestClient, httpx.AsyncClient)
- MongoDB (using mongomock or testcontainers-mongodb)
- Parquet & GCS Mocking (using pandas, pyarrow, and mock/unittest.mock)

Testing Requirements:
1. Setup Unit Tests under `tests/unit/`:
   - Mock MongoDB connections and database calls using a fixture.
   - Mock Google Cloud Storage client library to verify GCS uploads.
   - Write unit tests for core helper functions, custom formulas, and validation logic: Validate scope constraints against target environments before running any test. Implement safety stop-conditions monitoring that pauses tests if system performance degrades.
   - Verify that log archiving buffers logs correctly and generates a valid Parquet file (read the written file back using pyarrow/pandas and check the schemas match).

2. Setup Integration Tests under `tests/integration/`:
   - Use FastAPI `TestClient` or `httpx.AsyncClient` to call endpoints.
   - Test key routes:
          - POST /tests/schedule - Schedule adversarial test (requires scope, rules of engagement, timing, and stop conditions)
     - POST /tests/findings - Log high-risk findings immediately through secure channels
     - POST /tests/reports - Generate test reports with reproducible evidence, impact, likelihood, and remediation guidance
     - POST /tests/retest - Retest remediated findings to validate closure
   - Verify the request validation (e.g. invalid schemas return 422 Unprocessable Entity).
   - Assert correct database records are inserted/updated in the mock MongoDB.
   - Test failure modes: database timeout, GCS upload failure (check that fallback local storage works).

3. Setup End-to-End Tests under `tests/e2e/`:
   - Test full workflows (e.g., trigger an action, verify the database state, trigger the log archiver, and check the generated parquet payload).
   - Ensure authentication and role-based access checks (if applicable) are tested.

Write clean, highly structured pytest code utilizing fixtures. Include clean tear-downs to reset the database states and local temp files.
```

### Optimization Prompt
```markdown
Task: Optimize the performance, maintainability, and scalability of the `offensive-security-service` microservice.

Areas of Optimization:
1. Database (MongoDB) Performance:
   - Review and implement the index design: Index on test_schedules (scheduled_time, status) and adversarial_findings (severity, status).
   - Optimize queries using project filters and pagination to minimize memory usage on large collections.
   - Enforce connection pooling configurations with PyMongo/Beanie, tuning `maxPoolSize`, `minPoolSize`, and `maxIdleTimeMS`.

2. Logging (Parquet Archiving) Pipeline:
   - Optimize memory consumption during the Parquet conversion. Instead of loading all buffered logs into memory at once, stream logs in chunks using `pyarrow.parquet.ParquetWriter`.
   - Implement snappy or zstd compression on the Parquet file to optimize GCS storage fees and network transfer times.
   - Use async background tasks (e.g., FastAPI's `BackgroundTasks` or Celery) so that log writing and GCS uploads do not block the active API request-response cycle.

3. Deployment & Cloud Resource Optimization:
   - GCP (Cloud Run): Configure CPU and memory limits. Setup concurrency settings to handle multiple simultaneous requests per container instance, minimizing cold starts.
   - Proxmox (LXC/VM): Design container configuration profiles with appropriate swap space limits, IO limits, and CPU weight parameters.
   - Implement health check endpoints (`/health` and `/ready`) that verify MongoDB and disk storage health for liveness/readiness probes in Proxmox / Google Cloud.

Analyze the microservice code to refactor any synchronous blocking calls to asynchronous alternatives (`async`/`await`). Provide clean, optimized refactoring blocks for index creation, background task logic, and async query executions.
```

---

## User Story 10: Application and Product Security Agent

**Summary**:
The goal of the Application and Product Security Agent is to fulfill the story requirements: \"As a proactive Application and Product Security Agent, I want to embed automated security assessment throughout software delivery so that applications and APIs meet security requirements before release.\". To achieve this, the microservice `appsec-service` will expose several API endpoints using FastAPI, managing data across MongoDB collections like `releases`, `scan_results`, `exceptions`, `gate_policies`. Key functionality includes enforcing specific business constraints such as: Implement policy engine that checks scan results for critical/high vulnerabilities and blocks releases. Maintain full trace of exceptions and false positives. To ensure audit compliance and regulatory alignment, the microservice captures all decisions in high-performance local MongoDB collections and archives long-term logs to compressed Parquet files, which are securely uploaded to Google Cloud Storage. The microservice is designed for containerized deployment, running on GCP Cloud Run for cloud workflows or within Proxmox LXC containers for localized, secure production environments. Acceptance criteria dictate strict validation, verification checkpoints, and human-in-the-loop approvals for any critical or material actions.

### Implementation Prompt
```markdown
Task: Implement the `appsec-service` microservice for the 'Application and Product Security Agent'.

Technology Stack:
- Python
- Modular Microservices Architecture
- FastAPI for the API layer
- MongoDB for the database layer (use PyMongo or Beanie ODM)
- Parquet for long-term log storage (using PyArrow/Pandas)
- Google Cloud (GCS/Cloud Run) for cloud deployment
- Proxmox VE for local virtualization/production deployment

Requirements:
1. Create a structured Python project with FastAPI for the `appsec-service`:
   - `main.py` - FastAPI app initialization, routes registration, and exception handlers.
   - `config.py` - Pydantic settings loading MongoDB URI, GCP project details, Proxmox configs, and log paths.
   - `models/` - MongoDB schemas mapping the collections: `releases`, `scan_results`, `exceptions`, `gate_policies`.
   - `routers/` - Clean FastAPI router modules implementing:
          - POST /releases/assess - Assess a software release (threat modeling and security testing results)
     - POST /scans/code - Assess code, dependencies, containers, and secrets against rules
     - POST /releases/gate - Evaluate security gate to decide if critical findings block or allow release
     - POST /exceptions/release - Document false positives and approved release exceptions
     - GET /metrics/delivery - Report security gate coverage, remediation time, and release decisions
   - `services/` - Business logic implementation.
   - `utils/logging.py` - Custom logger logging events to MongoDB for active querying and periodically buffering/writing log events to local Parquet files, with automated upload to Google Cloud Storage.

2. Specific Business Logic:
   - Story: As a proactive Application and Product Security Agent, I want to embed automated security assessment throughout software delivery so that applications and APIs meet security requirements before release.
   - Custom implementation details: Implement policy engine that checks scan results for critical/high vulnerabilities and blocks releases. Maintain full trace of exceptions and false positives.

3. Parquet Logging Pipeline:
   - Configure a background task or worker that runs every hour or when logs reach 1000 records.
   - Buffer raw logs as standard dicts. Format into a Pandas DataFrame or PyArrow Table using a schema representing (timestamp, event_id, event_type, agent_identity, details_json, severity).
   - Write logs locally to a Parquet file (using Snappy compression).
   - Upload the resulting Parquet file to a Google Cloud Storage bucket (e.g., `gs://bank-audit-logs/appsec-service/YYYY/MM/DD/`) using `google-cloud-storage`.
   - Setup fallback local directory in Proxmox VM storage if GCP is unreachable.

4. Deployment Configuration:
   - Write a `Dockerfile` multi-stage build optimizing dependency size and security (running as non-root user).
   - Write a Google Cloud Build configuration `cloudbuild.yaml` to build the container and deploy to Google Cloud Run with minimum/maximum instances.
   - Write a Proxmox deployment configuration template (e.g., an Ansible playbook or shell script using pct/qm commands) to deploy this microservice as an LXC container or VM.

Ensure the code is modular, fully typed with Python type hints, incorporates proper error handling with FastAPI HTTPExceptions, and includes clear docstrings. Do not use placeholders.
```

### Testing Prompt
```markdown
Task: Write automated tests (unit, integration, and end-to-end) for the `appsec-service` microservice.

Technology Stack:
- Python (pytest, pytest-asyncio)
- FastAPI (TestClient, httpx.AsyncClient)
- MongoDB (using mongomock or testcontainers-mongodb)
- Parquet & GCS Mocking (using pandas, pyarrow, and mock/unittest.mock)

Testing Requirements:
1. Setup Unit Tests under `tests/unit/`:
   - Mock MongoDB connections and database calls using a fixture.
   - Mock Google Cloud Storage client library to verify GCS uploads.
   - Write unit tests for core helper functions, custom formulas, and validation logic: Implement policy engine that checks scan results for critical/high vulnerabilities and blocks releases. Maintain full trace of exceptions and false positives.
   - Verify that log archiving buffers logs correctly and generates a valid Parquet file (read the written file back using pyarrow/pandas and check the schemas match).

2. Setup Integration Tests under `tests/integration/`:
   - Use FastAPI `TestClient` or `httpx.AsyncClient` to call endpoints.
   - Test key routes:
          - POST /releases/assess - Assess a software release (threat modeling and security testing results)
     - POST /scans/code - Assess code, dependencies, containers, and secrets against rules
     - POST /releases/gate - Evaluate security gate to decide if critical findings block or allow release
     - POST /exceptions/release - Document false positives and approved release exceptions
     - GET /metrics/delivery - Report security gate coverage, remediation time, and release decisions
   - Verify the request validation (e.g. invalid schemas return 422 Unprocessable Entity).
   - Assert correct database records are inserted/updated in the mock MongoDB.
   - Test failure modes: database timeout, GCS upload failure (check that fallback local storage works).

3. Setup End-to-End Tests under `tests/e2e/`:
   - Test full workflows (e.g., trigger an action, verify the database state, trigger the log archiver, and check the generated parquet payload).
   - Ensure authentication and role-based access checks (if applicable) are tested.

Write clean, highly structured pytest code utilizing fixtures. Include clean tear-downs to reset the database states and local temp files.
```

### Optimization Prompt
```markdown
Task: Optimize the performance, maintainability, and scalability of the `appsec-service` microservice.

Areas of Optimization:
1. Database (MongoDB) Performance:
   - Review and implement the index design: Index on releases (version, status) and scan_results (release_id, gate_passed).
   - Optimize queries using project filters and pagination to minimize memory usage on large collections.
   - Enforce connection pooling configurations with PyMongo/Beanie, tuning `maxPoolSize`, `minPoolSize`, and `maxIdleTimeMS`.

2. Logging (Parquet Archiving) Pipeline:
   - Optimize memory consumption during the Parquet conversion. Instead of loading all buffered logs into memory at once, stream logs in chunks using `pyarrow.parquet.ParquetWriter`.
   - Implement snappy or zstd compression on the Parquet file to optimize GCS storage fees and network transfer times.
   - Use async background tasks (e.g., FastAPI's `BackgroundTasks` or Celery) so that log writing and GCS uploads do not block the active API request-response cycle.

3. Deployment & Cloud Resource Optimization:
   - GCP (Cloud Run): Configure CPU and memory limits. Setup concurrency settings to handle multiple simultaneous requests per container instance, minimizing cold starts.
   - Proxmox (LXC/VM): Design container configuration profiles with appropriate swap space limits, IO limits, and CPU weight parameters.
   - Implement health check endpoints (`/health` and `/ready`) that verify MongoDB and disk storage health for liveness/readiness probes in Proxmox / Google Cloud.

Analyze the microservice code to refactor any synchronous blocking calls to asynchronous alternatives (`async`/`await`). Provide clean, optimized refactoring blocks for index creation, background task logic, and async query executions.
```

---

## User Story 11: Cloud and Container Security Agent

**Summary**:
The goal of the Cloud and Container Security Agent is to fulfill the story requirements: \"As a proactive Cloud and Container Security Agent, I want to enforce security guardrails and remediate cloud workload exposures so that cloud services remain secure and compliant throughout their lifecycle.\". To achieve this, the microservice `cloud-security-service` will expose several API endpoints using FastAPI, managing data across MongoDB collections like `cloud_inventory`, `violations`, `iac_assessments`, `posture_metrics`. Key functionality includes enforcing specific business constraints such as: Implement an IaC parser checking against OPA policies. Setup auto-remediation workflows for low-risk findings (e.g., closing open SSH ports on security groups) with automated rollback. To ensure audit compliance and regulatory alignment, the microservice captures all decisions in high-performance local MongoDB collections and archives long-term logs to compressed Parquet files, which are securely uploaded to Google Cloud Storage. The microservice is designed for containerized deployment, running on GCP Cloud Run for cloud workflows or within Proxmox LXC containers for localized, secure production environments. Acceptance criteria dictate strict validation, verification checkpoints, and human-in-the-loop approvals for any critical or material actions.

### Implementation Prompt
```markdown
Task: Implement the `cloud-security-service` microservice for the 'Cloud and Container Security Agent'.

Technology Stack:
- Python
- Modular Microservices Architecture
- FastAPI for the API layer
- MongoDB for the database layer (use PyMongo or Beanie ODM)
- Parquet for long-term log storage (using PyArrow/Pandas)
- Google Cloud (GCS/Cloud Run) for cloud deployment
- Proxmox VE for local virtualization/production deployment

Requirements:
1. Create a structured Python project with FastAPI for the `cloud-security-service`:
   - `main.py` - FastAPI app initialization, routes registration, and exception handlers.
   - `config.py` - Pydantic settings loading MongoDB URI, GCP project details, Proxmox configs, and log paths.
   - `models/` - MongoDB schemas mapping the collections: `cloud_inventory`, `violations`, `iac_assessments`, `posture_metrics`.
   - `routers/` - Clean FastAPI router modules implementing:
          - POST /cloud/inventory - Ingest and inventory cloud accounts, clusters, and workloads
     - POST /cloud/detect - Detect misconfigurations, excessive permissions, exposed services, and vulnerable workloads
     - POST /cloud/iac-assess - Assess Infrastructure-as-Code (Terraform/Helm) templates pre-deployment
     - POST /cloud/remediate - Auto-remediate low-risk violations and route material changes for approval
     - GET /cloud/posture - Retrieve cloud posture reporting highlighting gaps, trends, and owners
   - `services/` - Business logic implementation.
   - `utils/logging.py` - Custom logger logging events to MongoDB for active querying and periodically buffering/writing log events to local Parquet files, with automated upload to Google Cloud Storage.

2. Specific Business Logic:
   - Story: As a proactive Cloud and Container Security Agent, I want to enforce security guardrails and remediate cloud workload exposures so that cloud services remain secure and compliant throughout their lifecycle.
   - Custom implementation details: Implement an IaC parser checking against OPA policies. Setup auto-remediation workflows for low-risk findings (e.g., closing open SSH ports on security groups) with automated rollback.

3. Parquet Logging Pipeline:
   - Configure a background task or worker that runs every hour or when logs reach 1000 records.
   - Buffer raw logs as standard dicts. Format into a Pandas DataFrame or PyArrow Table using a schema representing (timestamp, event_id, event_type, agent_identity, details_json, severity).
   - Write logs locally to a Parquet file (using Snappy compression).
   - Upload the resulting Parquet file to a Google Cloud Storage bucket (e.g., `gs://bank-audit-logs/cloud-security-service/YYYY/MM/DD/`) using `google-cloud-storage`.
   - Setup fallback local directory in Proxmox VM storage if GCP is unreachable.

4. Deployment Configuration:
   - Write a `Dockerfile` multi-stage build optimizing dependency size and security (running as non-root user).
   - Write a Google Cloud Build configuration `cloudbuild.yaml` to build the container and deploy to Google Cloud Run with minimum/maximum instances.
   - Write a Proxmox deployment configuration template (e.g., an Ansible playbook or shell script using pct/qm commands) to deploy this microservice as an LXC container or VM.

Ensure the code is modular, fully typed with Python type hints, incorporates proper error handling with FastAPI HTTPExceptions, and includes clear docstrings. Do not use placeholders.
```

### Testing Prompt
```markdown
Task: Write automated tests (unit, integration, and end-to-end) for the `cloud-security-service` microservice.

Technology Stack:
- Python (pytest, pytest-asyncio)
- FastAPI (TestClient, httpx.AsyncClient)
- MongoDB (using mongomock or testcontainers-mongodb)
- Parquet & GCS Mocking (using pandas, pyarrow, and mock/unittest.mock)

Testing Requirements:
1. Setup Unit Tests under `tests/unit/`:
   - Mock MongoDB connections and database calls using a fixture.
   - Mock Google Cloud Storage client library to verify GCS uploads.
   - Write unit tests for core helper functions, custom formulas, and validation logic: Implement an IaC parser checking against OPA policies. Setup auto-remediation workflows for low-risk findings (e.g., closing open SSH ports on security groups) with automated rollback.
   - Verify that log archiving buffers logs correctly and generates a valid Parquet file (read the written file back using pyarrow/pandas and check the schemas match).

2. Setup Integration Tests under `tests/integration/`:
   - Use FastAPI `TestClient` or `httpx.AsyncClient` to call endpoints.
   - Test key routes:
          - POST /cloud/inventory - Ingest and inventory cloud accounts, clusters, and workloads
     - POST /cloud/detect - Detect misconfigurations, excessive permissions, exposed services, and vulnerable workloads
     - POST /cloud/iac-assess - Assess Infrastructure-as-Code (Terraform/Helm) templates pre-deployment
     - POST /cloud/remediate - Auto-remediate low-risk violations and route material changes for approval
     - GET /cloud/posture - Retrieve cloud posture reporting highlighting gaps, trends, and owners
   - Verify the request validation (e.g. invalid schemas return 422 Unprocessable Entity).
   - Assert correct database records are inserted/updated in the mock MongoDB.
   - Test failure modes: database timeout, GCS upload failure (check that fallback local storage works).

3. Setup End-to-End Tests under `tests/e2e/`:
   - Test full workflows (e.g., trigger an action, verify the database state, trigger the log archiver, and check the generated parquet payload).
   - Ensure authentication and role-based access checks (if applicable) are tested.

Write clean, highly structured pytest code utilizing fixtures. Include clean tear-downs to reset the database states and local temp files.
```

### Optimization Prompt
```markdown
Task: Optimize the performance, maintainability, and scalability of the `cloud-security-service` microservice.

Areas of Optimization:
1. Database (MongoDB) Performance:
   - Review and implement the index design: Compound index on violations for (status, severity) and (resource_id, rule_id).
   - Optimize queries using project filters and pagination to minimize memory usage on large collections.
   - Enforce connection pooling configurations with PyMongo/Beanie, tuning `maxPoolSize`, `minPoolSize`, and `maxIdleTimeMS`.

2. Logging (Parquet Archiving) Pipeline:
   - Optimize memory consumption during the Parquet conversion. Instead of loading all buffered logs into memory at once, stream logs in chunks using `pyarrow.parquet.ParquetWriter`.
   - Implement snappy or zstd compression on the Parquet file to optimize GCS storage fees and network transfer times.
   - Use async background tasks (e.g., FastAPI's `BackgroundTasks` or Celery) so that log writing and GCS uploads do not block the active API request-response cycle.

3. Deployment & Cloud Resource Optimization:
   - GCP (Cloud Run): Configure CPU and memory limits. Setup concurrency settings to handle multiple simultaneous requests per container instance, minimizing cold starts.
   - Proxmox (LXC/VM): Design container configuration profiles with appropriate swap space limits, IO limits, and CPU weight parameters.
   - Implement health check endpoints (`/health` and `/ready`) that verify MongoDB and disk storage health for liveness/readiness probes in Proxmox / Google Cloud.

Analyze the microservice code to refactor any synchronous blocking calls to asynchronous alternatives (`async`/`await`). Provide clean, optimized refactoring blocks for index creation, background task logic, and async query executions.
```

---

## User Story 12: Identity and Access Management Agent

**Summary**:
The goal of the Identity and Access Management Agent is to fulfill the story requirements: \"As a proactive Identity and Access Management Agent, I want to govern the identity lifecycle and enforce appropriate access so that users receive only the access required for authorised business purposes.\". To achieve this, the microservice `iam-service` will expose several API endpoints using FastAPI, managing data across MongoDB collections like `identities`, `access_rights`, `certifications`, `access_logs`. Key functionality includes enforcing specific business constraints such as: Implement least privilege role-mapping. Enforce workflow transitions for Joiners (auto-provision), Movers (re-evaluate roles), and Leavers (immediate auto-revoke). To ensure audit compliance and regulatory alignment, the microservice captures all decisions in high-performance local MongoDB collections and archives long-term logs to compressed Parquet files, which are securely uploaded to Google Cloud Storage. The microservice is designed for containerized deployment, running on GCP Cloud Run for cloud workflows or within Proxmox LXC containers for localized, secure production environments. Acceptance criteria dictate strict validation, verification checkpoints, and human-in-the-loop approvals for any critical or material actions.

### Implementation Prompt
```markdown
Task: Implement the `iam-service` microservice for the 'Identity and Access Management Agent'.

Technology Stack:
- Python
- Modular Microservices Architecture
- FastAPI for the API layer
- MongoDB for the database layer (use PyMongo or Beanie ODM)
- Parquet for long-term log storage (using PyArrow/Pandas)
- Google Cloud (GCS/Cloud Run) for cloud deployment
- Proxmox VE for local virtualization/production deployment

Requirements:
1. Create a structured Python project with FastAPI for the `iam-service`:
   - `main.py` - FastAPI app initialization, routes registration, and exception handlers.
   - `config.py` - Pydantic settings loading MongoDB URI, GCP project details, Proxmox configs, and log paths.
   - `models/` - MongoDB schemas mapping the collections: `identities`, `access_rights`, `certifications`, `access_logs`.
   - `routers/` - Clean FastAPI router modules implementing:
          - POST /identities/event - Process Joiner, Mover, and Leaver (JML) events
     - POST /access/request - Evaluate and provision access requests based on role and least privilege
     - POST /access/approve-high-risk - Route high-risk access requests for explicit owner approval
     - POST /access/certify - Run access certifications to find unused, excessive, or orphaned access
     - DELETE /access/revoke - Remove leaver and revoked access within service level targets
   - `services/` - Business logic implementation.
   - `utils/logging.py` - Custom logger logging events to MongoDB for active querying and periodically buffering/writing log events to local Parquet files, with automated upload to Google Cloud Storage.

2. Specific Business Logic:
   - Story: As a proactive Identity and Access Management Agent, I want to govern the identity lifecycle and enforce appropriate access so that users receive only the access required for authorised business purposes.
   - Custom implementation details: Implement least privilege role-mapping. Enforce workflow transitions for Joiners (auto-provision), Movers (re-evaluate roles), and Leavers (immediate auto-revoke).

3. Parquet Logging Pipeline:
   - Configure a background task or worker that runs every hour or when logs reach 1000 records.
   - Buffer raw logs as standard dicts. Format into a Pandas DataFrame or PyArrow Table using a schema representing (timestamp, event_id, event_type, agent_identity, details_json, severity).
   - Write logs locally to a Parquet file (using Snappy compression).
   - Upload the resulting Parquet file to a Google Cloud Storage bucket (e.g., `gs://bank-audit-logs/iam-service/YYYY/MM/DD/`) using `google-cloud-storage`.
   - Setup fallback local directory in Proxmox VM storage if GCP is unreachable.

4. Deployment Configuration:
   - Write a `Dockerfile` multi-stage build optimizing dependency size and security (running as non-root user).
   - Write a Google Cloud Build configuration `cloudbuild.yaml` to build the container and deploy to Google Cloud Run with minimum/maximum instances.
   - Write a Proxmox deployment configuration template (e.g., an Ansible playbook or shell script using pct/qm commands) to deploy this microservice as an LXC container or VM.

Ensure the code is modular, fully typed with Python type hints, incorporates proper error handling with FastAPI HTTPExceptions, and includes clear docstrings. Do not use placeholders.
```

### Testing Prompt
```markdown
Task: Write automated tests (unit, integration, and end-to-end) for the `iam-service` microservice.

Technology Stack:
- Python (pytest, pytest-asyncio)
- FastAPI (TestClient, httpx.AsyncClient)
- MongoDB (using mongomock or testcontainers-mongodb)
- Parquet & GCS Mocking (using pandas, pyarrow, and mock/unittest.mock)

Testing Requirements:
1. Setup Unit Tests under `tests/unit/`:
   - Mock MongoDB connections and database calls using a fixture.
   - Mock Google Cloud Storage client library to verify GCS uploads.
   - Write unit tests for core helper functions, custom formulas, and validation logic: Implement least privilege role-mapping. Enforce workflow transitions for Joiners (auto-provision), Movers (re-evaluate roles), and Leavers (immediate auto-revoke).
   - Verify that log archiving buffers logs correctly and generates a valid Parquet file (read the written file back using pyarrow/pandas and check the schemas match).

2. Setup Integration Tests under `tests/integration/`:
   - Use FastAPI `TestClient` or `httpx.AsyncClient` to call endpoints.
   - Test key routes:
          - POST /identities/event - Process Joiner, Mover, and Leaver (JML) events
     - POST /access/request - Evaluate and provision access requests based on role and least privilege
     - POST /access/approve-high-risk - Route high-risk access requests for explicit owner approval
     - POST /access/certify - Run access certifications to find unused, excessive, or orphaned access
     - DELETE /access/revoke - Remove leaver and revoked access within service level targets
   - Verify the request validation (e.g. invalid schemas return 422 Unprocessable Entity).
   - Assert correct database records are inserted/updated in the mock MongoDB.
   - Test failure modes: database timeout, GCS upload failure (check that fallback local storage works).

3. Setup End-to-End Tests under `tests/e2e/`:
   - Test full workflows (e.g., trigger an action, verify the database state, trigger the log archiver, and check the generated parquet payload).
   - Ensure authentication and role-based access checks (if applicable) are tested.

Write clean, highly structured pytest code utilizing fixtures. Include clean tear-downs to reset the database states and local temp files.
```

### Optimization Prompt
```markdown
Task: Optimize the performance, maintainability, and scalability of the `iam-service` microservice.

Areas of Optimization:
1. Database (MongoDB) Performance:
   - Review and implement the index design: Index on identities (employee_id, status) and access_rights (identity_id, role, status).
   - Optimize queries using project filters and pagination to minimize memory usage on large collections.
   - Enforce connection pooling configurations with PyMongo/Beanie, tuning `maxPoolSize`, `minPoolSize`, and `maxIdleTimeMS`.

2. Logging (Parquet Archiving) Pipeline:
   - Optimize memory consumption during the Parquet conversion. Instead of loading all buffered logs into memory at once, stream logs in chunks using `pyarrow.parquet.ParquetWriter`.
   - Implement snappy or zstd compression on the Parquet file to optimize GCS storage fees and network transfer times.
   - Use async background tasks (e.g., FastAPI's `BackgroundTasks` or Celery) so that log writing and GCS uploads do not block the active API request-response cycle.

3. Deployment & Cloud Resource Optimization:
   - GCP (Cloud Run): Configure CPU and memory limits. Setup concurrency settings to handle multiple simultaneous requests per container instance, minimizing cold starts.
   - Proxmox (LXC/VM): Design container configuration profiles with appropriate swap space limits, IO limits, and CPU weight parameters.
   - Implement health check endpoints (`/health` and `/ready`) that verify MongoDB and disk storage health for liveness/readiness probes in Proxmox / Google Cloud.

Analyze the microservice code to refactor any synchronous blocking calls to asynchronous alternatives (`async`/`await`). Provide clean, optimized refactoring blocks for index creation, background task logic, and async query executions.
```

---

## User Story 13: Privileged Access Management Agent

**Summary**:
The goal of the Privileged Access Management Agent is to fulfill the story requirements: \"As a proactive Privileged Access Management Agent, I want to control, monitor, and revoke privileged access dynamically so that administrative capabilities cannot be misused or retained unnecessarily.\". To achieve this, the microservice `pam-service` will expose several API endpoints using FastAPI, managing data across MongoDB collections like `privileged_accounts`, `access_sessions`, `rotation_logs`, `emergency_logs`. Key functionality includes enforcing specific business constraints such as: Enforce strong authentication checks. Implement time-to-live (TTL) timers on active sessions, auto-revoking access when the session expires. Vault key materials securely. To ensure audit compliance and regulatory alignment, the microservice captures all decisions in high-performance local MongoDB collections and archives long-term logs to compressed Parquet files, which are securely uploaded to Google Cloud Storage. The microservice is designed for containerized deployment, running on GCP Cloud Run for cloud workflows or within Proxmox LXC containers for localized, secure production environments. Acceptance criteria dictate strict validation, verification checkpoints, and human-in-the-loop approvals for any critical or material actions.

### Implementation Prompt
```markdown
Task: Implement the `pam-service` microservice for the 'Privileged Access Management Agent'.

Technology Stack:
- Python
- Modular Microservices Architecture
- FastAPI for the API layer
- MongoDB for the database layer (use PyMongo or Beanie ODM)
- Parquet for long-term log storage (using PyArrow/Pandas)
- Google Cloud (GCS/Cloud Run) for cloud deployment
- Proxmox VE for local virtualization/production deployment

Requirements:
1. Create a structured Python project with FastAPI for the `pam-service`:
   - `main.py` - FastAPI app initialization, routes registration, and exception handlers.
   - `config.py` - Pydantic settings loading MongoDB URI, GCP project details, Proxmox configs, and log paths.
   - `models/` - MongoDB schemas mapping the collections: `privileged_accounts`, `access_sessions`, `rotation_logs`, `emergency_logs`.
   - `routers/` - Clean FastAPI router modules implementing:
          - POST /pam/accounts - Discover and inventory privileged accounts and credentials
     - POST /pam/request - Request time-bound, purpose-specific privileged access (requires strong auth)
     - POST /pam/rotate - Vault and rotate privileged credentials according to policy
     - POST /pam/sessions/record - Record and monitor active privileged sessions
     - POST /pam/sessions/revoke - Suspend/revoke suspicious or expired privileged access dynamically
     - POST /pam/emergency/review - Log and review post-use emergency (break-glass) access
   - `services/` - Business logic implementation.
   - `utils/logging.py` - Custom logger logging events to MongoDB for active querying and periodically buffering/writing log events to local Parquet files, with automated upload to Google Cloud Storage.

2. Specific Business Logic:
   - Story: As a proactive Privileged Access Management Agent, I want to control, monitor, and revoke privileged access dynamically so that administrative capabilities cannot be misused or retained unnecessarily.
   - Custom implementation details: Enforce strong authentication checks. Implement time-to-live (TTL) timers on active sessions, auto-revoking access when the session expires. Vault key materials securely.

3. Parquet Logging Pipeline:
   - Configure a background task or worker that runs every hour or when logs reach 1000 records.
   - Buffer raw logs as standard dicts. Format into a Pandas DataFrame or PyArrow Table using a schema representing (timestamp, event_id, event_type, agent_identity, details_json, severity).
   - Write logs locally to a Parquet file (using Snappy compression).
   - Upload the resulting Parquet file to a Google Cloud Storage bucket (e.g., `gs://bank-audit-logs/pam-service/YYYY/MM/DD/`) using `google-cloud-storage`.
   - Setup fallback local directory in Proxmox VM storage if GCP is unreachable.

4. Deployment Configuration:
   - Write a `Dockerfile` multi-stage build optimizing dependency size and security (running as non-root user).
   - Write a Google Cloud Build configuration `cloudbuild.yaml` to build the container and deploy to Google Cloud Run with minimum/maximum instances.
   - Write a Proxmox deployment configuration template (e.g., an Ansible playbook or shell script using pct/qm commands) to deploy this microservice as an LXC container or VM.

Ensure the code is modular, fully typed with Python type hints, incorporates proper error handling with FastAPI HTTPExceptions, and includes clear docstrings. Do not use placeholders.
```

### Testing Prompt
```markdown
Task: Write automated tests (unit, integration, and end-to-end) for the `pam-service` microservice.

Technology Stack:
- Python (pytest, pytest-asyncio)
- FastAPI (TestClient, httpx.AsyncClient)
- MongoDB (using mongomock or testcontainers-mongodb)
- Parquet & GCS Mocking (using pandas, pyarrow, and mock/unittest.mock)

Testing Requirements:
1. Setup Unit Tests under `tests/unit/`:
   - Mock MongoDB connections and database calls using a fixture.
   - Mock Google Cloud Storage client library to verify GCS uploads.
   - Write unit tests for core helper functions, custom formulas, and validation logic: Enforce strong authentication checks. Implement time-to-live (TTL) timers on active sessions, auto-revoking access when the session expires. Vault key materials securely.
   - Verify that log archiving buffers logs correctly and generates a valid Parquet file (read the written file back using pyarrow/pandas and check the schemas match).

2. Setup Integration Tests under `tests/integration/`:
   - Use FastAPI `TestClient` or `httpx.AsyncClient` to call endpoints.
   - Test key routes:
          - POST /pam/accounts - Discover and inventory privileged accounts and credentials
     - POST /pam/request - Request time-bound, purpose-specific privileged access (requires strong auth)
     - POST /pam/rotate - Vault and rotate privileged credentials according to policy
     - POST /pam/sessions/record - Record and monitor active privileged sessions
     - POST /pam/sessions/revoke - Suspend/revoke suspicious or expired privileged access dynamically
     - POST /pam/emergency/review - Log and review post-use emergency (break-glass) access
   - Verify the request validation (e.g. invalid schemas return 422 Unprocessable Entity).
   - Assert correct database records are inserted/updated in the mock MongoDB.
   - Test failure modes: database timeout, GCS upload failure (check that fallback local storage works).

3. Setup End-to-End Tests under `tests/e2e/`:
   - Test full workflows (e.g., trigger an action, verify the database state, trigger the log archiver, and check the generated parquet payload).
   - Ensure authentication and role-based access checks (if applicable) are tested.

Write clean, highly structured pytest code utilizing fixtures. Include clean tear-downs to reset the database states and local temp files.
```

### Optimization Prompt
```markdown
Task: Optimize the performance, maintainability, and scalability of the `pam-service` microservice.

Areas of Optimization:
1. Database (MongoDB) Performance:
   - Review and implement the index design: Compound index on access_sessions for (status, expires_at) and (account_id, active).
   - Optimize queries using project filters and pagination to minimize memory usage on large collections.
   - Enforce connection pooling configurations with PyMongo/Beanie, tuning `maxPoolSize`, `minPoolSize`, and `maxIdleTimeMS`.

2. Logging (Parquet Archiving) Pipeline:
   - Optimize memory consumption during the Parquet conversion. Instead of loading all buffered logs into memory at once, stream logs in chunks using `pyarrow.parquet.ParquetWriter`.
   - Implement snappy or zstd compression on the Parquet file to optimize GCS storage fees and network transfer times.
   - Use async background tasks (e.g., FastAPI's `BackgroundTasks` or Celery) so that log writing and GCS uploads do not block the active API request-response cycle.

3. Deployment & Cloud Resource Optimization:
   - GCP (Cloud Run): Configure CPU and memory limits. Setup concurrency settings to handle multiple simultaneous requests per container instance, minimizing cold starts.
   - Proxmox (LXC/VM): Design container configuration profiles with appropriate swap space limits, IO limits, and CPU weight parameters.
   - Implement health check endpoints (`/health` and `/ready`) that verify MongoDB and disk storage health for liveness/readiness probes in Proxmox / Google Cloud.

Analyze the microservice code to refactor any synchronous blocking calls to asynchronous alternatives (`async`/`await`). Provide clean, optimized refactoring blocks for index creation, background task logic, and async query executions.
```

---

## User Story 14: Data Security and Information Protection Agent

**Summary**:
The goal of the Data Security and Information Protection Agent is to fulfill the story requirements: \"As a proactive Data Security and Information Protection Agent, I want to discover, classify, monitor, and protect sensitive information so that unauthorised disclosure, alteration, and loss are prevented.\". To achieve this, the microservice `data-protection-service` will expose several API endpoints using FastAPI, managing data across MongoDB collections like `repositories`, `classifications`, `leakage_cases`, `handling_controls`. Key functionality includes enforcing specific business constraints such as: Implement classification engine scanning files/DB schemas for PII, PAN, PCI data. Build DLP rules matching classification with permissible egress zones. Block egress dynamically on high-confidence violations. To ensure audit compliance and regulatory alignment, the microservice captures all decisions in high-performance local MongoDB collections and archives long-term logs to compressed Parquet files, which are securely uploaded to Google Cloud Storage. The microservice is designed for containerized deployment, running on GCP Cloud Run for cloud workflows or within Proxmox LXC containers for localized, secure production environments. Acceptance criteria dictate strict validation, verification checkpoints, and human-in-the-loop approvals for any critical or material actions.

### Implementation Prompt
```markdown
Task: Implement the `data-protection-service` microservice for the 'Data Security and Information Protection Agent'.

Technology Stack:
- Python
- Modular Microservices Architecture
- FastAPI for the API layer
- MongoDB for the database layer (use PyMongo or Beanie ODM)
- Parquet for long-term log storage (using PyArrow/Pandas)
- Google Cloud (GCS/Cloud Run) for cloud deployment
- Proxmox VE for local virtualization/production deployment

Requirements:
1. Create a structured Python project with FastAPI for the `data-protection-service`:
   - `main.py` - FastAPI app initialization, routes registration, and exception handlers.
   - `config.py` - Pydantic settings loading MongoDB URI, GCP project details, Proxmox configs, and log paths.
   - `models/` - MongoDB schemas mapping the collections: `repositories`, `classifications`, `leakage_cases`, `handling_controls`.
   - `routers/` - Clean FastAPI router modules implementing:
          - POST /data/repositories - Discover and classify in-scope data repositories
     - POST /data/controls - Apply and verify handling controls aligned with classification, location, and regulatory rules
     - POST /data/leakage/investigate - Investigate suspected data leakage incidents
     - POST /data/leakage/remediate - Initiate high-confidence protective actions (e.g. blocking data egress)
     - GET /data/metrics - Retrieve data protection metrics (classification coverage, violations, remediation)
   - `services/` - Business logic implementation.
   - `utils/logging.py` - Custom logger logging events to MongoDB for active querying and periodically buffering/writing log events to local Parquet files, with automated upload to Google Cloud Storage.

2. Specific Business Logic:
   - Story: As a proactive Data Security and Information Protection Agent, I want to discover, classify, monitor, and protect sensitive information so that unauthorised disclosure, alteration, and loss are prevented.
   - Custom implementation details: Implement classification engine scanning files/DB schemas for PII, PAN, PCI data. Build DLP rules matching classification with permissible egress zones. Block egress dynamically on high-confidence violations.

3. Parquet Logging Pipeline:
   - Configure a background task or worker that runs every hour or when logs reach 1000 records.
   - Buffer raw logs as standard dicts. Format into a Pandas DataFrame or PyArrow Table using a schema representing (timestamp, event_id, event_type, agent_identity, details_json, severity).
   - Write logs locally to a Parquet file (using Snappy compression).
   - Upload the resulting Parquet file to a Google Cloud Storage bucket (e.g., `gs://bank-audit-logs/data-protection-service/YYYY/MM/DD/`) using `google-cloud-storage`.
   - Setup fallback local directory in Proxmox VM storage if GCP is unreachable.

4. Deployment Configuration:
   - Write a `Dockerfile` multi-stage build optimizing dependency size and security (running as non-root user).
   - Write a Google Cloud Build configuration `cloudbuild.yaml` to build the container and deploy to Google Cloud Run with minimum/maximum instances.
   - Write a Proxmox deployment configuration template (e.g., an Ansible playbook or shell script using pct/qm commands) to deploy this microservice as an LXC container or VM.

Ensure the code is modular, fully typed with Python type hints, incorporates proper error handling with FastAPI HTTPExceptions, and includes clear docstrings. Do not use placeholders.
```

### Testing Prompt
```markdown
Task: Write automated tests (unit, integration, and end-to-end) for the `data-protection-service` microservice.

Technology Stack:
- Python (pytest, pytest-asyncio)
- FastAPI (TestClient, httpx.AsyncClient)
- MongoDB (using mongomock or testcontainers-mongodb)
- Parquet & GCS Mocking (using pandas, pyarrow, and mock/unittest.mock)

Testing Requirements:
1. Setup Unit Tests under `tests/unit/`:
   - Mock MongoDB connections and database calls using a fixture.
   - Mock Google Cloud Storage client library to verify GCS uploads.
   - Write unit tests for core helper functions, custom formulas, and validation logic: Implement classification engine scanning files/DB schemas for PII, PAN, PCI data. Build DLP rules matching classification with permissible egress zones. Block egress dynamically on high-confidence violations.
   - Verify that log archiving buffers logs correctly and generates a valid Parquet file (read the written file back using pyarrow/pandas and check the schemas match).

2. Setup Integration Tests under `tests/integration/`:
   - Use FastAPI `TestClient` or `httpx.AsyncClient` to call endpoints.
   - Test key routes:
          - POST /data/repositories - Discover and classify in-scope data repositories
     - POST /data/controls - Apply and verify handling controls aligned with classification, location, and regulatory rules
     - POST /data/leakage/investigate - Investigate suspected data leakage incidents
     - POST /data/leakage/remediate - Initiate high-confidence protective actions (e.g. blocking data egress)
     - GET /data/metrics - Retrieve data protection metrics (classification coverage, violations, remediation)
   - Verify the request validation (e.g. invalid schemas return 422 Unprocessable Entity).
   - Assert correct database records are inserted/updated in the mock MongoDB.
   - Test failure modes: database timeout, GCS upload failure (check that fallback local storage works).

3. Setup End-to-End Tests under `tests/e2e/`:
   - Test full workflows (e.g., trigger an action, verify the database state, trigger the log archiver, and check the generated parquet payload).
   - Ensure authentication and role-based access checks (if applicable) are tested.

Write clean, highly structured pytest code utilizing fixtures. Include clean tear-downs to reset the database states and local temp files.
```

### Optimization Prompt
```markdown
Task: Optimize the performance, maintainability, and scalability of the `data-protection-service` microservice.

Areas of Optimization:
1. Database (MongoDB) Performance:
   - Review and implement the index design: Index on repositories (uri, classification) and leakage_cases (severity, status).
   - Optimize queries using project filters and pagination to minimize memory usage on large collections.
   - Enforce connection pooling configurations with PyMongo/Beanie, tuning `maxPoolSize`, `minPoolSize`, and `maxIdleTimeMS`.

2. Logging (Parquet Archiving) Pipeline:
   - Optimize memory consumption during the Parquet conversion. Instead of loading all buffered logs into memory at once, stream logs in chunks using `pyarrow.parquet.ParquetWriter`.
   - Implement snappy or zstd compression on the Parquet file to optimize GCS storage fees and network transfer times.
   - Use async background tasks (e.g., FastAPI's `BackgroundTasks` or Celery) so that log writing and GCS uploads do not block the active API request-response cycle.

3. Deployment & Cloud Resource Optimization:
   - GCP (Cloud Run): Configure CPU and memory limits. Setup concurrency settings to handle multiple simultaneous requests per container instance, minimizing cold starts.
   - Proxmox (LXC/VM): Design container configuration profiles with appropriate swap space limits, IO limits, and CPU weight parameters.
   - Implement health check endpoints (`/health` and `/ready`) that verify MongoDB and disk storage health for liveness/readiness probes in Proxmox / Google Cloud.

Analyze the microservice code to refactor any synchronous blocking calls to asynchronous alternatives (`async`/`await`). Provide clean, optimized refactoring blocks for index creation, background task logic, and async query executions.
```

---

## User Story 15: Cryptography and Key Management Agent

**Summary**:
The goal of the Cryptography and Key Management Agent is to fulfill the story requirements: \"As a proactive Cryptography and Key Management Agent, I want to govern cryptographic assets and automate their secure lifecycle so that sensitive information and transactions remain protected.\". To achieve this, the microservice `cryptography-service` will expose several API endpoints using FastAPI, managing data across MongoDB collections like `crypto_assets`, `lifecycle_actions`, `escalations`, `agility_plans`. Key functionality includes enforcing specific business constraints such as: Implement key and certificate scanner. Auto-rotate TLS certificates using ACME protocols or key vault APIs. Never log private keys or passphrases; redact them in logging filters. To ensure audit compliance and regulatory alignment, the microservice captures all decisions in high-performance local MongoDB collections and archives long-term logs to compressed Parquet files, which are securely uploaded to Google Cloud Storage. The microservice is designed for containerized deployment, running on GCP Cloud Run for cloud workflows or within Proxmox LXC containers for localized, secure production environments. Acceptance criteria dictate strict validation, verification checkpoints, and human-in-the-loop approvals for any critical or material actions.

### Implementation Prompt
```markdown
Task: Implement the `cryptography-service` microservice for the 'Cryptography and Key Management Agent'.

Technology Stack:
- Python
- Modular Microservices Architecture
- FastAPI for the API layer
- MongoDB for the database layer (use PyMongo or Beanie ODM)
- Parquet for long-term log storage (using PyArrow/Pandas)
- Google Cloud (GCS/Cloud Run) for cloud deployment
- Proxmox VE for local virtualization/production deployment

Requirements:
1. Create a structured Python project with FastAPI for the `cryptography-service`:
   - `main.py` - FastAPI app initialization, routes registration, and exception handlers.
   - `config.py` - Pydantic settings loading MongoDB URI, GCP project details, Proxmox configs, and log paths.
   - `models/` - MongoDB schemas mapping the collections: `crypto_assets`, `lifecycle_actions`, `escalations`, `agility_plans`.
   - `routers/` - Clean FastAPI router modules implementing:
          - POST /crypto/inventory - Inventory cryptographic keys, certificates, algorithms, and dependencies
     - GET /crypto/weak - Detect weak, expired, unapproved, or soon-to-expire cryptographic assets
     - POST /crypto/lifecycle - Issue, rotate, revoke, or destroy certificates and keys according to policy
     - POST /crypto/escalate - Escalate critical expiry risks before service impact
     - POST /crypto/agility - Generate cryptographic-agility plans to address deprecated algorithms
   - `services/` - Business logic implementation.
   - `utils/logging.py` - Custom logger logging events to MongoDB for active querying and periodically buffering/writing log events to local Parquet files, with automated upload to Google Cloud Storage.

2. Specific Business Logic:
   - Story: As a proactive Cryptography and Key Management Agent, I want to govern cryptographic assets and automate their secure lifecycle so that sensitive information and transactions remain protected.
   - Custom implementation details: Implement key and certificate scanner. Auto-rotate TLS certificates using ACME protocols or key vault APIs. Never log private keys or passphrases; redact them in logging filters.

3. Parquet Logging Pipeline:
   - Configure a background task or worker that runs every hour or when logs reach 1000 records.
   - Buffer raw logs as standard dicts. Format into a Pandas DataFrame or PyArrow Table using a schema representing (timestamp, event_id, event_type, agent_identity, details_json, severity).
   - Write logs locally to a Parquet file (using Snappy compression).
   - Upload the resulting Parquet file to a Google Cloud Storage bucket (e.g., `gs://bank-audit-logs/cryptography-service/YYYY/MM/DD/`) using `google-cloud-storage`.
   - Setup fallback local directory in Proxmox VM storage if GCP is unreachable.

4. Deployment Configuration:
   - Write a `Dockerfile` multi-stage build optimizing dependency size and security (running as non-root user).
   - Write a Google Cloud Build configuration `cloudbuild.yaml` to build the container and deploy to Google Cloud Run with minimum/maximum instances.
   - Write a Proxmox deployment configuration template (e.g., an Ansible playbook or shell script using pct/qm commands) to deploy this microservice as an LXC container or VM.

Ensure the code is modular, fully typed with Python type hints, incorporates proper error handling with FastAPI HTTPExceptions, and includes clear docstrings. Do not use placeholders.
```

### Testing Prompt
```markdown
Task: Write automated tests (unit, integration, and end-to-end) for the `cryptography-service` microservice.

Technology Stack:
- Python (pytest, pytest-asyncio)
- FastAPI (TestClient, httpx.AsyncClient)
- MongoDB (using mongomock or testcontainers-mongodb)
- Parquet & GCS Mocking (using pandas, pyarrow, and mock/unittest.mock)

Testing Requirements:
1. Setup Unit Tests under `tests/unit/`:
   - Mock MongoDB connections and database calls using a fixture.
   - Mock Google Cloud Storage client library to verify GCS uploads.
   - Write unit tests for core helper functions, custom formulas, and validation logic: Implement key and certificate scanner. Auto-rotate TLS certificates using ACME protocols or key vault APIs. Never log private keys or passphrases; redact them in logging filters.
   - Verify that log archiving buffers logs correctly and generates a valid Parquet file (read the written file back using pyarrow/pandas and check the schemas match).

2. Setup Integration Tests under `tests/integration/`:
   - Use FastAPI `TestClient` or `httpx.AsyncClient` to call endpoints.
   - Test key routes:
          - POST /crypto/inventory - Inventory cryptographic keys, certificates, algorithms, and dependencies
     - GET /crypto/weak - Detect weak, expired, unapproved, or soon-to-expire cryptographic assets
     - POST /crypto/lifecycle - Issue, rotate, revoke, or destroy certificates and keys according to policy
     - POST /crypto/escalate - Escalate critical expiry risks before service impact
     - POST /crypto/agility - Generate cryptographic-agility plans to address deprecated algorithms
   - Verify the request validation (e.g. invalid schemas return 422 Unprocessable Entity).
   - Assert correct database records are inserted/updated in the mock MongoDB.
   - Test failure modes: database timeout, GCS upload failure (check that fallback local storage works).

3. Setup End-to-End Tests under `tests/e2e/`:
   - Test full workflows (e.g., trigger an action, verify the database state, trigger the log archiver, and check the generated parquet payload).
   - Ensure authentication and role-based access checks (if applicable) are tested.

Write clean, highly structured pytest code utilizing fixtures. Include clean tear-downs to reset the database states and local temp files.
```

### Optimization Prompt
```markdown
Task: Optimize the performance, maintainability, and scalability of the `cryptography-service` microservice.

Areas of Optimization:
1. Database (MongoDB) Performance:
   - Review and implement the index design: Index on crypto_assets (expiry_date, status) and (algorithm, strength).
   - Optimize queries using project filters and pagination to minimize memory usage on large collections.
   - Enforce connection pooling configurations with PyMongo/Beanie, tuning `maxPoolSize`, `minPoolSize`, and `maxIdleTimeMS`.

2. Logging (Parquet Archiving) Pipeline:
   - Optimize memory consumption during the Parquet conversion. Instead of loading all buffered logs into memory at once, stream logs in chunks using `pyarrow.parquet.ParquetWriter`.
   - Implement snappy or zstd compression on the Parquet file to optimize GCS storage fees and network transfer times.
   - Use async background tasks (e.g., FastAPI's `BackgroundTasks` or Celery) so that log writing and GCS uploads do not block the active API request-response cycle.

3. Deployment & Cloud Resource Optimization:
   - GCP (Cloud Run): Configure CPU and memory limits. Setup concurrency settings to handle multiple simultaneous requests per container instance, minimizing cold starts.
   - Proxmox (LXC/VM): Design container configuration profiles with appropriate swap space limits, IO limits, and CPU weight parameters.
   - Implement health check endpoints (`/health` and `/ready`) that verify MongoDB and disk storage health for liveness/readiness probes in Proxmox / Google Cloud.

Analyze the microservice code to refactor any synchronous blocking calls to asynchronous alternatives (`async`/`await`). Provide clean, optimized refactoring blocks for index creation, background task logic, and async query executions.
```

---

## User Story 16: Third-Party and Supply-Chain Security Agent

**Summary**:
The goal of the Third-Party and Supply-Chain Security Agent is to fulfill the story requirements: \"As a proactive Third-Party and Supply-Chain Security Agent, I want to assess and continuously monitor supplier security risk so that external dependencies do not expose the bank to unacceptable harm.\". To achieve this, the microservice `supply-chain-security-service` will expose several API endpoints using FastAPI, managing data across MongoDB collections like `suppliers`, `risk_assessments`, `supplier_findings`, `contracts`. Key functionality includes enforcing specific business constraints such as: Implement supplier risk-weighting engine. Build trigger notifications when supplier security postures drift (e.g., external threat feeds indicating breach). Block onboarding dynamically without human override. To ensure audit compliance and regulatory alignment, the microservice captures all decisions in high-performance local MongoDB collections and archives long-term logs to compressed Parquet files, which are securely uploaded to Google Cloud Storage. The microservice is designed for containerized deployment, running on GCP Cloud Run for cloud workflows or within Proxmox LXC containers for localized, secure production environments. Acceptance criteria dictate strict validation, verification checkpoints, and human-in-the-loop approvals for any critical or material actions.

### Implementation Prompt
```markdown
Task: Implement the `supply-chain-security-service` microservice for the 'Third-Party and Supply-Chain Security Agent'.

Technology Stack:
- Python
- Modular Microservices Architecture
- FastAPI for the API layer
- MongoDB for the database layer (use PyMongo or Beanie ODM)
- Parquet for long-term log storage (using PyArrow/Pandas)
- Google Cloud (GCS/Cloud Run) for cloud deployment
- Proxmox VE for local virtualization/production deployment

Requirements:
1. Create a structured Python project with FastAPI for the `supply-chain-security-service`:
   - `main.py` - FastAPI app initialization, routes registration, and exception handlers.
   - `config.py` - Pydantic settings loading MongoDB URI, GCP project details, Proxmox configs, and log paths.
   - `models/` - MongoDB schemas mapping the collections: `suppliers`, `risk_assessments`, `supplier_findings`, `contracts`.
   - `routers/` - Clean FastAPI router modules implementing:
          - POST /suppliers/assess - Assess supplier security before onboarding and periodically
     - POST /suppliers/risk - Calculate supplier risk factoring in criticality, data access, connectivity, subcontractors, and concentration
     - POST /suppliers/contracts - Map contractual security requirements to assessed supplier risk
     - POST /suppliers/findings - Track security findings, remediation actions, owners, and deadlines
     - POST /suppliers/approve - Route high-risk onboarding or risk acceptances for human approval
   - `services/` - Business logic implementation.
   - `utils/logging.py` - Custom logger logging events to MongoDB for active querying and periodically buffering/writing log events to local Parquet files, with automated upload to Google Cloud Storage.

2. Specific Business Logic:
   - Story: As a proactive Third-Party and Supply-Chain Security Agent, I want to assess and continuously monitor supplier security risk so that external dependencies do not expose the bank to unacceptable harm.
   - Custom implementation details: Implement supplier risk-weighting engine. Build trigger notifications when supplier security postures drift (e.g., external threat feeds indicating breach). Block onboarding dynamically without human override.

3. Parquet Logging Pipeline:
   - Configure a background task or worker that runs every hour or when logs reach 1000 records.
   - Buffer raw logs as standard dicts. Format into a Pandas DataFrame or PyArrow Table using a schema representing (timestamp, event_id, event_type, agent_identity, details_json, severity).
   - Write logs locally to a Parquet file (using Snappy compression).
   - Upload the resulting Parquet file to a Google Cloud Storage bucket (e.g., `gs://bank-audit-logs/supply-chain-security-service/YYYY/MM/DD/`) using `google-cloud-storage`.
   - Setup fallback local directory in Proxmox VM storage if GCP is unreachable.

4. Deployment Configuration:
   - Write a `Dockerfile` multi-stage build optimizing dependency size and security (running as non-root user).
   - Write a Google Cloud Build configuration `cloudbuild.yaml` to build the container and deploy to Google Cloud Run with minimum/maximum instances.
   - Write a Proxmox deployment configuration template (e.g., an Ansible playbook or shell script using pct/qm commands) to deploy this microservice as an LXC container or VM.

Ensure the code is modular, fully typed with Python type hints, incorporates proper error handling with FastAPI HTTPExceptions, and includes clear docstrings. Do not use placeholders.
```

### Testing Prompt
```markdown
Task: Write automated tests (unit, integration, and end-to-end) for the `supply-chain-security-service` microservice.

Technology Stack:
- Python (pytest, pytest-asyncio)
- FastAPI (TestClient, httpx.AsyncClient)
- MongoDB (using mongomock or testcontainers-mongodb)
- Parquet & GCS Mocking (using pandas, pyarrow, and mock/unittest.mock)

Testing Requirements:
1. Setup Unit Tests under `tests/unit/`:
   - Mock MongoDB connections and database calls using a fixture.
   - Mock Google Cloud Storage client library to verify GCS uploads.
   - Write unit tests for core helper functions, custom formulas, and validation logic: Implement supplier risk-weighting engine. Build trigger notifications when supplier security postures drift (e.g., external threat feeds indicating breach). Block onboarding dynamically without human override.
   - Verify that log archiving buffers logs correctly and generates a valid Parquet file (read the written file back using pyarrow/pandas and check the schemas match).

2. Setup Integration Tests under `tests/integration/`:
   - Use FastAPI `TestClient` or `httpx.AsyncClient` to call endpoints.
   - Test key routes:
          - POST /suppliers/assess - Assess supplier security before onboarding and periodically
     - POST /suppliers/risk - Calculate supplier risk factoring in criticality, data access, connectivity, subcontractors, and concentration
     - POST /suppliers/contracts - Map contractual security requirements to assessed supplier risk
     - POST /suppliers/findings - Track security findings, remediation actions, owners, and deadlines
     - POST /suppliers/approve - Route high-risk onboarding or risk acceptances for human approval
   - Verify the request validation (e.g. invalid schemas return 422 Unprocessable Entity).
   - Assert correct database records are inserted/updated in the mock MongoDB.
   - Test failure modes: database timeout, GCS upload failure (check that fallback local storage works).

3. Setup End-to-End Tests under `tests/e2e/`:
   - Test full workflows (e.g., trigger an action, verify the database state, trigger the log archiver, and check the generated parquet payload).
   - Ensure authentication and role-based access checks (if applicable) are tested.

Write clean, highly structured pytest code utilizing fixtures. Include clean tear-downs to reset the database states and local temp files.
```

### Optimization Prompt
```markdown
Task: Optimize the performance, maintainability, and scalability of the `supply-chain-security-service` microservice.

Areas of Optimization:
1. Database (MongoDB) Performance:
   - Review and implement the index design: Index on suppliers (risk_rating, status) and supplier_findings (supplier_id, deadline).
   - Optimize queries using project filters and pagination to minimize memory usage on large collections.
   - Enforce connection pooling configurations with PyMongo/Beanie, tuning `maxPoolSize`, `minPoolSize`, and `maxIdleTimeMS`.

2. Logging (Parquet Archiving) Pipeline:
   - Optimize memory consumption during the Parquet conversion. Instead of loading all buffered logs into memory at once, stream logs in chunks using `pyarrow.parquet.ParquetWriter`.
   - Implement snappy or zstd compression on the Parquet file to optimize GCS storage fees and network transfer times.
   - Use async background tasks (e.g., FastAPI's `BackgroundTasks` or Celery) so that log writing and GCS uploads do not block the active API request-response cycle.

3. Deployment & Cloud Resource Optimization:
   - GCP (Cloud Run): Configure CPU and memory limits. Setup concurrency settings to handle multiple simultaneous requests per container instance, minimizing cold starts.
   - Proxmox (LXC/VM): Design container configuration profiles with appropriate swap space limits, IO limits, and CPU weight parameters.
   - Implement health check endpoints (`/health` and `/ready`) that verify MongoDB and disk storage health for liveness/readiness probes in Proxmox / Google Cloud.

Analyze the microservice code to refactor any synchronous blocking calls to asynchronous alternatives (`async`/`await`). Provide clean, optimized refactoring blocks for index creation, background task logic, and async query executions.
```

---

## User Story 17: Security Assurance and Control Testing Agent

**Summary**:
The goal of the Security Assurance and Control Testing Agent is to fulfill the story requirements: \"As a proactive Security Assurance and Control Testing Agent, I want to test security controls independently and continuously so that control failures are identified and corrected before causing material harm.\". To achieve this, the microservice `security-assurance-service` will expose several API endpoints using FastAPI, managing data across MongoDB collections like `control_tests`, `test_results`, `assurance_findings`. Key functionality includes enforcing specific business constraints such as: Implement standard testing routines validating control inputs against expected outputs. Enforce evidentiary file uploads (e.g. logs/configs) and check hashes before closing findings. To ensure audit compliance and regulatory alignment, the microservice captures all decisions in high-performance local MongoDB collections and archives long-term logs to compressed Parquet files, which are securely uploaded to Google Cloud Storage. The microservice is designed for containerized deployment, running on GCP Cloud Run for cloud workflows or within Proxmox LXC containers for localized, secure production environments. Acceptance criteria dictate strict validation, verification checkpoints, and human-in-the-loop approvals for any critical or material actions.

### Implementation Prompt
```markdown
Task: Implement the `security-assurance-service` microservice for the 'Security Assurance and Control Testing Agent'.

Technology Stack:
- Python
- Modular Microservices Architecture
- FastAPI for the API layer
- MongoDB for the database layer (use PyMongo or Beanie ODM)
- Parquet for long-term log storage (using PyArrow/Pandas)
- Google Cloud (GCS/Cloud Run) for cloud deployment
- Proxmox VE for local virtualization/production deployment

Requirements:
1. Create a structured Python project with FastAPI for the `security-assurance-service`:
   - `main.py` - FastAPI app initialization, routes registration, and exception handlers.
   - `config.py` - Pydantic settings loading MongoDB URI, GCP project details, Proxmox configs, and log paths.
   - `models/` - MongoDB schemas mapping the collections: `control_tests`, `test_results`, `assurance_findings`.
   - `routers/` - Clean FastAPI router modules implementing:
          - POST /assurance/test - Schedule and run control tests following approved procedures
     - POST /assurance/results - Log test results separating control design failures from operational failures
     - POST /assurance/findings - Document findings with evidence, risk rating, owner, and remediation action
     - POST /assurance/findings/close - Verify corrective evidence and close findings
     - POST /assurance/escalate - Escalate repeated and systemic control failures
   - `services/` - Business logic implementation.
   - `utils/logging.py` - Custom logger logging events to MongoDB for active querying and periodically buffering/writing log events to local Parquet files, with automated upload to Google Cloud Storage.

2. Specific Business Logic:
   - Story: As a proactive Security Assurance and Control Testing Agent, I want to test security controls independently and continuously so that control failures are identified and corrected before causing material harm.
   - Custom implementation details: Implement standard testing routines validating control inputs against expected outputs. Enforce evidentiary file uploads (e.g. logs/configs) and check hashes before closing findings.

3. Parquet Logging Pipeline:
   - Configure a background task or worker that runs every hour or when logs reach 1000 records.
   - Buffer raw logs as standard dicts. Format into a Pandas DataFrame or PyArrow Table using a schema representing (timestamp, event_id, event_type, agent_identity, details_json, severity).
   - Write logs locally to a Parquet file (using Snappy compression).
   - Upload the resulting Parquet file to a Google Cloud Storage bucket (e.g., `gs://bank-audit-logs/security-assurance-service/YYYY/MM/DD/`) using `google-cloud-storage`.
   - Setup fallback local directory in Proxmox VM storage if GCP is unreachable.

4. Deployment Configuration:
   - Write a `Dockerfile` multi-stage build optimizing dependency size and security (running as non-root user).
   - Write a Google Cloud Build configuration `cloudbuild.yaml` to build the container and deploy to Google Cloud Run with minimum/maximum instances.
   - Write a Proxmox deployment configuration template (e.g., an Ansible playbook or shell script using pct/qm commands) to deploy this microservice as an LXC container or VM.

Ensure the code is modular, fully typed with Python type hints, incorporates proper error handling with FastAPI HTTPExceptions, and includes clear docstrings. Do not use placeholders.
```

### Testing Prompt
```markdown
Task: Write automated tests (unit, integration, and end-to-end) for the `security-assurance-service` microservice.

Technology Stack:
- Python (pytest, pytest-asyncio)
- FastAPI (TestClient, httpx.AsyncClient)
- MongoDB (using mongomock or testcontainers-mongodb)
- Parquet & GCS Mocking (using pandas, pyarrow, and mock/unittest.mock)

Testing Requirements:
1. Setup Unit Tests under `tests/unit/`:
   - Mock MongoDB connections and database calls using a fixture.
   - Mock Google Cloud Storage client library to verify GCS uploads.
   - Write unit tests for core helper functions, custom formulas, and validation logic: Implement standard testing routines validating control inputs against expected outputs. Enforce evidentiary file uploads (e.g. logs/configs) and check hashes before closing findings.
   - Verify that log archiving buffers logs correctly and generates a valid Parquet file (read the written file back using pyarrow/pandas and check the schemas match).

2. Setup Integration Tests under `tests/integration/`:
   - Use FastAPI `TestClient` or `httpx.AsyncClient` to call endpoints.
   - Test key routes:
          - POST /assurance/test - Schedule and run control tests following approved procedures
     - POST /assurance/results - Log test results separating control design failures from operational failures
     - POST /assurance/findings - Document findings with evidence, risk rating, owner, and remediation action
     - POST /assurance/findings/close - Verify corrective evidence and close findings
     - POST /assurance/escalate - Escalate repeated and systemic control failures
   - Verify the request validation (e.g. invalid schemas return 422 Unprocessable Entity).
   - Assert correct database records are inserted/updated in the mock MongoDB.
   - Test failure modes: database timeout, GCS upload failure (check that fallback local storage works).

3. Setup End-to-End Tests under `tests/e2e/`:
   - Test full workflows (e.g., trigger an action, verify the database state, trigger the log archiver, and check the generated parquet payload).
   - Ensure authentication and role-based access checks (if applicable) are tested.

Write clean, highly structured pytest code utilizing fixtures. Include clean tear-downs to reset the database states and local temp files.
```

### Optimization Prompt
```markdown
Task: Optimize the performance, maintainability, and scalability of the `security-assurance-service` microservice.

Areas of Optimization:
1. Database (MongoDB) Performance:
   - Review and implement the index design: Index on control_tests (control_id, scheduled_date) and assurance_findings (status, severity).
   - Optimize queries using project filters and pagination to minimize memory usage on large collections.
   - Enforce connection pooling configurations with PyMongo/Beanie, tuning `maxPoolSize`, `minPoolSize`, and `maxIdleTimeMS`.

2. Logging (Parquet Archiving) Pipeline:
   - Optimize memory consumption during the Parquet conversion. Instead of loading all buffered logs into memory at once, stream logs in chunks using `pyarrow.parquet.ParquetWriter`.
   - Implement snappy or zstd compression on the Parquet file to optimize GCS storage fees and network transfer times.
   - Use async background tasks (e.g., FastAPI's `BackgroundTasks` or Celery) so that log writing and GCS uploads do not block the active API request-response cycle.

3. Deployment & Cloud Resource Optimization:
   - GCP (Cloud Run): Configure CPU and memory limits. Setup concurrency settings to handle multiple simultaneous requests per container instance, minimizing cold starts.
   - Proxmox (LXC/VM): Design container configuration profiles with appropriate swap space limits, IO limits, and CPU weight parameters.
   - Implement health check endpoints (`/health` and `/ready`) that verify MongoDB and disk storage health for liveness/readiness probes in Proxmox / Google Cloud.

Analyze the microservice code to refactor any synchronous blocking calls to asynchronous alternatives (`async`/`await`). Provide clean, optimized refactoring blocks for index creation, background task logic, and async query executions.
```

---

## User Story 18: Regulatory Security Compliance Agent

**Summary**:
The goal of the Regulatory Security Compliance Agent is to fulfill the story requirements: \"As a proactive Regulatory Security Compliance Agent, I want to identify obligations, evaluate compliance, and coordinate evidence so that the bank meets applicable cybersecurity requirements.\". To achieve this, the microservice `compliance-service` will expose several API endpoints using FastAPI, managing data across MongoDB collections like `obligations`, `mappings`, `compliance_assessments`, `evidence_store`. Key functionality includes enforcing specific business constraints such as: Setup regulatory calendar track reporting deadlines. Map DORA and PCI controls dynamically to evidence files. Require human signatures on submissions prior to final lock. To ensure audit compliance and regulatory alignment, the microservice captures all decisions in high-performance local MongoDB collections and archives long-term logs to compressed Parquet files, which are securely uploaded to Google Cloud Storage. The microservice is designed for containerized deployment, running on GCP Cloud Run for cloud workflows or within Proxmox LXC containers for localized, secure production environments. Acceptance criteria dictate strict validation, verification checkpoints, and human-in-the-loop approvals for any critical or material actions.

### Implementation Prompt
```markdown
Task: Implement the `compliance-service` microservice for the 'Regulatory Security Compliance Agent'.

Technology Stack:
- Python
- Modular Microservices Architecture
- FastAPI for the API layer
- MongoDB for the database layer (use PyMongo or Beanie ODM)
- Parquet for long-term log storage (using PyArrow/Pandas)
- Google Cloud (GCS/Cloud Run) for cloud deployment
- Proxmox VE for local virtualization/production deployment

Requirements:
1. Create a structured Python project with FastAPI for the `compliance-service`:
   - `main.py` - FastAPI app initialization, routes registration, and exception handlers.
   - `config.py` - Pydantic settings loading MongoDB URI, GCP project details, Proxmox configs, and log paths.
   - `models/` - MongoDB schemas mapping the collections: `obligations`, `mappings`, `compliance_assessments`, `evidence_store`.
   - `routers/` - Clean FastAPI router modules implementing:
          - POST /compliance/obligations - Ingest and maintain regulatory security obligations (DORA, PCI-DSS, SOC2)
     - POST /compliance/map - Map obligations to policies, controls, evidence, owners, and reporting dates
     - POST /compliance/assess - Evaluate gaps and generate accountable remediation plans
     - POST /compliance/evidence - Collect, check, and store compliance evidence
     - POST /compliance/submit - Route regulatory submissions and attestations for authorised human approval
   - `services/` - Business logic implementation.
   - `utils/logging.py` - Custom logger logging events to MongoDB for active querying and periodically buffering/writing log events to local Parquet files, with automated upload to Google Cloud Storage.

2. Specific Business Logic:
   - Story: As a proactive Regulatory Security Compliance Agent, I want to identify obligations, evaluate compliance, and coordinate evidence so that the bank meets applicable cybersecurity requirements.
   - Custom implementation details: Setup regulatory calendar track reporting deadlines. Map DORA and PCI controls dynamically to evidence files. Require human signatures on submissions prior to final lock.

3. Parquet Logging Pipeline:
   - Configure a background task or worker that runs every hour or when logs reach 1000 records.
   - Buffer raw logs as standard dicts. Format into a Pandas DataFrame or PyArrow Table using a schema representing (timestamp, event_id, event_type, agent_identity, details_json, severity).
   - Write logs locally to a Parquet file (using Snappy compression).
   - Upload the resulting Parquet file to a Google Cloud Storage bucket (e.g., `gs://bank-audit-logs/compliance-service/YYYY/MM/DD/`) using `google-cloud-storage`.
   - Setup fallback local directory in Proxmox VM storage if GCP is unreachable.

4. Deployment Configuration:
   - Write a `Dockerfile` multi-stage build optimizing dependency size and security (running as non-root user).
   - Write a Google Cloud Build configuration `cloudbuild.yaml` to build the container and deploy to Google Cloud Run with minimum/maximum instances.
   - Write a Proxmox deployment configuration template (e.g., an Ansible playbook or shell script using pct/qm commands) to deploy this microservice as an LXC container or VM.

Ensure the code is modular, fully typed with Python type hints, incorporates proper error handling with FastAPI HTTPExceptions, and includes clear docstrings. Do not use placeholders.
```

### Testing Prompt
```markdown
Task: Write automated tests (unit, integration, and end-to-end) for the `compliance-service` microservice.

Technology Stack:
- Python (pytest, pytest-asyncio)
- FastAPI (TestClient, httpx.AsyncClient)
- MongoDB (using mongomock or testcontainers-mongodb)
- Parquet & GCS Mocking (using pandas, pyarrow, and mock/unittest.mock)

Testing Requirements:
1. Setup Unit Tests under `tests/unit/`:
   - Mock MongoDB connections and database calls using a fixture.
   - Mock Google Cloud Storage client library to verify GCS uploads.
   - Write unit tests for core helper functions, custom formulas, and validation logic: Setup regulatory calendar track reporting deadlines. Map DORA and PCI controls dynamically to evidence files. Require human signatures on submissions prior to final lock.
   - Verify that log archiving buffers logs correctly and generates a valid Parquet file (read the written file back using pyarrow/pandas and check the schemas match).

2. Setup Integration Tests under `tests/integration/`:
   - Use FastAPI `TestClient` or `httpx.AsyncClient` to call endpoints.
   - Test key routes:
          - POST /compliance/obligations - Ingest and maintain regulatory security obligations (DORA, PCI-DSS, SOC2)
     - POST /compliance/map - Map obligations to policies, controls, evidence, owners, and reporting dates
     - POST /compliance/assess - Evaluate gaps and generate accountable remediation plans
     - POST /compliance/evidence - Collect, check, and store compliance evidence
     - POST /compliance/submit - Route regulatory submissions and attestations for authorised human approval
   - Verify the request validation (e.g. invalid schemas return 422 Unprocessable Entity).
   - Assert correct database records are inserted/updated in the mock MongoDB.
   - Test failure modes: database timeout, GCS upload failure (check that fallback local storage works).

3. Setup End-to-End Tests under `tests/e2e/`:
   - Test full workflows (e.g., trigger an action, verify the database state, trigger the log archiver, and check the generated parquet payload).
   - Ensure authentication and role-based access checks (if applicable) are tested.

Write clean, highly structured pytest code utilizing fixtures. Include clean tear-downs to reset the database states and local temp files.
```

### Optimization Prompt
```markdown
Task: Optimize the performance, maintainability, and scalability of the `compliance-service` microservice.

Areas of Optimization:
1. Database (MongoDB) Performance:
   - Review and implement the index design: Compound index on obligations for (framework, section) and mappings for (obligation_id, control_id).
   - Optimize queries using project filters and pagination to minimize memory usage on large collections.
   - Enforce connection pooling configurations with PyMongo/Beanie, tuning `maxPoolSize`, `minPoolSize`, and `maxIdleTimeMS`.

2. Logging (Parquet Archiving) Pipeline:
   - Optimize memory consumption during the Parquet conversion. Instead of loading all buffered logs into memory at once, stream logs in chunks using `pyarrow.parquet.ParquetWriter`.
   - Implement snappy or zstd compression on the Parquet file to optimize GCS storage fees and network transfer times.
   - Use async background tasks (e.g., FastAPI's `BackgroundTasks` or Celery) so that log writing and GCS uploads do not block the active API request-response cycle.

3. Deployment & Cloud Resource Optimization:
   - GCP (Cloud Run): Configure CPU and memory limits. Setup concurrency settings to handle multiple simultaneous requests per container instance, minimizing cold starts.
   - Proxmox (LXC/VM): Design container configuration profiles with appropriate swap space limits, IO limits, and CPU weight parameters.
   - Implement health check endpoints (`/health` and `/ready`) that verify MongoDB and disk storage health for liveness/readiness probes in Proxmox / Google Cloud.

Analyze the microservice code to refactor any synchronous blocking calls to asynchronous alternatives (`async`/`await`). Provide clean, optimized refactoring blocks for index creation, background task logic, and async query executions.
```

---

## User Story 19: Security Awareness and Human Risk Agent

**Summary**:
The goal of the Security Awareness and Human Risk Agent is to fulfill the story requirements: \"As a proactive Security Awareness and Human Risk Agent, I want to deliver risk-based learning and behavioural interventions so that employees recognise and avoid security threats.\". To achieve this, the microservice `human-risk-service` will expose several API endpoints using FastAPI, managing data across MongoDB collections like `training_assignments`, `simulations`, `user_behaviors`, `coaching_logs`. Key functionality includes enforcing specific business constraints such as: Implement targeted phishing engine scheduling and assessment. Calculate individual user 'Human Risk Scores' by combining training history with phishing failure rates and proxy block logs. To ensure audit compliance and regulatory alignment, the microservice captures all decisions in high-performance local MongoDB collections and archives long-term logs to compressed Parquet files, which are securely uploaded to Google Cloud Storage. The microservice is designed for containerized deployment, running on GCP Cloud Run for cloud workflows or within Proxmox LXC containers for localized, secure production environments. Acceptance criteria dictate strict validation, verification checkpoints, and human-in-the-loop approvals for any critical or material actions.

### Implementation Prompt
```markdown
Task: Implement the `human-risk-service` microservice for the 'Security Awareness and Human Risk Agent'.

Technology Stack:
- Python
- Modular Microservices Architecture
- FastAPI for the API layer
- MongoDB for the database layer (use PyMongo or Beanie ODM)
- Parquet for long-term log storage (using PyArrow/Pandas)
- Google Cloud (GCS/Cloud Run) for cloud deployment
- Proxmox VE for local virtualization/production deployment

Requirements:
1. Create a structured Python project with FastAPI for the `human-risk-service`:
   - `main.py` - FastAPI app initialization, routes registration, and exception handlers.
   - `config.py` - Pydantic settings loading MongoDB URI, GCP project details, Proxmox configs, and log paths.
   - `models/` - MongoDB schemas mapping the collections: `training_assignments`, `simulations`, `user_behaviors`, `coaching_logs`.
   - `routers/` - Clean FastAPI router modules implementing:
          - POST /awareness/assign - Assign security training based on role and risk exposure
     - POST /awareness/simulate - Schedule and record phishing/social engineering simulations
     - POST /awareness/behavior - Record high-risk behavioural patterns (e.g. repeated blocklist hits)
     - POST /awareness/coach - Trigger targeted coaching and micro-learning modules based on risk triggers
     - GET /awareness/metrics - Measure program effectiveness using behavioral changes
   - `services/` - Business logic implementation.
   - `utils/logging.py` - Custom logger logging events to MongoDB for active querying and periodically buffering/writing log events to local Parquet files, with automated upload to Google Cloud Storage.

2. Specific Business Logic:
   - Story: As a proactive Security Awareness and Human Risk Agent, I want to deliver risk-based learning and behavioural interventions so that employees recognise and avoid security threats.
   - Custom implementation details: Implement targeted phishing engine scheduling and assessment. Calculate individual user 'Human Risk Scores' by combining training history with phishing failure rates and proxy block logs.

3. Parquet Logging Pipeline:
   - Configure a background task or worker that runs every hour or when logs reach 1000 records.
   - Buffer raw logs as standard dicts. Format into a Pandas DataFrame or PyArrow Table using a schema representing (timestamp, event_id, event_type, agent_identity, details_json, severity).
   - Write logs locally to a Parquet file (using Snappy compression).
   - Upload the resulting Parquet file to a Google Cloud Storage bucket (e.g., `gs://bank-audit-logs/human-risk-service/YYYY/MM/DD/`) using `google-cloud-storage`.
   - Setup fallback local directory in Proxmox VM storage if GCP is unreachable.

4. Deployment Configuration:
   - Write a `Dockerfile` multi-stage build optimizing dependency size and security (running as non-root user).
   - Write a Google Cloud Build configuration `cloudbuild.yaml` to build the container and deploy to Google Cloud Run with minimum/maximum instances.
   - Write a Proxmox deployment configuration template (e.g., an Ansible playbook or shell script using pct/qm commands) to deploy this microservice as an LXC container or VM.

Ensure the code is modular, fully typed with Python type hints, incorporates proper error handling with FastAPI HTTPExceptions, and includes clear docstrings. Do not use placeholders.
```

### Testing Prompt
```markdown
Task: Write automated tests (unit, integration, and end-to-end) for the `human-risk-service` microservice.

Technology Stack:
- Python (pytest, pytest-asyncio)
- FastAPI (TestClient, httpx.AsyncClient)
- MongoDB (using mongomock or testcontainers-mongodb)
- Parquet & GCS Mocking (using pandas, pyarrow, and mock/unittest.mock)

Testing Requirements:
1. Setup Unit Tests under `tests/unit/`:
   - Mock MongoDB connections and database calls using a fixture.
   - Mock Google Cloud Storage client library to verify GCS uploads.
   - Write unit tests for core helper functions, custom formulas, and validation logic: Implement targeted phishing engine scheduling and assessment. Calculate individual user 'Human Risk Scores' by combining training history with phishing failure rates and proxy block logs.
   - Verify that log archiving buffers logs correctly and generates a valid Parquet file (read the written file back using pyarrow/pandas and check the schemas match).

2. Setup Integration Tests under `tests/integration/`:
   - Use FastAPI `TestClient` or `httpx.AsyncClient` to call endpoints.
   - Test key routes:
          - POST /awareness/assign - Assign security training based on role and risk exposure
     - POST /awareness/simulate - Schedule and record phishing/social engineering simulations
     - POST /awareness/behavior - Record high-risk behavioural patterns (e.g. repeated blocklist hits)
     - POST /awareness/coach - Trigger targeted coaching and micro-learning modules based on risk triggers
     - GET /awareness/metrics - Measure program effectiveness using behavioral changes
   - Verify the request validation (e.g. invalid schemas return 422 Unprocessable Entity).
   - Assert correct database records are inserted/updated in the mock MongoDB.
   - Test failure modes: database timeout, GCS upload failure (check that fallback local storage works).

3. Setup End-to-End Tests under `tests/e2e/`:
   - Test full workflows (e.g., trigger an action, verify the database state, trigger the log archiver, and check the generated parquet payload).
   - Ensure authentication and role-based access checks (if applicable) are tested.

Write clean, highly structured pytest code utilizing fixtures. Include clean tear-downs to reset the database states and local temp files.
```

### Optimization Prompt
```markdown
Task: Optimize the performance, maintainability, and scalability of the `human-risk-service` microservice.

Areas of Optimization:
1. Database (MongoDB) Performance:
   - Review and implement the index design: Index on training_assignments (user_id, status) and user_behaviors (user_id, risk_score).
   - Optimize queries using project filters and pagination to minimize memory usage on large collections.
   - Enforce connection pooling configurations with PyMongo/Beanie, tuning `maxPoolSize`, `minPoolSize`, and `maxIdleTimeMS`.

2. Logging (Parquet Archiving) Pipeline:
   - Optimize memory consumption during the Parquet conversion. Instead of loading all buffered logs into memory at once, stream logs in chunks using `pyarrow.parquet.ParquetWriter`.
   - Implement snappy or zstd compression on the Parquet file to optimize GCS storage fees and network transfer times.
   - Use async background tasks (e.g., FastAPI's `BackgroundTasks` or Celery) so that log writing and GCS uploads do not block the active API request-response cycle.

3. Deployment & Cloud Resource Optimization:
   - GCP (Cloud Run): Configure CPU and memory limits. Setup concurrency settings to handle multiple simultaneous requests per container instance, minimizing cold starts.
   - Proxmox (LXC/VM): Design container configuration profiles with appropriate swap space limits, IO limits, and CPU weight parameters.
   - Implement health check endpoints (`/health` and `/ready`) that verify MongoDB and disk storage health for liveness/readiness probes in Proxmox / Google Cloud.

Analyze the microservice code to refactor any synchronous blocking calls to asynchronous alternatives (`async`/`await`). Provide clean, optimized refactoring blocks for index creation, background task logic, and async query executions.
```

---

## User Story 20: Insider Threat Management Agent

**Summary**:
The goal of the Insider Threat Management Agent is to fulfill the story requirements: \"As a proactive Insider Threat Management Agent, I want to identify and investigate authorised-user risk indicators so that malicious, negligent, or compromised insider activity is addressed early.\". To achieve this, the microservice `insider-threat-service` will expose several API endpoints using FastAPI, managing data across MongoDB collections like `activity_telemetry`, `insider_alerts`, `investigation_cases`, `case_audit_logs`. Key functionality includes enforcing specific business constraints such as: Enforce strict RBAC for investigation cases. Build anomaly detection correlating out-of-hours logins with bulk data downloads. Restrict disciplinary actions to human reviews. To ensure audit compliance and regulatory alignment, the microservice captures all decisions in high-performance local MongoDB collections and archives long-term logs to compressed Parquet files, which are securely uploaded to Google Cloud Storage. The microservice is designed for containerized deployment, running on GCP Cloud Run for cloud workflows or within Proxmox LXC containers for localized, secure production environments. Acceptance criteria dictate strict validation, verification checkpoints, and human-in-the-loop approvals for any critical or material actions.

### Implementation Prompt
```markdown
Task: Implement the `insider-threat-service` microservice for the 'Insider Threat Management Agent'.

Technology Stack:
- Python
- Modular Microservices Architecture
- FastAPI for the API layer
- MongoDB for the database layer (use PyMongo or Beanie ODM)
- Parquet for long-term log storage (using PyArrow/Pandas)
- Google Cloud (GCS/Cloud Run) for cloud deployment
- Proxmox VE for local virtualization/production deployment

Requirements:
1. Create a structured Python project with FastAPI for the `insider-threat-service`:
   - `main.py` - FastAPI app initialization, routes registration, and exception handlers.
   - `config.py` - Pydantic settings loading MongoDB URI, GCP project details, Proxmox configs, and log paths.
   - `models/` - MongoDB schemas mapping the collections: `activity_telemetry`, `insider_alerts`, `investigation_cases`, `case_audit_logs`.
   - `routers/` - Clean FastAPI router modules implementing:
          - POST /insider/telemetry - Ingest activity telemetry (data access, login hours, USB egress)
     - POST /insider/alerts - Generate insider risk alerts requiring corroborating context
     - POST /insider/cases - Manage access-controlled, fully auditable insider investigation cases
     - POST /insider/escalate - Escalate high-risk cases to Legal, HR, Privacy, or Investigations
     - GET /insider/cases/audit - Retrieve tamper-evident case change logs
   - `services/` - Business logic implementation.
   - `utils/logging.py` - Custom logger logging events to MongoDB for active querying and periodically buffering/writing log events to local Parquet files, with automated upload to Google Cloud Storage.

2. Specific Business Logic:
   - Story: As a proactive Insider Threat Management Agent, I want to identify and investigate authorised-user risk indicators so that malicious, negligent, or compromised insider activity is addressed early.
   - Custom implementation details: Enforce strict RBAC for investigation cases. Build anomaly detection correlating out-of-hours logins with bulk data downloads. Restrict disciplinary actions to human reviews.

3. Parquet Logging Pipeline:
   - Configure a background task or worker that runs every hour or when logs reach 1000 records.
   - Buffer raw logs as standard dicts. Format into a Pandas DataFrame or PyArrow Table using a schema representing (timestamp, event_id, event_type, agent_identity, details_json, severity).
   - Write logs locally to a Parquet file (using Snappy compression).
   - Upload the resulting Parquet file to a Google Cloud Storage bucket (e.g., `gs://bank-audit-logs/insider-threat-service/YYYY/MM/DD/`) using `google-cloud-storage`.
   - Setup fallback local directory in Proxmox VM storage if GCP is unreachable.

4. Deployment Configuration:
   - Write a `Dockerfile` multi-stage build optimizing dependency size and security (running as non-root user).
   - Write a Google Cloud Build configuration `cloudbuild.yaml` to build the container and deploy to Google Cloud Run with minimum/maximum instances.
   - Write a Proxmox deployment configuration template (e.g., an Ansible playbook or shell script using pct/qm commands) to deploy this microservice as an LXC container or VM.

Ensure the code is modular, fully typed with Python type hints, incorporates proper error handling with FastAPI HTTPExceptions, and includes clear docstrings. Do not use placeholders.
```

### Testing Prompt
```markdown
Task: Write automated tests (unit, integration, and end-to-end) for the `insider-threat-service` microservice.

Technology Stack:
- Python (pytest, pytest-asyncio)
- FastAPI (TestClient, httpx.AsyncClient)
- MongoDB (using mongomock or testcontainers-mongodb)
- Parquet & GCS Mocking (using pandas, pyarrow, and mock/unittest.mock)

Testing Requirements:
1. Setup Unit Tests under `tests/unit/`:
   - Mock MongoDB connections and database calls using a fixture.
   - Mock Google Cloud Storage client library to verify GCS uploads.
   - Write unit tests for core helper functions, custom formulas, and validation logic: Enforce strict RBAC for investigation cases. Build anomaly detection correlating out-of-hours logins with bulk data downloads. Restrict disciplinary actions to human reviews.
   - Verify that log archiving buffers logs correctly and generates a valid Parquet file (read the written file back using pyarrow/pandas and check the schemas match).

2. Setup Integration Tests under `tests/integration/`:
   - Use FastAPI `TestClient` or `httpx.AsyncClient` to call endpoints.
   - Test key routes:
          - POST /insider/telemetry - Ingest activity telemetry (data access, login hours, USB egress)
     - POST /insider/alerts - Generate insider risk alerts requiring corroborating context
     - POST /insider/cases - Manage access-controlled, fully auditable insider investigation cases
     - POST /insider/escalate - Escalate high-risk cases to Legal, HR, Privacy, or Investigations
     - GET /insider/cases/audit - Retrieve tamper-evident case change logs
   - Verify the request validation (e.g. invalid schemas return 422 Unprocessable Entity).
   - Assert correct database records are inserted/updated in the mock MongoDB.
   - Test failure modes: database timeout, GCS upload failure (check that fallback local storage works).

3. Setup End-to-End Tests under `tests/e2e/`:
   - Test full workflows (e.g., trigger an action, verify the database state, trigger the log archiver, and check the generated parquet payload).
   - Ensure authentication and role-based access checks (if applicable) are tested.

Write clean, highly structured pytest code utilizing fixtures. Include clean tear-downs to reset the database states and local temp files.
```

### Optimization Prompt
```markdown
Task: Optimize the performance, maintainability, and scalability of the `insider-threat-service` microservice.

Areas of Optimization:
1. Database (MongoDB) Performance:
   - Review and implement the index design: Compound index on activity_telemetry for (user_id, timestamp) and investigation_cases for (status, sensitivity).
   - Optimize queries using project filters and pagination to minimize memory usage on large collections.
   - Enforce connection pooling configurations with PyMongo/Beanie, tuning `maxPoolSize`, `minPoolSize`, and `maxIdleTimeMS`.

2. Logging (Parquet Archiving) Pipeline:
   - Optimize memory consumption during the Parquet conversion. Instead of loading all buffered logs into memory at once, stream logs in chunks using `pyarrow.parquet.ParquetWriter`.
   - Implement snappy or zstd compression on the Parquet file to optimize GCS storage fees and network transfer times.
   - Use async background tasks (e.g., FastAPI's `BackgroundTasks` or Celery) so that log writing and GCS uploads do not block the active API request-response cycle.

3. Deployment & Cloud Resource Optimization:
   - GCP (Cloud Run): Configure CPU and memory limits. Setup concurrency settings to handle multiple simultaneous requests per container instance, minimizing cold starts.
   - Proxmox (LXC/VM): Design container configuration profiles with appropriate swap space limits, IO limits, and CPU weight parameters.
   - Implement health check endpoints (`/health` and `/ready`) that verify MongoDB and disk storage health for liveness/readiness probes in Proxmox / Google Cloud.

Analyze the microservice code to refactor any synchronous blocking calls to asynchronous alternatives (`async`/`await`). Provide clean, optimized refactoring blocks for index creation, background task logic, and async query executions.
```

---

## User Story 21: Security Resilience and Cyber Recovery Agent

**Summary**:
The goal of the Security Resilience and Cyber Recovery Agent is to fulfill the story requirements: \"As a proactive Security Resilience and Cyber Recovery Agent, I want to validate recovery capabilities and coordinate cyber-resilience improvements so that critical banking services can recover within approved tolerances.\". To achieve this, the microservice `cyber-resilience-service` will expose several API endpoints using FastAPI, managing data across MongoDB collections like `service_mappings`, `resilience_objectives`, `backup_tests`, `exercise_logs`, `corrective_actions`. Key functionality includes enforcing specific business constraints such as: Implement dependency mapping graph. Build evaluation logic verifying recovery times against RTO/RPO limits and raising high-priority findings for violations. To ensure audit compliance and regulatory alignment, the microservice captures all decisions in high-performance local MongoDB collections and archives long-term logs to compressed Parquet files, which are securely uploaded to Google Cloud Storage. The microservice is designed for containerized deployment, running on GCP Cloud Run for cloud workflows or within Proxmox LXC containers for localized, secure production environments. Acceptance criteria dictate strict validation, verification checkpoints, and human-in-the-loop approvals for any critical or material actions.

### Implementation Prompt
```markdown
Task: Implement the `cyber-resilience-service` microservice for the 'Security Resilience and Cyber Recovery Agent'.

Technology Stack:
- Python
- Modular Microservices Architecture
- FastAPI for the API layer
- MongoDB for the database layer (use PyMongo or Beanie ODM)
- Parquet for long-term log storage (using PyArrow/Pandas)
- Google Cloud (GCS/Cloud Run) for cloud deployment
- Proxmox VE for local virtualization/production deployment

Requirements:
1. Create a structured Python project with FastAPI for the `cyber-resilience-service`:
   - `main.py` - FastAPI app initialization, routes registration, and exception handlers.
   - `config.py` - Pydantic settings loading MongoDB URI, GCP project details, Proxmox configs, and log paths.
   - `models/` - MongoDB schemas mapping the collections: `service_mappings`, `resilience_objectives`, `backup_tests`, `exercise_logs`, `corrective_actions`.
   - `routers/` - Clean FastAPI router modules implementing:
          - POST /resilience/map - Map critical banking services to tech, data, suppliers, identities, and recovery paths
     - POST /resilience/objectives - Record recovery objectives (RTO/RPO) and impact tolerances
     - POST /resilience/test - Schedule and log backup integrity, isolation, and restoration tests
     - POST /resilience/exercises - Orchestrate ransomware and destructive-attack simulation exercises
     - POST /resilience/findings - Generate owned and time-bound corrective actions for failed recovery tests
   - `services/` - Business logic implementation.
   - `utils/logging.py` - Custom logger logging events to MongoDB for active querying and periodically buffering/writing log events to local Parquet files, with automated upload to Google Cloud Storage.

2. Specific Business Logic:
   - Story: As a proactive Security Resilience and Cyber Recovery Agent, I want to validate recovery capabilities and coordinate cyber-resilience improvements so that critical banking services can recover within approved tolerances.
   - Custom implementation details: Implement dependency mapping graph. Build evaluation logic verifying recovery times against RTO/RPO limits and raising high-priority findings for violations.

3. Parquet Logging Pipeline:
   - Configure a background task or worker that runs every hour or when logs reach 1000 records.
   - Buffer raw logs as standard dicts. Format into a Pandas DataFrame or PyArrow Table using a schema representing (timestamp, event_id, event_type, agent_identity, details_json, severity).
   - Write logs locally to a Parquet file (using Snappy compression).
   - Upload the resulting Parquet file to a Google Cloud Storage bucket (e.g., `gs://bank-audit-logs/cyber-resilience-service/YYYY/MM/DD/`) using `google-cloud-storage`.
   - Setup fallback local directory in Proxmox VM storage if GCP is unreachable.

4. Deployment Configuration:
   - Write a `Dockerfile` multi-stage build optimizing dependency size and security (running as non-root user).
   - Write a Google Cloud Build configuration `cloudbuild.yaml` to build the container and deploy to Google Cloud Run with minimum/maximum instances.
   - Write a Proxmox deployment configuration template (e.g., an Ansible playbook or shell script using pct/qm commands) to deploy this microservice as an LXC container or VM.

Ensure the code is modular, fully typed with Python type hints, incorporates proper error handling with FastAPI HTTPExceptions, and includes clear docstrings. Do not use placeholders.
```

### Testing Prompt
```markdown
Task: Write automated tests (unit, integration, and end-to-end) for the `cyber-resilience-service` microservice.

Technology Stack:
- Python (pytest, pytest-asyncio)
- FastAPI (TestClient, httpx.AsyncClient)
- MongoDB (using mongomock or testcontainers-mongodb)
- Parquet & GCS Mocking (using pandas, pyarrow, and mock/unittest.mock)

Testing Requirements:
1. Setup Unit Tests under `tests/unit/`:
   - Mock MongoDB connections and database calls using a fixture.
   - Mock Google Cloud Storage client library to verify GCS uploads.
   - Write unit tests for core helper functions, custom formulas, and validation logic: Implement dependency mapping graph. Build evaluation logic verifying recovery times against RTO/RPO limits and raising high-priority findings for violations.
   - Verify that log archiving buffers logs correctly and generates a valid Parquet file (read the written file back using pyarrow/pandas and check the schemas match).

2. Setup Integration Tests under `tests/integration/`:
   - Use FastAPI `TestClient` or `httpx.AsyncClient` to call endpoints.
   - Test key routes:
          - POST /resilience/map - Map critical banking services to tech, data, suppliers, identities, and recovery paths
     - POST /resilience/objectives - Record recovery objectives (RTO/RPO) and impact tolerances
     - POST /resilience/test - Schedule and log backup integrity, isolation, and restoration tests
     - POST /resilience/exercises - Orchestrate ransomware and destructive-attack simulation exercises
     - POST /resilience/findings - Generate owned and time-bound corrective actions for failed recovery tests
   - Verify the request validation (e.g. invalid schemas return 422 Unprocessable Entity).
   - Assert correct database records are inserted/updated in the mock MongoDB.
   - Test failure modes: database timeout, GCS upload failure (check that fallback local storage works).

3. Setup End-to-End Tests under `tests/e2e/`:
   - Test full workflows (e.g., trigger an action, verify the database state, trigger the log archiver, and check the generated parquet payload).
   - Ensure authentication and role-based access checks (if applicable) are tested.

Write clean, highly structured pytest code utilizing fixtures. Include clean tear-downs to reset the database states and local temp files.
```

### Optimization Prompt
```markdown
Task: Optimize the performance, maintainability, and scalability of the `cyber-resilience-service` microservice.

Areas of Optimization:
1. Database (MongoDB) Performance:
   - Review and implement the index design: Index on service_mappings (service_name) and backup_tests (service_id, test_date, status).
   - Optimize queries using project filters and pagination to minimize memory usage on large collections.
   - Enforce connection pooling configurations with PyMongo/Beanie, tuning `maxPoolSize`, `minPoolSize`, and `maxIdleTimeMS`.

2. Logging (Parquet Archiving) Pipeline:
   - Optimize memory consumption during the Parquet conversion. Instead of loading all buffered logs into memory at once, stream logs in chunks using `pyarrow.parquet.ParquetWriter`.
   - Implement snappy or zstd compression on the Parquet file to optimize GCS storage fees and network transfer times.
   - Use async background tasks (e.g., FastAPI's `BackgroundTasks` or Celery) so that log writing and GCS uploads do not block the active API request-response cycle.

3. Deployment & Cloud Resource Optimization:
   - GCP (Cloud Run): Configure CPU and memory limits. Setup concurrency settings to handle multiple simultaneous requests per container instance, minimizing cold starts.
   - Proxmox (LXC/VM): Design container configuration profiles with appropriate swap space limits, IO limits, and CPU weight parameters.
   - Implement health check endpoints (`/health` and `/ready`) that verify MongoDB and disk storage health for liveness/readiness probes in Proxmox / Google Cloud.

Analyze the microservice code to refactor any synchronous blocking calls to asynchronous alternatives (`async`/`await`). Provide clean, optimized refactoring blocks for index creation, background task logic, and async query executions.
```

---

## User Story 22: Payment and Financial Systems Security Agent

**Summary**:
The goal of the Payment and Financial Systems Security Agent is to fulfill the story requirements: \"As a proactive Payment and Financial Systems Security Agent, I want to monitor and protect payment platforms and financial messaging systems so that transactions remain confidential, accurate, available, and trustworthy.\". To achieve this, the microservice `payment-security-service` will expose several API endpoints using FastAPI, managing data across MongoDB collections like `payment_assets`, `payment_telemetry`, `suspicious_events`, `block_rules`. Key functionality includes enforcing specific business constraints such as: Implement real-time transaction correlation with fraud and SWIFT message templates. Integrate SWIFT customer security controls (CSCF) validation and block rules checking. To ensure audit compliance and regulatory alignment, the microservice captures all decisions in high-performance local MongoDB collections and archives long-term logs to compressed Parquet files, which are securely uploaded to Google Cloud Storage. The microservice is designed for containerized deployment, running on GCP Cloud Run for cloud workflows or within Proxmox LXC containers for localized, secure production environments. Acceptance criteria dictate strict validation, verification checkpoints, and human-in-the-loop approvals for any critical or material actions.

### Implementation Prompt
```markdown
Task: Implement the `payment-security-service` microservice for the 'Payment and Financial Systems Security Agent'.

Technology Stack:
- Python
- Modular Microservices Architecture
- FastAPI for the API layer
- MongoDB for the database layer (use PyMongo or Beanie ODM)
- Parquet for long-term log storage (using PyArrow/Pandas)
- Google Cloud (GCS/Cloud Run) for cloud deployment
- Proxmox VE for local virtualization/production deployment

Requirements:
1. Create a structured Python project with FastAPI for the `payment-security-service`:
   - `main.py` - FastAPI app initialization, routes registration, and exception handlers.
   - `config.py` - Pydantic settings loading MongoDB URI, GCP project details, Proxmox configs, and log paths.
   - `models/` - MongoDB schemas mapping the collections: `payment_assets`, `payment_telemetry`, `suspicious_events`, `block_rules`.
   - `routers/` - Clean FastAPI router modules implementing:
          - POST /payments/assets - Inventory critical payment assets, networks, and communication paths
     - POST /payments/monitor - Ingest and monitor payment-specific access, crypto, and network controls
     - POST /payments/correlate - Correlate suspicious technical events with fraud and transaction context
     - POST /payments/escalate - Escalate high-risk payment events immediately
     - POST /payments/block - Apply automated transaction blocking based on fraud and operational rules
   - `services/` - Business logic implementation.
   - `utils/logging.py` - Custom logger logging events to MongoDB for active querying and periodically buffering/writing log events to local Parquet files, with automated upload to Google Cloud Storage.

2. Specific Business Logic:
   - Story: As a proactive Payment and Financial Systems Security Agent, I want to monitor and protect payment platforms and financial messaging systems so that transactions remain confidential, accurate, available, and trustworthy.
   - Custom implementation details: Implement real-time transaction correlation with fraud and SWIFT message templates. Integrate SWIFT customer security controls (CSCF) validation and block rules checking.

3. Parquet Logging Pipeline:
   - Configure a background task or worker that runs every hour or when logs reach 1000 records.
   - Buffer raw logs as standard dicts. Format into a Pandas DataFrame or PyArrow Table using a schema representing (timestamp, event_id, event_type, agent_identity, details_json, severity).
   - Write logs locally to a Parquet file (using Snappy compression).
   - Upload the resulting Parquet file to a Google Cloud Storage bucket (e.g., `gs://bank-audit-logs/payment-security-service/YYYY/MM/DD/`) using `google-cloud-storage`.
   - Setup fallback local directory in Proxmox VM storage if GCP is unreachable.

4. Deployment Configuration:
   - Write a `Dockerfile` multi-stage build optimizing dependency size and security (running as non-root user).
   - Write a Google Cloud Build configuration `cloudbuild.yaml` to build the container and deploy to Google Cloud Run with minimum/maximum instances.
   - Write a Proxmox deployment configuration template (e.g., an Ansible playbook or shell script using pct/qm commands) to deploy this microservice as an LXC container or VM.

Ensure the code is modular, fully typed with Python type hints, incorporates proper error handling with FastAPI HTTPExceptions, and includes clear docstrings. Do not use placeholders.
```

### Testing Prompt
```markdown
Task: Write automated tests (unit, integration, and end-to-end) for the `payment-security-service` microservice.

Technology Stack:
- Python (pytest, pytest-asyncio)
- FastAPI (TestClient, httpx.AsyncClient)
- MongoDB (using mongomock or testcontainers-mongodb)
- Parquet & GCS Mocking (using pandas, pyarrow, and mock/unittest.mock)

Testing Requirements:
1. Setup Unit Tests under `tests/unit/`:
   - Mock MongoDB connections and database calls using a fixture.
   - Mock Google Cloud Storage client library to verify GCS uploads.
   - Write unit tests for core helper functions, custom formulas, and validation logic: Implement real-time transaction correlation with fraud and SWIFT message templates. Integrate SWIFT customer security controls (CSCF) validation and block rules checking.
   - Verify that log archiving buffers logs correctly and generates a valid Parquet file (read the written file back using pyarrow/pandas and check the schemas match).

2. Setup Integration Tests under `tests/integration/`:
   - Use FastAPI `TestClient` or `httpx.AsyncClient` to call endpoints.
   - Test key routes:
          - POST /payments/assets - Inventory critical payment assets, networks, and communication paths
     - POST /payments/monitor - Ingest and monitor payment-specific access, crypto, and network controls
     - POST /payments/correlate - Correlate suspicious technical events with fraud and transaction context
     - POST /payments/escalate - Escalate high-risk payment events immediately
     - POST /payments/block - Apply automated transaction blocking based on fraud and operational rules
   - Verify the request validation (e.g. invalid schemas return 422 Unprocessable Entity).
   - Assert correct database records are inserted/updated in the mock MongoDB.
   - Test failure modes: database timeout, GCS upload failure (check that fallback local storage works).

3. Setup End-to-End Tests under `tests/e2e/`:
   - Test full workflows (e.g., trigger an action, verify the database state, trigger the log archiver, and check the generated parquet payload).
   - Ensure authentication and role-based access checks (if applicable) are tested.

Write clean, highly structured pytest code utilizing fixtures. Include clean tear-downs to reset the database states and local temp files.
```

### Optimization Prompt
```markdown
Task: Optimize the performance, maintainability, and scalability of the `payment-security-service` microservice.

Areas of Optimization:
1. Database (MongoDB) Performance:
   - Review and implement the index design: Compound index on payment_telemetry for (asset_id, timestamp) and suspicious_events for (severity, status).
   - Optimize queries using project filters and pagination to minimize memory usage on large collections.
   - Enforce connection pooling configurations with PyMongo/Beanie, tuning `maxPoolSize`, `minPoolSize`, and `maxIdleTimeMS`.

2. Logging (Parquet Archiving) Pipeline:
   - Optimize memory consumption during the Parquet conversion. Instead of loading all buffered logs into memory at once, stream logs in chunks using `pyarrow.parquet.ParquetWriter`.
   - Implement snappy or zstd compression on the Parquet file to optimize GCS storage fees and network transfer times.
   - Use async background tasks (e.g., FastAPI's `BackgroundTasks` or Celery) so that log writing and GCS uploads do not block the active API request-response cycle.

3. Deployment & Cloud Resource Optimization:
   - GCP (Cloud Run): Configure CPU and memory limits. Setup concurrency settings to handle multiple simultaneous requests per container instance, minimizing cold starts.
   - Proxmox (LXC/VM): Design container configuration profiles with appropriate swap space limits, IO limits, and CPU weight parameters.
   - Implement health check endpoints (`/health` and `/ready`) that verify MongoDB and disk storage health for liveness/readiness probes in Proxmox / Google Cloud.

Analyze the microservice code to refactor any synchronous blocking calls to asynchronous alternatives (`async`/`await`). Provide clean, optimized refactoring blocks for index creation, background task logic, and async query executions.
```

---

## User Story 23: Digital Banking and Customer Security Agent

**Summary**:
The goal of the Digital Banking and Customer Security Agent is to fulfill the story requirements: \"As a proactive Digital Banking and Customer Security Agent, I want to detect and counter attacks against digital banking channels so that customers can access services securely with minimal friction.\". To achieve this, the microservice `digital-banking-security-service` will expose several API endpoints using FastAPI, managing data across MongoDB collections like `channel_telemetry`, `detected_attacks`, `session_states`, `lockout_policies`. Key functionality includes enforcing specific business constraints such as: Build a fast evaluation engine checking login rates per IP/account (bot detection) and initiating MFA challenge requests (step-up authentication). To ensure audit compliance and regulatory alignment, the microservice captures all decisions in high-performance local MongoDB collections and archives long-term logs to compressed Parquet files, which are securely uploaded to Google Cloud Storage. The microservice is designed for containerized deployment, running on GCP Cloud Run for cloud workflows or within Proxmox LXC containers for localized, secure production environments. Acceptance criteria dictate strict validation, verification checkpoints, and human-in-the-loop approvals for any critical or material actions.

### Implementation Prompt
```markdown
Task: Implement the `digital-banking-security-service` microservice for the 'Digital Banking and Customer Security Agent'.

Technology Stack:
- Python
- Modular Microservices Architecture
- FastAPI for the API layer
- MongoDB for the database layer (use PyMongo or Beanie ODM)
- Parquet for long-term log storage (using PyArrow/Pandas)
- Google Cloud (GCS/Cloud Run) for cloud deployment
- Proxmox VE for local virtualization/production deployment

Requirements:
1. Create a structured Python project with FastAPI for the `digital-banking-security-service`:
   - `main.py` - FastAPI app initialization, routes registration, and exception handlers.
   - `config.py` - Pydantic settings loading MongoDB URI, GCP project details, Proxmox configs, and log paths.
   - `models/` - MongoDB schemas mapping the collections: `channel_telemetry`, `detected_attacks`, `session_states`, `lockout_policies`.
   - `routers/` - Clean FastAPI router modules implementing:
          - POST /digital/telemetry - Ingest web, mobile, API, and authentication telemetry
     - POST /digital/detect - Detect account takeover (ATO), credential stuffing, bot activity, and session abuse
     - POST /digital/step-up - Trigger approved step-up authentication (MFA/OTP) or session protection
     - POST /digital/lockout - Enforce customer lockout or service denial based on decision thresholds
     - GET /digital/metrics - Retrieve effectiveness metrics (prevented attacks, false positives, customer impact)
   - `services/` - Business logic implementation.
   - `utils/logging.py` - Custom logger logging events to MongoDB for active querying and periodically buffering/writing log events to local Parquet files, with automated upload to Google Cloud Storage.

2. Specific Business Logic:
   - Story: As a proactive Digital Banking and Customer Security Agent, I want to detect and counter attacks against digital banking channels so that customers can access services securely with minimal friction.
   - Custom implementation details: Build a fast evaluation engine checking login rates per IP/account (bot detection) and initiating MFA challenge requests (step-up authentication).

3. Parquet Logging Pipeline:
   - Configure a background task or worker that runs every hour or when logs reach 1000 records.
   - Buffer raw logs as standard dicts. Format into a Pandas DataFrame or PyArrow Table using a schema representing (timestamp, event_id, event_type, agent_identity, details_json, severity).
   - Write logs locally to a Parquet file (using Snappy compression).
   - Upload the resulting Parquet file to a Google Cloud Storage bucket (e.g., `gs://bank-audit-logs/digital-banking-security-service/YYYY/MM/DD/`) using `google-cloud-storage`.
   - Setup fallback local directory in Proxmox VM storage if GCP is unreachable.

4. Deployment Configuration:
   - Write a `Dockerfile` multi-stage build optimizing dependency size and security (running as non-root user).
   - Write a Google Cloud Build configuration `cloudbuild.yaml` to build the container and deploy to Google Cloud Run with minimum/maximum instances.
   - Write a Proxmox deployment configuration template (e.g., an Ansible playbook or shell script using pct/qm commands) to deploy this microservice as an LXC container or VM.

Ensure the code is modular, fully typed with Python type hints, incorporates proper error handling with FastAPI HTTPExceptions, and includes clear docstrings. Do not use placeholders.
```

### Testing Prompt
```markdown
Task: Write automated tests (unit, integration, and end-to-end) for the `digital-banking-security-service` microservice.

Technology Stack:
- Python (pytest, pytest-asyncio)
- FastAPI (TestClient, httpx.AsyncClient)
- MongoDB (using mongomock or testcontainers-mongodb)
- Parquet & GCS Mocking (using pandas, pyarrow, and mock/unittest.mock)

Testing Requirements:
1. Setup Unit Tests under `tests/unit/`:
   - Mock MongoDB connections and database calls using a fixture.
   - Mock Google Cloud Storage client library to verify GCS uploads.
   - Write unit tests for core helper functions, custom formulas, and validation logic: Build a fast evaluation engine checking login rates per IP/account (bot detection) and initiating MFA challenge requests (step-up authentication).
   - Verify that log archiving buffers logs correctly and generates a valid Parquet file (read the written file back using pyarrow/pandas and check the schemas match).

2. Setup Integration Tests under `tests/integration/`:
   - Use FastAPI `TestClient` or `httpx.AsyncClient` to call endpoints.
   - Test key routes:
          - POST /digital/telemetry - Ingest web, mobile, API, and authentication telemetry
     - POST /digital/detect - Detect account takeover (ATO), credential stuffing, bot activity, and session abuse
     - POST /digital/step-up - Trigger approved step-up authentication (MFA/OTP) or session protection
     - POST /digital/lockout - Enforce customer lockout or service denial based on decision thresholds
     - GET /digital/metrics - Retrieve effectiveness metrics (prevented attacks, false positives, customer impact)
   - Verify the request validation (e.g. invalid schemas return 422 Unprocessable Entity).
   - Assert correct database records are inserted/updated in the mock MongoDB.
   - Test failure modes: database timeout, GCS upload failure (check that fallback local storage works).

3. Setup End-to-End Tests under `tests/e2e/`:
   - Test full workflows (e.g., trigger an action, verify the database state, trigger the log archiver, and check the generated parquet payload).
   - Ensure authentication and role-based access checks (if applicable) are tested.

Write clean, highly structured pytest code utilizing fixtures. Include clean tear-downs to reset the database states and local temp files.
```

### Optimization Prompt
```markdown
Task: Optimize the performance, maintainability, and scalability of the `digital-banking-security-service` microservice.

Areas of Optimization:
1. Database (MongoDB) Performance:
   - Review and implement the index design: Compound index on channel_telemetry for (ip_address, timestamp) and (account_id, timestamp).
   - Optimize queries using project filters and pagination to minimize memory usage on large collections.
   - Enforce connection pooling configurations with PyMongo/Beanie, tuning `maxPoolSize`, `minPoolSize`, and `maxIdleTimeMS`.

2. Logging (Parquet Archiving) Pipeline:
   - Optimize memory consumption during the Parquet conversion. Instead of loading all buffered logs into memory at once, stream logs in chunks using `pyarrow.parquet.ParquetWriter`.
   - Implement snappy or zstd compression on the Parquet file to optimize GCS storage fees and network transfer times.
   - Use async background tasks (e.g., FastAPI's `BackgroundTasks` or Celery) so that log writing and GCS uploads do not block the active API request-response cycle.

3. Deployment & Cloud Resource Optimization:
   - GCP (Cloud Run): Configure CPU and memory limits. Setup concurrency settings to handle multiple simultaneous requests per container instance, minimizing cold starts.
   - Proxmox (LXC/VM): Design container configuration profiles with appropriate swap space limits, IO limits, and CPU weight parameters.
   - Implement health check endpoints (`/health` and `/ready`) that verify MongoDB and disk storage health for liveness/readiness probes in Proxmox / Google Cloud.

Analyze the microservice code to refactor any synchronous blocking calls to asynchronous alternatives (`async`/`await`). Provide clean, optimized refactoring blocks for index creation, background task logic, and async query executions.
```

---

## User Story 24: Cyber-Fraud Security Agent

**Summary**:
The goal of the Cyber-Fraud Security Agent is to fulfill the story requirements: \"As a proactive Cyber-Fraud Security Agent, I want to correlate cyber, identity, and transaction signals and initiate approved countermeasures so that fraud losses and customer harm are reduced.\". To achieve this, the microservice `cyber-fraud-service` will expose several API endpoints using FastAPI, managing data across MongoDB collections like `fraud_signals`, `fraud_cases`, `campaigns`, `restriction_policies`. Key functionality includes enforcing specific business constraints such as: Implement fraud scoring combining identity risk (IP location changes) and transaction anomalies (unusual amounts). Provide clear reasoning logs explaining automatic account blocks. To ensure audit compliance and regulatory alignment, the microservice captures all decisions in high-performance local MongoDB collections and archives long-term logs to compressed Parquet files, which are securely uploaded to Google Cloud Storage. The microservice is designed for containerized deployment, running on GCP Cloud Run for cloud workflows or within Proxmox LXC containers for localized, secure production environments. Acceptance criteria dictate strict validation, verification checkpoints, and human-in-the-loop approvals for any critical or material actions.

### Implementation Prompt
```markdown
Task: Implement the `cyber-fraud-service` microservice for the 'Cyber-Fraud Security Agent'.

Technology Stack:
- Python
- Modular Microservices Architecture
- FastAPI for the API layer
- MongoDB for the database layer (use PyMongo or Beanie ODM)
- Parquet for long-term log storage (using PyArrow/Pandas)
- Google Cloud (GCS/Cloud Run) for cloud deployment
- Proxmox VE for local virtualization/production deployment

Requirements:
1. Create a structured Python project with FastAPI for the `cyber-fraud-service`:
   - `main.py` - FastAPI app initialization, routes registration, and exception handlers.
   - `config.py` - Pydantic settings loading MongoDB URI, GCP project details, Proxmox configs, and log paths.
   - `models/` - MongoDB schemas mapping the collections: `fraud_signals`, `fraud_cases`, `campaigns`, `restriction_policies`.
   - `routers/` - Clean FastAPI router modules implementing:
          - POST /fraud/correlate - Correlate cyber security, identity verification, and transaction telemetry
     - POST /fraud/cases - Create and update fraud cases (requires evidence, confidence, loss, and affected parties)
     - POST /fraud/campaigns - Share confirmed campaign details with fraud and threat intelligence teams
     - POST /fraud/restrict - Enforce account or transaction restrictions based on approved policies
     - GET /fraud/metrics - Generate outcomes dashboard (prevented loss, speed, false positives, recovery)
   - `services/` - Business logic implementation.
   - `utils/logging.py` - Custom logger logging events to MongoDB for active querying and periodically buffering/writing log events to local Parquet files, with automated upload to Google Cloud Storage.

2. Specific Business Logic:
   - Story: As a proactive Cyber-Fraud Security Agent, I want to correlate cyber, identity, and transaction signals and initiate approved countermeasures so that fraud losses and customer harm are reduced.
   - Custom implementation details: Implement fraud scoring combining identity risk (IP location changes) and transaction anomalies (unusual amounts). Provide clear reasoning logs explaining automatic account blocks.

3. Parquet Logging Pipeline:
   - Configure a background task or worker that runs every hour or when logs reach 1000 records.
   - Buffer raw logs as standard dicts. Format into a Pandas DataFrame or PyArrow Table using a schema representing (timestamp, event_id, event_type, agent_identity, details_json, severity).
   - Write logs locally to a Parquet file (using Snappy compression).
   - Upload the resulting Parquet file to a Google Cloud Storage bucket (e.g., `gs://bank-audit-logs/cyber-fraud-service/YYYY/MM/DD/`) using `google-cloud-storage`.
   - Setup fallback local directory in Proxmox VM storage if GCP is unreachable.

4. Deployment Configuration:
   - Write a `Dockerfile` multi-stage build optimizing dependency size and security (running as non-root user).
   - Write a Google Cloud Build configuration `cloudbuild.yaml` to build the container and deploy to Google Cloud Run with minimum/maximum instances.
   - Write a Proxmox deployment configuration template (e.g., an Ansible playbook or shell script using pct/qm commands) to deploy this microservice as an LXC container or VM.

Ensure the code is modular, fully typed with Python type hints, incorporates proper error handling with FastAPI HTTPExceptions, and includes clear docstrings. Do not use placeholders.
```

### Testing Prompt
```markdown
Task: Write automated tests (unit, integration, and end-to-end) for the `cyber-fraud-service` microservice.

Technology Stack:
- Python (pytest, pytest-asyncio)
- FastAPI (TestClient, httpx.AsyncClient)
- MongoDB (using mongomock or testcontainers-mongodb)
- Parquet & GCS Mocking (using pandas, pyarrow, and mock/unittest.mock)

Testing Requirements:
1. Setup Unit Tests under `tests/unit/`:
   - Mock MongoDB connections and database calls using a fixture.
   - Mock Google Cloud Storage client library to verify GCS uploads.
   - Write unit tests for core helper functions, custom formulas, and validation logic: Implement fraud scoring combining identity risk (IP location changes) and transaction anomalies (unusual amounts). Provide clear reasoning logs explaining automatic account blocks.
   - Verify that log archiving buffers logs correctly and generates a valid Parquet file (read the written file back using pyarrow/pandas and check the schemas match).

2. Setup Integration Tests under `tests/integration/`:
   - Use FastAPI `TestClient` or `httpx.AsyncClient` to call endpoints.
   - Test key routes:
          - POST /fraud/correlate - Correlate cyber security, identity verification, and transaction telemetry
     - POST /fraud/cases - Create and update fraud cases (requires evidence, confidence, loss, and affected parties)
     - POST /fraud/campaigns - Share confirmed campaign details with fraud and threat intelligence teams
     - POST /fraud/restrict - Enforce account or transaction restrictions based on approved policies
     - GET /fraud/metrics - Generate outcomes dashboard (prevented loss, speed, false positives, recovery)
   - Verify the request validation (e.g. invalid schemas return 422 Unprocessable Entity).
   - Assert correct database records are inserted/updated in the mock MongoDB.
   - Test failure modes: database timeout, GCS upload failure (check that fallback local storage works).

3. Setup End-to-End Tests under `tests/e2e/`:
   - Test full workflows (e.g., trigger an action, verify the database state, trigger the log archiver, and check the generated parquet payload).
   - Ensure authentication and role-based access checks (if applicable) are tested.

Write clean, highly structured pytest code utilizing fixtures. Include clean tear-downs to reset the database states and local temp files.
```

### Optimization Prompt
```markdown
Task: Optimize the performance, maintainability, and scalability of the `cyber-fraud-service` microservice.

Areas of Optimization:
1. Database (MongoDB) Performance:
   - Review and implement the index design: Compound index on fraud_signals for (user_id, timestamp) and fraud_cases for (status, confidence).
   - Optimize queries using project filters and pagination to minimize memory usage on large collections.
   - Enforce connection pooling configurations with PyMongo/Beanie, tuning `maxPoolSize`, `minPoolSize`, and `maxIdleTimeMS`.

2. Logging (Parquet Archiving) Pipeline:
   - Optimize memory consumption during the Parquet conversion. Instead of loading all buffered logs into memory at once, stream logs in chunks using `pyarrow.parquet.ParquetWriter`.
   - Implement snappy or zstd compression on the Parquet file to optimize GCS storage fees and network transfer times.
   - Use async background tasks (e.g., FastAPI's `BackgroundTasks` or Celery) so that log writing and GCS uploads do not block the active API request-response cycle.

3. Deployment & Cloud Resource Optimization:
   - GCP (Cloud Run): Configure CPU and memory limits. Setup concurrency settings to handle multiple simultaneous requests per container instance, minimizing cold starts.
   - Proxmox (LXC/VM): Design container configuration profiles with appropriate swap space limits, IO limits, and CPU weight parameters.
   - Implement health check endpoints (`/health` and `/ready`) that verify MongoDB and disk storage health for liveness/readiness probes in Proxmox / Google Cloud.

Analyze the microservice code to refactor any synchronous blocking calls to asynchronous alternatives (`async`/`await`). Provide clean, optimized refactoring blocks for index creation, background task logic, and async query executions.
```

---

## User Story 25: Security Policy, Standards and Documentation Agent

**Summary**:
The goal of the Security Policy, Standards and Documentation Agent is to fulfill the story requirements: \"As a proactive Security Policy, Standards and Documentation Agent, I want to maintain consistent and traceable security documentation so that personnel and agents can apply current requirements correctly.\". To achieve this, the microservice `policy-documentation-service` will expose several API endpoints using FastAPI, managing data across MongoDB collections like `documents`, `change_proposals`, `obsolete_records`, `notifications`. Key functionality includes enforcing specific business constraints such as: Implement semantic similarity or rule-based parsing to cross-reference document clauses and alert on contradictions. Enforce record keeping rules for superseded files. To ensure audit compliance and regulatory alignment, the microservice captures all decisions in high-performance local MongoDB collections and archives long-term logs to compressed Parquet files, which are securely uploaded to Google Cloud Storage. The microservice is designed for containerized deployment, running on GCP Cloud Run for cloud workflows or within Proxmox LXC containers for localized, secure production environments. Acceptance criteria dictate strict validation, verification checkpoints, and human-in-the-loop approvals for any critical or material actions.

### Implementation Prompt
```markdown
Task: Implement the `policy-documentation-service` microservice for the 'Security Policy, Standards and Documentation Agent'.

Technology Stack:
- Python
- Modular Microservices Architecture
- FastAPI for the API layer
- MongoDB for the database layer (use PyMongo or Beanie ODM)
- Parquet for long-term log storage (using PyArrow/Pandas)
- Google Cloud (GCS/Cloud Run) for cloud deployment
- Proxmox VE for local virtualization/production deployment

Requirements:
1. Create a structured Python project with FastAPI for the `policy-documentation-service`:
   - `main.py` - FastAPI app initialization, routes registration, and exception handlers.
   - `config.py` - Pydantic settings loading MongoDB URI, GCP project details, Proxmox configs, and log paths.
   - `models/` - MongoDB schemas mapping the collections: `documents`, `change_proposals`, `obsolete_records`, `notifications`.
   - `routers/` - Clean FastAPI router modules implementing:
          - POST /docs - Create or upload security documentation (with owner, version, classification, review dates)
     - POST /docs/changes - Propose policy changes mapped to regulatory, risk, and control drivers
     - GET /docs/conflicts - Detect conflicting, duplicated, or obsolete requirements
     - POST /docs/publish - Publish approved changes to authorized repositories and notify stakeholders
     - GET /docs/history - Retrieve superseded versions and archive records
   - `services/` - Business logic implementation.
   - `utils/logging.py` - Custom logger logging events to MongoDB for active querying and periodically buffering/writing log events to local Parquet files, with automated upload to Google Cloud Storage.

2. Specific Business Logic:
   - Story: As a proactive Security Policy, Standards and Documentation Agent, I want to maintain consistent and traceable security documentation so that personnel and agents can apply current requirements correctly.
   - Custom implementation details: Implement semantic similarity or rule-based parsing to cross-reference document clauses and alert on contradictions. Enforce record keeping rules for superseded files.

3. Parquet Logging Pipeline:
   - Configure a background task or worker that runs every hour or when logs reach 1000 records.
   - Buffer raw logs as standard dicts. Format into a Pandas DataFrame or PyArrow Table using a schema representing (timestamp, event_id, event_type, agent_identity, details_json, severity).
   - Write logs locally to a Parquet file (using Snappy compression).
   - Upload the resulting Parquet file to a Google Cloud Storage bucket (e.g., `gs://bank-audit-logs/policy-documentation-service/YYYY/MM/DD/`) using `google-cloud-storage`.
   - Setup fallback local directory in Proxmox VM storage if GCP is unreachable.

4. Deployment Configuration:
   - Write a `Dockerfile` multi-stage build optimizing dependency size and security (running as non-root user).
   - Write a Google Cloud Build configuration `cloudbuild.yaml` to build the container and deploy to Google Cloud Run with minimum/maximum instances.
   - Write a Proxmox deployment configuration template (e.g., an Ansible playbook or shell script using pct/qm commands) to deploy this microservice as an LXC container or VM.

Ensure the code is modular, fully typed with Python type hints, incorporates proper error handling with FastAPI HTTPExceptions, and includes clear docstrings. Do not use placeholders.
```

### Testing Prompt
```markdown
Task: Write automated tests (unit, integration, and end-to-end) for the `policy-documentation-service` microservice.

Technology Stack:
- Python (pytest, pytest-asyncio)
- FastAPI (TestClient, httpx.AsyncClient)
- MongoDB (using mongomock or testcontainers-mongodb)
- Parquet & GCS Mocking (using pandas, pyarrow, and mock/unittest.mock)

Testing Requirements:
1. Setup Unit Tests under `tests/unit/`:
   - Mock MongoDB connections and database calls using a fixture.
   - Mock Google Cloud Storage client library to verify GCS uploads.
   - Write unit tests for core helper functions, custom formulas, and validation logic: Implement semantic similarity or rule-based parsing to cross-reference document clauses and alert on contradictions. Enforce record keeping rules for superseded files.
   - Verify that log archiving buffers logs correctly and generates a valid Parquet file (read the written file back using pyarrow/pandas and check the schemas match).

2. Setup Integration Tests under `tests/integration/`:
   - Use FastAPI `TestClient` or `httpx.AsyncClient` to call endpoints.
   - Test key routes:
          - POST /docs - Create or upload security documentation (with owner, version, classification, review dates)
     - POST /docs/changes - Propose policy changes mapped to regulatory, risk, and control drivers
     - GET /docs/conflicts - Detect conflicting, duplicated, or obsolete requirements
     - POST /docs/publish - Publish approved changes to authorized repositories and notify stakeholders
     - GET /docs/history - Retrieve superseded versions and archive records
   - Verify the request validation (e.g. invalid schemas return 422 Unprocessable Entity).
   - Assert correct database records are inserted/updated in the mock MongoDB.
   - Test failure modes: database timeout, GCS upload failure (check that fallback local storage works).

3. Setup End-to-End Tests under `tests/e2e/`:
   - Test full workflows (e.g., trigger an action, verify the database state, trigger the log archiver, and check the generated parquet payload).
   - Ensure authentication and role-based access checks (if applicable) are tested.

Write clean, highly structured pytest code utilizing fixtures. Include clean tear-downs to reset the database states and local temp files.
```

### Optimization Prompt
```markdown
Task: Optimize the performance, maintainability, and scalability of the `policy-documentation-service` microservice.

Areas of Optimization:
1. Database (MongoDB) Performance:
   - Review and implement the index design: Index on documents (title, version, status) and change_proposals (status, review_date).
   - Optimize queries using project filters and pagination to minimize memory usage on large collections.
   - Enforce connection pooling configurations with PyMongo/Beanie, tuning `maxPoolSize`, `minPoolSize`, and `maxIdleTimeMS`.

2. Logging (Parquet Archiving) Pipeline:
   - Optimize memory consumption during the Parquet conversion. Instead of loading all buffered logs into memory at once, stream logs in chunks using `pyarrow.parquet.ParquetWriter`.
   - Implement snappy or zstd compression on the Parquet file to optimize GCS storage fees and network transfer times.
   - Use async background tasks (e.g., FastAPI's `BackgroundTasks` or Celery) so that log writing and GCS uploads do not block the active API request-response cycle.

3. Deployment & Cloud Resource Optimization:
   - GCP (Cloud Run): Configure CPU and memory limits. Setup concurrency settings to handle multiple simultaneous requests per container instance, minimizing cold starts.
   - Proxmox (LXC/VM): Design container configuration profiles with appropriate swap space limits, IO limits, and CPU weight parameters.
   - Implement health check endpoints (`/health` and `/ready`) that verify MongoDB and disk storage health for liveness/readiness probes in Proxmox / Google Cloud.

Analyze the microservice code to refactor any synchronous blocking calls to asynchronous alternatives (`async`/`await`). Provide clean, optimized refactoring blocks for index creation, background task logic, and async query executions.
```

---

## User Story 26: Security Programme and Portfolio Management Agent

**Summary**:
The goal of the Security Programme and Portfolio Management Agent is to fulfill the story requirements: \"As a proactive Security Programme and Portfolio Management Agent, I want to prioritise and track security investments and delivery so that resources produce measurable risk reduction and regulatory value.\". To achieve this, the microservice `portfolio-management-service` will expose several API endpoints using FastAPI, managing data across MongoDB collections like `initiatives`, `rankings`, `forecasts`, `portfolio_reports`. Key functionality includes enforcing specific business constraints such as: Implement prioritization algorithm (e.g., WSJF or Weighted Scoring Model). Build forecast modeling tool using historical delivery rates to flag milestone slip risks. To ensure audit compliance and regulatory alignment, the microservice captures all decisions in high-performance local MongoDB collections and archives long-term logs to compressed Parquet files, which are securely uploaded to Google Cloud Storage. The microservice is designed for containerized deployment, running on GCP Cloud Run for cloud workflows or within Proxmox LXC containers for localized, secure production environments. Acceptance criteria dictate strict validation, verification checkpoints, and human-in-the-loop approvals for any critical or material actions.

### Implementation Prompt
```markdown
Task: Implement the `portfolio-management-service` microservice for the 'Security Programme and Portfolio Management Agent'.

Technology Stack:
- Python
- Modular Microservices Architecture
- FastAPI for the API layer
- MongoDB for the database layer (use PyMongo or Beanie ODM)
- Parquet for long-term log storage (using PyArrow/Pandas)
- Google Cloud (GCS/Cloud Run) for cloud deployment
- Proxmox VE for local virtualization/production deployment

Requirements:
1. Create a structured Python project with FastAPI for the `portfolio-management-service`:
   - `main.py` - FastAPI app initialization, routes registration, and exception handlers.
   - `config.py` - Pydantic settings loading MongoDB URI, GCP project details, Proxmox configs, and log paths.
   - `models/` - MongoDB schemas mapping the collections: `initiatives`, `rankings`, `forecasts`, `portfolio_reports`.
   - `routers/` - Clean FastAPI router modules implementing:
          - POST /portfolio/initiatives - Create and track security initiatives (owner, scope, milestones, budget, risks, targets)
     - POST /portfolio/rank - Rank initiatives using risk reduction, regulatory urgency, dependencies, and cost-benefit
     - GET /portfolio/deviations - Track delivery schedule and budget deviations early
     - POST /portfolio/forecast - Project portfolio performance using capacity, financial, and delivery metrics
     - GET /portfolio/report - Generate portfolio health report displaying expenditure, progress, and residual risk
   - `services/` - Business logic implementation.
   - `utils/logging.py` - Custom logger logging events to MongoDB for active querying and periodically buffering/writing log events to local Parquet files, with automated upload to Google Cloud Storage.

2. Specific Business Logic:
   - Story: As a proactive Security Programme and Portfolio Management Agent, I want to prioritise and track security investments and delivery so that resources produce measurable risk reduction and regulatory value.
   - Custom implementation details: Implement prioritization algorithm (e.g., WSJF or Weighted Scoring Model). Build forecast modeling tool using historical delivery rates to flag milestone slip risks.

3. Parquet Logging Pipeline:
   - Configure a background task or worker that runs every hour or when logs reach 1000 records.
   - Buffer raw logs as standard dicts. Format into a Pandas DataFrame or PyArrow Table using a schema representing (timestamp, event_id, event_type, agent_identity, details_json, severity).
   - Write logs locally to a Parquet file (using Snappy compression).
   - Upload the resulting Parquet file to a Google Cloud Storage bucket (e.g., `gs://bank-audit-logs/portfolio-management-service/YYYY/MM/DD/`) using `google-cloud-storage`.
   - Setup fallback local directory in Proxmox VM storage if GCP is unreachable.

4. Deployment Configuration:
   - Write a `Dockerfile` multi-stage build optimizing dependency size and security (running as non-root user).
   - Write a Google Cloud Build configuration `cloudbuild.yaml` to build the container and deploy to Google Cloud Run with minimum/maximum instances.
   - Write a Proxmox deployment configuration template (e.g., an Ansible playbook or shell script using pct/qm commands) to deploy this microservice as an LXC container or VM.

Ensure the code is modular, fully typed with Python type hints, incorporates proper error handling with FastAPI HTTPExceptions, and includes clear docstrings. Do not use placeholders.
```

### Testing Prompt
```markdown
Task: Write automated tests (unit, integration, and end-to-end) for the `portfolio-management-service` microservice.

Technology Stack:
- Python (pytest, pytest-asyncio)
- FastAPI (TestClient, httpx.AsyncClient)
- MongoDB (using mongomock or testcontainers-mongodb)
- Parquet & GCS Mocking (using pandas, pyarrow, and mock/unittest.mock)

Testing Requirements:
1. Setup Unit Tests under `tests/unit/`:
   - Mock MongoDB connections and database calls using a fixture.
   - Mock Google Cloud Storage client library to verify GCS uploads.
   - Write unit tests for core helper functions, custom formulas, and validation logic: Implement prioritization algorithm (e.g., WSJF or Weighted Scoring Model). Build forecast modeling tool using historical delivery rates to flag milestone slip risks.
   - Verify that log archiving buffers logs correctly and generates a valid Parquet file (read the written file back using pyarrow/pandas and check the schemas match).

2. Setup Integration Tests under `tests/integration/`:
   - Use FastAPI `TestClient` or `httpx.AsyncClient` to call endpoints.
   - Test key routes:
          - POST /portfolio/initiatives - Create and track security initiatives (owner, scope, milestones, budget, risks, targets)
     - POST /portfolio/rank - Rank initiatives using risk reduction, regulatory urgency, dependencies, and cost-benefit
     - GET /portfolio/deviations - Track delivery schedule and budget deviations early
     - POST /portfolio/forecast - Project portfolio performance using capacity, financial, and delivery metrics
     - GET /portfolio/report - Generate portfolio health report displaying expenditure, progress, and residual risk
   - Verify the request validation (e.g. invalid schemas return 422 Unprocessable Entity).
   - Assert correct database records are inserted/updated in the mock MongoDB.
   - Test failure modes: database timeout, GCS upload failure (check that fallback local storage works).

3. Setup End-to-End Tests under `tests/e2e/`:
   - Test full workflows (e.g., trigger an action, verify the database state, trigger the log archiver, and check the generated parquet payload).
   - Ensure authentication and role-based access checks (if applicable) are tested.

Write clean, highly structured pytest code utilizing fixtures. Include clean tear-downs to reset the database states and local temp files.
```

### Optimization Prompt
```markdown
Task: Optimize the performance, maintainability, and scalability of the `portfolio-management-service` microservice.

Areas of Optimization:
1. Database (MongoDB) Performance:
   - Review and implement the index design: Index on initiatives (status, owner) and rankings (initiative_id, score).
   - Optimize queries using project filters and pagination to minimize memory usage on large collections.
   - Enforce connection pooling configurations with PyMongo/Beanie, tuning `maxPoolSize`, `minPoolSize`, and `maxIdleTimeMS`.

2. Logging (Parquet Archiving) Pipeline:
   - Optimize memory consumption during the Parquet conversion. Instead of loading all buffered logs into memory at once, stream logs in chunks using `pyarrow.parquet.ParquetWriter`.
   - Implement snappy or zstd compression on the Parquet file to optimize GCS storage fees and network transfer times.
   - Use async background tasks (e.g., FastAPI's `BackgroundTasks` or Celery) so that log writing and GCS uploads do not block the active API request-response cycle.

3. Deployment & Cloud Resource Optimization:
   - GCP (Cloud Run): Configure CPU and memory limits. Setup concurrency settings to handle multiple simultaneous requests per container instance, minimizing cold starts.
   - Proxmox (LXC/VM): Design container configuration profiles with appropriate swap space limits, IO limits, and CPU weight parameters.
   - Implement health check endpoints (`/health` and `/ready`) that verify MongoDB and disk storage health for liveness/readiness probes in Proxmox / Google Cloud.

Analyze the microservice code to refactor any synchronous blocking calls to asynchronous alternatives (`async`/`await`). Provide clean, optimized refactoring blocks for index creation, background task logic, and async query executions.
```

---

## User Story 27: Security Research, Innovation and Emerging Technology Agent

**Summary**:
The goal of the Security Research, Innovation and Emerging Technology Agent is to fulfill the story requirements: \"As a proactive Security Research, Innovation and Emerging Technology Agent, I want to evaluate emerging threats and defensive technologies so that the bank can adopt useful innovations without introducing unmanaged risk.\". To achieve this, the microservice `security-research-service` will expose several API endpoints using FastAPI, managing data across MongoDB collections like `research_topics`, `evaluations`, `poc_environments`, `recommendations`. Key functionality includes enforcing specific business constraints such as: Automate provisioning of sandboxed VMs or LXCs on Proxmox for PoCs. Prevent ingestion of production or customer data inside sandbox environments via strict firewall and policy validations. To ensure audit compliance and regulatory alignment, the microservice captures all decisions in high-performance local MongoDB collections and archives long-term logs to compressed Parquet files, which are securely uploaded to Google Cloud Storage. The microservice is designed for containerized deployment, running on GCP Cloud Run for cloud workflows or within Proxmox LXC containers for localized, secure production environments. Acceptance criteria dictate strict validation, verification checkpoints, and human-in-the-loop approvals for any critical or material actions.

### Implementation Prompt
```markdown
Task: Implement the `security-research-service` microservice for the 'Security Research, Innovation and Emerging Technology Agent'.

Technology Stack:
- Python
- Modular Microservices Architecture
- FastAPI for the API layer
- MongoDB for the database layer (use PyMongo or Beanie ODM)
- Parquet for long-term log storage (using PyArrow/Pandas)
- Google Cloud (GCS/Cloud Run) for cloud deployment
- Proxmox VE for local virtualization/production deployment

Requirements:
1. Create a structured Python project with FastAPI for the `security-research-service`:
   - `main.py` - FastAPI app initialization, routes registration, and exception handlers.
   - `config.py` - Pydantic settings loading MongoDB URI, GCP project details, Proxmox configs, and log paths.
   - `models/` - MongoDB schemas mapping the collections: `research_topics`, `evaluations`, `poc_environments`, `recommendations`.
   - `routers/` - Clean FastAPI router modules implementing:
          - POST /research/topics - Prioritize and track research topics by relevance and business impact
     - POST /research/evaluations - Document security, privacy, compliance, operational, and financial evaluations
     - POST /research/poc - Spin up proofs of concept in isolated, approved sandbox environments
     - POST /research/recommendations - Generate technology adoption criteria, benefits, risks, and limitations
     - POST /research/roadmaps - Update relevant risk, architecture, and control roadmaps with findings
   - `services/` - Business logic implementation.
   - `utils/logging.py` - Custom logger logging events to MongoDB for active querying and periodically buffering/writing log events to local Parquet files, with automated upload to Google Cloud Storage.

2. Specific Business Logic:
   - Story: As a proactive Security Research, Innovation and Emerging Technology Agent, I want to evaluate emerging threats and defensive technologies so that the bank can adopt useful innovations without introducing unmanaged risk.
   - Custom implementation details: Automate provisioning of sandboxed VMs or LXCs on Proxmox for PoCs. Prevent ingestion of production or customer data inside sandbox environments via strict firewall and policy validations.

3. Parquet Logging Pipeline:
   - Configure a background task or worker that runs every hour or when logs reach 1000 records.
   - Buffer raw logs as standard dicts. Format into a Pandas DataFrame or PyArrow Table using a schema representing (timestamp, event_id, event_type, agent_identity, details_json, severity).
   - Write logs locally to a Parquet file (using Snappy compression).
   - Upload the resulting Parquet file to a Google Cloud Storage bucket (e.g., `gs://bank-audit-logs/security-research-service/YYYY/MM/DD/`) using `google-cloud-storage`.
   - Setup fallback local directory in Proxmox VM storage if GCP is unreachable.

4. Deployment Configuration:
   - Write a `Dockerfile` multi-stage build optimizing dependency size and security (running as non-root user).
   - Write a Google Cloud Build configuration `cloudbuild.yaml` to build the container and deploy to Google Cloud Run with minimum/maximum instances.
   - Write a Proxmox deployment configuration template (e.g., an Ansible playbook or shell script using pct/qm commands) to deploy this microservice as an LXC container or VM.

Ensure the code is modular, fully typed with Python type hints, incorporates proper error handling with FastAPI HTTPExceptions, and includes clear docstrings. Do not use placeholders.
```

### Testing Prompt
```markdown
Task: Write automated tests (unit, integration, and end-to-end) for the `security-research-service` microservice.

Technology Stack:
- Python (pytest, pytest-asyncio)
- FastAPI (TestClient, httpx.AsyncClient)
- MongoDB (using mongomock or testcontainers-mongodb)
- Parquet & GCS Mocking (using pandas, pyarrow, and mock/unittest.mock)

Testing Requirements:
1. Setup Unit Tests under `tests/unit/`:
   - Mock MongoDB connections and database calls using a fixture.
   - Mock Google Cloud Storage client library to verify GCS uploads.
   - Write unit tests for core helper functions, custom formulas, and validation logic: Automate provisioning of sandboxed VMs or LXCs on Proxmox for PoCs. Prevent ingestion of production or customer data inside sandbox environments via strict firewall and policy validations.
   - Verify that log archiving buffers logs correctly and generates a valid Parquet file (read the written file back using pyarrow/pandas and check the schemas match).

2. Setup Integration Tests under `tests/integration/`:
   - Use FastAPI `TestClient` or `httpx.AsyncClient` to call endpoints.
   - Test key routes:
          - POST /research/topics - Prioritize and track research topics by relevance and business impact
     - POST /research/evaluations - Document security, privacy, compliance, operational, and financial evaluations
     - POST /research/poc - Spin up proofs of concept in isolated, approved sandbox environments
     - POST /research/recommendations - Generate technology adoption criteria, benefits, risks, and limitations
     - POST /research/roadmaps - Update relevant risk, architecture, and control roadmaps with findings
   - Verify the request validation (e.g. invalid schemas return 422 Unprocessable Entity).
   - Assert correct database records are inserted/updated in the mock MongoDB.
   - Test failure modes: database timeout, GCS upload failure (check that fallback local storage works).

3. Setup End-to-End Tests under `tests/e2e/`:
   - Test full workflows (e.g., trigger an action, verify the database state, trigger the log archiver, and check the generated parquet payload).
   - Ensure authentication and role-based access checks (if applicable) are tested.

Write clean, highly structured pytest code utilizing fixtures. Include clean tear-downs to reset the database states and local temp files.
```

### Optimization Prompt
```markdown
Task: Optimize the performance, maintainability, and scalability of the `security-research-service` microservice.

Areas of Optimization:
1. Database (MongoDB) Performance:
   - Review and implement the index design: Index on research_topics (status, priority) and evaluations (technology_name, overall_score).
   - Optimize queries using project filters and pagination to minimize memory usage on large collections.
   - Enforce connection pooling configurations with PyMongo/Beanie, tuning `maxPoolSize`, `minPoolSize`, and `maxIdleTimeMS`.

2. Logging (Parquet Archiving) Pipeline:
   - Optimize memory consumption during the Parquet conversion. Instead of loading all buffered logs into memory at once, stream logs in chunks using `pyarrow.parquet.ParquetWriter`.
   - Implement snappy or zstd compression on the Parquet file to optimize GCS storage fees and network transfer times.
   - Use async background tasks (e.g., FastAPI's `BackgroundTasks` or Celery) so that log writing and GCS uploads do not block the active API request-response cycle.

3. Deployment & Cloud Resource Optimization:
   - GCP (Cloud Run): Configure CPU and memory limits. Setup concurrency settings to handle multiple simultaneous requests per container instance, minimizing cold starts.
   - Proxmox (LXC/VM): Design container configuration profiles with appropriate swap space limits, IO limits, and CPU weight parameters.
   - Implement health check endpoints (`/health` and `/ready`) that verify MongoDB and disk storage health for liveness/readiness probes in Proxmox / Google Cloud.

Analyze the microservice code to refactor any synchronous blocking calls to asynchronous alternatives (`async`/`await`). Provide clean, optimized refactoring blocks for index creation, background task logic, and async query executions.
```

---

## User Story 28: Physical and Environmental Security Coordination Agent

**Summary**:
The goal of the Physical and Environmental Security Coordination Agent is to fulfill the story requirements: \"As a proactive Physical and Environmental Security Coordination Agent, I want to correlate physical, environmental, and cyber events so that threats to critical facilities and technology are identified and addressed promptly.\". To achieve this, the microservice `physical-security-service` will expose several API endpoints using FastAPI, managing data across MongoDB collections like `physical_events`, `anomalous_alerts`, `emergency_records`, `evidence_metadata`. Key functionality includes enforcing specific business constraints such as: Build correlation rules connecting badging events with network logins (e.g., alert if user logs into PC in City A while badging in City B). Audit physical evidence handovers. To ensure audit compliance and regulatory alignment, the microservice captures all decisions in high-performance local MongoDB collections and archives long-term logs to compressed Parquet files, which are securely uploaded to Google Cloud Storage. The microservice is designed for containerized deployment, running on GCP Cloud Run for cloud workflows or within Proxmox LXC containers for localized, secure production environments. Acceptance criteria dictate strict validation, verification checkpoints, and human-in-the-loop approvals for any critical or material actions.

### Implementation Prompt
```markdown
Task: Implement the `physical-security-service` microservice for the 'Physical and Environmental Security Coordination Agent'.

Technology Stack:
- Python
- Modular Microservices Architecture
- FastAPI for the API layer
- MongoDB for the database layer (use PyMongo or Beanie ODM)
- Parquet for long-term log storage (using PyArrow/Pandas)
- Google Cloud (GCS/Cloud Run) for cloud deployment
- Proxmox VE for local virtualization/production deployment

Requirements:
1. Create a structured Python project with FastAPI for the `physical-security-service`:
   - `main.py` - FastAPI app initialization, routes registration, and exception handlers.
   - `config.py` - Pydantic settings loading MongoDB URI, GCP project details, Proxmox configs, and log paths.
   - `models/` - MongoDB schemas mapping the collections: `physical_events`, `anomalous_alerts`, `emergency_records`, `evidence_metadata`.
   - `routers/` - Clean FastAPI router modules implementing:
          - POST /physical/events - Ingest facility access, environmental (temp/water), ATM, and physical security logs
     - POST /physical/correlate - Correlate physical access events with cyber events and generate anomalous access alerts
     - POST /physical/emergency - Trigger emergency actions and safety procedures (e.g. lockdowns, alerts)
     - POST /physical/evidence - Preserve and share physical evidence only with authorized personnel
     - GET /physical/coordination - Retrieve coordination status with Corporate Security and Facilities
   - `services/` - Business logic implementation.
   - `utils/logging.py` - Custom logger logging events to MongoDB for active querying and periodically buffering/writing log events to local Parquet files, with automated upload to Google Cloud Storage.

2. Specific Business Logic:
   - Story: As a proactive Physical and Environmental Security Coordination Agent, I want to correlate physical, environmental, and cyber events so that threats to critical facilities and technology are identified and addressed promptly.
   - Custom implementation details: Build correlation rules connecting badging events with network logins (e.g., alert if user logs into PC in City A while badging in City B). Audit physical evidence handovers.

3. Parquet Logging Pipeline:
   - Configure a background task or worker that runs every hour or when logs reach 1000 records.
   - Buffer raw logs as standard dicts. Format into a Pandas DataFrame or PyArrow Table using a schema representing (timestamp, event_id, event_type, agent_identity, details_json, severity).
   - Write logs locally to a Parquet file (using Snappy compression).
   - Upload the resulting Parquet file to a Google Cloud Storage bucket (e.g., `gs://bank-audit-logs/physical-security-service/YYYY/MM/DD/`) using `google-cloud-storage`.
   - Setup fallback local directory in Proxmox VM storage if GCP is unreachable.

4. Deployment Configuration:
   - Write a `Dockerfile` multi-stage build optimizing dependency size and security (running as non-root user).
   - Write a Google Cloud Build configuration `cloudbuild.yaml` to build the container and deploy to Google Cloud Run with minimum/maximum instances.
   - Write a Proxmox deployment configuration template (e.g., an Ansible playbook or shell script using pct/qm commands) to deploy this microservice as an LXC container or VM.

Ensure the code is modular, fully typed with Python type hints, incorporates proper error handling with FastAPI HTTPExceptions, and includes clear docstrings. Do not use placeholders.
```

### Testing Prompt
```markdown
Task: Write automated tests (unit, integration, and end-to-end) for the `physical-security-service` microservice.

Technology Stack:
- Python (pytest, pytest-asyncio)
- FastAPI (TestClient, httpx.AsyncClient)
- MongoDB (using mongomock or testcontainers-mongodb)
- Parquet & GCS Mocking (using pandas, pyarrow, and mock/unittest.mock)

Testing Requirements:
1. Setup Unit Tests under `tests/unit/`:
   - Mock MongoDB connections and database calls using a fixture.
   - Mock Google Cloud Storage client library to verify GCS uploads.
   - Write unit tests for core helper functions, custom formulas, and validation logic: Build correlation rules connecting badging events with network logins (e.g., alert if user logs into PC in City A while badging in City B). Audit physical evidence handovers.
   - Verify that log archiving buffers logs correctly and generates a valid Parquet file (read the written file back using pyarrow/pandas and check the schemas match).

2. Setup Integration Tests under `tests/integration/`:
   - Use FastAPI `TestClient` or `httpx.AsyncClient` to call endpoints.
   - Test key routes:
          - POST /physical/events - Ingest facility access, environmental (temp/water), ATM, and physical security logs
     - POST /physical/correlate - Correlate physical access events with cyber events and generate anomalous access alerts
     - POST /physical/emergency - Trigger emergency actions and safety procedures (e.g. lockdowns, alerts)
     - POST /physical/evidence - Preserve and share physical evidence only with authorized personnel
     - GET /physical/coordination - Retrieve coordination status with Corporate Security and Facilities
   - Verify the request validation (e.g. invalid schemas return 422 Unprocessable Entity).
   - Assert correct database records are inserted/updated in the mock MongoDB.
   - Test failure modes: database timeout, GCS upload failure (check that fallback local storage works).

3. Setup End-to-End Tests under `tests/e2e/`:
   - Test full workflows (e.g., trigger an action, verify the database state, trigger the log archiver, and check the generated parquet payload).
   - Ensure authentication and role-based access checks (if applicable) are tested.

Write clean, highly structured pytest code utilizing fixtures. Include clean tear-downs to reset the database states and local temp files.
```

### Optimization Prompt
```markdown
Task: Optimize the performance, maintainability, and scalability of the `physical-security-service` microservice.

Areas of Optimization:
1. Database (MongoDB) Performance:
   - Review and implement the index design: Compound index on physical_events for (location, timestamp) and (badge_id, timestamp).
   - Optimize queries using project filters and pagination to minimize memory usage on large collections.
   - Enforce connection pooling configurations with PyMongo/Beanie, tuning `maxPoolSize`, `minPoolSize`, and `maxIdleTimeMS`.

2. Logging (Parquet Archiving) Pipeline:
   - Optimize memory consumption during the Parquet conversion. Instead of loading all buffered logs into memory at once, stream logs in chunks using `pyarrow.parquet.ParquetWriter`.
   - Implement snappy or zstd compression on the Parquet file to optimize GCS storage fees and network transfer times.
   - Use async background tasks (e.g., FastAPI's `BackgroundTasks` or Celery) so that log writing and GCS uploads do not block the active API request-response cycle.

3. Deployment & Cloud Resource Optimization:
   - GCP (Cloud Run): Configure CPU and memory limits. Setup concurrency settings to handle multiple simultaneous requests per container instance, minimizing cold starts.
   - Proxmox (LXC/VM): Design container configuration profiles with appropriate swap space limits, IO limits, and CPU weight parameters.
   - Implement health check endpoints (`/health` and `/ready`) that verify MongoDB and disk storage health for liveness/readiness probes in Proxmox / Google Cloud.

Analyze the microservice code to refactor any synchronous blocking calls to asynchronous alternatives (`async`/`await`). Provide clean, optimized refactoring blocks for index creation, background task logic, and async query executions.
```

---

## User Story 29: Information Security Business Partnership Agent

**Summary**:
The goal of the Information Security Business Partnership Agent is to fulfill the story requirements: \"As a proactive Information Security Business Partnership Agent, I want to engage business units and advise their initiatives so that security risks are understood and managed without unnecessary delivery delays.\". To achieve this, the microservice `business-partnership-service` will expose several API endpoints using FastAPI, managing data across MongoDB collections like `business_projects`, `consultations`, `routings`, `tracking_actions`. Key functionality includes enforcing specific business constraints such as: Implement automated routing matrix checking keywords (e.g. 'payment' routes to Payment Agent, 'cloud' routes to Cloud Agent). Measure SLA response times of specialist agents. To ensure audit compliance and regulatory alignment, the microservice captures all decisions in high-performance local MongoDB collections and archives long-term logs to compressed Parquet files, which are securely uploaded to Google Cloud Storage. The microservice is designed for containerized deployment, running on GCP Cloud Run for cloud workflows or within Proxmox LXC containers for localized, secure production environments. Acceptance criteria dictate strict validation, verification checkpoints, and human-in-the-loop approvals for any critical or material actions.

### Implementation Prompt
```markdown
Task: Implement the `business-partnership-service` microservice for the 'Information Security Business Partnership Agent'.

Technology Stack:
- Python
- Modular Microservices Architecture
- FastAPI for the API layer
- MongoDB for the database layer (use PyMongo or Beanie ODM)
- Parquet for long-term log storage (using PyArrow/Pandas)
- Google Cloud (GCS/Cloud Run) for cloud deployment
- Proxmox VE for local virtualization/production deployment

Requirements:
1. Create a structured Python project with FastAPI for the `business-partnership-service`:
   - `main.py` - FastAPI app initialization, routes registration, and exception handlers.
   - `config.py` - Pydantic settings loading MongoDB URI, GCP project details, Proxmox configs, and log paths.
   - `models/` - MongoDB schemas mapping the collections: `business_projects`, `consultations`, `routings`, `tracking_actions`.
   - `routers/` - Clean FastAPI router modules implementing:
          - POST /bp/initiatives - Screen business initiatives for security involvement using defined criteria
     - POST /bp/advise - Express initiative security risks in business, customer, financial, and regulatory terms
     - POST /bp/route - Route requests to correct specialist agents
     - POST /bp/track - Track security decisions, actions, exceptions, and owners for business projects
     - POST /bp/escalate - Escalate unresolved high-risk business matters
   - `services/` - Business logic implementation.
   - `utils/logging.py` - Custom logger logging events to MongoDB for active querying and periodically buffering/writing log events to local Parquet files, with automated upload to Google Cloud Storage.

2. Specific Business Logic:
   - Story: As a proactive Information Security Business Partnership Agent, I want to engage business units and advise their initiatives so that security risks are understood and managed without unnecessary delivery delays.
   - Custom implementation details: Implement automated routing matrix checking keywords (e.g. 'payment' routes to Payment Agent, 'cloud' routes to Cloud Agent). Measure SLA response times of specialist agents.

3. Parquet Logging Pipeline:
   - Configure a background task or worker that runs every hour or when logs reach 1000 records.
   - Buffer raw logs as standard dicts. Format into a Pandas DataFrame or PyArrow Table using a schema representing (timestamp, event_id, event_type, agent_identity, details_json, severity).
   - Write logs locally to a Parquet file (using Snappy compression).
   - Upload the resulting Parquet file to a Google Cloud Storage bucket (e.g., `gs://bank-audit-logs/business-partnership-service/YYYY/MM/DD/`) using `google-cloud-storage`.
   - Setup fallback local directory in Proxmox VM storage if GCP is unreachable.

4. Deployment Configuration:
   - Write a `Dockerfile` multi-stage build optimizing dependency size and security (running as non-root user).
   - Write a Google Cloud Build configuration `cloudbuild.yaml` to build the container and deploy to Google Cloud Run with minimum/maximum instances.
   - Write a Proxmox deployment configuration template (e.g., an Ansible playbook or shell script using pct/qm commands) to deploy this microservice as an LXC container or VM.

Ensure the code is modular, fully typed with Python type hints, incorporates proper error handling with FastAPI HTTPExceptions, and includes clear docstrings. Do not use placeholders.
```

### Testing Prompt
```markdown
Task: Write automated tests (unit, integration, and end-to-end) for the `business-partnership-service` microservice.

Technology Stack:
- Python (pytest, pytest-asyncio)
- FastAPI (TestClient, httpx.AsyncClient)
- MongoDB (using mongomock or testcontainers-mongodb)
- Parquet & GCS Mocking (using pandas, pyarrow, and mock/unittest.mock)

Testing Requirements:
1. Setup Unit Tests under `tests/unit/`:
   - Mock MongoDB connections and database calls using a fixture.
   - Mock Google Cloud Storage client library to verify GCS uploads.
   - Write unit tests for core helper functions, custom formulas, and validation logic: Implement automated routing matrix checking keywords (e.g. 'payment' routes to Payment Agent, 'cloud' routes to Cloud Agent). Measure SLA response times of specialist agents.
   - Verify that log archiving buffers logs correctly and generates a valid Parquet file (read the written file back using pyarrow/pandas and check the schemas match).

2. Setup Integration Tests under `tests/integration/`:
   - Use FastAPI `TestClient` or `httpx.AsyncClient` to call endpoints.
   - Test key routes:
          - POST /bp/initiatives - Screen business initiatives for security involvement using defined criteria
     - POST /bp/advise - Express initiative security risks in business, customer, financial, and regulatory terms
     - POST /bp/route - Route requests to correct specialist agents
     - POST /bp/track - Track security decisions, actions, exceptions, and owners for business projects
     - POST /bp/escalate - Escalate unresolved high-risk business matters
   - Verify the request validation (e.g. invalid schemas return 422 Unprocessable Entity).
   - Assert correct database records are inserted/updated in the mock MongoDB.
   - Test failure modes: database timeout, GCS upload failure (check that fallback local storage works).

3. Setup End-to-End Tests under `tests/e2e/`:
   - Test full workflows (e.g., trigger an action, verify the database state, trigger the log archiver, and check the generated parquet payload).
   - Ensure authentication and role-based access checks (if applicable) are tested.

Write clean, highly structured pytest code utilizing fixtures. Include clean tear-downs to reset the database states and local temp files.
```

### Optimization Prompt
```markdown
Task: Optimize the performance, maintainability, and scalability of the `business-partnership-service` microservice.

Areas of Optimization:
1. Database (MongoDB) Performance:
   - Review and implement the index design: Index on business_projects (business_unit, status) and consultations (project_id, status).
   - Optimize queries using project filters and pagination to minimize memory usage on large collections.
   - Enforce connection pooling configurations with PyMongo/Beanie, tuning `maxPoolSize`, `minPoolSize`, and `maxIdleTimeMS`.

2. Logging (Parquet Archiving) Pipeline:
   - Optimize memory consumption during the Parquet conversion. Instead of loading all buffered logs into memory at once, stream logs in chunks using `pyarrow.parquet.ParquetWriter`.
   - Implement snappy or zstd compression on the Parquet file to optimize GCS storage fees and network transfer times.
   - Use async background tasks (e.g., FastAPI's `BackgroundTasks` or Celery) so that log writing and GCS uploads do not block the active API request-response cycle.

3. Deployment & Cloud Resource Optimization:
   - GCP (Cloud Run): Configure CPU and memory limits. Setup concurrency settings to handle multiple simultaneous requests per container instance, minimizing cold starts.
   - Proxmox (LXC/VM): Design container configuration profiles with appropriate swap space limits, IO limits, and CPU weight parameters.
   - Implement health check endpoints (`/health` and `/ready`) that verify MongoDB and disk storage health for liveness/readiness probes in Proxmox / Google Cloud.

Analyze the microservice code to refactor any synchronous blocking calls to asynchronous alternatives (`async`/`await`). Provide clean, optimized refactoring blocks for index creation, background task logic, and async query executions.
```

---

## User Story 30: CISO Office Agent

**Summary**:
The goal of the CISO Office Agent is to fulfill the story requirements: \"As a proactive CISO Office Agent, I want to orchestrate security priorities, performance, decisions, and reporting so that the CISO and governing bodies maintain effective oversight of cyber risk.\". To achieve this, the microservice `ciso-office-service` will expose several API endpoints using FastAPI, managing data across MongoDB collections like `consolidated_views`, `ciso_reports`, `ciso_escalations`, `evidence_links`. Key functionality includes enforcing specific business constraints such as: Build aggregator calling endpoints of all microservices to compile executive reports. Implement trace validations checking that compliance numbers link back to actual signed artifacts. To ensure audit compliance and regulatory alignment, the microservice captures all decisions in high-performance local MongoDB collections and archives long-term logs to compressed Parquet files, which are securely uploaded to Google Cloud Storage. The microservice is designed for containerized deployment, running on GCP Cloud Run for cloud workflows or within Proxmox LXC containers for localized, secure production environments. Acceptance criteria dictate strict validation, verification checkpoints, and human-in-the-loop approvals for any critical or material actions.

### Implementation Prompt
```markdown
Task: Implement the `ciso-office-service` microservice for the 'CISO Office Agent'.

Technology Stack:
- Python
- Modular Microservices Architecture
- FastAPI for the API layer
- MongoDB for the database layer (use PyMongo or Beanie ODM)
- Parquet for long-term log storage (using PyArrow/Pandas)
- Google Cloud (GCS/Cloud Run) for cloud deployment
- Proxmox VE for local virtualization/production deployment

Requirements:
1. Create a structured Python project with FastAPI for the `ciso-office-service`:
   - `main.py` - FastAPI app initialization, routes registration, and exception handlers.
   - `config.py` - Pydantic settings loading MongoDB URI, GCP project details, Proxmox configs, and log paths.
   - `models/` - MongoDB schemas mapping the collections: `consolidated_views`, `ciso_reports`, `ciso_escalations`, `evidence_links`.
   - `routers/` - Clean FastAPI router modules implementing:
          - GET /ciso/view - Retrieve consolidated operating view aggregating data from all security agents
     - POST /ciso/reports - Generate reports distinguishing facts, estimates, assumptions, and decisions
     - POST /ciso/escalations - Escalate material risks, incidents, control failures, and regulatory matters
     - GET /ciso/conflicts - Detect and route conflicting agent recommendations for resolution
     - GET /ciso/traceability - Verify traceability of board materials to primary evidence
   - `services/` - Business logic implementation.
   - `utils/logging.py` - Custom logger logging events to MongoDB for active querying and periodically buffering/writing log events to local Parquet files, with automated upload to Google Cloud Storage.

2. Specific Business Logic:
   - Story: As a proactive CISO Office Agent, I want to orchestrate security priorities, performance, decisions, and reporting so that the CISO and governing bodies maintain effective oversight of cyber risk.
   - Custom implementation details: Build aggregator calling endpoints of all microservices to compile executive reports. Implement trace validations checking that compliance numbers link back to actual signed artifacts.

3. Parquet Logging Pipeline:
   - Configure a background task or worker that runs every hour or when logs reach 1000 records.
   - Buffer raw logs as standard dicts. Format into a Pandas DataFrame or PyArrow Table using a schema representing (timestamp, event_id, event_type, agent_identity, details_json, severity).
   - Write logs locally to a Parquet file (using Snappy compression).
   - Upload the resulting Parquet file to a Google Cloud Storage bucket (e.g., `gs://bank-audit-logs/ciso-office-service/YYYY/MM/DD/`) using `google-cloud-storage`.
   - Setup fallback local directory in Proxmox VM storage if GCP is unreachable.

4. Deployment Configuration:
   - Write a `Dockerfile` multi-stage build optimizing dependency size and security (running as non-root user).
   - Write a Google Cloud Build configuration `cloudbuild.yaml` to build the container and deploy to Google Cloud Run with minimum/maximum instances.
   - Write a Proxmox deployment configuration template (e.g., an Ansible playbook or shell script using pct/qm commands) to deploy this microservice as an LXC container or VM.

Ensure the code is modular, fully typed with Python type hints, incorporates proper error handling with FastAPI HTTPExceptions, and includes clear docstrings. Do not use placeholders.
```

### Testing Prompt
```markdown
Task: Write automated tests (unit, integration, and end-to-end) for the `ciso-office-service` microservice.

Technology Stack:
- Python (pytest, pytest-asyncio)
- FastAPI (TestClient, httpx.AsyncClient)
- MongoDB (using mongomock or testcontainers-mongodb)
- Parquet & GCS Mocking (using pandas, pyarrow, and mock/unittest.mock)

Testing Requirements:
1. Setup Unit Tests under `tests/unit/`:
   - Mock MongoDB connections and database calls using a fixture.
   - Mock Google Cloud Storage client library to verify GCS uploads.
   - Write unit tests for core helper functions, custom formulas, and validation logic: Build aggregator calling endpoints of all microservices to compile executive reports. Implement trace validations checking that compliance numbers link back to actual signed artifacts.
   - Verify that log archiving buffers logs correctly and generates a valid Parquet file (read the written file back using pyarrow/pandas and check the schemas match).

2. Setup Integration Tests under `tests/integration/`:
   - Use FastAPI `TestClient` or `httpx.AsyncClient` to call endpoints.
   - Test key routes:
          - GET /ciso/view - Retrieve consolidated operating view aggregating data from all security agents
     - POST /ciso/reports - Generate reports distinguishing facts, estimates, assumptions, and decisions
     - POST /ciso/escalations - Escalate material risks, incidents, control failures, and regulatory matters
     - GET /ciso/conflicts - Detect and route conflicting agent recommendations for resolution
     - GET /ciso/traceability - Verify traceability of board materials to primary evidence
   - Verify the request validation (e.g. invalid schemas return 422 Unprocessable Entity).
   - Assert correct database records are inserted/updated in the mock MongoDB.
   - Test failure modes: database timeout, GCS upload failure (check that fallback local storage works).

3. Setup End-to-End Tests under `tests/e2e/`:
   - Test full workflows (e.g., trigger an action, verify the database state, trigger the log archiver, and check the generated parquet payload).
   - Ensure authentication and role-based access checks (if applicable) are tested.

Write clean, highly structured pytest code utilizing fixtures. Include clean tear-downs to reset the database states and local temp files.
```

### Optimization Prompt
```markdown
Task: Optimize the performance, maintainability, and scalability of the `ciso-office-service` microservice.

Areas of Optimization:
1. Database (MongoDB) Performance:
   - Review and implement the index design: Index on ciso_reports (reporting_period, status) and ciso_escalations (severity, status).
   - Optimize queries using project filters and pagination to minimize memory usage on large collections.
   - Enforce connection pooling configurations with PyMongo/Beanie, tuning `maxPoolSize`, `minPoolSize`, and `maxIdleTimeMS`.

2. Logging (Parquet Archiving) Pipeline:
   - Optimize memory consumption during the Parquet conversion. Instead of loading all buffered logs into memory at once, stream logs in chunks using `pyarrow.parquet.ParquetWriter`.
   - Implement snappy or zstd compression on the Parquet file to optimize GCS storage fees and network transfer times.
   - Use async background tasks (e.g., FastAPI's `BackgroundTasks` or Celery) so that log writing and GCS uploads do not block the active API request-response cycle.

3. Deployment & Cloud Resource Optimization:
   - GCP (Cloud Run): Configure CPU and memory limits. Setup concurrency settings to handle multiple simultaneous requests per container instance, minimizing cold starts.
   - Proxmox (LXC/VM): Design container configuration profiles with appropriate swap space limits, IO limits, and CPU weight parameters.
   - Implement health check endpoints (`/health` and `/ready`) that verify MongoDB and disk storage health for liveness/readiness probes in Proxmox / Google Cloud.

Analyze the microservice code to refactor any synchronous blocking calls to asynchronous alternatives (`async`/`await`). Provide clean, optimized refactoring blocks for index creation, background task logic, and async query executions.
```

---

## User Story 31: Agent Orchestration and Workflow Agent

**Summary**:
The goal of the Agent Orchestration and Workflow Agent is to fulfill the story requirements: \"As a proactive Agent Orchestration and Workflow Agent, I want to coordinate work across specialist agents so that security activities are completed efficiently without duplication, conflict, or loss of accountability.\". To achieve this, the microservice `orchestration-workflow-service` will expose several API endpoints using FastAPI, managing data across MongoDB collections like `tasks`, `workflows`, `delegations`, `conflict_rules`. Key functionality includes enforcing specific business constraints such as: Build directed acyclic graph (DAG) workflow engine mapping inter-agent task dependencies. Prevent privilege escalation by validating agent scopes before task routing. To ensure audit compliance and regulatory alignment, the microservice captures all decisions in high-performance local MongoDB collections and archives long-term logs to compressed Parquet files, which are securely uploaded to Google Cloud Storage. The microservice is designed for containerized deployment, running on GCP Cloud Run for cloud workflows or within Proxmox LXC containers for localized, secure production environments. Acceptance criteria dictate strict validation, verification checkpoints, and human-in-the-loop approvals for any critical or material actions.

### Implementation Prompt
```markdown
Task: Implement the `orchestration-workflow-service` microservice for the 'Agent Orchestration and Workflow Agent'.

Technology Stack:
- Python
- Modular Microservices Architecture
- FastAPI for the API layer
- MongoDB for the database layer (use PyMongo or Beanie ODM)
- Parquet for long-term log storage (using PyArrow/Pandas)
- Google Cloud (GCS/Cloud Run) for cloud deployment
- Proxmox VE for local virtualization/production deployment

Requirements:
1. Create a structured Python project with FastAPI for the `orchestration-workflow-service`:
   - `main.py` - FastAPI app initialization, routes registration, and exception handlers.
   - `config.py` - Pydantic settings loading MongoDB URI, GCP project details, Proxmox configs, and log paths.
   - `models/` - MongoDB schemas mapping the collections: `tasks`, `workflows`, `delegations`, `conflict_rules`.
   - `routers/` - Clean FastAPI router modules implementing:
          - POST /orchestration/tasks - Route tasks to specialist agents based on capability, authority, priority, and availability
     - GET /orchestration/workflows - Retrieve dependency trees, owners, deadlines, and current workflow states
     - POST /orchestration/check - Detect duplicate or conflicting actions before execution
     - POST /orchestration/retry - Retry stalled workflows or trigger escalation policies
     - GET /orchestration/trace - Retrieve end-to-end traceability path of delegated actions
   - `services/` - Business logic implementation.
   - `utils/logging.py` - Custom logger logging events to MongoDB for active querying and periodically buffering/writing log events to local Parquet files, with automated upload to Google Cloud Storage.

2. Specific Business Logic:
   - Story: As a proactive Agent Orchestration and Workflow Agent, I want to coordinate work across specialist agents so that security activities are completed efficiently without duplication, conflict, or loss of accountability.
   - Custom implementation details: Build directed acyclic graph (DAG) workflow engine mapping inter-agent task dependencies. Prevent privilege escalation by validating agent scopes before task routing.

3. Parquet Logging Pipeline:
   - Configure a background task or worker that runs every hour or when logs reach 1000 records.
   - Buffer raw logs as standard dicts. Format into a Pandas DataFrame or PyArrow Table using a schema representing (timestamp, event_id, event_type, agent_identity, details_json, severity).
   - Write logs locally to a Parquet file (using Snappy compression).
   - Upload the resulting Parquet file to a Google Cloud Storage bucket (e.g., `gs://bank-audit-logs/orchestration-workflow-service/YYYY/MM/DD/`) using `google-cloud-storage`.
   - Setup fallback local directory in Proxmox VM storage if GCP is unreachable.

4. Deployment Configuration:
   - Write a `Dockerfile` multi-stage build optimizing dependency size and security (running as non-root user).
   - Write a Google Cloud Build configuration `cloudbuild.yaml` to build the container and deploy to Google Cloud Run with minimum/maximum instances.
   - Write a Proxmox deployment configuration template (e.g., an Ansible playbook or shell script using pct/qm commands) to deploy this microservice as an LXC container or VM.

Ensure the code is modular, fully typed with Python type hints, incorporates proper error handling with FastAPI HTTPExceptions, and includes clear docstrings. Do not use placeholders.
```

### Testing Prompt
```markdown
Task: Write automated tests (unit, integration, and end-to-end) for the `orchestration-workflow-service` microservice.

Technology Stack:
- Python (pytest, pytest-asyncio)
- FastAPI (TestClient, httpx.AsyncClient)
- MongoDB (using mongomock or testcontainers-mongodb)
- Parquet & GCS Mocking (using pandas, pyarrow, and mock/unittest.mock)

Testing Requirements:
1. Setup Unit Tests under `tests/unit/`:
   - Mock MongoDB connections and database calls using a fixture.
   - Mock Google Cloud Storage client library to verify GCS uploads.
   - Write unit tests for core helper functions, custom formulas, and validation logic: Build directed acyclic graph (DAG) workflow engine mapping inter-agent task dependencies. Prevent privilege escalation by validating agent scopes before task routing.
   - Verify that log archiving buffers logs correctly and generates a valid Parquet file (read the written file back using pyarrow/pandas and check the schemas match).

2. Setup Integration Tests under `tests/integration/`:
   - Use FastAPI `TestClient` or `httpx.AsyncClient` to call endpoints.
   - Test key routes:
          - POST /orchestration/tasks - Route tasks to specialist agents based on capability, authority, priority, and availability
     - GET /orchestration/workflows - Retrieve dependency trees, owners, deadlines, and current workflow states
     - POST /orchestration/check - Detect duplicate or conflicting actions before execution
     - POST /orchestration/retry - Retry stalled workflows or trigger escalation policies
     - GET /orchestration/trace - Retrieve end-to-end traceability path of delegated actions
   - Verify the request validation (e.g. invalid schemas return 422 Unprocessable Entity).
   - Assert correct database records are inserted/updated in the mock MongoDB.
   - Test failure modes: database timeout, GCS upload failure (check that fallback local storage works).

3. Setup End-to-End Tests under `tests/e2e/`:
   - Test full workflows (e.g., trigger an action, verify the database state, trigger the log archiver, and check the generated parquet payload).
   - Ensure authentication and role-based access checks (if applicable) are tested.

Write clean, highly structured pytest code utilizing fixtures. Include clean tear-downs to reset the database states and local temp files.
```

### Optimization Prompt
```markdown
Task: Optimize the performance, maintainability, and scalability of the `orchestration-workflow-service` microservice.

Areas of Optimization:
1. Database (MongoDB) Performance:
   - Review and implement the index design: Compound index on tasks for (assigned_agent_id, status) and workflows for (parent_id, status).
   - Optimize queries using project filters and pagination to minimize memory usage on large collections.
   - Enforce connection pooling configurations with PyMongo/Beanie, tuning `maxPoolSize`, `minPoolSize`, and `maxIdleTimeMS`.

2. Logging (Parquet Archiving) Pipeline:
   - Optimize memory consumption during the Parquet conversion. Instead of loading all buffered logs into memory at once, stream logs in chunks using `pyarrow.parquet.ParquetWriter`.
   - Implement snappy or zstd compression on the Parquet file to optimize GCS storage fees and network transfer times.
   - Use async background tasks (e.g., FastAPI's `BackgroundTasks` or Celery) so that log writing and GCS uploads do not block the active API request-response cycle.

3. Deployment & Cloud Resource Optimization:
   - GCP (Cloud Run): Configure CPU and memory limits. Setup concurrency settings to handle multiple simultaneous requests per container instance, minimizing cold starts.
   - Proxmox (LXC/VM): Design container configuration profiles with appropriate swap space limits, IO limits, and CPU weight parameters.
   - Implement health check endpoints (`/health` and `/ready`) that verify MongoDB and disk storage health for liveness/readiness probes in Proxmox / Google Cloud.

Analyze the microservice code to refactor any synchronous blocking calls to asynchronous alternatives (`async`/`await`). Provide clean, optimized refactoring blocks for index creation, background task logic, and async query executions.
```

---

## User Story 32: AI Governance and Model Risk Agent

**Summary**:
The goal of the AI Governance and Model Risk Agent is to fulfill the story requirements: \"As a proactive AI Governance and Model Risk Agent, I want to assess and continuously oversee security agents and their models so that AI operates accurately, safely, lawfully, and within approved risk tolerance.\". To achieve this, the microservice `ai-governance-service` will expose several API endpoints using FastAPI, managing data across MongoDB collections like `models_registry`, `assessments`, `monitoring_logs`, `restriction_records`. Key functionality includes enforcing specific business constraints such as: Implement automated evaluation suite testing model outputs against pre-configured validation sets. Setup alert triggers when output drift metrics exceed statistical limits. To ensure audit compliance and regulatory alignment, the microservice captures all decisions in high-performance local MongoDB collections and archives long-term logs to compressed Parquet files, which are securely uploaded to Google Cloud Storage. The microservice is designed for containerized deployment, running on GCP Cloud Run for cloud workflows or within Proxmox LXC containers for localized, secure production environments. Acceptance criteria dictate strict validation, verification checkpoints, and human-in-the-loop approvals for any critical or material actions.

### Implementation Prompt
```markdown
Task: Implement the `ai-governance-service` microservice for the 'AI Governance and Model Risk Agent'.

Technology Stack:
- Python
- Modular Microservices Architecture
- FastAPI for the API layer
- MongoDB for the database layer (use PyMongo or Beanie ODM)
- Parquet for long-term log storage (using PyArrow/Pandas)
- Google Cloud (GCS/Cloud Run) for cloud deployment
- Proxmox VE for local virtualization/production deployment

Requirements:
1. Create a structured Python project with FastAPI for the `ai-governance-service`:
   - `main.py` - FastAPI app initialization, routes registration, and exception handlers.
   - `config.py` - Pydantic settings loading MongoDB URI, GCP project details, Proxmox configs, and log paths.
   - `models/` - MongoDB schemas mapping the collections: `models_registry`, `assessments`, `monitoring_logs`, `restriction_records`.
   - `routers/` - Clean FastAPI router modules implementing:
          - POST /ai/register - Register agent and model metadata (owner, purpose, version, tools, data sources, authority)
     - POST /ai/assess - Perform pre-deployment assessment covering accuracy, robustness, privacy, bias, and regulatory risk
     - POST /ai/monitor - Monitor model and prompt performance and drift against approved thresholds
     - POST /ai/restrict - Enforce restriction or suspension on unsafe or non-compliant agents
     - POST /ai/approve - Route high-impact model changes for independent validation and human approval
   - `services/` - Business logic implementation.
   - `utils/logging.py` - Custom logger logging events to MongoDB for active querying and periodically buffering/writing log events to local Parquet files, with automated upload to Google Cloud Storage.

2. Specific Business Logic:
   - Story: As a proactive AI Governance and Model Risk Agent, I want to assess and continuously oversee security agents and their models so that AI operates accurately, safely, lawfully, and within approved risk tolerance.
   - Custom implementation details: Implement automated evaluation suite testing model outputs against pre-configured validation sets. Setup alert triggers when output drift metrics exceed statistical limits.

3. Parquet Logging Pipeline:
   - Configure a background task or worker that runs every hour or when logs reach 1000 records.
   - Buffer raw logs as standard dicts. Format into a Pandas DataFrame or PyArrow Table using a schema representing (timestamp, event_id, event_type, agent_identity, details_json, severity).
   - Write logs locally to a Parquet file (using Snappy compression).
   - Upload the resulting Parquet file to a Google Cloud Storage bucket (e.g., `gs://bank-audit-logs/ai-governance-service/YYYY/MM/DD/`) using `google-cloud-storage`.
   - Setup fallback local directory in Proxmox VM storage if GCP is unreachable.

4. Deployment Configuration:
   - Write a `Dockerfile` multi-stage build optimizing dependency size and security (running as non-root user).
   - Write a Google Cloud Build configuration `cloudbuild.yaml` to build the container and deploy to Google Cloud Run with minimum/maximum instances.
   - Write a Proxmox deployment configuration template (e.g., an Ansible playbook or shell script using pct/qm commands) to deploy this microservice as an LXC container or VM.

Ensure the code is modular, fully typed with Python type hints, incorporates proper error handling with FastAPI HTTPExceptions, and includes clear docstrings. Do not use placeholders.
```

### Testing Prompt
```markdown
Task: Write automated tests (unit, integration, and end-to-end) for the `ai-governance-service` microservice.

Technology Stack:
- Python (pytest, pytest-asyncio)
- FastAPI (TestClient, httpx.AsyncClient)
- MongoDB (using mongomock or testcontainers-mongodb)
- Parquet & GCS Mocking (using pandas, pyarrow, and mock/unittest.mock)

Testing Requirements:
1. Setup Unit Tests under `tests/unit/`:
   - Mock MongoDB connections and database calls using a fixture.
   - Mock Google Cloud Storage client library to verify GCS uploads.
   - Write unit tests for core helper functions, custom formulas, and validation logic: Implement automated evaluation suite testing model outputs against pre-configured validation sets. Setup alert triggers when output drift metrics exceed statistical limits.
   - Verify that log archiving buffers logs correctly and generates a valid Parquet file (read the written file back using pyarrow/pandas and check the schemas match).

2. Setup Integration Tests under `tests/integration/`:
   - Use FastAPI `TestClient` or `httpx.AsyncClient` to call endpoints.
   - Test key routes:
          - POST /ai/register - Register agent and model metadata (owner, purpose, version, tools, data sources, authority)
     - POST /ai/assess - Perform pre-deployment assessment covering accuracy, robustness, privacy, bias, and regulatory risk
     - POST /ai/monitor - Monitor model and prompt performance and drift against approved thresholds
     - POST /ai/restrict - Enforce restriction or suspension on unsafe or non-compliant agents
     - POST /ai/approve - Route high-impact model changes for independent validation and human approval
   - Verify the request validation (e.g. invalid schemas return 422 Unprocessable Entity).
   - Assert correct database records are inserted/updated in the mock MongoDB.
   - Test failure modes: database timeout, GCS upload failure (check that fallback local storage works).

3. Setup End-to-End Tests under `tests/e2e/`:
   - Test full workflows (e.g., trigger an action, verify the database state, trigger the log archiver, and check the generated parquet payload).
   - Ensure authentication and role-based access checks (if applicable) are tested.

Write clean, highly structured pytest code utilizing fixtures. Include clean tear-downs to reset the database states and local temp files.
```

### Optimization Prompt
```markdown
Task: Optimize the performance, maintainability, and scalability of the `ai-governance-service` microservice.

Areas of Optimization:
1. Database (MongoDB) Performance:
   - Review and implement the index design: Index on models_registry (agent_name, version) and monitoring_logs (model_id, timestamp, drift_score).
   - Optimize queries using project filters and pagination to minimize memory usage on large collections.
   - Enforce connection pooling configurations with PyMongo/Beanie, tuning `maxPoolSize`, `minPoolSize`, and `maxIdleTimeMS`.

2. Logging (Parquet Archiving) Pipeline:
   - Optimize memory consumption during the Parquet conversion. Instead of loading all buffered logs into memory at once, stream logs in chunks using `pyarrow.parquet.ParquetWriter`.
   - Implement snappy or zstd compression on the Parquet file to optimize GCS storage fees and network transfer times.
   - Use async background tasks (e.g., FastAPI's `BackgroundTasks` or Celery) so that log writing and GCS uploads do not block the active API request-response cycle.

3. Deployment & Cloud Resource Optimization:
   - GCP (Cloud Run): Configure CPU and memory limits. Setup concurrency settings to handle multiple simultaneous requests per container instance, minimizing cold starts.
   - Proxmox (LXC/VM): Design container configuration profiles with appropriate swap space limits, IO limits, and CPU weight parameters.
   - Implement health check endpoints (`/health` and `/ready`) that verify MongoDB and disk storage health for liveness/readiness probes in Proxmox / Google Cloud.

Analyze the microservice code to refactor any synchronous blocking calls to asynchronous alternatives (`async`/`await`). Provide clean, optimized refactoring blocks for index creation, background task logic, and async query executions.
```

---

## User Story 33: Agent Identity and Authorization Agent

**Summary**:
The goal of the Agent Identity and Authorization Agent is to fulfill the story requirements: \"As a proactive Agent Identity and Authorization Agent, I want to authenticate every agent and grant task-specific, short-lived permissions so that autonomous actions follow least privilege and separation of duties.\". To achieve this, the microservice `agent-auth-service` will expose several API endpoints using FastAPI, managing data across MongoDB collections like `agent_identities`, `issued_tokens`, `access_policies`, `auth_audit_logs`. Key functionality includes enforcing specific business constraints such as: Enforce strict PKI verification for agents. Implement JSON Web Token (JWT) issuing logic with customized claims (e.g. task_scope, system_scope) expiring within 5-15 minutes. To ensure audit compliance and regulatory alignment, the microservice captures all decisions in high-performance local MongoDB collections and archives long-term logs to compressed Parquet files, which are securely uploaded to Google Cloud Storage. The microservice is designed for containerized deployment, running on GCP Cloud Run for cloud workflows or within Proxmox LXC containers for localized, secure production environments. Acceptance criteria dictate strict validation, verification checkpoints, and human-in-the-loop approvals for any critical or material actions.

### Implementation Prompt
```markdown
Task: Implement the `agent-auth-service` microservice for the 'Agent Identity and Authorization Agent'.

Technology Stack:
- Python
- Modular Microservices Architecture
- FastAPI for the API layer
- MongoDB for the database layer (use PyMongo or Beanie ODM)
- Parquet for long-term log storage (using PyArrow/Pandas)
- Google Cloud (GCS/Cloud Run) for cloud deployment
- Proxmox VE for local virtualization/production deployment

Requirements:
1. Create a structured Python project with FastAPI for the `agent-auth-service`:
   - `main.py` - FastAPI app initialization, routes registration, and exception handlers.
   - `config.py` - Pydantic settings loading MongoDB URI, GCP project details, Proxmox configs, and log paths.
   - `models/` - MongoDB schemas mapping the collections: `agent_identities`, `issued_tokens`, `access_policies`, `auth_audit_logs`.
   - `routers/` - Clean FastAPI router modules implementing:
          - POST /auth/register - Register unique, verifiable agent identities with cryptographic credentials
     - POST /auth/token - Grant short-lived access tokens limited by task, system, environment, data, and time
     - POST /auth/high-risk - Request approved authorization for high-risk permissions
     - POST /auth/revoke - Revoke or rotate agent credentials immediately
     - GET /auth/audit - Retrieve complete audit log of authentication and authorization decisions
   - `services/` - Business logic implementation.
   - `utils/logging.py` - Custom logger logging events to MongoDB for active querying and periodically buffering/writing log events to local Parquet files, with automated upload to Google Cloud Storage.

2. Specific Business Logic:
   - Story: As a proactive Agent Identity and Authorization Agent, I want to authenticate every agent and grant task-specific, short-lived permissions so that autonomous actions follow least privilege and separation of duties.
   - Custom implementation details: Enforce strict PKI verification for agents. Implement JSON Web Token (JWT) issuing logic with customized claims (e.g. task_scope, system_scope) expiring within 5-15 minutes.

3. Parquet Logging Pipeline:
   - Configure a background task or worker that runs every hour or when logs reach 1000 records.
   - Buffer raw logs as standard dicts. Format into a Pandas DataFrame or PyArrow Table using a schema representing (timestamp, event_id, event_type, agent_identity, details_json, severity).
   - Write logs locally to a Parquet file (using Snappy compression).
   - Upload the resulting Parquet file to a Google Cloud Storage bucket (e.g., `gs://bank-audit-logs/agent-auth-service/YYYY/MM/DD/`) using `google-cloud-storage`.
   - Setup fallback local directory in Proxmox VM storage if GCP is unreachable.

4. Deployment Configuration:
   - Write a `Dockerfile` multi-stage build optimizing dependency size and security (running as non-root user).
   - Write a Google Cloud Build configuration `cloudbuild.yaml` to build the container and deploy to Google Cloud Run with minimum/maximum instances.
   - Write a Proxmox deployment configuration template (e.g., an Ansible playbook or shell script using pct/qm commands) to deploy this microservice as an LXC container or VM.

Ensure the code is modular, fully typed with Python type hints, incorporates proper error handling with FastAPI HTTPExceptions, and includes clear docstrings. Do not use placeholders.
```

### Testing Prompt
```markdown
Task: Write automated tests (unit, integration, and end-to-end) for the `agent-auth-service` microservice.

Technology Stack:
- Python (pytest, pytest-asyncio)
- FastAPI (TestClient, httpx.AsyncClient)
- MongoDB (using mongomock or testcontainers-mongodb)
- Parquet & GCS Mocking (using pandas, pyarrow, and mock/unittest.mock)

Testing Requirements:
1. Setup Unit Tests under `tests/unit/`:
   - Mock MongoDB connections and database calls using a fixture.
   - Mock Google Cloud Storage client library to verify GCS uploads.
   - Write unit tests for core helper functions, custom formulas, and validation logic: Enforce strict PKI verification for agents. Implement JSON Web Token (JWT) issuing logic with customized claims (e.g. task_scope, system_scope) expiring within 5-15 minutes.
   - Verify that log archiving buffers logs correctly and generates a valid Parquet file (read the written file back using pyarrow/pandas and check the schemas match).

2. Setup Integration Tests under `tests/integration/`:
   - Use FastAPI `TestClient` or `httpx.AsyncClient` to call endpoints.
   - Test key routes:
          - POST /auth/register - Register unique, verifiable agent identities with cryptographic credentials
     - POST /auth/token - Grant short-lived access tokens limited by task, system, environment, data, and time
     - POST /auth/high-risk - Request approved authorization for high-risk permissions
     - POST /auth/revoke - Revoke or rotate agent credentials immediately
     - GET /auth/audit - Retrieve complete audit log of authentication and authorization decisions
   - Verify the request validation (e.g. invalid schemas return 422 Unprocessable Entity).
   - Assert correct database records are inserted/updated in the mock MongoDB.
   - Test failure modes: database timeout, GCS upload failure (check that fallback local storage works).

3. Setup End-to-End Tests under `tests/e2e/`:
   - Test full workflows (e.g., trigger an action, verify the database state, trigger the log archiver, and check the generated parquet payload).
   - Ensure authentication and role-based access checks (if applicable) are tested.

Write clean, highly structured pytest code utilizing fixtures. Include clean tear-downs to reset the database states and local temp files.
```

### Optimization Prompt
```markdown
Task: Optimize the performance, maintainability, and scalability of the `agent-auth-service` microservice.

Areas of Optimization:
1. Database (MongoDB) Performance:
   - Review and implement the index design: Compound index on issued_tokens for (jti, expires_at) and agent_identities for (agent_id, status).
   - Optimize queries using project filters and pagination to minimize memory usage on large collections.
   - Enforce connection pooling configurations with PyMongo/Beanie, tuning `maxPoolSize`, `minPoolSize`, and `maxIdleTimeMS`.

2. Logging (Parquet Archiving) Pipeline:
   - Optimize memory consumption during the Parquet conversion. Instead of loading all buffered logs into memory at once, stream logs in chunks using `pyarrow.parquet.ParquetWriter`.
   - Implement snappy or zstd compression on the Parquet file to optimize GCS storage fees and network transfer times.
   - Use async background tasks (e.g., FastAPI's `BackgroundTasks` or Celery) so that log writing and GCS uploads do not block the active API request-response cycle.

3. Deployment & Cloud Resource Optimization:
   - GCP (Cloud Run): Configure CPU and memory limits. Setup concurrency settings to handle multiple simultaneous requests per container instance, minimizing cold starts.
   - Proxmox (LXC/VM): Design container configuration profiles with appropriate swap space limits, IO limits, and CPU weight parameters.
   - Implement health check endpoints (`/health` and `/ready`) that verify MongoDB and disk storage health for liveness/readiness probes in Proxmox / Google Cloud.

Analyze the microservice code to refactor any synchronous blocking calls to asynchronous alternatives (`async`/`await`). Provide clean, optimized refactoring blocks for index creation, background task logic, and async query executions.
```

---

## User Story 34: Agent Safety and Policy Enforcement Agent

**Summary**:
The goal of the Agent Safety and Policy Enforcement Agent is to fulfill the story requirements: \"As a proactive Agent Safety and Policy Enforcement Agent, I want to evaluate agent requests before execution and block unsafe or unauthorised actions so that autonomy remains within legal, ethical, security, and operational boundaries.\". To achieve this, the microservice `agent-safety-service` will expose several API endpoints using FastAPI, managing data across MongoDB collections like `evaluation_requests`, `safety_rules`, `enforcement_records`, `estop_states`. Key functionality includes enforcing specific business constraints such as: Implement semantic checks and regex rules to detect prompt injections and tool abuse pre-execution. Build a global 'emergency-stop' Redis/MongoDB toggle to block all agent actions instantly. To ensure audit compliance and regulatory alignment, the microservice captures all decisions in high-performance local MongoDB collections and archives long-term logs to compressed Parquet files, which are securely uploaded to Google Cloud Storage. The microservice is designed for containerized deployment, running on GCP Cloud Run for cloud workflows or within Proxmox LXC containers for localized, secure production environments. Acceptance criteria dictate strict validation, verification checkpoints, and human-in-the-loop approvals for any critical or material actions.

### Implementation Prompt
```markdown
Task: Implement the `agent-safety-service` microservice for the 'Agent Safety and Policy Enforcement Agent'.

Technology Stack:
- Python
- Modular Microservices Architecture
- FastAPI for the API layer
- MongoDB for the database layer (use PyMongo or Beanie ODM)
- Parquet for long-term log storage (using PyArrow/Pandas)
- Google Cloud (GCS/Cloud Run) for cloud deployment
- Proxmox VE for local virtualization/production deployment

Requirements:
1. Create a structured Python project with FastAPI for the `agent-safety-service`:
   - `main.py` - FastAPI app initialization, routes registration, and exception handlers.
   - `config.py` - Pydantic settings loading MongoDB URI, GCP project details, Proxmox configs, and log paths.
   - `models/` - MongoDB schemas mapping the collections: `evaluation_requests`, `safety_rules`, `enforcement_records`, `estop_states`.
   - `routers/` - Clean FastAPI router modules implementing:
          - POST /safety/evaluate - Evaluate proposed agent action against identity, scope, policies, and risk limits
     - POST /safety/detect - Analyze requests for prompt injection, data exfiltration, tool abuse, and instruction conflicts
     - POST /safety/block - Block prohibited action and create tamper-evident record of decision
     - POST /safety/estop - Execute emergency stop to suspend individual agents or the entire system
     - GET /safety/logs - Retrieve enforcement logs with reasons and integrity hashes
   - `services/` - Business logic implementation.
   - `utils/logging.py` - Custom logger logging events to MongoDB for active querying and periodically buffering/writing log events to local Parquet files, with automated upload to Google Cloud Storage.

2. Specific Business Logic:
   - Story: As a proactive Agent Safety and Policy Enforcement Agent, I want to evaluate agent requests before execution and block unsafe or unauthorised actions so that autonomy remains within legal, ethical, security, and operational boundaries.
   - Custom implementation details: Implement semantic checks and regex rules to detect prompt injections and tool abuse pre-execution. Build a global 'emergency-stop' Redis/MongoDB toggle to block all agent actions instantly.

3. Parquet Logging Pipeline:
   - Configure a background task or worker that runs every hour or when logs reach 1000 records.
   - Buffer raw logs as standard dicts. Format into a Pandas DataFrame or PyArrow Table using a schema representing (timestamp, event_id, event_type, agent_identity, details_json, severity).
   - Write logs locally to a Parquet file (using Snappy compression).
   - Upload the resulting Parquet file to a Google Cloud Storage bucket (e.g., `gs://bank-audit-logs/agent-safety-service/YYYY/MM/DD/`) using `google-cloud-storage`.
   - Setup fallback local directory in Proxmox VM storage if GCP is unreachable.

4. Deployment Configuration:
   - Write a `Dockerfile` multi-stage build optimizing dependency size and security (running as non-root user).
   - Write a Google Cloud Build configuration `cloudbuild.yaml` to build the container and deploy to Google Cloud Run with minimum/maximum instances.
   - Write a Proxmox deployment configuration template (e.g., an Ansible playbook or shell script using pct/qm commands) to deploy this microservice as an LXC container or VM.

Ensure the code is modular, fully typed with Python type hints, incorporates proper error handling with FastAPI HTTPExceptions, and includes clear docstrings. Do not use placeholders.
```

### Testing Prompt
```markdown
Task: Write automated tests (unit, integration, and end-to-end) for the `agent-safety-service` microservice.

Technology Stack:
- Python (pytest, pytest-asyncio)
- FastAPI (TestClient, httpx.AsyncClient)
- MongoDB (using mongomock or testcontainers-mongodb)
- Parquet & GCS Mocking (using pandas, pyarrow, and mock/unittest.mock)

Testing Requirements:
1. Setup Unit Tests under `tests/unit/`:
   - Mock MongoDB connections and database calls using a fixture.
   - Mock Google Cloud Storage client library to verify GCS uploads.
   - Write unit tests for core helper functions, custom formulas, and validation logic: Implement semantic checks and regex rules to detect prompt injections and tool abuse pre-execution. Build a global 'emergency-stop' Redis/MongoDB toggle to block all agent actions instantly.
   - Verify that log archiving buffers logs correctly and generates a valid Parquet file (read the written file back using pyarrow/pandas and check the schemas match).

2. Setup Integration Tests under `tests/integration/`:
   - Use FastAPI `TestClient` or `httpx.AsyncClient` to call endpoints.
   - Test key routes:
          - POST /safety/evaluate - Evaluate proposed agent action against identity, scope, policies, and risk limits
     - POST /safety/detect - Analyze requests for prompt injection, data exfiltration, tool abuse, and instruction conflicts
     - POST /safety/block - Block prohibited action and create tamper-evident record of decision
     - POST /safety/estop - Execute emergency stop to suspend individual agents or the entire system
     - GET /safety/logs - Retrieve enforcement logs with reasons and integrity hashes
   - Verify the request validation (e.g. invalid schemas return 422 Unprocessable Entity).
   - Assert correct database records are inserted/updated in the mock MongoDB.
   - Test failure modes: database timeout, GCS upload failure (check that fallback local storage works).

3. Setup End-to-End Tests under `tests/e2e/`:
   - Test full workflows (e.g., trigger an action, verify the database state, trigger the log archiver, and check the generated parquet payload).
   - Ensure authentication and role-based access checks (if applicable) are tested.

Write clean, highly structured pytest code utilizing fixtures. Include clean tear-downs to reset the database states and local temp files.
```

### Optimization Prompt
```markdown
Task: Optimize the performance, maintainability, and scalability of the `agent-safety-service` microservice.

Areas of Optimization:
1. Database (MongoDB) Performance:
   - Review and implement the index design: Index on evaluation_requests (agent_id, status, evaluated_at) and enforcement_records (action_blocked, reason_code).
   - Optimize queries using project filters and pagination to minimize memory usage on large collections.
   - Enforce connection pooling configurations with PyMongo/Beanie, tuning `maxPoolSize`, `minPoolSize`, and `maxIdleTimeMS`.

2. Logging (Parquet Archiving) Pipeline:
   - Optimize memory consumption during the Parquet conversion. Instead of loading all buffered logs into memory at once, stream logs in chunks using `pyarrow.parquet.ParquetWriter`.
   - Implement snappy or zstd compression on the Parquet file to optimize GCS storage fees and network transfer times.
   - Use async background tasks (e.g., FastAPI's `BackgroundTasks` or Celery) so that log writing and GCS uploads do not block the active API request-response cycle.

3. Deployment & Cloud Resource Optimization:
   - GCP (Cloud Run): Configure CPU and memory limits. Setup concurrency settings to handle multiple simultaneous requests per container instance, minimizing cold starts.
   - Proxmox (LXC/VM): Design container configuration profiles with appropriate swap space limits, IO limits, and CPU weight parameters.
   - Implement health check endpoints (`/health` and `/ready`) that verify MongoDB and disk storage health for liveness/readiness probes in Proxmox / Google Cloud.

Analyze the microservice code to refactor any synchronous blocking calls to asynchronous alternatives (`async`/`await`). Provide clean, optimized refactoring blocks for index creation, background task logic, and async query executions.
```

---

## User Story 35: Agent Audit and Evidence Agent

**Summary**:
The goal of the Agent Audit and Evidence Agent is to fulfill the story requirements: \"As a proactive Agent Audit and Evidence Agent, I want to preserve tamper-evident records of agent decisions and actions so that every material outcome can be investigated, explained, reproduced, and audited.\". To achieve this, the microservice `agent-audit-service` will expose several API endpoints using FastAPI, managing data across MongoDB collections like `raw_audit_logs`, `integrity_chains`, `tamper_alerts`. Key functionality includes enforcing specific business constraints such as: Setup daily pipeline mapping MongoDB raw audit logs to Parquet files, uploading them to immutable GCP Cloud Storage buckets (WORM). Implement SHA-256 hash chaining for hot audit logs in MongoDB. To ensure audit compliance and regulatory alignment, the microservice captures all decisions in high-performance local MongoDB collections and archives long-term logs to compressed Parquet files, which are securely uploaded to Google Cloud Storage. The microservice is designed for containerized deployment, running on GCP Cloud Run for cloud workflows or within Proxmox LXC containers for localized, secure production environments. Acceptance criteria dictate strict validation, verification checkpoints, and human-in-the-loop approvals for any critical or material actions.

### Implementation Prompt
```markdown
Task: Implement the `agent-audit-service` microservice for the 'Agent Audit and Evidence Agent'.

Technology Stack:
- Python
- Modular Microservices Architecture
- FastAPI for the API layer
- MongoDB for the database layer (use PyMongo or Beanie ODM)
- Parquet for long-term log storage (using PyArrow/Pandas)
- Google Cloud (GCS/Cloud Run) for cloud deployment
- Proxmox VE for local virtualization/production deployment

Requirements:
1. Create a structured Python project with FastAPI for the `agent-audit-service`:
   - `main.py` - FastAPI app initialization, routes registration, and exception handlers.
   - `config.py` - Pydantic settings loading MongoDB URI, GCP project details, Proxmox configs, and log paths.
   - `models/` - MongoDB schemas mapping the collections: `raw_audit_logs`, `integrity_chains`, `tamper_alerts`.
   - `routers/` - Clean FastAPI router modules implementing:
          - POST /audit/logs - Ingest structured logs capturing identity, inputs, evidence, action, approval, tools, outputs, and timestamp
     - POST /audit/protect - Apply cryptographic integrity protections (e.g., hash chaining or WORM) to ingested logs
     - GET /audit/reconstruct - Retrieve complete sequence of logs to reconstruct a material decision
     - POST /audit/verify - Run integrity check across logs and generate alert if data is missing or altered
     - GET /audit/export - Export evidence in approved regulatory formats
   - `services/` - Business logic implementation.
   - `utils/logging.py` - Custom logger logging events to MongoDB for active querying and periodically buffering/writing log events to local Parquet files, with automated upload to Google Cloud Storage.

2. Specific Business Logic:
   - Story: As a proactive Agent Audit and Evidence Agent, I want to preserve tamper-evident records of agent decisions and actions so that every material outcome can be investigated, explained, reproduced, and audited.
   - Custom implementation details: Setup daily pipeline mapping MongoDB raw audit logs to Parquet files, uploading them to immutable GCP Cloud Storage buckets (WORM). Implement SHA-256 hash chaining for hot audit logs in MongoDB.

3. Parquet Logging Pipeline:
   - Configure a background task or worker that runs every hour or when logs reach 1000 records.
   - Buffer raw logs as standard dicts. Format into a Pandas DataFrame or PyArrow Table using a schema representing (timestamp, event_id, event_type, agent_identity, details_json, severity).
   - Write logs locally to a Parquet file (using Snappy compression).
   - Upload the resulting Parquet file to a Google Cloud Storage bucket (e.g., `gs://bank-audit-logs/agent-audit-service/YYYY/MM/DD/`) using `google-cloud-storage`.
   - Setup fallback local directory in Proxmox VM storage if GCP is unreachable.

4. Deployment Configuration:
   - Write a `Dockerfile` multi-stage build optimizing dependency size and security (running as non-root user).
   - Write a Google Cloud Build configuration `cloudbuild.yaml` to build the container and deploy to Google Cloud Run with minimum/maximum instances.
   - Write a Proxmox deployment configuration template (e.g., an Ansible playbook or shell script using pct/qm commands) to deploy this microservice as an LXC container or VM.

Ensure the code is modular, fully typed with Python type hints, incorporates proper error handling with FastAPI HTTPExceptions, and includes clear docstrings. Do not use placeholders.
```

### Testing Prompt
```markdown
Task: Write automated tests (unit, integration, and end-to-end) for the `agent-audit-service` microservice.

Technology Stack:
- Python (pytest, pytest-asyncio)
- FastAPI (TestClient, httpx.AsyncClient)
- MongoDB (using mongomock or testcontainers-mongodb)
- Parquet & GCS Mocking (using pandas, pyarrow, and mock/unittest.mock)

Testing Requirements:
1. Setup Unit Tests under `tests/unit/`:
   - Mock MongoDB connections and database calls using a fixture.
   - Mock Google Cloud Storage client library to verify GCS uploads.
   - Write unit tests for core helper functions, custom formulas, and validation logic: Setup daily pipeline mapping MongoDB raw audit logs to Parquet files, uploading them to immutable GCP Cloud Storage buckets (WORM). Implement SHA-256 hash chaining for hot audit logs in MongoDB.
   - Verify that log archiving buffers logs correctly and generates a valid Parquet file (read the written file back using pyarrow/pandas and check the schemas match).

2. Setup Integration Tests under `tests/integration/`:
   - Use FastAPI `TestClient` or `httpx.AsyncClient` to call endpoints.
   - Test key routes:
          - POST /audit/logs - Ingest structured logs capturing identity, inputs, evidence, action, approval, tools, outputs, and timestamp
     - POST /audit/protect - Apply cryptographic integrity protections (e.g., hash chaining or WORM) to ingested logs
     - GET /audit/reconstruct - Retrieve complete sequence of logs to reconstruct a material decision
     - POST /audit/verify - Run integrity check across logs and generate alert if data is missing or altered
     - GET /audit/export - Export evidence in approved regulatory formats
   - Verify the request validation (e.g. invalid schemas return 422 Unprocessable Entity).
   - Assert correct database records are inserted/updated in the mock MongoDB.
   - Test failure modes: database timeout, GCS upload failure (check that fallback local storage works).

3. Setup End-to-End Tests under `tests/e2e/`:
   - Test full workflows (e.g., trigger an action, verify the database state, trigger the log archiver, and check the generated parquet payload).
   - Ensure authentication and role-based access checks (if applicable) are tested.

Write clean, highly structured pytest code utilizing fixtures. Include clean tear-downs to reset the database states and local temp files.
```

### Optimization Prompt
```markdown
Task: Optimize the performance, maintainability, and scalability of the `agent-audit-service` microservice.

Areas of Optimization:
1. Database (MongoDB) Performance:
   - Review and implement the index design: Compound index on raw_audit_logs for (timestamp, agent_id) and (correlation_id, step_num).
   - Optimize queries using project filters and pagination to minimize memory usage on large collections.
   - Enforce connection pooling configurations with PyMongo/Beanie, tuning `maxPoolSize`, `minPoolSize`, and `maxIdleTimeMS`.

2. Logging (Parquet Archiving) Pipeline:
   - Optimize memory consumption during the Parquet conversion. Instead of loading all buffered logs into memory at once, stream logs in chunks using `pyarrow.parquet.ParquetWriter`.
   - Implement snappy or zstd compression on the Parquet file to optimize GCS storage fees and network transfer times.
   - Use async background tasks (e.g., FastAPI's `BackgroundTasks` or Celery) so that log writing and GCS uploads do not block the active API request-response cycle.

3. Deployment & Cloud Resource Optimization:
   - GCP (Cloud Run): Configure CPU and memory limits. Setup concurrency settings to handle multiple simultaneous requests per container instance, minimizing cold starts.
   - Proxmox (LXC/VM): Design container configuration profiles with appropriate swap space limits, IO limits, and CPU weight parameters.
   - Implement health check endpoints (`/health` and `/ready`) that verify MongoDB and disk storage health for liveness/readiness probes in Proxmox / Google Cloud.

Analyze the microservice code to refactor any synchronous blocking calls to asynchronous alternatives (`async`/`await`). Provide clean, optimized refactoring blocks for index creation, background task logic, and async query executions.
```

---

## User Story 36: Agent Quality Assurance and Validation Agent

**Summary**:
The goal of the Agent Quality Assurance and Validation Agent is to fulfill the story requirements: \"As a proactive Agent Quality Assurance and Validation Agent, I want to independently test agent decisions, workflows, and outputs so that only reliable agent capabilities are deployed and retained.\". To achieve this, the microservice `agent-qa-service` will expose several API endpoints using FastAPI, managing data across MongoDB collections like `qa_test_runs`, `evaluation_metrics`, `defects_registry`. Key functionality includes enforcing specific business constraints such as: Build LLM-as-a-judge evaluation harness comparing agent outputs against gold-standard answers. Auto-suspend agent services in the registry if QA validation metrics fall below SLAs. To ensure audit compliance and regulatory alignment, the microservice captures all decisions in high-performance local MongoDB collections and archives long-term logs to compressed Parquet files, which are securely uploaded to Google Cloud Storage. The microservice is designed for containerized deployment, running on GCP Cloud Run for cloud workflows or within Proxmox LXC containers for localized, secure production environments. Acceptance criteria dictate strict validation, verification checkpoints, and human-in-the-loop approvals for any critical or material actions.

### Implementation Prompt
```markdown
Task: Implement the `agent-qa-service` microservice for the 'Agent Quality Assurance and Validation Agent'.

Technology Stack:
- Python
- Modular Microservices Architecture
- FastAPI for the API layer
- MongoDB for the database layer (use PyMongo or Beanie ODM)
- Parquet for long-term log storage (using PyArrow/Pandas)
- Google Cloud (GCS/Cloud Run) for cloud deployment
- Proxmox VE for local virtualization/production deployment

Requirements:
1. Create a structured Python project with FastAPI for the `agent-qa-service`:
   - `main.py` - FastAPI app initialization, routes registration, and exception handlers.
   - `config.py` - Pydantic settings loading MongoDB URI, GCP project details, Proxmox configs, and log paths.
   - `models/` - MongoDB schemas mapping the collections: `qa_test_runs`, `evaluation_metrics`, `defects_registry`.
   - `routers/` - Clean FastAPI router modules implementing:
          - POST /qa/tests - Run functional, security, safety, performance, and adversarial test suites on agents
     - POST /qa/metrics - Log test performance metrics (accuracy, false positives/negatives, latency, quality)
     - POST /qa/validate - Validate critical agent outputs independently using alternative evaluation models
     - POST /qa/regression - Trigger regression testing due to changes in models, prompts, policies, tools, or integrations
     - POST /qa/defects - Log detected defects with owner, priority, and traceability links
   - `services/` - Business logic implementation.
   - `utils/logging.py` - Custom logger logging events to MongoDB for active querying and periodically buffering/writing log events to local Parquet files, with automated upload to Google Cloud Storage.

2. Specific Business Logic:
   - Story: As a proactive Agent Quality Assurance and Validation Agent, I want to independently test agent decisions, workflows, and outputs so that only reliable agent capabilities are deployed and retained.
   - Custom implementation details: Build LLM-as-a-judge evaluation harness comparing agent outputs against gold-standard answers. Auto-suspend agent services in the registry if QA validation metrics fall below SLAs.

3. Parquet Logging Pipeline:
   - Configure a background task or worker that runs every hour or when logs reach 1000 records.
   - Buffer raw logs as standard dicts. Format into a Pandas DataFrame or PyArrow Table using a schema representing (timestamp, event_id, event_type, agent_identity, details_json, severity).
   - Write logs locally to a Parquet file (using Snappy compression).
   - Upload the resulting Parquet file to a Google Cloud Storage bucket (e.g., `gs://bank-audit-logs/agent-qa-service/YYYY/MM/DD/`) using `google-cloud-storage`.
   - Setup fallback local directory in Proxmox VM storage if GCP is unreachable.

4. Deployment Configuration:
   - Write a `Dockerfile` multi-stage build optimizing dependency size and security (running as non-root user).
   - Write a Google Cloud Build configuration `cloudbuild.yaml` to build the container and deploy to Google Cloud Run with minimum/maximum instances.
   - Write a Proxmox deployment configuration template (e.g., an Ansible playbook or shell script using pct/qm commands) to deploy this microservice as an LXC container or VM.

Ensure the code is modular, fully typed with Python type hints, incorporates proper error handling with FastAPI HTTPExceptions, and includes clear docstrings. Do not use placeholders.
```

### Testing Prompt
```markdown
Task: Write automated tests (unit, integration, and end-to-end) for the `agent-qa-service` microservice.

Technology Stack:
- Python (pytest, pytest-asyncio)
- FastAPI (TestClient, httpx.AsyncClient)
- MongoDB (using mongomock or testcontainers-mongodb)
- Parquet & GCS Mocking (using pandas, pyarrow, and mock/unittest.mock)

Testing Requirements:
1. Setup Unit Tests under `tests/unit/`:
   - Mock MongoDB connections and database calls using a fixture.
   - Mock Google Cloud Storage client library to verify GCS uploads.
   - Write unit tests for core helper functions, custom formulas, and validation logic: Build LLM-as-a-judge evaluation harness comparing agent outputs against gold-standard answers. Auto-suspend agent services in the registry if QA validation metrics fall below SLAs.
   - Verify that log archiving buffers logs correctly and generates a valid Parquet file (read the written file back using pyarrow/pandas and check the schemas match).

2. Setup Integration Tests under `tests/integration/`:
   - Use FastAPI `TestClient` or `httpx.AsyncClient` to call endpoints.
   - Test key routes:
          - POST /qa/tests - Run functional, security, safety, performance, and adversarial test suites on agents
     - POST /qa/metrics - Log test performance metrics (accuracy, false positives/negatives, latency, quality)
     - POST /qa/validate - Validate critical agent outputs independently using alternative evaluation models
     - POST /qa/regression - Trigger regression testing due to changes in models, prompts, policies, tools, or integrations
     - POST /qa/defects - Log detected defects with owner, priority, and traceability links
   - Verify the request validation (e.g. invalid schemas return 422 Unprocessable Entity).
   - Assert correct database records are inserted/updated in the mock MongoDB.
   - Test failure modes: database timeout, GCS upload failure (check that fallback local storage works).

3. Setup End-to-End Tests under `tests/e2e/`:
   - Test full workflows (e.g., trigger an action, verify the database state, trigger the log archiver, and check the generated parquet payload).
   - Ensure authentication and role-based access checks (if applicable) are tested.

Write clean, highly structured pytest code utilizing fixtures. Include clean tear-downs to reset the database states and local temp files.
```

### Optimization Prompt
```markdown
Task: Optimize the performance, maintainability, and scalability of the `agent-qa-service` microservice.

Areas of Optimization:
1. Database (MongoDB) Performance:
   - Review and implement the index design: Index on qa_test_runs (agent_id, status, run_date) and defects_registry (status, priority).
   - Optimize queries using project filters and pagination to minimize memory usage on large collections.
   - Enforce connection pooling configurations with PyMongo/Beanie, tuning `maxPoolSize`, `minPoolSize`, and `maxIdleTimeMS`.

2. Logging (Parquet Archiving) Pipeline:
   - Optimize memory consumption during the Parquet conversion. Instead of loading all buffered logs into memory at once, stream logs in chunks using `pyarrow.parquet.ParquetWriter`.
   - Implement snappy or zstd compression on the Parquet file to optimize GCS storage fees and network transfer times.
   - Use async background tasks (e.g., FastAPI's `BackgroundTasks` or Celery) so that log writing and GCS uploads do not block the active API request-response cycle.

3. Deployment & Cloud Resource Optimization:
   - GCP (Cloud Run): Configure CPU and memory limits. Setup concurrency settings to handle multiple simultaneous requests per container instance, minimizing cold starts.
   - Proxmox (LXC/VM): Design container configuration profiles with appropriate swap space limits, IO limits, and CPU weight parameters.
   - Implement health check endpoints (`/health` and `/ready`) that verify MongoDB and disk storage health for liveness/readiness probes in Proxmox / Google Cloud.

Analyze the microservice code to refactor any synchronous blocking calls to asynchronous alternatives (`async`/`await`). Provide clean, optimized refactoring blocks for index creation, background task logic, and async query executions.
```

---

## User Story 37: Human Oversight and Escalation Agent

**Summary**:
The goal of the Human Oversight and Escalation Agent is to fulfill the story requirements: \"As a proactive Human Oversight and Escalation Agent, I want to present material decisions to accountable human authorities with complete evidence and options so that required intervention is timely and informed.\". To achieve this, the microservice `human-escalation-service` will expose several API endpoints using FastAPI, managing data across MongoDB collections like `escalations`, `approvals`, `escalation_paths`. Key functionality includes enforcing specific business constraints such as: Implement email/Slack/Teams notification system for human approvals. Prevent silent approval by ensuring that if an SLA deadline passes, the task is redirected to backup stakeholders. To ensure audit compliance and regulatory alignment, the microservice captures all decisions in high-performance local MongoDB collections and archives long-term logs to compressed Parquet files, which are securely uploaded to Google Cloud Storage. The microservice is designed for containerized deployment, running on GCP Cloud Run for cloud workflows or within Proxmox LXC containers for localized, secure production environments. Acceptance criteria dictate strict validation, verification checkpoints, and human-in-the-loop approvals for any critical or material actions.

### Implementation Prompt
```markdown
Task: Implement the `human-escalation-service` microservice for the 'Human Oversight and Escalation Agent'.

Technology Stack:
- Python
- Modular Microservices Architecture
- FastAPI for the API layer
- MongoDB for the database layer (use PyMongo or Beanie ODM)
- Parquet for long-term log storage (using PyArrow/Pandas)
- Google Cloud (GCS/Cloud Run) for cloud deployment
- Proxmox VE for local virtualization/production deployment

Requirements:
1. Create a structured Python project with FastAPI for the `human-escalation-service`:
   - `main.py` - FastAPI app initialization, routes registration, and exception handlers.
   - `config.py` - Pydantic settings loading MongoDB URI, GCP project details, Proxmox configs, and log paths.
   - `models/` - MongoDB schemas mapping the collections: `escalations`, `approvals`, `escalation_paths`.
   - `routers/` - Clean FastAPI router modules implementing:
          - POST /escalations - Submit escalation request (requires issue, impact, urgency, evidence, options, recommendation)
     - GET /escalations/active - Retrieve active escalations assigned to authorized human decision-makers
     - POST /escalations/resolve - Process human decision (approve, reject, request modification) and record response
     - POST /escalations/deadline - Check and trigger secondary escalation path if human response SLAs are breached
   - `services/` - Business logic implementation.
   - `utils/logging.py` - Custom logger logging events to MongoDB for active querying and periodically buffering/writing log events to local Parquet files, with automated upload to Google Cloud Storage.

2. Specific Business Logic:
   - Story: As a proactive Human Oversight and Escalation Agent, I want to present material decisions to accountable human authorities with complete evidence and options so that required intervention is timely and informed.
   - Custom implementation details: Implement email/Slack/Teams notification system for human approvals. Prevent silent approval by ensuring that if an SLA deadline passes, the task is redirected to backup stakeholders.

3. Parquet Logging Pipeline:
   - Configure a background task or worker that runs every hour or when logs reach 1000 records.
   - Buffer raw logs as standard dicts. Format into a Pandas DataFrame or PyArrow Table using a schema representing (timestamp, event_id, event_type, agent_identity, details_json, severity).
   - Write logs locally to a Parquet file (using Snappy compression).
   - Upload the resulting Parquet file to a Google Cloud Storage bucket (e.g., `gs://bank-audit-logs/human-escalation-service/YYYY/MM/DD/`) using `google-cloud-storage`.
   - Setup fallback local directory in Proxmox VM storage if GCP is unreachable.

4. Deployment Configuration:
   - Write a `Dockerfile` multi-stage build optimizing dependency size and security (running as non-root user).
   - Write a Google Cloud Build configuration `cloudbuild.yaml` to build the container and deploy to Google Cloud Run with minimum/maximum instances.
   - Write a Proxmox deployment configuration template (e.g., an Ansible playbook or shell script using pct/qm commands) to deploy this microservice as an LXC container or VM.

Ensure the code is modular, fully typed with Python type hints, incorporates proper error handling with FastAPI HTTPExceptions, and includes clear docstrings. Do not use placeholders.
```

### Testing Prompt
```markdown
Task: Write automated tests (unit, integration, and end-to-end) for the `human-escalation-service` microservice.

Technology Stack:
- Python (pytest, pytest-asyncio)
- FastAPI (TestClient, httpx.AsyncClient)
- MongoDB (using mongomock or testcontainers-mongodb)
- Parquet & GCS Mocking (using pandas, pyarrow, and mock/unittest.mock)

Testing Requirements:
1. Setup Unit Tests under `tests/unit/`:
   - Mock MongoDB connections and database calls using a fixture.
   - Mock Google Cloud Storage client library to verify GCS uploads.
   - Write unit tests for core helper functions, custom formulas, and validation logic: Implement email/Slack/Teams notification system for human approvals. Prevent silent approval by ensuring that if an SLA deadline passes, the task is redirected to backup stakeholders.
   - Verify that log archiving buffers logs correctly and generates a valid Parquet file (read the written file back using pyarrow/pandas and check the schemas match).

2. Setup Integration Tests under `tests/integration/`:
   - Use FastAPI `TestClient` or `httpx.AsyncClient` to call endpoints.
   - Test key routes:
          - POST /escalations - Submit escalation request (requires issue, impact, urgency, evidence, options, recommendation)
     - GET /escalations/active - Retrieve active escalations assigned to authorized human decision-makers
     - POST /escalations/resolve - Process human decision (approve, reject, request modification) and record response
     - POST /escalations/deadline - Check and trigger secondary escalation path if human response SLAs are breached
   - Verify the request validation (e.g. invalid schemas return 422 Unprocessable Entity).
   - Assert correct database records are inserted/updated in the mock MongoDB.
   - Test failure modes: database timeout, GCS upload failure (check that fallback local storage works).

3. Setup End-to-End Tests under `tests/e2e/`:
   - Test full workflows (e.g., trigger an action, verify the database state, trigger the log archiver, and check the generated parquet payload).
   - Ensure authentication and role-based access checks (if applicable) are tested.

Write clean, highly structured pytest code utilizing fixtures. Include clean tear-downs to reset the database states and local temp files.
```

### Optimization Prompt
```markdown
Task: Optimize the performance, maintainability, and scalability of the `human-escalation-service` microservice.

Areas of Optimization:
1. Database (MongoDB) Performance:
   - Review and implement the index design: Compound index on escalations for (status, urgency) and (assigned_human_id, status).
   - Optimize queries using project filters and pagination to minimize memory usage on large collections.
   - Enforce connection pooling configurations with PyMongo/Beanie, tuning `maxPoolSize`, `minPoolSize`, and `maxIdleTimeMS`.

2. Logging (Parquet Archiving) Pipeline:
   - Optimize memory consumption during the Parquet conversion. Instead of loading all buffered logs into memory at once, stream logs in chunks using `pyarrow.parquet.ParquetWriter`.
   - Implement snappy or zstd compression on the Parquet file to optimize GCS storage fees and network transfer times.
   - Use async background tasks (e.g., FastAPI's `BackgroundTasks` or Celery) so that log writing and GCS uploads do not block the active API request-response cycle.

3. Deployment & Cloud Resource Optimization:
   - GCP (Cloud Run): Configure CPU and memory limits. Setup concurrency settings to handle multiple simultaneous requests per container instance, minimizing cold starts.
   - Proxmox (LXC/VM): Design container configuration profiles with appropriate swap space limits, IO limits, and CPU weight parameters.
   - Implement health check endpoints (`/health` and `/ready`) that verify MongoDB and disk storage health for liveness/readiness probes in Proxmox / Google Cloud.

Analyze the microservice code to refactor any synchronous blocking calls to asynchronous alternatives (`async`/`await`). Provide clean, optimized refactoring blocks for index creation, background task logic, and async query executions.
```

---

## User Story 38: Autonomous Action Control Agent

**Summary**:
The goal of the Autonomous Action Control Agent is to fulfill the story requirements: \"As a proactive Autonomous Action Control Agent, I want to classify, authorise, supervise, and reverse autonomous actions so that agents act quickly while keeping operational and customer risk within approved limits.\". To achieve this, the microservice `autonomous-control-service` will expose several API endpoints using FastAPI, managing data across MongoDB collections like `action_tiers`, `preflight_checks`, `execution_limits`, `execution_verifications`. Key functionality includes enforcing specific business constraints such as: Implement rate limiting token bucket. Integrate preflight validation routines that test rollback endpoints prior to initiating any material autonomous action. To ensure audit compliance and regulatory alignment, the microservice captures all decisions in high-performance local MongoDB collections and archives long-term logs to compressed Parquet files, which are securely uploaded to Google Cloud Storage. The microservice is designed for containerized deployment, running on GCP Cloud Run for cloud workflows or within Proxmox LXC containers for localized, secure production environments. Acceptance criteria dictate strict validation, verification checkpoints, and human-in-the-loop approvals for any critical or material actions.

### Implementation Prompt
```markdown
Task: Implement the `autonomous-control-service` microservice for the 'Autonomous Action Control Agent'.

Technology Stack:
- Python
- Modular Microservices Architecture
- FastAPI for the API layer
- MongoDB for the database layer (use PyMongo or Beanie ODM)
- Parquet for long-term log storage (using PyArrow/Pandas)
- Google Cloud (GCS/Cloud Run) for cloud deployment
- Proxmox VE for local virtualization/production deployment

Requirements:
1. Create a structured Python project with FastAPI for the `autonomous-control-service`:
   - `main.py` - FastAPI app initialization, routes registration, and exception handlers.
   - `config.py` - Pydantic settings loading MongoDB URI, GCP project details, Proxmox configs, and log paths.
   - `models/` - MongoDB schemas mapping the collections: `action_tiers`, `preflight_checks`, `execution_limits`, `execution_verifications`.
   - `routers/` - Clean FastAPI router modules implementing:
          - POST /control/tiers - Assign and manage approved autonomy and impact tiers for actions
     - POST /control/preflight - Run pre-execution check validating scope, dependencies, impact, confidence, and rollback
     - POST /control/limits - Check rate limits, circuit breakers, and health thresholds before action execution
     - POST /control/verify - Verify post-execution outcomes and execute rollback or escalation on failure
   - `services/` - Business logic implementation.
   - `utils/logging.py` - Custom logger logging events to MongoDB for active querying and periodically buffering/writing log events to local Parquet files, with automated upload to Google Cloud Storage.

2. Specific Business Logic:
   - Story: As a proactive Autonomous Action Control Agent, I want to classify, authorise, supervise, and reverse autonomous actions so that agents act quickly while keeping operational and customer risk within approved limits.
   - Custom implementation details: Implement rate limiting token bucket. Integrate preflight validation routines that test rollback endpoints prior to initiating any material autonomous action.

3. Parquet Logging Pipeline:
   - Configure a background task or worker that runs every hour or when logs reach 1000 records.
   - Buffer raw logs as standard dicts. Format into a Pandas DataFrame or PyArrow Table using a schema representing (timestamp, event_id, event_type, agent_identity, details_json, severity).
   - Write logs locally to a Parquet file (using Snappy compression).
   - Upload the resulting Parquet file to a Google Cloud Storage bucket (e.g., `gs://bank-audit-logs/autonomous-control-service/YYYY/MM/DD/`) using `google-cloud-storage`.
   - Setup fallback local directory in Proxmox VM storage if GCP is unreachable.

4. Deployment Configuration:
   - Write a `Dockerfile` multi-stage build optimizing dependency size and security (running as non-root user).
   - Write a Google Cloud Build configuration `cloudbuild.yaml` to build the container and deploy to Google Cloud Run with minimum/maximum instances.
   - Write a Proxmox deployment configuration template (e.g., an Ansible playbook or shell script using pct/qm commands) to deploy this microservice as an LXC container or VM.

Ensure the code is modular, fully typed with Python type hints, incorporates proper error handling with FastAPI HTTPExceptions, and includes clear docstrings. Do not use placeholders.
```

### Testing Prompt
```markdown
Task: Write automated tests (unit, integration, and end-to-end) for the `autonomous-control-service` microservice.

Technology Stack:
- Python (pytest, pytest-asyncio)
- FastAPI (TestClient, httpx.AsyncClient)
- MongoDB (using mongomock or testcontainers-mongodb)
- Parquet & GCS Mocking (using pandas, pyarrow, and mock/unittest.mock)

Testing Requirements:
1. Setup Unit Tests under `tests/unit/`:
   - Mock MongoDB connections and database calls using a fixture.
   - Mock Google Cloud Storage client library to verify GCS uploads.
   - Write unit tests for core helper functions, custom formulas, and validation logic: Implement rate limiting token bucket. Integrate preflight validation routines that test rollback endpoints prior to initiating any material autonomous action.
   - Verify that log archiving buffers logs correctly and generates a valid Parquet file (read the written file back using pyarrow/pandas and check the schemas match).

2. Setup Integration Tests under `tests/integration/`:
   - Use FastAPI `TestClient` or `httpx.AsyncClient` to call endpoints.
   - Test key routes:
          - POST /control/tiers - Assign and manage approved autonomy and impact tiers for actions
     - POST /control/preflight - Run pre-execution check validating scope, dependencies, impact, confidence, and rollback
     - POST /control/limits - Check rate limits, circuit breakers, and health thresholds before action execution
     - POST /control/verify - Verify post-execution outcomes and execute rollback or escalation on failure
   - Verify the request validation (e.g. invalid schemas return 422 Unprocessable Entity).
   - Assert correct database records are inserted/updated in the mock MongoDB.
   - Test failure modes: database timeout, GCS upload failure (check that fallback local storage works).

3. Setup End-to-End Tests under `tests/e2e/`:
   - Test full workflows (e.g., trigger an action, verify the database state, trigger the log archiver, and check the generated parquet payload).
   - Ensure authentication and role-based access checks (if applicable) are tested.

Write clean, highly structured pytest code utilizing fixtures. Include clean tear-downs to reset the database states and local temp files.
```

### Optimization Prompt
```markdown
Task: Optimize the performance, maintainability, and scalability of the `autonomous-control-service` microservice.

Areas of Optimization:
1. Database (MongoDB) Performance:
   - Review and implement the index design: Index on preflight_checks (action_id, status) and execution_verifications (action_id, success).
   - Optimize queries using project filters and pagination to minimize memory usage on large collections.
   - Enforce connection pooling configurations with PyMongo/Beanie, tuning `maxPoolSize`, `minPoolSize`, and `maxIdleTimeMS`.

2. Logging (Parquet Archiving) Pipeline:
   - Optimize memory consumption during the Parquet conversion. Instead of loading all buffered logs into memory at once, stream logs in chunks using `pyarrow.parquet.ParquetWriter`.
   - Implement snappy or zstd compression on the Parquet file to optimize GCS storage fees and network transfer times.
   - Use async background tasks (e.g., FastAPI's `BackgroundTasks` or Celery) so that log writing and GCS uploads do not block the active API request-response cycle.

3. Deployment & Cloud Resource Optimization:
   - GCP (Cloud Run): Configure CPU and memory limits. Setup concurrency settings to handle multiple simultaneous requests per container instance, minimizing cold starts.
   - Proxmox (LXC/VM): Design container configuration profiles with appropriate swap space limits, IO limits, and CPU weight parameters.
   - Implement health check endpoints (`/health` and `/ready`) that verify MongoDB and disk storage health for liveness/readiness probes in Proxmox / Google Cloud.

Analyze the microservice code to refactor any synchronous blocking calls to asynchronous alternatives (`async`/`await`). Provide clean, optimized refactoring blocks for index creation, background task logic, and async query executions.
```

---

