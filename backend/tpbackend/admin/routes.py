from fastapi import APIRouter, Depends

from tpbackend.api.auth import authenticate_admin
from tpbackend.admin.activities import router as activities_router
from tpbackend.admin.games import router as games_router
from tpbackend.admin.misc import router as misc_router
from tpbackend.admin.platforms import router as platforms_router
from tpbackend.admin.users import router as users_router

# not in swagger, and every route requires admin permission
router = APIRouter(
    include_in_schema=False,
    dependencies=[Depends(authenticate_admin)],
)
router.include_router(users_router)
router.include_router(activities_router)
router.include_router(games_router)
router.include_router(platforms_router)
router.include_router(misc_router)
