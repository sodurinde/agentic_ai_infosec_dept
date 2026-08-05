import logging
from typing import List, Type, Any
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie, Document
from shared.config import settings

logger = logging.getLogger("shared.database")

class DatabaseManager:
    def __init__(self):
        self.client: AsyncIOMotorClient = None
        self.db: Any = None

    async def initialize(self, document_models: List[Type[Document]] = None):
        """
        Initializes MongoDB connection and Beanie ODM.
        """
        try:
            logger.info(f"Connecting to MongoDB at {settings.mongo_uri}")
            self.client = AsyncIOMotorClient(settings.mongo_uri)
            self.db = self.client[settings.db_name]
            
            # Initialise Beanie with the given document models
            models = document_models if document_models else []
            await init_beanie(database=self.db, document_models=models)
            logger.info("MongoDB and Beanie ODM initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise e

    async def close(self):
        if self.client:
            self.client.close()
            logger.info("MongoDB client connection closed.")

db_manager = DatabaseManager()
