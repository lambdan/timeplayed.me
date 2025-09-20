import uvicorn
import asyncio
import os
from tpbackend.oblivionis import storage as oblivionisStorage, sync as oblivionisSync
from tpbackend.bot import bot
from tpbackend.storage import storage_v2
from tpbackend.api import app

async def start_api():
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def start_bot():  
    await bot.start(os.environ["DISCORD_TOKEN"])

async def async_main():
    await asyncio.gather(
        start_api(),
        start_bot(),
        oblivionisSync.start()
    )

def main():
    oblivionisStorage.connect_db()
    storage_v2.connect_db()
    asyncio.run(async_main())

if __name__ == "__main__":
    main()