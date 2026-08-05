import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from shared.database import DatabaseManager

@pytest.mark.asyncio
async def test_database_manager_initialize():
    # Instantiate a clean database manager to test its actual logic
    db_mgr = DatabaseManager()
    
    with patch("shared.database.AsyncIOMotorClient") as mock_motor, \
         patch("shared.database.init_beanie", new_callable=AsyncMock) as mock_init_beanie:
        
        mock_client_instance = MagicMock()
        mock_motor.return_value = mock_client_instance
        
        await db_mgr.initialize(document_models=[])
        
        mock_motor.assert_called_once()
        mock_init_beanie.assert_called_once_with(database=db_mgr.db, document_models=[])
        assert db_mgr.client == mock_client_instance
        assert db_mgr.db == mock_client_instance[db_mgr.db.name]

@pytest.mark.asyncio
async def test_database_manager_close():
    db_mgr = DatabaseManager()
    db_mgr.client = MagicMock()
    
    await db_mgr.close()
    
    db_mgr.client.close.assert_called_once()
