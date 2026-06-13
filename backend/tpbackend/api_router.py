from fastapi import APIRouter

# from tpbackend.api_v2_main import router as api_v2
from .user.routes import router as api_v2_users
from .game.routes import router as api_v2_games
from .platform.routes import router as api_v2_platforms
from .discord.routes import router as api_v2_discord
from .sgdb.routes import router as sgdb_router
from .charts.routes import router as charts_router
from .activity.routes import router as activities_router

api_router = APIRouter(prefix="/api")

# api_router.include_router(api)
# api_router.include_router(api_v2)
api_router.include_router(api_v2_users)
api_router.include_router(activities_router)
api_router.include_router(api_v2_games)
api_router.include_router(api_v2_platforms)

api_router.include_router(charts_router, prefix="/charts")
api_router.include_router(api_v2_discord, prefix="/discord")
api_router.include_router(sgdb_router, prefix="/sgdb")
