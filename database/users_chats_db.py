import motor.motor_asyncio
from info import DATABASE_URI, DATABASE_NAME, SECONDDB_URI

class UserDatabase:
    def __init__(self, database_name):
        # primary db
        self._client = motor.motor_asyncio.AsyncIOMotorClient(DATABASE_URI)
        self.db = self._client[database_name]
        self.users = self.db.users
        self.groups = self.db.groups

        # secondary db
        self._client2 = motor.motor_asyncio.AsyncIOMotorClient(SECONDDB_URI)
        self.db2 = self._client2[database_name]
        self.users2 = self.db2.users
        self.groups2 = self.db2.groups

    def new_user(self, user_id, name):
        return dict(
            id=user_id,
            name=name,
            ban_status=dict(
                is_banned=False,
                ban_reason=""
            ),
            verification_status=dict(
                date="1999-12-31",
                time="23:59:59"
            )
        )

    def new_group(self, group_id, title):
        return dict(
            id=group_id,
            title=title,
            chat_status=dict(
                is_disabled=False,
                reason=""
            ),
            settings=dict()  # Add default settings if needed
        )

    async def add_user(self, user_id, name, use_primary_db=True):
        user = self.new_user(user_id, name)
        if use_primary_db:
            await self.users.insert_one(user)
        else:
            await self.users2.insert_one(user)

    async def is_user_exist(self, user_id):
        user = await self.users.find_one({'id': user_id})
        if user:
            return True
        user = await self.users2.find_one({'id': user_id})
        return user is not None

    async def ban_user(self, user_id, reason="No Reason"):
        ban_status = dict(is_banned=True, ban_reason=reason)
        user = await self.users.find_one({'id': user_id})
        if user:
            await self.users.update_one({'id': user_id}, {'$set': {'ban_status': ban_status}})
        else:
            await self.users2.update_one({'id': user_id}, {'$set': {'ban_status': ban_status}})

    async def remove_ban(self, user_id):
        ban_status = dict(is_banned=False, ban_reason="")
        user = await self.users.find_one({'id': user_id})
        if user:
            await self.users.update_one({'id': user_id}, {'$set': {'ban_status': ban_status}})
        else:
            await self.users2.update_one({'id': user_id}, {'$set': {'ban_status': ban_status}})

    async def get_ban_status(self, user_id):
        default = dict(is_banned=False, ban_reason="")
        user = await self.users.find_one({'id': user_id})
        if user:
            return user.get('ban_status', default)
        user = await self.users2.find_one({'id': user_id})
        if user:
            return user.get('ban_status', default)
        return default

    async def update_verification(self, user_id, date, time):
        status = dict(date=str(date), time=str(time))
        user = await self.users.find_one({'id': user_id})
        if user:
            await self.users.update_one({'id': user_id}, {'$set': {'verification_status': status}})
        else:
            await self.users2.update_one({'id': user_id}, {'$set': {'verification_status': status}})

    async def get_verification(self, user_id):
        default = dict(date="1999-12-31", time="23:59:59")
        user = await self.users.find_one({'id': user_id})
        if user:
            return user.get('verification_status', default)
        user = await self.users2.find_one({'id': user_id})
        if user:
            return user.get('verification_status', default)
        return default

    async def total_users_count(self):
        count1 = await self.users.count_documents({})
        count2 = await self.users2.count_documents({})
        return count1 + count2

    async def get_all_users(self):
        users1 = await self.users.find({}).to_list(length=None)
        users2 = await self.users2.find({}).to_list(length=None)
        return users1 + users2

    async def delete_user(self, user_id):
        deleted1 = await self.users.delete_many({'id': user_id})
        deleted2 = await self.users2.delete_many({'id': user_id})
        return deleted1.deleted_count + deleted2.deleted_count


# Usage
user_db = UserDatabase(DATABASE_NAME)
