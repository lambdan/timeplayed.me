from fastapi import Depends
from fastapi.openapi.models import HTTPBearer
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from tpbackend.__version__ import __version__
from tpbackend.storage import User
from tpbackend.api.responses import unauthorized
from tpbackend.user.tokens import lookup_user
import logging

from typing import Annotated

logger = logging.getLogger("api-authenticate")

security = HTTPBearer()


def authenticate(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    token = credentials.credentials
    user = lookup_user(token)
    if user:
        return user
    return unauthorized()


AuthenticatedUser = Annotated[User, Depends(authenticate)]
