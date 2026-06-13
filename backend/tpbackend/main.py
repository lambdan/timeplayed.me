import asyncio
import os
from .oblivionis import storage as oblivionis_storage, sync as oblivionis_sync
from .discord.bot import bot
from tpbackend.storage import db, clean_loop
import tpbackend.api.api as api


async def start_api():
    await api.run()


async def start_bot():
    await bot.start(os.environ["DISCORD_TOKEN"])


async def async_main():
    await asyncio.gather(
        start_api(), start_bot(), oblivionis_sync.sync_loop(), clean_loop()
    )


def main():
    oblivionis_storage.connect_db()
    db.connect()
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
