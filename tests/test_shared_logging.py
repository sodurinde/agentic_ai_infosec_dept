import os
import shutil
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import pandas as pd
import pyarrow.parquet as pq

import shared.logging
from shared.logging import log_audit_event, flush_logs_to_parquet, start_periodic_parquet_archiver
from shared.config import settings

@pytest.fixture(autouse=True)
def clean_log_dir():
    # Make sure _log_buffer is empty before each test
    shared.logging._log_buffer.clear()
    yield
    # Clean up test_logs directory
    if os.path.exists(settings.local_log_dir):
        shutil.rmtree(settings.local_log_dir)
    shared.logging._log_buffer.clear()

@pytest.mark.asyncio
async def test_log_audit_event_buffers_and_inserts():
    mock_collection = AsyncMock()
    
    details = {"action": "test"}
    await log_audit_event(
        event_type="TEST_EVENT",
        agent_identity="test-agent",
        details=details,
        severity="INFO",
        db_collection=mock_collection
    )
    
    # Check MongoDB insert was called
    mock_collection.insert_one.assert_called_once()
    inserted_arg = mock_collection.insert_one.call_args[0][0]
    assert inserted_arg["event_type"] == "TEST_EVENT"
    assert inserted_arg["agent_identity"] == "test-agent"
    assert inserted_arg["severity"] == "INFO"
    
    # Check buffer contains the record
    assert len(shared.logging._log_buffer) == 1
    assert shared.logging._log_buffer[0]["event_type"] == "TEST_EVENT"

@pytest.mark.asyncio
async def test_flush_logs_to_parquet():
    # Setup log buffer with a few records
    for i in range(3):
        shared.logging._log_buffer.append({
            "timestamp": f"2026-08-05T09:00:0{i}",
            "event_id": f"id-{i}",
            "event_type": "DUMMY_EVENT",
            "agent_identity": "dummy-agent",
            "details_json": '{"info": "test"}',
            "severity": "INFO"
        })
        
    # Flush logs
    await flush_logs_to_parquet()
    
    # Buffer should be cleared
    assert len(shared.logging._log_buffer) == 0
    
    # Check local file was created
    assert os.path.exists(settings.local_log_dir)
    files = os.listdir(settings.local_log_dir)
    assert len(files) == 1
    assert files[0].endswith(".parquet")
    
    # Read the parquet file back and check content and schema
    filepath = os.path.join(settings.local_log_dir, files[0])
    table = pq.read_table(filepath)
    df = table.to_pandas()
    assert len(df) == 3
    assert list(df.columns) == ['timestamp', 'event_id', 'event_type', 'agent_identity', 'details_json', 'severity']
    assert df.iloc[0]['event_id'] == 'id-0'

@pytest.mark.asyncio
async def test_periodic_parquet_archiver():
    with patch("shared.logging.flush_logs_to_parquet", new_callable=AsyncMock) as mock_flush:
        # We patch asyncio.sleep to raise CancelledError after being called once to stop infinite loop
        call_count = 0
        async def mock_sleep(delay):
            nonlocal call_count
            call_count += 1
            if call_count > 1:
                raise asyncio.CancelledError()
            
        with patch("asyncio.sleep", side_effect=mock_sleep):
            try:
                await start_periodic_parquet_archiver()
            except asyncio.CancelledError:
                pass
                
        mock_flush.assert_called()
