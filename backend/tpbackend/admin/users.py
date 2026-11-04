import logging
from typing import cast

from fastapi import APIRouter

from tpbackend.admin.models import (
    Admin_DiscordHistory,
    Admin_PostUser,
    Admin_SetPermissions,
    Admin_User,
    Admin_UserDetails,
)
from tpbackend.api.auth import AdminUser
from tpbackend.api.params import limit, offset, query_search
from tpbackend.api.responses import bad_request, not_found
from tpbackend.permissions import ALL_PERMISSIONS, PERMISSION_ADMIN
from tpbackend.storage import DiscordHistory, User, User_or_none
from tpbackend.user.query import UserQuery
from tpbackend.utils2 import clamp

logger = logging.getLogger("admin-users")
router = APIRouter()


def __get_user(user_id: int) -> User:
    user = User_or_none(user_id)
    if not user:
        return not_found("User not found")
    return user


@router.get("/permissions", response_model=list[str])
def get_all_permissions() -> list[str]:
    return ALL_PERMISSIONS


@router.get("/users", response_model=list[Admin_User])
def get_users(
    offset=offset(), limit=limit(), search=query_search("users")
) -> list[Admin_User]:
    query = UserQuery.base()
    query = UserQuery.search(query, search=search)
    query = UserQuery.apply_sort(query, "id", "asc")
    query = query.offset(max(0, int(offset))).limit(clamp(int(limit), 1, 100))
    return [Admin_User.from_user(u) for u in query]


@router.post("/user", response_model=Admin_UserDetails)
def add_user(data: Admin_PostUser, admin: AdminUser) -> Admin_UserDetails:
    """users without discord, eg for testing"""
    name = data.name.strip()
    if not name:
        return bad_request("Name cannot be empty")
    display_name = (data.display_name or "").strip() or None
    user = cast(User, User.create(name=name, display_name=display_name))
    user.add_history(f"User added by admin {admin.get_name()}")
    user.save()
    # reload, a freshly created user has the default platform object in default_platform_id
    return Admin_UserDetails.from_user(__get_user(user.get_id()))


@router.get("/user/{user_id}", response_model=Admin_UserDetails)
def get_user(user_id: int) -> Admin_UserDetails:
    return Admin_UserDetails.from_user(__get_user(user_id))


@router.put("/user/{user_id}/permissions", response_model=Admin_UserDetails)
def set_permissions(
    user_id: int, data: Admin_SetPermissions, admin: AdminUser
) -> Admin_UserDetails:
    user = __get_user(user_id)
    for permission in data.permissions:
        if permission not in ALL_PERMISSIONS:
            return bad_request(f"Invalid permission '{permission}'")
    if user.get_id() == admin.get_id() and PERMISSION_ADMIN not in data.permissions:
        return bad_request("You can't remove your own admin permission")

    for permission in list(user.get_permissions()):
        if permission not in data.permissions:
            user.remove_permission(permission)
    for permission in data.permissions:
        user.add_permission(permission)
    user.add_history(f"Permissions set by admin {admin.get_name()}")
    user.save()
    return Admin_UserDetails.from_user(user)


@router.delete("/user/{user_id}")
def delete_user(user_id: int, admin: AdminUser):
    user = __get_user(user_id)
    if user.get_id() == admin.get_id():
        return bad_request("You can't delete yourself")
    # activities, live activities, tokens and history are deleted by cascade
    user.delete_instance()
    logger.info(
        "User %s '%s' deleted by admin %s",
        user_id,
        user.get_name(),
        admin.get_name(),
    )
    return "Deleted"


@router.get(
    "/user/{user_id}/discord_history", response_model=list[Admin_DiscordHistory]
)
def get_discord_history(
    user_id: int, offset=offset(), limit=limit()
) -> list[Admin_DiscordHistory]:
    user = __get_user(user_id)
    if not user.get_discord_id():
        return []
    query = (
        DiscordHistory.select()
        .where(DiscordHistory.user == user.get_discord_id())  # type: ignore
        .order_by(DiscordHistory.timestamp.desc())  # type: ignore
        .offset(max(0, int(offset)))
        .limit(clamp(int(limit), 1, 100))
    )
    return [
        Admin_DiscordHistory.from_discord_history(cast(DiscordHistory, e))
        for e in query
    ]
