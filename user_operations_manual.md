# User Operations Manual: Modular Agentic Banking Security Microservices (Phase 0)

This manual provides instructions for security analysts, agent developers, and client integrations interacting with the bank's baseline InfoSec microservices.

---

## 1. Quick Start

By default, when running locally, the base microservice template is accessible at:
*   **Base URL**: `http://127.0.0.1:8000`
*   **Swagger API Documentation**: `http://127.0.0.1:8000/docs`
*   **OpenAPI Specification**: `http://127.0.0.1:8000/openapi.json`

---

## 2. Authentication & Headers

All non-public endpoints enforce mandatory identification checks via the custom safety middleware. 

### Mandatory Header:
Any request made to protected endpoints must include the `X-Agent-ID` HTTP header, representing the calling agent's unique identity.
*   **Header Name**: `X-Agent-ID`
*   **Value Format**: `<agent-type>-agent-<id>` (e.g., `soc-agent-005` or `governance-agent-001`)

If this header is missing, the API rejects the request immediately with a `401 Unauthorized` response:
```json
{
  "error": "Unauthorized",
  "message": "Missing mandatory X-Agent-ID header identifying the agent."
}
```

---

## 3. API Reference

### 3.1 Public Endpoints
No headers are required to access these operational and routing check endpoints.

#### GET `/health`
Returns the operational health status of the microservice.
*   **Response (200 OK)**:
    ```json
    {
      "status": "healthy",
      "service": "base_service"
    }
    ```

#### GET `/ready`
Validates that the service is initialized and that the underlying database connection is fully reachable.
*   **Response (200 OK)**:
    ```json
    {
      "status": "ready"
    }
    ```
*   **Response (503 Service Unavailable)**:
    If the database is unreachable or down, the readiness probe fails:
    ```json
    {
      "detail": "Service not ready: Database unreachable - <exception-details>"
    }
    ```

---

### 3.2 Protected Endpoints
These endpoints require the `X-Agent-ID` header.

#### GET `/metadata`
Retrieves all service metadata records from the database. Each access is recorded in the immutable audit log.
*   **Headers Required**: `X-Agent-ID: <agent_id>`
*   **Response (200 OK)**:
    ```json
    [
      {
        "id": "60c72b2f9b1d8a23d4f8b965",
        "name": "Base Template Service",
        "status": "ONLINE",
        "last_updated": "2026-08-05T12:00:00Z"
      }
    ]
    ```

#### POST `/metadata/status`
Updates the operational status of the service metadata record. Each change generates a high-severity `WARNING` log in the audit trail.
*   **Headers Required**: `X-Agent-ID: <agent_id>`
*   **Request Body (JSON)**:
    ```json
    {
      "status": "MAINTENANCE"
    }
    ```
*   **Response (200 OK)**:
    ```json
    {
      "id": "60c72b2f9b1d8a23d4f8b965",
      "name": "Base Template Service",
      "status": "MAINTENANCE",
      "last_updated": "2026-08-05T12:10:43Z"
    }
    ```
*   **Response (404 Not Found)**:
    If the metadata record does not exist in MongoDB:
    ```json
    {
      "detail": "Service metadata record not found."
    }
    ```

---

## 4. Client Integration Examples

### 4.1 CLI Integration (`curl`)

**Querying Metadata (Protected)**:
```bash
curl -X GET "http://127.0.0.1:8000/metadata" \
     -H "accept: application/json" \
     -H "X-Agent-ID: compliance-agent-12"
```

**Updating Status (Protected)**:
```bash
curl -X POST "http://127.0.0.1:8000/metadata/status" \
     -H "accept: application/json" \
     -H "Content-Type: application/json" \
     -H "X-Agent-ID: compliance-agent-12" \
     -d "{\"status\": \"OFFLINE\"}"
```

### 4.2 Python Integration (`httpx`)

```python
import httpx

headers = {
    "X-Agent-ID": "incident-response-agent-3",
    "Content-Type": "application/json"
}

# 1. Fetch Metadata
with httpx.Client(base_url="http://127.0.0.1:8000") as client:
    response = client.get("/metadata", headers=headers)
    if response.status_code == 200:
        print("Current Metadata:", response.json())
        
    # 2. Update Status
    payload = {"status": "ONLINE"}
    response = client.post("/metadata/status", json=payload, headers=headers)
    if response.status_code == 200:
        print("Updated Metadata:", response.json())
```

---

## 5. Security & Audits

All interactions with protected endpoints generate logs in the MongoDB `raw_audit_logs` collection. 

### Audit Log Schema:
*   `timestamp`: Date and time of the event in UTC ISO format.
*   `event_id`: Unique 16-character hexadecimal string identifier for the transaction.
*   `event_type`: Category of the action (`METADATA_READ`, `STATUS_CHANGED`).
*   `agent_identity`: The `X-Agent-ID` header supplied by the client.
*   `details_json`: JSON-serialized dictionary details (such as count of records returned, or `old_status` vs `new_status`).
*   `severity`: Log severity classification (`INFO`, `WARNING`, `ERROR`).
