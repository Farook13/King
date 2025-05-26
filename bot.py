import logging
import logging.config
from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from database.ia_filterdb import Media, Media2, choose_mediaDB, db as clientDB
from database.users_chats_db import db
from info import SESSION, API_ID, API_HASH, BOT_TOKEN, LOG_STR, LOG_CHANNEL, SECONDDB_URI
from utils import temp
from typing import Union, Optional, AsyncGenerator
from pyrogram import types
from Script import script 
from datetime import date, datetime 
import pytz
from sample_info import tempDict
import sys

# Setup logging
logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("imdbpy").setLevel(logging.ERROR)

class Bot(Client):
    def __init__(self):
        super().__init__(
            name=SESSION,
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            workers=200,
            plugins={"root": "plugins"},
            sleep_threshold=10,
        )

    async def start(self):
        try:
            b_users, b_chats = await db.get_banned()
            temp.BANNED_USERS = b_users
            temp.BANNED_CHATS = b_chats
        except Exception as e:
            logging.error(f"Failed to get banned users/chats: {e}")
            sys.exit(1)

        await super().start()

        try:
            await Media.ensure_indexes()
            await Media2.ensure_indexes()

            stats = await clientDB.command('dbStats')
            free_db_size = round(512 - ((stats['dataSize'] / (1024 * 1024)) + (stats['indexSize'] / (1024 * 1024))), 2)

            if SECONDDB_URI and free_db_size < 10:
                tempDict["indexDB"] = SECONDDB_URI
                logging.info(f"Primary DB space low ({free_db_size}MB), switching to secondary DB.")
            elif not SECONDDB_URI:
                logging.error("SECONDDB_URI not set. Exiting.")
                sys.exit(1)
            else:
                logging.info(f"Primary DB has enough space ({free_db_size}MB).")

            await choose_mediaDB()

            me = await self.get_me()
            temp.ME = me.id
            temp.U_NAME = me.username
            temp.B_NAME = me.first_name
            self.username = '@' + me.username

            logging.info(f"{me.first_name} (v{__version__} - Layer {layer}) started as @{me.username}")
            logging.info(LOG_STR)
            logging.info(script.LOGO)

            tz = pytz.timezone('Asia/Kolkata')
            now = datetime.now(tz)
            today = date.today()
            time = now.strftime("%H:%M:%S %p")
            await self.send_message(chat_id=LOG_CHANNEL, text=script.RESTART_TXT.format(today, time))

        except Exception as e:
            logging.exception("Startup failed.")
            await self.stop()
            sys.exit(1)

    async def stop(self, *args):
        await super().stop()
        logging.info("Bot stopped. Bye.")

    async def iter_messages(
        self,
        chat_id: Union[int, str],
        limit: int,
        offset: int = 0,
    ) -> Optional[AsyncGenerator["types.Message", None]]:
        current = offset
        while True:
            new_diff = min(200, limit - current)
            if new_diff <= 0:
                return
            messages = await self.get_messages(chat_id, list(range(current, current + new_diff + 1)))
            for message in messages:
                yield message
                current += 1

app = Bot()
app.run()
