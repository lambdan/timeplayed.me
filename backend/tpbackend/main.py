import uvicorn
import asyncio
import os
from tpbackend.oblivionis import storage as oblivionisStorage, sync as oblivionisSync
from tpbackend.bot import bot
from tpbackend.storage import storage_v2
from fastapi import FastAPI

# from tpbackend.api import router as api_v1_deprecated
from tpbackend.api import router_not_deprecated as api_v1_not_deprecated
from tpbackend.api_v2_main import router as api_v2
from tpbackend.api_v2.users.routes import router as api_v2_users
from tpbackend.api_v2.discord.routes import router as api_v2_discord


async def start_api():
    app = FastAPI(title="Timeplayed")
    # app.include_router(api_v1_deprecated, prefix="/api", deprecated=True)
    # app.include_router(api_v1_not_deprecated, prefix="/api")
    app.include_router(api_v2, prefix="/api/v2")
    app.include_router(api_v2_users, prefix="/api/v2/users")
    app.include_router(api_v2_discord, prefix="/api/v2/discord")

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
    storage_v2.connect_db()
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
