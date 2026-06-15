from fastapi import APIRouter
from pydantic import BaseModel
from tpbackend.__version__ import __version__
import datetime

misc_router = APIRouter()
started = datetime.datetime.now()


@misc_router.get("/ping", tags=["misc"])
def ping():
    return "pong"


class Info(BaseModel):
    version: str
    uptime: int


@misc_router.get("/info", response_model=Info, tags=["misc"])
def info() -> Info:
    uptime = int((datetime.datetime.now() - started).total_seconds())
    return Info(version=__version__, uptime=uptime)
