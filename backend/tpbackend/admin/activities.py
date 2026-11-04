import datetime
import logging
from typing import cast

from fastapi import APIRouter

from tpbackend.activity.query import ActivityQuery
from tpbackend.admin.models import (
    Admin_Activity,
    Admin_ActivityDetails,
    Admin_MoveActivities,
    Admin_Moved,
    Admin_OverlapGroup,
    Admin_OverlapsMerged,
    Admin_PatchActivity,
)
from tpbackend.api.auth import AdminUser
from tpbackend.api.params import limit, offset, query_id
from tpbackend.api.responses import bad_request, not_found
from tpbackend.game.select import GameSelect
from tpbackend.globals import MINIMUM_SESSION_LENGTH
from tpbackend.operations import find_overlapping_groups, merge_overlapping_group
from tpbackend.storage import (
    Activity,
    Activity_or_none,
    Platform_or_none,
    User_or_none,
    db,
)
from tpbackend.utils2 import clamp

logger = logging.getLogger("admin-activities")
router = APIRouter()


def __get_activity(activity_id: int) -> Activity:
    activity = Activity_or_none(activity_id, include_hidden=True)
    if not activity:
        return not_found("Activity not found")
    return activity


@router.get("/activities", response_model=list[Admin_Activity])
def get_activities(
    offset=offset(),
    limit=limit(),
    user=query_id("user"),
    game=query_id("game"),
    platform=query_id("platform"),
) -> list[Admin_Activity]:
    query = ActivityQuery.base(include_hidden=True)
    if user is not None:
        query = ActivityQuery.user(query, user)
    if game is not None:
        query = ActivityQuery.game(query, game)
    if platform is not None:
        query = ActivityQuery.platform(query, platform)
    query = ActivityQuery.apply_sort(query, "timestamp", "desc")
    query = query.offset(max(0, int(offset))).limit(clamp(int(limit), 1, 100))
    return [Admin_Activity.from_activity(a) for a in query]


@router.get("/activity/{activity_id}", response_model=Admin_ActivityDetails)
def get_activity(activity_id: int) -> Admin_ActivityDetails:
    return Admin_ActivityDetails.from_activity(__get_activity(activity_id))


@router.patch("/activity/{activity_id}", response_model=Admin_ActivityDetails)
def patch_activity(
    activity_id: int, data: Admin_PatchActivity, admin: AdminUser
) -> Admin_ActivityDetails:
    activity = __get_activity(activity_id)
    sent = data.model_fields_set

    if "game_id" in sent:
        if data.game_id is None:
            return bad_request("game_id cannot be null")
        game = GameSelect.by_id(data.game_id)
        if not game:
            return not_found("Game not found")
        if game.get_id() != activity.get_game().get_id():
            activity.set_game(game)

    if "platform_id" in sent:
        platform = Platform_or_none(data.platform_id)
        if not platform:
            return not_found("Platform not found")
        if platform.get_id() != activity.get_platform().get_id():
            activity.set_platform(platform)

    if "user_id" in sent:
        user = User_or_none(data.user_id)
        if not user:
            return not_found("User not found")
        if user.get_id() != activity.get_user().get_id():
            activity.set_user(user)

    if "seconds" in sent:
        if data.seconds is None or data.seconds <= 0:
            return bad_request("seconds must be positive")
        if data.seconds < MINIMUM_SESSION_LENGTH:
            return bad_request(
                f"Activity must be at least {MINIMUM_SESSION_LENGTH} seconds long"
            )
        if data.seconds != activity.get_seconds():
            activity.set_seconds(data.seconds)

    if "ended" in sent:
        if data.ended is None:
            return bad_request("ended cannot be null")
        ended = datetime.datetime.fromtimestamp(
            data.ended / 1000, tz=datetime.timezone.utc
        )
        if ended != activity.get_ended():
            activity.set_datetime(ended)

    if "hidden" in sent:
        if data.hidden is None:
            return bad_request("hidden cannot be null")
        if data.hidden != activity.get_hidden():
            activity.set_hidden(data.hidden)

    if activity.pending_history:
        activity.add_history(f"Edited by admin {admin.get_name()}")
    activity.save()
    return Admin_ActivityDetails.from_activity(activity)


@router.delete("/activity/{activity_id}")
def delete_activity(activity_id: int, admin: AdminUser):
    activity = __get_activity(activity_id)
    activity.delete_instance()
    logger.info("Activity %s deleted by admin %s", activity_id, admin.get_name())
    return "Deleted"


@router.post("/activities/move", response_model=Admin_Moved)
def move_activities(data: Admin_MoveActivities) -> Admin_Moved:
    """all activities (all users) from one game to another, both games are kept"""
    from_game = GameSelect.by_id(data.from_game_id)
    to_game = GameSelect.by_id(data.to_game_id)
    if not from_game or not to_game:
        return not_found("Game not found")
    if from_game.get_id() == to_game.get_id():
        return bad_request("Can't move activities to the same game")

    activities = list(Activity.select().where(Activity.game == from_game))  # type: ignore
    with db.atomic():
        for activity in activities:
            activity = cast(Activity, activity)
            activity.set_game(to_game)
            activity.save()
    return Admin_Moved(moved=len(activities))


@router.get("/activities/overlaps", response_model=list[Admin_OverlapGroup])
def get_overlaps() -> list[Admin_OverlapGroup]:
    result = []
    for group in find_overlapping_groups():
        # same choice as merge_overlapping_group
        keep = max(group, key=lambda a: a.get_seconds())
        result.append(
            Admin_OverlapGroup(
                keep_id=keep.get_id(),
                remove_ids=[a.get_id() for a in group if a.get_id() != keep.get_id()],
            )
        )
    return result


@router.post("/activities/overlaps/merge", response_model=Admin_OverlapsMerged)
def merge_overlaps() -> Admin_OverlapsMerged:
    groups = find_overlapping_groups()
    for group in groups:
        merge_overlapping_group(group)
    return Admin_OverlapsMerged(
        groups=len(groups), removed=sum(len(group) - 1 for group in groups)
    )
