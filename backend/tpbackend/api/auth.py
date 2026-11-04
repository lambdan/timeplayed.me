from fastapi import Depends
from fastapi.openapi.models import HTTPBearer
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from tpbackend.__version__ import __version__
from tpbackend.storage import User
from tpbackend.api.responses import forbidden, unauthorized
from tpbackend.permissions import PERMISSION_ADMIN
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


def authenticate_admin(user: AuthenticatedUser) -> User:
    if user.has_permission(PERMISSION_ADMIN):
        return user
    return forbidden("Admin permission required")


AdminUser = Annotated[User, Depends(authenticate_admin)]
