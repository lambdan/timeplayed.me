import uvicorn
import asyncio
import os
from tpbackend.oblivionis import storage as oblivionisStorage, sync as oblivionisSync
from tpbackend.bot import bot
from tpbackend.storage import storage_v2
from fastapi import FastAPI
from tpbackend.api_v2.router import api_router

# from tpbackend.api import router as api_v1_deprecated


async def start_api():
    app = FastAPI(title="timeplayed")
    app.include_router(api_router)

    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def start_bot():
    await bot.start(os.environ["DISCORD_TOKEN"])


async def async_main():
    await asyncio.gather(
        start_api(), start_bot(), oblivionisSync.sync_loop(), storage_v2.clean_loop()
    )


def main():
    oblivionisStorage.connect_db()
    storage_v2.db.connect()
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
