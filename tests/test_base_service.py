import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from services.base_service.main import app, ServiceMetadata

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "base_service"}

@pytest.mark.asyncio
async def test_ready_endpoint_success(mock_beanie_metadata):
    mock_beanie_metadata["count"].return_value = 1
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
    mock_beanie_metadata["count"].assert_called_once()

@pytest.mark.asyncio
async def test_ready_endpoint_db_failure(mock_beanie_metadata):
    mock_beanie_metadata["count"].side_effect = Exception("DB Connection Timeout")
    response = client.get("/ready")
    assert response.status_code == 503
    assert "Database unreachable" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_metadata_endpoint(mock_beanie_metadata):
    mock_record = ServiceMetadata(name="Base Template Service", status="ONLINE", last_updated=datetime.now(timezone.utc))
    mock_beanie_metadata["find_all"].return_value.to_list = AsyncMock(return_value=[mock_record])
    
    with patch("services.base_service.main.log_audit_event", new_callable=AsyncMock) as mock_log:
        response = client.get("/metadata", headers={"X-Agent-ID": "test-agent"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Base Template Service"
        assert data[0]["status"] == "ONLINE"
        
        # Verify audit log was triggered
        mock_log.assert_called_once()
        log_args = mock_log.call_args[1]
        assert log_args["event_type"] == "METADATA_READ"
        assert log_args["agent_identity"] == "test-agent"

@pytest.mark.asyncio
async def test_update_status_endpoint_not_found(mock_beanie_metadata):
    mock_beanie_metadata["find_one"].return_value = None
    
    response = client.post(
        "/metadata/status",
        headers={"X-Agent-ID": "test-agent"},
        json={"status": "OFFLINE"}
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_update_status_endpoint_success(mock_beanie_metadata):
    mock_record = ServiceMetadata(name="Base Template Service", status="ONLINE", last_updated=datetime.now(timezone.utc))
    mock_beanie_metadata["find_one"].return_value = mock_record
    
    with patch("services.base_service.main.log_audit_event", new_callable=AsyncMock) as mock_log, \
         patch.object(ServiceMetadata, "save", new_callable=AsyncMock) as mock_save:
        response = client.post(
            "/metadata/status",
            headers={"X-Agent-ID": "test-agent"},
            json={"status": "MAINTENANCE"}
        )
        assert response.status_code == 200
        
        # Verify DB save was called and updated status
        assert mock_record.status == "MAINTENANCE"
        mock_save.assert_called_once()
        
        # Verify warning audit log
        mock_log.assert_called_once()
        log_args = mock_log.call_args[1]
        assert log_args["event_type"] == "STATUS_CHANGED"
        assert log_args["severity"] == "WARNING"

@pytest.mark.asyncio
async def test_lifespan_handler():
    from services.base_service.main import lifespan
    
    with patch("services.base_service.main.asyncio.create_task") as mock_create_task, \
         patch("services.base_service.main.ServiceMetadata.count", new_callable=AsyncMock) as mock_count, \
         patch("services.base_service.main.ServiceMetadata.insert", new_callable=AsyncMock) as mock_insert, \
         patch("services.base_service.main.db_manager.initialize", new_callable=AsyncMock) as mock_init, \
         patch("services.base_service.main.flush_logs_to_parquet", new_callable=AsyncMock) as mock_flush, \
         patch("services.base_service.main.db_manager.close", new_callable=AsyncMock) as mock_close:
         
        mock_count.return_value = 0
        
        async with lifespan(app=None):
            # Verify startup actions
            mock_init.assert_called_once()
            mock_create_task.assert_called_once()
            mock_count.assert_called_once()
            mock_insert.assert_called_once()
            
            # Shutdown actions should not be called yet
            mock_flush.assert_not_called()
            mock_close.assert_not_called()
            
        # Verify shutdown actions are called after exiting the context
        mock_flush.assert_called_once()
        mock_close.assert_called_once()
