import motor.motor_asyncio
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URI = os.getenv("DATABASE_URI")  # MongoDB URI for primary DB
SECONDDB_URI = os.getenv("SECONDDB_URI")  # MongoDB URI for secondary DB
DATABASE_NAME = os.getenv("DATABASE_NAME", "FilterBot")

class UserDatabase:
    def __init__(self, database_name=DATABASE_NAME):
        # Primary DB
        self._client = motor.motor_asyncio.AsyncIOMotorClient(DATABASE_URI)
        self.db = self._client[database_name]
        self.users = self.db.users
        self.chats = self.db.chats

        # Secondary DB
        self._client2 = motor.motor_asyncio.AsyncIOMotorClient(SECONDDB_URI)
        self.db2 = self._client2[database_name]
        self.users2 = self.db2.users
        self.chats2 = self.db2.chats

    async def get_banned(self):
        """Fetch banned users and chats from primary and secondary DBs."""
        banned_users = await self.users.find({"is_banned": True}).to_list(length=None)
        banned_chats = await self.chats.find({"is_banned": True}).to_list(length=None)
        banned_users2 = await self.users2.find({"is_banned": True}).to_list(length=None)
        banned_chats2 = await self.chats2.find({"is_banned": True}).to_list(length=None)
        
        return {
            "banned_users": banned_users + banned_users2,
            "banned_chats": banned_chats + banned_chats2,
        }

# Create the db instance
db = UserDatabase()
