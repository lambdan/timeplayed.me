import asyncio
from .oblivionis import storage as oblivionis_storage, sync as oblivionis_sync
from .discord.bot import bot
from tpbackend.globals import (
    DISCORD_ENABLED,
    DISCORD_TOKEN,
    IGDB_ENABLED,
    OBLIVIONIS_ENABLED,
    SGDB_ENABLED,
)
from tpbackend.storage import db, clean_loop
from tpbackend import evolutions
import tpbackend.api.api as api
import logging

logger = logging.getLogger("main")


async def start_api():
    await api.run()


async def start_bot():
    await bot.start(DISCORD_TOKEN)


def log_integrations():
    def status(enabled: bool) -> str:
        return "enabled" if enabled else "disabled"

    logger.info("Discord: %s (DISCORD_TOKEN)", status(DISCORD_ENABLED))
    logger.info("SGDB: %s (SGDB_TOKEN)", status(SGDB_ENABLED))
    logger.info("IGDB: %s (IGDB_CLIENT_ID, IGDB_CLIENT_SECRET)", status(IGDB_ENABLED))
    logger.info("Oblivionis sync: %s (OBLIVIONIS_DB)", status(OBLIVIONIS_ENABLED))


async def async_main():
    tasks = [start_api(), clean_loop()]
    if DISCORD_ENABLED:
        tasks.append(start_bot())
    if OBLIVIONIS_ENABLED:
        tasks.append(oblivionis_sync.sync_loop())
    await asyncio.gather(*tasks)


def main():
    log_integrations()
    evolutions.apply(db.database, **db.connect_params)
    if OBLIVIONIS_ENABLED:
        oblivionis_storage.connect_db()
    db.connect()
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
