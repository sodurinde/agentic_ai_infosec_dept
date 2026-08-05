import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta
import asyncio
from beanie import PydanticObjectId

from services.governance_service.main import app
from services.governance_service.models.policy import Policy
from services.governance_service.models.exception import PolicyException
from services.governance_service.models.report import GovernanceReport

client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_db_init():
    with (
        patch(
            "services.governance_service.main.db_manager.initialize",
            new_callable=AsyncMock
        ),
        patch(
            "services.governance_service.main.db_manager.close",
            new_callable=AsyncMock
        )
    ):
        yield


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy", "service": "governance_service"
    }


@pytest.mark.asyncio
async def test_ready_endpoint_success():
    with patch.object(Policy, "count", new_callable=AsyncMock) as mock_count:
        mock_count.return_value = 1
        response = client.get("/ready")
        assert response.status_code == 200
        assert response.json() == {"status": "ready"}


@pytest.mark.asyncio
async def test_ready_endpoint_failure():
    with patch.object(Policy, "count", new_callable=AsyncMock) as mock_count:
        mock_count.side_effect = Exception("DB Connection Timeout")
        response = client.get("/ready")
        assert response.status_code == 503
        assert "Database unreachable" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_policies():
    mock_policy = Policy(
        title="Access Control",
        content="Restrict access",
        version="1.0",
        owner="Alice",
        review_deadline=datetime.now(timezone.utc)
    )

    mock_query = MagicMock()
    mock_query.to_list = AsyncMock(return_value=[mock_policy])

    with (
        patch.object(Policy, "find_all", return_value=mock_query),
        patch(
            "services.governance_service.routers.policies.log_audit_event",
            new_callable=AsyncMock
        ) as mock_log
    ):

        response = client.get(
            "/policies", headers={"X-Agent-ID": "governance-agent"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Access Control"
        mock_log.assert_called_once()


@pytest.mark.asyncio
async def test_create_policy():
    with (
        patch.object(Policy, "insert", new_callable=AsyncMock) as mock_insert,
        patch(
            "services.governance_service.routers.policies.log_audit_event",
            new_callable=AsyncMock
        ) as mock_log
    ):

        payload = {
            "title": "Data Protection",
            "content": "Encrypt data",
            "version": "1.0",
            "owner": "Bob",
            "review_deadline": datetime.now(timezone.utc).isoformat()
        }

        response = client.post(
            "/policies", json=payload,
            headers={"X-Agent-ID": "governance-agent"}
        )
        assert response.status_code == 201
        assert response.json()["title"] == "Data Protection"
        mock_insert.assert_called_once()
        mock_log.assert_called_once()


@pytest.mark.asyncio
async def test_approve_policy_success():
    pid = PydanticObjectId()
    mock_policy = Policy(
        id=pid,
        title="Data Protection",
        content="Encrypt data",
        version="1.0",
        owner="Bob",
        review_deadline=datetime.now(timezone.utc)
    )

    with (
        patch.object(
            Policy, "get", new_callable=AsyncMock, return_value=mock_policy
        ),
        patch.object(Policy, "save", new_callable=AsyncMock) as mock_save,
        patch(
            "services.governance_service.routers.policies.log_audit_event",
            new_callable=AsyncMock
        ) as mock_log
    ):

        payload = {
            "policy_id": str(pid),
            "approved_by": "CSO",
            "approval_signature": "sig-123"
        }

        response = client.post(
            "/policies/approve", json=payload,
            headers={"X-Agent-ID": "governance-agent"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "APPROVED"
        assert data["approved_by"] == "CSO"
        assert data["approval_signature"] == "sig-123"
        mock_save.assert_called_once()
        mock_log.assert_called_once()


@pytest.mark.asyncio
async def test_approve_policy_missing_signature():
    payload = {
        "policy_id": str(PydanticObjectId()),
        "approved_by": "CSO",
        "approval_signature": "  "
    }
    response = client.post(
        "/policies/approve", json=payload,
        headers={"X-Agent-ID": "governance-agent"}
    )
    assert response.status_code == 400
    assert "Signature validation failed" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_exception_success():
    pid = PydanticObjectId()
    mock_policy = Policy(
        id=pid,
        title="Data Protection",
        content="Encrypt data",
        version="1.0",
        owner="Bob",
        review_deadline=datetime.now(timezone.utc)
    )

    with (
        patch.object(
            Policy, "get", new_callable=AsyncMock, return_value=mock_policy
        ),
        patch.object(
            PolicyException, "insert", new_callable=AsyncMock
        ) as mock_insert,
        patch(
            "services.governance_service.routers.exceptions.log_audit_event",
            new_callable=AsyncMock
        ) as mock_log
    ):

        payload = {
            "policy_id": str(pid),
            "owner": "DevTeam",
            "justification": "legacy system compatibility",
            "compensating_controls": "firewall restrictions",
            "risk_rating": "HIGH",
            "expiry_date": (
                datetime.now(timezone.utc) + timedelta(days=30)
            ).isoformat(),
            "approved_by": "CSO",
            "approval_signature": "sig-456"
        }

        response = client.post(
            "/exceptions", json=payload,
            headers={"X-Agent-ID": "governance-agent"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["risk_rating"] == "HIGH"
        assert data["is_approved"] is True
        mock_insert.assert_called_once()
        mock_log.assert_called_once()


@pytest.mark.asyncio
async def test_create_exception_invalid_rating():
    payload = {
        "policy_id": str(PydanticObjectId()),
        "owner": "DevTeam",
        "justification": "legacy system compatibility",
        "compensating_controls": "firewall restrictions",
        "risk_rating": "SUPER_HIGH",
        "expiry_date": (
            datetime.now(timezone.utc) + timedelta(days=30)
        ).isoformat()
    }
    response = client.post(
        "/exceptions", json=payload,
        headers={"X-Agent-ID": "governance-agent"}
    )
    assert response.status_code == 400
    assert "Invalid risk rating" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_escalations():
    mock_exc = PolicyException(
        policy_id="pid",
        owner="DevTeam",
        justification="...",
        compensating_controls="...",
        risk_rating="MEDIUM",
        expiry_date=datetime.now(timezone.utc),
        is_escalated=True
    )

    mock_query = MagicMock()
    mock_query.to_list = AsyncMock(return_value=[mock_exc])

    with (
        patch.object(PolicyException, "find", return_value=mock_query),
        patch(
            "services.governance_service.routers.exceptions.log_audit_event",
            new_callable=AsyncMock
        )
    ):

        response = client.get(
            "/exceptions/escalations",
            headers={"X-Agent-ID": "governance-agent"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["is_escalated"] is True


@pytest.mark.asyncio
async def test_generate_report():
    with (
        patch.object(Policy, "count", new_callable=AsyncMock, return_value=10),
        patch.object(Policy, "find") as mock_find_policy,
        patch.object(PolicyException, "find") as mock_find_exc,
        patch.object(
            GovernanceReport, "insert", new_callable=AsyncMock
        ) as mock_report_insert,
        patch(
            "services.governance_service.routers.reports.log_audit_event",
            new_callable=AsyncMock
        )
    ):

        # Mock policy find(Policy.status == "APPROVED").count()
        mock_find_policy.return_value.count = AsyncMock(return_value=6)

        # Mock exceptions find counts
        mock_query_exc = MagicMock()
        mock_query_exc.count = AsyncMock(side_effect=[2, 1])
        mock_find_exc.return_value = mock_query_exc

        response = client.get(
            "/governance/report", headers={"X-Agent-ID": "governance-agent"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["metrics"]["total_policies"] == 10
        assert data["metrics"]["percentage_approved"] == 60.0
        assert data["metrics"]["active_exceptions"] == 2
        assert data["metrics"]["escalated_exceptions"] == 1
        mock_report_insert.assert_called_once()


@pytest.mark.asyncio
async def test_scheduler_loop():
    from services.governance_service.main import (
        check_governance_escalations_loop,
    )

    # Setup overdue policy and expired exception mocks
    pid = PydanticObjectId()
    mock_policy = Policy(
        id=pid,
        title="Access Control",
        content="Restrict access",
        version="1.0",
        owner="Alice",
        review_deadline=datetime.now(timezone.utc) - timedelta(days=1),
        status="DRAFT"
    )

    eid = PydanticObjectId()
    mock_exc = PolicyException(
        id=eid,
        policy_id=str(pid),
        owner="DevTeam",
        justification="...",
        compensating_controls="...",
        risk_rating="HIGH",
        expiry_date=datetime.now(timezone.utc) - timedelta(days=1),
        is_escalated=False
    )

    # Mock Policy.find
    mock_find_policy = MagicMock()
    mock_find_policy.to_list = AsyncMock(return_value=[mock_policy])

    # Mock Exception.find
    mock_find_exc = MagicMock()
    mock_find_exc.to_list = AsyncMock(return_value=[mock_exc])

    with (
        patch.object(Policy, "find", return_value=mock_find_policy),
        patch.object(
            Policy, "save", new_callable=AsyncMock
        ) as mock_policy_save,
        patch.object(PolicyException, "find", return_value=mock_find_exc),
        patch.object(
            PolicyException, "save", new_callable=AsyncMock
        ) as mock_exc_save,
        patch(
            "services.governance_service.main.log_audit_event",
            new_callable=AsyncMock
        ) as mock_log,
        patch(
            "asyncio.sleep", side_effect=asyncio.CancelledError
        )
    ):

        try:
            await check_governance_escalations_loop(0.1)
        except asyncio.CancelledError:
            pass

        assert mock_policy.status == "OVERDUE"
        assert mock_exc.is_escalated is True
        mock_policy_save.assert_called_once()
        mock_exc_save.assert_called_once()
        assert mock_log.call_count == 2
