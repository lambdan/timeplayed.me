import logging
from typing import cast

from fastapi import APIRouter

from tpbackend.admin.models import (
    Admin_PatchPlatform,
    Admin_Platform,
    Admin_PostPlatform,
    activity_count,
)
from tpbackend.api.auth import AdminUser
from tpbackend.api.responses import bad_request, not_found
from tpbackend.platform.query import PlatformQuery
from tpbackend.storage import LiveActivity, Platform, Platform_or_none, User

logger = logging.getLogger("admin-platforms")
router = APIRouter()


def __get_platform(platform_id: int) -> Platform:
    platform = Platform_or_none(platform_id)
    if not platform:
        return not_found("Platform not found")
    return platform


def __color(color: str | None) -> str | None:
    """colors are stored as hex without #"""
    if color is None:
        return None
    return color.strip().lstrip("#") or None


@router.get("/platforms", response_model=list[Admin_Platform])
def get_platforms() -> list[Admin_Platform]:
    query = PlatformQuery.apply_sort(PlatformQuery.base(), "id", "asc")
    return [Admin_Platform.from_platform(p) for p in query]


@router.post("/platform", response_model=Admin_Platform)
def add_platform(data: Admin_PostPlatform, admin: AdminUser) -> Admin_Platform:
    abbreviation = data.abbreviation.strip().lower()
    if not abbreviation:
        return bad_request("Abbreviation cannot be empty")
    if Platform.get_or_none(Platform.abbreviation == abbreviation):  # type: ignore
        return bad_request("Platform with that abbreviation already exists")
    platform = cast(Platform, Platform.create(abbreviation=abbreviation))
    platform.add_history(f"Platform added by admin {admin.get_name()}")
    platform.save()
    return Admin_Platform.from_platform(platform)


@router.patch("/platform/{platform_id}", response_model=Admin_Platform)
def patch_platform(
    platform_id: int, data: Admin_PatchPlatform, admin: AdminUser
) -> Admin_Platform:
    platform = __get_platform(platform_id)
    sent = data.model_fields_set

    if "abbreviation" in sent:
        abbreviation = (data.abbreviation or "").strip().lower()
        if not abbreviation:
            return bad_request("Abbreviation cannot be empty")
        if abbreviation != platform.get_abbreviation():
            other = Platform.get_or_none(Platform.abbreviation == abbreviation)  # type: ignore
            if other:
                return bad_request("Platform with that abbreviation already exists")
            platform.set_abbreviation(abbreviation)

    if "name" in sent:
        name = (data.name or "").strip() or None
        if name != platform.get_name():
            platform.set_name(name)

    if "color_primary" in sent:
        color = __color(data.color_primary)
        if color != platform.get_color_primary():
            platform.set_color_primary(color)

    if "color_secondary" in sent:
        color = __color(data.color_secondary)
        if color != platform.get_color_secondary():
            platform.set_color_secondary(color)

    if "icon" in sent:
        icon = (data.icon or "").strip() or None
        if icon != platform.get_icon():
            platform.set_icon(icon)

    if platform.pending_history:
        platform.add_history(f"Edited by admin {admin.get_name()}")
    platform.save()
    return Admin_Platform.from_platform(platform)


@router.delete("/platform/{platform_id}")
def delete_platform(platform_id: int, admin: AdminUser):
    platform = __get_platform(platform_id)
    if activity_count(platform=platform) > 0:
        return bad_request("Platform has activities")
    if User.select().where(User.default_platform == platform).count() > 0:  # type: ignore
        return bad_request("Platform is the default platform of a user")
    if LiveActivity.select().where(LiveActivity.platform == platform).count() > 0:  # type: ignore
        return bad_request("Platform has a live activity running")
    platform.delete_instance()
    logger.info("Platform %s deleted by admin %s", platform_id, admin.get_name())
    return "Deleted"
