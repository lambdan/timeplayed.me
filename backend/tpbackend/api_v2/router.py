from fastapi import APIRouter

# from tpbackend.api_v2_main import router as api_v2
from tpbackend.api_v2.users.routes import router as api_v2_users
from tpbackend.api_v2.discord.routes import router as api_v2_discord
from tpbackend.api_v2.sgdb.routes import router as sgdb_router
from tpbackend.api_v2.charts.routes import router as charts_router

api_router = APIRouter(prefix="/api")

# api_router.include_router(api)
# api_router.include_router(api_v2)
api_router.include_router(api_v2_users, prefix="/users")

api_router.include_router(charts_router, prefix="/charts")


api_router.include_router(api_v2_discord, prefix="/discord")

api_router.include_router(sgdb_router, prefix="/sgdb")
