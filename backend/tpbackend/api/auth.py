from fastapi import Depends
from fastapi.openapi.models import HTTPBearer
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from tpbackend.__version__ import __version__
from tpbackend.storage import Token, User
from tpbackend.api.responses import forbidden, unauthorized
from tpbackend.history_actor import set_history_actor
from tpbackend.permissions import Permission
from tpbackend.user.tokens import lookup_token, lookup_user
import logging

from typing import Annotated

logger = logging.getLogger("api-authenticate")

security = HTTPBearer()


def authenticate(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    token = credentials.credentials
    user = lookup_user(token)
    if user:
        # changes made in this request are theirs
        set_history_actor(user)
        return user
    return unauthorized()


AuthenticatedUser = Annotated[User, Depends(authenticate)]

optional_security = HTTPBearer(auto_error=False)


def authenticate_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_security),
) -> User | None:
    """for routes that work without logging in, but show more to some users"""
    if not credentials:
        return None
    return lookup_user(credentials.credentials)


OptionalUser = Annotated[User | None, Depends(authenticate_optional)]


def current_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Token:
    """the token the request was made with"""
    token = lookup_token(credentials.credentials)
    if token:
        return token
    return unauthorized()


CurrentToken = Annotated[Token, Depends(current_token)]


def authenticate_admin(user: AuthenticatedUser) -> User:
    if user.has_permission(Permission.ADMIN):
        return user
    return forbidden("Admin permission required")


AdminUser = Annotated[User, Depends(authenticate_admin)]


def authenticate_manual_activity(user: AuthenticatedUser) -> User:
    # adding activity (manual tracking page, API) and changing its game or platform,
    # what could be used to inflate the numbers
    if user.has_permission(Permission.MANUAL_ACTIVITY):
        return user
    return forbidden("Manual activity permission required")


ManualActivityUser = Annotated[User, Depends(authenticate_manual_activity)]
