import os
from pyrogram import Client
import asyncio
import logging

PREMIUM_SESSION = os.environ.get("PREMIUM_SESSION", "pyrogram session")              
BOT_USERNAME = os.environ.get("BOT_USERNAME", "Rename_bot")

def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)

class User(Client):
    def init(self):
        super().init(
            PREMIUM_SESSION,
            api_hash=Config.API_HASH,
            api_id=Config.API_ID,
            workers=50
        )
        self.LOGGER = LOGGER

    async def start(self):
        await super().start()
        if BOT_USERNAME:
            await User.send_message(self, chat_id=BOT_USERNAME, text="🚀 BOT WORK STARTED ❤️‍🔥")
        usr_bot_me = await self.get_me()
        return (self, usr_bot_me.id)

    async def stop(self, *args):
        await super().stop()
        self.LOGGER(name).info("Bot stopped. Bye.")
