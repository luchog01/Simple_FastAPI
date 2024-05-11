from motor.motor_asyncio import AsyncIOMotorClient
from ....settings import MONGO_URI

DATABASE = "fcitracker-database"

class NotFoundException(Exception):
    def __init__(self, item_name: str):
        self.item_name = item_name
        super().__init__(f"{item_name} not found")

class AlreadyExistsException(Exception):
    def __init__(self, item_name: str):
        self.item_name = item_name
        super().__init__(f"{item_name} already exists")

class Database:
    client = None
    database = None

    @classmethod
    def connect(cls):
        print("Connecting to database")
        if cls.client is None:
            cls.client = AsyncIOMotorClient(MONGO_URI)
            cls.database = cls.client[DATABASE]

    @classmethod
    def close(cls):
        print("Closing database connection")
        if cls.client is not None:
            cls.client.close()
            cls.client = None
            cls.database = None
