import os
from shared.config import GlobalSettings

def test_config_load_defaults():
    # Test that defaults or environment variables loaded successfully
    settings = GlobalSettings()
    assert settings.environment in ["testing", "development", "production"]
    assert settings.port == 8000
    assert settings.mongo_uri == "mongodb://localhost:27017"
    assert settings.db_name == "test_db"
    assert settings.gcp_project == "mock-project"
    assert settings.gcs_bucket == "mock-bucket"
    assert settings.parquet_log_buffer_size == 5
    assert settings.parquet_archive_interval_seconds == 2
