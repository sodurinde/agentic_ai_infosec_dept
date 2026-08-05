import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from shared.middleware import AgentSafetyMiddleware

# Setup temporary FastAPI application for testing middleware
app = FastAPI()
app.add_middleware(AgentSafetyMiddleware)

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/ready")
def ready():
    return {"status": "ready"}

@app.get("/test-protected")
def protected():
    return {"message": "secret"}

@app.get("/test-error")
def error():
    raise ValueError("Database timeout simulation")

client = TestClient(app)

def test_middleware_bypass_public():
    # Verify public endpoints bypass check
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
    
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}

def test_middleware_blocks_without_header():
    # Verify X-Agent-ID is required for protected endpoints
    response = client.get("/test-protected")
    assert response.status_code == 401
    assert response.json()["error"] == "Unauthorized"
    assert "X-Agent-ID" in response.json()["message"]

def test_middleware_allows_with_header():
    # Verify valid header passes and injects process time header
    response = client.get("/test-protected", headers={"X-Agent-ID": "test-agent-id"})
    assert response.status_code == 200
    assert response.json() == {"message": "secret"}
    assert "X-Process-Time" in response.headers

def test_middleware_handles_internal_errors():
    # Verify unhandled exceptions in endpoint code are caught and return a 500
    response = client.get("/test-error", headers={"X-Agent-ID": "test-agent-id"})
    assert response.status_code == 500
    assert response.json()["error"] == "Internal Server Error"
    assert "An error occurred" in response.json()["message"]
