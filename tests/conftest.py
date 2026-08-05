import asyncio
import os
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set environment variables for tests before importing anything else
os.environ["ENVIRONMENT"] = "testing"
os.environ["PORT"] = "8000"
os.environ["MONGO_URI"] = "mongodb://localhost:27017"
os.environ["DB_NAME"] = "test_db"
os.environ["LOCAL_LOG_DIR"] = "./test_logs"
os.environ["GCP_PROJECT"] = "mock-project"
os.environ["GCS_BUCKET"] = "mock-bucket"
os.environ["PARQUET_LOG_BUFFER_SIZE"] = "5"
os.environ["PARQUET_ARCHIVE_INTERVAL_SECONDS"] = "2"

class MockClient:
    def __init__(self, *args, **kwargs):
        pass
    def __getitem__(self, name):
        return MockDatabase(name, self)
    def append_metadata(self, *args, **kwargs):
        pass
    def close(self):
        pass

class MockDatabase:
    def __init__(self, name, client):
        self.name = name
        self.client = client
    def __getitem__(self, name):
        return MockCollection(name, self)
    def get_collection(self, name):
        return MockCollection(name, self)
    async def list_collection_names(self, *args, **kwargs):
        return []
    async def command(self, *args, **kwargs):
        return {"version": "6.0"}

class MockCollection:
    def __init__(self, name, db):
        self.name = name
        self.database = db
    async def create_index(self, *args, **kwargs):
        return None
    async def index_information(self, *args, **kwargs):
        return {}
    async def find_one(self, *args, **kwargs):
        return None
    def find(self, *args, **kwargs):
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        return mock_cursor
    async def insert_one(self, *args, **kwargs):
        mock_result = MagicMock()
        mock_result.inserted_id = "mock_id"
        return mock_result

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
def init_beanie_for_tests():
    """Session fixture to initialize Beanie ODM on the MockClient."""
    from services.base_service.main import ServiceMetadata
    from services.governance_service.models.policy import Policy
    from services.governance_service.models.exception import PolicyException
    from services.governance_service.models.report import GovernanceReport
    from shared.database import db_manager

    # Run initialize with patched AsyncIOMotorClient
    with patch("shared.database.AsyncIOMotorClient", MockClient):
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(
                db_manager.initialize(
                    document_models=[
                        ServiceMetadata,
                        Policy,
                        PolicyException,
                        GovernanceReport,
                    ]
                )
            )
        finally:
            loop.close()
    yield

@pytest.fixture(autouse=True)
def mock_gcs_client():
    """Mock Google Cloud Storage Client to prevent network requests during tests."""
    with patch("shared.logging.storage.Client") as mock_client:
        mock_instance = MagicMock()
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        
        mock_instance.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.upload_from_filename = MagicMock()
        
        mock_client.return_value = mock_instance
        yield {
            "client": mock_instance,
            "bucket": mock_bucket,
            "blob": mock_blob
        }

@pytest.fixture
def mock_beanie_metadata():
    """Mock the ServiceMetadata Beanie document methods for endpoint testing."""
    from services.base_service.main import ServiceMetadata
    
    with patch.object(ServiceMetadata, "count", new_callable=AsyncMock) as mock_count, \
         patch.object(ServiceMetadata, "insert", new_callable=AsyncMock) as mock_insert, \
         patch.object(ServiceMetadata, "find_all") as mock_find_all, \
         patch.object(ServiceMetadata, "find_one", new_callable=AsyncMock) as mock_find_one:
         
        # Set up default returns
        mock_count.return_value = 1
        
        # mock find_all().to_list()
        mock_query = MagicMock()
        mock_query.to_list = AsyncMock(return_value=[])
        mock_find_all.return_value = mock_query
        
        # mock find_one() -> returns mock query
        mock_find_one.return_value = None
        
        yield {
            "count": mock_count,
            "insert": mock_insert,
            "find_all": mock_find_all,
            "find_one": mock_find_one
        }
