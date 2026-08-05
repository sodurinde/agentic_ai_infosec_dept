import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta
from beanie import PydanticObjectId

from services.risk_mgmt_service.main import app
from services.risk_mgmt_service.models.methodology import Methodology
from services.risk_mgmt_service.models.risk import Risk
from services.risk_mgmt_service.models.treatment import TreatmentPlan

client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_db_init():
    with (
        patch(
            "services.risk_mgmt_service.main.db_manager.initialize",
            new_callable=AsyncMock
        ),
        patch(
            "services.risk_mgmt_service.main.db_manager.close",
            new_callable=AsyncMock
        )
    ):
        yield


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy", "service": "risk_management_service"
    }


@pytest.mark.asyncio
async def test_ready_endpoint_success():
    with patch.object(Risk, "count", new_callable=AsyncMock) as mock_count:
        mock_count.return_value = 1
        response = client.get("/ready")
        assert response.status_code == 200
        assert response.json() == {"status": "ready"}


@pytest.mark.asyncio
async def test_ready_endpoint_failure():
    with patch.object(Risk, "count", new_callable=AsyncMock) as mock_count:
        mock_count.side_effect = Exception("DB Connection Timeout")
        response = client.get("/ready")
        assert response.status_code == 503
        assert "Database unreachable" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_methodology():
    with (
        patch.object(
            Methodology, "insert", new_callable=AsyncMock
        ) as mock_insert,
        patch(
            "services.risk_mgmt_service.routers.risks.log_audit_event",
            new_callable=AsyncMock
        ) as mock_log
    ):

        payload = {
            "name": "NIST SP 800-30",
            "description": "Standard risk methodology"
        }

        response = client.post(
            "/risks/methodologies", json=payload,
            headers={"X-Agent-ID": "risk-agent"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "NIST SP 800-30"
        mock_insert.assert_called_once()
        mock_log.assert_called_once()


@pytest.mark.asyncio
async def test_assess_risk_success():
    mid = PydanticObjectId()
    mock_methodology = Methodology(
        id=mid,
        name="NIST SP 800-30",
        description="Standard risk methodology"
    )

    with (
        patch.object(
            Methodology, "get", new_callable=AsyncMock,
            return_value=mock_methodology
        ),
        patch.object(Risk, "insert", new_callable=AsyncMock) as mock_insert,
        patch(
            "services.risk_mgmt_service.routers.risks.log_audit_event",
            new_callable=AsyncMock
        ) as mock_log
    ):

        payload = {
            "title": "Unauthorized DB Access",
            "description": "Risk of data leakage",
            "methodology_id": str(mid),
            "likelihood": 4,
            "impact": 3,
            "vulnerability_factor": 0.5,
            "control_effectiveness": 0.20
        }

        response = client.post(
            "/risks/assess", json=payload, headers={"X-Agent-ID": "risk-agent"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["inherent_score"] == 12
        assert data["residual_score"] == 9.60
        mock_insert.assert_called_once()
        mock_log.assert_called_once()


@pytest.mark.asyncio
async def test_assess_risk_invalid_methodology():
    payload = {
        "title": "Unauthorized DB Access",
        "description": "Risk of data leakage",
        "methodology_id": str(PydanticObjectId()),
        "likelihood": 4,
        "impact": 3,
        "vulnerability_factor": 0.5,
        "control_effectiveness": 0.20
    }

    response = client.post(
        "/risks/assess", json=payload, headers={"X-Agent-ID": "risk-agent"}
    )
    assert response.status_code == 404
    assert "Risk Methodology not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_risk_register():
    mock_risk = Risk(
        title="Unauthorized DB Access",
        description="...",
        methodology_id="mid",
        likelihood=3,
        impact=4,
        inherent_score=12,
        residual_score=12.0
    )

    mock_query = MagicMock()
    mock_query.to_list = AsyncMock(return_value=[mock_risk])

    with (
        patch.object(Risk, "find_all", return_value=mock_query),
        patch(
            "services.risk_mgmt_service.routers.risks.log_audit_event",
            new_callable=AsyncMock
        ) as mock_log
    ):

        response = client.get(
            "/risks/register", headers={"X-Agent-ID": "risk-agent"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Unauthorized DB Access"
        mock_log.assert_called_once()


@pytest.mark.asyncio
async def test_define_treatment():
    rid = PydanticObjectId()
    mock_risk = Risk(
        id=rid,
        title="Unauthorized DB Access",
        description="...",
        methodology_id="mid",
        likelihood=3,
        impact=4,
        inherent_score=12,
        residual_score=12.0,
        control_effectiveness=0.0
    )

    with (
        patch.object(
            Risk, "get", new_callable=AsyncMock, return_value=mock_risk
        ),
        patch.object(Risk, "save", new_callable=AsyncMock) as mock_risk_save,
        patch.object(
            TreatmentPlan, "insert", new_callable=AsyncMock
        ) as mock_plan_insert,
        patch(
            "services.risk_mgmt_service.routers.risks.log_audit_event",
            new_callable=AsyncMock
        ) as mock_log
    ):

        payload = {
            "risk_id": str(rid),
            "owner": "NetSecTeam",
            "target_date": (
                datetime.now(timezone.utc) + timedelta(days=15)
            ).isoformat(),
            "mitigation_actions": "Deploy firewall rule",
            "expected_control_effectiveness": 0.80
        }

        response = client.post(
            "/risks/treatment", json=payload,
            headers={"X-Agent-ID": "risk-agent"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["expected_control_effectiveness"] == 0.80
        assert mock_risk.status == "TREATED"
        assert mock_risk.control_effectiveness == 0.80
        assert mock_risk.residual_score == 2.40  # 12 * (1 - 0.8) = 2.4
        mock_risk_save.assert_called_once()
        mock_plan_insert.assert_called_once()
        mock_log.assert_called_once()


@pytest.mark.asyncio
async def test_escalate_risk_success():
    rid = PydanticObjectId()
    mock_risk = Risk(
        id=rid,
        title="Critical Vulnerability",
        description="...",
        methodology_id="mid",
        likelihood=5,
        impact=4,
        inherent_score=20,
        residual_score=16.0
    )

    with (
        patch.object(
            Risk, "get", new_callable=AsyncMock, return_value=mock_risk
        ),
        patch.object(Risk, "save", new_callable=AsyncMock) as mock_save,
        patch(
            "services.risk_mgmt_service.routers.risks.log_audit_event",
            new_callable=AsyncMock
        ) as mock_log
    ):

        payload = {"risk_id": str(rid)}

        response = client.post(
            "/risks/escalate",
            json=payload,
            headers={"X-Agent-ID": "risk-agent"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ESCALATED"
        mock_save.assert_called_once()
        mock_log.assert_called_once()


@pytest.mark.asyncio
async def test_escalate_risk_below_threshold():
    rid = PydanticObjectId()
    mock_risk = Risk(
        id=rid,
        title="Medium Vulnerability",
        description="...",
        methodology_id="mid",
        likelihood=3,
        impact=3,
        inherent_score=9,
        residual_score=9.0
    )

    with patch.object(
        Risk, "get", new_callable=AsyncMock, return_value=mock_risk
    ):
        payload = {"risk_id": str(rid)}
        response = client.post(
            "/risks/escalate", json=payload,
            headers={"X-Agent-ID": "risk-agent"}
        )
        assert response.status_code == 400
        assert "does not exceed the appetite tolerance" in (
            response.json()["detail"]
        )


@pytest.mark.asyncio
async def test_incident_trigger_high_severity():
    rid = PydanticObjectId()
    mock_risk = Risk(
        id=rid,
        title="Phishing Outbreak",
        description="...",
        methodology_id="mid",
        likelihood=2,
        impact=4,
        inherent_score=8,
        residual_score=8.0,
        control_effectiveness=0.0
    )

    with (
        patch.object(
            Risk, "get", new_callable=AsyncMock, return_value=mock_risk
        ),
        patch.object(Risk, "save", new_callable=AsyncMock) as mock_save,
        patch(
            "services.risk_mgmt_service.routers.risks.log_audit_event",
            new_callable=AsyncMock
        ) as mock_log
    ):

        payload = {
            "risk_id": str(rid),
            "incident_id": "inc-99",
            "description": "Active phishing wave detected",
            "severity": "HIGH"
        }

        response = client.post(
            "/risks/incident-trigger", json=payload,
            headers={"X-Agent-ID": "risk-agent"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["likelihood"] == 3
        assert data["inherent_score"] == 12
        assert data["residual_score"] == 12.0
        mock_save.assert_called_once()
        mock_log.assert_called_once()
