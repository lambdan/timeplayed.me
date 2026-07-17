from fastapi import APIRouter, FastAPI
from pydantic import BaseModel
import uvicorn

from tpbackend.__version__ import __version__
from tpbackend.user.routes import router as user_router
from tpbackend.game.routes import router as game_router
from tpbackend.platform.routes import router as platform_router
from tpbackend.discord.routes import router as discord_router
from tpbackend.sgdb.routes import router as sgdb_router
from tpbackend.igdb.routes import router as igdb_router
from tpbackend.charts.routes import router as charts_router
from tpbackend.activity.routes import router as activity_router
from .misc import misc_router
import logging

logger = logging.getLogger("api")


class VersionInfo(BaseModel):
    version: str


def create_app():
    app = FastAPI(title="timeplayed", version=__version__)
    api_router = APIRouter(prefix="/api")

    api_router.include_router(misc_router)
    api_router.include_router(user_router)
    api_router.include_router(activity_router)
    api_router.include_router(game_router)
    api_router.include_router(platform_router)
    api_router.include_router(charts_router, prefix="/charts")
    api_router.include_router(discord_router, prefix="/discord")
    api_router.include_router(sgdb_router, prefix="/sgdb")
    api_router.include_router(igdb_router, prefix="/igdb")

    app.include_router(api_router)
    return app


async def run(host="0.0.0.0", port=8000, log_level="info"):
    config = uvicorn.Config(create_app(), host=host, port=port, log_level=log_level)
    server = uvicorn.Server(config)
    await server.serve()
