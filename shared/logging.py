import os
import json
import time
import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from google.cloud import storage

from shared.config import settings

# Setup standard logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("shared.logging")

# In-memory buffer for logs before archiving to Parquet
_log_buffer: List[Dict[str, Any]] = []
_buffer_lock = asyncio.Lock()

async def log_audit_event(
    event_type: str,
    agent_identity: str,
    details: Dict[str, Any],
    severity: str = "INFO",
    db_collection = None
):
    """
    Logs an audit event to MongoDB for real-time access and buffers it for long-term Parquet archiving.
    """
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_id": os.urandom(8).hex(),
        "event_type": event_type,
        "agent_identity": agent_identity,
        "details_json": json.dumps(details),
        "severity": severity
    }
    
    # 1. Hot Storage (MongoDB) - if DB collection is supplied
    if db_collection is not None:
        try:
            await db_collection.insert_one(event.copy())
        except Exception as e:
            logger.error(f"Failed to log event to MongoDB hot storage: {e}")

    # 2. Buffering for Cold Storage (Parquet)
    async with _buffer_lock:
        _log_buffer.append(event)
        buffer_size = len(_log_buffer)

    logger.info(f"[{severity}] Audit Log: {event_type} by {agent_identity}")

    # Trigger flush if buffer limit is reached
    if buffer_size >= settings.parquet_log_buffer_size:
        # Run flush in background to not block the current request
        asyncio.create_task(flush_logs_to_parquet())


async def flush_logs_to_parquet():
    """
    Flushes buffered log records, writes them to a local Parquet file, and uploads to GCS.
    """
    global _log_buffer
    
    async with _buffer_lock:
        if not _log_buffer:
            return
        records_to_write = list(_log_buffer)
        _log_buffer.clear()

    logger.info(f"Archiving {len(records_to_write)} records to Parquet cold storage...")
    
    # Convert list of dicts to DataFrame
    df = pd.DataFrame(records_to_write)
    
    # Define exact schema for Parquet
    schema = pa.schema([
        ('timestamp', pa.string()),
        ('event_id', pa.string()),
        ('event_type', pa.string()),
        ('agent_identity', pa.string()),
        ('details_json', pa.string()),
        ('severity', pa.string())
    ])
    
    table = pa.Table.from_pandas(df, schema=schema)
    
    # Make sure local directory exists
    os.makedirs(settings.local_log_dir, exist_ok=True)
    
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    file_name = f"audit_logs_{timestamp_str}.parquet"
    local_path = os.path.join(settings.local_log_dir, file_name)
    
    try:
        # Write Parquet locally with Snappy compression
        pq.write_table(table, local_path, compression='SNAPPY')
        logger.info(f"Local Parquet archive written: {local_path}")
        
        # Upload to Google Cloud Storage
        await upload_parquet_to_gcs(local_path, file_name)
    except Exception as e:
        logger.error(f"Error during Parquet archiving process: {e}. Fallback local file remains at {local_path}")


async def upload_parquet_to_gcs(local_path: str, file_name: str):
    """
    Uploads the local Parquet archive to GCS.
    """
    try:
        # Run blocking GCS client call in a separate thread pool executor
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _sync_upload_to_gcs, local_path, file_name)
    except Exception as e:
        logger.error(f"Failed to upload Parquet to Google Cloud Storage: {e}. Local file preserved.")


def _sync_upload_to_gcs(local_path: str, file_name: str):
    storage_client = storage.Client(project=settings.gcp_project)
    bucket = storage_client.bucket(settings.gcs_bucket)
    
    # Organise logs by date: YYYY/MM/DD/file_name
    date_prefix = datetime.now(timezone.utc).strftime("%Y/%m/%d")
    blob_path = f"logs/{date_prefix}/{file_name}"
    
    blob = bucket.blob(blob_path)
    blob.upload_from_filename(local_path)
    logger.info(f"Parquet log successfully uploaded to GCS: gs://{settings.gcs_bucket}/{blob_path}")


async def start_periodic_parquet_archiver():
    """
    Background loop that flushes logs periodically.
    """
    while True:
        await asyncio.sleep(settings.parquet_archive_interval_seconds)
        try:
            await flush_logs_to_parquet()
        except Exception as e:
            logger.error(f"Error in periodic log archiver: {e}")
