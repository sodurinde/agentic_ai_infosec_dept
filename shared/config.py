import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class GlobalSettings(BaseSettings):
    # App Env
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")
    port: int = Field(default=8000, validation_alias="PORT")

    # MongoDB Setup
    mongo_uri: str = Field(default="mongodb://localhost:27017", validation_alias="MONGO_URI")
    db_name: str = Field(default="bank_infosec", validation_alias="DB_NAME")

    # GCP Setup
    gcp_project: str = Field(default="bank-infosec-prod", validation_alias="GCP_PROJECT")
    gcs_bucket: str = Field(default="bank-audit-logs", validation_alias="GCS_BUCKET")

    # Proxmox Setup
    proxmox_node: str = Field(default="pve-node-1", validation_alias="PROXMOX_NODE")

    # Logging & Parquet settings
    local_log_dir: str = Field(default="/var/log/bank_infosec", validation_alias="LOCAL_LOG_DIR")
    parquet_log_buffer_size: int = Field(default=1000, validation_alias="PARQUET_LOG_BUFFER_SIZE")
    parquet_archive_interval_seconds: int = Field(default=3600, validation_alias="PARQUET_ARCHIVE_INTERVAL_SECONDS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = GlobalSettings()
